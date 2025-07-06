from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio
from EsproChat import app


# Members tracking
group_members = {}

# 60 Custom Messages
custom_messages = [
    "Hello kaise ho?", "Aap to bhool gaye hume 😢", "Kya haal hai?", "Mazaa aa gaya aapko dekh ke!",
    "Aaj to din ban gaya!", "Aap aaye bahar aayi 😍", "Itne din baad?", "Party kab de rahe ho?",
    "Kaha ho aajkal?", "Naam suna suna lag raha hai!", "Firse mil gaye 😁", "Apni yaad dilayi",
    "Kya chal raha hai?", "Thoda smile bhi kar lo", "Kaam kaisa chal raha hai?", "Kya mast dp hai!",
    "Hum to aapke fan hain", "Kabhi chai ho jaye?", "Online aaye aap 😄", "Sab thik hai na?",
    "Dil garden garden ho gaya!", "Aap aaye to jagmaga gaya", "Thoda active raha karo yaar",
    "Roz aaya karo group me", "Ek smile bhej do!", "Old is gold 😎", "Miss kar rahe the aapko",
    "Aapke bina kuch adhoora", "Tum ho to sab kuch hai", "Time travel se aaye kya?",
    "Re-entry detected! 😆", "Group ki jaan ho aap", "Ek photo bhejo", "Shayari sunao zara",
    "Energy aap se hi hai", "Leader vibe aapki", "Itna cool kaise ho?", "Hum bhi the kabhi active",
    "Kya yaad dilaya tune!", "Akele ho kya?", "Good vibes detected ✨", "Dil se salute!",
    "Thodi der ruk jao", "Old memories ❤️", "Tumhe dekh ke khushi hui", "Aap mast ho", 
    "Pehchana mujhe?", "Hum bhi yaad karte hai", "Chalo fir se shuru karte hai", "Group ka legend!",
    "Masti time aa gaya!", "Sab kuch theek hai na?", "Kaafi din ho gaye tumhe dekhe!", "Hamesha haste raho 😄",
    "Thoda gossip karte hain!", "Kya naya chal raha hai?", "Mood fresh ho gaya aapko dekhke!",
    "Bas aapka hi intezar tha", "Zindagi me rang bhar diye!", "You’re special 😇", "Aap aaye to sab theek lag raha hai"
]

# Track joined members
@app.on_message(filters.new_chat_members)
async def track_members(client, message: Message):
    chat_id = message.chat.id
    if chat_id not in group_members:
        group_members[chat_id] = set()

    for user in message.new_chat_members:
        group_members[chat_id].add(user.id)

# Tag all except bot
@app.on_message(filters.command("ritik") & filters.group)
async def tag_all_members(client, message: Message):
    chat_id = message.chat.id
    bot_user = await client.get_me()
    members = group_members.get(chat_id, [])

    if not members:
        await message.reply("Abhi tak koi members track nahi hua.")
        return

    msg = await message.reply("Tagging sabhi members...")

    i = 0
    for user_id in members:
        if user_id == bot_user.id:
            continue  # bot ko skip karo

        try:
            user = await client.get_users(user_id)
            mention = f"@{user.username}" if user.username else user.mention()
            text = f"{mention} {custom_messages[i % len(custom_messages)]}"
            await message.reply(text)
            i += 1
            await asyncio.sleep(1)
        except Exception:
            continue

    await msg.edit("✅ Tagging done!")

