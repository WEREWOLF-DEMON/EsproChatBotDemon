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

# Ignore matplotlib font warnings
warnings.filterwarnings("ignore", category=UserWarning)

# MongoDB Setup
mongo_client = MongoClient(MONGO_URL)
db = mongo_client["EsproMain"]
messages_col = db["messages"]

# ✅ Track each message daily per user
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

# 🎨 Generate leaderboard image
def generate_bar_chart(data: list, title: str):
    names = [item["name"][:12] + "..." if len(item["name"]) > 15 else item["name"] for item in data]
    counts = [item["count"] for item in data]

    plt.rcParams.update({
        "text.color": "white",
        "axes.labelcolor": "white",
        "xtick.color": "white",
        "ytick.color": "white",
        "axes.edgecolor": "white"
    })

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor("#1e001e")
    ax.set_facecolor("#1e001e")

    bars = ax.barh(names[::-1], counts[::-1], color="#e84d78")

    ax.set_title("LEADERBOARD", fontsize=22, fontweight="bold", color="white", pad=20)
    ax.set_xlabel("Messages", fontsize=12)
    ax.grid(True, axis='x', linestyle="--", alpha=0.3)

    for bar in bars:
        width = bar.get_width()
        ax.text(width + 3, bar.get_y() + bar.get_height() / 2, str(width),
                va='center', color='white', fontsize=10)

    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", dpi=300, facecolor=fig.get_facecolor())
    buffer.name = "leaderboard.png"
    buffer.seek(0)
    plt.close()
    return buffer

# 📊 Fetch leaderboard data
async def get_leaderboard(chat_id, mode):
    query = {"chat_id": chat_id}

    if mode == "today":
        query["date"] = datetime.utcnow().strftime("%Y-%m-%d")
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
            name = user.first_name or "User"
        except:
            name = str(r["_id"])
        leaderboard.append({
            "name": name,
            "user_id": r["_id"],
            "count": r["count"]
        })

    return leaderboard

# 📌 /rankings command
@app.on_message(filters.command("rankings"))
async def rankings_cmd(_, message: Message):
    try:
        await message.delete()  # 🗑️ Command message delete
    except:
        pass  # Agar bot ke paas delete permission na ho, toh error na aaye

    await send_leaderboard(message, "overall")  # 📊 Rankings send

# 🔁 Callback: overall, today, week
@app.on_callback_query(filters.regex("^(today|overall|week)$"))
async def leaderboard_callback(_, query: CallbackQuery):
    await send_leaderboard(query.message, query.data, edit=True)

# 📤 Send chart + text leaderboard
async def send_leaderboard(message_or_msg, mode, edit=False):
    chat_id = message_or_msg.chat.id
    leaderboard = await get_leaderboard(chat_id, mode)

    if not leaderboard:
        text = "No data available for this period."
        if edit:
            return await message_or_msg.edit_text(text)
        return await message_or_msg.reply(text)

    chart = generate_bar_chart(leaderboard, mode.upper())

    caption = f"📈 **{mode.capitalize()} Leaderboard**\n\n"
    total_count = sum(item["count"] for item in leaderboard)

    for idx, item in enumerate(leaderboard, start=1):
        try:
            user = await app.get_users(item["user_id"])
            mention = user.mention
        except:
            mention = f"`{item['user_id']}`"
        caption += f"**{idx}.** {mention} • `{item['count']}` \n"

    caption += f"\n📩 **Total messages:** `{total_count}`"

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

    if edit:
        await message_or_msg.delete()
        await message_or_msg.reply_photo(chart, caption=caption, reply_markup=markup)
    else:
        await message_or_msg.reply_photo(chart, caption=caption, reply_markup=markup)
