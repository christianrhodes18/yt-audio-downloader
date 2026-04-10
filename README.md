# yt-audio-downloader (GUI)

A tiny, local **Tkinter** app that lets you paste YouTube links and download **audio-only** files using **yt-dlp**, saved into a folder with stable, numbered filenames.

This is designed for simple offline listening workflows (e.g., importing into lightweight players like **Bound** on iOS).

<img width="748" height="662" alt="image" src="https://github.com/user-attachments/assets/d1835014-bbb7-4082-9f5e-67cda506d7d8" />

## Features

- Paste a blob of text → it finds `youtube.com` / `youtu.be` URLs automatically
- Downloads **audio-only** and saves as `.m4a` (AAC)
- Creates filenames like `01 - <name>.m4a`, `02 - <name>.m4a`, …
- Optional **custom names** (one per URL, line-by-line)
- Category selector:
  - **Generic / Motivational / Tutorials / Playlists**: simple numbering + optional custom names
  - **Bible**: choose a starting book and auto-assign canonical book order + numbering
- Best-effort macOS **Dark Mode** palette (matches system appearance when possible)

## Requirements

- Python 3.10+ (recommended: 3.12)
- `ffmpeg` (needed for audio extraction/conversion)

## Install

```bash
git clone <your-repo-url>
cd yt-audio-downloader
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Install ffmpeg (macOS):

```bash
brew install ffmpeg
```

### macOS SSL certificate note

If you see an error like `CERTIFICATE_VERIFY_FAILED`, and you installed Python from python.org, run:

- Finder → Applications → Python 3.x → `Install Certificates.command`

Then try again.

## Run

```bash
python app.py
```

## Using the app

1. **Choose folder…** (optional)
2. Pick a **Category**
3. Set **Subfolder** (auto-fills from Category unless you’ve typed a custom value)
4. Set **Number prefix starts at** (this becomes the `01`, `02`, `03` part)
5. Paste URLs into the big text box
6. (Optional) Paste **custom names** (one per URL line, no extension)
7. Click **Download audio**

## iPhone / iOS: offline playback with Bound (recommended)

One easy workflow:

1. Download audio on your Mac into a folder like `Downloads/Bible/`
2. Transfer files to iPhone:
   - **AirDrop** the folder (or a `.zip` of it), or
   - Use **Finder** (USB cable) → iPhone → **Files** tab → drag into the Bound app container (if available), or
   - Use iCloud Drive and download locally in the Files app
3. In **Bound**, use its **Import / Add from Files** option to bring the audio in.

Tip: Bound (and most players) sort nicely when filenames are prefixed like `01 - ...`.

## Notes (legal / terms)

You are responsible for ensuring you have the rights/permission to download and store audio from any URL you provide, and for complying with the platform’s terms of service.

## Development

- Main GUI: `app.py`
- Downloader logic: `download_audio.py`

