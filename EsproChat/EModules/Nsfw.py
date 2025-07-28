import aiohttp
import asyncio
import os
import time
from collections import defaultdict
from EsproChat import app
from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, SIGHTENGINE_API_USER, SIGHTENGINE_API_SECRET, AUTH_USERS

# Initialize properly
if isinstance(OWNER_ID, list):
    owner_ids = [int(x) for x in OWNER_ID]
else:
    owner_ids = [int(OWNER_ID)]

authorized_users = set(AUTH_USERS)
authorized_users.update(owner_ids)

# NSFW State
nsfw_enabled = defaultdict(lambda: True)
user_spam_tracker = defaultdict(int)
user_messages = defaultdict(list)
last_alert_time = defaultdict(float)
processing_lock = defaultdict(asyncio.Lock)

# HTTP Session
session = aiohttp.ClientSession()

nekos_api = "https://nekos.best/api/v2/neko"

async def get_neko_image():
    try:
        async with session.get(nekos_api, timeout=8) as r:
            if r.status == 200:
                data = await r.json()
                return data["results"][0]["url"]
    except:
        return "https://nekos.best/api/v2/neko/0001.png"

async def check_nsfw(file_path: str):
    url = "https://api.sightengine.com/1.0/check.json"
    try:
        form = aiohttp.FormData()
        form.add_field("media", open(file_path, "rb"), filename="file.jpg", content_type="image/jpeg")
        form.add_field("models", "nudity,wad,offensive,drugs,gore")
        form.add_field("api_user", SIGHTENGINE_API_USER)
        form.add_field("api_secret", SIGHTENGINE_API_SECRET)
        async with session.post(url, data=form, timeout=20) as resp:
            return await resp.json()
    except Exception as e:
        print(f"Sightengine error: {e}")
        return None
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

async def delete_user_messages(client, chat_id, user_id):
    msgs = user_messages.get((chat_id, user_id), [])
    if not msgs:
        return
    
    # Split into chunks of 100
    for i in range(0, len(msgs), 100):
        chunk = msgs[i:i + 100]
        try:
            await client.delete_messages(chat_id, chunk)
        except:
            for msg_id in chunk:
                try:
                    await client.delete_messages(chat_id, msg_id)
                except:
                    continue
    
    user_messages[(chat_id, user_id)].clear()

def is_violating_content(result):
    if not result:
        return False
        
    nudity = float(result.get("nudity", {}).get("raw", 0))
    partial = float(result.get("nudity", {}).get("partial", 0))
    sexual = float(result.get("nudity", {}).get("sexual_activity", 0))
    weapon = float(result.get("weapon", 0))
    drugs = float(result.get("drugs", 0))
    offensive = float(result.get("offensive", {}).get("prob", 0))
    gore = float(result.get("gore", {}).get("prob", 0))

    return (nudity > 0.4 or partial > 0.45 or sexual > 0.35 or 
            weapon > 0.6 or drugs > 0.5 or offensive > 0.55 or gore > 0.5)

async def process_nsfw(client, message, file_path, chat_id, user):
    async with processing_lock[(chat_id, user.id)]:
        result = await check_nsfw(file_path)
        
        if is_violating_content(result):
            user_spam_tracker[user.id] += 1
            await delete_user_messages(client, chat_id, user.id)

            now = time.time()
            if now - last_alert_time[user.id] < 15:
                return
            last_alert_time[user.id] = now

            neko_img = await get_neko_image()
            
            # Fixed f-string syntax
            nudity_score = float(result.get("nudity", {}).get("raw", 0)) * 100
            partial_score = float(result.get("nudity", {}).get("partial", 0)) * 100
            weapon_score = float(result.get("weapon", 0)) * 100
            drugs_score = float(result.get("drugs", 0)) * 100
            gore_score = float(result.get("gore", {}).get("prob", 0)) * 100
            
            caption = (
                "🚨 **Content Removed - Policy Violation**\n\n"
                f"👤 User: {user.mention}\n"
                f"🆔 `{user.id}` | Total Violations: {user_spam_tracker[user.id]}\n\n"
                "**Detection Scores:**\n"
                f"• Nudity: {nudity_score:.1f}%\n"
                f"• Partial Nudity: {partial_score:.1f}%\n"
                f"• Weapons: {weapon_score:.1f}%\n"
                f"• Drugs: {drugs_score:.1f}%\n"
                f"• Gore/Violence: {gore_score:.1f}%"
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

@app.on_message(filters.group & (
    filters.photo | 
    filters.video | 
    filters.animation | 
    filters.sticker | 
    filters.document
))
async def nsfw_guard(client, message: Message):
    if not message.from_user or message.from_user.id in authorized_users:
        return
    if message.caption and message.caption.startswith("/"):
        return
    if not nsfw_enabled[message.chat.id]:
        return
    
    if message.sticker and not (message.sticker.is_video or message.sticker.is_animated):
        return
    
    user_messages[(message.chat.id, message.from_user.id)].append(message.id)
    if len(user_messages[(message.chat.id, message.from_user.id)]) > 50:
        user_messages[(message.chat.id, message.from_user.id)].pop(0)
    
    try:
        file_path = await message.download()
        asyncio.create_task(process_nsfw(client, message, file_path, message.chat.id, message.from_user))
    except Exception as e:
        print(f"Download failed: {e}")

@app.on_message(filters.command("nsfw") & filters.group)
async def toggle_nsfw(client, message: Message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
        return await message.reply("❌ You need admin rights to toggle NSFW filter.")
    
    if len(message.command) < 2:
        status = "ENABLED ✅" if nsfw_enabled[message.chat.id] else "DISABLED ❌"
        return await message.reply(f"🛡️ NSFW Filter Status: {status}\nUsage: /nsfw on or /nsfw off")
    
    state = message.command[1].lower()
    if state in ("on", "yes", "enable"):
        nsfw_enabled[message.chat.id] = True
        await message.reply("✅ NSFW filter ENABLED - All media will be scanned")
    elif state in ("off", "no", "disable"):
        nsfw_enabled[message.chat.id] = False
        await message.reply("❌ NSFW filter DISABLED - Media will not be scanned")
    else:
        await message.reply("❌ Invalid command. Use /nsfw on or /nsfw off")

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
            return await message.reply("❌ Reply to user or provide ID/username")
        
        authorized_users.add(user_id)
        await message.reply(f"✅ User {user_id} can now bypass NSFW filter")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

async def cleanup():
    await session.close()

app.run()
