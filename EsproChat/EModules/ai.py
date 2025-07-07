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

# ✅ Smart chat handler
@app.on_message(filters.text & ~filters.command(["teach"]))
async def smart_bot_handler(client, message: Message):
    # ❌ Ignore if message is for someone else
    if is_message_for_someone_else(message):
        return

    if not message.text:
        return

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
Tum ek sweet, funny aur real ladki ho. Har reply short aur Hindi-English mix mein do, jaise real girl karti hai. Sirf 1-2 line.

User: {message.text}
Espro:
"""

        response = g4f.ChatCompletion.create(
            model=g4f.models.default,
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


# ✅ Manual teach command (silent in groups)
@app.on_message(filters.command("teach") & filters.text)
async def teach_command(client, message: Message):
    is_owner = message.from_user.id == OWNER_ID
    is_admin = False

    if message.chat.type != "private":
        try:
            member = await client.get_chat_member(message.chat.id, message.from_user.id)
            is_admin = member.status in ("administrator", "creator")
        except:
            pass

    if not (is_owner or is_admin or message.chat.type == "private"):
        return  # ❌ Ignore silently if not allowed

    try:
        text = message.text.split(" ", 1)[1]
        if "|" not in text:
            if message.chat.type == "private":
                return await message.reply("❌ Format:\n`/teach question | answer`")
            else:
                return  # ❌ Group me silent

        question, answer = text.split("|", 1)
        question = question.strip().lower()
        answer = answer.strip()

        chatdb.update_one(
            {"question": question},
            {"$set": {"answer": answer}},
            upsert=True
        )

        if message.chat.type == "private":
            await message.reply("✅ Bot ne naya jawab yaad kar liya!")

    except Exception as e:
        if message.chat.type == "private":
            await message.reply("😓 Error:\n" + str(e))
