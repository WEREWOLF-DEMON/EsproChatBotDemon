import aiohttp
import os
from EsproChat import app
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, SIGHTENGINE_API_USER, SIGHTENGINE_API_SECRET, AUTH_USERS

nekos_api = "https://nekos.best/api/v2/neko"

# ✅ Dynamic authorized user list
authorized_users = set(6656608288)

async def check_nsfw(file_path: str):
    """Check media using Sightengine API and return result JSON."""
    url = f"https://api.sightengine.com/1.0/check.json?models=nudity,wad,offensive,text-content&api_user={SIGHTENGINE_API_USER}&api_secret={SIGHTENGINE_API_SECRET}"
    try:
        async with aiohttp.ClientSession() as session:
            with open(file_path, "rb") as f:
                form = aiohttp.FormData()
                form.add_field("media", f, filename="file.jpg")
                async with session.post(url, data=form) as resp:
                    return await resp.json()
    except Exception as e:
        print("Sightengine API error:", e)
        return None

async def get_neko_image():
    """Fetch neko image for stylish response."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(nekos_api) as r:
                neko_json = await r.json()
                return neko_json["results"][0]["url"]
    except:
        return "https://nekos.best/api/v2/neko/0001.png"

# ✅ Main NSFW Detection Handler
@app.on_message(filters.group & (filters.photo | filters.video | filters.animation | filters.sticker))
async def nsfw_guard(client, message: Message):
    user = message.from_user
    if not user:
        return

    # ✅ Skip OWNER and Authorized Users
    if user.id == OWNER_ID or user.id in authorized_users:
        return

    # ✅ Download media
    try:
        file_path = await message.download()
    except:
        return

    # ✅ Scan file with Sightengine
    result = await check_nsfw(file_path)
    if not result:
        return

    nudity = result.get("nudity", {}).get("raw", 0)
    weapon = result.get("weapon", {}).get("prob", 0)
    alcohol = result.get("alcohol", {}).get("prob", 0)
    drugs = result.get("drugs", {}).get("prob", 0)
    offensive = result.get("offensive", {}).get("prob", 0)

    # ✅ If any detection > 70%, delete
    if any(x > 0.7 for x in [nudity, weapon, alcohol, drugs, offensive]):
        try:
            await message.delete()
        except:
            print("Delete failed: Bot needs admin rights with delete permission")
            return

        neko_img = await get_neko_image()
        caption = (
            f"🚫 **NSFW Content Deleted**\n\n"
            f"👤 User: {user.mention}\n"
            f"🆔 ID: `{user.id}`\n"
            f"🔍 **Ratings:**\n"
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
                    [[InlineKeyboardButton("➕ Add Me To Your Group", url=f"https://t.me/{client.me.username}?startgroup=true")]]
                )
            )
        except:
            await message.reply(caption)

    # ✅ Remove temp file
    try:
        os.remove(file_path)
    except:
        pass

# ✅ Owner Command to Authorize User
@app.on_message(filters.command("authorize") & filters.user(OWNER_ID))
async def authorize_user(client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.reply("Reply to a user's message to authorize them.")
    user_id = message.reply_to_message.from_user.id
    authorized_users.add(user_id)
    await message.reply(f"✅ User `{user_id}` has been authorized.")

# ✅ Owner Command to Unauthorize User
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
