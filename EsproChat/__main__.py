import asyncio
import importlib
import traceback
from pyrogram import idle
from pyrogram.types import BotCommand
from EsproChat import app
from EsproChat.EModules import ALL_EModules
from config import LOGGER_ID, SETCMD

async def Murali():
    await app.start()

    for all_module in ALL_EModules:
        try:
            importlib.import_module("EsproChat.EModules." + all_module)
        except Exception as err:
            print(f"Failed to import {all_module}: {err}")

    print("CHIKU BOT HAS BEEN STARTED")
    print("Join our Channel: @EsproUpdate")

    if SETCMD:
        try:
            await app.set_bot_commands(
                [
                    BotCommand("alive", "check bot is alive or dead"),
                    BotCommand("id", "check your id"),
                    BotCommand("ping", "check bot ping"),
                    BotCommand("chatbot", "enable or disable chatbot"),
                    BotCommand("start", "start chiku bot"),
                    BotCommand("tgm", "upload file to telegra.ph")
                ]
            )
        except Exception:
            traceback.print_exc()

    await idle()

if __name__ == "__main__":
    asyncio.run(Murali())
