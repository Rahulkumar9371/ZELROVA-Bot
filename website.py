import json
import os
from datetime import datetime
from urllib.parse import urlencode

import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

from config import Config
from database import db


app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DISCORD_API = "https://discord.com/api/v10"

BOT_CLIENT_ID = str(Config.CLIENT_ID)
CLIENT_SECRET = str(Config.CLIENT_SECRET)
OWNER_ID = str(Config.OWNER_ID).strip()
REDIRECT_URI = os.getenv("REDIRECT_URI", f"{Config.DASHBOARD_URL}/callback")


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_current_user():
    return session.get("discord_user")


def is_owner_logged_in():
    user = get_current_user()
    return bool(user and str(user.get("id")).strip() == OWNER_ID)


def owner_required_json():
    if not is_owner_logged_in():
        return jsonify({
            "success": False,
            "message": "Owner login required."
        }), 403
    return None


def add_system_log(message):
    data = db.load()
    data.setdefault("logs", {})
    data["logs"].setdefault("dashboard", {})
    data["logs"]["dashboard"].setdefault("system", [])
    data["logs"]["dashboard"]["system"].insert(0, {
        "message": message,
        "time": now()
    })
    data["logs"]["dashboard"]["system"] = data["logs"]["dashboard"]["system"][:100]
    db.save(data)


def dashboard_defaults():
    return {
        "server_name": "ZELROVA Community",
        "server_id": "",
        "prefix": Config.PREFIX,
        "language": "English",
        "theme": Config.THEME_DEFAULT,
        "bot_status": "Online",
        "maintenance_mode": False,
        "developer_mode": False,
        "premium": False,
        "modules": dict(Config.DEFAULT_MODULES)
    }


def get_dashboard_config():
    data = db.load()
    data.setdefault("dashboard", {})
    data["dashboard"].setdefault("server_config", dashboard_defaults())
    config = dashboard_defaults()
    config.update(data["dashboard"]["server_config"])
    config.setdefault("modules", {})
    config["modules"] = {**Config.DEFAULT_MODULES, **config.get("modules", {})}
    data["dashboard"]["server_config"] = config
    db.save(data)
    return config


def save_dashboard_config(config):
    data = db.load()
    data.setdefault("dashboard", {})
    data["dashboard"]["server_config"] = config
    db.save(data)


def get_server_list():
    data = db.load()
    servers = []

    for guild_id, server in data.get("servers", {}).items():
        if not server.get("bot_joined") or not server.get("online"):
            continue

        stats = server.get("stats", {})

        servers.append({
            "id": str(guild_id),
            "name": server.get("server_name", "Unknown Server"),
            "owner": server.get("owner_name") or server.get("owner_id", "Unknown"),
            "owner_id": server.get("owner_id", "Unknown"),
            "members": int(server.get("member_count", 0) or 0),
            "icon": server.get("icon_url") or "/static/logo.png",
            "joined_at": server.get("joined_at") or "Unknown",
            "commands": int(stats.get("commands", 0) or 0),
            "tickets": int(stats.get("tickets", 0) or 0),
            "warnings": int(stats.get("warnings", 0) or 0),
            "messages": int(stats.get("messages", 0) or 0),
            "trust_score": int(server.get("trust_score", 0) or 0),
            "activity_score": int(server.get("activity_score", 0) or 0),
            "online": True,
            "premium": str(guild_id) in data.get("premium", {}).get("servers", [])
        })

    servers.sort(key=lambda s: (s["trust_score"], s["members"], s["commands"]), reverse=True)
    return servers


def get_dashboard_data():
    data = db.load()
    server_list = get_server_list()
    bot_state = data.get("bot", {})
    music_state = data.get("music", {})

    total_users = sum(s["members"] for s in server_list)
    total_commands = sum(s["commands"] for s in server_list)

    return {
        "server_config": get_dashboard_config(),
        "automod": Config.AUTOMOD,
        "announcements": {"enabled": True, "channel_id": "", "last_message": "", "scheduled": []},
        "levels": Config.LEVELS,
        "logs": data.get("logs", {}),
        "reaction_roles": {"enabled": True, "roles": []},
        "tickets": Config.TICKETS,
        "warnings": data.get("warnings", {}),
        "whitelist": data.get("whitelist", {"enabled": True, "servers": [], "users": [], "owners": [OWNER_ID]}),
        "bot_state": bot_state,
        "server_list": server_list,
        "live_servers": {"servers": server_list, "last_sync": data.get("dashboard", {}).get("last_sync")},
        "music_state": music_state,
        "invite_url": Config.BOT_INVITE_URL,
        "server_invite": Config.DISCORD_SERVER_INVITE,
        "owner": get_current_user(),
        "is_owner": is_owner_logged_in(),
        "stats": {
            "servers": len(server_list),
            "users": total_users,
            "commands": total_commands,
            "security_score": int(bot_state.get("security_score", 0) or 0),
            "latency": bot_state.get("latency", "0ms"),
            "database": "Live Database",
            "hosting": "Railway Ready",
            "dashboard": "Active",
            "last_sync": data.get("dashboard", {}).get("last_sync") or "Never"
        }
    }


def queue_owner_action(action, payload=None):
    data = db.load()
    data.setdefault("owner_actions", {"pending": [], "completed": []})

    item = {
        "id": f"action_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "action": action,
        "payload": payload or {},
        "status": "pending",
        "created_at": now()
    }

    data["owner_actions"].setdefault("pending", [])
    data["owner_actions"].setdefault("completed", [])
    data["owner_actions"]["pending"].append(item)
    db.save(data)

    add_system_log(f"Owner action queued: {action}")
    return item


@app.context_processor
def inject_global_links():
    return {
        "invite_url": Config.BOT_INVITE_URL,
        "server_invite": Config.DISCORD_SERVER_INVITE,
        "current_user": get_current_user(),
        "is_owner": is_owner_logged_in()
    }


@app.route("/")
def home():
    return render_template("index.html", data=get_dashboard_data())


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
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10
    )

    if token_response.status_code != 200:
        return "Discord OAuth failed. Check CLIENT_ID, CLIENT_SECRET and REDIRECT_URI.", 400

    access_token = token_response.json().get("access_token")

    user_response = requests.get(
        f"{DISCORD_API}/users/@me",
        headers={"Authorization": f"Bearer {access_token}"},
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

    add_system_log(f"Dashboard login: {user.get('username')} ({user.get('id')})")
    return redirect(url_for("owner_panel"))


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


@app.route("/whitelist")
def whitelist():
    return render_template("whitelist.html", data=get_dashboard_data())


@app.route("/ai")
def ai():
    return render_template("ai.html", data=get_dashboard_data())


@app.route("/owner-panel")
def owner_panel():
    if not get_current_user():
        return redirect(url_for("login"))

    if not is_owner_logged_in():
        return render_template("dashboard.html", data=get_dashboard_data()), 403

    return render_template("ownerpanel.html", data=get_dashboard_data())


@app.route("/api/dashboard-data")
def api_dashboard_data():
    return jsonify(get_dashboard_data())


@app.route("/api/server-list")
def api_server_list():
    return jsonify({"success": True, "servers": get_server_list()})


@app.route("/api/bot/live-sync", methods=["POST"])
def api_bot_live_sync():
    payload = request.get_json() or {}
    servers = payload.get("servers", [])

    data = db.load()

    for server in servers:
        guild_id = str(server.get("id"))
        current = db.get_server(guild_id)

        current.update({
            "server_name": server.get("name", "Unknown Server"),
            "server_id": guild_id,
            "owner_id": str(server.get("owner_id", "")),
            "owner_name": server.get("owner_name", "Unknown Owner"),
            "member_count": int(server.get("members", 0) or 0),
            "icon_url": server.get("icon"),
            "joined_at": server.get("joined_at", "Unknown"),
            "bot_joined": True,
            "online": True,
            "trust_score": int(server.get("trust_score", 0) or 0),
            "activity_score": int(server.get("activity_score", 0) or 0)
        })

        current.setdefault("stats", {})
        current["stats"]["commands"] = int(server.get("commands", 0) or 0)
        current["stats"]["tickets"] = int(server.get("tickets", 0) or 0)
        current["stats"]["warnings"] = int(server.get("warnings", 0) or 0)
        current["stats"]["messages"] = int(server.get("messages", 0) or 0)

        db.update_server(guild_id, current)

    data = db.load()
    data.setdefault("bot", {})
    data["bot"].update({
        "status": "Online",
        "servers": len(servers),
        "users": int(payload.get("users", 0) or 0),
        "commands": int(payload.get("commands", 0) or 0),
        "latency": payload.get("latency", "0ms"),
        "security_score": int(payload.get("security_score", 0) or 0),
        "last_ready": now()
    })

    data.setdefault("dashboard", {})
    data["dashboard"]["last_sync"] = now()

    db.save(data)

    return jsonify({"success": True, "message": "Live sync updated.", "servers": len(servers)})


@app.route("/api/music/status")
def api_music_status():
    return jsonify({"success": True, "music": db.get_music_state()})


@app.route("/api/music/update", methods=["POST"])
def api_music_update():
    payload = request.get_json() or {}
    db.update_music_state(**payload)
    return jsonify({"success": True, "message": "Music state updated.", "music": db.get_music_state()})


@app.route("/api/music/control", methods=["POST"])
def api_music_control():
    denied = owner_required_json()
    if denied:
        return denied

    payload = request.get_json() or {}
    action = payload.get("action")
    data = payload.get("payload", {})

    allowed = {"pause", "resume", "skip", "stop", "volume", "loop", "shuffle"}

    if action not in allowed:
        return jsonify({"success": False, "message": "Invalid music action."}), 400

    queued = queue_owner_action(f"music_{action}", data)

    return jsonify({
        "success": True,
        "message": f"Music action queued: {action}",
        "action_id": queued["id"]
    })


@app.route("/api/save/server-config", methods=["POST"])
def api_save_server_config():
    config = get_dashboard_config()
    config.update(request.get_json() or {})
    save_dashboard_config(config)
    return jsonify({"success": True, "message": "Server config saved."})


@app.route("/api/save/modules", methods=["POST"])
def api_save_modules():
    config = get_dashboard_config()
    config.setdefault("modules", {})
    config["modules"].update(request.get_json() or {})
    save_dashboard_config(config)
    queue_owner_action("sync_modules", config["modules"])
    return jsonify({"success": True, "message": "Modules saved."})


@app.route("/api/save/automod", methods=["POST"])
def api_save_automod():
    queue_owner_action("sync_automod", request.get_json() or {})
    return jsonify({"success": True, "message": "AutoMod action queued."})


@app.route("/api/owner/action", methods=["POST"])
def api_owner_action():
    denied = owner_required_json()
    if denied:
        return denied

    payload = request.get_json() or {}
    queued = queue_owner_action(payload.get("action", "Unknown Action"), payload.get("payload", {}))

    return jsonify({
        "success": True,
        "message": f"Owner action queued: {queued['action']}",
        "action_id": queued["id"]
    })


@app.route("/api/owner/leave-server", methods=["POST"])
def api_owner_leave_server():
    denied = owner_required_json()
    if denied:
        return denied

    server_id = str((request.get_json() or {}).get("server_id", "")).strip()
    if not server_id:
        return jsonify({"success": False, "message": "Server ID required."}), 400

    queued = queue_owner_action("leave_server", {"server_id": server_id})
    return jsonify({"success": True, "message": f"Leave server queued: {server_id}", "action_id": queued["id"]})


@app.route("/api/owner/actions")
def api_owner_actions():
    data = db.load()
    data.setdefault("owner_actions", {"pending": [], "completed": []})
    db.save(data)
    return jsonify(data["owner_actions"])


@app.route("/api/owner/action-complete", methods=["POST"])
def api_owner_action_complete():
    payload = request.get_json() or {}
    action_id = payload.get("action_id")
    result = payload.get("result", "completed")

    data = db.load()
    data.setdefault("owner_actions", {"pending": [], "completed": []})

    pending = []
    completed_item = None

    for item in data["owner_actions"].get("pending", []):
        if item.get("id") == action_id:
            item["status"] = "completed"
            item["result"] = result
            item["completed_at"] = now()
            completed_item = item
        else:
            pending.append(item)

    data["owner_actions"]["pending"] = pending

    if completed_item:
        data["owner_actions"].setdefault("completed", [])
        data["owner_actions"]["completed"].insert(0, completed_item)
        data["owner_actions"]["completed"] = data["owner_actions"]["completed"][:100]

    db.save(data)
    return jsonify({"success": True})


@app.route("/api/logs/clear", methods=["POST"])
def api_clear_logs():
    data = db.load()
    data["logs"] = {}
    db.save(data)
    return jsonify({"success": True, "message": "Logs cleared."})


@app.route("/api/backup/create", methods=["POST"])
def api_create_backup():
    backup_dir = os.path.join(BASE_DIR, Config.BACKUP_DIR)
    os.makedirs(backup_dir, exist_ok=True)

    filename = f"zelrova_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path = os.path.join(backup_dir, filename)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(db.load(), file, indent=4, ensure_ascii=False)

    return jsonify({"success": True, "message": "Backup created.", "file": filename})


@app.route("/api/status")
def api_status():
    data = get_dashboard_data()
    return jsonify({
        "success": True,
        "bot": Config.BOT_NAME,
        "version": Config.VERSION,
        "status": data["bot_state"].get("status", "Offline"),
        "servers": data["stats"]["servers"],
        "users": data["stats"]["users"],
        "latency": data["stats"]["latency"],
        "dashboard": "Active",
        "time": now()
    })


@app.errorhandler(404)
def page_not_found(error):
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")