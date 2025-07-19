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
TYPING_SPEED = 0.003
MIN_TYPING_TIME = 0.1
MAX_TYPING_TIME = 0.8

# Sticker database
STICKER_DB = {
    "romantic": [
        "CAACAgQAAxkBAAICfmh7FWZSHFJEXnW0SqMyGjtF7GBCAALXEQACMO4JUpqFa3kNXiSNHgQ",
        "CAACAgEAAxkBAAICemh7FTtL5LoJGj61Jf705Sttt2XvAAKbAwACIZGZR_UlcXmwWjWeHgQ"
    ],
    "flirty": [
        "CAACAgUAAxkBAAIClmh7F6zVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E",
        "CAACAgUAAxkBAAICl2h7F7DVZ4X2Xj5H5QABrX3AAb0n9QACJxUAAmXZ4Vd7eUz4J8qj3h4E"
    ]
}

# Emoji database
EMOJI_DB = {
    "romantic": ["❤️", "🥰", "💖", "😘", "💕", "💘", "💓", "💞", "💗", "💝"],
    "happy": ["😊", "☺️", "✨", "🌸", "🎉", "😄", "🤗", "🎊", "🥳", "🌼"]
}

async def ultra_fast_typing(message):
    text_length = len(message.text)
    typing_time = min(max(text_length * TYPING_SPEED, MIN_TYPING_TIME), MAX_TYPING_TIME)
    await message.reply_chat_action(ChatAction.TYPING)
    await asyncio.sleep(typing_time)

def is_message_for_me(message: Message) -> bool:
    if message.chat.type == ChatType.PRIVATE:
        return True
    if message.reply_to_message and message.reply_to_message.from_user.is_self:
        return True
    if message.entities:
        for entity in message.entities:
            if entity.type == "mention":
                mention = message.text[entity.offset:entity.offset + entity.length].lower()
                if mention == f"@{BOT_USERNAME.lower()}":
                    return True
    return False

async def generate_instant_response(user_input: str) -> str:
    quick_responses = {
        "hi": ["Hello! 😊", "Hi there! 👋", "Namaste! 🙏"],
        "how are you": ["I'm good! 😄", "Mast hu! 😎", "Badhiya! 👍"],
        "what's your name": ["I'm Espro! 😊", "Mera naam Espro hai! 💖", "Espro bol sakte ho 😘"]
    }
    user_input = user_input.lower().strip("?,.!")
    for pattern, responses in quick_responses.items():
        if pattern in user_input:
            return random.choice(responses)
    return None

async def handle_sticker_reply(client, message: Message, text: str):
    text = text.lower()
    sticker_type = None
    if any(word in text for word in ["pyaar", "love", "like"]):
        sticker_type = "romantic"
    elif any(word in text for word in ["cute", "beautiful", "sexy"]):
        sticker_type = "flirty"
    elif any(word in text for word in ["happy", "khush", "achha"]):
        sticker_type = "happy"

    if sticker_type and random.random() < 0.4:
        try:
            await client.send_sticker(
                chat_id=message.chat.id,
                sticker=random.choice(STICKER_DB[sticker_type]),
                reply_to_message_id=message.id
            )
            return True
        except:
            pass
    return False

@app.on_message(filters.text & ~filters.command)
async def lightning_fast_handler(client, message: Message):
    try:
        if not is_message_for_me(message):
            return

        typing_task = asyncio.create_task(ultra_fast_typing(message))
        user_input = message.text.strip()
        instant_response = await generate_instant_response(user_input)

        if instant_response:
            await typing_task
            return await message.reply(instant_response)

        sticker_sent = await handle_sticker_reply(client, message, user_input)
        if sticker_sent:
            await typing_task
            return

        base_prompt = f"You're Espro, respond quickly in Hinglish.\nUser: {user_input}\nBot:"

        try:
            response = await g4f.ChatCompletion.create_async(
                model=g4f.models.gpt_4,
                messages=[{"role": "user", "content": base_prompt}],
                timeout=8
            )
            final_response = response.strip()

            if not any(char in final_response for char in ["❤️", "😊", "😂"]):
                final_response += " " + random.choice(EMOJI_DB["happy"])

            await typing_task
            await message.reply(final_response)

            if any(word in user_input.lower() for word in ["kyun", "kaise", "kya"]):
                chatdb.update_one(
                    {"question": user_input.lower()},
                    {"$set": {"answer": final_response}},
                    upsert=True
                )

        except Exception:
            await typing_task
            await message.reply(random.choice([
                "Hmm... samajh nahi aaya 😅",
                "Phir se try karo? 🤔",
                "Network issue lag raha hai..."
            ]))

    except Exception as e:
        print(f"Error: {e}")
        await message.reply("Oops... thoda wait karo 😅")

@app.on_message(filters.command("teach"))
async def enhanced_teach_command(client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("Sorry, only my owner can teach me!")
    try:
        _, payload = message.text.split(maxsplit=1)
        if "|" not in payload:
            return await message.reply("Format: /teach question | answer")

        question, answer = payload.split("|", 1)
        question = question.strip().lower()
        answer = answer.strip()

        if not question or not answer:
            return await message.reply("Both question and answer required!")

        if len(question) > 150 or len(answer) > 150:
            return await message.reply("Keep both under 150 characters!")

        chatdb.update_one(
            {"question": question},
            {"$set": {"answer": answer}},
            upsert=True
        )

        await message.reply(f"✅ Learned!\n\nQ: {question}\nA: {answer}")

    except Exception as e:
        await message.reply(f"Error: {str(e)}")
