from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
from EsproChat import app


@app.on_message(filters.command("staff") & filters.group)
async def staff_list(client: Client, message: Message):
    chat_id = message.chat.id
    admins = await client.get_chat_members(chat_id, filter=ChatMemberStatus.ADMINISTRATORS)

    founders = []
    cofounders = []
    admin_list = []

    for member in admins:
        user = member.user
        mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
        status = member.status
        custom_title = member.custom_title or ""

        if user.is_self:
            continue  # skip bot itself

        if status == ChatMemberStatus.OWNER:
            founders.append(f"👑 <b>Founder</b>\n └ {mention}")
        elif "owner" in custom_title.lower():
            cofounders.append(f" ├ {mention} » {custom_title}")
        elif "boss" in custom_title.lower() or "maharana" in custom_title.lower():
            cofounders.append(f" ├ {mention} » {custom_title}")
        elif "queen" in custom_title.lower() or "baby" in custom_title.lower():
            cofounders.append(f" ├ {mention} » {custom_title}")
        else:
            admin_list.append(f" ├ {mention} » {custom_title or user.first_name}")

    # formatting message
    staff_text = ""

    if founders:
        staff_text += "\n".join(founders) + "\n\n"
    if cofounders:
        staff_text += "⚜️ <b>Co-founders</b>\n" + "\n".join(cofounders) + "\n\n"
    if admin_list:
        staff_text += "👮🏼 <b>Admins</b>\n" + "\n".join(admin_list)

    if not staff_text:
        staff_text = "No admins found in this group."

    await message.reply_text(staff_text, parse_mode="HTML", disable_web_page_preview=True)
