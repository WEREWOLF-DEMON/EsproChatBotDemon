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
NEKOS_API = "https://nekos.best/api/v2/neko"

# Initialize users from config.py
def get_user_ids(ids):
    if isinstance(ids, list):
        return tuple(int(i) for i in ids)
    return (int(ids),) if ids else ()

# Owner and authorized users (initialize from config)
owner_ids = get_user_ids(OWNER_ID)
authorized_users = set(owner_ids)  # Starts with just owners

# Ensure downloads directory exists
os.makedirs('downloads', exist_ok=True)

# NSFW detection thresholds
NSFW_THRESHOLDS = {
    'sexual_activity': 0.15,
    'sexual_display': 0.15,
    'weapon': 0.25,
    'drug': 0.25,
    'violence': 0.25
}

# NSFW keywords
NSFW_KEYWORDS = [
    r"\b(porn|xxx|adult|nsfw|sex|fuck|dick|pussy|boobs|nude|naked)\b",
    r"\b(shit|asshole|bitch|bastard|cunt|whore|slut)\b",
    r"\b(drugs|heroin|cocaine|weed|marijuana|hash|lsd|ecstasy|meth)\b",
    r"\b(kill|murder|rape|terrorist|bomb|shoot|gun|attack)\b",
    r"\b(suicide|selfharm|cutting|hang|die)\b"
]

async def get_random_neko():
    """Get random neko image from API"""
    try:
        response = await asyncio.to_thread(requests.get, NEKOS_API, timeout=5)
        return response.json()['results'][0]['url']
    except Exception as e:
        logger.error(f"Neko API Error: {e}")
        return None

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
        
        for key, threshold in NSFW_THRESHOLDS.items():
            if result.get('nudity', {}).get(key, 0) > threshold:
                return True
            if result.get(key, 0) > threshold:
                return True
        return False
    except Exception as e:
        logger.error(f"NSFW Check Error: {e}")
        return False

async def take_action(message: Message, content_type: str):
    """Delete content and send warning"""
    try:
        user = message.from_user
        neko_url = await get_random_neko()
        
        await message.delete()
        
        warning_msg = (
            f"⚠️ <b>Content Removed</b> ⚠️\n\n"
            f"• <b>User:</b> {user.mention if user else 'Unknown'}\n"
            f"• <b>Type:</b> {content_type}\n"
            f"• <b>Action:</b> Removed for policy violation\n\n"
            "<i>This content crossed our safety thresholds</i>"
        )
        
        if neko_url:
            sent_msg = await message.reply_photo(
                photo=neko_url,
                caption=warning_msg,
                parse_mode="HTML"
            )
        else:
            sent_msg = await message.reply(
                warning_msg,
                parse_mode="HTML"
            )
            
        await asyncio.sleep(8)
        await sent_msg.delete()
        
    except Exception as e:
        logger.error(f"Action Error: {e}")

async def process_media(message: Message):
    """Process media content checking"""
    file_path = None
    try:
        file_path = await message.download(file_name='downloads/')
        if file_path and await check_nsfw(file_path):
            content_type = "Media"
            if message.sticker:
                content_type = "Sticker"
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

@app.on_message(filters.command("authorize") & filters.user(owner_ids))
async def authorize_user(_, message: Message):
    """Add user to authorized list"""
    try:
        if len(message.command) < 2:
            await message.reply("❌ Usage: /authorize <user_id>")
            return
            
        user_id = int(message.command[1])
        if user_id in authorized_users:
            await message.reply(f"ℹ️ User {user_id} is already authorized")
        else:
            authorized_users.add(user_id)
            await message.reply(f"✅ Authorized user {user_id}")
            
    except (IndexError, ValueError):
        await message.reply("❌ Usage: /authorize <user_id>")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

@app.on_message(filters.command("unauthorize") & filters.user(owner_ids))
async def unauthorize_user(_, message: Message):
    """Remove user from authorized list"""
    try:
        if len(message.command) < 2:
            await message.reply("❌ Usage: /unauthorize <user_id>")
            return
            
        user_id = int(message.command[1])
        if user_id not in authorized_users:
            await message.reply(f"ℹ️ User {user_id} is not authorized")
        else:
            authorized_users.discard(user_id)
            await message.reply(f"✅ Unauthorized user {user_id}")
            
    except (IndexError, ValueError):
        await message.reply("❌ Usage: /unauthorize <user_id>")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

@app.on_message(filters.command("authorized") & filters.user(owner_ids))
async def list_authorized(_, message: Message):
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
async def media_filter(_, message: Message):
    """Filter media for unauthorized users"""
    await process_media(message)

@app.on_message(filters.text & ~filters.user(authorized_users))
async def text_filter(_, message: Message):
    """Filter text for unauthorized users"""
    text = message.text.lower()
    if any(re.search(pattern, text) for pattern in NSFW_KEYWORDS):
        await take_action(message, "Text Message")

__PLUGIN__ = "nsfw_protector"
__DESCRIPTION__ = "Advanced NSFW content filtering with authorization system"
__COMMANDS__ = {
    "authorize <user_id>": "Authorize user to bypass filters (Owner only)",
    "unauthorize <user_id>": "Remove user authorization (Owner only)",
    "authorized": "List authorized users (Owner only)"
}
