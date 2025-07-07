from pyrogram import Client, filters
from pyrogram.types import Message
import re

app = Client("bio_link_filter_bot")

# ✅ Link keywords pattern (covers all types of links)
LINK_PATTERNS = [
    r"https?://",       # http:// or https://
    r"www\.",           # www.
    r"\.com",           # .com
    r"\.net",           # .net
    r"\.in",            # .in
    r"t\.me",           # Telegram link
    r"telegram\.me",
    r"instagram\.com",
    r"fb\.com",
    r"facebook\.com",
    r"onlyfans\.com",
    r"pornhub\.com",    # (optional — if NSFW filtering)
]

# ✅ Compile pattern
BIO_LINK_REGEX = re.compile("|".join(LINK_PATTERNS), re.IGNORECASE)

# ✅ Cache for blocked users
users_with_links = set()

# ✅ Function: Check if user's bio contains any link
async def bio_has_any_link(client, user_id: int) -> bool:
    try:
        user = await client.get_users(user_id)
        bio = user.bio or ""
        return BIO_LINK_REGEX.search(bio) is not None
    except:
        return False

# ✅ Main handler: Check user bio and delete messages
@app.on_message(filters.group & filters.text)
async def delete_if_bio_has_link(client: Client, message: Message):
    user = message.from_user
    if not user:
        return

    user_id = user.id

    # If already blocked, recheck bio to see if cleared
    if user_id in users_with_links:
        if await bio_has_any_link(client, user_id):
            try:
                await message.delete()
                return
            except:
                return
        else:
            users_with_links.discard(user_id)  # Bio cleaned, allow messages

    # Not in cache, check now
    if await bio_has_any_link(client, user_id):
        users_with_links.add(user_id)
        try:
            await message.delete()
        except:
            pass
