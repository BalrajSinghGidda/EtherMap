#!/usr/bin/env python3
# events-server.py
# Full-featured Flask server for EtherMap visualization project
# - Cookie-based auth (SQLite)
# - Devices registration & listing
# - File uploads/downloads + temp links
# - SSE (/events) open to anonymous reporters
# - /log_event accepts anonymous events (for netcat/raw clients)
# - Web UI routes (/ , /upload, /files, /viewer.html) require login and redirect to /login

import json
import os
import secrets
import sqlite3
import threading
import time
from datetime import datetime, timezone

from flask import (
    Flask,
    Response,
    abort,
    g,
    jsonify,
    redirect,
    request,
    send_from_directory,
    session,
    stream_with_context,
)
from werkzeug.security import check_password_hash, generate_password_hash

# ---------- Config ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) or "."
EVENTS_FILE = os.path.join(BASE_DIR, "events.log")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
STATE_FILE = os.path.join(BASE_DIR, "state.json")
DB_PATH = os.path.join(BASE_DIR, "auth.db")
TEMP_TOKENS = {}  # token -> (name, expires_ts)

# Server settings
HOST = "0.0.0.0"
PORT = 5000
SESSION_SECRET = os.environ.get("FLASK_SECRET") or "dev-secret-change-me"

app = Flask(__name__, static_folder=".")
app.secret_key = SESSION_SECRET
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 24 * 7  # 7 days

# ensure upload dir exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------- Utilities ----------


def tail_file(path):
    # generator that yields appended lines (simple tail -f)
    while not os.path.exists(path):
        time.sleep(0.05)
    with open(path, "r") as f:
        for line in f:
            yield line
        while True:
            line = f.readline()
            if line:
                yield line
            else:
                time.sleep(0.05)


def human_size(n):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024 or unit == "TB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024.0
    return f"{n:.1f} PB"


def fmt_mtime(ts):
    try:
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return "-"


def write_state_from_events():
    """Rebuild a lightweight node state map from recent events."""
    latest = {}
    if not os.path.exists(EVENTS_FILE):
        with open(STATE_FILE, "w") as f:
            json.dump({"nodes": []}, f)
        return
    try:
        with open(EVENTS_FILE, "r") as f:
            for line in f:
                try:
                    evt = json.loads(line)
                except Exception:
                    continue
                detail = evt.get("detail") or {}
                ip = detail.get("ip") or detail.get("client_id") or detail.get("src")
                if not ip:
                    continue
                evt_type = evt.get("type") or "unknown"
                if evt_type in ("put_start", "get_start"):
                    state = "transferring"
                elif evt_type in ("client_disconnected",):
                    state = "idle"
                elif evt_type in ("error",):
                    state = "error"
                else:
                    state = "connected"
                latest[str(ip)] = state
    except Exception:
        pass
    with open(STATE_FILE, "w") as f:
        json.dump({"nodes": [{"ip": k, "state": v} for k, v in latest.items()]}, f)


def read_recent_events(limit=500):
    if not os.path.exists(EVENTS_FILE):
        return []
    events = []
    with open(EVENTS_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except Exception:
                continue
    return events[-limit:] if limit > 0 else events


def append_event(event_obj):
    """Normalize and append one event to the event log + derived state file."""
    evt_type = str(event_obj.get("type") or "raw")
    detail = event_obj.get("detail")
    if not isinstance(detail, dict):
        detail = {"raw": str(detail)[:4000] if detail is not None else ""}
    evt = {
        "ts": event_obj.get("ts") or time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "type": evt_type,
        "detail": detail,
    }
    with open(EVENTS_FILE, "a") as f:
        f.write(json.dumps(evt) + "\n")
    write_state_from_events()


def parse_ts(ts_text):
    if not ts_text:
        return None
    try:
        return datetime.fromisoformat(str(ts_text).replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def make_token(filename, ttl):
    token = secrets.token_urlsafe(18)
    expires = time.time() + int(ttl)
    TEMP_TOKENS[token] = (filename, expires)
    return token, expires


def validate_token(token):
    rec = TEMP_TOKENS.get(token)
    if not rec:
        return None
    name, expires = rec
    if time.time() > expires:
        try:
            del TEMP_TOKENS[token]
        except KeyError:
            pass
        return None
    return name


def token_cleanup_loop():
    while True:
        now = time.time()
        to_delete = [t for t, (_, exp) in list(TEMP_TOKENS.items()) if exp < now]
        for t in to_delete:
            try:
                del TEMP_TOKENS[t]
            except KeyError:
                pass
        time.sleep(5)


_cleanup_thread = threading.Thread(target=token_cleanup_loop, daemon=True)
_cleanup_thread.start()

# ---------- Database helpers (SQLite) ----------


def get_db():
    db = getattr(g, "_db", None)
    if db is None:
        os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
        db = g._db = sqlite3.connect(DB_PATH, check_same_thread=False)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_db(error):
    db = getattr(g, "_db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript(
        """
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      pw_hash TEXT NOT NULL,
      created_ts INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS devices (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      client_id TEXT NOT NULL,
      name TEXT,
      device_type TEXT,
      icon TEXT,
      ua TEXT,
      last_seen INTEGER,
      FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """
    )
    cols = [r["name"] for r in db.execute("PRAGMA table_info(devices)").fetchall()]
    if "device_type" not in cols:
        db.execute("ALTER TABLE devices ADD COLUMN device_type TEXT")
    if "icon" not in cols:
        db.execute("ALTER TABLE devices ADD COLUMN icon TEXT")
    db.commit()


# ---------- Auth helpers ----------


def login_required(f):
    # simple decorator
    from functools import wraps

    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            # redirect to login page
            return redirect("/login")
        return f(*args, **kwargs)

    return wrapped


# ---------- SSE (events) - open to anonymous reporters ----------
@app.route("/events")
def sse():
    def gen():
        for line in tail_file(EVENTS_FILE):
            yield f"data: {line.strip()}\n\n"

    return Response(stream_with_context(gen()), mimetype="text/event-stream")


# Provide a lightweight state endpoint (protected since it may reveal user info)
@app.route("/api/state")
@login_required
def state():
    if not os.path.exists(STATE_FILE):
        return jsonify({"nodes": []})
    with open(STATE_FILE) as f:
        return Response(f.read(), mimetype="application/json")


# ---------- Root and static pages (login/register/viewer) ----------
# Serve login/register pages (we created html earlier)
@app.route("/login")
def login_page():
    return send_from_directory(".", "login.html")


@app.route("/register")
def register_page():
    return send_from_directory(".", "register.html")


# viewer is gated: redirect to login if not authenticated
@app.route("/")
@login_required
def root():
    return send_from_directory(".", "viewer.html")


@app.route("/viewer.html")
@login_required
def viewer_page():
    return send_from_directory(".", "viewer.html")


# ---------- Auth endpoints ----------
@app.route("/api/auth/register", methods=["POST"])
def api_register():
    data = request.get_json(force=True)
    username = (data.get("username") or "").strip()
    pw = data.get("password")
    if not username or not pw:
        return jsonify({"ok": False, "error": "missing"}), 400
    db = get_db()
    try:
        cur = db.cursor()
        cur.execute(
            "INSERT INTO users (username, pw_hash, created_ts) VALUES (?, ?, ?)",
            (username, generate_password_hash(pw), int(time.time())),
        )
        db.commit()
        return jsonify({"ok": True})
    except sqlite3.IntegrityError:
        return jsonify({"ok": False, "error": "user exists"}), 409


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json(force=True)
    username = (data.get("username") or "").strip()
    pw = data.get("password")
    if not username or not pw:
        return jsonify({"ok": False, "error": "missing"}), 400
    db = get_db()
    row = db.execute(
        "SELECT id, pw_hash FROM users WHERE username=?", (username,)
    ).fetchone()
    if not row or not check_password_hash(row["pw_hash"], pw):
        append_event(
            {
                "type": "auth_failed",
                "detail": {
                    "username": username,
                    "ip": request.remote_addr or "unknown",
                },
            }
        )
        return jsonify({"ok": False, "error": "bad"}), 401
    session.clear()
    session["user_id"] = row["id"]
    session.permanent = True
    append_event(
        {
            "type": "auth_success",
            "detail": {"username": username, "ip": request.remote_addr or "unknown"},
        }
    )
    return jsonify({"ok": True, "user_id": row["id"], "username": username})


@app.route("/api/auth/logout", methods=["POST", "GET"])
def api_logout():
    session.clear()
    if request.method == "GET":
        return redirect("/login")
    return jsonify({"ok": True})


@app.route("/api/auth/me")
@login_required
def api_me():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"ok": False}), 401
    db = get_db()
    row = db.execute("SELECT id, username FROM users WHERE id=?", (uid,)).fetchone()
    if not row:
        return jsonify({"ok": False}), 401
    return jsonify({"ok": True, "user_id": row["id"], "username": row["username"]})


# ---------- Devices endpoints (protected) ----------
@app.route("/api/devices/register", methods=["POST"])
@login_required
def api_devices_register():
    data = request.get_json(force=True)
    client_id = (data.get("client_id") or "").strip()
    name = (data.get("name") or "").strip()
    device_type = (data.get("device_type") or "client").strip()[:32]
    icon = (data.get("icon") or "💻").strip()[:8]
    ua = request.headers.get("User-Agent", "")[:255]
    if not client_id:
        return jsonify({"ok": False, "error": "missing client_id"}), 400
    uid = session["user_id"]
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "SELECT id FROM devices WHERE user_id=? AND client_id=?", (uid, client_id)
    )
    r = cur.fetchone()
    ts = int(time.time())
    if r:
        cur.execute(
            "UPDATE devices SET name=?, device_type=?, icon=?, ua=?, last_seen=? WHERE id=?",
            (name, device_type, icon, ua, ts, r["id"]),
        )
    else:
        cur.execute(
            "INSERT INTO devices (user_id, client_id, name, device_type, icon, ua, last_seen) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (uid, client_id, name, device_type, icon, ua, ts),
        )
    db.commit()
    append_event(
        {
            "type": "client_connected",
            "detail": {
                "ip": client_id,
                "name": name or client_id,
                "device_type": device_type,
                "icon": icon,
            },
        }
    )
    return jsonify({"ok": True})


@app.route("/api/devices/list")
@login_required
def api_devices_list():
    uid = session["user_id"]
    db = get_db()
    rows = db.execute(
        "SELECT client_id, name, device_type, icon, last_seen FROM devices WHERE user_id=? ORDER BY last_seen DESC",
        (uid,),
    ).fetchall()
    devices = []
    for r in rows:
        devices.append(
            {
                "client_id": r["client_id"],
                "name": r["name"] or r["client_id"],
                "device_type": r["device_type"] or "client",
                "icon": r["icon"] or "💻",
                "last_seen": r["last_seen"],
            }
        )
    return jsonify({"ok": True, "devices": devices})


@app.route("/api/devices/profile", methods=["POST"])
@login_required
def api_devices_profile():
    data = request.get_json(force=True)
    client_id = (data.get("client_id") or "").strip()
    if not client_id:
        return jsonify({"ok": False, "error": "missing client_id"}), 400
    name = (data.get("name") or "").strip()
    device_type = (data.get("device_type") or "client").strip()[:32]
    icon = (data.get("icon") or "💻").strip()[:8]
    uid = session["user_id"]
    db = get_db()
    db.execute(
        "UPDATE devices SET name=?, device_type=?, icon=?, last_seen=? WHERE user_id=? AND client_id=?",
        (name, device_type, icon, int(time.time()), uid, client_id),
    )
    db.commit()
    return jsonify({"ok": True})


@app.route("/api/devices/delete", methods=["POST"])
@login_required
def api_devices_delete():
    data = request.get_json(force=True)
    client_id = (data.get("client_id") or "").strip()
    if not client_id:
        return jsonify({"ok": False, "error": "missing client_id"}), 400
    uid = session["user_id"]
    db = get_db()
    cur = db.execute(
        "DELETE FROM devices WHERE user_id=? AND client_id=?",
        (uid, client_id),
    )
    db.commit()
    if cur.rowcount == 0:
        return jsonify({"ok": False, "error": "not found"}), 404
    append_event(
        {
            "type": "device_removed",
            "detail": {"ip": client_id, "src": client_id, "dst": "SERVER"},
        }
    )
    return jsonify({"ok": True})


# ---------- Event logging (open) ----------
@app.route("/api/events/log", methods=["POST"])
def api_log_event():
    # Accept anonymous events (from netcat/raw clients) and authenticated ones alike
    try:
        data = request.get_json(force=True)
    except Exception:
        # if not JSON, try form fields
        data = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
            "type": "raw",
            "detail": {"raw": request.get_data(as_text=True)[:4000]},
        }
    try:
        append_event(data)
    except Exception as e:
        print("log_event write error:", e)
    return jsonify({"ok": True})


# ---------- Uploads & files (web protected) ----------
@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file = request.files.get("file")
        if not file:
            return jsonify({"ok": False, "error": "no file"}), 400
        safe_name = os.path.basename(file.filename)
        path = os.path.join(UPLOAD_DIR, safe_name)
        try:
            file.save(path)
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

        # prefer client_id if submitted (from browser localStorage), else use remote addr
        client_id = (
            request.form.get("client_id")
            or request.headers.get("X-Forwarded-For")
            or request.remote_addr
            or session.get("user_id")
        )
        evt = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
            "type": "put_done",
            "detail": {
                "ip": client_id,
                "src": client_id,
                "dst": "SERVER",
                "direction": "upload",
                "file": safe_name,
                "size": os.path.getsize(path),
            },
        }
        append_event(evt)
        return jsonify({"ok": True, "file": safe_name})

    # serve upload page if exists, else small fallback
    if os.path.exists(os.path.join(".", "upload.html")):
        return send_from_directory(".", "upload.html")
    return '<html><body><h1>Upload</h1><form method="post" enctype="multipart/form-data"><input type=file name=file><input type=submit></form></body></html>'


def collect_upload_files():
    entries = sorted(
        [p for p in os.listdir(UPLOAD_DIR) if not p.startswith(".")], reverse=True
    )
    files = []
    for name in entries:
        full = os.path.join(UPLOAD_DIR, name)
        try:
            st = os.stat(full)
            files.append(
                {
                    "name": name,
                    "size": st.st_size,
                    "size_h": human_size(st.st_size),
                    "mtime": int(st.st_mtime),
                    "mtime_s": fmt_mtime(st.st_mtime),
                }
            )
        except Exception:
            files.append(
                {
                    "name": name,
                    "size": None,
                    "size_h": "?",
                    "mtime": None,
                    "mtime_s": "?",
                }
            )
    return files


@app.route("/api/files/rename", methods=["POST"])
@login_required
def rename_file_api():
    data = request.get_json(force=True)
    old = os.path.basename((data.get("old_name") or "").strip())
    new = os.path.basename((data.get("new_name") or "").strip())
    if not old or not new:
        return jsonify({"ok": False, "error": "missing file name"}), 400
    old_path = os.path.join(UPLOAD_DIR, old)
    new_path = os.path.join(UPLOAD_DIR, new)
    if not os.path.isfile(old_path):
        return jsonify({"ok": False, "error": "source missing"}), 404
    if os.path.exists(new_path):
        return jsonify({"ok": False, "error": "target exists"}), 409
    os.rename(old_path, new_path)
    append_event(
        {
            "type": "file_renamed",
            "detail": {
                "ip": str(session.get("user_id")),
                "src": str(session.get("user_id")),
                "dst": "SERVER",
                "old_name": old,
                "new_name": new,
            },
        }
    )
    return jsonify({"ok": True})


@app.route("/api/files/delete", methods=["POST"])
@login_required
def delete_file_api():
    data = request.get_json(force=True)
    name = os.path.basename((data.get("name") or "").strip())
    if not name:
        return jsonify({"ok": False, "error": "missing file name"}), 400
    path = os.path.join(UPLOAD_DIR, name)
    if not os.path.isfile(path):
        return jsonify({"ok": False, "error": "not found"}), 404
    os.remove(path)
    append_event(
        {
            "type": "file_deleted",
            "detail": {
                "ip": str(session.get("user_id")),
                "src": str(session.get("user_id")),
                "dst": "SERVER",
                "file": name,
            },
        }
    )
    return jsonify({"ok": True})


@app.route("/api/analytics")
@login_required
def analytics_api():
    events = read_recent_events(1500)
    transfer_events = {"put_start", "put_done", "get_start", "get_done"}
    by_device = {}
    auth_fail_by_ip = {}
    burst_window = []
    now = time.time()
    for evt in events:
        detail = evt.get("detail") or {}
        src = str(
            detail.get("src") or detail.get("ip") or detail.get("client_id") or ""
        )
        evt_type = evt.get("type") or "unknown"
        size = int(detail.get("size") or 0)
        ts = parse_ts(evt.get("ts")) or now
        if src:
            if src not in by_device:
                by_device[src] = {"events": 0, "bytes": 0, "transfers": 0}
            by_device[src]["events"] += 1
            if evt_type in transfer_events:
                by_device[src]["transfers"] += 1
                by_device[src]["bytes"] += size
        if evt_type == "auth_failed":
            ip = str(detail.get("ip") or "unknown")
            auth_fail_by_ip[ip] = auth_fail_by_ip.get(ip, 0) + 1
        burst_window.append(ts)
    burst_window = [t for t in burst_window if now - t <= 20]
    top = sorted(
        [{"id": k, **v} for k, v in by_device.items()],
        key=lambda x: (x["bytes"], x["events"]),
        reverse=True,
    )[:8]
    return jsonify(
        {
            "ok": True,
            "totals": {
                "events": len(events),
                "devices": len(by_device),
                "bytes": sum(v["bytes"] for v in by_device.values()),
                "burst_20s": len(burst_window),
            },
            "top_devices": top,
            "auth_fail_by_ip": auth_fail_by_ip,
        }
    )


@app.route("/api/state/export")
@login_required
def export_state_api():
    events = read_recent_events(5000)
    state_payload = {"nodes": []}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try:
                state_payload = json.load(f)
            except Exception:
                state_payload = {"nodes": []}
    uid = session["user_id"]
    db = get_db()
    devices = [
        dict(r)
        for r in db.execute(
            "SELECT client_id, name, device_type, icon, last_seen FROM devices WHERE user_id=? ORDER BY last_seen DESC",
            (uid,),
        ).fetchall()
    ]
    payload = {
        "version": 1,
        "exported_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "state": state_payload,
        "events": events,
        "devices": devices,
    }
    return jsonify({"ok": True, "payload": payload})


@app.route("/api/state/import", methods=["POST"])
@login_required
def import_state_api():
    data = request.get_json(force=True)
    payload = data.get("payload") if isinstance(data, dict) else None
    if not isinstance(payload, dict):
        return jsonify({"ok": False, "error": "invalid payload"}), 400
    events = payload.get("events")
    if not isinstance(events, list):
        return jsonify({"ok": False, "error": "missing events"}), 400
    with open(EVENTS_FILE, "w") as f:
        for evt in events[-5000:]:
            if isinstance(evt, dict):
                f.write(json.dumps(evt) + "\n")
    write_state_from_events()
    devices = payload.get("devices") or []
    uid = session["user_id"]
    db = get_db()
    for d in devices:
        if not isinstance(d, dict):
            continue
        client_id = (d.get("client_id") or "").strip()
        if not client_id:
            continue
        db.execute(
            "INSERT OR REPLACE INTO devices (id, user_id, client_id, name, device_type, icon, ua, last_seen) VALUES ((SELECT id FROM devices WHERE user_id=? AND client_id=?), ?, ?, ?, ?, ?, '', ?)",
            (
                uid,
                client_id,
                uid,
                client_id,
                (d.get("name") or client_id)[:255],
                (d.get("device_type") or "client")[:32],
                (d.get("icon") or "💻")[:8],
                int(d.get("last_seen") or time.time()),
            ),
        )
    db.commit()
    return jsonify({"ok": True})


@app.route("/files")
@login_required
def files_page():
    if os.path.exists(os.path.join(".", "files.html")):
        return send_from_directory(".", "files.html")
    return jsonify({"ok": True, "files": collect_upload_files()})


@app.route("/api/files")
@login_required
def list_files_api():
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
    except Exception:
        return jsonify({"ok": False, "error": "uploads dir error"}), 500
    return jsonify({"ok": True, "files": collect_upload_files()})


@app.route("/files/<path:name>")
@login_required
def serve_file(name):
    if ".." in name or name.startswith("/"):
        abort(404)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    path = os.path.join(UPLOAD_DIR, name)
    if not os.path.isfile(path):
        abort(404)
    size = os.path.getsize(path)
    src = str(session.get("user_id") or request.remote_addr or "unknown")
    append_event(
        {
            "type": "get_done",
            "detail": {
                "ip": src,
                "src": "SERVER",
                "dst": src,
                "direction": "download",
                "file": name,
                "size": size,
            },
        }
    )
    return send_from_directory(UPLOAD_DIR, name, as_attachment=True)


@app.route("/api/files/temp", methods=["POST"])
@login_required
def create_temp_link():
    data = request.get_json(force=True)
    name = data.get("name")
    if not name:
        return jsonify({"ok": False, "error": "missing name"}), 400
    name = os.path.basename(name)
    full = os.path.join(UPLOAD_DIR, name)
    if not os.path.isfile(full):
        return jsonify({"ok": False, "error": "file not found"}), 404
    ttl = int(data.get("ttl", 60))
    token, expires = make_token(name, ttl)
    url = f"/api/files/temp/{token}"
    return jsonify({"ok": True, "url": url, "expires": int(expires)})


@app.route("/api/files/temp/<token>")
def serve_temp(token):
    name = validate_token(token)
    if not name:
        abort(404)
    try:
        full = os.path.join(UPLOAD_DIR, name)
        if os.path.isfile(full):
            size = os.path.getsize(full)
            append_event(
                {
                    "type": "get_done",
                    "detail": {
                        "ip": str(request.remote_addr or "anon"),
                        "src": "SERVER",
                        "dst": str(request.remote_addr or "anon"),
                        "direction": "download",
                        "file": name,
                        "size": size,
                    },
                }
            )
        return send_from_directory(UPLOAD_DIR, name, as_attachment=True)
    except Exception as e:
        print("serve_temp error:", e)
        abort(500)


# ---------- Run server (init DB inside app context) ----------
if __name__ == "__main__":
    # create DB schema inside app context
    with app.app_context():
        init_db()
    print(f"Events server running at http://{HOST}:{PORT}/")
    # ensure events file exists
    open(EVENTS_FILE, "a").close()
    app.run(host=HOST, port=PORT, debug=False)
