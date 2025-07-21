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
from typing import Tuple, List

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# API Configurations
SIGHTENGINE_USER = "1916313622"
SIGHTENGINE_SECRET = "frPDtcGYH42kUkmsKuGoj9SVYHCMW9QA"

# Initialize authorized users from OWNER_ID
def get_owner_ids(owner_id):
    if isinstance(owner_id, list):
        return tuple(int(i) for i in owner_id)
    elif owner_id:
        return (int(owner_id),)
    return ()

authorized_users: Tuple[int, ...] = get_owner_ids(OWNER_ID)
exempt_users: Tuple[int, ...] = get_owner_ids(OWNER_ID)

# Create downloads directory
os.makedirs('downloads', exist_ok=True)

# NSFW keywords
NSFW_KEYWORDS = [
    "porn", "xxx", "adult", "nsfw", "sex", "fuck", "dick", "pussy", "boobs", "nude",
    "shit", "asshole", "bitch", "bastard", "cunt", "whore", "slut",
    "drugs", "heroin", "cocaine", "weed", "marijuana", "hash", "lsd", "ecstasy", "meth",
    "kill", "murder", "rape", "terrorist", "bomb", "shoot", "gun", "attack",
    "suicide", "selfharm", "cutting", "hang", "die"
]

async def check_nsfw(file_path: str) -> bool:
    """Check media for NSFW content"""
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
    """Delete NSFW content and warn user"""
    try:
        user = message.from_user
        await message.delete()
        warning = await message.reply(
            f"⚠️ NSFW Content Removed!\n\n"
            f"👤 User: {user.first_name or 'Unknown'}\n"
            f"🆔 ID: {user.id}\n"
            f"✉️ Username: @{user.username or 'N/A'}\n"
            f"📛 Content: {content_type}"
        )
        await asyncio.sleep(10)
        await warning.delete()
    except Exception as e:
        logger.error(f"Action Error: {e}")

async def process_media(message: Message):
    """Process and check media files"""
    file_path = None
    try:
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
        logger.error(f"Media Process Error: {e}")
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass

def update_auth_users(user_id: int, action: str):
    """Update authorized users list"""
    global authorized_users
    current = list(authorized_users)
    if action == "add" and user_id not in current:
        current.append(user_id)
    elif action == "remove" and user_id in current:
        current.remove(user_id)
    authorized_users = tuple(current)

@app.on_message(filters.command("addauth") & filters.user(exempt_users))
async def add_auth(_, message: Message):
    """Add user to authorized list"""
    try:
        user_id = int(message.command[1])
        update_auth_users(user_id, "add")
        await message.reply(f"✅ Added {user_id} to authorized list!")
    except (IndexError, ValueError):
        await message.reply("❌ Usage: /addauth <user_id>")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

@app.on_message(filters.command("remauth") & filters.user(exempt_users))
async def rem_auth(_, message: Message):
    """Remove user from authorized list"""
    try:
        user_id = int(message.command[1])
        update_auth_users(user_id, "remove")
        await message.reply(f"✅ Removed {user_id} from authorized list!")
    except (IndexError, ValueError):
        await message.reply("❌ Usage: /remauth <user_id>")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

@app.on_message(filters.command("listauth") & filters.user(exempt_users))
async def list_auth(_, message: Message):
    """List authorized users"""
    if not authorized_users:
        await message.reply("ℹ️ No authorized users!")
    else:
        users = "\n".join(f"• <code>{uid}</code>" for uid in authorized_users)
        await message.reply(f"🛡️ Authorized Users:\n{users}", parse_mode="HTML")

@app.on_message(
    (filters.photo | filters.video | filters.document | 
     filters.sticker | filters.animation) & 
    ~filters.user(authorized_users)
)
async def filter_media(_, message: Message):
    """Filter NSFW media"""
    await process_media(message)

@app.on_message(filters.text & ~filters.user(authorized_users))
async def filter_text(_, message: Message):
    """Filter NSFW text"""
    text = message.text.lower()
    if any(re.search(rf'\b{kw}\b', text) for kw in NSFW_KEYWORDS):
        await take_action(message, "Text Message")

__PLUGIN__ = "nsfw_protector"
__DESCRIPTION__ = "Advanced NSFW content filtering system"
__COMMANDS__ = {
    "addauth <user_id>": "Authorize user to bypass filters",
    "remauth <user_id>": "Remove user authorization",
    "listauth": "List authorized users"
}
