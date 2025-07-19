from EsproChat import app
from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message
from config import MONGO_URL, OWNER_ID
import g4f
from pymongo import MongoClient
import asyncio
import re
import random
from datetime import datetime

# MongoDB setup
mongo = MongoClient(MONGO_URL)
chatdb = mongo.ChatDB.chat_data

# Faster response time configuration
TYPING_SPEED = 0.02  # Seconds per character (faster than before)
MIN_TYPING_TIME = 0.5  # Minimum typing time
MAX_TYPING_TIME = 2.0  # Maximum typing time

# Emoji database with 100+ emojis
EMOJI_DB = {
    "romantic": ["❤️", "🥰", "💖", "😘", "💕", "💘", "💓", "💞", "💗", "💝"],
    "happy": ["😊", "☺️", "✨", "🌸", "🎉", "😄", "🤗", "🎊", "🥳", "🌼"],
    "sad": ["🥺", "😔", "😢", "💔", "😞", "😭", "😟", "😥", "😿", "☹️"],
    "flirty": ["😳", "👀", "💋", "😏", "😉", "😈", "👄", "👅", "🍑", "🔥"],
    "funny": ["😂", "🤣", "😆", "😝", "😜", "🤪", "🐒", "🍌", "🎭", "🤡"],
    "time": {
        "morning": ["🌞", "☀️", "🌅", "🌄", "🐦", "🍳", "☕", "🌻", "👋", "🌤️"],
        "day": ["😎", "🌈", "🌞", "🏖️", "🍹", "👒", "🕶️", "🚶", "🌡️", "⛱️"],
        "evening": ["🌙", "🌆", "🌇", "🍷", "🌃", "🏙️", "🌉", "🛋️", "📺", "🌠"],
        "night": ["✨", "🌌", "🌕", "🌚", "🛌", "💤", "🌛", "🌜", "🦉", "🧸"]
    }
}

# Sticker database (replace with your actual sticker IDs)
STICKER_DB = {
    "romantic": [
        "CAACAgUAAxkBAAICbWh7FKwivGnaDMUYtfTgUIOqeYVoAAIkGAACJtxwVxlSuVnRcaJbHgQ",
        "CAACAgUAAxkBAAICcGh7FNHNNsQ08dfKy6hJ_Sut_ZB0AAJsGAACLn_gV6C4NxtVTJJ-HgQ",
        "CAACAgUAAxkBAAICdGh7FO-X_IcyVry1J5waNvRJPBJbAALpFAAC_4ThVwuGqcXQHPlQHgQ"
    ],
    "flirty": [
        "CAACAgUAAxkBAAICd2h7FRA-rTHHwwuThaaCBe_iL3QAAycQAAIxiXhUOHDGuGPyIdMeBA",
        "CAACAgEAAxkBAAICemh7FTtL5LoJGj61Jf705Sttt2XvAAKbAwACIZGZR_UlcXmwWjWeHgQ",
        "CAACAgQAAxkBAAICfmh7FWZSHFJEXnW0SqMyGjtF7GBCAALXEQACMO4JUpqFa3kNXiSNHgQ"
    ],
    "happy": [
        "CAACAgQAAxkBAAICgWh7Fhq9p4BdQnaqeRmIeIf1sHHkAAIMCgACKM7RUsygu40CSdsTHgQ",
        "CAACAgUAAxkBAAIChGh7FkFle5KZYUDCAAHOrP5JnoohEAACGBUAAuWt-VdCjQ7H8dJbBB4E",
        "CAACAgUAAxkBAAICiGh7FqEtpn-u4ibZf88L6UtC2HnuAAKUFgACf0WAVfN0pe7cEmo6HgQ"
    ],
    "greeting": [
        "CAACAgUAAxkBAAICimh7FwABYVQ1vTzZz5QY8gABX1tqSAACpRcAAg4F4VcAAW5e0gABXlweBA",
        "CAACAgUAAxkBAAICjGh7F0Y4t8u4Xb0v3QABW1Z9b4QyWwACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICjmh7F3J5M6lQ5J9b1gABJXQABQABvQ8AAo4WAAJ5UuFXwqQj3wAB1YQeBA"
    ]
}

def is_message_for_someone_else(message: Message):
    if message.reply_to_message:
        replied_user = message.reply_to_message.from_user
        if replied_user and not replied_user.is_self:
            return True

    if message.entities:
        for entity in message.entities:
            if entity.type == "mention":
                mention_text = message.text[entity.offset : entity.offset + entity.length]
                if mention_text.lower() != f"@{BOT_USERNAME.lower()}":
                    return True
    return False

def contains_link(text):
    link_pattern = r"(https?://\S+|t\.me/\S+|www\.\S+|[\w\-]+\.(com|in|net|org|xyz|me|link|ly|site|bio|store))"
    return bool(re.search(link_pattern, text.lower()))

async def human_typing(message):
    text_length = len(message.text)
    typing_time = min(max(text_length * TYPING_SPEED, MIN_TYPING_TIME), MAX_TYPING_TIME)
    await message.reply_chat_action(ChatAction.TYPING)
    await asyncio.sleep(typing_time)

def get_emoji_for_message(text):
    text = text.lower()
    
    if is_romantic(text):
        return random.choice(EMOJI_DB["romantic"])
    elif any(word in text for word in ["khush", "happy", "achha", "good", "nice"]):
        return random.choice(EMOJI_DB["happy"])
    elif any(word in text for word in ["udaas", "sad", "dukh", "tension", "problem"]):
        return random.choice(EMOJI_DB["sad"])
    elif is_flirty(text):
        return random.choice(EMOJI_DB["flirty"])
    elif is_funny(text):
        return random.choice(EMOJI_DB["funny"])
    
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        return random.choice(EMOJI_DB["time"]["morning"])
    elif 12 <= current_hour < 17:
        return random.choice(EMOJI_DB["time"]["day"])
    elif 17 <= current_hour < 22:
        return random.choice(EMOJI_DB["time"]["evening"])
    else:
        return random.choice(EMOJI_DB["time"]["night"])

async def send_context_sticker(client, message, text):
    text = text.lower()
    
    if is_romantic(text):
        sticker_type = "romantic"
    elif is_flirty(text):
        sticker_type = "flirty"
    elif any(word in text for word in ["hi", "hello", "hey", "namaste"]):
        sticker_type = "greeting"
    else:
        sticker_type = "happy"
    
    try:
        await client.send_sticker(
            chat_id=message.chat.id,
            sticker=random.choice(STICKER_DB[sticker_type]),
            reply_to_message_id=message.id
        )
        return True
    except:
        return False

def is_romantic(text):
    text = text.lower()
    romantic_words = ["pyaar", "love", "like", "pasand", "dil", "pyar", "miss", "yaad", 
                     "cute", "beautiful", "handsome", "sexy", "hot", "hug", "kiss", "romantic"]
    return any(word in text for word in romantic_words)

def is_flirty(text):
    text = text.lower()
    flirty_words = ["sexy", "hot", "attractive", "chikni", "handsome", "gori", "figure", "body"]
    return any(word in text for word in flirty_words)

def is_funny(text):
    text = text.lower()
    funny_words = ["haso", "joke", "majak", "funny", "hasi", "comedy", "lol"]
    return any(word in text for word in funny_words)

def extract_name(message: Message):
    """Extract name from message with proper handling"""
    user = message.from_user
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    return user.first_name or ""

def process_name_in_text(text, name):
    """Insert name naturally in responses"""
    name_inserts = [
        f"{name}...",
        f"{name} ji...",
        f"Hey {name}...",
        f"{name} baby...",
        f"Oye {name}...",
        f"Dear {name}...",
        f"{name} darling..."
    ]
    return random.choice(name_inserts) + " " + text

@app.on_message(filters.text & ~filters.regex(r"^/"))
async def smart_bot_handler(client, message: Message):
    if is_message_for_someone_else(message) or contains_link(message.text):
        return

    # Faster response initiation
    typing_task = asyncio.create_task(human_typing(message))

    try:
        user_input = message.text.strip()
        user_name = extract_name(message)
        
        # Check if someone is being tagged/asked about
        if message.entities:
            for entity in message.entities:
                if entity.type == "mention":
                    mention = user_input[entity.offset:entity.offset+entity.length]
                    return await message.reply(f"{mention} kaun hai? Mujhe nahi pata... {get_emoji_for_message('confused')}")

        # MongoDB check (faster response for known queries)
        if any(word in user_input.lower() for word in ["kyun", "kaise", "kya", "kab"]):
            data = chatdb.find_one({"question": user_input.lower()})
            if data:
                response = data["answer"] + " " + get_emoji_for_message(user_input)
                if random.random() < 0.7:  # 70% chance to use name
                    response = process_name_in_text(response, user_name)
                await typing_task  # Ensure typing completes
                return await message.reply(response)

        # Sticker response (25% chance)
        if random.random() < 0.25:
            sticker_sent = await send_context_sticker(client, message, user_input)
            if sticker_sent:
                await asyncio.sleep(0.3)  # Small delay after sticker
                return

        # Generate response
        base_prompt = f"""
You are Espro, a 19-year-old Indian girl chatting on WhatsApp. Reply naturally in Hinglish with emojis.

Guidelines:
1. Be extremely human-like (no bot behavior)
2. Use the person's name naturally ({user_name})
3. Keep responses short (1-2 lines max)
4. Match the tone (romantic, funny, casual)
5. Add relevant emoji
6. Make occasional typing mistakes
7. Be emotionally intelligent

Context:
Time: {datetime.now().strftime("%I:%M %p")}
Mood: {'Romantic' if is_romantic(user_input) else 'Flirty' if is_flirty(user_input) else 'Funny' if is_funny(user_input) else 'Normal'}

Message: {user_input}
Espro:
"""

        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4,
            messages=[{"role": "user", "content": base_prompt}],
            stream=False
        )

        final_answer = response.strip()
        
        # Enhance the response
        if not any(char in final_answer for char in ["❤️", "😊", "😂", "😍", "🤔", "🥺"]):
            final_answer += " " + get_emoji_for_message(user_input)
        
        # Add human touches
        if random.random() < 0.3:
            final_answer = final_answer.replace(".", "...").replace("!", "!!")
        if random.random() < 0.2:
            final_answer = final_answer.lower().replace("hai", "haan").replace("ho", "hii")
        
        # Insert name naturally
        if random.random() < 0.8 and user_name:  # 80% chance to use name
            final_answer = process_name_in_text(final_answer, user_name)

        await typing_task  # Ensure typing completes
        
        if final_answer:
            await message.reply(final_answer)
        else:
            await message.reply(f"{user_name}... samajh nahi aaya... {get_emoji_for_message('confused')}")

    except Exception as e:
        error_msg = random.choice([
            f"Arey {user_name}... kuch to gadbad hai 😅",
            "Oops... thoda wait karo",
            "Network slow lag raha hai...",
            "Phir try karna thodi der baad"
        ])
        await message.reply(error_msg)

@app.on_message(filters.command("teach") & filters.text)
async def teach_command(client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply(f"Sorry {extract_name(message)}... ye option mere liye nahi hai {get_emoji_for_message('no')}")

    try:
        text = message.text.split(" ", 1)[1]
        if "|" not in text:
            return await message.reply("Galat format! Sahi format: `/teach sawaal | jawab`")

        question, answer = text.split("|", 1)
        question = question.strip().lower()
        answer = answer.strip()

        if not any(word in question for word in ["kyun", "kaise", "kya", "kab", "kaha"]):
            return await message.reply(f"{extract_name(message)}... main sirf facts yaad kar sakti hu {get_emoji_for_message('sorry')}")

        chatdb.update_one(
            {"question": question},
            {"$set": {"answer": answer}},
            upsert=True
        )

        await message.reply(f"Haan {extract_name(message)}... samajh gayi! Yaad rakhungi {get_emoji_for_message('happy')}")

    except Exception as e:
        await message.reply(f"Oops {extract_name(message)}... kuch to gadbad hai {get_emoji_for_message('confused')}")
