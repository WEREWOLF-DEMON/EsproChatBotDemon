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
import re
import emoji

# MongoDB setup
mongo = MongoClient(MONGO_URL)
chatdb = mongo.ChatDB.chat_data

# Typing config
TYPING_SPEED = 0.003  # Ultra-fast typing
MIN_TYPING_TIME = 0.1  # Minimum typing delay
MAX_TYPING_TIME = 0.8  # Maximum typing delay

# Enhanced Sticker Database
STICKER_DB = {
    "romantic": [
        "CAACAgQAAxkBAAICfmh7FWZSHFJEXnW0SqMyGjtF7GBCAALXEQACMO4JUpqFa3kNXiSNHgQ",
        "CAACAgEAAxkBAAICemh7FTtL5LoJGj61Jf705Sttt2XvAAKbAwACIZGZR_UlcXmwWjWeHgQ"
    ],
    "flirty": [
        "CAACAgUAAxkBAAIClmh7F6zVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICl2h7F7DVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E"
    ],
    "happy": [
        "CAACAgUAAxkBAAICmGh7F7TVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICmWh7F7jVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E"
    ]
}

# Complete Emoji Database
EMOJI_DB = {
    "romantic": ["❤️", "🥰", "💖", "😘", "💕"],
    "happy": ["😊", "☺️", "✨", "🌸", "🎉"],
    "flirty": ["😳", "😏", "😉", "👀", "💋"]
}

# Conversation state tracking
conversation_state = {}

async def ultra_fast_typing(message):
    """Optimized typing simulation"""
    text_length = len(message.text)
    typing_time = min(max(text_length * TYPING_SPEED, MIN_TYPING_TIME), MAX_TYPING_TIME)
    await message.reply_chat_action(ChatAction.TYPING)
    await asyncio.sleep(typing_time)

def is_message_for_me(message: Message) -> bool:
    """Smart message detection with 3 checks"""
    # 1. Check if it's a direct message
    if message.chat.type == ChatType.PRIVATE:
        return True
    
    # 2. Check if replying to me
    if message.reply_to_message and message.reply_to_message.from_user.is_self:
        return True
    
    # 3. Check if mentioning me
    if message.entities:
        for entity in message.entities:
            if entity.type == "mention":
                mention = message.text[entity.offset:entity.offset+entity.length].lower()
                if mention == f"@{BOT_USERNAME.lower()}":
                    return True
    return False

async def generate_instant_response(user_input: str) -> str:
    """Pre-defined quick responses for common queries"""
    quick_responses = {
        "hi": ["Hello! 😊", "Hi there! 👋", "Namaste! 🙏"],
        "how are you": ["I'm good! 😄", "Mast hu! 😎", "Badhiya! 👍"],
        "what's your name": ["I'm Espro! 😊", "Mera naam Espro hai! 💖", "Espro bol sakte ho 😘"],
        "good morning": ["Shubh prabhat! 🌄", "Good morning! ☀️", "Namaste! 🌞"],
        "good night": ["Shubh ratri! 🌙", "Sweet dreams! 💤", "Good night! 🌃"]
    }
    
    user_input = user_input.lower().strip("?,.!")
    for pattern, responses in quick_responses.items():
        if pattern in user_input:
            return random.choice(responses)
    return None

async def handle_sticker_reply(client, message: Message, text: str):
    """Smart sticker replies with context"""
    text = text.lower()
    sticker_type = None
    
    if any(word in text for word in ["pyaar", "love", "like", "romantic"]):
        sticker_type = "romantic"
    elif any(word in text for word in ["cute", "beautiful", "sexy", "hot"]):
        sticker_type = "flirty"
    elif any(word in text for word in ["happy", "khush", "achha", "good"]):
        sticker_type = "happy"
    
    if sticker_type and random.random() < 0.4:  # 40% chance to reply with sticker
        try:
            await client.send_sticker(
                chat_id=message.chat.id,
                sticker=random.choice(STICKER_DB[sticker_type]),
                reply_to_message_id=message.id
            )
            return True
        except Exception as e:
            print(f"Sticker error: {e}")
            return False
    return False

@app.on_message(filters.text & ~filters.command)
async def lightning_fast_handler(client, message: Message):
    """Ultra-optimized message handler"""
    try:
        # Step 1: Check if message is for me
        if not is_message_for_me(message):
            return
        
        # Step 2: Start typing immediately
        typing_task = asyncio.create_task(ultra_fast_typing(message))
        
        # Step 3: Check for instant response
        user_input = message.text.strip()
        instant_response = await generate_instant_response(user_input)
        
        if instant_response:
            await typing_task
            return await message.reply(instant_response)
        
        # Step 4: Try sticker reply
        sticker_sent = await handle_sticker_reply(client, message, user_input)
        if sticker_sent:
            await typing_task
            return
        
        # Step 5: Generate smart response
        base_prompt = f"""You're Espro, a friendly Indian AI assistant. Respond in casual Hinglish (Hindi+English) with emojis. Keep responses under 2 sentences.

Current time: {datetime.now().strftime("%I:%M %p")}
Message: {user_input}
Response:"""
        
        try:
            response = await g4f.ChatCompletion.create_async(
                model=g4f.models.gpt_4,
                messages=[{"role": "user", "content": base_prompt}],
                timeout=8  # Faster timeout
            )
            final_response = response.strip()
            
            # Add emoji if missing
            if not any(char in final_response for char in ["❤️", "😊", "😂", "🥰", "😘"]):
                final_response += " " + random.choice(EMOJI_DB["happy"])
            
            await typing_task
            await message.reply(final_response)
            
            # Cache factual responses
            if any(word in user_input.lower() for word in ["kyun", "kaise", "kya", "what", "how", "why"]):
                chatdb.update_one(
                    {"question": user_input.lower()},
                    {"$set": {"answer": final_response}},
                    upsert=True
                )
                
        except Exception as e:
            await typing_task
            await message.reply(random.choice([
                "Hmm... samajh nahi aaya 😅",
                "Phir se try karo? 🤔",
                "Network issue lag raha hai...",
                "Thoda aur clear puchoge? 😊"
            ]))
            
    except Exception as e:
        print(f"Handler error: {e}")
        await message.reply("Oops... thoda wait karo 😅")

@app.on_message(filters.command("teach"))
async def enhanced_teach_command(client, message: Message):
    """Powerful teach command with validation"""
    if message.from_user.id != OWNER_ID:
        return await message.reply("Sorry, only my owner can teach me! 😊")
    
    try:
        # Extract question and answer
        _, payload = message.text.split(maxsplit=1)
        if "|" not in payload:
            return await message.reply("Format: /teach question | answer\nExample: /teach What's your age? | I'm 19 years old 😊")
            
        question, answer = payload.split("|", 1)
        question = question.strip().lower()
        answer = answer.strip()
        
        # Validate input
        if not question or not answer:
            return await message.reply("Both question and answer are required! 😊")
            
        if len(question) > 150 or len(answer) > 150:
            return await message.reply("Please keep both under 150 characters! 😊")
        
        # Store in database
        chatdb.update_one(
            {"question": question},
            {"$set": {"answer": answer}},
            upsert=True
        )
        
        await message.reply(f"✅ Learned successfully!\n\nQ: {question}\nA: {answer}\n\nNow I'll remember this! 😊")
        
    except Exception as e:
        await message.reply(f"Oops! Error: {str(e)}\n\nCorrect format: /teach question | answer")
