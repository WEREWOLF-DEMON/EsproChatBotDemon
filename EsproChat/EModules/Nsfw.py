import aiohttp
import asyncio
import os
import time
from collections import defaultdict
from EsproChat import app
from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, SIGHTENGINE_API_USER, SIGHTENGINE_API_SECRET, AUTH_USERS

# ✅ Convert OWNER_ID safely
if isinstance(OWNER_ID, list):
    owner_ids = [int(x) for x in OWNER_ID]
else:
    owner_ids = [int(OWNER_ID)]

authorized_users = set(AUTH_USERS)
authorized_users.update(owner_ids)

# ✅ NSFW State
nsfw_enabled = defaultdict(lambda: True)
user_spam_tracker = defaultdict(int)
user_messages = defaultdict(list)
last_alert_time = defaultdict(float)
processing_lock = defaultdict(asyncio.Lock)

# ✅ HTTP Session with timeout
timeout = aiohttp.ClientTimeout(total=10)
session = aiohttp.ClientSession(timeout=timeout)

nekos_api = "https://nekos.best/api/v2/neko"

# ✅ Fast fetch random neko image with retry
async def get_neko_image(retry=3):
    for _ in range(retry):
        try:
            async with session.get(nekos_api) as r:
                if r.status == 200:
                    data = await r.json()
                    return data["results"][0]["url"]
        except:
            await asyncio.sleep(1)
    return "https://nekos.best/api/v2/neko/0001.png"

# ✅ Optimized Sightengine API Check
async def check_nsfw(file_path: str):
    url = "https://api.sightengine.com/1.0/check.json"
    try:
        async with aiohttp.MultipartWriter('form-data') as mp:
            part = mp.append(open(file_path, 'rb'))
            part.set_content_disposition('form-data', name='media', filename='file.jpg')
            part.headers['Content-Type'] = 'image/jpeg'
            
            part = mp.append('nudity,wad,offensive')
            part.set_content_disposition('form-data', name='models')
            
            part = mp.append(SIGHTENGINE_API_USER)
            part.set_content_disposition('form-data', name='api_user')
            
            part = mp.append(SIGHTENGINE_API_SECRET)
            part.set_content_disposition('form-data', name='api_secret')

            async with session.post(url, data=mp) as resp:
                return await resp.json()
    except Exception as e:
        print(f"Sightengine error: {e}")
        return None
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# ✅ Bulk delete messages efficiently
async def delete_user_messages(client, chat_id, user_id):
    msgs = user_messages.get((chat_id, user_id), [])
    if not msgs:
        return
    
    # Split into chunks of 100 (Telegram API limit)
    for i in range(0, len(msgs), 100):
        chunk = msgs[i:i + 100]
        try:
            await client.delete_messages(chat_id, chunk)
        except Exception as e:
            print(f"Failed to delete messages: {e}")
            # Fallback to individual deletion
            for msg_id in chunk:
                try:
                    await client.delete_messages(chat_id, msg_id)
                except:
                    continue
    
    user_messages[(chat_id, user_id)].clear()

# ✅ Process NSFW with optimized logic
async def process_nsfw(client, message, file_path, chat_id, user):
    async with processing_lock[(chat_id, user.id)]:
        result = await check_nsfw(file_path)
        if not result:
            return

        # ✅ Extract detection scores
        nudity = float(result.get("nudity", {}).get("raw", 0))
        partial = float(result.get("nudity", {}).get("partial", 0))
        sexual = float(result.get("nudity", {}).get("sexual_activity", 0))
        weapon = float(result.get("weapon", 0))
        drugs = float(result.get("drugs", 0))
        offensive = float(result.get("offensive", {}).get("prob", 0))

        # Weighted combined score
        combined_score = (nudity*0.4 + partial*0.3 + sexual*0.2 + offensive*0.1)

        # ✅ NSFW decision logic with thresholds
        is_nsfw = (
            combined_score > 0.35 or 
            nudity > 0.45 or 
            partial > 0.5 or 
            sexual > 0.4 or 
            weapon > 0.7 or 
            drugs > 0.5 or 
            offensive > 0.6
        )

        if is_nsfw:
            user_spam_tracker[user.id] += 1
            await delete_user_messages(client, chat_id, user.id)

            # Rate limit alerts to prevent spam
            now = time.time()
            if now - last_alert_time[user.id] < 20:  # 20 seconds cooldown
                return
            last_alert_time[user.id] = now

            # Get replacement image
            neko_img = await get_neko_image()
            
            # Prepare alert message
            caption = (
                f"🚫 **NSFW Content Detected & Removed**\n\n"
                f"👤 User: {user.mention}\n"
                f"🆔 `{user.id}` | Violations: {user_spam_tracker[user.id]}\n\n"
                f"**Detection Scores:**\n"
                f"• Nudity: `{nudity*100:.1f}%`\n"
                f"• Partial Nudity: `{partial*100:.1f}%`\n"
                f"• Sexual Activity: `{sexual*100:.1f}%`\n"
                f"• Offensive: `{offensive*100:.1f}%`\n"
                f"• Weapons: `{weapon*100:.1f}%`\n"
                f"• Drugs: `{drugs*100:.1f}%`"
            )

            try:
                await message.reply_photo(
                    neko_img,
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{client.me.username}?startgroup=true")]]
                    )
                )
            except Exception as e:
                print(f"Failed to send alert: {e}")

# ✅ Main Detector with improved media handling
@app.on_message(filters.group & (
    filters.photo | 
    filters.video | 
    filters.animation | 
    filters.sticker | 
    filters.document
))
async def nsfw_guard(client, message: Message):
    chat_id = message.chat.id
    user = message.from_user
    
    # Skip checks for authorized users and commands
    if not user or user.id in authorized_users:
        return
    if message.caption and message.caption.startswith("/"):
        return
    if not nsfw_enabled[chat_id]:
        return
    
    # Handle different media types
    media_types = {
        "photo": message.photo,
        "video": message.video,
        "animation": message.animation,
        "sticker": message.sticker,
        "document": message.document
    }
    
    # Skip non-media messages and static stickers
    media_type = next((t for t, m in media_types.items() if m), None)
    if not media_type:
        return
    if media_type == "sticker" and not (message.sticker.is_video or message.sticker.is_animated):
        return
    
    # Track message for bulk deletion
    user_messages[(chat_id, user.id)].append(message.id)
    if len(user_messages[(chat_id, user.id)]) > 50:  # Keep last 50 messages
        user_messages[(chat_id, user.id)].pop(0)
    
    try:
        file_path = await message.download()
        asyncio.create_task(process_nsfw(client, message, file_path, chat_id, user))
    except Exception as e:
        print(f"Download failed: {e}")

# ✅ Toggle NSFW Filter with better response
@app.on_message(filters.command("nsfw") & filters.group)
async def toggle_nsfw(client, message: Message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
        return await message.reply("❌ You need to be an admin to use this command.")
    
    if len(message.command) < 2:
        current = "ENABLED" if nsfw_enabled[message.chat.id] else "DISABLED"
        return await message.reply(
            f"🛡️ **NSFW Filter Status**: {current}\n"
            "Usage: `/nsfw on` or `/nsfw off`"
        )
    
    state = message.command[1].lower()
    if state in ("on", "yes", "enable"):
        nsfw_enabled[message.chat.id] = True
        await message.reply("✅ **NSFW filter ENABLED** - All media will be scanned for inappropriate content.")
    elif state in ("off", "no", "disable"):
        nsfw_enabled[message.chat.id] = False
        await message.reply("❌ **NSFW filter DISABLED** - Media will not be scanned.")
    else:
        await message.reply("❌ Invalid command. Use `/nsfw on` or `/nsfw off`.")

# ✅ Improved authorize commands
@app.on_message(filters.command("authorize") & filters.user(owner_ids))
async def authorize_user(client, message: Message):
    try:
        if message.reply_to_message and message.reply_to_message.from_user:
            user_id = message.reply_to_message.from_user.id
        elif len(message.command) > 1:
            try:
                user_id = int(message.command[1])
            except ValueError:
                user_obj = await client.get_users(message.command[1])
                user_id = user_obj.id
        else:
            return await message.reply("❌ Reply to a user or provide user ID/username.")
        
        authorized_users.add(user_id)
        await message.reply(f"✅ User `{user_id}` is now authorized to bypass NSFW filter.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

@app.on_message(filters.command("unauthorize") & filters.user(owner_ids))
async def unauthorize_user(client, message: Message):
    try:
        if message.reply_to_message and message.reply_to_message.from_user:
            user_id = message.reply_to_message.from_user.id
        elif len(message.command) > 1:
            try:
                user_id = int(message.command[1])
            except ValueError:
                user_obj = await client.get_users(message.command[1])
                user_id = user_obj.id
        else:
            return await message.reply("❌ Reply to a user or provide user ID/username.")
        
        if user_id in authorized_users:
            authorized_users.remove(user_id)
            await message.reply(f"❌ User `{user_id}` can no longer bypass NSFW filter.")
        else:
            await message.reply("ℹ️ This user wasn't authorized.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# Cleanup on shutdown
async def cleanup():
    await session.close()

app.add_handler(filters.group, nsfw_guard)
app.run(cleanup())
