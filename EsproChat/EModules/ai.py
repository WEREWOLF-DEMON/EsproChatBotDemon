from EsproChat import app
from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message
from config import MONGO_URL, OWNER_ID  # ✅ Corrected this line
import g4f
from pymongo import MongoClient
import asyncio
import re

# ✅ MongoDB setup
mongo = MongoClient(MONGO_URL)
chatdb = mongo.ChatDB.chat_data

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
                if mention_text.lower() != f"@{BOT_USERNAME.lower()}":
                    return True
    return False

# ❌ Ignore if message contains a link
def contains_link(text):
    link_pattern = r"(https?://\S+|t\.me/\S+|www\.\S+|[\w\-]+\.(com|in|net|org|xyz|me|link|ly|site|bio|store))"
    return bool(re.search(link_pattern, text.lower()))

# ✅ Human-like typing delays
async def human_typing(message):
    text_length = len(message.text)
    typing_time = min(max(text_length * 0.05, 1), 3)  # 0.05s per character, min 1s, max 3s
    await message.reply_chat_action(ChatAction.TYPING)
    await asyncio.sleep(typing_time)

# ✅ Dynamic Emoji Selector
def get_emoji_for_message(text):
    text = text.lower()
    
    # Romantic messages
    if any(word in text for word in ["pyaar", "love", "like", "pasand", "dil", "pyar", "miss"]):
        return random.choice(["❤️", "🥰", "💖", "😘", "💕"])
    
    # Happy messages
    elif any(word in text for word in ["khush", "happy", "achha", "good", "nice"]):
        return random.choice(["😊", "☺️", "✨", "🌸", "🎉"])
    
    # Sad messages
    elif any(word in text for word in ["udaas", "sad", "dukh", "tension", "problem"]):
        return random.choice(["🥺", "😔", "😢", "💔", "😞"])
    
    # Flirty messages
    elif any(word in text for word in ["cute", "beautiful", "handsome", "sexy", "hot"]):
        return random.choice(["😳", "👀", "💋", "😏", "😉"])
    
    # Default emoji based on time
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        return "🌞"  # Morning
    elif 12 <= current_hour < 17:
        return "😎"  # Afternoon
    elif 17 <= current_hour < 22:
        return "🌙"  # Evening
    else:
        return "✨"  # Night

# ✅ Sticker Responder
async def send_context_sticker(client, message, text):
    text = text.lower()
    
    # Romantic stickers
    if any(word in text for word in ["pyaar", "love", "chumma", "pyar", "hug"]):
        sticker_id = random.choice([
            "CAACAgUAAxkBAAICbWh7FKwivGnaDMUYtfTgUIOqeYVoAAIkGAACJtxwVxlSuVnRcaJbHgQ",  # Replace with actual sticker IDs
            "CAACAgUAAxkBAAICcGh7FNHNNsQ08dfKy6hJ_Sut_ZB0AAJsGAACLn_gV6C4NxtVTJJ-HgQ",
            "CAACAgUAAxkBAAICdGh7FO-X_IcyVry1J5waNvRJPBJbAALpFAAC_4ThVwuGqcXQHPlQHgQ"
        ])
    
    # Shy stickers for flirty messages
    elif any(word in text for word in ["cute", "beautiful", "sexy", "hot"]):
        sticker_id = random.choice([
            "CAACAgUAAxkBAAICd2h7FRA-rTHHwwuThaaCBe_iL3QAAycQAAIxiXhUOHDGuGPyIdMeBA",
            "CAACAgEAAxkBAAICemh7FTtL5LoJGj61Jf705Sttt2XvAAKbAwACIZGZR_UlcXmwWjWeHgQ",
            "CAACAgQAAxkBAAICfmh7FWZSHFJEXnW0SqMyGjtF7GBCAALXEQACMO4JUpqFa3kNXiSNHgQ"
        ])
    
    # Happy stickers
    elif any(word in text for word in ["happy", "khush", "achha", "good"]):
        sticker_id = random.choice([
            "CAACAgQAAxkBAAICgWh7Fhq9p4BdQnaqeRmIeIf1sHHkAAIMCgACKM7RUsygu40CSdsTHgQ",
            "CAACAgUAAxkBAAIChGh7FkFle5KZYUDCAAHOrP5JnoohEAACGBUAAuWteVdCjQ7H8dJbBB4E",
            "CAACAgUAAxkBAAICiGh7FqEtpn-u4ibZf88L6UtC2HnuAAKUFgACf0WAVfN0pe7cEmo6HgQ"
        ])
    else:
        return False
    
    try:
        await client.send_sticker(
            chat_id=message.chat.id,
            sticker=sticker_id,
            reply_to_message_id=message.id
        )
        return True
    except:
        return False

# ✅ Smart Chat Handler
@app.on_message(filters.text & ~filters.regex(r"^/"))
async def smart_bot_handler(client, message: Message):
    if is_message_for_someone_else(message) or contains_link(message.text):
        return

    await human_typing(message)

    try:
        user_input = message.text.strip()
        user_name = message.from_user.first_name

        # 🔍 Check MongoDB first (only for factual questions)
        if any(word in user_input.lower() for word in ["kyun", "kaise", "kya", "kab"]):
            data = chatdb.find_one({"question": user_input.lower()})
            if data:
                return await message.reply(data["answer"] + " " + get_emoji_for_message(user_input))

        # Random sticker response (30% chance for eligible messages)
        if random.random() < 0.3:
            sticker_sent = await send_context_sticker(client, message, user_input)
            if sticker_sent:
                await asyncio.sleep(0.5)  # Small delay after sticker

        # 🧠 Generate human-like response
        base_prompt = f"""
Tum Espro ho - ek 19 saal ki ladki jo bilkul natural insaan ki tarah baat karti hai. Tumhe emojis aur casual Hinglish mein baat karna pasand hai.

Important Rules:
1. Kabhi bhi AI ya bot ki tarah mat bolna
2. 1-2 lines se zyada mat likhna
3. Message ke hisaab se perfect emoji use karna
4. Romantic/Flirty messages ko casually handle karna
5. Thoda informal likho (like "koi" ki jagah "koii")
6. Message ke context ke hisaab se react karna

Current Mood: {'Romantic' if is_romantic(user_input) else 'Normal'}
Time: {'Night' if 22 <= datetime.now().hour < 5 else 'Evening' if 17 <= datetime.now().hour < 22 else 'Day'}

User ({user_name}): {user_input}
Espro (casual reply):
"""

        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4,
            messages=[{"role": "user", "content": base_prompt}],
        )

        final_answer = response.strip()
        
        # Add dynamic emoji if missing
        if not any(char in final_answer for char in ["❤️", "😊", "😂", "😍", "🤔", "🥺"]):
            final_answer += " " + get_emoji_for_message(user_input)

        # Human-like text variations
        if random.random() < 0.3:
            final_answer = final_answer.replace(".", "...").replace("!", "!!")
        
        if random.random() < 0.2:
            final_answer = final_answer.lower().replace("hai", "haan").replace("ho", "hii")

        if final_answer:
            # Sometimes send sticker instead of text (10% chance)
            if random.random() < 0.1:
                sticker_sent = await send_context_sticker(client, message, user_input)
                if sticker_sent:
                    return
            
            # Save only factual responses
            if any(word in user_input.lower() for word in ["kyun", "kaise", "kya", "kab"]):
                chatdb.update_one(
                    {"question": user_input.lower()},
                    {"$set": {"answer": final_answer}},
                    upsert=True
                )
            
            await message.reply(final_answer)
        else:
            await message.reply("Samajh nahi aaya... " + get_emoji_for_message("confused"))

    except Exception as e:
        error_msg = random.choice([
            "Arey... kuch gadbad ho gaya 😅",
            "Oops... phir se try karo",
            "Lagta hai network mein dikkat hai...",
            "Thodi der baad message karna..."
        ])
        await message.reply(error_msg)

# ✅ Romantic message detection
def is_romantic(text):
    text = text.lower()
    romantic_words = ["pyaar", "love", "like", "pasand", "dil", "pyar", "miss", "yaad", 
                     "cute", "beautiful", "handsome", "sexy", "hot", "hug", "kiss"]
    return any(word in text for word in romantic_words)

# ✅ /teach command (only for factual information)
@app.on_message(filters.command("teach") & filters.text)
async def teach_command(client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("Ye option mere liye nahi hai... " + get_emoji_for_message("no"))

    try:
        text = message.text.split(" ", 1)[1]
        if "|" not in text:
            return await message.reply("Galat format! Sahi format: `/teach sawaal | jawab`")

        question, answer = text.split("|", 1)
        question = question.strip().lower()
        answer = answer.strip()

        # Only allow teaching factual information
        if not any(word in question for word in ["kyun", "kaise", "kya", "kab", "kaha"]):
            return await message.reply("Main sirf facts yaad kar sakti hu... " + get_emoji_for_message("sorry"))

        chatdb.update_one(
            {"question": question},
            {"$set": {"answer": answer}},
            upsert=True
        )

        await message.reply("Haan samajh gayi! Yaad rakhungi " + get_emoji_for_message("happy"))

    except Exception as e:
        await message.reply("Oops... kuch to gadbad hai " + get_emoji_for_message("confused"))
