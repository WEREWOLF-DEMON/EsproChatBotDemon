import aiohttp
import asyncio
import os
import subprocess
from PIL import Image
from collections import defaultdict
from EsproChat import app
from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, SIGHTENGINE_API_USER, SIGHTENGINE_API_SECRET, AUTH_USERS

# ✅ Owner & Auth
owner_ids = [int(x) for x in OWNER_ID] if isinstance(OWNER_ID, list) else [int(OWNER_ID)]
authorized_users = set(int(x) for x in AUTH_USERS)
authorized_users.update(owner_ids)

# ✅ State
nsfw_enabled = defaultdict(lambda: True)  # Enabled by default
user_spam_tracker = defaultdict(int)
user_messages = defaultdict(list)

session = aiohttp.ClientSession()
nekos_api = "https://nekos.best/api/v2/neko"

# ✅ Get Random Neko Image
async def get_neko_image():
    try:
        async with session.get(nekos_api, timeout=8) as r:
            if r.status == 200:
                data = await r.json()
                return data["results"][0]["url"]
    except:
        return "https://nekos.best/api/v2/neko/0001.png"

# ✅ Sightengine NSFW Check
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

# ✅ Convert any media to JPG (handle video stickers & videos)
def convert_to_jpg(file_path):
    try:
        if file_path.endswith(".webp"):
            # Static Sticker
            new_path = file_path.replace(".webp", ".jpg")
            img = Image.open(file_path).convert("RGB")
            img.save(new_path, "JPEG")
            os.remove(file_path)
            return new_path
        elif file_path.endswith((".tgs", ".webm", ".mp4", ".mkv")):
            # Video or animated sticker
            new_path = file_path + ".jpg"
            cmd = f'ffmpeg -y -i "{file_path}" -vf "select=eq(n\\,0)" -frames:v 1 -q:v 3 "{new_path}"'
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(file_path):
                os.remove(file_path)
            return new_path if os.path.exists(new_path) else file_path
        return file_path
    except:
        return file_path

# ✅ Process Detection → Delete if NSFW
async def process_nsfw(client, message, file_path, chat_id, user):
    result = await check_nsfw(file_path)
    if os.path.exists(file_path):
        os.remove(file_path)

    if not result:
        return

    # ✅ Extract Scores
    nudity = float(result.get("nudity", {}).get("raw", 0))
    partial = float(result.get("nudity", {}).get("partial", 0))
    sexual = float(result.get("nudity", {}).get("sexual_activity", 0))
    weapon = float(result.get("weapon", 0))
    drugs = float(result.get("drugs", 0))
    offensive = float(result.get("offensive", {}).get("prob", 0))

    # ✅ Decision Logic
    if (nudity > 0.35 or sexual > 0.25 or drugs > 0.5 or weapon > 0.6 or offensive > 0.45):
        # Track user strike
        user_spam_tracker[user.id] += 1
        user_messages[(chat_id, user.id)].append(message.id)

        # Delete actual message
        try:
            await client.delete_messages(chat_id, message.id)
        except:
            pass

        # Delete ALL previous spam messages (batch delete)
        if len(user_messages[(chat_id, user.id)]) > 1:
            try:
                await client.delete_messages(chat_id, user_messages[(chat_id, user.id)])
            except:
                pass
            user_messages[(chat_id, user.id)] = []

        # Auto-ban after 5 warnings
        if user_spam_tracker[user.id] >= 5:
            try:
                await client.kick_chat_member(chat_id, user.id)
            except:
                pass

        # ✅ Send alert EVERY time after delete
        neko_img = await get_neko_image()
        caption = (
            f"🚫 **NSFW/Illegal Content Removed**\n"
            f"👤 {user.mention}\n"
            f"🆔 `{user.id}` | Warnings: `{user_spam_tracker[user.id]}`\n\n"
            f"**Detection Scores:**\n"
            f"Nudity: `{nudity*100:.1f}%` | Partial: `{partial*100:.1f}%`\n"
            f"Sexual: `{sexual*100:.1f}%` | Drugs: `{drugs*100:.1f}%`\n"
            f"Weapon: `{weapon*100:.1f}%` | Offensive: `{offensive*100:.1f}%`"
        )

        await client.send_photo(
            chat_id=chat_id,
            photo=neko_img,
            caption=caption,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{client.me.username}?startgroup=true")]]
            ),
        )

# ✅ Main Handler
@app.on_message(filters.group & (filters.photo | filters.video | filters.animation | filters.sticker | filters.document))
async def nsfw_guard(client, message: Message):
    chat_id = message.chat.id
    user = message.from_user

    if not user or user.id in authorized_users:
        return
    if message.caption and message.caption.startswith("/"):
        return
    if not nsfw_enabled[chat_id]:
        return

    try:
        file_path = await message.download()
        file_path = convert_to_jpg(file_path)  # Convert to JPG for detection
        asyncio.create_task(process_nsfw(client, message, file_path, chat_id, user))
    except:
        pass

# ✅ Toggle NSFW Filter (on/off)
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

# ✅ Authorize User
@app.on_message(filters.command("authorize") & filters.user(owner_ids))
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
        return await message.reply("Reply to a user or provide username/ID.")
    authorized_users.add(user_id)
    await message.reply(f"✅ User `{user_id}` authorized successfully!")

# ✅ Unauthorize User
@app.on_message(filters.command("unauthorize") & filters.user(owner_ids))
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
        return await message.reply("Reply to a user or provide username/ID.")
    if user_id in authorized_users:
        authorized_users.remove(user_id)
        await message.reply(f"❌ User `{user_id}` authorization removed.")
    else:
        await message.reply("User was not authorized.")
