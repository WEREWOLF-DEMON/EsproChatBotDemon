import aiohttp
import asyncio
import os
import time
from collections import defaultdict
from EsproChat import app
from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, SIGHTENGINE_API_USER, SIGHTENGINE_API_SECRET, AUTH_USERS

# ✅ Config
nekos_api = "https://nekos.best/api/v2/neko"
authorized_users = set(AUTH_USERS) | {OWNER_ID}
nsfw_enabled = defaultdict(lambda: True)
user_spam_tracker = defaultdict(int)
user_messages = defaultdict(list)
last_alert_time = defaultdict(float)

session = aiohttp.ClientSession()

# ✅ Fetch random neko image
async def get_neko_image():
    try:
        async with session.get(nekos_api, timeout=8) as r:
            if r.status == 200:
                data = await r.json()
                return data["results"][0]["url"]
    except:
        return "https://nekos.best/api/v2/neko/0001.png"

# ✅ Sightengine API Check
async def check_nsfw(file_path: str):
    url = "https://api.sightengine.com/1.0/check.json"
    try:
        form = aiohttp.FormData()
        form.add_field("media", open(file_path, "rb"), filename="file.jpg", content_type="image/jpeg")
        form.add_field("models", "nudity,wad,offensive")
        form.add_field("api_user", SIGHTENGINE_API_USER)
        form.add_field("api_secret", SIGHTENGINE_API_SECRET)
        async with session.post(url, data=form, timeout=20) as resp:
            return await resp.json()
    except:
        return None

# ✅ Delete multiple messages
async def delete_user_messages(client, chat_id, user_id):
    msgs = user_messages.get((chat_id, user_id), [])
    if msgs:
        try:
            await client.delete_messages(chat_id, msgs)
        except:
            for m in msgs:
                try:
                    await client.delete_messages(chat_id, m)
                except:
                    pass
    user_messages[(chat_id, user_id)].clear()

# ✅ Process NSFW
async def process_nsfw(client, message, file_path, chat_id, user):
    result = await check_nsfw(file_path)
    if os.path.exists(file_path):
        os.remove(file_path)

    if not result:
        return

    # ✅ Extract detection scores
    nudity = float(result.get("nudity", {}).get("raw", 0))
    partial = float(result.get("nudity", {}).get("partial", 0))
    sexual = float(result.get("nudity", {}).get("sexual_activity", 0))
    weapon = float(result.get("weapon", 0))
    drugs = float(result.get("drugs", 0))
    offensive = float(result.get("offensive", {}).get("prob", 0))

    combined_score = (nudity + partial + sexual + offensive) / 4

    # ✅ NSFW decision logic
    if combined_score > 0.4 or weapon > 0.8 or drugs > 0.6:
        user_spam_tracker[user.id] += 1
        await delete_user_messages(client, chat_id, user.id)

        # ✅ Anti-spam: Avoid frequent alerts
        now = time.time()
        if now - last_alert_time[user.id] < 25:
            return
        last_alert_time[user.id] = now

        neko_img = await get_neko_image()
        caption = (
            f"🚫 **NSFW Content Removed**\n\n"
            f"👤 User: {user.mention}\n"
            f"🆔 `{user.id}` | Spam Count: {user_spam_tracker[user.id]}\n\n"
            f"**Scores:**\n"
            f"Nudity: `{nudity*100:.1f}%` | Partial: `{partial*100:.1f}%`\n"
            f"Sexual: `{sexual*100:.1f}%` | Offensive: `{offensive*100:.1f}%`"
        )

        await message.reply_photo(
            neko_img,
            caption=caption,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{client.me.username}?startgroup=true")]]
            )
        )

# ✅ Main Detector
@app.on_message(filters.group & (filters.photo | filters.video | filters.animation | filters.sticker))
async def nsfw_guard(client, message: Message):
    chat_id = message.chat.id
    user = message.from_user
    if not user or user.id in authorized_users:
        return
    if message.caption and message.caption.startswith("/"):
        return
    if not nsfw_enabled[chat_id]:
        return
    if message.sticker and not (message.sticker.is_video or message.sticker.is_animated):
        return

    # ✅ Track messages for bulk deletion
    user_messages[(chat_id, user.id)].append(message.id)
    if len(user_messages[(chat_id, user.id)]) > 30:
        user_messages[(chat_id, user.id)].pop(0)

    try:
        file_path = await message.download()
        asyncio.create_task(process_nsfw(client, message, file_path, chat_id, user))
    except:
        pass

# ✅ Toggle NSFW Filter
@app.on_message(filters.command("nsfw") & filters.group)
async def toggle_nsfw(client, message: Message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
        return await message.reply("❌ Only admins can toggle NSFW filter.")
    if len(message.command) < 2:
        return await message.reply("Usage: `/nsfw on` or `/nsfw off`")
    state = message.command[1].lower()
    if state == "on":
        nsfw_enabled[message.chat.id] = True
        await message.reply("✅ **NSFW filter ENABLED**")
    elif state == "off":
        nsfw_enabled[message.chat.id] = False
        await message.reply("❌ **NSFW filter DISABLED**")
    else:
        await message.reply("❌ Invalid command. Use `/nsfw on` or `/nsfw off`.")

# ✅ Authorize User (OWNER only)
@app.on_message(filters.command("authorize") & filters.user(OWNER_ID))
async def authorize_user(client, message: Message):
    user_id = None
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        try:
            user_obj = await client.get_users(message.command[1])
            user_id = user_obj.id
        except:
            return await message.reply("❌ Invalid user.")
    if not user_id:
        return await message.reply("Reply or provide username/ID.")
    authorized_users.add(user_id)
    await message.reply(f"✅ User `{user_id}` is now authorized.")

@app.on_message(filters.command("unauthorize") & filters.user(OWNER_ID))
async def unauthorize_user(client, message: Message):
    user_id = None
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        try:
            user_obj = await client.get_users(message.command[1])
            user_id = user_obj.id
        except:
            return await message.reply("❌ Invalid user.")
    if not user_id:
        return await message.reply("Reply or provide username/ID.")
    if user_id in authorized_users:
        authorized_users.remove(user_id)
        await message.reply(f"❌ User `{user_id}` authorization removed.")
    else:
        await message.reply("User was not authorized.")
