from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import ChatPrivileges
from EsproChat import app  # Use your bot instance here

# 🔐 Master ID who can always promote/demote users
MASTER_ID = 7666870729


# ✅ Promote User to Full Admin
@app.on_message(filters.command("admin") & filters.group)
async def promote_user(client, message):
    if not message.reply_to_message:
        return await message.reply("❗ Reply to the user you want to promote as admin.")

    chat_id = message.chat.id
    sender_id = message.from_user.id
    sender = await client.get_chat_member(chat_id, sender_id)

    # Permission check — allow if MASTER_ID or has promote rights
    if sender_id != MASTER_ID and (
        sender.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]
        or not sender.privileges.can_promote_members
    ):
        return await message.reply("🚫 You don't have permission to promote someone.")

    target_user = message.reply_to_message.from_user

    try:
        await client.promote_chat_member(
            chat_id,
            target_user.id,
            privileges=ChatPrivileges(
                can_manage_chat=True,
                can_delete_messages=True,
                can_restrict_members=True,
                can_promote_members=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_manage_video_chats=True,
                can_post_messages=True,
                can_edit_messages=True,
                can_manage_topics=True,
                can_change_info=True,
                is_anonymous=False  # Set True if you want the admin to appear as bot
            )
        )
        await message.reply(f"👑 {target_user.mention} is now a full-power admin.")
    except Exception as e:
        await message.reply(f"❌ Failed to promote:\n`{e}`")


# ❌ Demote User from Admin
@app.on_message(filters.command("disadmin") & filters.group)
async def demote_user(client, message):
    if not message.reply_to_message:
        return await message.reply("❗ Reply to the admin you want to demote.")

    chat_id = message.chat.id
    sender_id = message.from_user.id
    sender = await client.get_chat_member(chat_id, sender_id)

    # Permission check — allow if MASTER_ID or has promote rights
    if sender_id != MASTER_ID and (
        sender.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]
        or not sender.privileges.can_promote_members
    ):
        return await message.reply("🚫 You don't have permission to demote someone.")

    target_user = message.reply_to_message.from_user

    try:
        await client.promote_chat_member(
            chat_id,
            target_user.id,
            privileges=ChatPrivileges()  # Remove all rights
        )
        await message.reply(f"❌ {target_user.mention} is no longer an admin.")
    except Exception as e:
        await message.reply(f"❌ Failed to demote:\n`{e}`")
