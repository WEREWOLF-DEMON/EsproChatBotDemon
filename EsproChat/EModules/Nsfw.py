import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, AUTH_USERS, SIGHTENGINE_API_USER, SIGHTENGINE_API_SECRET
import random

nekos_api = "https://nekos.best/api/v2/neko"

# Authorized users list (dynamic)
authorized_users = set(AUTH_USERS)

# Filter NSFW content in groups
@Client.on_message(filters.group & filters.media & ~filters.command)
async def nsfw_guard(client: Client, message: Message):
    user = message.from_user
    if not user:
        return

    user_id = user.id
    if user_id != OWNER_ID and user_id not in authorized_users:
        return

    # Check media type
    file = None
    if message.photo:
        file = await message.download()
    elif message.sticker and not message.sticker.is_animated:
        file = await message.download()
    elif message.video:
        file = await message.download()
    elif message.animation:
        file = await message.download()
    elif message.document and message.document.mime_type.startswith("image"):
        file = await message.download()
    else:
        return

    # Scan using Sightengine
    try:
        async with aiohttp.ClientSession() as session:
            with open(file, "rb") as f:
                data = aiohttp.FormData()
                data.add_field("media", f, filename="image.jpg")
                url = f"https://api.sightengine.com/1.0/check.json?models=nudity,wad,offensive,text-content&api_user={SIGHTENGINE_API_USER}&api_secret={SIGHTENGINE_API_SECRET}"
                async with session.post(url, data=data) as resp:
                    result = await resp.json()

        # Check probabilities
        nudity = result.get("nudity", {}).get("raw", 0)
        weapon = result.get("weapon", {}).get("prob", 0)
        alcohol = result.get("alcohol", {}).get("prob", 0)
        drugs = result.get("drugs", {}).get("prob", 0)
        offensive = result.get("offensive", {}).get("prob", 0)

        if any(x > 0.7 for x in [nudity, weapon, alcohol, drugs, offensive]):
            await message.delete()

            # Get neko image
            async with aiohttp.ClientSession() as session:
                async with session.get(nekos_api) as r:
                    neko_json = await r.json()
                    neko_url = neko_json["results"][0]["url"]

            text = f"🚫 **NSFW Content Detected & Deleted**\n\n" \
                   f"👤 User: {user.mention} ({user.id})\n" \
                   f"🧾 Username: @{user.username if user.username else 'N/A'}\n" \
                   f"📎 Type: {message.media}\n" \
                   f"🔞 Rating: Nudity({nudity*100:.1f}%), Weapon({weapon*100:.1f}%), Alcohol({alcohol*100:.1f}%), Drugs({drugs*100:.1f}%), Offensive({offensive*100:.1f}%)"

            await message.reply_photo(
                photo=neko_url,
                caption=text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add Me To Your Group", url=f"https://t.me/{client.me.username}?startgroup=true")]
                ])
            )
    except Exception as e:
        print("NSFW scan error:", e)


# Admin commands to authorize/remove users
@Client.on_message(filters.command("authorize") & filters.user(OWNER_ID))
async def authorize_user(client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.reply("Reply to a user's message to authorize them.")
    user_id = message.reply_to_message.from_user.id
    authorized_users.add(user_id)
    await message.reply(f"✅ User `{user_id}` has been authorized.")


@Client.on_message(filters.command("unauthorize") & filters.user(OWNER_ID))
async def unauthorize_user(client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.reply("Reply to a user's message to remove authorization.")
    user_id = message.reply_to_message.from_user.id
    if user_id in authorized_users:
        authorized_users.remove(user_id)
        await message.reply(f"❌ User `{user_id}` authorization removed.")
    else:
        await message.reply("User is not authorized.")
