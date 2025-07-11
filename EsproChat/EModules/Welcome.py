import os
from PIL import ImageDraw, Image, ImageFont, ImageChops
from pyrogram import Client, filters, enums
from pyrogram.types import *
from pyrogram.handlers import MessageHandler, ChatMemberUpdatedHandler
from logging import getLogger
from EsproChat import app

LOGGER = getLogger(__name__)

class WelDatabase:
    def __init__(self):
        self.data = {}

    async def find_one(self, chat_id):
        return chat_id in self.data

    async def add_wlcm(self, chat_id):
        self.data[chat_id] = {}

    async def rm_wlcm(self, chat_id):
        if chat_id in self.data:
            del self.data[chat_id]

wlcm = WelDatabase()

class temp:
    ME = None
    CURRENT = 2
    CANCEL = False
    MELCOW = {}
    U_NAME = None
    B_NAME = None

# ✅ Compatible circle crop function
def circle(pfp, size=(500, 500)):
    try:
        resample_filter = Image.Resampling.LANCZOS
    except AttributeError:
        resample_filter = Image.ANTIALIAS

    pfp = pfp.resize(size, resample_filter).convert("RGBA")
    bigsize = (pfp.size[0] * 3, pfp.size[1] * 3)
    mask = Image.new("R", bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(pfp.size, resample_filter)
    mask = ImageChops.darker(mask, pfp.split()[-1])
    pfp.putalpha(mask)
    return pfp

# ✅ Welcome image generator
def welcomepic(pic, user, chatname, id, uname):
    background = Image.open("EsproChat/assets/wel2.png")
    pfp = Image.open(pic).convert("RGBA")
    pfp = circle(pfp)
    pfp = pfp.resize((825, 824))

    draw = ImageDraw.Draw(background)
    font = ImageFont.truetype('EsproChat/assets/font.ttf', size=110)
    welcome_font = ImageFont.truetype('EsproChat/assets/font.ttf', size=60)

    draw.text((2100, 1420), f'ID: {id}', fill=(0, 0, 0), font=font)
    pfp_position = (1990, 435)
    background.paste(pfp, pfp_position, pfp)
    background.save(f"downloads/welcome#{id}.png")
    return f"downloads/welcome#{id}.png"

# ✅ /wel command to toggle welcome system
@app.on_message(filters.command("wel") & ~filters.private)
async def auto_state(_, message):
    usage = "**Usage:**\n⦿ /wel [on|off]\n⦿ Only admins can enable/disable welcome image."
    if len(message.command) == 1:
        return await message.reply_text(usage)

    chat_id = message.chat.id
    user = await app.get_chat_member(chat_id, message.from_user.id)
    if user.status in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
        is_enabled = await wlcm.find_one(chat_id)
        state = message.text.split(None, 1)[1].strip().lower()

        if state == "on":
            if is_enabled:
                return await message.reply_text("✅ Special Welcome is already enabled.")
            await wlcm.add_wlcm(chat_id)
            await message.reply_text(f"✅ Enabled Special Welcome in **{message.chat.title}**")

        elif state == "off":
            if not is_enabled:
                return await message.reply_text("❌ Special Welcome is already disabled.")
            await wlcm.rm_wlcm(chat_id)
            await message.reply_text(f"✅ Disabled Special Welcome in **{message.chat.title}**")

        else:
            await message.reply_text(usage)
    else:
        await message.reply_text("❌ Only group admins can use this command.")

# ✅ Welcome message handler
@app.on_chat_member_updated(filters.group, group=-3)
async def greet_group(_, member: ChatMemberUpdated):
    chat_id = member.chat.id
    is_enabled = await wlcm.find_one(chat_id)
    if not is_enabled:
        return

    if (
        not member.new_chat_member or
        member.new_chat_member.status in {"banned", "left", "restricted"} or
        member.old_chat_member
    ):
        return

    user = member.new_chat_member.user if member.new_chat_member else member.from_user
    try:
        pic = await app.download_media(user.photo.big_file_id, file_name=f"downloads/pp{user.id}.png")
    except AttributeError:
        pic = "EsproChat/assets/upic.png"

    if (temp.MELCOW).get(f"welcome-{chat_id}") is not None:
        try:
            await temp.MELCOW[f"welcome-{chat_id}"].delete()
        except Exception as e:
            LOGGER.error(e)

    try:
        welcomeimg = welcomepic(pic, user.first_name, member.chat.title, user.id, user.username or "N/A")
        temp.MELCOW[f"welcome-{chat_id}"] = await app.send_photo(
            chat_id,
            photo=welcomeimg,
            caption=f"""
**👋 Welcome to {member.chat.title}**

**Name:** {user.mention}
**ID:** `{user.id}`
**Username:** @{user.username or "N/A"}""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Me", url="https://t.me/MissEsproBot?startgroup=true")]
            ])
        )
    except Exception as e:
        LOGGER.error(e)

    try:
        os.remove(f"downloads/welcome#{user.id}.png")
        os.remove(f"downloads/pp{user.id}.png")
    except Exception:
        pass

# ✅ Bot joins new group logging (optional LOG_CHANNEL_ID)
@app.on_message(filters.new_chat_members & filters.group, group=-1)
async def bot_wel(_, message):
    for u in message.new_chat_members:
        if u.id == app.me.id:
            await app.send_message(
                LOG_CHANNEL_ID,
                f"""**🔔 New Group Joined**

**Group Name:** {message.chat.title}
**Group ID:** `{message.chat.id}`
**Username:** @{message.chat.username or "N/A"}"""
    )
