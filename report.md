# 🏁 EtherMap Final Project Report

## 🌌 Project Overview
EtherMap is a real-time network topology visualization and monitoring suite designed for live exhibitions and network activity tracking. It transforms abstract data transmissions into a dynamic, interactive, and visually engaging experience.

## 🛠️ Tech Stack
- **Backend:** Python 3.13, Flask (REST API), Flask-SocketIO (Signaling), SQLite (Persistence).
- **Frontend:** D3.js (Force-directed Graph), Phosphor Icons, CSS3 (Omarchy custom theming).
- **Environment:** Nix Flakes for reproducible deployment.

## 💎 Key Features Implemented

### 1. **Dynamic Network Visualization**
- **Force-Directed Graph:** High-performance rendering of network nodes and links using D3.js.
- **Real-time Updates:** Asynchronous event streaming via SSE (Server-Sent Events) keeps the topology live.
- **P2P Mapping:** Visualization of direct peer-to-peer signaling exchanges beyond simple client-server paths.

### 2. **Rich Interactivity & UX**
- **Animated Data Flow:** Pulsing dash animations on active links visually represent data transfers.
- **Node Metadata Cards:** Hovering over nodes reveals detailed device profiles (OS, Type, IDs).
- **Navigation Tools:** Integrated **Zoom & Pan** support and a **Center View** button for effortless exploration of large networks.
- **Timeline Replay:** A functional VCR-style control to replay historical network events and trace past activity.
- **Tabbed Dashboard:** A clean, organized sidebar for Status, Activity, and Settings.

### 3. **Advanced Backend Optimization**
- **In-Memory Caching:** Implemented `STATE_CACHE` in the Flask backend to avoid expensive log parsing on every event.
- **Standardized API:** Transitioned all internal endpoints to a professional `/api/v1` style structure.
- **Demo Lifecycle:** Built-in administrative reset tools to wipe exhibition state instantly.

### 4. **Aesthetics & Personalization**
- **Omarchy Theme:** A custom Midnight Blue & Soft White color palette with full light/dark mode support.
- **Iconography:** Integration of the Phosphor Icon library for a modern, sharp UI.
- **Mobile First:** Fully responsive design across all pages, ensuring the dashboard is accessible on phones, tablets, and desktops.
- **Custom Identities:** Users can register devices with custom names, types, and icons.

## 📈 Analytics & Feedback
- **Live Sparklines:** Real-time event frequency monitoring within the dashboard.
- **Security Feedback:** Real-time password strength metering on the identity portal.
- **Activity Filtering:** Instant search and filtering of the live event log.

## 🚀 Conclusion
EtherMap is now a fully-featured, exhibition-ready prototype. It successfully bridges the gap between raw network logging and human-centric visualization, providing a robust platform for future network analytics and real-time monitoring.

---
*Generated on: April 29, 2026*
