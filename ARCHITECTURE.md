# EtherMap Architecture

## Components

### 1. events-server.py

* Handles file uploads
* Logs events
* Provides SSE endpoint for real-time updates

### 2. auth_signaling.py

* Handles authentication (login/register)
* Manages devices
* Provides Socket.IO signaling and chat

### 3. server.py

* Runs both servers together
* Entry point of the application

---

## Frontend

### viewer.html

* Displays network nodes and events
* Connects to SSE endpoint

### upload.html

* Allows file upload
* Sends events to server

### login.html / register.html

* User authentication UI

---

## Data Flow

1. User uploads file
2. events-server logs event
3. SSE pushes update to viewer
4. Viewer updates node visualization

---

## Key Technologies

* Flask (backend)
* Socket.IO (realtime signaling)
* SSE (event streaming)
* HTML/CSS/JS (frontend)
* SQLite (database)

---

## Known Constraints

* Not production secure
* Designed for demo purposes
* Minimal error handling

