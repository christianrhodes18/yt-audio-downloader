#!/usr/bin/env python3
"""Simple GUI: paste YouTube links, download audio (m4a) named from video titles."""

from __future__ import annotations

import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from download_audio import bible_books_ordered, download_one, parse_urls

DEFAULT_DIR = Path(__file__).resolve().parent / "downloads"
DEFAULT_SUBFOLDER = "Downloads"
CATEGORIES = ["Generic", "Bible", "Motivational", "Tutorials", "Playlists"]


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("YouTube → audio (yt-dlp)")
        self.minsize(520, 480)
        self.output_dir = DEFAULT_DIR

        self._build()
        self._set_folder_label()
        self._sync_category_ui()
        self._apply_system_theme()

    def _build(self) -> None:
        pad = {"padx": 10, "pady": 6}

        frm_top = ttk.Frame(self)
        frm_top.pack(fill=tk.X, **pad)

        ttk.Label(frm_top, text="Save audio to:").pack(side=tk.LEFT)
        self.lbl_folder = ttk.Label(frm_top, text="", width=50)
        self.lbl_folder.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        ttk.Button(frm_top, text="Choose folder…", command=self._pick_folder).pack(
            side=tk.RIGHT
        )

        frm_opts = ttk.Frame(self)
        frm_opts.pack(fill=tk.X, padx=10, pady=(0, 6))

        ttk.Label(frm_opts, text="Category:").pack(side=tk.LEFT)
        self.var_category = tk.StringVar(value="Generic")
        self.cmb_category = ttk.Combobox(
            frm_opts,
            textvariable=self.var_category,
            values=CATEGORIES,
            state="readonly",
            width=12,
        )
        self.cmb_category.pack(side=tk.LEFT, padx=(6, 12))
        self.cmb_category.bind("<<ComboboxSelected>>", lambda _e: self._sync_category_ui())

        ttk.Label(frm_opts, text="Subfolder:").pack(side=tk.LEFT)
        self.var_subfolder = tk.StringVar(value=DEFAULT_SUBFOLDER)
        self._subfolder_last_auto = DEFAULT_SUBFOLDER
        self._subfolder_user_edited = False
        ent_subfolder = ttk.Entry(frm_opts, textvariable=self.var_subfolder, width=18)
        ent_subfolder.pack(
            side=tk.LEFT, padx=(6, 12)
        )
        self.var_subfolder.trace_add("write", lambda *_: self._on_subfolder_change())

        ttk.Label(frm_opts, text="Number prefix starts at:").pack(side=tk.LEFT)
        self.var_start_index = tk.StringVar(value="1")
        ttk.Entry(frm_opts, textvariable=self.var_start_index, width=6).pack(
            side=tk.LEFT, padx=(6, 12)
        )

        self.frm_bible = ttk.Frame(self)
        self.frm_bible.pack(fill=tk.X, padx=10, pady=(0, 6))

        self.var_auto_bible_index = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.frm_bible,
            text="Auto-assign Bible book numbers in order",
            variable=self.var_auto_bible_index,
        ).pack(side=tk.LEFT)

        ttk.Label(self.frm_bible, text="Starting book:").pack(side=tk.LEFT, padx=(12, 0))
        self.books = bible_books_ordered()
        self.var_start_book = tk.StringVar(value=self.books[0])
        ttk.Combobox(
            self.frm_bible,
            textvariable=self.var_start_book,
            values=self.books,
            state="readonly",
            width=22,
        ).pack(side=tk.LEFT, padx=(6, 0))

        ttk.Label(
            self,
            text="Paste YouTube URLs (any mix of lines; multiple URLs per line is fine):",
        ).pack(anchor=tk.W, padx=10, pady=(4, 0))

        self.txt_urls = scrolledtext.ScrolledText(self, height=12, wrap=tk.WORD)
        self.txt_urls.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        ttk.Label(
            self,
            text="Optional custom filenames (one per URL, line-by-line; without extension):",
        ).pack(anchor=tk.W, padx=10, pady=(0, 0))
        self.txt_names = scrolledtext.ScrolledText(self, height=4, wrap=tk.WORD)
        self.txt_names.pack(fill=tk.X, padx=10, pady=(4, 6))

        frm_btn = ttk.Frame(self)
        frm_btn.pack(fill=tk.X, padx=10, pady=(0, 6))
        self.btn_go = ttk.Button(frm_btn, text="Download audio", command=self._on_download)
        self.btn_go.pack(side=tk.LEFT)
        ttk.Label(
            frm_btn,
            text="Saves as numbered .m4a files. Requires ffmpeg for conversion.",
        ).pack(side=tk.LEFT, padx=(12, 0))

        ttk.Label(self, text="Log:").pack(anchor=tk.W, padx=10)
        self.txt_log = scrolledtext.ScrolledText(self, height=14, wrap=tk.WORD, state=tk.DISABLED)
        self.txt_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    def _set_folder_label(self) -> None:
        self.lbl_folder.configure(text=str(self.output_dir))

    def _pick_folder(self) -> None:
        path = filedialog.askdirectory(initialdir=str(self.output_dir))
        if path:
            self.output_dir = Path(path)
            self._set_folder_label()

    def _log(self, msg: str) -> None:
        def append() -> None:
            self.txt_log.configure(state=tk.NORMAL)
            self.txt_log.insert(tk.END, msg)
            self.txt_log.see(tk.END)
            self.txt_log.configure(state=tk.DISABLED)

        self.after(0, append)

    def _is_macos_dark_mode(self) -> bool:
        if sys.platform != "darwin":
            return False
        try:
            proc = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True,
                text=True,
            )
            return proc.returncode == 0 and "Dark" in (proc.stdout or "")
        except Exception:
            return False

    def _apply_system_theme(self) -> None:
        # Best-effort dark palette on macOS when system is in Dark Mode.
        # Tk doesn't automatically follow the system appearance.
        if not self._is_macos_dark_mode():
            return

        bg = "#1e1e1e"
        fg = "#e6e6e6"
        field_bg = "#2a2a2a"

        try:
            self.configure(background=bg)
            style = ttk.Style(self)
            style.configure("TFrame", background=bg)
            style.configure("TLabel", background=bg, foreground=fg)
            style.configure("TCheckbutton", background=bg, foreground=fg)
            style.configure("TButton", background=bg, foreground=fg)
            style.configure("TEntry", fieldbackground=field_bg, foreground=fg)
            style.configure("TCombobox", fieldbackground=field_bg, foreground=fg)
        except Exception:
            pass

        for w in (self.txt_urls, self.txt_names, self.txt_log):
            try:
                w.configure(
                    background=field_bg,
                    foreground=fg,
                    insertbackground=fg,
                )
            except Exception:
                pass

    def _on_subfolder_change(self) -> None:
        current = self.var_subfolder.get().strip()
        # Mark as user-edited only when they diverge from the last auto-set value.
        if current and current != self._subfolder_last_auto:
            self._subfolder_user_edited = True

    def _set_subfolder_auto(self, value: str) -> None:
        self._subfolder_last_auto = value
        self._subfolder_user_edited = False
        self.var_subfolder.set(value)

    def _sync_category_ui(self) -> None:
        is_bible = self.var_category.get() == "Bible"
        if is_bible:
            self.frm_bible.pack(fill=tk.X, padx=10, pady=(0, 6))
            if not self._subfolder_user_edited:
                self._set_subfolder_auto("Bible")
        else:
            self.frm_bible.pack_forget()
            if not self._subfolder_user_edited:
                self._set_subfolder_auto(self.var_category.get() or DEFAULT_SUBFOLDER)

    def _on_download(self) -> None:
        raw = self.txt_urls.get("1.0", tk.END)
        urls = parse_urls(raw)
        if not urls:
            messagebox.showinfo("No URLs", "No YouTube URLs found in the text.")
            return

        # Optional custom names: one per URL (line-by-line)
        raw_names = self.txt_names.get("1.0", tk.END).splitlines()
        names = [n.strip() for n in raw_names if n.strip() != ""]

        subfolder = self.var_subfolder.get().strip() or DEFAULT_SUBFOLDER
        try:
            start_index = int(self.var_start_index.get().strip() or "1")
        except ValueError:
            messagebox.showerror(
                "Number prefix",
                "Number prefix starts at must be a whole number (e.g. 1).",
            )
            return

        self.btn_go.configure(state=tk.DISABLED)
        self.txt_log.configure(state=tk.NORMAL)
        self.txt_log.delete("1.0", tk.END)
        self.txt_log.configure(state=tk.DISABLED)

        out = self.output_dir / subfolder

        def work() -> None:
            try:
                self._log(f"Found {len(urls)} URL(s). Saving to:\n{out}\n\n")
                bad = 0
                is_bible = self.var_category.get() == "Bible"
                if is_bible and self.var_auto_bible_index.get():
                    try:
                        start_book_idx = self.books.index(self.var_start_book.get())
                    except ValueError:
                        start_book_idx = 0

                    for offset, url in enumerate(urls):
                        book_idx = start_book_idx + offset
                        index = book_idx + 1  # 1-based across whole Bible
                        title_override = None

                        if offset < len(names):
                            title_override = names[offset]
                        elif book_idx < len(self.books):
                            title_override = self.books[book_idx]

                        code = download_one(
                            url,
                            out,
                            index=index,
                            title_override=title_override,
                            audio_format="m4a",
                            log=self._log,
                        )
                        if code != 0:
                            bad += 1
                else:
                    for i, url in enumerate(urls, start=start_index):
                        name_idx = i - start_index
                        title_override = names[name_idx] if name_idx < len(names) else None
                        code = download_one(
                            url,
                            out,
                            index=i,
                            title_override=title_override,
                            audio_format="m4a",
                            log=self._log,
                        )
                        if code != 0:
                            bad += 1

                self._log("\nDone.\n")
                if bad:
                    self.after(
                        0,
                        lambda: messagebox.showwarning(
                            "Finished with errors",
                            f"{bad} of {len(urls)} download(s) failed. Check the log.",
                        ),
                    )
                else:
                    self.after(
                        0,
                        lambda: messagebox.showinfo("Done", f"Saved {len(urls)} file(s) to:\n{out}"),
                    )
            finally:
                self.after(0, lambda: self.btn_go.configure(state=tk.NORMAL))

        threading.Thread(target=work, daemon=True).start()


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
