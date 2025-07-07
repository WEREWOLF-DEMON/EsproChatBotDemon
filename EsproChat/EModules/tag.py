from pyrogram import Client, filters
from pyrogram.enums import ChatType, ChatMemberStatus
from pyrogram.errors import UserNotParticipant
import asyncio
import random
from EsproChat import app

# Normal font funny/sweet messages
TAGMES = [
    "Hey, kaha ho? 🤗",
    "Aaj bhool gaye kya hume? 😢",
    "Voice chat aao na 🥺",
    "Hello ji, kaise ho?",
    "Tumhari yaad aa rahi hai 😍",
    "Muskurao, kyunki aaj bhi tum pyare lag rahe ho 💖",
    "Kuch to bol do na 🥲",
    "Aap jaise dost ka koi mol nahi 💎",
    "Tum ho kaun? Hume bhool gaye kya? 😏",
    "Online aao, party karni hai 🥳",

    # 50 New Added
    "Good morning sabko ☀️",
    "Kya haal chaal hai aapka?",
    "Aaj ka plan kya hai? 😜",
    "Coffee pila do koi ☕",
    "Kya tumhe song sunna pasand hai?",
    "Chalo choti si game khelte hain 🎮",
    "Mujhe miss kiya kya? 😅",
    "Aaj to full masti karenge 🕺",
    "Yaar tu kitna cute hai 😍",
    "Dil garden garden ho gaya 🌸",

    "Suno ji, baat karo zara 📞",
    "Kitna busy ho yaar tum 😒",
    "Dil ki baat share karo 💬",
    "Tumse milke acha laga 🤝",
    "Tu meri list me top pe hai ✨",
    "Pyar wali vibes aa rahi hai 💘",
    "Mere bina bore to nahi ho?",
    "Kya tum single ho? 👀",
    "Chup mat raho yaar 😶",
    "Kya tum dost banoge mera? 🤝",

    "Bhai tu real hai ya AI 😄",
    "Kya tumko meme pasand hai?",
    "Kya haal hai school/college ka?",
    "Aaj kuch naya seekha kya?",
    "Tumhara mood kaisa hai? 🤔",
    "Mujhe bhi batao apna secret 😅",
    "Aj kal kam dikh rahe ho 😐",
    "Jaldi reply karo yaar 📨",
    "Bina tumhare group suna suna lagta hai 😔",
    "Sab kuch theek hai na? 🤗",

    "Aap group ke hero ho 💪",
    "Friendship forever 💞",
    "Tum smile bahut pyari hai 😊",
    "Tum online ho to sab kuch bright lagta hai 🔆",
    "Apni ek selfie bhejo 📸",
    "Zara nazar to milaao 😳",
    "Thoda time mere liye bhi nikaalo ⏰",
    "Ye group tumhare bina adhoora hai 🥹",
    "Tum perfect ho 🥰",
    "Tumhe padhai me interest hai kya? 📚",

    "Kya kal movie dekhi? 🎬",
    "Tumse baat kar ke acha laga 😇",
    "Apni awaz bhejo na 🎤",
    "Aj mausam bada suhana hai 🌧️",
    "Kya tum singer ho? 😁",
    "Chalo milkar ek song gaate hain 🎵",
    "Kya tum real ho ya sapna? 🤭",
    "Tum group ke jaan ho 😍",
    "Mujhe bhool to nahi gaye 😔",
    "Aj sad hoon, tum baat karo na 🥺",

    "Tum online ho to maza aa jata hai 😍",
    "Bas tumhari yaad aa rahi hai 🤗",
    "Thoda sa hass do na 😅",
    "Group me tumhari kami mehsoos ho rahi hai 😢",
    "Suno zara, ek baat karni hai 💬",
    "Aaj ka din kaise guzra? ☀️",
    "Tum mujhe ache lagte ho... seriously! ❤️",
    "Aaj tumhe dekhkar din ban gaya 😄",
    "Tum itne cute kyun ho? 😳",
    "Main tumhara intezaar kar raha hoon 🕰️",
    
    "Hello hello hello, kaha ghoom rahe ho? 👀",
    "Tumhare bina sab suna suna lagta hai 🥺",
    "Ek smile bhej do please 😊",
    "Kya chal raha hai aajkal? 😏",
    "Apna favourite gana batao 🎵",
    "Tum school/college se bhag gaye kya? 😜",
    "Kya tum bhi mujhe yaad karte ho? 🤔",
    "Chalo ek photo bhejo 😁",
    "Mujhe tumhari zarurat hai 💖",
    "Tumhari baatein miss kar raha hoon 😔",
    
    "Group me aake kuch baat to karo 🗨️",
    "Tum sirf dekhte ho, kuch likhte kyun nahi? 🤨",
    "Kaash tumse mil sakta 💌",
    "Kya haal hai jaaneman 😂",
    "Aj group me full toofan hona chahiye 🌪️",
    "Tum jaise log rare hote hain 💎",
    "Kya tum shadi karne layak ho? 😜",
    "Aaj mausam bhi romantic hai aur tum bhi 🥰",
    "Tum group me jaan ho 🧡",
    "Tum online ho to lagta hai sab kuch sahi hai 😇",
    
    "Thoda chill kar lo na 😎",
    "Pakka tum kuch chhupa rahe ho 😝",
    "Tumhare jokes best hote hain 😂",
    "Tumhara DP bohot mast hai 📸",
    "Aaj party kiski taraf se hai? 🥳",
    "Kya tum bhi bore ho rahe ho? 😐",
    "Ek truth aur dare khelenge kya? 🎲",
    "Tumse pyar hone laga hai 💘",
    "Tum itne dino baad online aaye ho 🤩",
    "Aaj group me dhamal karna hai 💥",
    
    "Kya tum mere friend banoge? 🤝",
    "Tum group ke sabse pyare member ho 💖",
    "Tumhara username bohot unique hai 🔥",
    "Lagta hai aaj tum mood me ho 😜",
    "Tum mujhe confuse kar dete ho 😅",
    "Aaj koi naya joke sunao na 😂",
    "Tumko gaana sunna pasand hai kya? 🎧",
    "Aaj kya naya seekha? 📚",
    "Ek kahani batao zara 📖",
    "Tumhara favourite color kya hai? 🎨",
    
    "Tum apna number de sakte ho kya? 📱",
    "Tumse baat karke accha lagta hai 💬",
    "Thoda slow chal bhai 😄",
    "Tum itne smart kaise ho gaye? 😏",
    "Main hamesha online hoon, tum kab aate ho? 📲",
    "Kya tum mujhe bhool gaye? 😕",
    "Aj group dead kyun hai? 💤",
    "Sab kuch theek hai na? 🤍",
    "Aj group me tum hi highlight ho 💫",
    "Tumhare bina kuch adhura lagta hai 😔",
    
    "Ek secret batao apna 🤫",
    "Tum group ke sabse active member ho 🔥",
    "Tumhari aankhon me kuch baat hai 😳",
    "Thoda chill mode me aao 😌",
    "Mujhe tumhare saath hangout karna hai 😎",
    "Tum kuch likho, sab khush ho jayein 🤭",
    "Kaise ho legend? 😅",
    "Bhai aj to full masti karein 🎉",
    "Mujhe bhi apni squad me le lo 🧑‍🤝‍🧑",
    "Tum best ho, seriously 🥹"
]

spam_chats = []


@app.on_message(filters.command(["ritik"]))
async def tag_all_members(client, message):
    chat_id = message.chat.id

    if message.chat.type != ChatType.SUPERGROUP:
        return await message.reply("⚠️ Ye command sirf supergroups me kaam karta hai.")

    # Admin check
    try:
        user = await client.get_chat_member(chat_id, message.from_user.id)
        if user.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
            return await message.reply("🔐 Sirf admins hi ye command chala sakte hain.")
    except:
        return await message.reply("❌ Admin status check nahi ho paya.")

    if chat_id in spam_chats:
        return await message.reply("⏳ Already tagging. Use /tagoff to stop.")

    spam_chats.append(chat_id)
    await message.reply("✅ Tagging start ho gaya hai...")

    try:
        async for member in client.get_chat_members(chat_id):
            if chat_id not in spam_chats:
                break

            if member.user.is_bot:
                continue

            tag = f"[{member.user.first_name}](tg://user?id={member.user.id})"
            text = f"{tag} {random.choice(TAGMES)}"

            try:
                await client.send_message(chat_id, text)
                await asyncio.sleep(3)
            except Exception as e:
                print(f"Error tagging {member.user.id}: {e}")
                await asyncio.sleep(2)

    finally:
        if chat_id in spam_chats:
            spam_chats.remove(chat_id)

@app.on_message(filters.command(["ritikoff"]))
async def stop_tagging(client, message):
    chat_id = message.chat.id

    try:
        user = await client.get_chat_member(chat_id, message.from_user.id)
        if user.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
            return await message.reply("🔐 Sirf admins hi tag ko stop kar sakte hain.")
    except:
        return await message.reply("❌ Admin status check nahi ho paya.")

    if chat_id in spam_chats:
        spam_chats.remove(chat_id)
        return await message.reply("⛔ Tagging band kar diya gaya hai.")
    else:
        return await message.reply("⚠️ Abhi koi tagging nahi chal raha.")
