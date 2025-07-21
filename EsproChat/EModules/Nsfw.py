import requests
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, NSFW_API_USER, NSFW_API_SECRET
import os
import aiofiles
from EsproChat.database.nsfwauth import add_auth, rm_auth, get_auth

# Supported Media Types
MEDIA_TYPES = ["photo", "video", "animation", "sticker"]

async def detect_nsfw(path: str) -> dict:
    url = "https://api.sightengine.com/1.0/check.json"
    with open(path, "rb") as f:
        files = {'media': f}
        data = {
            'models': 'nudity,wad,offensive,text-content',
            'api_user': 1916313622,
            'api_secret': frPDtcGYH42kUkmsKuGoj9SVYHCMW9QA,
        }
        response = requests.post(url, files=files, data=data)
        return response.json()

async def neko_image() -> str:
    try:
        r = requests.get("https://nekos.best/api/v2/neko")
        return r.json()["results"][0]["url"]
    except:
        return "https://nekos.best/api/v2/neko"

@Client.on_message(filters.group & filters.media)
async def nsfw_filter(client: Client, message: Message):
    user = message.from_user
    chat_id = message.chat.id

    # Authorized check
    auth = await get_auth(chat_id)
    if user and (user.id == OWNER_ID or str(user.id) in auth):
        return

    # Media download
    try:
        file_path = f"downloads/{message.media_group_id or message.id}.temp"
        await client.download_media(message, file_path)
    except Exception as e:
        return

    # NSFW Detection
    try:
        result = await detect_nsfw(file_path)
        rating = result.get("nudity", {}).get("raw", 0)
        wad = result.get("weapon", 0) + result.get("alcohol", 0) + result.get("drugs", 0)
        offensive = result.get("offensive", {}).get("prob`, 0)

        # Delete if NSFW
        if rating > 0.4 or wad > 0.4 or offensive > 0.5:
            await message.delete()

            neko = await neko_image()
            mention = f"<a href=\"tg://user?id={user.id}\">{user.first_name}</a>"
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{client.me.username}?startgroup=true")]
            ])

            await message.reply_photo(
                photo=neko,
                caption=(
                    f"<b>🔞 NSFW Content Detected and Removed</b>\n\n"
                    f"👤 User: {mention} [{user.id}]\n"
                    f"🏷 Username: @{user.username if user.username else 'N/A'}\n"
                    f"📂 Content Type: {message.media.value}\n"
                    f"📍 Reason: {'Nudity' if rating > 0.4 else 'Weapon/Alcohol/Drugs' if wad > 0.4 else 'Offensive'}"
                ),
                reply_markup=buttons,
                parse_mode="html"
            )
    except Exception as e:
        pass
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# Authorization Commands
@Client.on_message(filters.command("addauth") & filters.user(OWNER_ID))
async def add_auth_user(_, message: Message):
    if not message.reply_to_message:
        return await message.reply("Reply to a user to authorize.")
    uid = message.reply_to_message.from_user.id
    await add_auth(message.chat.id, uid)
    await message.reply(f"✅ Authorized {uid} to post NSFW.")

@Client.on_message(filters.command("rmauth") & filters.user(OWNER_ID))
async def rm_auth_user(_, message: Message):
    if not message.reply_to_message:
        return await message.reply("Reply to a user to remove auth.")
    uid = message.reply_to_message.from_user.id
    await rm_auth(message.chat.id, uid)
    await message.reply(f"❌ Removed {uid} from authorized list.")
