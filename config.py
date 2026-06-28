import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_NAME = "ZELROVA"
    VERSION = "1.0 Final"
    MISSION = "One Bot. Everything You Need."

    PREFIX = os.getenv("BOT_PREFIX", "z!")
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))

    APPLICATION_ID = os.getenv("APPLICATION_ID", os.getenv("CLIENT_ID", ""))
    CLIENT_ID = os.getenv("CLIENT_ID", APPLICATION_ID)
    CLIENT_SECRET = os.getenv("CLIENT_SECRET", "")
    PUBLIC_KEY = os.getenv("PUBLIC_KEY", "")

    SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_THIS_SECRET_KEY")
    DASHBOARD_ENABLED = os.getenv("DASHBOARD_ENABLED", "true").lower() == "true"

    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5000"))
    DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://127.0.0.1:5000").rstrip("/")

    DISCORD_SERVER_INVITE = os.getenv(
        "DISCORD_SERVER_INVITE",
        "https://discord.gg/32urRvMMHf"
    )

    BOT_INVITE_URL = (
        "https://discord.com/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        "&permissions=8"
        "&scope=bot%20applications.commands"
    )

    DATABASE_TYPE = os.getenv("DATABASE_TYPE", "json")
    DATA_DIR = os.getenv("DATA_DIR", "data")
    DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(DATA_DIR, "database.json"))
    BACKUP_DIR = os.getenv("BACKUP_DIR", "backups")
    LOG_DIR = os.getenv("LOG_DIR", "logs")

    THEME_DEFAULT = "dark-red-purple-blue"

    DEFAULT_MODULES = {
        "home": True,
        "overview": True,
        "moderation": True,
        "security": True,
        "automod": True,
        "welcome": True,
        "reaction_roles": True,
        "tickets": True,
        "levels": True,
        "logs": True,
        "announcements": True,
        "analytics": True,
        "backup": True,
        "restore": True,
        "ai": True,
        "music": True,
        "community": True,
        "servers": True,
        "top_trusted_servers": True,
        "onboarding": True,
        "owner_panel": True,
        "whitelist": True,
        "premium": False,
        "developer_mode": False,
        "plugin_manager": False,
        "theme_engine": True,
        "api": True
    }

    MAX_WARNINGS = 3
    DEFAULT_TIMEOUT_MINUTES = 10
    MAX_PURGE = 100

    SECURITY = {
        "anti_raid": True,
        "anti_bot": True,
        "verification": True,
        "join_lock": False,
        "anti_everyone": True,
        "anti_here": True,
        "anti_webhook": True,
        "anti_channel_delete": True,
        "anti_role_delete": True,
        "anti_server_destroy": True,
        "auto_backup": True
    }

    AUTOMOD = {
        "bad_words": True,
        "spam": True,
        "duplicate_messages": True,
        "invite_links": True,
        "scam_links": True,
        "mention_spam": True,
        "emoji_spam": True,
        "caps_spam": True,
        "mass_ping": True,
        "flood_detection": True,
        "auto_timeout": True,
        "auto_warn": True,
        "auto_delete": True,
        "spam_protection": True,
        "auto_kick": False,
        "auto_ban": False
    }

    TICKETS = {
        "enabled": True,
        "transcripts": True,
        "rating": True,
        "analytics": True,
        "claim": True,
        "close": True,
        "staff_notes": True,
        "support_roles": [],
        "categories": [],
        "open_tickets": [],
        "closed_tickets": []
    }

    LEVELS = {
        "enabled": True,
        "xp_min": 10,
        "xp_max": 25,
        "cooldown": 60,
        "daily_min": 100,
        "daily_max": 250,
        "coins": True,
        "economy": True,
        "inventory": True,
        "achievements": True,
        "leaderboard": True,
        "xp": True,
        "rank_cards": True,
        "shop": True,
        "daily_rewards": True
    }

    AI = {
        "enabled": True,
        "chat": True,
        "moderator": True,
        "translate": True,
        "summary": True,
        "faq": True,
        "assistant": True,
        "coding_helper": True,
        "anime_helper": True,
        "story_helper": True
    }

    MUSIC = {
        "enabled": True,
        "youtube": True,
        "local_files": True,
        "queue": True,
        "loop": True,
        "volume": True,
        "dashboard_control": True
    }

    REQUIRED_FOLDERS = [
        DATA_DIR,
        BACKUP_DIR,
        LOG_DIR,
        "templates",
        "static",
        "cogs"
    ]

    @classmethod
    def create_required_folders(cls):
        for folder in cls.REQUIRED_FOLDERS:
            os.makedirs(folder, exist_ok=True)

    @classmethod
    def validate(cls):
        if not cls.DISCORD_TOKEN:
            print("WARNING: DISCORD_TOKEN is missing.")
        if not cls.CLIENT_ID:
            print("WARNING: CLIENT_ID is missing.")
        if cls.OWNER_ID == 0:
            print("WARNING: OWNER_ID is missing.")
        cls.create_required_folders()

    @classmethod
    def info(cls):
        return {
            "bot": cls.BOT_NAME,
            "version": cls.VERSION,
            "dashboard": cls.DASHBOARD_ENABLED,
            "database": cls.DATABASE_TYPE,
            "theme": cls.THEME_DEFAULT
        }


Config.validate()