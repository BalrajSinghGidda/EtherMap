#!/usr/bin/env python3
# auth_signaling.py
# Minimal signalling + broadcast server using Flask-SocketIO.
# Usage: pip install flask-socketio eventlet
# Run: python3 auth_signaling.py

import json
import os
import time

from flask import Flask, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room

EVENT_LOG = "events.log"


def ts():
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())


def emit_event(event_type, detail):
    evt = {"ts": ts(), "type": event_type, "detail": detail}
    with open(EVENT_LOG, "a") as f:
        f.write(json.dumps(evt) + "\n")


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET") or "dev-secret-change-me"
# CORS allowed for dev/demo. For production, restrict origins.
socketio = SocketIO(app, cors_allowed_origins="*")

# small in-memory client map (for demo)
clients = {}  # sid -> meta
room_members = {}  # room -> set(sid)
room_history = {}  # room -> [{from,msg,ts}]
MAX_ROOM_HISTORY = 80


@socketio.on("connect")
def on_connect():
    sid = request.sid
    user_id = session.get(
        "user_id"
    )  # if user logged in via events-server and shares cookie
    clients[sid] = {"user_id": user_id}
    emit("connected", {"sid": sid})
    emit_event("client_connected", {"ip": sid, "user": user_id})
    print("socket connected", sid, "user", user_id)


@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    clients.pop(sid, None)
    for room, members in list(room_members.items()):
        if sid in members:
            members.discard(sid)
            emit(
                "room_presence",
                {"channel": room, "members": sorted(list(members))},
                room=room,
            )
            if not members:
                room_members.pop(room, None)
    emit_event("client_disconnected", {"ip": sid})
    print("socket disconnected", sid)


# Exchange signaling payloads: { to: remoteSid, type: 'offer'|'answer'|'candidate', payload: ... }
@socketio.on("signal")
def on_signal(data):
    to = data.get("to")
    if to:
        emit("signal", data, to=to)


@socketio.on("list_peers")
def list_peers():
    peers = [{"sid": s, "user_id": v.get("user_id")} for s, v in clients.items()]
    emit("peers", peers)


# Broadcast channels (rooms)
@socketio.on("join_channel")
def join_channel(data):
    room = data.get("channel")
    if room:
        join_room(room)
        room_members.setdefault(room, set()).add(request.sid)
        emit("system", {"msg": f"{request.sid} joined {room}"}, room=room)
        emit(
            "room_presence",
            {"channel": room, "members": sorted(list(room_members.get(room, set())))},
            room=room,
        )
        emit(
            "room_history",
            {
                "channel": room,
                "messages": room_history.get(room, [])[-MAX_ROOM_HISTORY:],
            },
        )


@socketio.on("leave_channel")
def on_leave(data):
    room = data.get("channel")
    if room:
        leave_room(room)
        members = room_members.get(room, set())
        members.discard(request.sid)
        if members:
            room_members[room] = members
        else:
            room_members.pop(room, None)
        emit("system", {"msg": f"{request.sid} left {room}"}, room=room)
        emit(
            "room_presence",
            {"channel": room, "members": sorted(list(room_members.get(room, set())))},
            room=room,
        )


@socketio.on("channel_msg")
def channel_msg(data):
    room = data.get("channel")
    msg = data.get("msg")
    if room and msg is not None:
        entry = {"from": request.sid, "msg": str(msg)[:2000], "ts": ts()}
        room_history.setdefault(room, []).append(entry)
        room_history[room] = room_history[room][-MAX_ROOM_HISTORY:]
        emit("channel_msg", entry, room=room)


@socketio.on("room_state")
def room_state(data):
    room = data.get("channel")
    if not room:
        emit("room_presence", {"channel": "", "members": []})
        return
    emit(
        "room_presence",
        {"channel": room, "members": sorted(list(room_members.get(room, set())))},
    )
    emit(
        "room_history",
        {"channel": room, "messages": room_history.get(room, [])[-MAX_ROOM_HISTORY:]},
    )


if __name__ == "__main__":
    print("Starting signaling server on http://0.0.0.0:5050")
    # eventlet recommended for Flask-SocketIO
    socketio.run(app, host="0.0.0.0", port=5050)
