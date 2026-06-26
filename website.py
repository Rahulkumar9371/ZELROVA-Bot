import json
import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "CHANGE_THIS_SECRET_KEY")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BOT_CLIENT_ID = os.getenv("CLIENT_ID", "1518161863383187607")
DISCORD_SERVER_INVITE = os.getenv("DISCORD_SERVER_INVITE", "https://discord.gg/32urRvMMHf")

INVITE_URL = (
    f"https://discord.com/oauth2/authorize"
    f"?client_id={BOT_CLIENT_ID}"
    f"&permissions=8"
    f"&scope=bot%20applications.commands"
)

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
}

DEFAULT_DATA = {
    "server_config": {
        "server_name": "ZELROVA Community",
        "server_id": "",
        "prefix": "!",
        "language": "English",
        "theme": "dark-red-purple-blue",
        "bot_status": "Online",
        "maintenance_mode": False,
        "developer_mode": False,
        "premium": False,
        "modules": {
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
            "ai": True,
            "music": False,
            "community": True,
            "owner_panel": True,
            "whitelist": True,
            "servers": True
        }
    },
    "automod": {
        "bad_words": True,
        "spam_protection": True,
        "invite_links": True,
        "scam_links": True,
        "mention_spam": True,
        "emoji_spam": True,
        "caps_spam": True,
        "duplicate_messages": True,
        "mass_ping": True,
        "flood_detection": True,
        "auto_timeout": True,
        "auto_kick": False,
        "auto_ban": False
    },
    "announcements": {
        "enabled": True,
        "channel_id": "",
        "last_message": "",
        "scheduled": []
    },
    "levels": {
        "enabled": True,
        "xp": True,
        "leaderboard": True,
        "rank_cards": True,
        "coins": True,
        "economy": True,
        "achievements": True,
        "shop": True,
        "inventory": True,
        "daily_rewards": True
    },
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
    "tickets": {
        "enabled": True,
        "categories": [],
        "open_tickets": [],
        "closed_tickets": [],
        "transcripts": True,
        "rating": True,
        "analytics": True
    },
    "warnings": {
        "users": {}
    },
    "whitelist": {
        "enabled": True,
        "servers": [],
        "users": [],
        "owners": []
    },
    "bot_state": {
        "status": "Online",
        "latency": "42ms",
        "servers": 1,
        "users": 24800,
        "commands": 91000,
        "security_score": 98,
        "last_update": ""
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


def get_dashboard_data():
    config = load_json("server_config")
    bot_state = load_json("bot_state")

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
        "invite_url": INVITE_URL,
        "server_invite": DISCORD_SERVER_INVITE,
        "stats": {
            "servers": bot_state.get("servers", 1),
            "users": bot_state.get("users", 24800),
            "commands": bot_state.get("commands", 91000),
            "security_score": bot_state.get("security_score", 98),
            "latency": bot_state.get("latency", "42ms"),
            "database": "JSON Active",
            "hosting": "Render Working",
            "dashboard": "Routes Active"
        }
    }


@app.context_processor
def inject_global_links():
    return {
        "invite_url": INVITE_URL,
        "server_invite": DISCORD_SERVER_INVITE
    }


@app.route("/")
def home():
    return render_template("index.html")


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
    add_log("system_logs", "Dashboard module settings updated.")
    return jsonify({"success": True, "message": "Modules saved."})


@app.route("/api/save/automod", methods=["POST"])
def api_save_automod():
    data = request.get_json() or {}
    current = load_json("automod")
    current.update(data)
    save_json("automod", current)
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
    data = request.get_json() or {}
    action = data.get("action", "Unknown Action")

    config = load_json("server_config")

    if action == "Maintenance Mode":
        config["maintenance_mode"] = not config.get("maintenance_mode", False)
        save_json("server_config", config)

    if action == "Developer Mode":
        config["developer_mode"] = not config.get("developer_mode", False)
        save_json("server_config", config)

    add_log("system_logs", f"Owner action executed: {action}")

    return jsonify({
        "success": True,
        "message": f"Owner action executed: {action}"
    })


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
        "latency": state.get("latency", "42ms"),
        "website": "Running",
        "dashboard": "Active",
        "database": "JSON",
        "version": "1.0 Foundation",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


@app.errorhandler(404)
def page_not_found(error):
    return redirect(url_for("dashboard"))


ensure_json_files()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)