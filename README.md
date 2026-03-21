<div align="center">

# 🎵 Advanced Tag Editor
### Enterprise Edition v7.5.0

**A professional-grade audio metadata editor built with Python and PySide6**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://python.org)
[![PySide6](https://img.shields.io/badge/PySide6-6.x-green?logo=qt&logoColor=white)](https://pypi.org/project/PySide6/)
[![License](https://img.shields.io/badge/License-Proprietary-red)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](https://github.com)

</div>

---

## Overview

Advanced Tag Editor is a desktop application for managing audio file metadata with enterprise-level features. It supports batch operations, waveform visualization, a live statistics dashboard, and deep iTunes / LRCLIB integration — all wrapped in a dockable, theme-aware interface that remembers exactly how you left it.

Designed for audio archivists, music library managers, and audiophiles who need more than a basic tag editor.

---

## Screenshots
<img width="1365" height="767" alt="Screenshot 2026-03-21 071811" src="https://github.com/user-attachments/assets/8135abd1-6513-48ab-b58d-1998e7d1cda3" />

<img width="1365" height="767" alt="Screenshot 2026-03-21 071708" src="https://github.com/user-attachments/assets/d4e4ec49-845b-4075-bcbe-dfba7b73124b" />

<img width="1365" height="767" alt="Screenshot 2026-03-21 071723" src="https://github.com/user-attachments/assets/100b371b-226f-4545-8823-e3cc04314fb9" />



---

## Features

### 🗂 Metadata Management
- Read and write tags for **MP3** (ID3v2), **M4A** (MP4/AAC), and **FLAC** (Vorbis Comment)
- Edit title, artist, album, year, genre, and track number
- Embedded **cover art** support: fetch from iTunes, load from local file, or remove
- **Lyrics** support: embedded USLT (MP3), `©lyr` (M4A), and Vorbis `LYRICS` (FLAC)
- **Per-file undo / redo** history stack — `Ctrl+Z` / `Ctrl+Y`

### ⚡ Batch Operations
- **Auto Tag (Magic)** — fetch complete metadata + high-resolution cover art from the iTunes Search API for single or multiple selected files simultaneously
- **Batch Rename** — rename files using a template engine with tokens: `{title}`, `{artist}`, `{album}`, `{year}`, `{genre}`, `{tracknumber}`. Live preview before applying
- **Export to CSV** — dump full library metadata to a `.csv` file
- **Import from CSV** — mass-update metadata from an external CSV (matched by file path)
- **Processing Queue** dock — add files to a queue and run bulk auto-tagging in one click

### 🌊 Audio Analysis
- Displays **bitrate**, **sample rate**, and **format** for the selected file
- **BPM detection** via `librosa` — analyzes up to the first 60 seconds of audio (`Ctrl+B`)
- **Waveform Visualizer** dock powered by `pyqtgraph` + `numpy`:
  - Renders the full waveform with an RMS envelope fill
  - **Live playhead** that tracks playback position in real time
  - Theme-aware background and foreground colours

### 📊 Statistics Dashboard (Live Dock)
- Summary cards: total files, total duration, total size, detected formats
- **Tag completeness** progress bars — complete (5/5), partial (≥3), empty
- **Top genres** horizontal bar chart (up to 7 genres)
- **Tracks by decade** distribution chart
- Auto-refreshes every time a new folder is loaded

### 🔍 Library Tools
- **Duplicate Detector** (`Ctrl+D`) — finds files sharing identical title + artist combinations
- **Missing Tags Filter** (`Ctrl+M`) — filter the library by any combination of missing tags; missing cells highlighted in red
- **Live search filter** — instant keyword filtering across filename, title, artist, and album
- **Sortable columns** — click any header to sort ascending or descending
- **Tag completeness badge** — colour-coded `●` indicator per row (green / amber / red)

### 🎵 Integrated Media Player
- Play, pause, and seek directly within the application
- Seek bar with current time display
- Volume control — persisted across sessions

### 🖥 User Interface
- **Ribbon-style toolbar** with labelled sections: FILE, BATCH, ANALYSIS, VIEW, PLAYER, VOLUME
- **Column presets**: Compact, Standard, Detail — saved and restored on next launch
- **Toggle fullscreen** (`F11`) for maximum workspace; `Esc` to exit
- **Side-by-side or stacked** layout toggle for the table/editor split
- **Drag and drop** — drop audio files or a folder directly onto the window
- **Four dockable panels**: Activity Log, Waveform Visualizer, Processing Queue, Statistics Dashboard
- **Dark and Light themes** — fully custom `QPalette` for dark; system palette for light
- **Keyboard shortcuts overlay** (`F1`)

### 💾 Persistent Settings (QSettings)
Every aspect of the UI state is saved and restored automatically on the next launch:

| Setting | What is saved |
|---|---|
| Window | Size, position, maximized/fullscreen state |
| Docks & toolbars | Position, visibility, tab order (`saveState`) |
| Splitters | Outer tree/tabs ratio + inner table/editor ratio |
| Layout | Stacked vs. side-by-side |
| Theme | Dark or light |
| Volume | Slider position |
| Column preset | Compact / Standard / Detail |
| Column widths | Individual widths for all 9 columns |
| Last folder | Reopened automatically on startup |

---

## Requirements

### Core (required)
```
Python >= 3.9
PySide6 >= 6.4
mutagen >= 1.46
requests >= 2.28
```

### Optional (for full feature set)
```
librosa >= 0.10      # BPM detection
numpy  >= 1.24       # waveform data processing
pyqtgraph >= 0.13    # waveform visualizer widget
```

> The application runs without the optional packages. BPM detection and the waveform visualizer are gracefully disabled with an informational message if they are not installed.

---

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/danx123/advanced-tag-editor.git
cd advanced-tag-editor
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
# Core dependencies
pip install PySide6 mutagen requests

# Optional — for BPM detection and waveform visualizer
pip install librosa numpy pyqtgraph
```

### 4. Run the application
```bash
python advanced_tag_editor_enterprise_v5.2.py
```

### Optional: place a `tag.ico` file in the same directory to use a custom window icon.

---

## Usage

### Opening a folder
Use **File → Locate Folder…** or drag and drop a folder onto the window. The file table will populate with all `.mp3`, `.m4a`, and `.flac` files found.

### Editing tags
1. Click a row in the file table to load its metadata into the editor panel
2. Edit any field in the **Metadata Properties** form
3. Press `Ctrl+S` or click **Save Metadata** to write changes to disk
4. The editor automatically advances to the next file after saving

### Auto Tagging
Select one or more rows, then click **⚡ Auto Tag (Magic)** or press `Ctrl+T`. The application queries the iTunes Search API and writes title, artist, album, year, genre, track number, and cover art for each selected file. A progress dialog shows live status.

### Batch Rename
Select files, then press `Ctrl+R`. Choose a naming template (or write a custom one using `{tokens}`) and preview the result before applying.

### Waveform Visualizer
Select a file and click **"Load Waveform"** in the Waveform Visualizer dock. The audio is decoded and rendered as a waveform with an RMS envelope. The red playhead moves in real time during playback.

### CSV Workflow
- **Export** (`Ctrl+E`): saves all currently loaded file metadata to a `.csv`
- **Import** (`Ctrl+I`): reads a CSV and applies metadata back to the files matched by path — useful for bulk editing in a spreadsheet

### Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+S` | Save current metadata |
| `Ctrl+Z` | Undo last field change |
| `Ctrl+Y` | Redo |
| `F1` | Keyboard shortcuts overlay |
| `F5` | Refresh current folder |
| `F11` | Toggle fullscreen |
| `Esc` | Exit fullscreen |
| `Ctrl+T` | Auto Tag selected files |
| `Ctrl+R` | Batch Rename selected files |
| `Ctrl+E` | Export metadata to CSV |
| `Ctrl+I` | Import metadata from CSV |
| `Ctrl+B` | Detect BPM (requires librosa) |
| `Ctrl+D` | Find duplicates |
| `Ctrl+M` | Missing tags filter |
| `Ctrl+A` | Select all files |
| `Space` | Play / Pause |

---

## Supported Formats

| Format | Container | Tag Standard | Cover Art | Lyrics |
|---|---|---|---|---|
| `.mp3` | MPEG Audio | ID3v2 | APIC frame | USLT frame |
| `.m4a` | MPEG-4 / AAC | MP4 atoms | `covr` atom | `©lyr` atom |
| `.flac` | Free Lossless | Vorbis Comment | PICTURE block | `LYRICS` tag |

---


## Online Services Used

| Service | Purpose | When |
|---|---|---|
| [iTunes Search API](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/) | Metadata + cover art lookup | Auto Tag, Fetch Art |
| [LRCLIB](https://lrclib.net) | Synced and plain lyrics | Fetch Lyrics |

Both services are queried only on explicit user action. No data is sent automatically or in the background.



## License

© Macan Angkasa. All Rights Reserved.

This software is proprietary. Redistribution, modification, or use in any commercial or non-commercial product without explicit written permission from the author is prohibited.

---

## Acknowledgements

- [PySide6 / Qt](https://www.qt.io) — UI framework
- [mutagen](https://mutagen.readthedocs.io) — audio metadata library
- [librosa](https://librosa.org) — audio analysis and BPM detection
- [pyqtgraph](https://pyqtgraph.readthedocs.io) — waveform visualization
- [iTunes Search API](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/) — metadata and artwork lookup
- [LRCLIB](https://lrclib.net) — lyrics database

---

<div align="center">
<sub>Built with ♥ by Macan Angkasa</sub>
</div>
