from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
from datetime import datetime, timedelta
import random
import time
from EsproChat import app
from config import MONGO_URL

# ------------------- CONFIG -------------------
mongo_client = MongoClient(MONGO_URL)
db = mongo_client["BetGame"]
users = db["users"]

cooldowns = {}

# ------------------- UTILITIES -------------------

def get_user(user_id: int):
    user = users.find_one({"_id": user_id})
    if not user:
        user = {"_id": user_id, "coins": 100, "streak": 0}
        users.insert_one(user)
    return user

def update_user(user_id: int, coins: int, streak: int, last_claim=None):
    data = {"coins": coins, "streak": streak}
    if last_claim:
        data["last_claim"] = last_claim
    users.update_one({"_id": user_id}, {"$set": data}, upsert=True)

# ------------------- /game -------------------

@app.on_message(filters.command("game"))
async def start_command(client, message: Message):
    get_user(message.from_user.id)
    await message.reply_text(
        f"👋 Hello {message.from_user.first_name}!\n"
        f"🎮 Welcome to Life Bet Game!\n\n"
        f"You start with 💰 100 coins.\n"
        f"To bet, use: `/bet 10` or `/bet *`",
        quote=True
    )

# ------------------- /balance -------------------

@app.on_message(filters.command("balance"))
async def check_balance(client, message: Message):
    user = get_user(message.from_user.id)
    await message.reply(f"💼 You currently have {user['coins']} coins.")

# ------------------- /reset -------------------

@app.on_message(filters.command("reset"))
async def reset_coins(client, message: Message):
    update_user(message.from_user.id, coins=100, streak=0)
    await message.reply("🔄 Your coins have been reset to 100.")

# ------------------- /daily -------------------

@app.on_message(filters.command("daily"))
async def daily_bonus(client, message: Message):
    user_id = message.from_user.id
    user = get_user(user_id)
    now = datetime.utcnow()

    last_claim = user.get("last_claim")
    if last_claim:
        last_claim_time = datetime.fromisoformat(last_claim)
        if now < last_claim_time + timedelta(hours=24):
            remaining = (last_claim_time + timedelta(hours=24)) - now
            hours = remaining.seconds // 3600
            mins = (remaining.seconds % 3600) // 60
            return await message.reply(
                f"🕒 Wait {remaining.days}d {hours}h {mins}m for your next daily bonus."
            )

    bonus = 50
    new_coins = user["coins"] + bonus
    update_user(user_id, coins=new_coins, streak=user["streak"], last_claim=now.isoformat())
    await message.reply(f"🎁 You got +{bonus} coins!\n💰 Total: {new_coins} coins.")

# ------------------- /bet -------------------

@app.on_message(filters.command("bet"))
async def bet_game(client: Client, message: Message):
    user_id = message.from_user.id
    name = message.from_user.mention
    args = message.text.split()

    now = time.time()
    if user_id in cooldowns and now - cooldowns[user_id] < 5:
        return await message.reply("⏳ Please wait 5 seconds before betting again.")
    cooldowns[user_id] = now

    if len(args) != 2:
        return await message.reply("❌ Usage: /bet <amount>\nExample: /bet 10 or /bet *")

    user = get_user(user_id)

    if args[1] == "*":
        bet_amount = user["coins"]
    elif args[1].isdigit():
        bet_amount = int(args[1])
    else:
        return await message.reply("❌ Invalid amount.\nUse: /bet 10 or /bet *")

    if bet_amount <= 0:
        return await message.reply("❌ Bet amount must be more than 0.")
    if bet_amount > user["coins"]:
        return await message.reply("🚫 Not enough coins!")

    win = random.choice([True, False])

    if win:
        new_coins = user["coins"] + bet_amount
        new_streak = user["streak"] + 1
        update_user(user_id, new_coins, new_streak)

        await message.reply_photo(
            photo="https://i.imgur.com/F7N5Z4S.png",
            caption=(
                f"🎰 {name} has bet {bet_amount} coins\n"
                f"Oh yeah! He came back home with {bet_amount * 2} coins (✅)\n\n"
                f"🎯 <b>Consecutive victories:</b> {new_streak}"
            ),
            parse_mode="HTML"
        )
    else:
        new_coins = user["coins"] - bet_amount
        new_streak = 0
        update_user(user_id, new_coins, new_streak)

        await message.reply_photo(
            photo="https://i.imgur.com/AID8bGS.png",
            caption=(
                f"🎰 {name} has bet {bet_amount} coins\n"
                f"Oh no! He came back home without {bet_amount} coins (❌)."
            )
        )

# ------------------- /top -------------------

@app.on_message(filters.command("top"))
async def top_players(client, message: Message):
    top = users.find().sort("coins", -1).limit(5)
    leaderboard = "🏆 Top 5 Players:\n\n"
    for i, user in enumerate(top, start=1):
        try:
            u = await client.get_users(user["_id"])
            leaderboard += f"{i}. <a href='tg://user?id={u.id}'>{u.first_name}</a> — {user['coins']} coins\n"
        except:
            continue
    await message.reply_text(leaderboard, parse_mode="HTML", disable_web_page_preview=True)

# ------------------- /pay <user_id or reply> <amount> -------------------

@app.on_message(filters.command("pay"))
async def pay_command(client: Client, message: Message):
    sender_id = message.from_user.id
    sender = get_user(sender_id)

    if message.reply_to_message:
        receiver = message.reply_to_message.from_user
    else:
        args = message.text.split()
        if len(args) < 3 or not args[1].isdigit() or not args[2].isdigit():
            return await message.reply("❌ Usage: /pay <user_id or reply> <amount>")
        receiver = await client.get_users(int(args[1]))

    if not receiver or receiver.id == sender_id:
        return await message.reply("❌ Invalid user.")

    amount = int(message.text.split()[-1])
    if amount <= 0:
        return await message.reply("❌ Amount must be more than 0.")
    if amount > sender["coins"]:
        return await message.reply("🚫 You don't have enough coins!")

    receiver_data = get_user(receiver.id)
    update_user(sender_id, coins=sender["coins"] - amount, streak=sender["streak"])
    update_user(receiver.id, coins=receiver_data["coins"] + amount, streak=receiver_data["streak"])

    await message.reply(
        f"✅ You sent {amount} coins to {receiver.mention}.\n💼 Your new balance: {sender['coins'] - amount} coins."
            )
