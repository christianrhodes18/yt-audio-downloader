# AGENTS.md

## Cursor Cloud specific instructions

### Overview
This is a small desktop Tkinter GUI app (`app.py`) that downloads audio from YouTube using `yt-dlp`. The download logic lives in `download_audio.py`. There are no tests, no linter config, no CI, and no backend services.

### System dependencies (pre-installed on snapshot)
- `python3-tk` (required for tkinter)
- `python3.12-venv` (required for venv creation)
- `ffmpeg` (required by yt-dlp for audio extraction)

### Running the app
```bash
source /workspace/.venv/bin/activate
DISPLAY=:1 python3 /workspace/app.py
```

### Key caveats
- **YouTube bot detection**: Downloads from cloud VMs will fail with `Sign in to confirm you're not a bot` unless browser cookies are provided. This is a YouTube/yt-dlp limitation, not an app bug. The app correctly shows the error in its log pane.
- **Tkinter needs a display**: The app requires an X11 display. In cloud VMs, `DISPLAY=:1` is already provided by TigerVNC. Use the Desktop pane or computerUse subagent to interact with the GUI.
- **No automated tests exist**: Validate changes by running core logic in a Python REPL (e.g. `parse_urls`, `detect_bible_book` from `download_audio.py`) and by launching the GUI.
- The venv must include the system `python3-tk` package — use `python3 -m venv .venv` (without `--without-pip` or isolation flags that exclude system packages).
