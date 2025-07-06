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


@app.on_message(filters.command("staff") & filters.group)
async def staff_list(client: Client, message: Message):
    chat_id = message.chat.id
    staff_text = "👮‍♂️ **Group Staff List:**\n\n"

    async for member in client.get_chat_members(chat_id, filter=ChatMembersFilter.ADMINISTRATORS):
        user = member.user
        if user.is_bot:
            continue
        status = "👑 Owner" if member.status == "creator" else "🛡️ Admin"
        staff_text += f"{status} - {user.mention}\n"

    await message.reply_text(staff_text)
