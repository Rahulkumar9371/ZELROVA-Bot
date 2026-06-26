import json
import os
from datetime import datetime
from urllib.parse import urlencode

import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

from config import Config


app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BOT_CLIENT_ID = Config.CLIENT_ID
CLIENT_SECRET = Config.CLIENT_SECRET
OWNER_ID = str(Config.OWNER_ID)
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://127.0.0.1:5000/callback")
DISCORD_SERVER_INVITE = Config.DISCORD_SERVER_INVITE
BOT_INVITE_URL = Config.BOT_INVITE_URL

DISCORD_API = "https://discord.com/api/v10"

JSON_FILES = {
    "server_config": "server_config.json",
    "automod": "automod.json",
    "announcements": "announcements.json",
    "levels": "levels.json",
    "logs": "logs.json",
    "reaction_roles": "reaction_roles.json",
    "tickets": "tickets.json",
    "warnings": "warnings.json",
    "whitelist": "whitelist.json",
    "bot_state": "bot_state.json",
    "owner_actions": "owner_actions.json"
}

DEFAULT_DATA = {
    "server_config": {
        "server_name": "ZELROVA Community",
        "server_id": os.getenv("ZELROVA_SERVER_ID", ""),
        "prefix": "!",
        "language": "English",
        "theme": "dark-red-purple-blue",
        "bot_status": "Online",
        "maintenance_mode": False,
        "developer_mode": False,
        "premium": False,
        "modules": dict(Config.DEFAULT_MODULES)
    },

    "automod": dict(Config.AUTOMOD),

    "announcements": {
        "enabled": True,
        "channel_id": "",
        "last_message": "",
        "scheduled": []
    },

    "levels": dict(Config.LEVELS),

    "logs": {
        "enabled": True,
        "moderation_logs": [],
        "security_logs": [],
        "ticket_logs": [],
        "system_logs": []
    },

    "reaction_roles": {
        "enabled": True,
        "roles": []
    },

    "tickets": dict(Config.TICKETS),

    "warnings": {
        "users": {}
    },

    "whitelist": {
        "enabled": True,
        "servers": [],
        "users": [],
        "owners": [OWNER_ID]
    },

    "bot_state": {
        "status": "Online",
        "latency": "0ms",
        "servers": 0,
        "users": 0,
        "commands": 0,
        "security_score": 0,
        "last_update": ""
    },

    "owner_actions": {
        "pending": [],
        "completed": []
    }
}


def path_for(key):
    return os.path.join(BASE_DIR, JSON_FILES[key])


def save_json(key, data):
    with open(path_for(key), "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def deep_merge(default, current):
    if not isinstance(default, dict) or not isinstance(current, dict):
        return current

    merged = default.copy()

    for key, value in current.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value

    return merged


def load_json(key):
    if not os.path.exists(path_for(key)):
        save_json(key, DEFAULT_DATA[key])
        return DEFAULT_DATA[key]

    try:
        with open(path_for(key), "r", encoding="utf-8") as file:
            current = json.load(file)

        fixed = deep_merge(DEFAULT_DATA[key], current)

        if fixed != current:
            save_json(key, fixed)

        return fixed

    except Exception:
        save_json(key, DEFAULT_DATA[key])
        return DEFAULT_DATA[key]


def ensure_json_files():
    for key in JSON_FILES:
        load_json(key)


def add_log(category, message):
    logs = load_json("logs")

    if category not in logs:
        logs[category] = []

    logs[category].insert(0, {
        "message": message,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    logs[category] = logs[category][:100]
    save_json("logs", logs)


def load_database():
    database_path = Config.DATABASE_PATH

    if not os.path.exists(database_path):
        return {}

    try:
        with open(database_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}


def calculate_trust_score(server):
    stats = server.get("stats", {})
    members = int(server.get("member_count", 0) or 0)
    commands = int(stats.get("commands", 0) or 0)
    tickets = int(stats.get("tickets", 0) or 0)
    warnings = int(stats.get("warnings", 0) or 0)

    score = 50
    score += min(20, members // 100)
    score += min(15, commands // 50)
    score += min(10, tickets * 2)
    score -= min(20, warnings)

    return max(0, min(100, score))


def calculate_activity_score(server):
    stats = server.get("stats", {})
    messages = int(stats.get("messages", 0) or 0)
    commands = int(stats.get("commands", 0) or 0)
    tickets = int(stats.get("tickets", 0) or 0)

    score = 30
    score += min(30, messages // 100)
    score += min(25, commands // 30)
    score += min(15, tickets * 2)

    return max(0, min(100, score))


def get_server_list():
    database = load_database()
    servers = database.get("servers", {})
    premium_servers = database.get("premium", {}).get("servers", [])

    result = []

    for guild_id, server in servers.items():
        if server.get("bot_joined") is False:
            continue

        result.append({
            "id": guild_id,
            "name": server.get("server_name", "Unknown Server"),
            "owner": server.get("owner_id", "Unknown"),
            "members": server.get("member_count", 0),
            "icon": server.get("icon_url") or "/static/logo.png",
            "join_date": server.get("created_at", "Unknown"),
            "commands": server.get("stats", {}).get("commands", 0),
            "tickets": server.get("stats", {}).get("tickets", 0),
            "warnings": server.get("stats", {}).get("warnings", 0),
            "trust_score": calculate_trust_score(server),
            "activity_score": calculate_activity_score(server),
            "online": True,
            "premium": str(guild_id) in premium_servers
        })

    result.sort(key=lambda item: (item["trust_score"], item["members"]), reverse=True)

    return result


def get_dashboard_data():
    config = load_json("server_config")
    bot_state = load_json("bot_state")
    server_list = get_server_list()

    return {
        "server_config": config,
        "automod": load_json("automod"),
        "announcements": load_json("announcements"),
        "levels": load_json("levels"),
        "logs": load_json("logs"),
        "reaction_roles": load_json("reaction_roles"),
        "tickets": load_json("tickets"),
        "warnings": load_json("warnings"),
        "whitelist": load_json("whitelist"),
        "bot_state": bot_state,
        "server_list": server_list,
        "invite_url": BOT_INVITE_URL,
        "server_invite": DISCORD_SERVER_INVITE,
        "owner": get_current_user(),
        "is_owner": is_owner_logged_in(),
        "stats": {
            "servers": bot_state.get("servers", len(server_list)),
            "users": bot_state.get("users", sum(int(s["members"] or 0) for s in server_list)),
            "commands": bot_state.get("commands", sum(int(s["commands"] or 0) for s in server_list)),
            "security_score": bot_state.get("security_score", 98),
            "latency": bot_state.get("latency", "0ms"),
            "database": "JSON Active",
            "hosting": "Render Working",
            "dashboard": "Routes Active"
        }
    }


def get_current_user():
    return session.get("discord_user")


def is_owner_logged_in():
    user = get_current_user()

    if not user:
        return False

    return str(user.get("id")) == OWNER_ID


def owner_required_json():
    if not is_owner_logged_in():
        return jsonify({
            "success": False,
            "message": "Sorry, you are not allowed to enter here. Only the real owner can use this."
        }), 403

    return None


def queue_owner_action(action, payload=None):
    actions = load_json("owner_actions")

    item = {
        "id": f"action_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "action": action,
        "payload": payload or {},
        "status": "pending",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    actions["pending"].append(item)
    save_json("owner_actions", actions)

    add_log("system_logs", f"Owner action queued: {action}")

    return item


@app.context_processor
def inject_global_links():
    return {
        "invite_url": BOT_INVITE_URL,
        "server_invite": DISCORD_SERVER_INVITE,
        "current_user": get_current_user(),
        "is_owner": is_owner_logged_in()
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login")
def login():
    params = {
        "client_id": BOT_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "identify"
    }

    return redirect(f"https://discord.com/oauth2/authorize?{urlencode(params)}")


@app.route("/callback")
def callback():
    code = request.args.get("code")

    if not code:
        return redirect(url_for("dashboard"))

    token_response = requests.post(
        f"{DISCORD_API}/oauth2/token",
        data={
            "client_id": BOT_CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        },
        timeout=10
    )

    if token_response.status_code != 200:
        return "Discord OAuth failed. Check CLIENT_ID, CLIENT_SECRET and REDIRECT_URI.", 400

    token_data = token_response.json()
    access_token = token_data.get("access_token")

    user_response = requests.get(
        f"{DISCORD_API}/users/@me",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        timeout=10
    )

    if user_response.status_code != 200:
        return "Failed to read Discord user.", 400

    user = user_response.json()

    session["discord_user"] = {
        "id": user.get("id"),
        "username": user.get("username"),
        "global_name": user.get("global_name"),
        "avatar": user.get("avatar")
    }

    add_log("system_logs", f"Dashboard login: {user.get('username')} ({user.get('id')})")

    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", data=get_dashboard_data())


@app.route("/servers")
def servers():
    return render_template("servers.html", data=get_dashboard_data())


@app.route("/moderation")
def moderation():
    return render_template("moderation.html", data=get_dashboard_data())


@app.route("/security")
def security():
    return render_template("security.html", data=get_dashboard_data())


@app.route("/automod")
def automod():
    return render_template("automod.html", data=get_dashboard_data())


@app.route("/welcome")
def welcome():
    return render_template("welcome.html", data=get_dashboard_data())


@app.route("/reaction-roles")
def reaction_roles():
    return render_template("reaction_roles.html", data=get_dashboard_data())


@app.route("/tickets")
def tickets():
    return render_template("tickets.html", data=get_dashboard_data())


@app.route("/levels")
def levels():
    return render_template("levels.html", data=get_dashboard_data())


@app.route("/logs")
def logs():
    return render_template("logs.html", data=get_dashboard_data())


@app.route("/announcements")
def announcements():
    return render_template("announcements.html", data=get_dashboard_data())


@app.route("/analytics")
def analytics():
    return render_template("analytics.html", data=get_dashboard_data())


@app.route("/backups")
def backups():
    return render_template("backups.html", data=get_dashboard_data())


@app.route("/owner-panel")
def owner_panel():
    if not get_current_user():
        return """
        <html>
        <head>
        <title>ZELROVA Owner Lock</title>
        <link rel="stylesheet" href="/static/style.css">
        </head>
        <body class="zelrova-dashboard">
        <main class="main-panel" style="margin-left:0;width:100%;min-height:100vh;display:flex;align-items:center;justify-content:center;">
          <section class="glass-card" style="max-width:650px;text-align:center;">
            <span class="tag">PRIVATE OWNER PANEL</span>
            <h1 style="color:white;font-size:38px;margin:15px 0;">Owner Lock</h1>
            <p style="line-height:1.8;color:#cfcfe0;">Login with Discord to verify owner access.</p>
            <br>
            <a class="main-btn" href="/login">Login with Discord</a>
          </section>
        </main>
        </body>
        </html>
        """

    if not is_owner_logged_in():
        user = get_current_user()
        return f"""
        <html>
        <head>
        <title>Access Denied</title>
        <link rel="stylesheet" href="/static/style.css">
        </head>
        <body class="zelrova-dashboard">
        <main class="main-panel" style="margin-left:0;width:100%;min-height:100vh;display:flex;align-items:center;justify-content:center;">
          <section class="glass-card" style="max-width:720px;text-align:center;">
            <span class="tag">ACCESS DENIED</span>
            <h1 style="color:white;font-size:38px;margin:15px 0;">Sorry, you are not allowed to enter here.</h1>
            <p style="line-height:1.8;color:#cfcfe0;">
              Only the real ZELROVA owner can use this panel.<br>
              Logged in user: {user.get("username")}<br>
              Your Discord ID: {user.get("id")}
            </p>
            <br>
            <a class="ghost-btn" href="/logout">Logout</a>
            <a class="main-btn" href="/dashboard">Back Dashboard</a>
          </section>
        </main>
        </body>
        </html>
        """, 403

    return render_template("ownerpanel.html", data=get_dashboard_data())


@app.route("/whitelist")
def whitelist():
    return render_template("whitelist.html", data=get_dashboard_data())


@app.route("/ai")
def ai():
    return render_template("ai.html", data=get_dashboard_data())


@app.route("/api/dashboard-data")
def api_dashboard_data():
    return jsonify(get_dashboard_data())


@app.route("/api/server-list")
def api_server_list():
    return jsonify({
        "success": True,
        "servers": get_server_list()
    })


@app.route("/api/save/server-config", methods=["POST"])
def api_save_server_config():
    data = request.get_json() or {}
    current = load_json("server_config")
    current.update(data)
    save_json("server_config", current)
    add_log("system_logs", "Server configuration updated.")
    return jsonify({"success": True, "message": "Server settings saved."})


@app.route("/api/save/modules", methods=["POST"])
def api_save_modules():
    data = request.get_json() or {}
    config = load_json("server_config")
    config.setdefault("modules", {})
    config["modules"].update(data)
    save_json("server_config", config)
    queue_owner_action("sync_modules", data)
    add_log("system_logs", "Dashboard module settings updated.")
    return jsonify({"success": True, "message": "Modules saved."})


@app.route("/api/save/automod", methods=["POST"])
def api_save_automod():
    data = request.get_json() or {}
    current = load_json("automod")
    current.update(data)
    save_json("automod", current)
    queue_owner_action("sync_automod", data)
    add_log("moderation_logs", "AutoMod settings updated.")
    return jsonify({"success": True, "message": "AutoMod saved."})


@app.route("/api/save/levels", methods=["POST"])
def api_save_levels():
    data = request.get_json() or {}
    current = load_json("levels")
    current.update(data)
    save_json("levels", current)
    add_log("system_logs", "Level settings updated.")
    return jsonify({"success": True, "message": "Levels saved."})


@app.route("/api/save/tickets", methods=["POST"])
def api_save_tickets():
    data = request.get_json() or {}
    current = load_json("tickets")
    current.update(data)
    save_json("tickets", current)
    add_log("ticket_logs", "Ticket settings updated.")
    return jsonify({"success": True, "message": "Tickets saved."})


@app.route("/api/save/reaction-roles", methods=["POST"])
def api_save_reaction_roles():
    data = request.get_json() or {}
    current = load_json("reaction_roles")
    current.update(data)
    save_json("reaction_roles", current)
    add_log("system_logs", "Reaction roles settings updated.")
    return jsonify({"success": True, "message": "Reaction roles saved."})


@app.route("/api/save/announcements", methods=["POST"])
def api_save_announcements():
    data = request.get_json() or {}
    current = load_json("announcements")
    current.update(data)
    save_json("announcements", current)
    add_log("system_logs", "Announcement settings updated.")
    return jsonify({"success": True, "message": "Announcements saved."})


@app.route("/api/save/whitelist", methods=["POST"])
def api_save_whitelist():
    data = request.get_json() or {}
    current = load_json("whitelist")
    current.update(data)
    save_json("whitelist", current)
    add_log("security_logs", "Whitelist settings updated.")
    return jsonify({"success": True, "message": "Whitelist saved."})


@app.route("/api/bot-state/update", methods=["POST"])
def api_bot_state_update():
    data = request.get_json() or {}
    state = load_json("bot_state")
    state.update(data)
    state["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_json("bot_state", state)
    return jsonify({"success": True, "message": "Bot state updated."})


@app.route("/api/owner/action", methods=["POST"])
def api_owner_action():
    denied = owner_required_json()
    if denied:
        return denied

    data = request.get_json() or {}
    action = data.get("action", "Unknown Action")
    payload = data.get("payload", {})

    queued = queue_owner_action(action, payload)

    return jsonify({
        "success": True,
        "message": f"Owner action queued: {action}",
        "action_id": queued["id"]
    })


@app.route("/api/owner/leave-server", methods=["POST"])
def api_owner_leave_server():
    denied = owner_required_json()
    if denied:
        return denied

    data = request.get_json() or {}
    server_id = str(data.get("server_id", "")).strip()

    if not server_id:
        return jsonify({"success": False, "message": "Server ID required."}), 400

    queued = queue_owner_action("leave_server", {
        "server_id": server_id
    })

    return jsonify({
        "success": True,
        "message": f"Leave server action queued for {server_id}.",
        "action_id": queued["id"]
    })


@app.route("/api/owner/actions")
def api_owner_actions():
    actions = load_json("owner_actions")
    return jsonify(actions)


@app.route("/api/owner/action-complete", methods=["POST"])
def api_owner_action_complete():
    data = request.get_json() or {}
    action_id = data.get("action_id")
    result = data.get("result", "completed")

    actions = load_json("owner_actions")

    pending = []
    completed_item = None

    for item in actions.get("pending", []):
        if item.get("id") == action_id:
            item["status"] = "completed"
            item["result"] = result
            item["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            completed_item = item
        else:
            pending.append(item)

    actions["pending"] = pending

    if completed_item:
        actions.setdefault("completed", [])
        actions["completed"].insert(0, completed_item)
        actions["completed"] = actions["completed"][:100]

    save_json("owner_actions", actions)

    return jsonify({"success": True})


@app.route("/api/logs/clear", methods=["POST"])
def api_clear_logs():
    logs = load_json("logs")

    for key in logs:
        if isinstance(logs[key], list):
            logs[key] = []

    save_json("logs", logs)
    return jsonify({"success": True, "message": "Logs cleared."})


@app.route("/api/backup/create", methods=["POST"])
def api_create_backup():
    backup = get_dashboard_data()

    backup_dir = os.path.join(BASE_DIR, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    filename = f"zelrova_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path = os.path.join(backup_dir, filename)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(backup, file, indent=4, ensure_ascii=False)

    add_log("system_logs", f"Backup created: {filename}")

    return jsonify({
        "success": True,
        "message": "Backup created successfully.",
        "file": filename
    })


@app.route("/api/status")
def api_status():
    state = load_json("bot_state")

    return jsonify({
        "success": True,
        "bot": "ZELROVA",
        "status": state.get("status", "Online"),
        "latency": state.get("latency", "0ms"),
        "website": "Running",
        "dashboard": "Active",
        "database": "JSON",
        "version": Config.VERSION,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


@app.errorhandler(404)
def page_not_found(error):
    return redirect(url_for("dashboard"))


ensure_json_files()

if __name__ == "__main__":
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=True
    )