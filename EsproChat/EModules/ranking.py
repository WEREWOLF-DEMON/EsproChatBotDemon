import io
import warnings
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from pymongo import MongoClient
from pyrogram import filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from EsproChat import app
from config import MONGO_URL

# 🔕 Suppress matplotlib font warnings
warnings.filterwarnings("ignore", category=UserWarning)

# MongoDB setup
mongo_client = MongoClient(MONGO_URL)
db = mongo_client["EsproMain"]
messages_col = db["messages"]

# ➕ Count Messages for each user per day
@app.on_message(filters.group, group=6)
async def count_messages(_, message: Message):
    if not message.from_user:
        return
    user_id = message.from_user.id
    chat_id = message.chat.id
    today_date = datetime.utcnow().strftime("%Y-%m-%d")

    messages_col.update_one(
        {"chat_id": chat_id, "user_id": user_id, "date": today_date},
        {"$inc": {"count": 1}},
        upsert=True
    )

# 📊 Create Bar Chart
def generate_bar_chart(data: list, title: str):
    names = [item["name"] for item in data]
    counts = [item["count"] for item in data]

    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.barh(names[::-1], counts[::-1], color="#b30059")
    ax.set_title(title)
    ax.set_xlabel("Messages")
    ax.grid(True, axis='x', linestyle='--', alpha=0.5)

    for bar in bars:
        width = bar.get_width()
        ax.text(width + 1, bar.get_y() + bar.get_height() / 2, f'{width}', va='center')

    plt.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    plt.close()
    return buffer

# 📥 Leaderboard from MongoDB
async def get_leaderboard(chat_id, mode):
    query = {"chat_id": chat_id}

    if mode == "today":
        today = datetime.utcnow().strftime("%Y-%m-%d")
        query["date"] = today
    elif mode == "week":
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        query["date"] = {"$gte": one_week_ago.strftime("%Y-%m-%d")}

    pipeline = [
        {"$match": query},
        {"$group": {"_id": "$user_id", "count": {"$sum": "$count"}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]

    results = list(messages_col.aggregate(pipeline))
    leaderboard = []

    for r in results:
        try:
            user = await app.get_users(r["_id"])
            name = user.mention
        except:
            name = f"`{r['_id']}`"
        leaderboard.append({"name": name, "count": r["count"]})

    return leaderboard

# 📌 /rankings command
@app.on_message(filters.command("rankings"))
async def rankings_cmd(_, message: Message):
    await send_leaderboard(message, "overall")

# 🔁 Inline button callback: Today / Week / Overall
@app.on_callback_query(filters.regex("^(today|overall|week)$"))
async def leaderboard_callback(_, query: CallbackQuery):
    mode = query.data
    await send_leaderboard(query.message, mode, edit=True)

# 🖼️ Send leaderboard with chart + caption
async def send_leaderboard(message_or_msg, mode, edit=False):
    chat_id = message_or_msg.chat.id
    leaderboard = await get_leaderboard(chat_id, mode)

    if not leaderboard:
        text = "No data available for this period."
        if edit:
            return await message_or_msg.edit_text(text)
        return await message_or_msg.reply(text)

    # Chart image
    chart = generate_bar_chart(leaderboard, f"{mode.capitalize()} Leaderboard")

    # Text leaderboard
    caption = f"📈 **{mode.capitalize()} Leaderboard**\n\n"
    total_count = sum(item['count'] for item in leaderboard)

    for idx, item in enumerate(leaderboard, start=1):
        caption += f"**{idx}.** {item['name']} • `{item['count']}` messages\n"

    caption += f"\n📩 **Total messages:** `{total_count}`"

    # Inline buttons
    buttons = [
    [
        InlineKeyboardButton("Overall ✅" if mode == "overall" else "Overall", callback_data="overall"),
    ],
    [
        InlineKeyboardButton("Today ✅" if mode == "today" else "Today", callback_data="today"),
        InlineKeyboardButton("Week ✅" if mode == "week" else "Week", callback_data="week"),
    ]
    ]
    markup = InlineKeyboardMarkup(buttons)

    # Send or edit message
    if edit:
        await message_or_msg.delete()
        await message_or_msg.reply_photo(chart, caption=caption, reply_markup=markup)
    else:
        await message_or_msg.reply_photo(chart, caption=caption, reply_markup=markup)
