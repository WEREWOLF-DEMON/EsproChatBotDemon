from EsproChat import app
from pyrogram import filters
from pyrogram.types import Message
from config import OWNER_ID
import requests
import re
import asyncio
import os

# Sightengine API keys
SIGHTENGINE_USER = "1916313622"
SIGHTENGINE_SECRET = "frPDtcGYH42kUkmsKuGoj9SVYHCMW9QA"
SE_CREDENTIALS_AVAILABLE = bool(SIGHTENGINE_USER and SIGHTENGINE_SECRET)

# Exempted users
exempt_users = list(map(int, OWNER_ID if isinstance(OWNER_ID, (list, tuple)) else [OWNER_ID]))

# NSFW keywords (text filter)
NSFW_KEYWORDS = [
    "porn", "xxx", "adult", "nsfw", "sex", "fuck", "dick", "pussy", "boobs", "nude",
    "shit", "asshole", "bitch", "bastard", "cunt",
    "drugs?", "heroin", "cocaine", "weed", "marijuana", "lsd", "ecstasy",
    "meth", "opium", "ganja", "charas", "bhang", "smack", "crack",
    "kill", "murder", "rape", "terrorist", "bomb", "shoot",
    "suicide", "selfharm", "cutting"
]

# Downloads folder
if not os.path.exists('downloads'):
    os.makedirs('downloads')

# Get random neko image
def get_neko_image() -> str:
    try:
        response = requests.get("https://nekos.best/api/v2/neko", timeout=10)
        data = response.json()
        return data["results"][0]["url"]
    except Exception as e:
        print(f"Neko API Error: {e}")
        return "https://telegra.ph/file/018d6002a0ad3aee739f4.jpg"

# Check file with Sightengine
def check_nsfw(file_path: str) -> dict:
    if not SE_CREDENTIALS_AVAILABLE:
        return {}

    try:
        with open(file_path, 'rb') as f:
            files = {'media': f}
            response = requests.post(
                "https://api.sightengine.com/1.0/check.json",
                files=files,
                data={
                    'models': 'nudity-2.1,weapon,alcohol,recreational_drug,gore-2.0,violence,self-harm',
                    'api_user': SIGHTENGINE_USER,
                    'api_secret': SIGHTENGINE_SECRET
                },
                timeout=15
            )
        return response.json()
    except Exception as e:
        print(f"[NSFW API Error] {e}")
        return {}

# Media handler
async def process_media(message: Message):
    file_path = await message.download(file_name="downloads/")
    result = check_nsfw(file_path)

    reasons = []

    if result:
        if result.get("nudity", {}).get("sexual_activity", 0) > 0.7:
            reasons.append(f"🔞 Sexual ({result['nudity']['sexual_activity']*100:.1f}%)")
        if result.get("violence", {}).get("prob", 0) > 0.7:
            reasons.append(f"🔪 Violence ({result['violence']['prob']*100:.1f}%)")
        if result.get("weapon", {}).get("prob", 0) > 0.7:
            reasons.append(f"🔫 Weapon ({result['weapon']['prob']*100:.1f}%)")
        if result.get("drug", {}).get("prob", 0) > 0.7:
            reasons.append(f"💊 Drug ({result['drug']['prob']*100:.1f}%)")
        if result.get("gore", {}).get("prob", 0) > 0.7:
            reasons.append(f"🩸 Gore ({result['gore']['prob']*100:.1f}%)")

    if reasons:
        await message.delete()
        neko_img = get_neko_image()
        sender = await app.get_users(message.from_user.id)
        caption = f"""
⚠️ <b>NSFW Content Removed</b>
👤 Name: <code>{sender.first_name}</code>
🆔 ID: <code>{sender.id}</code>
📛 Username: @{sender.username if sender.username else "N/A"}
🚫 Reason(s): {" | ".join(reasons)}
"""
        sent = await message.chat.send_photo(neko_img, caption=caption, parse_mode="html")
        await asyncio.sleep(15)
        await sent.delete()

    try:
        os.remove(file_path)
    except:
        pass

# Text NSFW filter
@app.on_message(filters.text & ~filters.user(exempt_users))
async def text_filter(_, message: Message):
    text = message.text.lower()
    if any(re.search(rf"\b{kw}\b", text) for kw in NSFW_KEYWORDS):
        await message.delete()
        warn = await message.reply("⚠️ NSFW message removed")
        await asyncio.sleep(10)
        await warn.delete()

# Media filter for photos, docs, videos, stickers
@app.on_message(
    (filters.photo | filters.video | filters.document | filters.animation | filters.sticker)
    & ~filters.user(exempt_users)
)
async def media_filter(_, message: Message):
    await process_media(message)

# Add exempt user
@app.on_message(filters.command("addnsfw") & filters.user(exempt_users))
async def add_exempt(_, message: Message):
    try:
        user_id = int(message.command[1])
        if user_id not in exempt_users:
            exempt_users.append(user_id)
            await message.reply(f"✅ Added <code>{user_id}</code> to exempt list", parse_mode="html")
        else:
            await message.reply("ℹ️ Already in exempt list")
    except:
        await message.reply("❌ Usage: /addnsfw <user_id>")

# Remove exempt user
@app.on_message(filters.command("remnsfw") & filters.user(exempt_users))
async def rem_exempt(_, message: Message):
    try:
        user_id = int(message.command[1])
        if user_id in exempt_users:
            exempt_users.remove(user_id)
            await message.reply(f"✅ Removed <code>{user_id}</code> from exempt list", parse_mode="html")
        else:
            await message.reply("ℹ️ User not in exempt list")
    except:
        await message.reply("❌ Usage: /remnsfw <user_id>")

# List exempt users
@app.on_message(filters.command("listnsfw") & filters.user(exempt_users))
async def list_exempt(_, message: Message):
    if not exempt_users:
        await message.reply("ℹ️ No exempt users")
    else:
        text = "\n".join([f"• <code>{uid}</code>" for uid in exempt_users])
        await message.reply(f"🛡️ Exempt List:\n{text}", parse_mode="html")
