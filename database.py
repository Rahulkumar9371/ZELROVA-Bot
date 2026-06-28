import json
import os
from copy import deepcopy
from datetime import datetime

from config import Config


DEFAULT_SERVER = {
    "prefix": Config.PREFIX,
    "language": "en",
    "theme": Config.THEME_DEFAULT,
    "server_name": "Unknown Server",
    "server_id": "",
    "owner_id": "",
    "member_count": 0,
    "icon_url": None,
    "bot_joined": True,
    "online": True,
    "joined_at": None,
    "left_at": None,

    "modules": dict(Config.DEFAULT_MODULES),

    "channels": {
        "welcome": None,
        "leave": None,
        "logs": None,
        "tickets": None,
        "announcements": None,
        "music": None
    },

    "roles": {
        "autorole": None,
        "muted": None,
        "staff": None
    },

    "automod": dict(Config.AUTOMOD),
    "tickets": dict(Config.TICKETS),
    "levels": dict(Config.LEVELS),

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
    "last_daily": None,
    "created_at": None
}


DEFAULT_DATABASE = {
    "bot": {
        "name": Config.BOT_NAME,
        "version": Config.VERSION,
        "status": "offline",
        "maintenance": False,
        "developer_mode": False,
        "last_ready": None,
        "servers": 0,
        "users": 0,
        "latency": "0ms"
    },

    "dashboard": {
        "theme": Config.THEME_DEFAULT,
        "last_sync": None
    },

    "music": {
        "status": "idle",
        "current": None,
        "queue": [],
        "volume": 75,
        "loop": False,
        "updated_at": None
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

    def now(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            data = deepcopy(DEFAULT_DATABASE)
            self.save(data)
            return data

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
            data["servers"][guild_id]["server_id"] = guild_id
            data["servers"][guild_id]["created_at"] = self.now()
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

    def mark_server_live(self, guild):
        server = self.get_server(guild.id)

        server["server_name"] = guild.name
        server["server_id"] = str(guild.id)
        server["owner_id"] = str(guild.owner_id)
        server["member_count"] = guild.member_count or 0
        server["icon_url"] = guild.icon.url if guild.icon else None
        server["bot_joined"] = True
        server["online"] = True
        server["left_at"] = None

        if not server.get("joined_at"):
            server["joined_at"] = self.now()

        self.update_server(guild.id, server)

    def mark_server_removed(self, guild_id):
        server = self.get_server(guild_id)
        server["bot_joined"] = False
        server["online"] = False
        server["left_at"] = self.now()
        self.update_server(guild_id, server)

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
            data["users"][user_id]["created_at"] = self.now()
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
            "time": self.now()
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
            "created_at": self.now(),
            "closed_at": None
        }

        self.save(data)
        self.increment_stat(guild_id, "tickets")

    def close_ticket(self, guild_id, channel_id):
        data = self.load()
        ticket = data.get("tickets", {}).get(str(guild_id), {}).get(str(channel_id))

        if ticket:
            ticket["status"] = "closed"
            ticket["closed_at"] = self.now()
            self.save(data)

    def claim_ticket(self, guild_id, channel_id, staff_id):
        data = self.load()
        ticket = data.get("tickets", {}).get(str(guild_id), {}).get(str(channel_id))

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
            "time": self.now()
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
        data["bot"]["last_ready"] = self.now()
        self.save(data)

    def update_music_state(self, **kwargs):
        data = self.load()
        data.setdefault("music", deepcopy(DEFAULT_DATABASE["music"]))
        data["music"].update(kwargs)
        data["music"]["updated_at"] = self.now()
        self.save(data)

    def get_music_state(self):
        data = self.load()
        return data.get("music", deepcopy(DEFAULT_DATABASE["music"]))

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

    def live_servers(self):
        data = self.load()
        return {
            gid: server
            for gid, server in data.get("servers", {}).items()
            if server.get("bot_joined") and server.get("online")
        }


db = Database()