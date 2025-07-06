import asyncio
from pyrogram import Client, filters
from pyrogram.enums import ChatType, ChatMemberStatus
from EsproChat import app  # Your bot instance

SPAM_CHATS = []

# ✅ Admin check function
async def is_user_admin(client: Client, chat_id: int, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except:
        return False

# ✅ /mention /all /utag command
@app.on_message(filters.command(["mention", "all", "utag"]) & filters.group)
async def tag_all_users(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Admin check
    if not await is_user_admin(client, chat_id, user_id):
        return await message.reply_text("🚫 Only group admins can use this command.")

    # Check for existing tag process
    if chat_id in SPAM_CHATS:
        return await message.reply_text("⚠️ Tagging already running. Use /alloff to stop.")

    replied = message.reply_to_message
    if len(message.command) < 2 and not replied:
        return await message.reply_text("ℹ️ Reply to a message or use: `/all your_message`")

    mode = "reply" if replied else "text"
    text = message.text.split(None, 1)[1] if mode == "text" else ""

    SPAM_CHATS.append(chat_id)
    user_count = 0
    user_text = ""

    try:
        async for member in client.get_chat_members(chat_id):
            if chat_id not in SPAM_CHATS:
                break
            if member.user.is_bot:
                continue

            user_count += 1
            user_text += f"⊚ [{member.user.first_name}](tg://user?id={member.user.id})\n"

            if user_count == 5:
                try:
                    if mode == "reply":
                        await replied.reply_text(user_text)
                    else:
                        await client.send_message(chat_id, f"{text}\n{user_text}")
                except:
                    pass
                await asyncio.sleep(2)
                user_count = 0
                user_text = ""

        # Remaining users
        if user_text:
            try:
                if mode == "reply":
                    await replied.reply_text(user_text)
                else:
                    await client.send_message(chat_id, f"{text}\n{user_text}")
            except:
                pass
    finally:
        if chat_id in SPAM_CHATS:
            SPAM_CHATS.remove(chat_id)

# ✅ /alloff command to stop tagging
@app.on_message(filters.command("alloff") & filters.group)
async def stop_tagging(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Admin check
    if not await is_user_admin(client, chat_id, user_id):
        return await message.reply_text("🚫 Only group admins can stop the tag process.")

    if chat_id in SPAM_CHATS:
        SPAM_CHATS.remove(chat_id)
        await message.reply_text("✅ Tagging process stopped.")
    else:
        await message.reply_text("ℹ️ No tagging process is active.")
