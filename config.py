import os
from os import getenv


API_ID = int(os.environ.get("API_ID"))


API_HASH = os.environ.get("API_HASH")


BOT_TOKEN = os.environ.get("BOT_TOKEN")


BOT_USERNAME = getenv("BOT_USERNAME" , "EsproChatBot")


OWNER_ID = list(
    map(int, getenv("OWNER_ID", "6656608288").split())
) 

#Fill Only Username Without @
SUPPORT_GROUP = getenv(
    "SUPPORT_GROUP", "https://t.me/WerewolfDemonUpdate"
)  

MONGO_URL = os.environ.get("MONGO_URL")

LOGGER_ID = int(getenv("LOGGER_ID", "-1002861883767"))

# set True if you want yo set bot commands automatically 
SETCMD = getenv("SETCMD", "True")

# upstream repo 
UPSTREAM_REPO = getenv(
    "UPSTREAM_REPO",
    "https://github.com/RitikRohin/EsproChatBot",
)

UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "main")

# GIT TOKEN ( if your edited repo is private)
GIT_TOKEN = getenv("GIT_TOKEN", None)
