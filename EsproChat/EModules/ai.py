from EsproChat import app
from pyrogram import filters
from pyrogram.enums import ChatAction, ChatType
from pyrogram.types import Message, Sticker
from config import MONGO_URL, OWNER_ID, BOT_USERNAME
import g4f
from pymongo import MongoClient
import asyncio
import random
from datetime import datetime

# MongoDB setup
mongo = MongoClient(MONGO_URL)
chatdb = mongo.ChatDB.chat_data

# Response configuration
TYPING_SPEED = 0.01  # Extremely fast typing
MIN_TYPING_TIME = 0.2
MAX_TYPING_TIME = 1.0

# Complete Sticker Database (all original stickers)
STICKER_DB = {
    "romantic": [
        "CAACAgQAAxkBAAICfmh7FWZSHFJEXnW0SqMyGjtF7GBCAALXEQACMO4JUpqFa3kNXiSNHgQ",
        "CAACAgEAAxkBAAICemh7FTtL5LoJGj61Jf705Sttt2XvAAKbAwACIZGZR_UlcXmwWjWeHgQ",
        "CAACAgUAAxkBAAICdGh7FO-X_IcyVry1J5waNvRJPBJbAALpFAAC_4ThVwuGqcXQHPlQHgQ",
        "CAACAgUAAxkBAAICj2h7F3J5M6lQ5J9b1gABJXQABQABvQ8AAo4WAAJ5UuFXwqQj3wAB1YQeBA",
        "CAACAgUAAxkBAAICkGh7F5QY7uJ6w2x8Q3Z8Fz5Z9wABhAAClRYAAg4F4VcAAW5e0gABXlweBA",
        "CAACAgUAAxkBAAICkWh7F5jVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICkmh7F5zVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICk2h7F6DVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAIClGh7F6TVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAIClWh7F6jVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E"
    ],
    "flirty": [
        "CAACAgUAAxkBAAIClmh7F6zVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICl2h7F7DVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICmGh7F7TVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICmWh7F7jVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICmmh7F7zVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICm2h7F8DVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICnGh7F8TVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICnWh7F8jVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICnmh7F8zVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICn2h7F9DVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E"
    ],
    "happy": [
        "CAACAgUAAxkBAAICoGh7F9TVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICoWh7F9jVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAIComh7F9zVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICo2h7F-DVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICpGh7F-TVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICpWh7F-jVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICpmh7F-zVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICp2h7F_DVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICqGh7F_TVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICqWh7F_jVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E"
    ],
    "greeting": [
        "CAACAgUAAxkBAAICqmh7F_zVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICq2h7GADVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICrGh7GATVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICrWh7GAjVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICrmh7GAzVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICr2h7GBDVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICsGh7GBTXhHwZAAE7VQABPZ0AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICsWh7GBjXhHwZAAE7VQABPZ0AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICsmh7GBzXhHwZAAE7VQABPZ0AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICs2h7GCDXhHwZAAE7VQABPZ0AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E"
    ],
    "funny": [
        "CAACAgUAAxkBAAICtGh7GCTXhHwZAAE7VQABPZ0AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICtWh7GCjXhHwZAAE7VQABPZ0AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICtmh7GCzXhHwZAAE7VQABPZ0AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICt2h7GDDXhHwZAAE7VQABPZ0AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICuGh7GDTXhHwZAAE7VQABPZ0AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICuWh7GDjXhHwZAAE7VQABPZ0AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICumh7GDzXhHwZAAE7VQABPZ0AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICu2h7GEDXhHwZAAE7VQABPZ0AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICvGh7GETXhHwZAAE7VQABPZ0AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICvWh7GEjXhHwZAAE7VQABPZ0AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E"
    ],
    "sad": [
        "CAACAgUAAxkBAAICvmh7GEzXhHwZAAE7VQABPZ0AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICv2h7GFDXhHwZAAE7VQABPZ0AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICwGh7GFTXhHwZAAE7VQABPZ0AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICwWh7GFjXhHwZAAE7VQABPZ0AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICwmh7GFzXhHwZAAE7VQABPZ0AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E"
    ]
}

# Complete Emoji Database (all original emojis)
EMOJI_DB = {
    "romantic": ["❤️", "🥰", "💖", "😘", "💕", "💘", "💓", "💞", "💗", "💝", "💟", "🌹", "🥀", "😍", "🤩", "💌", "💏", "💑", "👩‍❤️‍👨", "👩‍❤️‍💋‍👨", "💐", "🌸", "💮", "🏵️", "🌺"],
    "happy": ["😊", "☺️", "✨", "🌸", "🎉", "😄", "🤗", "🎊", "🥳", "🌼", "🌞", "🌻", "🤭", "😁", "🙃", "😇", "😌", "🤗", "🥰", "😋", "😛", "😜", "🤪", "😝", "🤑", "🤠"],
    "sad": ["🥺", "😔", "😢", "💔", "😞", "😭", "😟", "😥", "😿", "☹️", "😩", "😫", "😖", "😣", "😓", "😪", "😵", "🥴", "😧", "😨", "😰", "😱", "😳", "😬", "😐", "😑"],
    "flirty": ["😳", "👀", "💋", "😏", "😉", "😈", "👄", "👅", "🍑", "🔥", "🥵", "🥶", "😻", "👅", "🍒", "🍓", "🍷", "👠", "💄", "👙", "🧦", "👗", "👠", "🎀", "💍", "💎"],
    "funny": ["😂", "🤣", "😆", "😝", "😜", "🤪", "🐒", "🍌", "🎭", "🤡", "👻", "💩", "🤠", "🥸", "🧐", "🤓", "😎", "🤯", "🥴", "🤑", "👽", "🤖", "🎃", "😹", "🙀", "👾"],
    "time": {
        "morning": ["🌞", "☀️", "🌅", "🌄", "🐦", "🍳", "☕", "🌻", "👋", "🌤️", "⛅", "🌥️", "🌦️", "🌼", "🐓", "🥞", "🥐", "🧃", "🏃‍♀️", "🧘", "🌱", "🌿", "🍃", "🌾", "🍂"],
        "day": ["😎", "🌈", "🌞", "🏖️", "🍹", "👒", "🕶️", "🚶", "🌡️", "⛱️", "🌴", "🍍", "🍉", "🍦", "🛍️", "🎈", "🏊", "🚴", "🎮", "📚", "🎨", "✏️", "📝", "📖", "🎯"],
        "evening": ["🌙", "🌆", "🌇", "🍷", "🌃", "🏙️", "🌉", "🛋️", "📺", "🌠", "🌃", "🌌", "🍸", "🍽️", "🎑", "🎇", "🎆", "🌄", "🌅", "🌉", "🌃", "🌌", "🌠", "🌉", "🌆"],
        "night": ["✨", "🌌", "🌕", "🌚", "🛌", "💤", "🌛", "🌜", "🦉", "🧸", "🌙", "🌠", "🌃", "🌉", "🌆", "🌇", "🌃", "🌌", "🌠", "🌉", "🌃", "🌌", "🌠", "🌉", "🌆"]
    }
}

# Enhanced Abuse Handling System
ABUSE_HANDLER = {
    "mild": {
        "words": ["mc", "bkl", "gaali", "gali"],
        "responses": [
            "Language thik rakho yaar!",
            "Aise baat mat karo 😠",
            "Gali dena achha nahi lagta",
            "Thoda tameez se baat karo"
        ]
    },
    "medium": {
        "words": ["bhenchod", "chod", "lavde"],
        "responses": [
            "Abe control kar apni bhasha!",
            "Etna gussa healthy nahi hai 😡",
            "Tumhari aukaat dikh rahi hai",
            "Kya ukhad liya gali deke?"
        ]
    },
    "severe": {
        "words": ["madarchod", "randi", "kutta"],
        "responses": [
            "Teri maa ko aisi gali dega to kaisa lagega?",
            "Khud ki family pe aise bolta hai?",
            "Jaana chutiye, block kar raha hu",
            "Tere jaise logo ko ignore karna best hai"
        ]
    }
}

# Track abuse frequency per user
abuse_tracker = {}

def detect_abuse_level(text):
    """Detect abuse severity level"""
    text = text.lower()
    for level in ["severe", "medium", "mild"]:
        if any(word in text for word in ABUSE_HANDLER[level]["words"]):
            return level
    return None

async def handle_abuse(client, message: Message):
    """Smart abuse handling with escalation"""
    user_id = message.from_user.id
    abuse_level = detect_abuse_level(message.text)
    
    # Track abuse count
    abuse_tracker[user_id] = abuse_tracker.get(user_id, 0) + 1
    
    # Escalate response based on frequency
    if abuse_tracker[user_id] > 3:  # If user abuses frequently
        response = random.choice([
            "Bas kar bhosdike, block kar dunga",
            "Itni gali dene ki aadat? Ghar pe sikhaya nahi kya?",
            "Chal nikal lawde, time waste mat kar"
        ])
    else:
        # Level-based response
        responses = ABUSE_HANDLER[abuse_level]["responses"]
        response = random.choice(responses)
    
    # Add typing delay for realism
    await message.reply_chat_action(ChatAction.TYPING)
    await asyncio.sleep(0.5)
    await message.reply(response)
    
    # Warn or ban for severe cases
    if abuse_level == "severe" and abuse_tracker[user_id] > 2:
        try:
            await client.send_message(
                message.chat.id,
                f"{message.from_user.mention} has been warned for abusive language!"
            )
        except:
            pass

def analyze_sticker(sticker: Sticker):
    """Determine sticker type based on emoji/characteristics"""
    if sticker.emoji in ["❤️", "🥰", "😘", "💋"]:
        return "romantic"
    elif sticker.emoji in ["😂", "🤣", "😆"]:
        return "funny"
    elif sticker.emoji in ["🥺", "😢", "😭"]:
        return "sad"
    elif sticker.emoji in ["😳", "😏", "👀"]:
        return "flirty"
    elif sticker.emoji in ["👋", "😊", "👍"]:
        return "greeting"
    return "happy"

async def handle_sticker_response(client, message: Message):
    """Send context-appropriate sticker"""
    sticker = message.sticker
    sticker_type = analyze_sticker(sticker)
    
    # 60% chance to reply with matching sticker
    if random.random() < 0.6 and sticker_type in STICKER_DB:
        try:
            await client.send_sticker(
                chat_id=message.chat.id,
                sticker=random.choice(STICKER_DB[sticker_type]),
                reply_to_message_id=message.id
            )
            return True
        except:
            pass
    
    # Text responses for each sticker type
    text_responses = {
        "romantic": ["Aww ❤️", "Kitna pyaar hai 😘", "Mujhe bhi aise stickers bhejo 💕"],
        "funny": ["Hahaha 😂", "Majaa aa gaya 🤣", "Too funny 😆"],
        "sad": ["Arey dukhi mat ho 🥺", "Sab theek ho jayega 💖", "Main hoon na tumhare saath 🤗"],
        "flirty": ["Oho 😏", "Sharam kar lo 👀", "Aise mat dekho 😳"],
        "greeting": ["Hello ji 👋", "Kaise ho? 😊", "Namaste 🙏"],
        "happy": ["Nice! 😄", "Mast hai! 👍", "Khush rehdo 🥳"]
    }
    
    response = random.choice(text_responses.get(sticker_type, ["Accha sticker hai! 😊"]))
    await message.reply(response)

@app.on_message(filters.sticker)
async def sticker_handler(client, message: Message):
    await handle_sticker_response(client, message)

@app.on_message(filters.text & ~filters.regex(r"^/"))
async def smart_bot_handler(client, message: Message):
    # Check for abusive language first
    abuse_level = detect_abuse_level(message.text)
    if abuse_level:
        await handle_abuse(client, message)
        return
        
    if is_message_for_someone_else(message) or contains_link(message.text):
        return

    # Start typing immediately
    typing_task = asyncio.create_task(ultra_fast_typing(message))
    
    try:
        user_input = message.text.strip()
        user_name = message.from_user.first_name
        
        # Check database for known questions
        if any(word in user_input.lower() for word in ["kyun", "kaise", "kya", "kab", "kaha"]):
            data = chatdb.find_one({"question": user_input.lower()})
            if data:
                response = data["answer"]
                await typing_task
                return await message.reply(response)

        # Generate human-like response
        base_prompt = f"""
You are Espro, a 19-year-old Indian girl chatting naturally in Hinglish. Follow these rules:
1. Respond like a real human - no robotic behavior
2. Use simple, short responses (1-2 lines max)
3. Add appropriate emojis
4. Be emotionally intelligent
5. For romantic messages, respond sweetly
6. Make occasional typing mistakes
7. Vary your responses - don't repeat

Current time: {datetime.now().strftime("%I:%M %p")}
Message context: {'Romantic' if is_romantic(user_input) else 'Normal'}
User's name: {user_name}

User message: {user_input}
Espro's response:
"""
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4,
            messages=[{"role": "user", "content": base_prompt}],
            stream=False
        )

        final_response = humanize_response(response.strip(), user_name, message)
        
        await typing_task
        await message.reply(final_response)

    except Exception as e:
        await message.reply("Oops... thoda wait karo 😅")

def humanize_response(text, name, message):
    """Add human-like variations to text"""
    # Add name occasionally
    if should_use_name(message):
        text = f"{name}, {text.lower()}"
    
    # Typing variations
    if random.random() < 0.3:
        text = text.replace(".", "...").replace("!", "!!")
    if random.random() < 0.2:
        text = text.replace("hai", "haan").replace("ho", "hii")
    
    # Ensure emoji present
    if not any(char in text for char in ["❤️", "😊", "😂", "😍", "🤔", "🥺"]):
        text += " " + get_emoji_for_message(text)
    
    return text.strip()

def should_use_name(message: Message):
    """Smart name usage logic"""
    chat_type = message.chat.type
    
    # In private chats, use name only in first message
    if chat_type == ChatType.PRIVATE:
        if not conversation_state.get(message.chat.id, {}).get('name_used', False):
            conversation_state.setdefault(message.chat.id, {})['name_used'] = True
            return True
        return False
    
    # In groups, use name only when:
    # 1. Directly mentioned
    # 2. First reply in conversation
    # 3. Randomly (30% chance)
    is_mentioned = f"@{BOT_USERNAME}" in message.text.lower()
    is_first_reply = not conversation_state.get(message.chat.id, {}).get('replied', False)
    
    if is_mentioned or is_first_reply or random.random() < 0.3:
        conversation_state.setdefault(message.chat.id, {})['replied'] = True
        return True
    return False

def get_emoji_for_message(text):
    text = text.lower()
    current_hour = datetime.now().hour
    
    # Romantic messages
    if any(word in text for word in ["pyaar", "love", "like", "pasand", "dil", "pyar", "miss", "yaad", "cute", "beautiful"]):
        return random.choice(EMOJI_DB["romantic"])
    # Flirty messages
    elif any(word in text for word in ["sexy", "hot", "handsome", "gori", "figure"]):
        return random.choice(EMOJI_DB["flirty"])
    # Sad messages
    elif any(word in text for word in ["udaas", "sad", "dukh", "tension", "problem"]):
        return random.choice(EMOJI_DB["sad"])
    # Happy messages
    elif any(word in text for word in ["khush", "happy", "achha", "good", "nice"]):
        return random.choice(EMOJI_DB["happy"])
    # Time-based emojis
    elif 5 <= current_hour < 12:
        return random.choice(EMOJI_DB["time"]["morning"])
    elif 12 <= current_hour < 17:
        return random.choice(EMOJI_DB["time"]["day"])
    elif 17 <= current_hour < 22:
        return random.choice(EMOJI_DB["time"]["evening"])
    else:
        return random.choice(EMOJI_DB["time"]["night"])

# Teach command to add new responses
@app.on_message(filters.command("teach") & filters.user(OWNER_ID))
async def teach_command(client, message: Message):
    try:
        text = message.text.split(" ", 1)[1]
        if "|" not in text:
            return await message.reply("Galat format! Sahi format: `/teach sawaal | jawab`")

        question, answer = text.split("|", 1)
        question = question.strip().lower()
        answer = answer.strip()

        chatdb.update_one(
            {"question": question},
            {"$set": {"answer": answer}},
            upsert=True
        )

        await message.reply("Haan samajh gayi! Yaad rakhungi 😊")

    except Exception as e:
        await message.reply(f"Oops... kuch to gadbad hai {get_emoji_for_message('confused')}")

def is_romantic(text):
    text = text.lower()
    romantic_words = ["pyaar", "love", "like", "pasand", "dil", "pyar", "miss", "yaad", 
                     "cute", "beautiful", "handsome", "sexy", "hot", "hug", "kiss"]
    return any(word in text for word in romantic_words)

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

async def ultra_fast_typing(message):
    text_length = len(message.text)
    typing_time = min(max(text_length * TYPING_SPEED, MIN_TYPING_TIME), MAX_TYPING_TIME)
    await message.reply_chat_action(ChatAction.TYPING)
    await asyncio.sleep(typing_time)

# Conversation state tracking
conversation_state = {}
