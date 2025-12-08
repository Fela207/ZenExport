# 🏯 ZenExport v5.2

![License](https://img.shields.io/badge/License-MIT-green.svg) ![Fusion 360](https://img.shields.io/badge/Fusion%20360-Addin-orange.svg) ![Python](https://img.shields.io/badge/Python-3.x-blue.svg)

**The "Peace of Mind" Local Save Workflow for Fusion 360.**

ZenExport is a Fusion 360 Add-In that **replaces** the native Cloud Save (`Ctrl+S`) with a powerful local asset manager. It forces a disciplined, organised folder structure on your hard drive, keeping your IP safe and your versions sane.

---

## ✨ Features that Spark Joy

- 🚫 **Ctrl+S Override:** We intercept the native save command. No more "Cloud Save" dialogs. One press, one local backup.
- 🧠 **Smart Context Binding:**
  - Setup a project _once_. ZenExport remembers which local folder belongs to which open tab (even "Untitled" ones!).
  - Switch tabs, press Save, and it goes to the right place. Every time.
- 💾 **Incremental Versioning:** auto-saves as `Project_v01.f3d`, `Project_v02.f3d`... never overwriting history.
- 🚀 **Intelligent Hashing:** Checks your design's DNA (Timeline, Bodies, Parameters). If nothing changed, it skips the save.
- 📦 **Full Package Export:**
  - 📄 `.f3d` (Parametric Source)
  - 🛠️ `.step` (CAD Interchange)
  - 🗿 `.stl` (Resultant Mesh for every visible body)
  - 🖼️ `_preview.png` (Viewport Snapshot)
- 📂 **Auto-Open:** Opens the project folder after every save so you can grab your files immediately.

---

## 🛠️ Installation

1.  **Download** this folder.
2.  Move it to your Fusion 360 API folder:
    - **Windows:** `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\`
    - _(Ensure the folder is named `ZenExport` and contains `ZenExport.py` inside)_
3.  **Restart Fusion 360**.
4.  Go to **Utilities > Scripts and Add-Ins**, select `ZenExport`, and ensure **Run on Startup** is checked.

---

## 🎮 How to Use

### 1. The First Save (Initialization)

Open a new design. Press **`Ctrl+S`**.

- ZenExport will ask: _"Where should this project live?"_
- Select a parent directory (e.g., `Desktop/MyProjects`).
- Confirm the **Project Name** (e.g., `TurboEncabulator`).
- **Action:** It creates `.../TurboEncabulator/CAD/v01/` and runs the export.

### 2. The Routine (Update)

Make some changes. Press **`Ctrl+S`**.

- **Action:** ZenExport detects the design changes and instantly creates `v02` in the same folder. No prompts.
- _If no changes were made, it tells you and skips the save._

### 3. The "Resume" (Context Awareness)

- Close Fusion.
- Re-open your `TurboEncabulator_v02.f3d` file.
- Press **`Ctrl+S`**.
- **Action:** ZenExport recognizes the file name and resumes saving to your existing project folder as `v03`.

### 4. Resolving "Untitled" Tabs

- If you have an "Untitled" tab that you previously set up as "Project A":
- ZenExport uses a **GUID (Session ID)** to remember it belongs to "Project A".
- Pressing Save will correctly update "Project A".

---

## 📂 Folder Structure

ZenExport enforces this clean layout:

```text
MyProject/
├── CAD/
│   ├── v01/
│   │   ├── MyProject_v01.f3d
│   │   └── MyProject_v01.step
│   └── v02/
│       ├── MyProject_v02.f3d
│       └── MyProject_v02.step
├── Models/
│   ├── ComponentA.stl
│   └── ComponentB.stl
└── _preview.png
```

---

## ⚠️ Known Limitations

- **Tabs stay "Untitled":** Since we bypass the Cloud Save, Fusion 360 doesn't update the tab name. Rely on the file system names!
- **Local Only:** This script does NOT upload to the Autodesk Cloud.

---

_"Order is the sanity of the mind, the health of the body, the peace of the city."_
