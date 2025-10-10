import logging
import os
from pyrogram.enums import ParseMode
from pyrogram import Client, filters
from pyrogram.types import BotCommand
from pyrogram.errors.exceptions.bad_request_400 import AccessTokenExpired, AccessTokenInvalid
import config

# Direct configuration values from config.py
API_ID = config.API_ID
API_HASH = config.API_HASH
OWNER_ID = config.OWNER_ID

# Initialize CLONES set
CLONES = set()

# Database collections (you need to initialize these properly)
try:
    from EsproChat import db as mongodb
    cloneownerdb = mongodb.cloneownerdb
    clonebotdb = mongodb.clonebotdb
except:
    # Fallback if database not available
    class MockCollection:
        async def find_one(self, query):
            return None
        async def insert_one(self, data):
            return True
        async def delete_one(self, query):
            return True
        async def delete_many(self, query):
            return True
        async def find(self, query=None):
            return MockCursor()
    
    class MockCursor:
        async def to_list(self, length=None):
            return []
    
    cloneownerdb = MockCollection()
    clonebotdb = MockCollection()

# Helper function to save clone bot owner
async def save_clonebot_owner(bot_id, user_id):
    """Save clone bot owner to database"""
    try:
        await cloneownerdb.insert_one({
            "bot_id": bot_id,
            "user_id": user_id
        })
        return True
    except Exception as e:
        logging.error(f"Error saving clone bot owner: {e}")
        return False

# Get app instance
try:
    from EsproChat import EsproChat as app
except:
    app = None

@Client.on_message(filters.command(["clone", "host", "deploy"]))
async def clone_txt(client, message):
    if len(message.command) > 1:
        bot_token = message.text.split(maxsplit=1)[1].strip()
        mi = await message.reply_text("Please wait while I check the bot token.")
        try:
            # Create bot client without plugins to avoid import errors
            ai = Client(
                f"bot_{bot_token[:10]}", 
                API_ID, 
                API_HASH, 
                bot_token=bot_token,
                in_memory=True
            )
            await ai.start()
            bot = await ai.get_me()
            bot_id = bot.id
            user_id = message.from_user.id
            
            # Save clone bot owner
            await save_clonebot_owner(bot_id, user_id)
            
            # Set bot commands
            try:
                await ai.set_bot_commands([
                    BotCommand("start", "Start the bot"),
                    BotCommand("help", "Get the help menu"),
                    BotCommand("clone", "Make your own chatbot"),
                    BotCommand("idclone", "Make your id-chatbot"),
                    BotCommand("ping", "Check if the bot is alive or dead"),
                    BotCommand("id", "Get users user_id"),
                    BotCommand("stats", "Check bot stats"),
                    BotCommand("gcast", "Broadcast any message to groups/users"),
                    BotCommand("shayri", "Get random shayri for love"),
                ])
            except Exception as e:
                logging.warning(f"Could not set bot commands: {e}")
            
            # Check if bot already exists
            cloned_bot = await clonebotdb.find_one({"token": bot_token})
            if cloned_bot:
                await mi.edit_text("**🤖 Your bot is already cloned ✅**")
                await ai.stop()
                return

            await mi.edit_text("**Cloning process started. Please wait for the bot to start.**")
            
            # Save bot details
            details = {
                "bot_id": bot.id,
                "is_bot": True,
                "user_id": user_id,
                "name": bot.first_name,
                "token": bot_token,
                "username": bot.username,
            }
            
            # Get total clones count
            try:
                cloned_bots = clonebotdb.find()
                cloned_bots_list = await cloned_bots.to_list(length=None)
                total_clones = len(cloned_bots_list)
            except:
                total_clones = 0

            # Notify owner
            try:
                if app:
                    await app.send_message(
                        int(OWNER_ID), 
                        f"**#New_Clone**\n\n**Bot:- @{bot.username}**\n\n**User ID:** `{user_id}`\n**Bot ID:** `{bot_id}`\n**Total Cloned:-** {total_clones + 1}"
                    )
            except Exception as e:
                logging.warning(f"Could not notify owner: {e}")

            # Insert into database
            await clonebotdb.insert_one(details)
            CLONES.add(bot.id)

            await mi.edit_text(
                f"**Bot @{bot.username} has been successfully cloned and started ✅.**\n**Remove clone by :- /delclone**\n**Check all cloned bot list by:- /cloned**"
            )
            
        except (AccessTokenExpired, AccessTokenInvalid):
            await mi.edit_text("**Invalid bot token. Please provide a valid one.**")
            return
        except Exception as e:
            logging.exception("Error while cloning bot.")
            await mi.edit_text(
                f"⚠️ <b>Error:</b>\n\n<code>{e}</code>\n\n**Forward this message to support for assistance**"
            )
    else:
        await message.reply_text("**Provide Bot Token after /clone Command from @Botfather.**\n\n**Example:** `/clone bot_token`")


@Client.on_message(filters.command("cloned"))
async def list_cloned_bots(client, message):
    try:
        user_id = message.from_user.id
        cloned_bots = clonebotdb.find({"user_id": user_id})
        cloned_bots_list = await cloned_bots.to_list(length=None)
        
        if not cloned_bots_list:
            await message.reply_text("No bots have been cloned by you yet.")
            return
            
        total_clones = len(cloned_bots_list)
        text = f"**Your Cloned Bots:** {total_clones}\n\n"
        
        for index, bot in enumerate(cloned_bots_list, 1):
            text += f"**{index}. Bot Name:** {bot['name']}\n"
            text += f"   **Username:** @{bot['username']}\n"
            text += f"   **Bot ID:** `{bot['bot_id']}`\n\n"
            
        await message.reply_text(text)
        
    except Exception as e:
        logging.exception(e)
        await message.reply_text("**An error occurred while listing cloned bots.**")


@Client.on_message(filters.command(["deletecloned", "delcloned", "delclone", "deleteclone", "removeclone", "cancelclone"]))
async def delete_cloned_bot(client, message):
    try:
        if len(message.command) < 2:
            await message.reply_text("**Provide Bot Token after /delclone Command.**\n\n**Example:** `/delclone bot_token`")
            return

        bot_token = message.command[1].strip()
        ok = await message.reply_text("**Checking the bot token...**")

        cloned_bot = await clonebotdb.find_one({"token": bot_token, "user_id": message.from_user.id})
        if cloned_bot:
            await clonebotdb.delete_one({"token": bot_token, "user_id": message.from_user.id})
            CLONES.discard(cloned_bot["bot_id"])
            
            bot_username = cloned_bot.get('username', 'unknown')
            app_username = client.me.username if client.me else "the_bot"
            
            await ok.edit_text(
                f"**🤖 Your cloned bot has been removed from my database ✅**\n**🔄 Kindly revoke your bot token from @botfather otherwise your bot will stop when @{app_username} restarts ☠️**"
            )
        else:
            await ok.edit_text("**⚠️ The provided bot token is not in your cloned list or doesn't exist.**")
            
    except Exception as e:
        await message.reply_text(f"**An error occurred while deleting the cloned bot:** {e}")
        logging.exception(e)


@Client.on_message(filters.command("delallclone") & filters.user(OWNER_ID))
async def delete_all_cloned_bots(client, message):
    try:
        a = await message.reply_text("**Deleting all cloned bots...**")
        await clonebotdb.delete_many({})
        CLONES.clear()
        await a.edit_text("**All cloned bots have been deleted successfully ✅**")
    except Exception as e:
        await a.edit_text(f"**An error occurred while deleting all cloned bots.** {e}")
        logging.exception(e)


@Client.on_message(filters.command("myclones"))
async def my_clones(client, message):
    try:
        user_id = message.from_user.id
        cloned_bots = clonebotdb.find({"user_id": user_id})
        cloned_bots_list = await cloned_bots.to_list(length=None)
        
        if not cloned_bots_list:
            await message.reply_text("**You haven't cloned any bots yet.**")
            return
            
        total_clones = len(cloned_bots_list)
        text = f"**Your Cloned Bots ({total_clones}):**\n\n"
        
        for index, bot in enumerate(cloned_bots_list, 1):
            text += f"**{index}. {bot['name']}**\n"
            text += f"   Username: @{bot['username']}\n"
            text += f"   Bot ID: `{bot['bot_id']}`\n\n"
            
        await message.reply_text(text)
        
    except Exception as e:
        logging.exception(e)
        await message.reply_text("**An error occurred while fetching your clones.**")


@Client.on_message(filters.command("clonehelp"))
async def clone_help(client, message):
    help_text = """
**🤖 Clone Bot Commands:**

**/clone <token>** - Clone a new bot using bot token
**/cloned** - List all your cloned bots
**/myclones** - Show your cloned bots
**/delclone <token>** - Remove a cloned bot
**/clonehelp** - Show this help message

**For Owner Only:**
**/delallclone** - Delete all cloned bots

**How to get bot token:**
1. Go to @BotFather
2. Create a new bot or use existing one
3. Copy the bot token
4. Use: `/clone your_bot_token_here`

**Example:**
`/clone 1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ`
"""
    await message.reply_text(help_text)
