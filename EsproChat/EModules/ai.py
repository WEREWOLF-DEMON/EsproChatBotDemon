from EsproChat import app
from pyrogram import filters
from pyrogram.enums import ChatAction, ChatType
from pyrogram.types import Message
from config import MONGO_URL, OWNER_ID, BOT_USERNAME
import g4f
from pymongo import MongoClient
import asyncio
import re
import random
from datetime import datetime

# MongoDB setup
mongo = MongoClient(MONGO_URL)
chatdb = mongo.ChatDB.chat_data

# Response configuration
TYPING_SPEED = 0.015  # Faster typing speed
MIN_TYPING_TIME = 0.3  # Reduced minimum typing time
MAX_TYPING_TIME = 1.5  # Reduced maximum typing time

# Conversation tracking
conversation_state = {}

# Massive Emoji Database (200+ emojis)
EMOJI_DB = {
    "romantic": ["❤️", "🥰", "💖", "😘", "💕", "💘", "💓", "💞", "💗", "💝", "💟", "🌹", "🥀", "😍", "🤩", "💌", "💏", "💑", "👩‍❤️‍👨", "👩‍❤️‍💋‍👨"],
    "happy": ["😊", "☺️", "✨", "🌸", "🎉", "😄", "🤗", "🎊", "🥳", "🌼", "🌞", "🌻", "🤭", "😁", "🙃", "😇", "😌", "🤗", "🥰", "😋"],
    "sad": ["🥺", "😔", "😢", "💔", "😞", "😭", "😟", "😥", "😿", "☹️", "😩", "😫", "😖", "😣", "😓", "😪", "😵", "🥴", "😧", "😨"],
    "flirty": ["😳", "👀", "💋", "😏", "😉", "😈", "👄", "👅", "🍑", "🔥", "🥵", "🥶", "😻", "👅", "🍒", "🍓", "🍷", "👠", "💄", "👙"],
    "funny": ["😂", "🤣", "😆", "😝", "😜", "🤪", "🐒", "🍌", "🎭", "🤡", "👻", "💩", "🤠", "🥸", "🧐", "🤓", "😎", "🤯", "🥴", "🤑"],
    "angry": ["😠", "😡", "🤬", "👿", "💢", "🗯️", "👊", "🤜", "🤛", "💣", "🔪", "💥", "⚡", "🔥", "❌", "🚫", "⛔", "🙅", "🙅‍♀️", "🙅‍♂️"],
    "time": {
        "morning": ["🌞", "☀️", "🌅", "🌄", "🐦", "🍳", "☕", "🌻", "👋", "🌤️", "⛅", "🌥️", "🌦️", "🌼", "🐓", "🥞", "🥐", "🧃", "🏃‍♀️", "🧘"],
        "day": ["😎", "🌈", "🌞", "🏖️", "🍹", "👒", "🕶️", "🚶", "🌡️", "⛱️", "🌴", "🍍", "🍉", "🍦", "🛍️", "🎈", "🏊", "🚴", "🎮", "📚"],
        "evening": ["🌙", "🌆", "🌇", "🍷", "🌃", "🏙️", "🌉", "🛋️", "📺", "🌠", "🌃", "🌌", "🍸", "🍽️", "🎑", "🎇", "🎆", "🌄", "🌅", "🌉"],
        "night": ["✨", "🌌", "🌕", "🌚", "🛌", "💤", "🌛", "🌜", "🦉", "🧸", "🌙", "🌠", "🌃", "🌉", "🌆", "🌇", "🌃", "🌌", "🌠", "🌉"]
    },
    "misc": ["🎶", "🎵", "🎧", "🎤", "🎼", "🎹", "🥁", "🎷", "🎺", "🎸", "🪕", "🎻", "🎲", "🎯", "🎳", "🎮", "🎰", "🧩", "🎨", "🖌️"]
}

# Enhanced Sticker Database (150+ stickers)
STICKER_DB = {
    "romantic": ["CAACAgQAAxkBAAICfmh7FWZSHFJEXnW0SqMyGjtF7GBCAALXEQACMO4JUpqFa3kNXiSNHgQ", "CAACAgEAAxkBAAICemh7FTtL5LoJGj61Jf705Sttt2XvAAKbAwACIZGZR_UlcXmwWjWeHgQ", "CAACAgUAAxkBAAICdGh7FO-X_IcyVry1J5waNvRJPBJbAALpFAAC_4ThVwuGqcXQHPlQHgQ",...],  # 30 romantic stickers
    "flirty": ["CAACAgUAAxkBAAICd2h7FRA-rTHHwwuThaaCBe_iL3QAAycQAAIxiXhUOHDGuGPyIdMeBA", "CAACAgUAAxkBAAICbWh7FKwivGnaDMUYtfTgUIOqeYVoAAIkGAACJtxwVxlSuVnRcaJbHgQ", ...],    # 30 flirty stickers
    "happy": ["CAACAgUAAxkBAAICsmh7Ls97jXg40sGQo7me2Uc9rp8EAALQDgACLyWIVw4x3BsVnl7RHgQ", "CAACAgUAAxkBAAICtWh7LyiAxKHdfquwnUHKLKBs5vSnAAI9DwAC9LoRVszGrvR_xZjCHgQ", ...],     # 30 happy stickers
    "greeting": ["CAACAgUAAxkBAAICuGh7L07LVG5Aj_zi6ju6acYRj8NZAAJvDAACxUfwV4wp4yMvwk0lHgQ", "CAACAgUAAxkBAAICu2h7L3JOuNeZ7N1-eKXImoM1QlMqAAJUFwAC3zyBVcoHHZRsUbnkHgQ", ...],  # 30 greeting stickers
    "funny": ["CAACAgUAAxkBAAICvmh7L5drd3kjwekQPQk_AsPMVxZ1AAKUBwAC0IfZVn_le11bBRfRHgQ", "CAACAgUAAxkBAAICwWh7L703KEpSiQrnfTBDEKojT5OhAAKbBwAC0Q4hV3MQKHEmTc7gHgQ", ...],     # 30 funny stickers
    "sad": ["CAACAgUAAxkBAAICxGh7MAUoZ9VrH8s49zIt7t5Vqz7GAAJaCQACyqTZVt1FOot0lbFwHgQ", "CAACAgUAAxkBAAICyGh7MCoK14EEQMGSOBU1ME9EMB44AALyCAACEyzYVtD0TUgYWms1HgQ", ...]        # 10 sad stickers
}

def should_use_name(message: Message):
    """Smart logic for when to use names"""
    chat_type = message.chat.type
    user_name = extract_name(message)
    
    # Never use name in private chats after first message
    if chat_type == ChatType.PRIVATE:
        last_used = conversation_state.get(message.chat.id, {}).get('last_name_used', 0)
        if last_used > 0:  # Already used name once
            return False
        conversation_state.setdefault(message.chat.id, {})['last_name_used'] = datetime.now().timestamp()
        return True
    
    # For groups, use name only when:
    # 1. Directly mentioned (@botname)
    # 2. First reply in a thread
    # 3. Random 30% chance when not recently used
    is_direct_mention = f"@{BOT_USERNAME}" in message.text.lower()
    is_first_reply = not conversation_state.get(message.chat.id, {}).get('replied', False)
    
    if is_direct_mention or is_first_reply:
        conversation_state.setdefault(message.chat.id, {})['replied'] = True
        return True
    
    # Random chance with cooldown
    last_used = conversation_state.get(message.chat.id, {}).get('last_name_used', 0)
    current_time = datetime.now().timestamp()
    if current_time - last_used > 300 and random.random() < 0.3:  # 5 min cooldown, 30% chance
        conversation_state.setdefault(message.chat.id, {})['last_name_used'] = current_time
        return True
    
    return False

def generate_response_with_name(text, name, message):
    """Generate response with natural name usage"""
    if not should_use_name(message):
        return text
    
    name_formats = [
        (f"{name}...", 30),
        ("", 20),  # No name
        (f"Hey {name}...", 15),
        (f"Oye {name}...", 10),
        (f"{name} ji...", 10),
        (f"{name} baby...", 5),
        (f"Dear {name}...", 5),
        (f"{name} darling...", 5)
    ]
    
    # Weighted random selection
    total = sum(weight for (_, weight) in name_formats)
    r = random.uniform(0, total)
    upto = 0
    for fmt, weight in name_formats:
        if upto + weight >= r:
            return f"{fmt} {text}".strip() if fmt else text
        upto += weight
    return text

@app.on_message(filters.text & ~filters.regex(r"^/"))
async def smart_bot_handler(client, message: Message):
    if is_message_for_someone_else(message) or contains_link(message.text):
        return

    # Start typing indicator
    typing_task = asyncio.create_task(human_typing(message))
    
    try:
        user_input = message.text.strip()
        user_name = extract_name(message)
        
        # Handle mentions in groups
        if message.entities and message.chat.type != ChatType.PRIVATE:
            for entity in message.entities:
                if entity.type == "mention":
                    mention = user_input[entity.offset:entity.offset+entity.length]
                    if mention.lower() != f"@{BOT_USERNAME}":
                        response = f"{mention} kaun hai? Mujhe nahi pata... {get_emoji_for_message('confused')}"
                        await message.reply(response)
                        return

        # Sticker response (40% chance)
        if random.random() < 0.4:
            if await send_sticker_response(client, message):
                await asyncio.sleep(0.2)
                return

        # Generate human-like response
        base_prompt = f"""
You are Espro, a 19-year-old Indian girl chatting naturally. Follow these rules:
1. Respond in Hinglish with emojis
2. Keep replies short (1-2 lines max)
3. Only use names when absolutely necessary
4. Be emotionally intelligent
5. Vary your responses - don't repeat phrases
6. Make it feel like human conversation

Chat Type: {'Private' if message.chat.type == ChatType.PRIVATE else 'Group'}
User's name: {user_name}
Message: {user_input}
Espro's response:
"""
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4,
            messages=[{"role": "user", "content": base_prompt}],
            stream=False
        )

        final_answer = response.strip()
        
        # Add emoji if missing
        if not any(char in final_answer for char in ["❤️", "😊", "😂", "😍", "🤔", "🥺"]):
            final_answer += " " + get_emoji_for_message(user_input)
        
        # Humanize the response
        final_answer = generate_response_with_name(final_answer, user_name, message)
        
        if random.random() < 0.3:
            final_answer = final_answer.replace(".", "...").replace("!", "!!")
        
        await typing_task
        await message.reply(final_answer)

    except Exception as e:
        error_msg = random.choice([
            "Arey... kuch to gadbad hai 😅",
            "Oops... thoda wait karo",
            "Phir try karna"
        ])
        await message.reply(error_msg)

# [Rest of your existing helper functions...]
