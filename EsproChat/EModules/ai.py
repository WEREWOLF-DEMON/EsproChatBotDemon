from EsproChat import app
from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message
import g4f
from pymongo import MongoClient

# ✅ Bot config
BOT_USERNAME = "MissEsproBot"  # 👈 apna bot username
OWNER_ID = 7666870729      # 👈 replace with actual owner ID

# ✅ MongoDB setup
mongo = MongoClient("mongodb+srv://esproaibot:esproai12307@espro.rz2fl.mongodb.net/?retryWrites=true&w=majority&appName=Espro")
db = mongo["ChatDB"]
replies = db["TrainedReplies"]

# ✅ Trained reply fetcher
def get_trained_reply(query: str):
    result = replies.find_one({"question": query.lower()})
    return result["answer"] if result else None

# ✅ Check if bot is mentioned or replied to (for groups)
def is_mentioned_or_replied(message: Message):
    if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.is_self:
        return True
    if message.entities:
        for entity in message.entities:
            if entity.type == "mention" and f"@{BOT_USERNAME.lower()}" in message.text.lower():
                return True
    return False

# ✅ Main chat handler
@app.on_message(filters.text & ~filters.regex(r"^/"))
async def chat_handler(client, message: Message):
    if message.chat.type == "group" or message.chat.type == "supergroup":
        if not is_mentioned_or_replied(message):
            return  # Ignore if bot not tagged/replied to in group

    await message.reply_chat_action(ChatAction.TYPING)
    user_text = message.text.strip().lower()

    # ✅ Owner's teach command
    if message.from_user.id == OWNER_ID and user_text.startswith("teach:"):
        try:
            # Format: teach: question | answer
            _, pair = user_text.split(":", 1)
            question, answer = map(str.strip, pair.split("|"))
            replies.update_one(
                {"question": question.lower()},
                {"$set": {"answer": answer}},
                upsert=True,
            )
            return await message.reply("✅ Sikha diya!")
        except:
            return await message.reply("❌ Format galat hai. Sahi format:\n`teach: question | answer`")

    # ✅ Check if trained reply exists
    trained = get_trained_reply(user_text)
    if trained:
        return await message.reply(trained)

    # ✅ Fallback: AI response
    try:
        prompt = f"""
Tum ek real dost ho. Har reply chhota, friendly aur Hindi me do. Formal mat bano.

User: {message.text}
Bot:
"""
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_3_5_turbo,
            messages=[{"role": "user", "content": prompt}],
        )
        await message.reply(response.strip())

    except Exception as e:
        await message.reply("😓 Error:\n" + str(e))
