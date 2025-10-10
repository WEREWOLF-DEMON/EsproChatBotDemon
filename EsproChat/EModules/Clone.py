from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ChatAction, ChatType
import asyncio
import random
import string
from pymongo import MongoClient
import datetime
import re
import os
from config import MONGO_URL, OWNER_ID, API_ID, API_HASH, BOT_TOKEN

# MongoDB Setup
mongo_client = MongoClient(MONGO_URL)
db = mongo_client.EsproCloneDB
clones_collection = db.clones
approvals_collection = db.approvals
broadcasts_collection = db.broadcasts
settings_collection = db.settings

# Configuration from config.py
MAIN_OWNER_ID = OWNER_ID

# Generate unique clone ID
def generate_clone_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

# Check if clone is approved
def is_approved(clone_id):
    approval = approvals_collection.find_one({"clone_id": clone_id})
    return approval and approval.get("approved", False)

# Get clone owner
def get_clone_owner(clone_id):
    clone = clones_collection.find_one({"clone_id": clone_id})
    return clone.get("owner_id") if clone else None

# Get all approved clones
def get_all_approved_clones():
    return list(clones_collection.find({"approved": True}))

# Get user's clones
def get_user_clones(user_id):
    return list(clones_collection.find({"owner_id": user_id}))

# Get clone by ID
def get_clone_by_id(clone_id):
    return clones_collection.find_one({"clone_id": clone_id})

# Remove clone
def remove_clone(clone_id):
    clones_collection.delete_one({"clone_id": clone_id})
    approvals_collection.delete_one({"clone_id": clone_id})

# Main Bot
app = Client("main_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Clone Bot Class
class CloneBot:
    def __init__(self, clone_id, bot_token):
        self.clone_id = clone_id
        self.bot_token = bot_token
        self.client = Client(f"clone_{clone_id}", api_id=API_ID, api_hash=API_HASH, bot_token=bot_token)
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.client.on_message(filters.command("start"))
        async def clone_start(client, message):
            if not is_approved(self.clone_id):
                await message.reply_text(
                    "⏳ **Approval Pending**\n\n"
                    "This clone is waiting for owner approval.\n\n"
                    "Please contact main owner for approval.\n"
                    f"**Owner ID:** `{MAIN_OWNER_ID}`"
                )
                return
            
            await message.reply_text(
                "🤖 **Clone Bot Active**\n\n"
                "I'm an approved clone of Espro Bot!\n"
                "You can chat with me normally."
            )
        
        @self.client.on_message(filters.text & ~filters.command)
        async def clone_chat(client, message):
            if not is_approved(self.clone_id):
                await message.reply_text(
                    "🚫 **Not Approved**\n\n"
                    "This clone is not approved yet.\n"
                    "Please wait for owner approval."
                )
                return
            
            # Add your chat handling logic here
            await message.reply_chat_action(ChatAction.TYPING)
            await asyncio.sleep(1)
            await message.reply_text("I'm a clone bot! How can I help you?")
    
    async def start(self):
        await self.client.start()
        print(f"Clone {self.clone_id} started")
    
    async def stop(self):
        await self.client.stop()
        print(f"Clone {self.clone_id} stopped")

# Store active clones
active_clones = {}

# /botfree command - Create clone
@app.on_message(filters.command("botfree"))
async def create_clone(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text(
            "**🤖 Clone Creation System**\n\n"
            "**Usage:** `/botfree <bot_token>`\n\n"
            "**Example:** `/botfree 123456:ABCdefGhIjKlMnOpQrStUvWxYz`\n\n"
            "**Features:**\n"
            "• Requires owner approval\n"
            "• Set custom owner ID\n" 
            "• Set channel & support group\n"
            "• Broadcast messages\n"
            "• Human-like chatting\n\n"
            "**Note:** Clone will not work until approved by main owner."
        )
        return
    
    bot_token = message.command[1]
    user_id = message.from_user.id
    
    # Validate bot token format
    if not re.match(r'^\d+:[\w-]+$', bot_token):
        await message.reply_text("❌ Invalid bot token format!")
        return
    
    # Generate clone ID
    clone_id = generate_clone_id()
    
    # Store clone data
    clone_data = {
        "clone_id": clone_id,
        "owner_id": user_id,
        "bot_token": bot_token,
        "created_at": datetime.datetime.now(),
        "approved": False,
        "settings": {
            "custom_owner_id": user_id,
            "channel": "",
            "support_group": ""
        }
    }
    
    clones_collection.insert_one(clone_data)
    
    # Notify main owner
    await client.send_message(
        MAIN_OWNER_ID,
        f"**🆕 New Clone Request**\n\n"
        f"**Clone ID:** `{clone_id}`\n"
        f"**User ID:** `{user_id}`\n"
        f"**Time:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        "**Commands:**\n"
        f"`/approve {clone_id}` - Approve clone\n"
        f"`/reject {clone_id}` - Reject clone\n"
        f"`/remove {clone_id}` - Remove clone"
    )
    
    # Send response to user
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 Contact Owner", url=f"tg://user?id={MAIN_OWNER_ID}")],
        [InlineKeyboardButton("🔄 Check Status", callback_data=f"status_{clone_id}")]
    ])
    
    await message.reply_text(
        f"**✅ Clone Created Successfully!**\n\n"
        f"**Clone ID:** `{clone_id}`\n"
        f"**Status:** ⏳ Waiting Approval\n\n"
        "Your clone has been created but needs approval from main owner.\n"
        "Once approved, it will start working automatically.\n\n"
        f"**Owner ID:** `{MAIN_OWNER_ID}`",
        reply_markup=keyboard
    )

# /approve command - Approve clone
@app.on_message(filters.command("approve") & filters.user(MAIN_OWNER_ID))
async def approve_clone(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("**Usage:** `/approve <clone_id>`")
        return
    
    clone_id = message.command[1]
    clone = get_clone_by_id(clone_id)
    
    if not clone:
        await message.reply_text("❌ Clone not found!")
        return
    
    if clone["approved"]:
        await message.reply_text("❌ Clone is already approved!")
        return
    
    # Update approval status
    clones_collection.update_one(
        {"clone_id": clone_id}, 
        {"$set": {"approved": True}}
    )
    
    approvals_collection.insert_one({
        "clone_id": clone_id,
        "approved": True,
        "approved_by": MAIN_OWNER_ID,
        "approved_at": datetime.datetime.now()
    })
    
    # Start the clone bot
    try:
        clone_bot = CloneBot(clone_id, clone["bot_token"])
        active_clones[clone_id] = clone_bot
        await clone_bot.start()
    except Exception as e:
        await message.reply_text(f"❌ Error starting clone: {str(e)}")
        return
    
    # Notify clone owner
    try:
        await client.send_message(
            clone["owner_id"],
            f"**🎉 Clone Approved!**\n\n"
            f"**Clone ID:** `{clone_id}`\n\n"
            "Your clone is now active and working!\n\n"
            "**Available Commands:**\n"
            "• `/setowner <id>` - Set custom owner ID\n"
            "• `/setchannel <username>` - Set channel\n"
            "• `/setsupport <username>` - Set support group\n"
            "• `/broadcast` - Broadcast message\n"
            "• `/myclones` - List your clones\n"
            "• `/removeclone <id>` - Remove your clone"
        )
    except:
        pass
    
    await message.reply_text(f"✅ Clone `{clone_id}` approved and started successfully!")

# /reject command - Reject clone
@app.on_message(filters.command("reject") & filters.user(MAIN_OWNER_ID))
async def reject_clone(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("**Usage:** `/reject <clone_id>`")
        return
    
    clone_id = message.command[1]
    clone = get_clone_by_id(clone_id)
    
    if not clone:
        await message.reply_text("❌ Clone not found!")
        return
    
    # Stop clone if running
    if clone_id in active_clones:
        await active_clones[clone_id].stop()
        del active_clones[clone_id]
    
    # Remove clone data
    remove_clone(clone_id)
    
    # Notify clone owner
    try:
        await client.send_message(
            clone["owner_id"],
            f"❌ **Clone Rejected**\n\n"
            f"**Clone ID:** `{clone_id}`\n\n"
            "Your clone request has been rejected by the main owner."
        )
    except:
        pass
    
    await message.reply_text(f"❌ Clone `{clone_id}` rejected and removed!")

# /remove command - Remove clone
@app.on_message(filters.command("remove") & filters.user(MAIN_OWNER_ID))
async def remove_clone_cmd(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("**Usage:** `/remove <clone_id>`")
        return
    
    clone_id = message.command[1]
    clone = get_clone_by_id(clone_id)
    
    if not clone:
        await message.reply_text("❌ Clone not found!")
        return
    
    # Stop clone if running
    if clone_id in active_clones:
        await active_clones[clone_id].stop()
        del active_clones[clone_id]
    
    # Remove clone data
    remove_clone(clone_id)
    
    # Notify clone owner
    try:
        await client.send_message(
            clone["owner_id"],
            f"🗑️ **Clone Removed**\n\n"
            f"**Clone ID:** `{clone_id}`\n\n"
            "Your clone has been removed by the main owner."
        )
    except:
        pass
    
    await message.reply_text(f"✅ Clone `{clone_id}` removed successfully!")

# /setowner command - Set custom owner
@app.on_message(filters.command("setowner"))
async def set_owner(client, message: Message):
    user_id = message.from_user.id
    user_clones = get_user_clones(user_id)
    
    if not user_clones:
        await message.reply_text("❌ You don't have any approved clones!")
        return
    
    if len(message.command) < 2:
        await message.reply_text("**Usage:** `/setowner <user_id>`")
        return
    
    new_owner = message.command[1]
    
    # Update owner for all user's approved clones
    for clone in user_clones:
        if clone["approved"]:
            clones_collection.update_one(
                {"clone_id": clone["clone_id"]},
                {"$set": {"settings.custom_owner_id": new_owner}}
            )
    
    await message.reply_text(f"✅ Owner ID updated to `{new_owner}` for all your clones!")

# /setchannel command - Set channel
@app.on_message(filters.command("setchannel"))
async def set_channel(client, message: Message):
    user_id = message.from_user.id
    user_clones = get_user_clones(user_id)
    
    if not user_clones:
        await message.reply_text("❌ You don't have any approved clones!")
        return
    
    if len(message.command) < 2:
        await message.reply_text("**Usage:** `/setchannel <channel_username>`")
        return
    
    channel = message.command[1].replace("@", "")
    
    # Update channel for all user's approved clones
    for clone in user_clones:
        if clone["approved"]:
            clones_collection.update_one(
                {"clone_id": clone["clone_id"]},
                {"$set": {"settings.channel": channel}}
            )
    
    await message.reply_text(f"✅ Channel updated to `{channel}` for all your clones!")

# /setsupport command - Set support group
@app.on_message(filters.command("setsupport"))
async def set_support(client, message: Message):
    user_id = message.from_user.id
    user_clones = get_user_clones(user_id)
    
    if not user_clones:
        await message.reply_text("❌ You don't have any approved clones!")
        return
    
    if len(message.command) < 2:
        await message.reply_text("**Usage:** `/setsupport <group_username>`")
        return
    
    support_group = message.command[1].replace("@", "")
    
    # Update support group for all user's approved clones
    for clone in user_clones:
        if clone["approved"]:
            clones_collection.update_one(
                {"clone_id": clone["clone_id"]},
                {"$set": {"settings.support_group": support_group}}
            )
    
    await message.reply_text(f"✅ Support group updated to `{support_group}` for all your clones!")

# /broadcast command - With clone support
@app.on_message(filters.command("broadcast"))
async def broadcast_message(client, message: Message):
    user_id = message.from_user.id
    
    # Check permissions
    if user_id != MAIN_OWNER_ID and not get_user_clones(user_id):
        await message.reply_text("❌ You don't have permission to broadcast!")
        return
    
    if len(message.command) < 2:
        await message.reply_text(
            "**📢 Broadcast System**\n\n"
            "**Usage:** `/broadcast <message>`\n\n"
            "**Options:**\n"
            "• Add `-clone` to send only to clone owners\n"
            "• Without `-clone` sends normal broadcast\n\n"
            "**Example:** `/broadcast Hello everyone! -clone`"
        )
        return
    
    broadcast_text = " ".join(message.command[1:])
    send_to_clones = "-clone" in broadcast_text
    broadcast_text = broadcast_text.replace("-clone", "").strip()
    
    if not broadcast_text:
        await message.reply_text("❌ Please provide a message to broadcast!")
        return
    
    sent_count = 0
    
    if send_to_clones:
        # Broadcast to clone owners only
        approved_clones = get_all_approved_clones()
        for clone in approved_clones:
            try:
                await client.send_message(
                    clone["owner_id"],
                    f"**📢 Broadcast from Main Owner**\n\n{broadcast_text}"
                )
                sent_count += 1
            except:
                continue
    else:
        # Normal broadcast to all users
        # You can implement your user database logic here
        users_collection = db.users
        all_users = users_collection.find()
        for user in all_users:
            try:
                await client.send_message(user["user_id"], broadcast_text)
                sent_count += 1
            except:
                continue
    
    await message.reply_text(f"✅ Broadcast sent to {sent_count} recipients!")

# /myclones command - List user's clones
@app.on_message(filters.command("myclones"))
async def my_clones(client, message: Message):
    user_id = message.from_user.id
    user_clones = get_user_clones(user_id)
    
    if not user_clones:
        await message.reply_text("❌ You don't have any clones!")
        return
    
    clones_text = "**🤖 Your Clones**\n\n"
    
    for clone in user_clones:
        status = "✅ Approved" if clone["approved"] else "⏳ Pending"
        settings = clone.get("settings", {})
        clones_text += f"**Clone ID:** `{clone['clone_id']}`\n"
        clones_text += f"**Status:** {status}\n"
        clones_text += f"**Owner ID:** `{settings.get('custom_owner_id', 'Not set')}`\n"
        clones_text += f"**Channel:** `{settings.get('channel', 'Not set')}`\n"
        clones_text += f"**Support:** `{settings.get('support_group', 'Not set')}`\n"
        clones_text += f"**Created:** {clone['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
        clones_text += "━━━━━━━━━━━━━━━━\n"
    
    clones_text += f"\n**Total Clones:** {len(user_clones)}"
    
    await message.reply_text(clones_text)

# /removeclone command - User can remove their own clone
@app.on_message(filters.command("removeclone"))
async def remove_own_clone(client, message: Message):
    user_id = message.from_user.id
    
    if len(message.command) < 2:
        await message.reply_text("**Usage:** `/removeclone <clone_id>`")
        return
    
    clone_id = message.command[1]
    clone = get_clone_by_id(clone_id)
    
    if not clone:
        await message.reply_text("❌ Clone not found!")
        return
    
    if clone["owner_id"] != user_id:
        await message.reply_text("❌ This is not your clone!")
        return
    
    # Stop clone if running
    if clone_id in active_clones:
        await active_clones[clone_id].stop()
        del active_clones[clone_id]
    
    # Remove clone data
    remove_clone(clone_id)
    
    await message.reply_text(f"✅ Your clone `{clone_id}` has been removed!")

# /allclones command - Main owner can see all clones
@app.on_message(filters.command("allclones") & filters.user(MAIN_OWNER_ID))
async def all_clones(client, message: Message):
    all_clones = list(clones_collection.find())
    
    if not all_clones:
        await message.reply_text("❌ No clones found!")
        return
    
    clones_text = "**🤖 All Clones**\n\n"
    
    for clone in all_clones:
        status = "✅ Approved" if clone["approved"] else "⏳ Pending"
        settings = clone.get("settings", {})
        clones_text += f"**Clone ID:** `{clone['clone_id']}`\n"
        clones_text += f"**Owner:** `{clone['owner_id']}`\n"
        clones_text += f"**Status:** {status}\n"
        clones_text += f"**Custom Owner:** `{settings.get('custom_owner_id', 'Not set')}`\n"
        clones_text += f"**Channel:** `{settings.get('channel', 'Not set')}`\n"
        clones_text += f"**Support:** `{settings.get('support_group', 'Not set')}`\n"
        clones_text += f"**Created:** {clone['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
        clones_text += "━━━━━━━━━━━━━━━━\n"
    
    clones_text += f"\n**Total Clones:** {len(all_clones)}"
    
    await message.reply_text(clones_text)

# Callback query handler for status check
@app.on_callback_query(filters.regex(r"status_(.+)"))
async def check_status(client, callback_query):
    clone_id = callback_query.matches[0].group(1)
    clone = get_clone_by_id(clone_id)
    
    if not clone:
        await callback_query.answer("Clone not found!", show_alert=True)
        return
    
    status = "✅ Approved" if clone["approved"] else "⏳ Waiting Approval"
    
    await callback_query.answer(
        f"Clone Status: {status}\n"
        f"Clone ID: {clone_id}\n"
        f"Owner ID: {clone['owner_id']}",
        show_alert=True
    )

# Start all approved clones on bot startup
async def start_approved_clones():
    approved_clones = get_all_approved_clones()
    for clone in approved_clones:
        try:
            clone_bot = CloneBot(clone["clone_id"], clone["bot_token"])
            active_clones[clone["clone_id"]] = clone_bot
            await clone_bot.start()
            print(f"✅ Started clone: {clone['clone_id']}")
        except Exception as e:
            print(f"❌ Failed to start clone {clone['clone_id']}: {e}")

# Run startup when bot starts
@app.on_message(filters.command("start"))
async def main_start(client, message: Message):
    await message.reply_text(
        "🤖 **Espro Clone System**\n\n"
        "**Main Bot Commands:**\n"
        "• `/botfree <token>` - Create clone\n"
        "• `/myclones` - Your clones\n"
        "• `/setowner <id>` - Set owner ID\n"
        "• `/setchannel <username>` - Set channel\n"
        "• `/setsupport <username>` - Set support group\n"
        "• `/removeclone <id>` - Remove your clone\n\n"
        "**Owner Commands:**\n"
        "• `/approve <id>` - Approve clone\n"
        "• `/reject <id>` - Reject clone\n"
        "• `/remove <id>` - Remove any clone\n"
        "• `/allclones` - List all clones\n"
        "• `/broadcast` - Broadcast messages"
    )

# Initialize when bot starts
@app.on_message(filters.command("init"))
async def initialize_system(client, message: Message):
    if message.from_user.id != MAIN_OWNER_ID:
        return
    
    await start_approved_clones()
    await message.reply_text("✅ Clone system initialized! All approved clones started.")

# Run the bot
if __name__ == "__main__":
    print("🤖 Starting Espro Clone System...")
    print(f"👑 Main Owner ID: {MAIN_OWNER_ID}")
    print("📊 Loading approved clones...")
    
    # Start approved clones on bot startup
    async def startup():
        await start_approved_clones()
    
    app.run()
