from EsproChat import app
from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message
import g4f

# 🔁 Bot username without @ (must match your bot)
BOT_USERNAME = "MissEsproBot"

# ✅ Check if the bot was replied to or mentioned
def is_mentioned_or_replied(message: Message):
    if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.is_self:
        return True
    if message.entities:
        for entity in message.entities:
            if entity.type == "mention" and f"@{BOT_USERNAME.lower()}" in message.text.lower():
                return True
    return False

# ✅ Message handler for all chat types
@app.on_message(filters.text)  # Removed ~filters.edited (crash fix)
async def chatgpt_handler(client, message: Message):
    if message.chat.type == "private":
        pass
    elif message.chat.type in ("group", "supergroup"):
        if not is_mentioned_or_replied(message):
            return

    await message.reply_chat_action(ChatAction.TYPING)

    try:
        prompt = f"""
Tum ek real insaan ho. Har reply casual, short, aur friendly Hindi me do.
Zyada lamba mat likho. Normal dost jaise baat karo.

User: {message.text}
Bot:
"""

        # ✅ Using default working model
        response = g4f.ChatCompletion.create(
            model=g4f.models.default,
            messages=[
                {"role": "user", "content": prompt},
            ],
        )

        await message.reply(response.strip())

    except Exception as e:
        await message.reply("😓 Error:\n" + str(e))
