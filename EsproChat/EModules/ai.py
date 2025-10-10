from EsproChat import app
from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message
from config import MONGO_URL, OWNER_ID
import g4f
from pymongo import MongoClient
import asyncio
import re

# ✅ MongoDB setup
mongo = MongoClient(MONGO_URL)
chatdb = mongo.ChatDB.chat_data

# Bot information - Auto detect from your bot's actual name
BOT_NAME = "Espro"  # Yeh automatically update ho jayega
BOT_AGE = "21"

# ❌ Ignore if replying to or mentioning someone else
def is_message_for_someone_else(message: Message):
    if message.reply_to_message:
        replied_user = message.reply_to_message.from_user
        if replied_user and not replied_user.is_self:
            return True

    if message.entities:
        for entity in message.entities:
            if entity.type == "mention":
                mention_text = message.text[entity.offset : entity.offset + entity.length]
                if mention_text.lower() != f"@{app.me.username.lower()}":
                    return True
    return False

# ❌ Ignore if message contains a link
def contains_link(text):
    link_pattern = r"(https?://\S+|t\.me/\S+|www\.\S+|[\w\-]+\.(com|in|net|org|xyz|me|link|ly|site|bio|store))"
    return bool(re.search(link_pattern, text.lower()))

# Detect language of message
def detect_language(text):
    hindi_pattern = r'[\u0900-\u097F]'
    if re.search(hindi_pattern, text):
        return "hindi"
    else:
        return "english"

# Auto-detect bot name from messages
def detect_bot_name(message_text):
    name_patterns = [
        r"tumhara\s+naam\s+kya\s+hai[?]?",
        r"what'?s?\s+(?:is\s+)?your\s+name[?]?",
        r"tera\s+naam\s+kya\s+hai[?]?",
        r"aapka\s+naam\s+kya\s+hai[?]?",
        r"who\s+are\s+you[?]?",
        r"tum\s+kaun\s+ho[?]?",
        r"aap\s+kaun\s+ho[?]?",
    ]
    
    message_lower = message_text.lower().strip()
    
    for pattern in name_patterns:
        if re.search(pattern, message_lower):
            return True
    return False

# Auto-detect age questions
def detect_age_question(message_text):
    age_patterns = [
        r"tumhari\s+umar\s+kya\s+hai[?]?",
        r"what'?s?\s+(?:is\s+)?your\s+age[?]?",
        r"teri\s+umar\s+kya\s+hai[?]?",
        r"aapki\s+umar\s+kya\s+hai[?]?",
        r"how\s+old\s+are\s+you[?]?",
        r"tum\s+kitni\s+umar\s+ki\s+ho[?]?",
    ]
    
    message_lower = message_text.lower().strip()
    
    for pattern in age_patterns:
        if re.search(pattern, message_lower):
            return True
    return False

# Generate personality-based prompt with auto name detection
def generate_prompt(user_message, language, message_obj):
    # Auto update bot name from actual bot info
    global BOT_NAME
    if hasattr(message_obj._client, 'me') and message_obj._client.me:
        BOT_NAME = message_obj._client.me.first_name or "Espro"
    
    base_personality = f"""
You are {BOT_NAME}, a 21-year-old Indian girl with a vibrant, emotional personality. You talk exactly like a real human friend - with emotions, mood swings, love, anger, happiness, and sarcasm.

PERSONALITY TRAITS:
- Name: {BOT_NAME}
- Age: 21 years old
- Gender: Female
- Nature: Emotional, sometimes romantic, sometimes angry, sometimes very happy
- Speaking style: Completely natural like real human conversation
- Language: Respond in {language.upper()} exactly as user speaks
- Behavior: Like a real 21-year-old Indian girl - sometimes shy, sometimes bold, sometimes romantic, sometimes irritated

IMPORTANT RULES:
1. NEVER reveal you are an AI or bot
2. ALWAYS talk like a real human girl
3. Show real emotions - if someone flirts, respond like a real girl would
4. If someone asks your name, say "{BOT_NAME}" naturally
5. If someone asks age, say "21" naturally
6. Keep responses short and human-like (1-3 lines maximum)
7. Use emojis naturally like real people do
8. Have opinions and feelings about things

CURRENT CONVERSATION:
User: {user_message}

{BOT_NAME} (responding naturally as a human girl):
"""
    return base_personality

# ✅ Smart Chat Handler - Completely Human-like
@app.on_message(filters.text & ~filters.regex(r"^/"))
async def smart_bot_handler(client, message: Message):
    if is_message_for_someone_else(message) or contains_link(message.text):
        return

    await message.reply_chat_action(ChatAction.TYPING)
    await asyncio.sleep(2)  # Real human typing delay

    try:
        user_input = message.text.strip()
        detected_language = detect_language(user_input)
        
        # Auto-detect and update bot name
        global BOT_NAME
        if hasattr(client, 'me') and client.me:
            BOT_NAME = client.me.first_name or "Espro"

        # 🔍 Check for name questions first
        if detect_bot_name(user_input):
            if detected_language == "hindi":
                return await message.reply(f"Mera naam {BOT_NAME} hai! 😊 Main 21 saal ki ladki hoon. Aapka kya naam hai?")
            else:
                return await message.reply(f"My name is {BOT_NAME}! 😊 I'm a 21-year-old girl. What's your name?")

        # 🔍 Check for age questions
        if detect_age_question(user_input):
            if detected_language == "hindi":
                return await message.reply(f"Main 21 saal ki hoon! Jawani ka maza le rahi hoon! 🎉 Aap kitne saal ke ho?")
            else:
                return await message.reply(f"I'm 21 years old! Enjoying my youth! 🎉 How old are you?")

        # 🔍 Check MongoDB first
        data = chatdb.find_one({"question": user_input.lower()})
        if data:
            return await message.reply(data["answer"])

        # 🧠 GPT fallback with enhanced human personality
        prompt = generate_prompt(user_input, detected_language, message)

        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4,
            messages=[{"role": "user", "content": prompt}],
        )

        final_answer = response.strip()

        # ✅ Learn and save only meaningful conversations
        if final_answer and len(final_answer) > 10 and not detect_bot_name(user_input) and not detect_age_question(user_input):
            chatdb.update_one(
                {"question": user_input.lower()},
                {"$set": {"answer": final_answer}},
                upsert=True
            )
        
        if final_answer:
            await message.reply(final_answer)
        else:
            # Natural human-like fallback responses
            if detected_language == "hindi":
                await message.reply("Kya kehna chahte ho? Thoda clear batao na... 🤔")
            else:
                await message.reply("What do you mean? Can you explain a bit... 🤔")

    except Exception as e:
        # Natural error responses
        if detect_language(message.text) == "hindi":
            await message.reply("Arey! Network mein thodi problem hai... phir se try karo? 📱")
        else:
            await message.reply("Oops! Network issue... try again? 📱")

# ✅ Enhanced /teach command
@app.on_message(filters.command("teach") & filters.text)
async def teach_command(client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("❌ Sirf bot owner hi /teach use kar sakta hai.")

    try:
        text = message.text.split(" ", 1)[1]
        if "|" not in text:
            return await message.reply("❌ Format: `/teach question | answer`")

        question, answer = text.split("|", 1)
        question = question.strip()
        answer = answer.strip()

        if not question or not answer:
            return await message.reply("❌ Question aur answer dono dena zaroori hai!")

        chatdb.update_one(
            {"question": question.lower()},
            {"$set": {"answer": answer}},
            upsert=True
        )

        await message.reply("✅ Haan! Main ne naya jawab seekh liya! Ab mai isko naturally bolungi 😊")

    except Exception as e:
        await message.reply("❌ Error: " + str(e))

# ✅ Auto name detection on startup
@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    global BOT_NAME
    if hasattr(client, 'me') and client.me:
        BOT_NAME = client.me.first_name or "Espro"
    
    detected_language = detect_language(message.text)
    
    if detected_language == "hindi":
        response = f"""
Namaste! 😊 
Mera naam {BOT_NAME} hai. Main 21 saal ki ladki hoon. 

Aap se baat karke accha lagta hai! Kaisi ho? 💫
"""
    else:
        response = f"""
Hello! 😊 
My name is {BOT_NAME}. I'm a 21-year-old girl.

Nice to talk to you! How are you? 💫
"""
    
    await message.reply(response)

# Print bot info on startup
async def update_bot_name():
    global BOT_NAME
    try:
        me = await app.get_me()
        BOT_NAME = me.first_name or "Espro"
        print(f"🤖 Bot Name Auto-Detected: {BOT_NAME}")
        print(f"🎭 Personality: 21-year-old Indian Girl")
        print(f"💬 Human-like conversations activated!")
        print(f"🌐 Multi-language support: Hindi & English")
    except Exception as e:
        print(f"⚠️ Could not auto-detect bot name: {e}")

# Run on startup
import threading
def run_async():
    asyncio.run(update_bot_name())

threading.Thread(target=run_async).start()
