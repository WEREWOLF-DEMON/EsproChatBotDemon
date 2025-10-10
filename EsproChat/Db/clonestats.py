from EsproChat import db as mongodb

cloneownerdb = mongodb.cloneownerdb
clonebotdb = mongodb.clonebotdb

def get_bot_users_collection(bot_id):
    from EsproChat import db as mongodb
    return mongodb[f"{bot_id}_users"]

def get_bot_chats_collection(bot_id):
    from EsproChat import db as mongodb
    return mongodb[f"{bot_id}_chats"]

async def is_served_cuser(bot_id, user_id: int) -> bool:
    usersdb = get_bot_users_collection(bot_id)
    user = await usersdb.find_one({"user_id": user_id})
    if not user:
        return False
    return True

async def add_served_cuser(bot_id, user_id: int):
    usersdb = get_bot_users_collection(bot_id)
    is_served = await is_served_cuser(bot_id, user_id)
    if is_served:
        return
    return await usersdb.insert_one({"user_id": user_id})

async def get_served_cusers(bot_id) -> list:
    usersdb = get_bot_users_collection(bot_id)
    return await usersdb.find({"user_id": {"$gt": 0}}).to_list(length=None)

async def is_served_cchat(bot_id, chat_id: int) -> bool:
    chatsdb = get_bot_chats_collection(bot_id)
    chat = await chatsdb.find_one({"chat_id": chat_id})
    if not chat:
        return False
    return True

async def add_served_cchat(bot_id, chat_id: int):
    chatsdb = get_bot_chats_collection(bot_id)
    is_served = await is_served_cchat(bot_id, chat_id)
    if is_served:
        return
    return await chatsdb.insert_one({"chat_id": chat_id})

async def get_served_cchats(bot_id) -> list:
    chatsdb = get_bot_chats_collection(bot_id)
    return await chatsdb.find({"chat_id": {"$lt": 0}}).to_list(length=None)
