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
async def staff_list(client, message: Message):
    chat_id = message.chat.id
    staff_text = "<b>🌐 GROUP STAFF</b>\n\n"

    founder = None
    admins = []

    async for member in client.get_chat_members(chat_id, filter="administrators"):
        user = member.user
        name = f"<a href='https://t.me/{user.username}'>{user.mention}</a>" if user.username else user.mention

        if member.status == "owner":
            founder = f"👑 <b>Founder</b>\n └ {name}\n"
        else:
            admins.append(f" ├ {name}")

    admin_text = "👮 <b>Admins</b>\n" + "\n".join(admins) if admins else "No admins found."

    full_text = staff_text + (founder or "👑 <b>Founder</b>\n └ Unknown\n") + "\n" + admin_text
    await message.reply_text(full_text, parse_mode="html", disable_web_page_preview=True)
