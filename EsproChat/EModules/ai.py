from EsproChat import app
from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message
import g4f
from g4f.models import gpt_4  # ✅ Ensure this matches your g4f version
from pymongo import MongoClient
import asyncio

# 🔧 Config
BOT_USERNAME = "MissEsproBot"  # without @
OWNER_ID = 7666870729
MONGO_URI = "mongodb+srv://esproaibot:esproai12307@espro.rz2fl.mongodb.net/?retryWrites=true&w=majority&appName=Espro"

# ✅ MongoDB setup
mongo = MongoClient(MONGO_URI)
chatdb = mongo.ChatDB.chat_data
chatdb.create_index("question", unique=True)  # Optional but good

# ✅ Smart chat handler (text messages only, no commands)
@app.on_message(filters.text & ~filters.command(["teach"]))
async def smart_bot_handler(client, message: Message):
    # Ignore bot messages
    if message.from_user and message.from_user.is_bot:
        return

    # ✅ Private: always reply
    if message.chat.type == "private":
        pass

    # ✅ Group: reply only if bot is mentioned or replied to
    elif message.chat.type in ("group", "supergroup"):
        is_mentioned = f"@{BOT_USERNAME.lower()}" in message.text.lower()
        is_replied_to_bot = (
            message.reply_to_message
            and message.reply_to_message.from_user
            and message.reply_to_message.from_user.is_self
        )
        if not (is_mentioned or is_replied_to_bot):
            return  # ❌ Ignore if bot not mentioned or not replied

    await message.reply_chat_action(ChatAction.TYPING)
    await asyncio.sleep(min(3, max(1, len(message.text) * 0.03)))  # dynamic typing delay

    try:
        user_input = message.text.strip().lower()

        # 🔍 Check if answer already learned
        data = chatdb.find_one({"question": user_input})
        if data:
            return await message.reply(data["answer"])

        # 🧠 GPT prompt
        prompt = f"""
Tum ek real ladki ho. Har reply chhoti aur friendly Hindi mein do. Sirf 1-2 line likho.

User: {message.text}
Espro:
"""

        # GPT response using g4f
        response = g4f.ChatCompletion.create(
            model=gpt_4,
            messages=[{"role": "user", "content": prompt}],
        )

        final_answer = response.strip()

        if final_answer:
            # ✅ Save to DB
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

# ✅ /teach command (owner/admin/private only)
@app.on_message(filters.command("teach") & filters.text)
async def teach_command(client, message: Message):
    is_owner = message.from_user.id == OWNER_ID
    is_admin = False

    # Check if user is admin (for group only)
    if message.chat.type != "private":
        try:
            member = await client.get_chat_member(message.chat.id, message.from_user.id)
            is_admin = member.status in ("administrator", "creator")
        except:
            pass

    # Only allow owner, admin, or private
    if not (is_owner or is_admin or message.chat.type == "private"):
        return await message.reply("❌ Sirf owner ya admin hi /teach use kar sakta hai.")

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
