from EsproChat import app
from pyrogram import Client, filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message
import g4f



def is_mentioned_or_replied(message: Message):
    """Check if bot is mentioned or replied to in a group."""
    if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.is_self:
        return True
    if message.entities:
        for entity in message.entities:
            if entity.type == "mention" and f"@{BOT_USERNAME.lower()}" in message.text.lower():
                return True
    return False


@app.on_message(filters.text & ~filters.edited)
async def chatgpt_handler(client, message: Message):
    # Private chat: reply to all messages
    if message.chat.type == "private":
        pass
    # Group chat: reply only if mentioned or replied to
    elif message.chat.type in ("group", "supergroup"):
        if not is_mentioned_or_replied(message):
            return

    user_msg = message.text
    await message.reply_chat_action(ChatAction.TYPING)

    try:
        prompt = f"""
Tum ek real insaan ho. Har reply casual, short, aur friendly Hindi me do.
Zyada lamba mat likho. Normal dost jaise baat karo.

User: {user_msg}
Bot:
"""

        response = g4f.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )

        await message.reply(response.strip())

    except Exception as e:
        await message.reply("😓 Error:\n" + str(e))

