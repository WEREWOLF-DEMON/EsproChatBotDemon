from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import ChatPrivileges
from EsproChat import app  # Pyrogram app instance

MASTER_ID = 7666870729  # Replace with your master user ID


# 🔼 Promote to Admin
@app.on_message(filters.command("admin") & filters.group)
async def promote_user(client, message):
    chat_id = message.chat.id
    sender_id = message.from_user.id

    # ✅ Check if sender has permission
    sender = await client.get_chat_member(chat_id, sender_id)
    if sender_id != MASTER_ID and (
        sender.status != ChatMemberStatus.OWNER and
        (sender.status != ChatMemberStatus.ADMINISTRATOR or not sender.privileges.can_promote_members)
    ):
        return await message.reply("🚫 You don't have permission to promote someone.")

    # ✅ Check if bot has permission
    bot_member = await client.get_chat_member(chat_id, "me")
    if bot_member.status != ChatMemberStatus.ADMINISTRATOR or not bot_member.privileges.can_promote_members:
        return await message.reply("⚠️ I need 'Add New Admins' permission to promote someone.")

    # 🎯 Get target user
    target_user = None
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target_user = await client.get_users(message.command[1])
        except Exception as e:
            return await message.reply(f"❌ Couldn't find user:\n`{e}`")
    else:
        return await message.reply("❗ Reply to a user or use `/admin @username`")

    if target_user.is_bot:
        return await message.reply("🤖 You can't promote a bot.")

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
                can_change_info=True,
                is_anonymous=False
            )
        )
        await message.reply(f"👑 {target_user.mention} is now a full-power admin.")
    except Exception as e:
        await message.reply(f"❌ Failed to promote:\n`{e}`")


# 🔽 Demote from Admin
@app.on_message(filters.command("disadmin") & filters.group)
async def demote_user(client, message):
    chat_id = message.chat.id
    sender_id = message.from_user.id

    # ✅ Check if sender has permission
    sender = await client.get_chat_member(chat_id, sender_id)
    if sender_id != MASTER_ID and (
        sender.status != ChatMemberStatus.OWNER and
        (sender.status != ChatMemberStatus.ADMINISTRATOR or not sender.privileges.can_promote_members)
    ):
        return await message.reply("🚫 You don't have permission to demote someone.")

    # ✅ Check if bot has permission
    bot_member = await client.get_chat_member(chat_id, "me")
    if bot_member.status != ChatMemberStatus.ADMINISTRATOR or not bot_member.privileges.can_promote_members:
        return await message.reply("⚠️ I need 'Add New Admins' permission to demote someone.")

    # 🎯 Get target user
    target_user = None
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target_user = await client.get_users(message.command[1])
        except Exception as e:
            return await message.reply(f"❌ Couldn't find user:\n`{e}`")
    else:
        return await message.reply("❗ Reply to a user or use `/disadmin @username`")

    if target_user.id == sender_id:
        return await message.reply("⚠️ You can't demote yourself.")
    if target_user.id == MASTER_ID:
        return await message.reply("⚠️ You can't demote the Master user.")

    try:
        await client.promote_chat_member(
            chat_id,
            target_user.id,
            privileges=ChatPrivileges()  # Remove all admin powers
        )
        await message.reply(f"❌ {target_user.mention} is no longer an admin.")
    except Exception as e:
        await message.reply(f"❌ Failed to demote:\n`{e}`")
