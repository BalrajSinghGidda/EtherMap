# EtherMap Project History

## Phase 1: Foundation
- Repository initialized with core components: `events-server.py`, `auth_signaling.py`, and `server.py`.
- Basic frontend templates created: `viewer.html`, `upload.html`, `login.html`, `register.html`.
- Implementation of Server-Sent Events (SSE) for real-time event streaming.
- Setup of Nix Flake for reproducible development environments.

## Phase 2: Core Enhancements
- **Authentication:** Added SQLite-based user registration and login with session management.
- **Device Management:** Implemented device registration, profiling, and listing to track multiple clients.
- **File System:** 
    - Enhanced file uploads with better metadata logging.
    - Added support for temporary, time-limited download links.
    - Implemented file rename and delete functionality in both backend and frontend.
- **Analytics:** Built a backend analytics engine to track "Top Talkers", total bytes, and event bursts.

## Phase 3: Visualization & UX
- **Viewer Improvements:**
    - Migrated to a more robust D3.js force-directed graph.
    - Added interactive node states (connected, idle, transferring, error).
    - Implemented a **Timeline Replay** feature to watch historical events.
    - Added a sidebar with sections for devices, analytics, alerts, and chat.
- **Real-time Signaling:** Enhanced the Socket.IO signaling server with room history and presence tracking.
- **State Persistence:** Added functionality to export and import the entire network state and event history as JSON.

## Phase 4: Stability & Testing
- Added `requirements.txt` for non-Nix environments.
- Created `tests/test_smoke.py` to verify auth, upload, and state flows.
- Fixed critical bugs in visualization cleanup and session handling.
- Verified end-to-end demo flow.

## Phase 5: Real-time Dynamics & State Sync
- **State Synchronization:**
    - Implemented `syncStateWithServer()` in the viewer to pull current node statuses from the `/api/state` endpoint.
    - Fixed "Resume Live" functionality to restore active connections instead of wiping the view.
- **Enhanced Visualization:**
    - Added CSS dash animations for active links to visualize real-time data flow.
    - Improved node differentiation with icons (🌐 for server, 💻/📱 for clients) and varied circle sizes.
    - Integrated devices profiles into the visualization to show custom names and emojis.
- **P2P Mapping:**
    - Extended `auth_signaling.py` to log peer-to-peer signaling events.
    - Added support in `viewer.html` to draw transient edges between peers during signaling exchange.

## Phase 6: UI Polish & Backend Optimization
- **Backend Optimization:**
    - Refactored `events-server.py` to use an in-memory `STATE_CACHE`.
    - Removed expensive full-log re-parsing on every event; state is now updated incrementally and saved periodically.
    - Added `load_initial_state` to rebuild cache from log on server startup.
- **UI Enhancements & Customization:**
    - **Theme Toggle:** Implemented a Light/Dark mode toggle with persistence via `localStorage`.
    - **Tabbed Sidebar:** Organized the viewer's sidebar into "Status", "Activity", and "Settings" tabs to reduce clutter and improve focus.
    - **Responsive Fixes:** Adjusted topnav and sidebar spacing for better accessibility across different resolutions.

## Phase 7: Topology Management & Admin Reset
- **Node Lifecycle Improvements:**
    - Implemented auto-disposal of disconnected nodes in `viewer.html` if they do not have a custom profile (un-renamed).
    - Renamed or profiled nodes now persist in an `idle` state upon disconnection, requiring manual removal from the device list.
    - Updated `syncStateWithServer()` to filter out inactive non-profiled nodes, preventing them from reappearing when resuming live view.
- **Admin Reset Feature:**
    - Added `/api/admin/reset` endpoint to `events-server.py` to trigger the full demo reset script safely.
    - Integrated a **Reset Topology** button in the viewer UI to allow administrators to wipe the server state (logs, uploads, nodes) from the browser.

## Phase 8: Universal Theming & UX Overhaul
- **Universal Theme Support:**
    - Extended the light/dark mode toggle to `files.html`, `upload.html`, `login.html`, and `register.html`.
    - Standardized CSS variables across all pages for consistent color schemes.
    - Theme preference now persists across the entire application using `localStorage`.
- **Identity Portal Revamp:**
    - Completely redesigned `login.html` and `register.html` with a modern "terminal" aesthetic.
    - Added subtle background animations and improved typography for a more engaging experience.
    - Updated navigation and layouts to be more professional and cohesive.

## Phase 9: Omarchy Theme & Advanced UI Components
- **Custom Theming:**
    - Implemented a new custom "Omarchy" color palette (Midnight Blue & Soft White) across all pages.
    - Created a matching light theme with inverted tones for a consistent experience.
- **Visual Language & Icons:**
    - Migrated from standard emojis to the **Phosphor Icon** library for all UI elements (topnav, buttons, sidebar).
    - Standardized icons across `viewer.html`, `upload.html`, and `files.html`.
- **Advanced Dashboard Features:**
    - **Real-time Sparkline:** Added a D3.js-powered event frequency chart in the viewer's Status tab.
    - **Password Strength Meter:** Implemented real-time security feedback on the registration page with color-coded strength bars.
- **UX Refinements:**
    - Overhauled `login.html` and `register.html` with thematic iconography and better input styling.
    - Improved button feedback with scale transforms and opacity transitions.

## Phase 10: Interactive UX & Project Finalization
- **Rich Interaction:**
    - Implemented **Node Detail Cards** (hover to view full device metadata/OS/ID).
    - Added **Floating Data Labels** to active links to show file names and transfer types in real-time.
    - Added a **Live Activity Filter** to the event log for instant searching.
- **Customization & Personalization:**
    - Integrated **Phosphor Icons** deeper, allowing users to pick custom icon names (e.g., `ph-desktop`, `ph-alien`) during registration.
    - Redesigned the Device List in the sidebar to render these icons dynamically.
- **Project Completion:**
    - Generated a comprehensive **`report.md`** summarizing the technical architecture and implemented feature set.
    - Verified all core flows (Auth → Discovery → Transfer → Reset) are operational.

---
*Last updated: April 29, 2026*
