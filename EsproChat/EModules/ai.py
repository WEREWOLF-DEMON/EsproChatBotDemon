from pyrogram import Client, filters
import g4f
from EsproChat import app



@app.on_message(filters.private & filters.text)
async def real_tone_chat(client, message):
    user_msg = message.text
    await message.reply_chat_action("typing")

    try:
        # Real human-style response prompt
        prompt = f"""
Tum ek real insaan ho. Har reply casual, chhoti aur friendly Hindi me do.
Zyada lamba na ho, normal dost jaise reply karo.

User: {user_msg}
Bot:
"""

        response = g4f.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )

        await message.reply(response.strip())

    except Exception as e:
        await message.reply("😓 Kuch error aaya:\n" + str(e))


