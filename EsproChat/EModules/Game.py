from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
import random
from EsproChat import app

MONGO_URL = "mongodb://localhost:27017"  # ⚠️ Replace with your Mongo 
mongo_client = MongoClient(MONGO_URL)
db = mongo_client["BetGame"]
users = db["users"]

# ------------------- UTILITIES -------------------

def get_user(user_id: int):
    user = users.find_one({"_id": user_id})
    if not user:
        users.insert_one({"_id": user_id, "coins": 100, "streak": 0})
        return {"_id": user_id, "coins": 100, "streak": 0}
    return user

def update_user(user_id: int, coins: int, streak: int):
    users.update_one({"_id": user_id}, {"$set": {"coins": coins, "streak": streak}}, upsert=True)

# ------------------- COMMAND: /start -------------------

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    user = get_user(message.from_user.id)
    await message.reply_text(
        f"👋 Hello {message.from_user.first_name}!\n"
        f"🎮 Welcome to Life Bet Game!\n\n"
        f"You start with 💰 {user['coins']} coins.\n"
        f"To bet, type: Bbet 1 or Bbet *"
    )

# ------------------- COMMAND: /balance -------------------

@app.on_message(filters.command("balance"))
async def check_balance(client, message: Message):
    user = get_user(message.from_user.id)
    await message.reply(f"💼 You currently have {user['coins']} coins.")

# ------------------- COMMAND: /reset -------------------

@app.on_message(filters.command("reset"))
async def reset_coins(client, message: Message):
    update_user(message.from_user.id, coins=100, streak=0)
    await message.reply("🔄 Your coins have been reset to 100.")

# ------------------- COMMAND: Bbet -------------------

@app.on_message(filters.command("bbet", prefixes=["B", "b"]))
async def bet_game(client: Client, message: Message):
    user_id = message.from_user.id
    name = message.from_user.mention
    args = message.text.split()

    if len(args) != 2:
        return await message.reply("❌ Usage: Bbet <amount>\nExample: Bbet 10 or Bbet *")

    user = get_user(user_id)

    # Handle "*"
    if args[1] == "*":
        bet_amount = user["coins"]
    else:
        if not args[1].isdigit():
            return await message.reply("❌ Invalid amount.\nUse: Bbet 10 or Bbet *")
        bet_amount = int(args[1])

    if bet_amount <= 0:
        return await message.reply("❌ Bet amount must be greater than 0.")
    if bet_amount > user["coins"]:
        return await message.reply("🚫 You don't have enough coins to bet!")

    win = random.choice([True, False])

    if win:
        new_coins = user["coins"] + bet_amount
        new_streak = user["streak"] + 1
        update_user(user_id, new_coins, new_streak)
        await message.reply_photo(
            photo="https://i.imgur.com/F7N5Z4S.png",
            caption=(
                f"🎰 {name} has bet {bet_amount} coins\n"
                f"🎉 He won and now has {new_coins} coins!\n"
                f"🔥 Streak: {new_streak}"
            )
        )
    else:
        new_coins = user["coins"] - bet_amount
        new_streak = 0
        update_user(user_id, new_coins, new_streak)
        await message.reply_photo(
            photo="https://i.imgur.com/AID8bGS.png",
            caption=(
                f"🎰 {name} has bet {bet_amount} coins\n"
                f"😢 He lost and now has {new_coins} coins."
            )
        )
