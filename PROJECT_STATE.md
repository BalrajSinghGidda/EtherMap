# Project Continuation Guide: EtherMap

## 🚀 Quick Start
1. **Environment:** Use `nix develop` to enter the dev shell.
2. **Run:** Execute `python server.py` to start both the Events and Signaling servers.
3. **Ports:**
   - Events Server: `http://127.0.0.1:5000`
   - Signaling Server: `http://127.0.0.1:5050`
4. **Test:** Run `pytest` to ensure core functionality is intact.

## 🧱 Architecture Overview
- **`events-server.py`**: The primary backend. Handles SQLite auth, file uploads, SSE event streaming, and analytics.
- **`auth_signaling.py`**: A secondary server for Socket.IO signaling and chat. Shares the same session secret.
- **`viewer.html`**: The main visualization hub using D3.js. Connects to SSE for events and Socket.IO for chat.
- **`state.json`**: A derived file containing the current "connected" state of all nodes, updated on every event.

## 📋 Current Tasks & Backlog
- [ ] **Standardization:** Refactor route names in `events-server.py` to follow a consistent `/api/` pattern.
- [ ] **Logging Optimization:** The `write_state_from_events` function currently re-reads the entire log. This should be optimized to use an incremental approach or in-memory state.
- [ ] **UI Polish:** The sidebar in `viewer.html` is functional but crowded. Consider a tabbed interface or better layout.
- [ ] **Connections:** Visualize persistent links between nodes based on historical communication patterns.

## 💡 Key Lessons / Pitfalls
- **Nix vs Pip:** Always prefer Nix for dependencies in this repo.
- **Port Collisions:** If `Address already in use` occurs, check for lingering Python processes on 5000/5050.
- **Shared Session:** Both servers must use the same `FLASK_SECRET` for cross-server authentication to work correctly.

---
*Use this file as a handoff for future CLI agents or developers.*
