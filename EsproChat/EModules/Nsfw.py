import aiohttp
import os
from collections import defaultdict
from EsproChat import app
from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, SIGHTENGINE_API_USER, SIGHTENGINE_API_SECRET, AUTH_USERS

# ✅ Config
nekos_api = "https://nekos.best/api/v2/neko"
authorized_users = set(AUTH_USERS)
nsfw_enabled = defaultdict(lambda: True)  # Default ON for all groups
user_spam_tracker = defaultdict(int)
user_messages = defaultdict(list)

# ✅ Fetch random neko image
async def get_neko_image():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(nekos_api, timeout=10) as r:
                if r.status == 200:
                    data = await r.json()
                    return data["results"][0]["url"]
    except:
        return "https://nekos.best/api/v2/neko/0001.png"

# ✅ Sightengine API for NSFW Check
async def check_nsfw(file_path: str):
    url = "https://api.sightengine.com/1.0/check.json"
    try:
        async with aiohttp.ClientSession() as session:
            with open(file_path, "rb") as f:
                form = aiohttp.FormData()
                form.add_field("media", f, filename="file.jpg", content_type="image/jpeg")
                form.add_field("models", "nudity,wad,offensive")
                form.add_field("api_user", SIGHTENGINE_API_USER)
                form.add_field("api_secret", SIGHTENGINE_API_SECRET)
                async with session.post(url, data=form, timeout=25) as resp:
                    return await resp.json()
    except Exception as e:
        print(f"[ERROR] Sightengine API: {e}")
        return None

# ✅ Delete all messages of a user in memory
async def delete_user_messages(client, chat_id, user_id):
    if user_messages[(chat_id, user_id)]:
        for msg_id in user_messages[(chat_id, user_id)]:
            try:
                await client.delete_messages(chat_id, msg_id)
            except:
                pass
        user_messages[(chat_id, user_id)].clear()

# ✅ Main NSFW Detector (Photo, Video, GIF, Stickers, Video Stickers)
@app.on_message(filters.group & (filters.photo | filters.video | filters.animation | filters.sticker))
async def nsfw_guard(client, message: Message):
    chat_id = message.chat.id
    user = message.from_user
    if not user:
        return

    # ✅ Ignore commands with media
    if message.caption and message.caption.startswith("/"):
        return

    # ✅ Track user messages
    user_messages[(chat_id, user.id)].append(message.id)
    if len(user_messages[(chat_id, user.id)]) > 20:
        user_messages[(chat_id, user.id)].pop(0)

    # ✅ Skip if feature is off
    if not nsfw_enabled[chat_id]:
        return

    # ✅ Skip owner & authorized users
    if user.id == OWNER_ID or user.id in authorized_users:
        return

    # ✅ Skip safe stickers (emojis, small tgs)
    if message.sticker and not message.sticker.is_video and not message.sticker.is_animated:
        return  # Normal static stickers are usually safe

    # ✅ Download media (photo, video, gif, video sticker)
    try:
        file_path = await message.download()
    except:
        return

    # ✅ Check NSFW
    result = await check_nsfw(file_path)
    try:
        os.remove(file_path)
    except:
        pass

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

    # ✅ Strong NSFW detection logic
    is_nsfw = (
        nudity > 0.6 or
        partial > 0.6 or
        sexual > 0.3 or
        weapon > 0.8 or
        alcohol > 0.8 or
        drugs > 0.6 or
        offensive > 0.7
    )

    if is_nsfw:
        # ✅ Increase spam counter
        user_spam_tracker[user.id] += 1

        # ✅ Delete all messages from this user (FAST)
        await delete_user_messages(client, chat_id, user.id)

        # ✅ Stylish NSFW alert
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

        try:
            await message.reply_photo(
                photo=neko_img,
                caption=caption,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{client.me.username}?startgroup=true")]]
                )
            )
        except:
            await message.reply(caption)
