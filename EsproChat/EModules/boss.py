from pyrogram import filters
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatPrivileges
)
from pyrogram.enums import ChatMemberStatus
from EsproChat import app  # Your Pyrogram app instance

# 👑 Master user who has all rights
MASTER_ID = 7666870729

# 🧠 Temporary permission state
# Format: {(chat_id, user_id): {"target_id": int, "permissions": set(), "mode": "promote"/"demote"}}
PERMISSION_SELECTION = {}

# ⬆️ Promote command
@app.on_message(filters.command("admin") & filters.group)
async def admin_command(client, message: Message):
    chat_id = message.chat.id
    sender_id = message.from_user.id

    if not message.reply_to_message:
        return await message.reply("❗ Reply to the user you want to promote.")

    sender = await client.get_chat_member(chat_id, sender_id)
    if sender.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR] and sender_id != MASTER_ID:
        return await message.reply("🚫 You are not allowed to promote users.")

    target = message.reply_to_message.from_user
    if target.is_bot:
        return await message.reply("🤖 You can't promote bots.")

    PERMISSION_SELECTION[(chat_id, sender_id)] = {
        "target_id": target.id,
        "permissions": set(),
        "mode": "promote"
    }

    await message.reply(
        f"🛠️ Select permissions to GIVE to {target.mention} ↓",
        reply_markup=permission_buttons(chat_id, sender_id)
    )

# ⬇️ Demote command
@app.on_message(filters.command("disadmin") & filters.group)
async def disadmin_command(client, message: Message):
    chat_id = message.chat.id
    sender_id = message.from_user.id

    if not message.reply_to_message:
        return await message.reply("❗ Reply to the admin you want to demote.")

    sender = await client.get_chat_member(chat_id, sender_id)
    if sender.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR] and sender_id != MASTER_ID:
        return await message.reply("🚫 You are not allowed to demote users.")

    target = message.reply_to_message.from_user
    member = await client.get_chat_member(chat_id, target.id)

    if member.status != ChatMemberStatus.ADMINISTRATOR:
        return await message.reply("❗ The user is not an admin.")

    PERMISSION_SELECTION[(chat_id, sender_id)] = {
        "target_id": target.id,
        "permissions": set(),
        "mode": "demote"
    }

    await message.reply(
        f"🧹 Select permissions to REMOVE from {target.mention} ↓",
        reply_markup=permission_buttons(chat_id, sender_id)
    )

# 🔘 Generate permission buttons
def permission_buttons(chat_id, sender_id):
    perm_labels = [
        ("delete", "Delete"),
        ("pin", "Pin"),
        ("invite", "Invite"),
        ("restrict", "Restrict"),
        ("promote", "Promote"),
        ("video", "Video"),
        ("info", "Info"),
        ("manage", "Manage"),
        ("anon", "Anonymous")
    ]

    current = PERMISSION_SELECTION.get((chat_id, sender_id), {}).get("permissions", set())
    buttons = []

    for i in range(0, len(perm_labels), 2):
        row = []
        for key, label in perm_labels[i:i+2]:
            emoji = "✅" if key in current else "❌"
            row.append(InlineKeyboardButton(f"{emoji} {label}", callback_data=f"perm|{key}"))
        buttons.append(row)

    buttons.append([InlineKeyboardButton("✅ Confirm", callback_data="perm|confirm")])
    return InlineKeyboardMarkup(buttons)

# ⚙️ Handle button presses
@app.on_callback_query(filters.regex(r"perm\|"))
async def handle_permissions(client, query: CallbackQuery):
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    key = query.data.split("|")[1]

    state = PERMISSION_SELECTION.get((chat_id, user_id))
    if not state:
        return await query.answer("⛔ Session expired. Use /admin or /disadmin again.", show_alert=True)

    target_id = state["target_id"]
    mode = state["mode"]
    perms = state["permissions"]

    if key == "confirm":
        if mode == "promote":
            privileges = ChatPrivileges(
                can_delete_messages="delete" in perms,
                can_pin_messages="pin" in perms,
                can_invite_users="invite" in perms,
                can_promote_members="promote" in perms,
                can_restrict_members="restrict" in perms,
                can_manage_video_chats="video" in perms,
                can_change_info="info" in perms,
                can_manage_chat="manage" in perms,
                is_anonymous="anon" in perms
            )
        else:  # demote
            current = await client.get_chat_member(chat_id, target_id)
            privileges = current.privileges or ChatPrivileges()
            privileges = ChatPrivileges(
                can_delete_messages=privileges.can_delete_messages and "delete" not in perms,
                can_pin_messages=privileges.can_pin_messages and "pin" not in perms,
                can_invite_users=privileges.can_invite_users and "invite" not in perms,
                can_promote_members=privileges.can_promote_members and "promote" not in perms,
                can_restrict_members=privileges.can_restrict_members and "restrict" not in perms,
                can_manage_video_chats=privileges.can_manage_video_chats and "video" not in perms,
                can_change_info=privileges.can_change_info and "info" not in perms,
                can_manage_chat=privileges.can_manage_chat and "manage" not in perms,
                is_anonymous=privileges.is_anonymous and "anon" not in perms
            )

        try:
            await client.promote_chat_member(chat_id, target_id, privileges=privileges)
            action = "promoted with" if mode == "promote" else "updated (removed)"
            await query.message.edit_text(f"✅ User {action} selected permissions.")
        except Exception as e:
            await query.message.edit_text(f"❌ Failed:\n`{e}`")
        PERMISSION_SELECTION.pop((chat_id, user_id), None)
        return

    # Toggle permission selection
    if key in perms:
        perms.remove(key)
    else:
        perms.add(key)

    await query.message.edit_reply_markup(permission_buttons(chat_id, user_id))
    await query.answer("✔️ Updated")
