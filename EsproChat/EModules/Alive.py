from EsproChat import app
from pyrogram import client, Client, filters 
import requests
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from EsproChat.EModules.Ping import get_readable_time
import time
from pyrogram.types import Message
from pyrogram.enums import ChatMembersFilter

_boot_ = time.time()

@app.on_cmd("alive")
async def alive(client, message):
    response = requests.get("https://nekos.best/api/v2/neko").json()
    M = response["results"][0]["url"]
    bot_uptime = int(time.time() - _boot_)
    Uptime = f"{get_readable_time(bot_uptime)}"
    await message.reply_photo(M, caption=f"{app.mention} ɪꜱ ꜱᴛɪʟʟ ᴀʟɪᴠᴇ ʙᴀʙʏ ❤️\n\nɪ ᴅɪᴅɴ'ᴛ ꜱʟᴇᴘᴛ ꜰʀᴏᴍ {Uptime} ", reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ 💓",
                        url=f"https://t.me/{app.username}?startgroup=true",
                    ),
                ],
            ]
    ))


