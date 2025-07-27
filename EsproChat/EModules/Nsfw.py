import aiohttp
import os
import asyncio
from EsproChat import app
from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, SIGHTENGINE_API_USER, SIGHTENGINE_API_SECRET, AUTH_USERS

nekos_api = "https://nekos.best/api/v2/neko"
authorized_users = set(AUTH_USERS)
nsfw_enabled = {}  # ✅ Per-group NSFW toggle
user_spam_tracker = {}  # ✅ Track spam uploads


# ✅ Fetch Neko image (fallback if API fails)
async def get_neko_image():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(nekos_api, timeout=10) as r:
                if r.status == 200:
                    data = await r.json()
                    return data["results"][0]["url"]
    except:
        pass
    return "https://nekos.best/api/v2/neko/0001.png"


# ✅ Sightengine NSFW Check
async def check_nsfw(file_path: str):
    url = f"https://api.sightengine.com/1.0/check.json"
    data = {
        "models": "nudity,wad,offensive,text-content",
        "api_user": SIGHTENGINE_API_USER,
        "api_secret": SIGHTENGINE_API_SECRET
    }
    try:
        async with aiohttp.ClientSession() as session:
            with open(file_path, "rb") as f:
                form = aiohttp.FormData()
                form.add_field("media", f, filename="file.jpg", content_type="image/jpeg")
                async with session.post(url, data=form, timeout=20) as resp:
                    return await resp.json()
    except Exception as e:
        print(f"[ERROR] Sightengine API: {e}")
        return None


# ✅ NSFW Detection Handler
@app.on_message(filters.group & (filters.photo | filters.video | filters.animation | filters.sticker))
async def nsfw_guard(client, message: Message):
    if message.caption and message.caption.startswith("/"):  # ✅ Ignore commands with media
        return

    chat_id = message.chat.id
    user = message.from_user
    if not user:
        return

    # ✅ Skip if feature disabled
    if not nsfw_enabled.get(chat_id, True):
        return

    # ✅ Skip owner/admin/authorized
    if user.id == OWNER_ID or user.id in authorized_users:
        return

    # ✅ Track spam
    user_spam_tracker[user.id] = user_spam_tracker.get(user.id, 0) + 1
    if user_spam_tracker[user.id] > 3:
        try:
            async for m in client.search_messages(chat_id, from_user=user.id, limit=10):
                await m.delete()
        except:
            pass
        user_spam_tracker[user.id] = 0
        return

    # ✅ Download file
    try:
        file_path = await message.download()
    except:
        return

    result = await check_nsfw(file_path)
    try:
        os.remove(file_path)
    except:
        pass

    if not result:
        return

    # ✅ Extract safe values
    nudity = float(result.get("nudity", {}).get("raw", 0))
    weapon = float(result.get("weapon", 0))
    alcohol = float(result.get("alcohol", 0))
    drugs = float(result.get("drugs", 0))
    offensive = float(result.get("offensive", {}).get("prob", 0))

    # ✅ Delete if NSFW > 70%
    if any(x > 0.7 for x in [nudity, weapon, alcohol, drugs, offensive]):
        try:
            await message.delete()
        except:
            print("No admin rights to delete")
            return

        neko_img = await get_neko_image()
        media_type = "Photo" if message.photo else "Video" if message.video else "GIF" if message.animation else "Sticker"

        caption = (
            f"🚫 **NSFW Content Removed**\n\n"
            f"👤 User: {user.mention}\n"
            f"🆔 ID: `{user.id}`\n"
            f"📎 Type: `{media_type}`\n"
            f"🔍 **Scores:**\n"
            f"Nudity: `{nudity*100:.1f}%`\n"
            f"Weapon: `{weapon*100:.1f}%`\n"
            f"Alcohol: `{alcohol*100:.1f}%`\n"
            f"Drugs: `{drugs*100:.1f}%`\n"
            f"Offensive: `{offensive*100:.1f}%`"
        )

        # ✅ Send stylish response
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


# ✅ NSFW Toggle Command
@app.on_message(filters.command("nsfw") & filters.group)
async def toggle_nsfw(client, message: Message):
    user = await client.get_chat_member(message.chat.id, message.from_user.id)
    if user.status not in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
        return await message.reply("❌ Only group admins can change NSFW settings.")

    if len(message.command) < 2:
        return await message.reply("Usage: `/nsfw on` or `/nsfw off`")

    state = message.command[1].lower()
    nsfw_enabled[message.chat.id] = (state == "on")
    await message.reply(f"✅ NSFW filter is now **{'enabled' if state == 'on' else 'disabled'}**.")


# ✅ Owner Authorization Commands
@app.on_message(filters.command("authorize") & filters.user(OWNER_ID))
async def authorize_user(client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.reply("Reply to a user's message to authorize them.")
    user_id = message.reply_to_message.from_user.id
    authorized_users.add(user_id)
    await message.reply(f"✅ User `{user_id}` has been authorized.")


@app.on_message(filters.command("unauthorize") & filters.user(OWNER_ID))
async def unauthorize_user(client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.reply("Reply to a user's message to remove authorization.")
    user_id = message.reply_to_message.from_user.id
    if user_id in authorized_users:
        authorized_users.remove(user_id)
        await message.reply(f"❌ User `{user_id}` authorization removed.")
    else:
        await message.reply("User is not authorized.")
