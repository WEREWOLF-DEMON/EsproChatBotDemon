import asyncio
import importlib
from pyrogram import idle
from EsproChat import app
from pyrogram.types import BotCommand
from EsproChat.EModules import ALL_EModules
from config import LOGGER_ID, SETCMD

loop = asyncio.get_event_loop()

#all Fixed

async def Murali():
await app.start()
for all_module in ALL_EModules:
importlib.import_module("EsproChat.EModules." + all_module)
print("Start ChatBot MissEspro ✨")
print("Join Karo @EsproUpdate")
if SETCMD:
try:
await app.set_bot_commands(
[
BotCommand("alive", "ᴄʜᴇᴄᴋ ʙᴏᴛ ɪꜱ ᴀʟɪᴠᴇ ᴏʀ ᴅᴇᴀᴅ"),
BotCommand("id", "ᴄʜᴇᴄᴋ ʏᴏᴜʀ ɪᴅ"),
BotCommand("ping", "ᴄʜᴇᴄᴋ ʙᴏᴛ ᴘɪɴɢ"),
BotCommand("chatbot", "ᴇɴᴀʙʟᴇ ᴏʀ ᴅɪꜱᴀʙʟᴇ ᴄʜᴀᴛʙᴏᴛ "),
BotCommand("start", "ꜱᴛᴀʀᴛ ᴄʜɪᴋᴜ ʙᴏᴛ"),
BotCommand("tgm", "ᴜᴘʟᴏᴀᴅ ꜰɪʟᴇ ᴛᴏ ᴛᴇʟᴇɢʀᴀᴘʜ ")
]
)
except Exception as e:
print(f"Failed to set bot commands: {e}")
pass
await idle()

if name == "main":
loop.run_until_complete(Murali())

