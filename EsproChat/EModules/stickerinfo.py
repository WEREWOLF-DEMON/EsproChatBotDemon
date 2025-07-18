from pyrogram import filters
from pyrogram.types import Message
from EsproChat import app

@app.on_message(filters.command("si"))
async def sticker_info_handler(client, message: Message):
    try:
        # Sticker fetch logic
        sticker = (
            message.sticker or
            (message.reply_to_message and message.reply_to_message.sticker)
        )

        if not sticker:
            return await message.reply("❌ Pehle sticker bhejo ya reply karo kisi sticker pe!")

        file_id = sticker.file_id       # ✅ Usable path for bots
        unique_id = sticker.file_unique_id
        emoji = sticker.emoji or "😶"

        await message.reply(
            f"🧷 **Sticker Details**\n\n"
            f"📌 **Path (file_id)**:\n`{file_id}`\n\n"
            f"🆔 **Unique ID**:\n`{unique_id}`\n"
            f"🙂 **Emoji**: {emoji}"
        )

    except Exception as e:
        await message.reply(f"⚠️ Error: `{str(e)}`")
  
