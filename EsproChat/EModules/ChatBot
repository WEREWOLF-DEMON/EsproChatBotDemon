from pyrogram import Client, filters, types, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from motor.motor_asyncio import AsyncIOMotorClient
import requests
from config import MONGO_URL
from EsproChat import app
from pyrogram.enums import ChatAction, ChatType

# MongoDB Setup
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client.appdatabass
chatbotdatabase = db.cappdarabase


# Admin Checker
async def is_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    except:
        return False


# /chatbot command
@app.on_message(filters.command("chatbot") & filters.group, group=6)
async def chatbot_command(_, message: Message):
    if await is_admin(message.chat.id, message.from_user.id):
        try:
            response = requests.get("https://nekos.best/api/v2/neko", timeout=5).json()
            image_url = response["results"][0]["url"]
        except Exception:
            image_url = "https://te.legra.ph/file/9a353dbac4665980f738a.jpg"  # fallback neko image

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="Eɴᴀʙʟᴇ ✅", callback_data="enable_chatbot"),
                    InlineKeyboardButton(text="Dɪsᴀʙʟᴇ ❌", callback_data="disable_chatbot"),
                ]
            ]
        )
        await message.reply_photo(
            image_url,
            caption=f"ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ᴛᴏ ᴇɴᴀʙʟᴇ ᴏʀ ᴅɪꜱᴀʙʟᴇ ᴄʜᴀᴛʙᴏᴛ ɪɴ <b>{message.chat.title}</b>",
            reply_markup=keyboard,
        )
    else:
        await message.reply_text("❌ Only group admins can use this command.", quote=True)


# Enable/Disable via button
@app.on_callback_query(filters.regex(r"^(enable|disable)_chatbot$"))
async def enable_disable_chatbot(_, query: types.CallbackQuery):
    chat_id = query.message.chat.id
    action = query.data

    if await is_admin(chat_id, query.from_user.id):
        if action == "enable_chatbot":
            exists = await chatbotdatabase.find_one({"chat_id": chat_id})
            if exists:
                await query.answer("✅ Chatbot is already enabled.", show_alert=True)
            else:
                await chatbotdatabase.insert_one({"chat_id": chat_id})
                await query.answer("✅ Chatbot enabled!", show_alert=True)
                await query.message.edit_text(f"✅ Chatbot enabled by {query.from_user.mention()}")
        else:  # disable_chatbot
            exists = await chatbotdatabase.find_one({"chat_id": chat_id})
            if exists:
                await chatbotdatabase.delete_one({"chat_id": chat_id})
                await query.answer("❌ Chatbot disabled!", show_alert=True)
                await query.message.edit_text(f"❌ Chatbot disabled by {query.from_user.mention()}")
            else:
                await query.answer("⚠️ Chatbot is not enabled yet.", show_alert=True)
    else:
        await query.answer("❌ Only group admins can control chatbot.", show_alert=True)


# Reply to text (private + group)
@app.on_message(filters.text & ~filters.bot, group=4)
async def chatbottexts(client, message: Message):
    user_id = message.from_user.id
    user_message = message.text

    # Handle Private Chat
    if message.chat.type == ChatType.PRIVATE:
        api_url = f"http://api.brainshop.ai/get?bid=181999&key=BTx5oIaCq8Cqut3S&uid={user_id}&msg={user_message}"
        try:
            response = requests.get(api_url, timeout=5).json().get("cnt")
            await message.reply_text(response)
        except Exception as e:
            print(f"[Private Chatbot Error] {e}")
            await message.reply_text("❌ Brain is sleeping. Try again later.")

    # Handle Group Chat
    else:
        if (message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.is_self) or not message.reply_to_message:
            chatbot_info = await chatbotdatabase.find_one({"chat_id": message.chat.id})
            if chatbot_info:
                try:
                    api_url = f"http://api.brainshop.ai/get?bid=181999&key=BTx5oIaCq8Cqut3S&uid={user_id}&msg={user_message}"
                    response = requests.get(api_url, timeout=5).json().get("cnt")
                    await client.send_chat_action(message.chat.id, ChatAction.TYPING)
                    await message.reply_text(response)
                except Exception as e:
                    print(f"[Group Chatbot Error] {e}")
                    # Don’t crash; just ignore
                    return
