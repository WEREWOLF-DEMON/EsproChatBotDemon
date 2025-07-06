import os
from PIL import ImageDraw, Image, ImageFont, ImageChops
from pyrogram import *
from pyrogram.types import *
from logging import getLogger
from EsproChat import app

LOGGER = getLogger(__name__)

# In-memory welcome database
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

# Create a circular version of the user's profile photo
def circle(pfp, size=(500, 500)):
    pfp = pfp.resize(size, Image.Resampling.LANCZOS).convert("RGBA")
    bigsize = (pfp.size[0] * 3, pfp.size[1] * 3)
    mask = Image.new("L", bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(pfp.size, Image.Resampling.LANCZOS)
    mask = ImageChops.darker(mask, pfp.split()[-1])
    pfp.putalpha(mask)
    return pfp

# Generate the welcome image with user info and group title
def welcomepic(pic, user, chatname, id, uname):
    os.makedirs("downloads", exist_ok=True)
    background = Image.open("EsproChat/assets/wel2.png")
    pfp = Image.open(pic).convert("RGBA")
    pfp = circle(pfp)
    pfp = pfp.resize((825, 824))
    draw = ImageDraw.Draw(background)
    font = ImageFont.truetype('EsproChat/assets/font.ttf', size=110)
    draw.text((2100, 1420), f'ID: {id}', fill=(255, 255, 255), font=font)
    pfp_position = (1990, 435)
    background.paste(pfp, pfp_position, pfp)
    output_path = f"downloads/welcome#{id}.png"
    background.save(output_path)
    return output_path

# Enable or disable special welcome
@app.on_message(filters.command("wel") & ~filters.private)
async def auto_state(_, message):
    usage = "**Usage:**\n⦿ /wel [on|off]\nOnly admins can use this command."
    if len(message.command) == 1:
        return await message.reply_text(usage)

    chat_id = message.chat.id
    user = await app.get_chat_member(chat_id, message.from_user.id)

    if user.status in (
        enums.ChatMemberStatus.ADMINISTRATOR,
        enums.ChatMemberStatus.OWNER,
    ):
        current = await wlcm.find_one(chat_id)
        state = message.text.split(None, 1)[1].strip().lower()

        if state == "on":
            if current:
                return await message.reply_text("Special Welcome Already Enabled")
            await wlcm.add_wlcm(chat_id)
            await message.reply_text(f"✅ Enabled Special Welcome in {message.chat.title}")

        elif state == "off":
            if not current:
                return await message.reply_text("Special Welcome Already Disabled")
            await wlcm.rm_wlcm(chat_id)
            await message.reply_text(f"❌ Disabled Special Welcome in {message.chat.title}")

        else:
            await message.reply_text(usage)
    else:
        await message.reply("🚫 Only admins can use this command.")

# Send welcome image when a new member joins (chat_member_updated handler)
@app.on_chat_member_updated(filters.group, group=-3)
async def greet_group(_, member: ChatMemberUpdated):
    chat_id = member.chat.id
    A = await wlcm.find_one(chat_id)
    if not A:
        return

    if (
        not member.new_chat_member
        or member.new_chat_member.status in {"banned", "left", "restricted"}
        or member.old_chat_member
    ):
        return

    user = member.new_chat_member.user if member.new_chat_member else member.from_user

    try:
        pic = await app.download_media(user.photo.big_file_id, file_name=f"downloads/pp{user.id}.png")
    except AttributeError:
        pic = "EsproChat/assets/upic.png"

    if temp.MELCOW.get(f"welcome-{member.chat.id}") is not None:
        try:
            await temp.MELCOW[f"welcome-{member.chat.id}"].delete()
        except Exception as e:
            LOGGER.exception("Failed to delete old welcome message:", exc_info=e)

    try:
        welcomeimg = welcomepic(pic, user.first_name, member.chat.title, user.id, user.username)
        temp.MELCOW[f"welcome-{member.chat.id}"] = await app.send_photo(
            chat_id,
            photo=welcomeimg,
            caption=f"""
**Wᴇʟᴄᴏᴍᴇ Tᴏ {member.chat.title}**
━━━━━━━━━━━━━━━━━━━━
**Nᴀᴍᴇ:** {user.mention}
**Iᴅ:** `{user.id}`
**Usᴇʀɴᴀᴍᴇ:** @{user.username if user.username else "N/A"}
━━━━━━━━━━━━━━━━━━━━
""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⦿ ᴀᴅᴅ ᴍᴇ ⦿", url="https://t.me/EsproChatBot?startgroup=true")]
            ])
        )
    except Exception as e:
        LOGGER.exception("Error while sending welcome image:", exc_info=e)

    try:
        os.remove(f"downloads/welcome#{user.id}.png")
        os.remove(f"downloads/pp{user.id}.png")
    except Exception:
        pass

# Inform when bot is added to a group
@app.on_message(filters.new_chat_members & filters.group, group=-1)
async def bot_wel(_, message):
    for u in message.new_chat_members:
        if u.id == app.me.id:
            await app.send_message(LOG_CHANNEL_ID, f"""
**NEW GROUP ADDED**
━━━━━━━━━━━━━━━━━━━━
**NAME:** {message.chat.title}
**ID:** `{message.chat.id}`
**USERNAME:** @{message.chat.username if message.chat.username else "N/A"}
━━━━━━━━━━━━━━━━━━━━
""")
