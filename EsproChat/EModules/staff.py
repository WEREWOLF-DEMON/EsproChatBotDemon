from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus, ChatMembersFilter
from EsproChat import app

@app.on_message(filters.command("staff") & filters.group)
async def staff_list(client: Client, message: Message):
    chat_id = message.chat.id

    owners = []
    admins = []

    async for member in client.get_chat_members(chat_id, filter=ChatMembersFilter.ADMINISTRATORS):
        user = member.user
        if user.is_bot:
            continue

        if member.status == ChatMemberStatus.OWNER:
            owners.append(user.mention)
        elif member.status == ChatMemberStatus.ADMINISTRATOR:
            admins.append(user.mention)

    # Format message
    staff_text = "👮‍♂️ **Group Staff List:**\n\n"

    if owners:
        staff_text += "**👑 Owner(s):**\n"
        for owner in owners:
            staff_text += f"• {owner}\n"
        staff_text += "\n"

    if admins:
        staff_text += "**🛡️ Admin(s):**\n"
        for admin in admins:
            staff_text += f"• {admin}\n"

    await message.reply_text(staff_text)
