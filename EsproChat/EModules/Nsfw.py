from EsproChat import app
from pyrogram import filters
from pyrogram.types import Message
from config import OWNER_ID
import requests
import re
import asyncio
import os
import tempfile
import logging
from typing import List, Tuple, Optional

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# API Configurations
SIGHTENGINE_USER = "1916313622"
SIGHTENGINE_SECRET = "frPDtcGYH42kUkmsKuGoj9SVYHCMW9QA"

# Database to store authorized users
authorized_users: Tuple[int, ...] = (int(OWNER_ID),) if OWNER_ID else ()
exempt_users: Tuple[int, ...] = (int(OWNER_ID),) if OWNER_ID else ()

# Create downloads directory if it doesn't exist
os.makedirs('downloads', exist_ok=True)

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

async def take_action(message: Message, content_type: str):
    """Delete content and send warning"""
    try:
        # Get user info
        user = message.from_user
        user_info = (
            f"👤 User: {user.first_name}\n"
            f"🆔 ID: {user.id}\n"
            f"✉️ Username: @{user.username if user.username else 'N/A'}\n"
            f"📛 Content: {content_type}"
        )
        
        # Delete the message
        await message.delete()
        
        # Send warning with user info
        warning_msg = await message.reply(f"⚠️ NSFW Content Removed!\n\n{user_info}")
        
        # Delete warning after 10 seconds
        await asyncio.sleep(10)
        await warning_msg.delete()
            
    except Exception as e:
        logger.error(f"Action Error: {e}")

async def process_media(message: Message):
    """Handle media content checking"""
    file_path = None
    try:
        # Download file to temp directory
        file_path = await message.download(file_name='downloads/')
        
        if file_path and os.path.exists(file_path):
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

@app.on_message(filters.command("addauth") & filters.user(exempt_users))
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

@app.on_message(filters.command("remauth") & filters.user(exempt_users))
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

@app.on_message(filters.command("listauth") & filters.user(exempt_users))
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
__DESCRIPTION__ = "Advanced NSFW content filtering system"
__COMMANDS__ = {
    "addauth <user_id>": "Add user to authorized list",
    "remauth <user_id>": "Remove user from authorized list",
    "listauth": "List authorized users"
}
