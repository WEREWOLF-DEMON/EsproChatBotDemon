from EsproChat import app
from pyrogram import filters
from pyrogram.types import Message
from config import OWNER_ID
import requests
import re
import asyncio
import os
import json
from typing import Optional, List, Union

# Sightengine Configuration
SIGHTENGINE_USER = "1916313622"  # Replace with your actual API user
SIGHTENGINE_SECRET = "frPDtcGYH42kUkmsKuGoj9SVYHCMW9QA"  # Replace with your actual API secret
SE_CREDENTIALS_AVAILABLE = bool(SIGHTENGINE_USER and SIGHTENGINE_SECRET)

# Database to store exempt user IDs
exempt_users: List[int] = []

# Create downloads directory if it doesn't exist
if not os.path.exists('downloads'):
    os.makedirs('downloads')

# Proper OWNER_ID handling from config.py
if isinstance(OWNER_ID, (list, tuple)):
    exempt_users.extend(map(int, OWNER_ID))
elif OWNER_ID:
    exempt_users.append(int(OWNER_ID))

# Enhanced NSFW keywords
NSFW_KEYWORDS = [
    # Sexual content
    "porn", "xxx", "adult", "nsfw", "sex", "fuck", "dick", "pussy", "boobs", "nude",
    # Profanity
    "shit", "asshole", "bitch", "bastard", "cunt", 
    # Drugs and substances
    "drugs?", "heroin", "cocaine", "weed", "marijuana", "hash", "lsd", "ecstasy",
    "meth", "opium", "ganja", "charas", "bhang", "smack", "crack", "amphetamine",
    # Violence
    "kill", "murder", "rape", "terrorist", "bomb", "shoot", 
    # Self-harm
    "suicide", "selfharm", "cutting"
]

def check_nsfw(file_path: str) -> Optional[dict]:
    """Check content using Sightengine API"""
    if not SE_CREDENTIALS_AVAILABLE:
        return None
        
    params = {
        'models': 'nudity-2.1,weapon,alcohol,recreational_drug,gore-2.0,violence,self-harm',
        'api_user': SIGHTENGINE_USER,
        'api_secret': SIGHTENGINE_SECRET
    }
    
    try:
        with open(file_path, 'rb') as f:
            files = {'media': f}
            response = requests.post(
                'https://api.sightengine.com/1.0/check.json',
                files=files,
                data=params,
                timeout=10
            )
        result = response.json()
        
        if 'error' in result:
            print(f"Sightengine Error: {result['error']['message']}")
            return None
            
        return result
        
    except Exception as e:
        print(f"API Error: {e}")
        return None

async def process_media(message: Message):
    """Handle media content checking"""
    if not SE_CREDENTIALS_AVAILABLE:
        return
        
    file_path = None
    try:
        # Download file to specific directory
        file_path = await message.download(file_name="downloads/")
        
        if not file_path or not os.path.exists(file_path):
            print(f"Download failed for message {message.id}")
            return
            
        result = check_nsfw(file_path)
        
        if result:
            nsfw_detected = False
            reasons = []
            
            checks = {
                'sexual content': result.get('nudity', {}).get('sexual_activity', 0) > 0.7,
                'violence': result.get('violence', {}).get('prob', 0) > 0.7,
                'drugs': result.get('drug', {}).get('prob', 0) > 0.7,
                'self-harm': result.get('selfharm', {}).get('prob', 0) > 0.7,
                'gore': result.get('gore', {}).get('prob', 0) > 0.7
            }
            
            for reason, detected in checks.items():
                if detected:
                    nsfw_detected = True
                    reasons.append(reason)
                
            if nsfw_detected:
                await message.delete()
                warn = await message.reply(f"⚠️ Removed for: {', '.join(reasons)}")
                await asyncio.sleep(10)
                await warn.delete()
                
    except Exception as e:
        print(f"Media processing error: {e}")
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass

@app.on_message(filters.command(["addnsfw"]) & filters.user(exempt_users))
async def add_exempt(client, message: Message):
    """Add user to NSFW exempt list"""
    try:
        user_id = int(message.command[1])
        if user_id not in exempt_users:
            exempt_users.append(user_id)
            await message.reply(f"✅ Added {user_id} to exempt list!")
        else:
            await message.reply(f"ℹ️ {user_id} is already exempt")
    except (IndexError, ValueError):
        await message.reply("❌ Usage: /addnsfw <user_id>")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

@app.on_message(filters.command(["remnsfw"]) & filters.user(exempt_users))
async def remove_exempt(client, message: Message):
    """Remove user from NSFW exempt list"""
    try:
        user_id = int(message.command[1])
        if user_id in exempt_users:
            exempt_users.remove(user_id)
            await message.reply(f"✅ Removed {user_id} from exempt list!")
        else:
            await message.reply(f"ℹ️ {user_id} is not in exempt list")
    except (IndexError, ValueError):
        await message.reply("❌ Usage: /remnsfw <user_id>")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

@app.on_message(filters.command(["listnsfw"]) & filters.user(exempt_users))
async def list_exempt(client, message: Message):
    """List all NSFW exempt users"""
    if not exempt_users:
        await message.reply("ℹ️ No exempt users!")
    else:
        users_list = "\n".join(f"• <code>{uid}</code>" for uid in exempt_users)
        await message.reply(f"🛡️ Exempt Users:\n{users_list}", parse_mode="HTML")

@app.on_message(
    (filters.photo | filters.video | filters.document | filters.sticker | filters.animation) & 
    ~filters.user(exempt_users)
)
async def media_filter(client, message: Message):
    """Filter all media content including stickers"""
    await process_media(message)

@app.on_message(filters.text & ~filters.user(exempt_users))
async def text_filter(client, message: Message):
    """Filter text messages for NSFW content"""
    text = message.text.lower()
    if any(re.search(rf'\b{kw}\b', text) for kw in NSFW_KEYWORDS):
        await message.delete()
        warn = await message.reply("⚠️ Message removed for policy violation")
        await asyncio.sleep(10)
        await warn.delete()

# Plugin information
__PLUGIN__ = "nsfw_filter"
__DESCRIPTION__ = "Advanced NSFW content filtering system"
__COMMANDS__ = {
    "addnsfw <user_id>": "Add user to exempt list",
    "remnsfw <user_id>": "Remove user from exempt list",
    "listnsfw": "List exempt users"
}
