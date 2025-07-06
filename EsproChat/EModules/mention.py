from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio
from EsproChat import app


# Memory storage for members (better to use database)
joined_members = {}



# Track new members
@app.on_message(filters.new_chat_members)
async def track_members(client, message: Message):
    chat_id = message.chat.id
    for user in message.new_chat_members:
        if chat_id not in joined_members:
            joined_members[chat_id] = set()
        joined_members[chat_id].add(user.id)


# /tagall command: tag each member separately
@app.on_message(filters.command("tagall") & filters.group)
async def tag_each(client, message: Message):
    chat_id = message.chat.id
    if chat_id not in joined_members or not joined_members[chat_id]:
        await message.reply("Koi member track nahi hua abhi tak.")
        return

    msg = await message.reply("Sab members ko tag kiya ja raha hai...")

    for user_id in joined_members[chat_id]:
        try:
            user = await client.get_users(user_id)
            mention = f"@{user.username}" if user.username else user.mention()
            await message.reply(mention)
            await asyncio.sleep(0.8)  # thoda delay spam se bachne ke liye
        except Exception as e:
            continue

    await msg.edit("✅ Tagging complete!2")

