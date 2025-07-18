from EsproChat import app
from pyrogram import Client, filters
from EsproChat.Db import get_served_chats, get_served_users, add_served_user, add_served_chat
import requests 
from Murali import Owner
from pyrogram.enums import ChatType
import random 
from config import OWNER_ID, LOGGER_ID
import asyncio
from EsproChat.Strings import HELP_BUTTON, START_TEXT, START_BUTTON
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

EMOJIOS = [
    "💣", "💥", "🪄", "🎋", "✨", "🦹", "🌺", "🍀", "💞", "🎁", "💌", "🧨", "⚡", "🤡", "👻",
    "🎃", "🎩", "🕊", "🍭", "🐻", "🦄", "🐼", "🐰", "🌸", "🌈", "🌟", "🌼", "🐱", "🐶", "🐨",
    "🐥", "🎮", "🎵", "📚", "🎨", "☕", "🍕", "🍦", "🍰", "🎈", "🎉", "🐤", "🍬"
]

STICKER = [
    "CAACAgUAAx0CfAEyWgAClxdl9Gg4N-HyCImjGFXOQSHz50MD9wACzgoAAgrrYVWxPZWXGNr8SjQE",
    "CAACAgUAAx0CfAEyWgAClx1l9Gh9PHZKDIw8qbacmxzRD1QNAAOcDQAC0YVxVQijiuf_CF8_NAQ",
    "CAACAgUAAx0CfAEyWgAClyJl9Giplzk45LHa3SWbl30VQud5sgACJAgAAkemgVWsjZK8lbezvDQE",
    "CAACAgUAAx0CfAEyWgACmzZl-DHnr2MOLOPp34onib6dzUFjZgACQAgAApt6iFXzn_VE52urQDQE",
    "CAACAgUAAx0CfAEyWgAClydl9GjEpP5YDBYtPn-g8aC55Mmw_wACyQwAApDeqFbZJHowNnvidjQE",
    "CAACAgUAAx0CbEz78AABAQsvZfP2vNspUQkhtlqbZvDVUTvtIeIAApwNAALRhXFVCKOK5_8IXz8eBA",
    "CAACAgUAAx0CffjZyQACKoZmInOTHCv5lfpO580Y_UPEeUveYAAClAgAAspLwVT1oL4z_bhK7x4E",
    "CAACAgUAAx0CffjZyQACKo5mInRgNfyhH-Y3tKwKyj4_RoKu9gACsgYAAtAF2VYY6HZG8DUiyh4E",
    "CAACAgUAAx0CffjZyQACKoVmInNNz2YqgVIOm0b_XNASdarg0QAC9QkAAlTOgFSpIzlJ8dofZR4E",
-   "CAACAgUAAx0CffjZyQACKohmInOZTlDo3YUTGWNdt1-8QFvrhQACqgwAArC9oFRVcuyU8PCqFR4E",
    "CAACAgUAAx0CffjZyQACKopmInPJwawFfy9z96S23cRxc5iI3QACegsAAtFEoVSKNlWkZeVvBh4E",
    "CAACAgUAAx0CffjZyQACKodmInOY37YoG7I-Mn9VbHbcE1VkYgACWAcAAmF4oFRci8T1o_XfEh4E",
    "CAACAgUAAx0CffjZyQACKotmInP5P_GvgKU67nB3ZXDU5UHdwQACBAkAAmGTqFTyMEUMwHr2WB4E",
    "CAACAgUAAx0CfAEyWgAClyxl9GkdhdvG8gmelpuDDXW43GdyYgACDAkAAgYmmVWwda82o5ssVx4E",

]

PHOTOS = [
    "https://telegra.ph/file/018d6002a0ad3aee739f4.jpg",
    "https://telegra.ph/file/9d1b413d24ef703e931e3.jpg",
    "https://telegra.ph/file/035f1b9835c47f45952f7.jpg",
    "https://telegra.ph/file/ca93aeef2e7b45918b668.jpg",
    "https://telegra.ph/file/be64889b9a092f05bb51e.jpg",
]

# Corrected startbot function with proper timing and sequence
@app.on_cmd("start")
async def startbot(client, message):
    try:
        # Step 1: Send the initial welcome photo
        imgg = await message.reply_photo(
            photo=random.choice(PHOTOS),
            caption=f"Hᴇʟʟᴏ {message.from_user.mention} 👋"
        )
        await asyncio.sleep(1.5) # Wait for 1.5 seconds

        # Step 2: Send the "let me start" message and edit it for animation
        let = await message.reply_text("ʟᴇᴛ ᴍᴇ sᴛᴀʀᴛ...")
        await asyncio.sleep(1) # Wait for 1 second
        await let.edit("ᴘʀᴇᴘᴀʀɪɴɢ ᴛʜᴇ ᴍᴀɢɪᴄ ✨")
        await asyncio.sleep(1.5) # Wait for 1.5 seconds

        # Step 3: Clean up the initial messages before the main content
        await imgg.delete()
        await let.delete()

        # Step 4: Quick animation with an emoji and a sticker
        emoji_msg = await message.reply_text(random.choice(EMOJIOS))
        await asyncio.sleep(0.8) # Wait for 0.8 seconds
        await emoji_msg.delete()

        sticker_msg = await message.reply_sticker(random.choice(STICKER))
        await asyncio.sleep(0.8) # Wait for 0.8 seconds
        await sticker_msg.delete()

        # Step 5: Send the final start message
        try:
            await app.resolve_peer(OWNER_ID[0])
            OWNER = OWNER_ID[0]
        except:
            OWNER = OWNER_ID[0]
            
        M = START_BUTTON(OWNER)
        response = requests.get("https://nekos.best/api/v2/neko").json()
        image_url = response["results"][0]["url"]
        await message.reply_photo(
            image_url,
            caption=START_TEXT.format(message.from_user.mention, app.mention),
            reply_markup=M,
        )

        # Step 6: Handle database and logging in the background
        try:
            if message.chat.type == ChatType.PRIVATE:
                await add_served_user(message.from_user.id)
            else:
                await add_served_chat(message.chat.id)
        except:
            pass
            
        await app.send_message(LOGGER_ID, f"ꜱᴏᴍᴇᴏɴᴇ ᴊᴜꜱᴛ ꜱᴛᴀʀᴛᴇᴅ {app.mention}\n\nɴᴀᴍᴇ - {message.from_user.mention}\nɪᴅ - {message.from_user.id}\nᴜꜱᴇʀɴᴀᴍᴇ - @{message.from_user.username}")

    except Exception as e:
        # If anything goes wrong, log the error
        print(f"Error in /start command: {e}")


@app.on_cmd("stats")
async def statsbot(client, message):
    if message.from_user.id not in Owner and message.from_user.id not in OWNER_ID:
        return

    response = requests.get("https://nekos.best/api/v2/neko").json()
    m = response["results"][0]["url"]
    users = len(await get_served_users())
    chats = len(await get_served_chats())
    await message.reply_photo(
        photo=m,
        caption=f"""ʜᴇʀᴇ ɪꜱ ᴛʜᴇ ᴛᴏᴛᴀʟ ꜱᴛᴀᴛꜱ ᴏꜰ {app.mention}:

➻ ᴄʜᴀᴛs : {chats}
➻ ᴜsᴇʀs : {users}
"""
    )
