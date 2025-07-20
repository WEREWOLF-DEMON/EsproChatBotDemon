from EsproChat import app
from pyrogram import filters
from pyrogram.types import Message
from config import OWNER_ID
import requests
import re
import asyncio
import os
import tempfile
import random
import logging
from typing import List, Optional, Tuple

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# API Configurations
SIGHTENGINE_USER = "1916313622"
SIGHTENGINE_SECRET = "frPDtcGYH42kUkmsKuGoj9SVYHCMW9QA"
NEKOS_API = "https://nekos.best/api/v2/neko"

# Database to store authorized users - using tuples instead of sets
authorized_users: Tuple[int, ...] = ()
exempt_users: Tuple[int, ...] = ()

# Initialize with owner from config
if isinstance(OWNER_ID, (list, tuple)):
    authorized_users = tuple(map(int, OWNER_ID))
    exempt_users = tuple(map(int, OWNER_ID))
elif OWNER_ID:
    authorized_users = (int(OWNER_ID),)
    exempt_users = (int(OWNER_ID),)

# Enhanced NSFW keywords
NSFW_KEYWORDS = [
    # Sexual content
    "porn", "xxx", "adult", "nsfw", "sex", "fuck", "dick", "pussy", "boobs", "nude", "naked",
    # Profanity
    "shit", "asshole", "bitch", "bastard", "cunt", "whore", "slut",
    # Drugs
    "drugs?", "heroin", "cocaine", "weed", "marijuana", "hash", "lsd", "ecstasy", "meth",
    # Violence
    "kill", "murder", "rape", "terrorist", "bomb", "shoot", "gun", "attack",
    # Self-harm
    "suicide", "selfharm", "cutting", "hang", "die"
]

async def check_nsfw(file_path: str) -> bool:
    """Check content using Sightengine API"""
    try:
        with open(file_path, 'rb') as f:
            response = await asyncio.to_thread(
                requests.post,
                'https://api.sightengine.com/1.0/check.json',
                files={'media': f},
                data={
                    'models': 'nudity-2.1,wad,drug,violence',
                    'api_user': SIGHTENGINE_USER,
                    'api_secret': SIGHTENGINE_SECRET
                },
                timeout=10
            )
        result = response.json()
        
        return (
            result.get('nudity', {}).get('sexual_activity', 0) > 0.7 or
            result.get('nudity', {}).get('sexual_display', 0) > 0.7 or
            result.get('weapon', 0) > 0.8 or
            result.get('drug', 0) > 0.8 or
            result.get('violence', 0) > 0.8
        )
    except Exception as e:
        logger.error(f"NSFW Check Error: {e}")
        return False

async def get_random_neko() -> Optional[str]:
    """Get random neko image from API"""
    try:
        response = await asyncio.to_thread(requests.get, NEKOS_API, timeout=5)
        data = response.json()
        return data['results'][0]['url']
    except Exception as e:
        logger.error(f"Neko API Error: {e}")
        return None

async def take_action(message: Message, content_type: str):
    """Delete content and send warning"""
    try:
        # Get user info
        user = message.from_user
        user_info = (
            f"👤 User: {user.first_name}\n"
            f"🆔 ID: {user.id}\n"
            f"✉️ Username: @{user.username}\n"
            f"📛 Content: {content_type}"
        )
        
        # Delete the message
        await message.delete()
        
        # Get random neko image
        neko_url = await get_random_neko()
        
        # Send warning with user info and neko image
        if neko_url:
            await message.reply_photo(
                photo=neko_url,
                caption=f"⚠️ NSFW Content Removed!\n\n{user_info}"
            )
        else:
            await message.reply(f"⚠️ NSFW Content Removed!\n\n{user_info}")
            
    except Exception as e:
        logger.error(f"Action Error: {e}")

async def process_media(message: Message):
    """Handle media content checking"""
    file_path = None
    try:
        # Download file to temp directory
        file_path = await message.download(file_name=tempfile.mktemp())
        
        if await check_nsfw(file_path):
            content_type = "Media"
            if message.sticker:
                content_type = "Animated Sticker" if message.sticker.is_animated else "Static Sticker"
            elif message.animation:
                content_type = "GIF"
            elif message.video:
                content_type = "Video"
            elif message.photo:
                content_type = "Photo"
                
            await take_action(message, content_type)
            
    except Exception as e:
        logger.error(f"Media Processing Error: {e}")
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass

def update_authorized_users(new_user: int, action: str):
    """Helper function to update authorized users"""
    global authorized_users
    current = list(authorized_users)
    if action == "add" and new_user not in current:
        current.append(new_user)
    elif action == "remove" and new_user in current:
        current.remove(new_user)
    authorized_users = tuple(current)

@app.on_message(filters.command(["addauth"]) & filters.user(exempt_users))
async def add_auth(client, message: Message):
    """Add user to authorized list"""
    try:
        user_id = int(message.command[1])
        update_authorized_users(user_id, "add")
        await message.reply(f"✅ Added {user_id} to authorized list!")
    except (IndexError, ValueError):
        await message.reply("❌ Usage: /addauth <user_id>")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

@app.on_message(filters.command(["remauth"]) & filters.user(exempt_users))
async def remove_auth(client, message: Message):
    """Remove user from authorized list"""
    try:
        user_id = int(message.command[1])
        update_authorized_users(user_id, "remove")
        await message.reply(f"✅ Removed {user_id} from authorized list!")
    except (IndexError, ValueError):
        await message.reply("❌ Usage: /remauth <user_id>")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

@app.on_message(filters.command(["listauth"]) & filters.user(exempt_users))
async def list_auth(client, message: Message):
    """List all authorized users"""
    if not authorized_users:
        await message.reply("ℹ️ No authorized users!")
    else:
        users_list = "\n".join(f"• <code>{uid}</code>" for uid in authorized_users)
        await message.reply(f"🛡️ Authorized Users:\n{users_list}", parse_mode="HTML")

@app.on_message(
    (filters.photo | filters.video | filters.document | 
     filters.sticker | filters.animation) & 
    ~filters.user(authorized_users)
)
async def media_filter(client, message: Message):
    """Filter all media content"""
    await process_media(message)

@app.on_message(filters.text & ~filters.user(authorized_users))
async def text_filter(client, message: Message):
    """Filter text messages for NSFW content"""
    text = message.text.lower()
    if any(re.search(rf'\b{kw}\b', text) for kw in NSFW_KEYWORDS):
        await take_action(message, "Text Message")

# Plugin information
__PLUGIN__ = "nsfw_protection"
__DESCRIPTION__ = "Advanced NSFW content filtering with neko warnings"
__COMMANDS__ = {
    "addauth <user_id>": "Add user to authorized list",
    "remauth <user_id>": "Remove user from authorized list",
    "listauth": "List authorized users"
}
