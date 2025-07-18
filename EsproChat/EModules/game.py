
from EsproChat import app
import random
import asyncio
import config

from pyrogram import filters, types
from nandha import pbot as bot
from nandha.db.game import update_cash, get_cash, update_name, get_steal_date, update_steal_date, get_top_users


from datetime import datetime, timedelta, date



__module__ = "Game"


__help__ = '''
*Commands*:
/steal, /bowl, /dart, /dice, /gamble, /balance, /richlist, /domain, /status

```
- /balance: Check your stash, cursed one 💰
- /dart and /bowl: Hit a 6 and score 10,000 cash. Land a 5 for 1,000 💸
  Unleash your cursed energy and aim true!
- /dice: Roll a 1 for 10,000 cash, or a 6 for 1,000 💸
  Let fate decide your fortune, sorcerer!
- /steal or /domain <reply to user>: Jack another cursed one's wallet once a day
  Swipe up to 1/3, 1/4, or 2/3 of their loot. Success ain't guaranteed, ya feel me?
- /gamble <amount>: Bet your cursed cash for a chance to double up
  High risk, high reward - that's the jujutsu way!
- /richlist: Peep the top ballers across all domains
  See who's really flexin' that cursed wealth!
- /status: show your game status.
- /characters: shows your owned characters.
```

*Note*:
Use these powers wisely, young jujutsu sorcerer. The Curse spirits are watching! 👁️
'''


dice_users = {}
dart_users = {}
bowl_users = {}


FLOOD_MAX = 10 # try again flood


# images

TRY_LATER_IMG = "https://raw.githubusercontent.com/NandhaxD/dumps/refs/heads/main/Makima/Makima_huh.jpg"
GOOD_LUCK_IMG = "https://raw.githubusercontent.com/NandhaxD/dumps/refs/heads/main/Makima/Makima_thumbs_up.jpg"
BAD_LUCK_IMG = "https://raw.githubusercontent.com/NandhaxD/dumps/refs/heads/main/Makima/Makima_moye.jpg"
SERIOUS_IMG = "https://raw.githubusercontent.com/NandhaxD/dumps/refs/heads/main/Makima/Makima_serious.jpg"

async def remove_user_after_delay(user_id, data):
    await asyncio.sleep(FLOOD_MAX * 60)
    if user_id in data:
        del data[user_id]


@bot.on_message(filters.command("setcash") & filters.user(config.DEV_LIST))
async def _setUserCash(_, m: types.Message):
      try:
         user_id = int(m.text.split()[1])
         cash = int(m.text.split()[2])
         ok = await update_cash(user_id, cash)
         if ok:
             await m.reply("Cash added to account!")         
      except Exception as e:
          return await m.reply(f"❌ ERROR: {e}")

@bot.on_message(filters.command("richlist"))
async def _richList(_, m: types.Message):
      users_list = await get_top_users()
      if not users_list:
          return await m.reply("*Yo, fam!* No top users in sight. 😅")
      else:
          text = "💸💸 **Rich Players flexin' in the groups... 💸💸**\n\n"
          for roll, user in enumerate(users_list, start=1):
              if user.get("name"):
                   text += f"{roll}, **{user['name']}** - {user['cash']} 💸\n"
              else:
                   text += f"{roll}, `{user['user_id']}` - {user['cash']} 💸\n"

          text += "**\nThink you can outshine me? Bring it on! 😼**"
          photo = "https://i.imgur.com/V5Fbjsi.jpeg"
          return await m.reply_photo(
            photo=photo,
            caption=text,
            quote=True
          )




@bot.on_message(filters.command("balance") & ~filters.forwarded)
async def _checkBalance(_, m: types.Message):
     user = m.from_user
     cash = await get_cash(user.id)
     if cash == 0:
         return await m.reply("*Bro* You are too poor try making some money otherwise you can't live in the world! 🥴")
     elif cash > 0:
         await update_name(user.id, user.full_name)
       
     text = f"**Yo, {user.full_name}! Your balance is a whopping {cash} cash!** 💸💸 [\u200B](https://i.imgur.com/3pVYYqD.jpeg). Now go buy some cool shades! 😎"
     return await m.reply(text, quote=True)



@bot.on_message(filters.command(["domain", "steal"]))
async def _stealCash(_, m: types.Message):
    user = m.from_user
    reply = m.reply_to_message
  
    if not reply: 
        return await m.reply_text("You need to reply to a fellow sorcerer, *bro* 😖")
    elif reply and (reply.from_user.is_bot or reply.from_user.id == user.id): 
        return
  
    user_cash = await get_cash(user.id)
    reply_user = reply.from_user
    today_date = date.today().day
  
    user_steal_date = await get_steal_date(user.id, reply_user.id)
  
    if user_steal_date and today_date == user_steal_date:
        return await m.reply_text("You've already pulled a heist today, *sorcerer*! Try again tomorrow, you crafty thief! 😈")
            
    elif user_cash > 999:
        reply_user_cash = await get_cash(reply_user.id)
        if reply_user_cash < 999:
            return await m.reply_text("Lol! Not enough cursed energy to steal from someone! They need at least 1000 cash 💸")

        else:
            msg = await m.reply("Activating Domain Expansion, Six Eyes! ...")
            await update_steal_date(user.id, reply_user.id, today_date)
            await asyncio.sleep(2)
            
            
            steal_percentage = random.randint(1, 60)
            okay = random.choice([True, False])
            
            if not okay:
                await msg.edit_text("😱 Oh no! You don't stand a chance against them today.")
            else:
                steal_cash = int((steal_percentage / 100) * reply_user_cash)
                await update_cash(user.id, steal_cash)
                await update_cash(reply_user.id, -steal_cash)
                await msg.edit_text(f"🤑 You just snagged {steal_cash} cash 💸💸 ({steal_percentage}%) from {reply_user.full_name}! You're a true sorcerer of fortune! 😼")
    else:
        return await m.reply_text("To pull off a heist, you need at least 1000 cash 💸. Time to exorcise some curses and earn that cash, *sorcerer*!")



@bot.on_message(filters.command(["bet", "gamble"]) & ~filters.forwarded)
async def _gamble(_, m: types.Message):
    user = m.from_user
    cash = await get_cash(user.id)
    if cash == 0:
        return await m.reply_text("😂 You're broke, *sorcerer*. Go exorcise some curses and come back.")
    else:
        if len(m.text.split()) < 2 or (m.text.split()[1].isdigit() is False):
            return await m.reply_text("🙄 What's wrong with you? Enter a valid amount, *sorcerer*.\nExample: /gamble 1000")
        gamble = int(m.text.split()[1])
        if cash < gamble:
            return await m.reply_text("😂 You think you're a special grade, but you're not. You don't have enough cash to gamble, *sorcerer*.")

        numbers = [2, -1.2, 0, 1.2, 0, -1.5, 1.5, 0, 0, 2.1, 1.3, 1.4, -1.2]
        user_number = random.choice(numbers)

        if user_number < 0:
            price = int(gamble * user_number)
            await update_cash(user.id, price)
            return await m.reply_text(
                f"🤧 [\u200B]({SERIOUS_IMG}) Oh no, *sorcerer*! You just lost {price} 💸 to a curse!"
            )
               
        elif user_number > 0:
            price = int(gamble * user_number)
            await update_cash(user.id, price)
            return await m.reply_text(f"🔥 Yessss, *sorcerer*! You just earned {price} Cash! You're on fire like Makima! 💸 [\u200B]({GOOD_LUCK_IMG})")
        else:
            await update_cash(user.id, -gamble)
            return await m.reply_text(f"😭 Oh no, *sorcerer*. You just lost {gamble} Cash. Better luck next time against the curses! 🤣 [\u200B]({BAD_LUCK_IMG})")
          

@bot.on_message(filters.command("dart")  & ~filters.forwarded)
async def _roll_dart(_, m: types.Message):
    user = m.from_user
    if dart_users.get(user.id):
        end_time = dart_users[user.id]
        current_time = datetime.now()
        remaining_time = end_time - current_time
        remaining_minutes = remaining_time.total_seconds() / 60
        return await m.reply_text(f"🥲 Please don't flood try again after {remaining_minutes:.2f} minutes ⏳ [\u200B]({TRY_LATER_IMG})")
      
    else:
       initial_time = timedelta(minutes=FLOOD_MAX)
       start_time = datetime.now()
       end_time = start_time + initial_time
       dart_users[user.id] = end_time
       msg_dice = await bot.send_dice(
         chat_id=m.chat.id,
         emoji="🎯",
         reply_to_message_id=m.id
       )
       value = msg_dice.dice.value
      
       cash = 0
         
       if value == 5:
            cash = 1000
       elif value == 6:
            cash = 10000
       else:
           await msg_dice.reply_text(f"Better luck next time, ghosty! 👻 [\u200B]({BAD_LUCK_IMG})")

       if cash > 0:
           await update_cash(user.id, cash)
           await msg_dice.reply_text(f"✨ **{user.full_name} earned {cash} cash.** 💵 [\u200B]({GOOD_LUCK_IMG})")
         
       return await asyncio.create_task(remove_user_after_delay(user.id, dart_users))

       
      


@bot.on_message(
  filters.command("bowl")  & ~filters.forwarded
)
async def _roll_bowl(_, m: types.Message):
    user = m.from_user
    if bowl_users.get(user.id):
        end_time = bowl_users[user.id]
        current_time = datetime.now()
        remaining_time = end_time - current_time
        remaining_minutes = remaining_time.total_seconds() / 60
        return await m.reply_text(f"🥲 Please don't flood try again after {remaining_minutes:.2f} minutes ⏳ [\u200B]({TRY_LATER_IMG})")

    else:
       initial_time = timedelta(minutes=FLOOD_MAX)
       start_time = datetime.now()
       end_time = start_time + initial_time
       bowl_users[user.id] = end_time
       msg_dice = await bot.send_dice(
         chat_id=m.chat.id,
         emoji="🎳",
         reply_to_message_id=m.id
       )
       value = msg_dice.dice.value
      
       cash = 0
         
       if value == 5:
            cash = 1000
       elif value == 6:
            cash = 10000
       else:
           await msg_dice.reply_text(f"Better luck next time, ghosty! 👻[\u200B]({SERIOUS_IMG})")

       if cash > 0:
           await update_cash(user.id, cash)
           await msg_dice.reply_text(f"✨ **{user.full_name} Earned {cash} Cash.** 💵[\u200B]({GOOD_LUCK_IMG})")
         
       return await asyncio.create_task(remove_user_after_delay(user.id, bowl_users))

       


@bot.on_message(
  filters.command("dice")  & ~filters.forwarded
)
async def _roll_dice(_, m: types.Message):
    user = m.from_user
    if dice_users.get(user.id):
        end_time = dice_users[user.id]
        current_time = datetime.now()
        remaining_time = end_time - current_time
        remaining_minutes = remaining_time.total_seconds() / 60
        return await m.reply_text(f"🥲 **Please don't flood try again after {remaining_minutes:.2f} minutes** ⏳ [\u200B]({TRY_LATER_IMG})")

    else:
       initial_time = timedelta(minutes=FLOOD_MAX)
       start_time = datetime.now()
       end_time = start_time + initial_time
       dice_users[user.id] = end_time
       msg_dice = await bot.send_dice(
         chat_id=m.chat.id,
         emoji="🎲",
         reply_to_message_id=m.id
       )
       value = msg_dice.dice.value
      
       cash = 0
         
       if value == 6:
            cash = 1000
       elif value == 1:
            cash = 10000
       else:
           await msg_dice.reply_text(f"Better luck next time, ghosty! 👻[\u200B]({SERIOUS_IMG})")

       if cash > 0:
           await update_cash(user.id, cash)
           await msg_dice.reply_text(f"✨ **{user.full_name} Earned {cash} Cash.** 💵[\u200B]({GOOD_LUCK_IMG})")
         
       return await asyncio.create_task(remove_user_after_delay(user.id, dice_users))

       
