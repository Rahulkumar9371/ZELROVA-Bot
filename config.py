import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ==================================================
    # ZELROVA BOT CORE
    # ==================================================

    BOT_NAME = "ZELROVA"
    VERSION = "1.0 Final Foundation"
    MISSION = "One Bot. Everything You Need."

    PREFIX = os.getenv("BOT_PREFIX", "!")
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))

    APPLICATION_ID = os.getenv("APPLICATION_ID", "")
    CLIENT_ID = os.getenv("CLIENT_ID", APPLICATION_ID)
    CLIENT_SECRET = os.getenv("CLIENT_SECRET", "")
    PUBLIC_KEY = os.getenv("PUBLIC_KEY", "")

    # ==================================================
    # WEBSITE / DASHBOARD
    # ==================================================

    SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_THIS_SECRET_KEY")
    DASHBOARD_ENABLED = os.getenv("DASHBOARD_ENABLED", "true").lower() == "true"

    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5000"))

    DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://127.0.0.1:5000")

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

    # ==================================================
    # DATABASE
    # ==================================================

    DATABASE_TYPE = os.getenv("DATABASE_TYPE", "json")
    DATABASE_PATH = os.getenv("DATABASE_PATH", "data/database.json")

    DATA_DIR = os.getenv("DATA_DIR", "data")
    BACKUP_DIR = os.getenv("BACKUP_DIR", "backups")
    LOG_DIR = os.getenv("LOG_DIR", "logs")

    # ==================================================
    # BRANDING
    # ==================================================

    THEME_DEFAULT = "dark-red-purple-blue"

    THEME_COLORS = {
        "dark-red-purple-blue": {
            "background": "#050507",
            "red": "#ff2d55",
            "purple": "#8a3ffc",
            "blue": "#2d7dff"
        },
        "dark-red": {
            "background": "#080305",
            "red": "#ff2d55",
            "purple": "#8a3ffc",
            "blue": "#2d7dff"
        },
        "anime": {
            "background": "#09020f",
            "red": "#ff4fd8",
            "purple": "#9b5cff",
            "blue": "#44a3ff"
        },
        "cyber": {
            "background": "#020807",
            "red": "#ff2d55",
            "purple": "#8a3ffc",
            "blue": "#00ffc8"
        }
    }

    # ==================================================
    # DEFAULT MODULES
    # ==================================================

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
        "music": False,
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
        # ==================================================
    # MODERATION
    # ==================================================

    MAX_WARNINGS = 3
    DEFAULT_TIMEOUT_MINUTES = 10
    MAX_PURGE = 100

    # ==================================================
    # SECURITY
    # ==================================================

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

    # ==================================================
    # AUTOMOD
    # ==================================================

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
        "auto_delete": True
    }

    # ==================================================
    # COMMUNITY
    # ==================================================

    COMMUNITY = {
        "welcome_card": True,
        "leave_card": True,
        "auto_role": True,
        "reaction_roles": True,
        "boost_message": True,
        "rules_panel": True,
        "member_counter": True,
        "birthdays": True,
        "community_stats": True,
        "custom_onboarding": True
    }

    # ==================================================
    # TICKETS
    # ==================================================

    TICKETS = {
        "enabled": True,
        "transcripts": True,
        "rating": True,
        "analytics": True,
        "claim": True,
        "close": True,
        "staff_notes": True,
        "support_roles": []
    }

    # ==================================================
    # LEVELS
    # ==================================================

    LEVELS = {
        "enabled": True,
        "xp_min": 10,
        "xp_max": 25,
        "daily_min": 100,
        "daily_max": 250,
        "coins": True,
        "economy": True,
        "inventory": True,
        "achievements": True,
        "leaderboard": True
    }

    # ==================================================
    # AI
    # ==================================================

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
        "story_helper": True,
        "image_prompt_generator": True
    }

    # ==================================================
    # MUSIC
    # ==================================================

    MUSIC = {
        "enabled": True,
        "youtube": False,
        "spotify": False,
        "radio": True,
        "queue": True,
        "loop": True,
        "volume": True
    }

    # ==================================================
    # OWNER PANEL
    # ==================================================

    OWNER_PANEL = {
        "live_console": True,
        "broadcast": True,
        "remote_commands": True,
        "global_ban": True,
        "premium_manager": True,
        "bot_status": True,
        "server_control": True,
        "user_control": True
    }

    # ==================================================
    # LIVE SERVER RANKING
    # ==================================================

    RANKING = {
        "enabled": True,
        "top_servers": 100,
        "calculate_trust_score": True,
        "live_member_count": True,
        "live_command_count": True,
        "live_ticket_count": True
    }

    # ==================================================
    # ANALYTICS
    # ==================================================

    ANALYTICS = {
        "dashboard": True,
        "graphs": True,
        "heatmap": True,
        "logs_viewer": True,
        "server_health": True,
        "live_statistics": True
    }
        # ==================================================
    # PREMIUM FEATURES
    # ==================================================

    PREMIUM = {
        "theme_engine": True,
        "cloud_backup": True,
        "multi_server": True,
        "plugin_marketplace": True,
        "voice_ai": False,
        "custom_ai": False,
        "mobile_dashboard": True,
        "pwa": False
    }

    # ==================================================
    # WEBSITE PAGES
    # ==================================================

    WEBSITE_PAGES = [
        "home",
        "overview",
        "features",
        "dashboard",
        "servers",
        "moderation",
        "security",
        "tickets",
        "levels",
        "analytics",
        "logs",
        "reaction_roles",
        "welcome",
        "backups",
        "owner_panel",
        "community",
        "anime",
        "gaming",
        "coding",
        "developer",
        "english",
        "japanese",
        "music",
        "fun",
        "manga",
        "story",
        "events",
        "announcements",
        "support"
    ]

    # ==================================================
    # FOLDERS
    # ==================================================

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


# ==================================================
# INITIALIZE CONFIG
# ==================================================

Config.validate()