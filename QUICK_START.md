# 🚀 Fitness AI — One-Click Quick Start Guide

You now have one-click launcher scripts ready to run on Windows without needing to type terminal commands.

---

## 🎯 Main One-Click Open File

### **`open.bat`** (or **`start.bat`**)
> **Double-click this file to launch the entire Fitness AI system.**

When double-clicked, it automatically:
1. **Detects the environment**: finds Python (`.venv`), the SQLite database (`fitness.db`), and Node/Expo.
2. **Starts the Backend API Server**: FastAPI runs on `http://localhost:8000` in its own dedicated window.
3. **Starts the Mobile App**: Expo Metro Bundler runs on port `8081` in its own dedicated window (showing the QR code for Expo Go).
4. **Opens the Browser**: Automatically navigates to the interactive API Documentation at [`http://localhost:8000/docs`](http://localhost:8000/docs).

---

## 🖥️ Windows Desktop Shortcut

### **`create_desktop_shortcut.bat`**
Double-click this once to place a **"Fitness AI"** shortcut directly on your Windows Desktop. After that, you can launch Fitness AI right from your desktop with a single double-click!

---

## ⚙️ Specialized Component Launchers

If you only want to run specific services individually:

| File | What it does |
| :--- | :--- |
| **`start_backend.bat`** | Starts only the FastAPI backend server on `http://localhost:8000` and configures `DATABASE_URL` for `fitness.db`. |
| **`start_mobile.bat`** | Starts only the Expo Metro bundler for the mobile client. |
| **`start_notion_sync.bat`** | Starts the background Notion collection worker (syncs every 300s) as described in `START-HERE-NOTION.txt`. |
| **`open_menu.bat`** | Interactive menu to launch specific components, launch all, create shortcuts, or open the project in VS Code. |

---

## 🛑 How to Stop the App

To stop the services:
- Close the **Backend API Server** console window (`Port 8000`).
- Close the **Mobile App** console window (`Expo Metro`).
- Or press `CTRL + C` inside either terminal window.
