from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio
from collections import defaultdict
import time
from EsproChat import app


# Memory-based message tracker
user_messages = defaultdict(list)

# Settings
MESSAGE_LIMIT = 10
TIME_WINDOW = 60  # seconds
EXCLUDED_USER_ID = 7666870729  # This user will not be restricted

@app.on_message(filters.group & filters.text & ~filters.service)
async def anti_spam_handler(client: Client, message: Message):
    user = message.from_user
    if not user:
        return

    user_id = user.id
    chat_id = message.chat.id

    # 🚫 Skip spam check for excluded user
    if user_id == EXCLUDED_USER_ID:
        return

    now = time.time()

    # Track user's message times
    user_messages[(chat_id, user_id)].append(now)

    # Keep only recent messages within TIME_WINDOW
    user_messages[(chat_id, user_id)] = [
        msg_time for msg_time in user_messages[(chat_id, user_id)]
        if now - msg_time <= TIME_WINDOW
    ]

    # Delete if message count exceeds limit
    if len(user_messages[(chat_id, user_id)]) > MESSAGE_LIMIT:
        try:
            await message.delete()
        except Exception as e:
            print(f"Failed to delete message: {e}")
