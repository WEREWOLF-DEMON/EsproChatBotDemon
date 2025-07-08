from pyrogram import Client, filters
from pyrogram.types import Message
import random
from EsproChat import app


# 🎉 List of 50 Random Welcome Messages
WELCOME_MESSAGES = [
    "Hey {mention}, welcome to {chat} 😄",
    "🎉 {mention} just joined {chat}! Make yourself at home.",
    "Glad to have you here, {mention} in {chat} 💫",
    "A wild {mention} appeared in {chat} 😍",
    "Warm welcome to {mention} in {chat}! 🌟",
    "{mention} joined the party! 🥳 Welcome to {chat}!",
    "Hello {mention}, great to see you in {chat} 💖",
    "Welcome aboard, {mention}! 🚀 Enjoy your stay at {chat}",
    "Big cheers to {mention} who just joined {chat} 🎊",
    "What's up {mention}? Welcome to {chat} 👋",
    "Brace yourself {chat}, {mention} has arrived! 😎",
    "Woohoo! {mention} is here now. Welcome to {chat}! 🕺",
    "Say hi to {mention}, our newest member in {chat} 👋",
    "Welcome to the gang, {mention}! 💃 This is {chat}",
    "Oh look! {mention} just landed in {chat} ✈️",
    "Yayy! {mention} made it to {chat} 🎉 Let’s get started!",
    "Boom! {mention} dropped into {chat} like a boss 😎",
    "{mention} has entered the chat 🚪 Welcome to {chat}!",
    "Make way! {mention} has arrived in {chat} 🏁",
    "A warm hug for {mention} ❤️ Welcome to {chat}!",
    "{mention}, welcome to the world of {chat} 🌍",
    "Surprise! {mention} is now part of {chat} 🪄",
    "Hi {mention}, welcome to your second home — {chat} 🏠",
    "{mention} came with swag into {chat} 🧢✨",
    "Let’s welcome {mention} with open hearts 💝 to {chat}",
    "{mention}, you're officially one of us now in {chat} 💫",
    "Look who's here! It's {mention}! Welcome to {chat} 🌟",
    "Be cool, {mention} has joined {chat} 🧊",
    "{mention} is in the house! Welcome to {chat} 🏠",
    "Hugs and smiles to {mention}, welcome to {chat} 😊",
    "Hey {mention}, let’s make some memories in {chat} 📸",
    "Lights, camera, welcome {mention} to {chat} 🎬",
    "🎈 Cheers to {mention}, the newest face in {chat}",
    "Big welcome to {mention} — part of the {chat} fam now! 👪",
    "{mention} teleported into {chat} 🚀",
    "Feeling lucky? {mention} just joined {chat} 🍀",
    "We were waiting for you, {mention}. Welcome to {chat} 🕰️",
    "Namaste {mention} 🙏 Welcome to {chat}",
    "One of us! One of us! Welcome {mention} to {chat} 🤝",
    "Let’s throw confetti for {mention} 🎊 Welcome to {chat}",
    "{mention}, bring your vibes into {chat} 🎶",
    "{mention}, welcome to our digital adda — {chat} 💻",
    "Applause! {mention} entered {chat} 👏",
    "Kya baat hai! {mention} joined {chat} 😍",
    "Welcome ke saath chai bhi milegi, {mention} ☕ in {chat}",
    "Hello hello {mention}, welcome to {chat} 🎤",
    "{mention}, we hope you brought snacks 🍿 Welcome to {chat}",
    "Yahan dosti bhi hogi, masti bhi! Welcome {mention} to {chat} 🥰",
    "New face, same energy 🔥 Welcome {mention} to {chat}",
    "{mention} is now live in {chat} 📺",
    "Dhamakedar welcome to {mention} 💥 in {chat}",
    "Aaj ka naya member: {mention} 🎉 Welcome to {chat}",
]

# 👋 Handle New Chat Members (add, invite, request accept)
@app.on_message(filters.new_chat_members)
async def welcome_new_member(client, message: Message):
    for member in message.new_chat_members:
        if member.is_bot:
            continue  # Ignore bots

        mention = member.mention(style="markdown")
        chat_name = message.chat.title
        welcome_text = random.choice(WELCOME_MESSAGES).format(mention=mention, chat=chat_name)

        await message.reply_text(
            welcome_text,
            disable_web_page_preview=True
        )
