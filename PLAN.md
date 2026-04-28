# EtherMap – Development Plan

## Overview

EtherMap is a real-time network topology visualization tool with:

* Live node tracking (SSE)
* File transfer system (mini FTP)
* Authentication and device tracking
* Chat and signaling (Socket.IO)

The goal is to stabilize, clean, and enhance the system for demonstration and future scalability.

---

## Current State

* Core functionality works (auth, upload, visualization)
* Codebase contains redundant files and inconsistent naming
* UI is functional but basic
* Logging and error handling are minimal

---

## Goals (Short-Term: Exhibition Ready)

### 1. Stability

* Ensure all routes work correctly (login, upload, viewer)
* Fix any broken links between frontend and backend
* Validate database interactions

### 2. Cleanup

* Remove unused/old files
* Standardize naming conventions
* Organize folder structure

### 3. UI Improvements

* Improve layout of viewer.html
* Add clear labels for nodes and events
* Make navigation between pages smoother

### 4. Logging & Debugging

* Improve event logging clarity
* Add error handling for failed uploads or auth issues

---

## Goals (Mid-Term)

### 1. Network Visualization Enhancements

* Show connections between nodes (edges)
* Animate node activity
* Differentiate node types (client/server)

### 2. File System Improvements

* Add file delete/download UI
* Improve temp link handling

### 3. Auth Improvements

* Session management cleanup
* Device naming support

---

## Code Guidelines

* Keep functions small and modular
* Avoid duplicating logic
* Prefer clarity over cleverness
* Add comments where logic is non-obvious

---

## Priority Order

1. Fix bugs
2. Ensure demo flow works end-to-end
3. Clean code
4. Enhance UI
5. Add new features

---

## Demo Flow (Must Work)

1. User registers/logs in
2. User uploads a file
3. Event is logged
4. Viewer shows node activity in real time

---

## Notes for AI Assistant (Copilot CLI)

* Do NOT rewrite entire files unless necessary
* Prefer incremental changes
* Ask for clarification if unsure about architecture
* Maintain compatibility with existing routes and structure

