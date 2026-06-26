import json
import os
from copy import deepcopy
from datetime import datetime

from config import Config


DEFAULT_DATABASE = {
    "bot": {
        "name": "ZELROVA",
        "version": "1.0 Foundation",
        "status": "online",
        "maintenance": False,
        "developer_mode": False,
        "last_ready": None
    },

    "dashboard": {
        "theme": "dark-red-purple-blue",
        "last_sync": None
    },

    "servers": {},

    "users": {},

    "tickets": {},

    "warnings": {},

    "logs": {},

    "premium": {
        "servers": [],
        "users": []
    }
}


DEFAULT_SERVER = {
    "prefix": "!",
    "language": "en",
    "theme": "dark-red-purple-blue",

    "modules": {
        "moderation": True,
        "security": True,
        "automod": True,
        "welcome": True,
        "reaction_roles": True,
        "tickets": True,
        "levels": True,
        "logs": True,
        "analytics": True,
        "ai": True,
        "music": False,
        "backup": True,
        "owner_panel": True
    },

    "channels": {
        "welcome": None,
        "leave": None,
        "logs": None,
        "tickets": None,
        "announcements": None
    },

    "roles": {
        "autorole": None,
        "muted": None,
        "staff": None
    },

    "automod": {
        "bad_words": True,
        "spam_protection": True,
        "invite_links": True,
        "scam_links": True,
        "mention_spam": True,
        "caps_spam": True,
        "duplicate_messages": True
    },

    "tickets": {
        "enabled": True,
        "category_name": "Tickets",
        "transcripts": True,
        "rating": True
    },

    "levels": {
        "enabled": True,
        "xp_min": 10,
        "xp_max": 25,
        "cooldown": 60,
        "daily_min": 100,
        "daily_max": 250
    },

    "stats": {
        "warnings": 0,
        "bans": 0,
        "kicks": 0,
        "tickets": 0,
        "messages": 0,
        "joins": 0,
        "commands": 0
    }
}


DEFAULT_USER = {
    "xp": 0,
    "level": 1,
    "coins": 0,
    "inventory": [],
    "achievements": [],
    "last_daily": None
}


class Database:
    def __init__(self):
        self.path = Config.DATABASE_PATH

        folder = os.path.dirname(self.path)
        if folder:
            os.makedirs(folder, exist_ok=True)

        if not os.path.exists(self.path):
            self.save(deepcopy(DEFAULT_DATABASE))
        else:
            self.ensure_structure()

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            self.save(deepcopy(DEFAULT_DATABASE))
            return deepcopy(DEFAULT_DATABASE)

    def save(self, data):
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def deep_merge(self, default, current):
        if not isinstance(default, dict) or not isinstance(current, dict):
            return current

        merged = deepcopy(default)

        for key, value in current.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self.deep_merge(merged[key], value)
            else:
                merged[key] = value

        return merged

    def ensure_structure(self):
        data = self.load()
        fixed = self.deep_merge(DEFAULT_DATABASE, data)

        if fixed != data:
            self.save(fixed)

    def reset(self):
        self.save(deepcopy(DEFAULT_DATABASE))

    def get_server(self, guild_id):
        data = self.load()
        guild_id = str(guild_id)

        if guild_id not in data["servers"]:
            data["servers"][guild_id] = deepcopy(DEFAULT_SERVER)
            data["servers"][guild_id]["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save(data)
        else:
            fixed = self.deep_merge(DEFAULT_SERVER, data["servers"][guild_id])
            if fixed != data["servers"][guild_id]:
                data["servers"][guild_id] = fixed
                self.save(data)

        return data["servers"][guild_id]

    def update_server(self, guild_id, server_data):
        data = self.load()
        data["servers"][str(guild_id)] = server_data
        self.save(data)

    def get_module(self, guild_id, module_name):
        server = self.get_server(guild_id)
        return server.get("modules", {}).get(module_name, False)

    def set_module(self, guild_id, module_name, value):
        server = self.get_server(guild_id)
        server.setdefault("modules", {})
        server["modules"][module_name] = bool(value)
        self.update_server(guild_id, server)

    def get_user(self, user_id):
        data = self.load()
        user_id = str(user_id)

        if user_id not in data["users"]:
            data["users"][user_id] = deepcopy(DEFAULT_USER)
            data["users"][user_id]["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save(data)
        else:
            fixed = self.deep_merge(DEFAULT_USER, data["users"][user_id])
            if fixed != data["users"][user_id]:
                data["users"][user_id] = fixed
                self.save(data)

        return data["users"][user_id]

    def update_user(self, user_id, user_data):
        data = self.load()
        data["users"][str(user_id)] = user_data
        self.save(data)

    def get_guild_user(self, guild_id, user_id):
        return self.get_user(f"{guild_id}-{user_id}")

    def update_guild_user(self, guild_id, user_id, user_data):
        self.update_user(f"{guild_id}-{user_id}", user_data)

    def add_warning(self, guild_id, user_id, reason, moderator_id):
        data = self.load()
        guild_id = str(guild_id)
        user_id = str(user_id)

        data.setdefault("warnings", {})
        data["warnings"].setdefault(guild_id, {})
        data["warnings"][guild_id].setdefault(user_id, [])

        warning = {
            "reason": reason,
            "moderator_id": str(moderator_id),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        data["warnings"][guild_id][user_id].append(warning)
        self.save(data)
        self.increment_stat(guild_id, "warnings")

        return warning

    def get_warnings(self, guild_id, user_id):
        data = self.load()
        return data.get("warnings", {}).get(str(guild_id), {}).get(str(user_id), [])

    def clear_warnings(self, guild_id, user_id):
        data = self.load()
        guild_id = str(guild_id)
        user_id = str(user_id)

        if guild_id in data.get("warnings", {}) and user_id in data["warnings"][guild_id]:
            data["warnings"][guild_id][user_id] = []
            self.save(data)

    def create_ticket(self, guild_id, channel_id, user_id):
        data = self.load()
        guild_id = str(guild_id)
        channel_id = str(channel_id)

        data.setdefault("tickets", {})
        data["tickets"].setdefault(guild_id, {})

        data["tickets"][guild_id][channel_id] = {
            "user_id": str(user_id),
            "channel_id": channel_id,
            "status": "open",
            "claimed_by": None,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "closed_at": None
        }

        self.save(data)
        self.increment_stat(guild_id, "tickets")

    def close_ticket(self, guild_id, channel_id):
        data = self.load()
        guild_id = str(guild_id)
        channel_id = str(channel_id)

        ticket = data.get("tickets", {}).get(guild_id, {}).get(channel_id)

        if ticket:
            ticket["status"] = "closed"
            ticket["closed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save(data)

    def claim_ticket(self, guild_id, channel_id, staff_id):
        data = self.load()
        guild_id = str(guild_id)
        channel_id = str(channel_id)

        ticket = data.get("tickets", {}).get(guild_id, {}).get(channel_id)

        if ticket:
            ticket["claimed_by"] = str(staff_id)
            self.save(data)

    def add_log(self, guild_id, category, message):
        data = self.load()
        guild_id = str(guild_id)

        data.setdefault("logs", {})
        data["logs"].setdefault(guild_id, {})
        data["logs"][guild_id].setdefault(category, [])

        data["logs"][guild_id][category].insert(0, {
            "message": message,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        data["logs"][guild_id][category] = data["logs"][guild_id][category][:100]
        self.save(data)

    def increment_stat(self, guild_id, stat_name, amount=1):
        server = self.get_server(guild_id)

        server.setdefault("stats", {})
        server["stats"].setdefault(stat_name, 0)
        server["stats"][stat_name] += amount

        self.update_server(guild_id, server)

    def update_bot_state(self, **kwargs):
        data = self.load()
        data.setdefault("bot", {})
        data["bot"].update(kwargs)
        data["bot"]["last_ready"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save(data)

    def is_premium_server(self, guild_id):
        data = self.load()
        return str(guild_id) in data.get("premium", {}).get("servers", [])

    def add_premium_server(self, guild_id):
        data = self.load()
        guild_id = str(guild_id)

        data.setdefault("premium", {})
        data["premium"].setdefault("servers", [])

        if guild_id not in data["premium"]["servers"]:
            data["premium"]["servers"].append(guild_id)
            self.save(data)


db = Database()