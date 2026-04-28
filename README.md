# 🌐 EtherMap

**Mapping the Invisible Network**

EtherMap is a real-time network topology visualization tool that brings hidden network activity into a visible, interactive space.
It combines live event streaming, file transfer, authentication, and device tracking into a single system designed for learning, demonstration, and experimentation.

---

## 🚀 Features

* ⚡ **Real-Time Visualization**
  View network activity live using Server-Sent Events (SSE)

* 📂 **Mini FTP System**
  Upload files and track transfer events in real time

* 🔐 **Authentication System**
  User registration and login with session handling

* 🧠 **Device Tracking**
  Each client is uniquely identified and visualized

* 💬 **Chat & Signaling**
  Built-in Socket.IO support for communication and P2P signaling

* 🔗 **Temporary Download Links**
  Secure, time-limited file access

---

## 🧱 Project Structure

```
EtherMap/
├── auth_signaling.py       # Socket.IO signaling/chat server
├── events-server.py        # Auth + uploads + SSE event stream
├── server.py               # Starts both servers for demo
├── viewer.html             # Network visualization UI
├── upload.html             # File upload interface
├── login.html              # Login page
├── register.html           # Registration page
├── files.html              # File listing interface
├── auth.db                 # SQLite database
├── uploads/                # Uploaded files
```

---

## ⚙️ Tech Stack

* **Backend:** Flask, Flask-SocketIO
* **Realtime:** Server-Sent Events (SSE), WebSockets
* **Frontend:** HTML, CSS, JavaScript
* **Database:** SQLite

---

## 🧪 How It Works

1. User logs in or registers
2. User uploads a file
3. Server logs the event
4. Viewer receives live updates via SSE
5. Nodes and activity appear in real time

---

## ▶️ Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/EtherMap.git
cd EtherMap
```

### 2. Enter dev shell

```bash
nix develop
```

### 3. Run the server

```bash
python server.py
```

### Quick demo reset (between exhibition runs)

```bash
./reset_demo.sh --yes
```

This clears `events.log`, resets `state.json`, and removes uploaded files from `uploads/`.

### 4. Open in browser

* `http://127.0.0.1:5000/` → Network visualization
* `http://127.0.0.1:5000/upload` → Upload files
* `http://127.0.0.1:5000/login` → Authentication

---

## 🎯 Demo Flow (Recommended)

1. Open **http://127.0.0.1:5000/**
2. Login via **/login**
3. Upload a file
4. Watch the network update live

---

## ⚠️ Note

This project is built for educational and demonstration purposes.
It is not production-secure and may require additional validation and security improvements.

---

## 🧠 Future Improvements

* Animated node connections (edges)
* Enhanced UI/UX (dashboard style)
* File management system (download/delete UI)
* Improved authentication and session handling
* Advanced network analytics

---

## 👨‍💻 Author

**Balraj Singh**
Student | Developer | Builder of things that shouldn't exist (but do anyway)

---

## 🌌 Tagline

> *Where Connections Take Shape.*
