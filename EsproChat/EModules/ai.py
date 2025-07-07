from EsproChat import app
from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message
import g4f
from pymongo import MongoClient

# 🔧 Bot config
BOT_USERNAME = "MissEsproBot"  # 👈 without @
OWNER_ID = 7666870729  # 👈 Replace with your Telegram user ID
MONGO_URI = "mongodb+srv://esproaibot:esproai12307@espro.rz2fl.mongodb.net/?retryWrites=true&w=majority&appName=Espro"  # 👈 Replace this

# ✅ MongoDB setup
mongo = MongoClient(MONGO_URI)
chatdb = mongo.ChatDB.chat_data

# ❌ Check if message is replying/mentioning someone else (except bot)
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

# ✅ Chat handler (learn + respond)
@app.on_message(filters.text & ~filters.regex(r"^/"))
async def smart_bot_handler(client, message: Message):
    if message.chat.type == "private":
        pass
    elif message.chat.type in ("group", "supergroup"):
        if is_message_for_someone_else(message):
            return

    await message.reply_chat_action(ChatAction.TYPING)

    try:
        user_input = message.text.strip().lower()

        # 🔎 MongoDB check
        data = chatdb.find_one({"question": user_input})
        if data:
            await message.reply(data["answer"])
            return

        # 💬 Prompt
        prompt = f"""
Tum ek reyal ladki ho jitna ek ladki ke aandar hota hai tumare aandar hona chahiye Har reply 1 ya 2 line ka hi do. Friendly aur normal Hindi me baat karo.

User: {message.text}
Espro:
"""

        # 🧠 GPT response
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_3_5_turbo,  # ✅ Use correct model
            messages=[{"role": "user", "content": prompt}],
        )

        final_answer = response.strip()

        # 💾 Save to MongoDB
        chatdb.insert_one({"question": user_input, "answer": final_answer})
        await message.reply(final_answer)

    except Exception as e:
        await message.reply("😓 Error:\n" + str(e))

# ✅ /teach command (manual training)
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
