import asyncio
import importlib
from pyrogram import idle
from EsproChat import app
from pyrogram.types import BotCommand
from EsproChat.EModules import ALL_EModules
from config import LOGGER_ID, SETCMD

loop = asyncio.get_event_loop()

# all Fixed



async def Murali():
    await app.start()
    for all_module in ALL_EModules:
        importlib.import_module("EsproChat.EModules." + all_module)
    print("𝐁𝐎𝐓 𝐇𝐀𝐒 𝐁𝐄𝐄𝐍 𝐒𝐓𝐀𝐑𝐓𝐄𝐃 ✨")
    print("𝐃𝐨𝐧𝐭 𝐅𝐨𝐫𝐠𝐞𝐭 𝐓𝐨 𝐕𝐢𝐬𝐢𝐭 @EsproUpdate ⭐")
    if SETCMD:
        try:
            await app.set_bot_commands(
                [
                    BotCommand("alive", "ᴄʜᴇᴄᴋ ʙᴏᴛ ɪꜱ ᴀʟɪᴠᴇ ᴏʀ ᴅᴇᴀᴅ"),
                    BotCommand("id", "ᴄʜᴇᴄᴋ ʏᴏᴜʀ ɪᴅ"),
                    BotCommand("ping", "ᴄʜᴇᴄᴋ ʙᴏᴛ ᴘɪɴɢ"),
                    BotCommand("chatbot", "ᴇɴᴀʙʟᴇ ᴏʀ ᴅɪꜱᴀʙʟᴇ ᴄʜᴀᴛʙᴏᴛ "),
                    BotCommand("start", "ꜱᴛᴀʀᴛ ᴄʜɪᴋᴜ ʙᴏᴛ"),
                    BotCommand("tgm", "ᴜᴘʟᴏᴀᴅ ꜰɪʟᴇ ᴛᴏ ᴛᴇʟᴇɢʀᴀᴘʜ "),
                    BotCommand("rankings", "ᴠɪᴇᴡ ᴛʜᴇ ɢʀᴏᴜᴘ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ ")
                ]
            )
        except Exception as e:
            print(f"Failed to set bot commands: {e}")
            pass
    await idle()
    
if __name__ == "__main__":
    loop.run_until_complete(Murali())
