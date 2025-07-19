from EsproChat import app
from pyrogram import filters
from pyrogram.types import Message
from config import OWNER_ID, FALCON_API_KEY
import requests
import re
import asyncio
import os

# Database to store exempt user IDs
exempt_users = set()
exempt_users.add(OWNER_ID)  # Owner is exempt by default

# Enhanced NSFW keywords including drugs
NSFW_KEYWORDS = [
    # Sexual content
    "porn", "xxx", "adult", "nsfw", "sex", "fuck", "dick", "pussy", "boobs", "nude",
    # Profanity
    "shit", "asshole", "bitch", "bastard", "cunt", 
    # Drugs and substances
    "drugs?", "heroin", "cocaine", "weed", "marijuana", "hash", "lsd", "ecstasy",
    "meth", "opium", "ganja", "charas", "bhang", "smack", "crack", "amphetamine"
]

def check_nsfw(content_url: str) -> bool:
    """Check content using Falcon.ai API"""
    headers = {"Authorization": f"Bearer {FALCON_API_KEY}"}
    payload = {"url": content_url}
    
    try:
        response = requests.post(
            "https://api.falcons.ai/v1/nsfw-detection",
            headers=headers,
            json=payload,
            timeout=5
        )
        return response.json().get("is_nsfw", False)
    except Exception as e:
        print(f"NSFW API Error: {e}")
        return False

async def process_media(message: Message):
    """Handle media content checking"""
    try:
        file = await message.download()
        if check_nsfw(file):
            await message.delete()
            warn = await message.reply("⚠️ NSFW content removed as per community guidelines!")
            await asyncio.sleep(5)
            await warn.delete()
    except Exception as e:
        print(f"Media process error: {e}")
    finally:
        if os.path.exists(file):
            os.remove(file)

# Improved command names with authorization levels
@app.on_message(filters.command(["addnsfw", "addnsfwexempt"]) & filters.user(OWNER_ID))
async def add_exempt(client, message: Message):
    """Add user to NSFW exempt list"""
    try:
        if len(message.command) < 2:
            return await message.reply("❌ Usage: /addnsfw <user_id>")
        
        user_id = int(message.command[1])
        exempt_users.add(user_id)
        await message.reply(f"✅ Added {user_id} to NSFW exempt list!")
    except ValueError:
        await message.reply("❌ Invalid user ID format!")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

@app.on_message(filters.command(["remnsfw", "removensfwexempt"]) & filters.user(OWNER_ID))
async def remove_exempt(client, message: Message):
    """Remove user from NSFW exempt list"""
    try:
        if len(message.command) < 2:
            return await message.reply("❌ Usage: /remnsfw <user_id>")
        
        user_id = int(message.command[1])
        exempt_users.discard(user_id)
        await message.reply(f"✅ Removed {user_id} from NSFW exempt list!")
    except ValueError:
        await message.reply("❌ Invalid user ID format!")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

@app.on_message(filters.command(["listnsfw", "listnsfwexempt"]) & filters.user(OWNER_ID))
async def list_exempt(client, message: Message):
    """List all NSFW exempt users"""
    if not exempt_users:
        return await message.reply("ℹ️ No users in NSFW exempt list!")
    
    users_list = "\n".join(f"• <code>{uid}</code>" for uid in exempt_users)
    await message.reply(f"🛡️ <b>NSFW Exempt Users:</b>\n{users_list}", parse_mode="HTML")

# Content filtering handlers
@app.on_message(filters.media & ~filters.user(exempt_users))
async def media_filter(client, message: Message):
    """Filter all media content"""
    await process_media(message)

@app.on_message(filters.text & ~filters.user(exempt_users))
async def text_filter(client, message: Message):
    """Filter text messages for NSFW content"""
    text = message.text.lower()
    
    # Check for NSFW keywords
    if any(re.search(rf'\b{kw}\b', text) for kw in NSFW_KEYWORDS):
        await message.delete()
        warn = await message.reply("⚠️ Message removed for containing restricted content!")
        await asyncio.sleep(5)
        await warn.delete()

# Plugin information
__PLUGIN__ = "nsfw_filter"
__DESCRIPTION__ = "Advanced NSFW content filtering system with exempt user management"
__COMMANDS__ = {
    "addnsfw <user_id>": "Add user to NSFW exempt list (Owner only)",
    "remnsfw <user_id>": "Remove user from NSFW exempt list (Owner only)",
    "listnsfw": "List all exempt users (Owner only)"
}
