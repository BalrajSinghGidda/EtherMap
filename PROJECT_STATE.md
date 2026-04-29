# Project Continuation Guide: EtherMap

## 🚀 Quick Start
1. **Environment:** Use `nix develop` to enter the dev shell.
2. **Run:** Execute `python server.py` to start both the Events and Signaling servers.
3. **Ports:**
   - Events Server: `http://127.0.0.1:5000`
   - Signaling Server: `http://127.0.0.1:5050`
4. **Test:** Run `pytest` to ensure core functionality is intact.

## 🧱 Architecture Overview
- **`events-server.py`**: The primary backend. Handles SQLite auth, file uploads, SSE event streaming, and analytics. All JSON APIs standardized under `/api/`.
- **`auth_signaling.py`**: A secondary server for Socket.IO signaling and chat. Now logs `signaling` events for P2P visualization.
- **`viewer.html`**: The main visualization hub using D3.js. Supports animations, icons, and real-time state sync.

## 📋 Current Tasks & Backlog
- [x] **Standardization:** Refactor route names in `events-server.py` to follow a consistent `/api/` pattern.
- [x] **Logging Optimization:** Implemented in-memory `STATE_CACHE` for incremental state updates.
- [x] **UI Polish:** Added tabbed sidebar and light/dark mode toggle.
- [x] **Universal Themes:** Extended theme persistence to `files.html`, `upload.html`, and auth pages.
- [ ] **Custom Theme Implementation:** Await custom dark theme from user and create matching light theme.
- [ ] **Enhanced Analytics:** Add more granular tracking for signaling frequency and file transfer speeds.

## 💡 Key Lessons / Pitfalls
- **Nix vs Pip:** Always prefer Nix for dependencies in this repo.
- **Port Collisions:** If `Address already in use` occurs, check for lingering Python processes on 5000/5050.
- **Shared Session:** Both servers must use the same `FLASK_SECRET` for cross-server authentication to work correctly.

---
*Use this file as a handoff for future CLI agents or developers.*
