"""Download audio from YouTube URLs using yt-dlp."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable

try:
    import certifi  # type: ignore
except Exception:  # pragma: no cover
    certifi = None  # type: ignore

# Matches youtube.com/watch?... and youtu.be/... (stops at whitespace)
_YOUTUBE_URL_RE = re.compile(
    r"https?://(?:www\.)?(?:youtube\.com/watch\?[^\s]+|youtu\.be/[^\s]+)",
    re.IGNORECASE,
)


def parse_urls(raw: str) -> list[str]:
    """Extract YouTube URLs from pasted text; preserve order, dedupe."""
    seen: set[str] = set()
    out: list[str] = []
    for m in _YOUTUBE_URL_RE.finditer(raw):
        url = m.group(0).rstrip(").,]}\"'")
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


LogFn = Callable[[str], None]

_BIBLE_BOOKS_ORDERED = [
    "Genesis",
    "Exodus",
    "Leviticus",
    "Numbers",
    "Deuteronomy",
    "Joshua",
    "Judges",
    "Ruth",
    "1 Samuel",
    "2 Samuel",
    "1 Kings",
    "2 Kings",
    "1 Chronicles",
    "2 Chronicles",
    "Ezra",
    "Nehemiah",
    "Esther",
    "Job",
    "Psalms",
    "Proverbs",
    "Ecclesiastes",
    "Song of Solomon",
    "Isaiah",
    "Jeremiah",
    "Lamentations",
    "Ezekiel",
    "Daniel",
    "Hosea",
    "Joel",
    "Amos",
    "Obadiah",
    "Jonah",
    "Micah",
    "Nahum",
    "Habakkuk",
    "Zephaniah",
    "Haggai",
    "Zechariah",
    "Malachi",
    "Matthew",
    "Mark",
    "Luke",
    "John",
    "Acts",
    "Romans",
    "1 Corinthians",
    "2 Corinthians",
    "Galatians",
    "Ephesians",
    "Philippians",
    "Colossians",
    "1 Thessalonians",
    "2 Thessalonians",
    "1 Timothy",
    "2 Timothy",
    "Titus",
    "Philemon",
    "Hebrews",
    "James",
    "1 Peter",
    "2 Peter",
    "1 John",
    "2 John",
    "3 John",
    "Jude",
    "Revelation",
]

def bible_books_ordered() -> list[str]:
    return list(_BIBLE_BOOKS_ORDERED)


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip()).lower()


def detect_bible_book(title: str) -> str | None:
    """Try to detect a Bible book name from a video title."""
    t = _normalize(title)
    t = t.replace("psalm", "psalms")  # common singular/plural mismatch
    t = t.replace("song of songs", "song of solomon")

    def has(word: str) -> bool:
        return f" {word} " in f" {t} "

    # Handle numeric books with a few common variants.
    numeric_variants = [
        ("1 samuel", ["1 samuel", "i samuel", "first samuel"]),
        ("2 samuel", ["2 samuel", "ii samuel", "second samuel"]),
        ("1 kings", ["1 kings", "i kings", "first kings"]),
        ("2 kings", ["2 kings", "ii kings", "second kings"]),
        ("1 chronicles", ["1 chronicles", "i chronicles", "first chronicles"]),
        ("2 chronicles", ["2 chronicles", "ii chronicles", "second chronicles"]),
        ("1 corinthians", ["1 corinthians", "i corinthians", "first corinthians"]),
        ("2 corinthians", ["2 corinthians", "ii corinthians", "second corinthians"]),
        ("1 thessalonians", ["1 thessalonians", "i thessalonians", "first thessalonians"]),
        ("2 thessalonians", ["2 thessalonians", "ii thessalonians", "second thessalonians"]),
        ("1 timothy", ["1 timothy", "i timothy", "first timothy"]),
        ("2 timothy", ["2 timothy", "ii timothy", "second timothy"]),
        ("1 peter", ["1 peter", "i peter", "first peter"]),
        ("2 peter", ["2 peter", "ii peter", "second peter"]),
        ("1 john", ["1 john", "i john", "first john"]),
        ("2 john", ["2 john", "ii john", "second john"]),
        ("3 john", ["3 john", "iii john", "third john"]),
    ]
    for canonical, vars_ in numeric_variants:
        for v in vars_:
            if has(v):
                # Return canonical formatting as used in our ordered list.
                for b in _BIBLE_BOOKS_ORDERED:
                    if _normalize(b) == canonical:
                        return b

    # Non-numeric direct matches.
    for b in _BIBLE_BOOKS_ORDERED:
        nb = _normalize(b)
        if has(nb):
            return b

    return None


def _yt_dlp_env() -> dict[str, str]:
    env = os.environ.copy()
    if certifi is not None:
        cafile = certifi.where()
        env.setdefault("SSL_CERT_FILE", cafile)
        env.setdefault("REQUESTS_CA_BUNDLE", cafile)
    return env


def get_title(url: str) -> str | None:
    """Fetch video title (best-effort) without downloading media."""
    cmd = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--no-playlist",
        "--no-warnings",
        "--print",
        "%(title)s",
        url,
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_yt_dlp_env(),
    )
    if proc.returncode != 0:
        return None
    title = proc.stdout.strip()
    return title or None


def download_one(
    url: str,
    output_dir: Path,
    *,
    index: int | None = None,
    title_override: str | None = None,
    audio_format: str = "m4a",
    log: LogFn | None = None,
) -> int:
    """Run yt-dlp for a single URL. Returns subprocess return code."""
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{index:02d} - " if index is not None else ""
    template = str(output_dir / f"{prefix}%(title)s.%(ext)s")
    if title_override:
        template = str(output_dir / f"{prefix}{title_override}.%(ext)s")

    cmd = [
        sys.executable,
        "-m",
        "yt_dlp",
        "-x",
        "--audio-format",
        audio_format,
        "--audio-quality",
        "0",
        "-o",
        template,
        "--windows-filenames",
        "--no-playlist",
        "--newline",
        "--no-colors",
        url,
    ]

    env = _yt_dlp_env()

    if log:
        log(f"Starting: {url}\n")

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )

    if proc.stdout and log:
        log(proc.stdout)
    if proc.stderr and log:
        log(proc.stderr)

    if log:
        log(f"Exit code: {proc.returncode}\n")

    return proc.returncode


def download_all(
    urls: list[str],
    output_dir: Path,
    *,
    start_index: int = 1,
    rename_to_bible_book: bool = False,
    audio_format: str = "m4a",
    log: LogFn | None = None,
) -> list[tuple[str, int]]:
    """Download each URL sequentially. Returns (url, returncode) pairs."""
    results: list[tuple[str, int]] = []
    for i, url in enumerate(urls, start=start_index):
        title_override = None
        if rename_to_bible_book:
            title = get_title(url)
            if title:
                book = detect_bible_book(title)
                if book:
                    title_override = book
                    if log:
                        log(f"Detected book: {book} (from title: {title})\n")

        code = download_one(
            url,
            output_dir,
            index=i,
            title_override=title_override,
            audio_format=audio_format,
            log=log,
        )
        results.append((url, code))
    return results
