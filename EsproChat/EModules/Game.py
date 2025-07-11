from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import PeerIdInvalid
import random
from EsproChat import app  # Make sure EsproChat/__init__.py initializes the Client as `app`

# In-memory user coin data (not persistent)
user_data = {}  # {user_id: {"coins": float, "streak": int}}

# ------------------- /balance -------------------
@app.on_message(filters.command("balance"))
async def balance(client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"coins": 100.0, "streak": 0}
    coins = user_data[user_id]["coins"]
    await message.reply(f"💼 You currently have **{coins:,.3f}** coins.", parse_mode="markdown2")

# ------------------- /pay -------------------
@app.on_message(filters.command("pay"))
async def pay_user(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"coins": 100.0, "streak": 0}

    args = message.text.split()
    if len(args) < 2:
        return await message.reply("❌ Usage: `/pay @username 10` or reply to a user with `/pay 10`", quote=True)

    # Get amount
    try:
        amount = float(args[-1])
    except ValueError:
        return await message.reply("❌ Invalid amount!", quote=True)

    if amount <= 0:
        return await message.reply("❌ Amount must be greater than 0", quote=True)

    # Get target user
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif len(args) == 3 and args[1].startswith("@"):
        username = args[1].replace("@", "")
        try:
            target_user = await client.get_users(username)
        except PeerIdInvalid:
            return await message.reply("❌ User not found.", quote=True)
    else:
        return await message.reply("❌ Mention or reply to a user to send coins.", quote=True)

    target_id = target_user.id
    if target_id == user_id:
        return await message.reply("😅 You can't pay yourself!", quote=True)

    # Transfer coins
    sender = user_data[user_id]
    receiver = user_data.get(target_id, {"coins": 100.0, "streak": 0})

    if sender["coins"] < amount:
        return await message.reply("🚫 You don't have enough coins!", quote=True)

    sender["coins"] = round(sender["coins"] - amount, 3)
    receiver["coins"] = round(receiver["coins"] + amount, 3)
    user_data[target_id] = receiver

    await message.reply(
        f"✅ {message.from_user.mention} sent **{amount:,.3f}** coins to {target_user.mention}.\n"
        f"💰 Your Balance: **{sender['coins']:,.3f}**",
        parse_mode="markdown2"
    )

# ------------------- /bet -------------------
@app.on_message(filters.command("bet"))
async def bet_game(client: Client, message: Message):
    user_id = message.from_user.id
    name = message.from_user.mention
    args = message.text.split()

    if len(args) != 2:
        return await message.reply("❌ Usage: /bet <amount>\nExample: `/bet 1.5`", quote=True)

    try:
        bet_amount = float(args[1])
    except ValueError:
        return await message.reply("❌ Invalid amount!\nExample: `/bet 1.5`", quote=True)

    if bet_amount <= 0:
        return await message.reply("❌ Bet must be more than 0", quote=True)

    if user_id not in user_data:
        user_data[user_id] = {"coins": 100.0, "streak": 0}

    player = user_data[user_id]
    if bet_amount > player["coins"]:
        return await message.reply(f"🚫 Not enough coins! You have {player['coins']:.3f}", quote=True)

    win = random.choice([True, False])

    if win:
        player["coins"] = round(player["coins"] + bet_amount, 3)
        player["streak"] += 1
        await message.reply_photo(
            photo="https://i.imgur.com/F7N5Z4S.png",
            caption=(
                f"🎰 {name} has bet **{bet_amount:,.3f}** coins\n"
                f"🎉 Oh yeah! He came back home with **{bet_amount * 2:,.3f}** coins (✅)\n\n"
                f"🎯 Consecutive victories: **{player['streak']}**\n"
                f"💰 Balance: **{player['coins']:,.3f}**"
            ),
            parse_mode="markdown2"
        )
    else:
        player["coins"] = round(player["coins"] - bet_amount, 3)
        player["streak"] = 0
        await message.reply_photo(
            photo="https://i.imgur.com/AID8bGS.png",
            caption=(
                f"🎰 {name} has bet **{bet_amount:,.3f}** coins\n"
                f"Oh no! He came back home without **{bet_amount:,.3f}** coins (❌).\n\n"
                f"[🔁 Get more coins here!](https://t.me/YourChannel)\n"
                f"💰 Balance: **{player['coins']:,.3f}**"
            ),
            parse_mode="markdown2"
    )
