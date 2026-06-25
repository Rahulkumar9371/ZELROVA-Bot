"""
=========================================================
ZELROVA BOT
JSON Database Manager
Version 1.0 Foundation
=========================================================
"""

import json
import os
from copy import deepcopy

from config import Config


DEFAULT_DATABASE = {
    "bot": {
        "name": "ZELROVA",
        "version": "1.0 Foundation",
        "maintenance": False,
        "status": "online"
    },

    "dashboard": {
        "theme": "red"
    },

    "servers": {},

    "users": {},

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

            self.save(DEFAULT_DATABASE)

    # -----------------------------------

    def load(self):

        with open(self.path, "r", encoding="utf-8") as file:

            return json.load(file)

    # -----------------------------------

    def save(self, data):

        with open(self.path, "w", encoding="utf-8") as file:

            json.dump(
                data,
                file,
                indent=4
            )

    # -----------------------------------

    def reset(self):

        self.save(deepcopy(DEFAULT_DATABASE))

    # -----------------------------------

    def get_server(self, guild_id):

        data = self.load()

        guild_id = str(guild_id)

        if guild_id not in data["servers"]:

            data["servers"][guild_id] = {

                "prefix": "!",

                "language": "en",

                "theme": "red",

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

                    "music": False

                },

                "stats": {

                    "warnings": 0,

                    "bans": 0,

                    "tickets": 0,

                    "messages": 0,

                    "joins": 0

                }

            }

            self.save(data)

        return data["servers"][guild_id]

    # -----------------------------------

    def update_server(self, guild_id, server_data):

        data = self.load()

        data["servers"][str(guild_id)] = server_data

        self.save(data)

    # -----------------------------------

    def get_user(self, user_id):

        data = self.load()

        user_id = str(user_id)

        if user_id not in data["users"]:

            data["users"][user_id] = {

                "xp": 0,

                "level": 1,

                "coins": 0,

                "inventory": [],

                "achievements": []

            }

            self.save(data)

        return data["users"][user_id]

    # -----------------------------------

    def update_user(self, user_id, user_data):

        data = self.load()

        data["users"][str(user_id)] = user_data

        self.save(data)

    # -----------------------------------

    def increment_stat(self, guild_id, stat_name):

        server = self.get_server(guild_id)

        server["stats"][stat_name] += 1

        self.update_server(guild_id, server)

    # -----------------------------------

    def is_premium_server(self, guild_id):

        data = self.load()

        return str(guild_id) in data["premium"]["servers"]

    # -----------------------------------

    def add_premium_server(self, guild_id):

        data = self.load()

        guild_id = str(guild_id)

        if guild_id not in data["premium"]["servers"]:

            data["premium"]["servers"].append(guild_id)

            self.save(data)


db = Database()