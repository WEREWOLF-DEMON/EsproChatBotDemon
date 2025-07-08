from pyrogram import Client, filters
from pyrogram.types import Message, ChatJoinRequest
import random
from EsproChat import app

# 🎉 Welcome Message List
WELCOME_MESSAGES = [
    "Hey {mention}, welcome to {chat} 😄",
    "🎉 {mention} just joined {chat}! Make yourself at home.",
    "Glad to have you here, {mention} in {chat} 💫",
    "A wild {mention} appeared in {chat} 😍",
    "Namaste {mention} 🙏 Welcome to {chat}",
    "Kya baat hai! {mention} joined {chat} 😍",
    "Dhamakedar welcome to {mention} 💥 in {chat}",
    "Welcome ke saath chai bhi milegi, {mention} ☕ in {chat}",
    "One of us! One of us! Welcome {mention} to {chat} 🤝",
    "Hello hello {mention}, welcome to {chat} 🎤",
    # ... add more as you like
]

# ✅ Handle Normal Joins (add/invite)
@app.on_message(filters.new_chat_members)
async def welcome_new_member(client: Client, message: Message):
    for member in message.new_chat_members:
        if member.is_bot:
            continue
        mention = member.mention(style="markdown")
        chat_name = message.chat.title or "this group"
        welcome_text = random.choice(WELCOME_MESSAGES).format(mention=mention, chat=chat_name)
        await message.reply_text(welcome_text, disable_web_page_preview=True)

# ✅ Handle Join Request Accepted
@app.on_chat_join_request()
async def handle_join_request(client: Client, join_request: ChatJoinRequest):
    user = join_request.from_user
    mention = user.mention(style="markdown")
    chat_name = join_request.chat.title or "this group"
    welcome_text = random.choice(WELCOME_MESSAGES).format(mention=mention, chat=chat_name)

    await client.send_message(
        chat_id=join_request.chat.id,
        text=welcome_text,
        disable_web_page_preview=True
    )

    # Optional: Approve automatically (if you want)
    # await client.approve_chat_join_request(join_request.chat.id, user.id)
