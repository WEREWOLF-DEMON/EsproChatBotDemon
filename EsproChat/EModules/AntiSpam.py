from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ChatPrivileges
)
from EsproChat import app

OWNER_ID = 7666870729
user_power_selection = {}  # Stores selected permissions temporarily
awaiting_title = {}  # Stores pending titles for users

# List of toggleable powers with display emoji
POWER_BUTTONS = [
    ("🧹 Delete", "can_delete_messages"),
    ("📌 Pin", "can_pin_messages"),
    ("🔗 Invite", "can_invite_users"),
    ("🔒 Restrict", "can_restrict_members"),
    ("🧑‍💼 Promote", "can_promote_members"),
    ("🎥 Video", "can_manage_video_chats"),
    ("⚙️ Manage Chat", "can_manage_chat")
]

# Build the permission toggle UI
def build_keyboard(uid):
    selected = user_power_selection.get(uid, set())
    buttons, row = [], []
    for emoji, power in POWER_BUTTONS:
        mark = "✅" if power in selected else "☐"
        row.append(InlineKeyboardButton(f"{mark} {emoji}", callback_data=f"toggle:{power}:{uid}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("✅ Apply Permissions", callback_data=f"apply:{uid}")])
    return InlineKeyboardMarkup(buttons)

# /admin command
@app.on_message(filters.command("admin") & filters.group)
async def handle_admin(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        member = await message.chat.get_member(message.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await message.reply("🚫 Only admins or owner can use this.")

    args = message.text.split()[1:]

    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif args:
        try:
            target = await client.get_users(args[0] if args[0].startswith("@") else int(args[0]))
        except Exception as e:
            return await message.reply(f"❌ Failed to find user:\n`{e}`")
    else:
        return await message.reply("🧠 Usage: Reply or use `/admin @user`")

    user_power_selection[target.id] = set()
    await message.reply(
        f"🔘 Choose permissions for [{target.first_name}](tg://user?id={target.id}):",
        reply_markup=build_keyboard(target.id),
        disable_web_page_preview=True
    )

# Toggle individual permissions
@app.on_callback_query(filters.regex("toggle:(.*?):(\\d+)"))
async def toggle_power(client: Client, query: CallbackQuery):
    power, uid = query.data.split(":")[1:]
    uid = int(uid)

    if query.from_user.id != OWNER_ID:
        member = await client.get_chat_member(query.message.chat.id, query.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await query.answer("❌ Only admins or owner", show_alert=True)

    selected = user_power_selection.setdefault(uid, set())
    if power in selected:
        selected.remove(power)
    else:
        selected.add(power)

    await query.edit_message_reply_markup(reply_markup=build_keyboard(uid))

# Apply permissions and ask for title
@app.on_callback_query(filters.regex("apply:(\\d+)"))
async def ask_title(client: Client, query: CallbackQuery):
    uid = int(query.data.split(":")[1])

    if query.from_user.id != OWNER_ID:
        member = await client.get_chat_member(query.message.chat.id, query.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await query.answer("❌ Only admins or owner", show_alert=True)

    awaiting_title[query.message.chat.id] = uid
    await query.edit_message_text("💬 Please send a custom title/tag for this admin (like Boss, Helper, Leader)")

# Receive title and promote
@app.on_message(filters.text & filters.group)
async def receive_title(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id not in awaiting_title:
        return

    uid = awaiting_title.pop(chat_id)
    tag = message.text.strip()
    powers = user_power_selection.get(uid, set())

    perms = {
        "can_manage_chat": False,
        "can_delete_messages": False,
        "can_restrict_members": False,
        "can_invite_users": False,
        "can_pin_messages": False,
        "can_promote_members": False,
        "can_manage_video_chats": False,
        "is_anonymous": False
    }

    for power in powers:
        perms[power] = True

    privileges = ChatPrivileges(**perms)

    try:
        await client.promote_chat_member(chat_id, uid, privileges=privileges)
        await client.set_administrator_title(chat_id, uid, tag)
        await message.reply(f"✅ Promoted [User](tg://user?id={uid}) with title **{tag}** and powers: `{', '.join(powers) or 'None'}`")
        user_power_selection.pop(uid, None)
    except Exception as e:
        await message.reply(f"❌ Failed to promote:\n`{e}`")

# /disadmin command
@app.on_message(filters.command("disadmin") & filters.group)
async def disadmin_user(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        member = await client.get_chat_member(message.chat.id, message.from_user.id)
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
        return await message.reply("🧠 Usage:\n• Reply with `/disadmin`\n• or `/disadmin @username`")

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
