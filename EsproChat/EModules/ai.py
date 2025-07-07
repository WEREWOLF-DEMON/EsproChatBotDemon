from EsproChat import app
from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message
import g4f
from pymongo import MongoClient

# ✅ Bot Config
BOT_USERNAME = "MissEsproBot"  # 👈 Apna bot username daalein
OWNER_ID = 7666870729          # 👈 Apna Telegram user ID daalein

# ✅ MongoDB Setup (Replace with your actual MongoDB URI)
mongo = MongoClient("mongodb+srv://esproaibot:esproai12307@espro.rz2fl.mongodb.net/?retryWrites=true&w=majority&appName=Espro")
db = mongo["ChatDB"]
replies = db["TrainedReplies"]

# ✅ Get trained reply if available
def get_trained_reply(query: str):
    result = replies.find_one({"question": query.lower()})
    return result["answer"] if result else None

# ✅ Check if bot is mentioned or replied (in groups)
def is_mentioned_or_replied(message: Message):
    if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.is_self:
        return True
    if message.entities:
        for entity in message.entities:
            if entity.type == "mention" and f"@{BOT_USERNAME.lower()}" in message.text.lower():
                return True
    return False

# ✅ Main Chat Handler
@app.on_message(filters.text & ~filters.regex(r"^/"))
async def chat_handler(client, message: Message):
    user_text = message.text.strip().lower()

    # ✅ Group Chat Logic
    if message.chat.type in ("group", "supergroup"):
        if is_mentioned_or_replied(message):
            pass  # reply allowed
        elif message.reply_to_message and not message.reply_to_message.from_user.is_self:
            return  # don't reply if 2 users are talking
        else:
            pass  # single user message, allow

    await message.reply_chat_action(ChatAction.TYPING)

    # ✅ Owner Teaching Logic
    if message.from_user.id == OWNER_ID and user_text.startswith("teach:"):
        try:
            _, pair = user_text.split(":", 1)
            question, answer = map(str.strip, pair.split("|"))
            replies.update_one(
                {"question": question.lower()},
                {"$set": {"answer": answer}},
                upsert=True,
            )
            return await message.reply("✅ Sikha diya!")
        except:
            return await message.reply("❌ Format galat hai. Use:\n`teach: question | answer`")

    # ✅ Trained reply check
    trained = get_trained_reply(user_text)
    if trained:
        return await message.reply(trained)

    # ✅ Fallback to AI
    try:
        prompt = f"""  
Tum ek ladki real dost ho. Har reply chhota, friendly aur Hindi me do. Zyada formal mat bano.  
  
User: {message.text}  
Espro:  
"""  
        response = g4f.ChatCompletion.create(
            model=g4f.models.default,  # ✅ safest option
            messages=[{"role": "user", "content": prompt}],
        )

        if not response or not response.strip():
            raise Exception("Empty response from model.")

        await message.reply(response.strip())

    except Exception as e:
        await message.reply("😓 Error:\n" + str(e))
