import aiohttp
import asyncio
import os
import time
from collections import defaultdict
from EsproChat import app
from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, SIGHTENGINE_API_USER, SIGHTENGINE_API_SECRET, AUTH_USERS

# ✅ Initialize properly
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
session = None

async def initialize_session():
    global session
    timeout = aiohttp.ClientTimeout(total=10)
    session = aiohttp.ClientSession(timeout=timeout)

# ✅ Fast fetch random neko image with retry
nekos_api = "https://nekos.best/api/v2/neko"
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
            
            part = mp.append('nudity,wad,offensive,drugs,gore')
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

# ✅ Enhanced NSFW detection logic
def is_content_violating(result):
    if not result:
        return False
        
    # Extract scores
    nudity = float(result.get("nudity", {}).get("raw", 0))
    partial = float(result.get("nudity", {}).get("partial", 0))
    sexual = float(result.get("nudity", {}).get("sexual_activity", 0))
    weapon = float(result.get("weapon", 0))
    drugs = float(result.get("drugs", 0))
    offensive = float(result.get("offensive", {}).get("prob", 0))
    gore = float(result.get("gore", {}).get("prob", 0))

    # Strict detection thresholds
    return (
        nudity > 0.4 or
        partial > 0.45 or
        sexual > 0.35 or
        weapon > 0.6 or
        drugs > 0.5 or
        offensive > 0.55 or
        gore > 0.5
    )

# ✅ Process NSFW with optimized logic
async def process_nsfw(client, message, file_path, chat_id, user):
    async with processing_lock[(chat_id, user.id)]:
        result = await check_nsfw(file_path)
        
        if is_content_violating(result):
            user_spam_tracker[user.id] += 1
            await delete_user_messages(client, chat_id, user.id)

            # Rate limit alerts
            now = time.time()
            if now - last_alert_time[user.id] < 15:  # 15 seconds cooldown
                return
            last_alert_time[user.id] = now

            # Get replacement image
            neko_img = await get_neko_image()
            
            # Prepare detailed alert
            caption = (
                f"🚨 **Content Removed - Policy Violation**\n\n"
                f"👤 User: {user.mention}\n"
                f"🆔 `{user.id}` | Total Violations: {user_spam_tracker[user.id]}\n\n"
                f"**Detection Scores:**\n"
                f"• Nudity: `{float(result.get('nudity', {}).get('raw', 0)*100:.1f}%`\n"
                f"• Partial Nudity: `{float(result.get('nudity', {}).get('partial', 0)*100:.1f}%`\n"
                f"• Weapons: `{float(result.get('weapon', 0)*100:.1f}%`\n"
                f"• Drugs: `{float(result.get('drugs', 0)*100:.1f}%`\n"
                f"• Gore/Violence: `{float(result.get('gore', {}).get('prob', 0)*100:.1f}%`"
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

# ✅ Main Detector with all media types
@app.on_message(filters.group & (
    filters.photo | 
    filters.video | 
    filters.animation | 
    filters.sticker | 
    filters.document
))
async def nsfw_guard(client, message: Message):
    # Skip checks for authorized users and commands
    if not message.from_user or message.from_user.id in authorized_users:
        return
    if message.caption and message.caption.startswith("/"):
        return
    if not nsfw_enabled[message.chat.id]:
        return
    
    # Handle all media types including stickers and GIFs
    media_types = {
        "photo": message.photo,
        "video": message.video,
        "animation": message.animation,
        "sticker": message.sticker,
        "document": message.document
    }
    
    # Skip non-media and static stickers
    media_type = next((t for t, m in media_types.items() if m), None)
    if not media_type:
        return
    if media_type == "sticker" and not (message.sticker.is_video or message.sticker.is_animated):
        return
    
    # Track message for bulk deletion
    user_messages[(message.chat.id, message.from_user.id)].append(message.id)
    if len(user_messages[(message.chat.id, message.from_user.id)]) > 50:
        user_messages[(message.chat.id, message.from_user.id)].pop(0)
    
    try:
        file_path = await message.download()
        asyncio.create_task(process_nsfw(client, message, file_path, message.chat.id, message.from_user))
    except Exception as e:
        print(f"Download failed: {e}")

# ✅ Toggle NSFW Filter
@app.on_message(filters.command("nsfw") & filters.group)
async def toggle_nsfw(client, message: Message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
        return await message.reply("❌ You need admin rights to toggle NSFW filter.")
    
    if len(message.command) < 2:
        status = "ENABLED ✅" if nsfw_enabled[message.chat.id] else "DISABLED ❌"
        return await message.reply(f"🛡️ NSFW Filter Status: {status}\nUsage: `/nsfw on` or `/nsfw off`")
    
    state = message.command[1].lower()
    if state in ("on", "yes", "enable"):
        nsfw_enabled[message.chat.id] = True
        await message.reply("✅ **NSFW filter ENABLED** - All media will be scanned for inappropriate content.")
    elif state in ("off", "no", "disable"):
        nsfw_enabled[message.chat.id] = False
        await message.reply("❌ **NSFW filter DISABLED** - Media will not be scanned.")
    else:
        await message.reply("❌ Invalid command. Use `/nsfw on` or `/nsfw off`.")

# ✅ Authorize commands
@app.on_message(filters.command("authorize") & filters.user(owner_ids))
async def authorize_user(client, message: Message):
    try:
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
        elif len(message.command) > 1:
            try:
                user_id = int(message.command[1])
            except ValueError:
                user = await client.get_users(message.command[1])
                user_id = user.id
        else:
            return await message.reply("❌ Reply to user or provide ID/username.")
        
        authorized_users.add(user_id)
        await message.reply(f"✅ User `{user_id}` can now bypass NSFW filter.")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

# ✅ Cleanup function
async def cleanup():
    if session:
        await session.close()

# Initialize session when bot starts
@app.on_message(filters.command("init") & filters.user(owner_ids))
async def init_bot(client, message: Message):
    await initialize_session()
    await message.reply("✅ Bot initialized successfully!")

# Start the bot properly
if __name__ == "__main__":
    app.start()
    app.run()
    app.idle()
