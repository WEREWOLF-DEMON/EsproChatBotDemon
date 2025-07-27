import aiohttp
import os
from collections import defaultdict
from EsproChat import app
from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, SIGHTENGINE_API_USER, SIGHTENGINE_API_SECRET, AUTH_USERS

nekos_api = "https://nekos.best/api/v2/neko"
authorized_users = set(AUTH_USERS)
nsfw_enabled = {}  # ✅ Per-group NSFW toggle
user_spam_tracker = defaultdict(int)  # ✅ Spam count
user_messages = defaultdict(list)  # ✅ Store user messages for bulk delete

# ✅ Fetch neko image
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
    url = "https://api.sightengine.com/1.0/check.json"
    try:
        async with aiohttp.ClientSession() as session:
            with open(file_path, "rb") as f:
                form = aiohttp.FormData()
                form.add_field("media", f, filename="file.jpg", content_type="image/jpeg")
                form.add_field("models", "nudity,wad,offensive,text-content")
                form.add_field("api_user", SIGHTENGINE_API_USER)
                form.add_field("api_secret", SIGHTENGINE_API_SECRET)
                async with session.post(url, data=form, timeout=30) as resp:
                    return await resp.json()
    except Exception as e:
        print(f"[ERROR] Sightengine API: {e}")
        return None

# ✅ Delete all tracked messages of a user
async def delete_user_messages(client, chat_id, user_id):
    if user_messages[(chat_id, user_id)]:
        for msg_id in user_messages[(chat_id, user_id)]:
            try:
                await client.delete_messages(chat_id, msg_id)
            except:
                pass
        user_messages[(chat_id, user_id)].clear()

# ✅ NSFW Detection Handler
@app.on_message(filters.group & (filters.photo | filters.video | filters.animation | filters.sticker))
async def nsfw_guard(client, message: Message):
    if message.caption and message.caption.startswith("/"):  # Ignore commands with media
        return

    chat_id = message.chat.id
    user = message.from_user
    if not user:
        return

    # ✅ Track user's message for deletion
    user_messages[(chat_id, user.id)].append(message.id)
    if len(user_messages[(chat_id, user.id)]) > 20:
        user_messages[(chat_id, user.id)].pop(0)  # Keep last 20 only

    # ✅ Skip if feature disabled
    if not nsfw_enabled.get(chat_id, True):
        return

    # ✅ Skip owner/admin/authorized
    if user.id == OWNER_ID or user.id in authorized_users:
        return

    # ✅ Track spam
    user_spam_tracker[user.id] += 1
    if user_spam_tracker[user.id] > 3:
        await delete_user_messages(client, chat_id, user.id)
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

    nudity = float(result.get("nudity", {}).get("raw", 0))
    weapon = float(result.get("weapon", 0))
    alcohol = float(result.get("alcohol", 0))
    drugs = float(result.get("drugs", 0))
    offensive = float(result.get("offensive", {}).get("prob", 0))

    if any(x > 0.7 for x in [nudity, weapon, alcohol, drugs, offensive]):
        # ✅ Delete all user messages fast
        await delete_user_messages(client, chat_id, user.id)

        # ✅ Send stylish alert
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

# ✅ Enable / Disable NSFW Filter
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

# ✅ Owner Commands for User Whitelist
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
