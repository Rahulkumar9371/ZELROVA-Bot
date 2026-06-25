from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
from datetime import datetime

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
            "ai": True,
            "backup": True,
            "owner_panel": True
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
    }
}


def ensure_json_files():
    for key, filename in JSON_FILES.items():
        path = os.path.join(BASE_DIR, filename)
        if not os.path.exists(path):
            save_json(key, DEFAULT_DATA[key])


def load_json(key):
    path = os.path.join(BASE_DIR, JSON_FILES[key])

    if not os.path.exists(path):
        save_json(key, DEFAULT_DATA[key])
        return DEFAULT_DATA[key]

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not data:
            return DEFAULT_DATA[key]

        return data

    except Exception:
        save_json(key, DEFAULT_DATA[key])
        return DEFAULT_DATA[key]


def save_json(key, data):
    path = os.path.join(BASE_DIR, JSON_FILES[key])

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def add_log(category, message):
    logs = load_json("logs")

    log_item = {
        "message": message,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    if category not in logs:
        logs[category] = []

    logs[category].insert(0, log_item)
    logs[category] = logs[category][:50]

    save_json("logs", logs)


def get_dashboard_data():
    return {
        "server_config": load_json("server_config"),
        "automod": load_json("automod"),
        "announcements": load_json("announcements"),
        "levels": load_json("levels"),
        "logs": load_json("logs"),
        "reaction_roles": load_json("reaction_roles"),
        "tickets": load_json("tickets"),
        "warnings": load_json("warnings"),
        "whitelist": load_json("whitelist"),
        "stats": {
            "servers": 1,
            "users": 24800,
            "commands": 91000,
            "security_score": 98,
            "latency": "42ms",
            "database": "JSON Active",
            "hosting": "Render Working",
            "dashboard": "Routes Active"
        }
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
    data = request.get_json()
    current = load_json("server_config")
    current.update(data)
    save_json("server_config", current)
    add_log("system_logs", "Server configuration updated from dashboard.")
    return jsonify({"success": True, "message": "Server settings saved."})


@app.route("/api/save/modules", methods=["POST"])
def api_save_modules():
    data = request.get_json()
    config = load_json("server_config")

    if "modules" not in config:
        config["modules"] = {}

    config["modules"].update(data)
    save_json("server_config", config)
    add_log("system_logs", "Module settings updated.")
    return jsonify({"success": True, "message": "Modules updated."})


@app.route("/api/save/automod", methods=["POST"])
def api_save_automod():
    data = request.get_json()
    automod_data = load_json("automod")
    automod_data.update(data)
    save_json("automod", automod_data)
    add_log("moderation_logs", "AutoMod settings updated.")
    return jsonify({"success": True, "message": "AutoMod settings saved."})


@app.route("/api/save/levels", methods=["POST"])
def api_save_levels():
    data = request.get_json()
    levels_data = load_json("levels")
    levels_data.update(data)
    save_json("levels", levels_data)
    add_log("system_logs", "Level system settings updated.")
    return jsonify({"success": True, "message": "Level settings saved."})


@app.route("/api/save/tickets", methods=["POST"])
def api_save_tickets():
    data = request.get_json()
    tickets_data = load_json("tickets")
    tickets_data.update(data)
    save_json("tickets", tickets_data)
    add_log("ticket_logs", "Ticket system settings updated.")
    return jsonify({"success": True, "message": "Ticket settings saved."})


@app.route("/api/save/reaction-roles", methods=["POST"])
def api_save_reaction_roles():
    data = request.get_json()
    reaction_data = load_json("reaction_roles")
    reaction_data.update(data)
    save_json("reaction_roles", reaction_data)
    add_log("system_logs", "Reaction roles settings updated.")
    return jsonify({"success": True, "message": "Reaction roles saved."})


@app.route("/api/save/announcements", methods=["POST"])
def api_save_announcements():
    data = request.get_json()
    announcement_data = load_json("announcements")
    announcement_data.update(data)
    save_json("announcements", announcement_data)
    add_log("system_logs", "Announcement settings updated.")
    return jsonify({"success": True, "message": "Announcement settings saved."})


@app.route("/api/save/whitelist", methods=["POST"])
def api_save_whitelist():
    data = request.get_json()
    whitelist_data = load_json("whitelist")
    whitelist_data.update(data)
    save_json("whitelist", whitelist_data)
    add_log("security_logs", "Whitelist settings updated.")
    return jsonify({"success": True, "message": "Whitelist saved."})


@app.route("/api/owner/action", methods=["POST"])
def api_owner_action():
    data = request.get_json()
    action = data.get("action", "Unknown Action")

    add_log("system_logs", f"Owner action executed: {action}")

    return jsonify({
        "success": True,
        "message": f"Owner action executed: {action}"
    })


@app.route("/api/logs/clear", methods=["POST"])
def api_clear_logs():
    logs_data = load_json("logs")

    for key in logs_data:
        if isinstance(logs_data[key], list):
            logs_data[key] = []

    save_json("logs", logs_data)
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
    return jsonify({
        "success": True,
        "bot": "ZELROVA",
        "status": "Online",
        "website": "Running",
        "dashboard": "Active",
        "database": "JSON",
        "version": "1.0 Foundation",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


@app.errorhandler(404)
def page_not_found(error):
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    ensure_json_files()
    app.run(host="0.0.0.0", port=5000, debug=True)