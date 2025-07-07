from EsproChat import app
from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message
import g4f
from pymongo import MongoClient
import asyncio

# 🔧 Config
BOT_USERNAME = "MissEsproBot"  # without @
OWNER_ID = 7666870729
MONGO_URI = "mongodb+srv://esproaibot:esproai12307@espro.rz2fl.mongodb.net/?retryWrites=true&w=majority&appName=Espro"

# ✅ MongoDB setup
mongo = MongoClient(MONGO_URI)
chatdb = mongo.ChatDB.chat_data

# ❌ Ignore if replying/mentioning someone other than the bot
def is_message_for_someone_else(message: Message):
    # Ignore if replying to someone (not bot)
    if message.reply_to_message:
        replied_user = message.reply_to_message.from_user
        if replied_user and not replied_user.is_self:
            return True

    # Ignore if mentioning anyone other than the bot
    if message.entities:
        for entity in message.entities:
            if entity.type == "mention":
                mention_text = message.text[entity.offset : entity.offset + entity.length]
                if mention_text.lower() != f"@{BOT_USERNAME.lower()}":
                    return True
    return False

# ✅ Main smart chat handler
@app.on_message(filters.text & ~filters.regex(r"^/"))
async def smart_bot_handler(client, message: Message):
    if message.chat.type == "private":
        pass
    elif message.chat.type in ("group", "supergroup"):
        if is_message_for_someone_else(message):
            return  # ❌ Ignore group messages that tag or reply to others

    await message.reply_chat_action(ChatAction.TYPING)
    await asyncio.sleep(1)

    try:
        user_input = message.text.strip().lower()

        # 🔍 Check MongoDB first
        data = chatdb.find_one({"question": user_input})
        if data:
            return await message.reply(data["answer"])

        # 🧠 GPT fallback prompt
        prompt = f"""
Tum ek real ladki ho. Har reply chhoti aur friendly Hindi mein do. Sirf 1-2 line likho.

User: {message.text}
Espro:
"""

        # GPT reply
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4,  # Safe model
            messages=[{"role": "user", "content": prompt}],
        )

        final_answer = response.strip()

        # ✅ Save learned reply to MongoDB
        if final_answer:
            chatdb.update_one(
                {"question": user_input},
                {"$set": {"answer": final_answer}},
                upsert=True
            )
            await message.reply(final_answer)
        else:
            await message.reply("😓 Mujhe jawab nahi mila...")

    except Exception as e:
        await message.reply("😓 Error:\n" + str(e))

# ✅ /teach command (Only Owner Allowed)
@app.on_message(filters.command("teach") & filters.text)
async def teach_command(client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("❌ Sirf bot owner hi /teach use kar sakta hai.")

    try:
        text = message.text.split(" ", 1)[1]
        if "|" not in text:
            return await message.reply("❌ Format:\n`/teach question | answer`")

        question, answer = text.split("|", 1)
        question = question.strip().lower()
        answer = answer.strip()

        chatdb.update_one(
            {"question": question},
            {"$set": {"answer": answer}},
            upsert=True
        )

        await message.reply("✅ Bot ne naya jawab yaad kar liya!")

    except Exception as e:
        await message.reply("😓 Error:\n" + str(e))
