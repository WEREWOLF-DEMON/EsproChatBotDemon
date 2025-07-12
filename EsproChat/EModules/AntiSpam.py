from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatPrivileges
from EsproChat import app
OWNER_ID = 7666870729

# ---------------- Storage ----------------
user_power_selection = {}  # Temporary power selections

POWER_BUTTONS = [
    ("🧹 Delete", "del"),
    ("📌 Pin", "pin"),
    ("🔗 Invite", "invite"),
    ("🔒 Restrict", "restrict"),
    ("🧑‍💼 Promote", "promote"),
    ("🎥 Video", "video"),
    ("⚙️ Manage Chat", "manage"),
]

def build_keyboard(uid):
    selected = user_power_selection.get(uid, set())
    buttons, row = [], []
    for emoji, power in POWER_BUTTONS:
        active = "✅" if power in selected else "☐"
        row.append(InlineKeyboardButton(f"{active} {emoji}", callback_data=f"toggle:{power}:{uid}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("✅ Apply Powers", callback_data=f"apply:{uid}")])
    return InlineKeyboardMarkup(buttons)

# --------------- /admin ----------------
@app.on_message(filters.command("admin") & filters.group)
async def handle_admin_command(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        member = await message.chat.get_member(message.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await message.reply("🚫 Only group admins or the owner can use this.")

    args = message.text.split()[1:]

    # If used via reply, skip tag (fallback to inline button style)
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        user_power_selection[target.id] = set()
        return await message.reply(
            f"🔘 Choose powers for [{target.first_name}](tg://user?id={target.id}):",
            reply_markup=build_keyboard(target.id)
        )

    if len(args) < 3:
        return await message.reply("🧠 Usage:\n`/admin @user Tag del pin`\nOr reply with `/admin`")

    user_ref = args[0]
    tag = args[1]  # 🏷️ This will be used as admin title
    powers = args[2:]

    try:
        user = await client.get_users(user_ref if user_ref.startswith("@") else int(user_ref))
    except Exception as e:
        return await message.reply(f"❌ Failed to find user:\n`{e}`")

    privileges = ChatPrivileges(
        can_manage_chat="manage" in powers,
        can_delete_messages="del" in powers,
        can_restrict_members="restrict" in powers,
        can_invite_users="invite" in powers,
        can_pin_messages="pin" in powers,
        can_promote_members="promote" in powers,
        can_manage_video_chats="video" in powers,
        is_anonymous=False
    )

    try:
        await client.promote_chat_member(
            chat_id=message.chat.id,
            user_id=user.id,
            privileges=privileges
        )

        # ✨ Set custom admin title/tag
        await client.set_administrator_title(
            chat_id=message.chat.id,
            user_id=user.id,
            custom_title=tag
        )

        await message.reply(
            f"✅ [{user.first_name}](tg://user?id={user.id}) promoted as **{tag}** with powers: `{', '.join(powers)}`"
        )
    except Exception as e:
        await message.reply(f"❌ Error:\n`{e}`")

# ------------- Inline Button: Toggle -------------
@app.on_callback_query(filters.regex("toggle:(.*?):(\\d+)"))
async def toggle_power_button(client, query: CallbackQuery):
    power, target_id = query.data.split(":")[1:]
    target_id = int(target_id)

    if query.from_user.id != OWNER_ID:
        member = await client.get_chat_member(query.message.chat.id, query.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await query.answer("❌ Only admins or owner", show_alert=True)

    selected = user_power_selection.setdefault(target_id, set())
    if power in selected:
        selected.remove(power)
    else:
        selected.add(power)

    await query.edit_message_reply_markup(reply_markup=build_keyboard(target_id))

# ------------- Inline Button: Apply -------------
@app.on_callback_query(filters.regex("apply:(\\d+)"))
async def apply_inline_powers(client, query: CallbackQuery):
    target_id = int(query.data.split(":")[1])

    if query.from_user.id != OWNER_ID:
        member = await client.get_chat_member(query.message.chat.id, query.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await query.answer("❌ Only admins or owner", show_alert=True)

    powers = user_power_selection.get(target_id, set())

    privileges = ChatPrivileges(
        can_manage_chat="manage" in powers,
        can_delete_messages="del" in powers,
        can_restrict_members="restrict" in powers,
        can_invite_users="invite" in powers,
        can_pin_messages="pin" in powers,
        can_promote_members="promote" in powers,
        can_manage_video_chats="video" in powers,
        is_anonymous=False
    )

    try:
        await client.promote_chat_member(
            query.message.chat.id,
            target_id,
            privileges=privileges
        )
        await query.edit_message_text(
            f"✅ Promoted [User](tg://user?id={target_id}) with powers:\n• `{', '.join(powers) or 'None'}`"
        )
        user_power_selection.pop(target_id, None)
    except Exception as e:
        await query.edit_message_text(f"❌ Failed to promote:\n`{e}`")

# -------------- /disadmin ----------------
@app.on_message(filters.command("disadmin") & filters.group)
async def disadmin_user(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        member = await message.chat.get_member(message.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await message.reply("❌ Only group admins or the owner can use this.")

    args = message.text.split()[1:]

    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif args:
        try:
            target = await client.get_users(args[0] if args[0].startswith("@") else int(args[0]))
        except Exception as e:
            return await message.reply(f"❌ Failed to find user:\n`{e}`")
    else:
        return await message.reply("🧠 Reply or use `/disadmin @user`")

    empty_privileges = ChatPrivileges(
        can_manage_chat=False,
        can_delete_messages=False,
        can_restrict_members=False,
        can_invite_users=False,
        can_pin_messages=False,
        can_promote_members=False,
        can_manage_video_chats=False,
        is_anonymous=False
    )

    try:
        await client.promote_chat_member(
            chat_id=message.chat.id,
            user_id=target.id,
            privileges=empty_privileges
        )
        await message.reply(f"✅ [{target.first_name}](tg://user?id={target.id}) is no longer admin.")
    except Exception as e:
        await message.reply(f"❌ Error removing admin:\n`{e}`")

# ----------------- RUN ------------------
