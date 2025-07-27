import os
from os import getenv

# ✅ Core Bot Config
API_ID = int(getenv("API_ID", "0"))
API_HASH = getenv("API_HASH", "")
BOT_TOKEN = getenv("BOT_TOKEN", "")
BOT_USERNAME = getenv("BOT_USERNAME", "EsproChatBot")

# ✅ Owners & Authorization
OWNER_ID = list(map(int, getenv("OWNER_ID", "6656608288").split()))
AUTH_USERS = list(map(int, getenv("AUTH_USERS", "6656608288").split())) if getenv("AUTH_USERS") else []

# ✅ Support & Logger
SUPPORT_GROUP = getenv("SUPPORT_GROUP", "https://t.me/WerewolfDemonUpdate")
LOGGER_ID = int(getenv("LOGGER_ID", "-1002861883767"))

# ✅ MongoDB
MONGO_URL = getenv("MONGO_URL", "")

# ✅ Bot Commands Auto Setup
SETCMD = getenv("SETCMD", "True")

# ✅ Upstream Repo Settings
UPSTREAM_REPO = getenv("UPSTREAM_REPO", "https://github.com/WEREWOLF-DEMON/EsproChatBotDemon")
UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "main")
GIT_TOKEN = getenv("GIT_TOKEN", None)

# ✅ Sightengine API Keys for NSFW Detection
SIGHTENGINE_API_USER = getenv("SIGHTENGINE_API_USER", "1178928785")
SIGHTENGINE_API_SECRET = getenv("SIGHTENGINE_API_SECRET", "FxMLyJ9rw7f8jrXK3kS4JxuCpEzh7UrQ")
