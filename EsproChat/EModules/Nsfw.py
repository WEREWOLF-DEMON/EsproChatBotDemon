import aiohttp
import asyncio
import os
from collections import defaultdict
from EsproChat import app
from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, SIGHTENGINE_API_USER, SIGHTENGINE_API_SECRET, AUTH_USERS

# ✅ Config
nekos_api = "https://nekos.best/api/v2/neko"
authorized_users = set(AUTH_USERS)
nsfw_enabled = defaultdict(lambda: True)
user_spam_tracker = defaultdict(int)
user_messages = defaultdict(list)

session = aiohttp.ClientSession()  # Reuse session for speed

# ✅ Fetch random neko image
async def get_neko_image():
    try:
        async with session.get(nekos_api, timeout=10) as r:
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

        async with session.post(url, data=form, timeout=25) as resp:
            return await resp.json()
    except Exception as e:
        print(f"[ERROR] Sightengine API: {e}")
        return None

# ✅ Delete all messages from user
async def delete_user_messages(client, chat_id, user_id):
    for msg_id in user_messages.get((chat_id, user_id), []):
        try:
            await client.delete_messages(chat_id, msg_id)
        except:
            pass
    user_messages[(chat_id, user_id)].clear()

# ✅ Background Task for NSFW Analysis
async def process_nsfw(client, message, file_path, chat_id, user):
    result = await check_nsfw(file_path)
    os.remove(file_path)

    if not result:
        return

    # ✅ Extract scores
    nudity = float(result.get("nudity", {}).get("raw", 0))
    partial = float(result.get("nudity", {}).get("partial", 0))
    sexual = float(result.get("nudity", {}).get("sexual_activity", 0))
    weapon = float(result.get("weapon", 0))
    alcohol = float(result.get("alcohol", 0))
    drugs = float(result.get("drugs", 0))
    offensive = float(result.get("offensive", {}).get("prob", 0))

    # ✅ Detection logic
    if nudity > 0.6 or partial > 0.6 or sexual > 0.3 or weapon > 0.8 or alcohol > 0.8 or drugs > 0.6 or offensive > 0.7:
        user_spam_tracker[user.id] += 1
        await delete_user_messages(client, chat_id, user.id)

        neko_img = await get_neko_image()
        media_type = (
            "Photo" if message.photo else
            "Video Sticker" if message.sticker and message.sticker.is_video else
            "GIF Sticker" if message.sticker and message.sticker.is_animated else
            "GIF" if message.animation else
            "Video" if message.video else
            "Sticker"
        )

        caption = (
            f"🚫 **NSFW Content Removed**\n\n"
            f"👤 User: {user.mention}\n"
            f"🆔 ID: `{user.id}`\n"
            f"📎 Type: `{media_type}`\n\n"
            f"🔍 **Scores:**\n"
            f"Nudity: `{nudity*100:.1f}%`\n"
            f"Partial Nudity: `{partial*100:.1f}%`\n"
            f"Sexual: `{sexual*100:.1f}%`\n"
            f"Weapon: `{weapon*100:.1f}%`\n"
            f"Alcohol: `{alcohol*100:.1f}%`\n"
            f"Drugs: `{drugs*100:.1f}%`\n"
            f"Offensive: `{offensive*100:.1f}%`"
        )

        await message.reply_photo(
            photo=neko_img,
            caption=caption,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{client.me.username}?startgroup=true")]]
            )
        )

# ✅ Main NSFW Detector
@app.on_message(filters.group & (filters.photo | filters.video | filters.animation | filters.sticker))
async def nsfw_guard(client, message: Message):
    chat_id = message.chat.id
    user = message.from_user
    if not user or user.id in [OWNER_ID] or user.id in authorized_users:
        return
    if message.caption and message.caption.startswith("/"):
        return
    if not nsfw_enabled[chat_id]:
        return
    if message.sticker and not (message.sticker.is_video or message.sticker.is_animated):
        return

    # ✅ Track message
    user_messages[(chat_id, user.id)].append(message.id)
    if len(user_messages[(chat_id, user.id)]) > 20:
        user_messages[(chat_id, user.id)].pop(0)

    # ✅ Instant delete for safety
    await client.delete_messages(chat_id, message.id)

    # ✅ Download and process in background
    try:
        file_path = await message.download()
        asyncio.create_task(process_nsfw(client, message, file_path, chat_id, user))
    except:
        pass

# ✅ Toggle NSFW Filter with Stylish Responses
@app.on_message(filters.command("nsfw") & filters.group)
async def toggle_nsfw(client, message: Message):
    user = await client.get_chat_member(message.chat.id, message.from_user.id)
    if user.status not in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
        return await message.reply("❌ Only admins can toggle NSFW filter.")

    if len(message.command) < 2:
        return await message.reply("Usage: `/nsfw on` or `/nsfw off`")

    state = message.command[1].lower()
    if state not in ["on", "off"]:
        return await message.reply("❌ Invalid option!\nUsage: `/nsfw on` or `/nsfw off`")

    if state == "on":
        nsfw_enabled[message.chat.id] = True
        await message.reply("✅ **NSFW filter is now ENABLED.**")
    else:
        nsfw_enabled[message.chat.id] = False
        await message.reply("❌ **NSFW filter is now DISABLED.**")

# ✅ Authorize Commands
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
    await message.reply(f"✅ User `{user_id}` authorized.")

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
