# File: EsproChat/EModules/Nsfw.py

import requests
import os
import tempfile
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import MessageMediaType
from config import OWNER_ID  # make sure you have OWNER_ID in config

# Sightengine API credentials
SIGHTENGINE_USER = "1916313622"
SIGHTENGINE_SECRET = "frPDtcGYH42kUkmsKuGoj9SVYHCMW9QA"

# Allowed media types to scan
ALLOWED_MEDIA = [
    MessageMediaType.PHOTO,
    MessageMediaType.VIDEO,
    MessageMediaType.STICKER,
    MessageMediaType.DOCUMENT,
    MessageMediaType.ANIMATION  # gif
]

async def is_nsfw(file_path: str) -> dict:
    params = {
        'models': 'nudity,wad,offensive,gore',
        'api_user': SIGHTENGINE_USER,
        'api_secret': SIGHTENGINE_SECRET
    }
    with open(file_path, 'rb') as f:
        files = {'media': f}
        r = requests.post('https://api.sightengine.com/1.0/check.json', files=files, data=params)
        return r.json()

async def get_neko_image() -> str:
    try:
        r = requests.get("https://nekos.best/api/v2/neko")
        return r.json()["results"][0]["url"]
    except Exception:
        return "https://nekos.best/api/v2/neko"  # fallback static URL

@Client.on_message(filters.group & filters.media)
async def media_filter(client: Client, message: Message):
    if message.media not in ALLOWED_MEDIA:
        return  # Not a media we want to scan

    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        file_path = await message.download(file_name=temp_file.name)
        result = await is_nsfw(file_path)
        os.remove(file_path)

        # Extract NSFW probability
        nsfw_score = (
            result.get("nudity", {}).get("raw", 0) +
            result.get("nudity", {}).get("safe", 0) +
            result.get("nudity", {}).get("partial", 0) +
            result.get("weapon", 0) +
            result.get("alcohol", 0) +
            result.get("drugs", 0) +
            result.get("offensive", {}).get("prob", 0) +
            result.get("gore", 0)
        )

        # Threshold check
        if nsfw_score >= 0.6:
            await message.delete()

            neko_img = await get_neko_image()
            caption = (
                f"🚫 <b>NSFW Content Detected!</b>\n"
                f"🤖 <b>Reason:</b> {result.get('reason', 'Not Safe')}\n"
                f"📊 <b>NSFW Score:</b> {round(nsfw_score * 100, 2)}%\n"
                f"👤 <b>By:</b> {message.from_user.mention if message.from_user else 'Unknown'}\n"
                f"🆔 <code>{message.from_user.id if message.from_user else 'N/A'}</code>"
            )
            await message.chat.send_photo(neko_img, caption=caption, parse_mode="html")

    except Exception as e:
        # Log error to owner
        await client.send_message(OWNER_ID, f"[NSFW ERROR]\n{str(e)}")
