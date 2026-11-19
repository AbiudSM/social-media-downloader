"""Desktop interface. Run with python app.py."""
from __future__ import annotations

import json
import os
from pathlib import Path
import queue
import signal
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

from downloader import PLATFORMS, downloads_folder, validate_url


def worker_command() -> list[str]:
    if getattr(sys, "frozen", False):
        # The engine uses a separate console-mode executable so redirected
        # standard streams remain reliable in a windowed desktop distribution.
        return [str(Path(sys.executable).with_name("DownloaderWorker.exe")), "--worker"]
    return [sys.executable, "-u", str(Path(__file__).resolve()), "--worker"]


def run_gui():
    import customtkinter as ctk
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    accent = "#6251DF"
    ink = "#17213A"
    muted = "#748097"

    class App(ctk.CTk):
        def __init__(self):
            super().__init__()
            if os.name == "nt":
                icon = Path(ctk.__file__).with_name("assets") / "icons" / "CustomTkinter_icon_Windows.ico"
                self.iconbitmap(str(icon))
            self.title("Downloader · Video and audio")
            self.geometry("1020x790")
            self.minsize(920, 760)
            self.configure(fg_color="#F4F5FA")
            self.platform = "YouTube"
            self.format = "mp4"
            self.cookies = ""
            self.destination = downloads_folder()
            self.events = queue.Queue()
            self.process = None
            self.busy = False
            self.cancelled = False
            self.last_file = ""
            self.last_warning = ""
            self.details = ""
            self.controls = []
            self.platform_buttons = {}
            self.format_buttons = {}
            self.grid_columnconfigure(1, weight=1)
            self.grid_rowconfigure(0, weight=1)
            self.create_sidebar()
            self.create_content()
            self.select_platform("YouTube")
            self.select_format("mp4")
            self.protocol("WM_DELETE_WINDOW", self.close)
            self.bind("<Return>", lambda _: self.start_download() if not self.busy else None)
            self.after(100, self.poll)

        def label(self, parent, text, size=14, color=ink, bold=False, **kwargs):
            return ctk.CTkLabel(parent, text=text, text_color=color,
                                font=("Segoe UI", size, "bold" if bold else "normal"), **kwargs)

        def create_sidebar(self):
            side = ctk.CTkFrame(self, width=222, corner_radius=0, fg_color="#171C32")
            side.grid(row=0, column=0, sticky="nsew")
            side.grid_propagate(False)
            self.label(side, "↓", 40, "#AFA5FF", True).pack(anchor="w", padx=27, pady=(29, 0))
            self.label(side, "Downloader", 24, "white", True).pack(anchor="w", padx=27)
            self.label(side, "Platform", 11, "#A6AEC7", True).pack(anchor="w", padx=25, pady=(25, 12))
            symbols = {"YouTube": "▶", "Twitter (X)": "X", "Facebook": "f", "Instagram": "◎", "TikTok": "♪"}
            for name in PLATFORMS:
                button = ctk.CTkButton(side, text=f"{symbols[name]}     {name}", anchor="w", height=47,
                                       corner_radius=9, font=("Segoe UI", 14), hover_color="#323952",
                                       command=lambda p=name: self.select_platform(p))
                button.pack(fill="x", padx=16, pady=4)
                self.platform_buttons[name] = button
                self.controls.append(button)

        def create_content(self):
            body = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0,
                                           scrollbar_button_color="#D4D7E5")
            body.grid(row=0, column=1, sticky="nsew", padx=28, pady=20)
            self.label(body, "Download a video", 29, ink, True).pack(anchor="w", pady=(5, 16))

            card = ctk.CTkFrame(body, fg_color="white", corner_radius=16, border_width=1, border_color="#E7EAF2")
            card.pack(fill="x")
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=23, pady=16)
            self.url_label = self.label(inner, "Video URL", 11, muted, True)
            self.url_label.pack(anchor="w")
            row = ctk.CTkFrame(inner, fg_color="transparent")
            row.pack(fill="x", pady=(10, 5))
            self.url = ctk.CTkEntry(row, height=47, corner_radius=9, border_color="#E1E5EF",
                                  fg_color="#FAFBFE", text_color=ink, font=("Segoe UI", 13))
            self.url.pack(side="left", fill="x", expand=True)
            paste = ctk.CTkButton(row, text="Paste", width=68, height=45, fg_color="#EFEDFF",
                                 text_color=accent, hover_color="#E4E0FF", command=self.paste)
            paste.pack(side="left", padx=(9, 0))
            self.controls.extend([self.url, paste])
            self.hint = self.label(inner, "", 11, muted)
            self.hint.pack(anchor="w")
            self.label(inner, "Download format", 11, muted, True).pack(anchor="w", pady=(16, 11))
            formats = ctk.CTkFrame(inner, fg_color="transparent")
            formats.pack(fill="x")
            for value, title in [("mp4", "▶   MP4 · Video\nVideo and audio"), ("mp3", "♪   MP3 · Audio\nAudio only · 192 kbps")]:
                button = ctk.CTkButton(formats, text=title, height=70, corner_radius=10,
                                      border_width=2, font=("Segoe UI", 14),
                                      command=lambda f=value: self.select_format(f))
                button.pack(side="left", fill="x", expand=True, padx=(0, 6) if value == "mp4" else (6, 0))
                self.format_buttons[value] = button
                self.controls.append(button)

            destination = ctk.CTkFrame(inner, fg_color="#F6F7FB", corner_radius=9)
            destination.pack(fill="x", pady=(16, 10))
            self.label(destination, "↓   Save to Downloads", 13, ink, True).pack(anchor="w", padx=13, pady=(9, 0))
            self.label(destination, str(self.destination), 11, muted, wraplength=520, justify="left").pack(anchor="w", padx=13, pady=(0, 9))
            options = ctk.CTkFrame(inner, fg_color="transparent")
            options.pack(fill="x")
            cookie_button = ctk.CTkButton(options, text="Cookies (optional)", height=26, width=130,
                                         fg_color="transparent", text_color=muted, hover_color="#F0F1F7",
                                         font=("Segoe UI", 11), command=self.choose_cookies)
            cookie_button.pack(side="left")
            self.cookies_label = self.label(options, "For videos that require signing in", 10, muted)
            self.cookies_label.pack(side="left", padx=8)
            self.controls.append(cookie_button)
            self.download_button = ctk.CTkButton(inner, text="↓   Download MP4", height=48,
                                                  corner_radius=10, fg_color=accent, hover_color="#5141CA",
                                                  font=("Segoe UI", 15, "bold"), command=self.start_download)
            self.download_button.pack(fill="x", pady=(12, 0))

            status = ctk.CTkFrame(body, fg_color="transparent")
            status.pack(fill="x", pady=(14, 4))
            top = ctk.CTkFrame(status, fg_color="transparent")
            top.pack(fill="x")
            self.status_label = self.label(top, "Ready to download", 13, ink, True)
            self.status_label.pack(side="left")
            self.percent_label = self.label(top, "", 12, accent, True)
            self.percent_label.pack(side="right")
            self.progress = ctk.CTkProgressBar(status, height=7, progress_color=accent, fg_color="#E3E6F1")
            self.progress.pack(fill="x", pady=(10, 7))
            self.progress.set(0)
            self.status_detail = self.label(status, "", 11, muted,
                                           wraplength=640, justify="left", anchor="w")
            self.status_detail.pack(fill="x")
            actions = ctk.CTkFrame(status, fg_color="transparent")
            actions.pack(fill="x", pady=(9, 0))
            self.cancel_button = ctk.CTkButton(actions, text="Cancel", width=92, height=29,
                                               fg_color="#E8EAF3", hover_color="#DCE0ED", text_color=ink,
                                               state="disabled", command=self.cancel)
            self.cancel_button.pack(side="left")
            self.detail_button = ctk.CTkButton(actions, text="View details", width=92, height=29,
                                               fg_color="transparent", hover_color="#E8EAF3", text_color=muted,
                                               state="disabled", command=self.show_details)
            self.detail_button.pack(side="left", padx=6)
            ctk.CTkButton(actions, text="Open Downloads  ↗", width=145, height=29,
                          fg_color="transparent", text_color=accent, hover_color="#E8E5FC",
                          command=self.open_downloads).pack(side="right")

        def select_platform(self, platform):
            if self.busy:
                return
            self.platform = platform
            for name, button in self.platform_buttons.items():
                button.configure(fg_color="#6251DF" if name == platform else "transparent",
                                 text_color="white" if name == platform else "#BAC2D9")
            if hasattr(self, "url"):
                examples = {"YouTube": "https://www.youtube.com/watch?v=…", "Twitter (X)": "https://x.com/username/status/…",
                            "Facebook": "https://www.facebook.com/reel/…", "Instagram": "https://www.instagram.com/reel/…",
                            "TikTok": "https://www.tiktok.com/@username/video/…"}
                self.url.configure(placeholder_text=examples[platform])
                self.hint.configure(text=f"Paste a {platform} video link.")

        def select_format(self, value):
            if self.busy:
                return
            self.format = value
            for name, button in self.format_buttons.items():
                button.configure(fg_color="#F0EDFF" if name == value else "#FAFBFE",
                                 border_color=accent if name == value else "#E7EAF2",
                                 text_color=accent if name == value else muted,
                                 hover_color="#EAE6FF")
            self.download_button.configure(text=f"↓   Download {value.upper()}")

        def paste(self):
            try:
                text = self.clipboard_get().strip()
                self.url.delete(0, "end")
                self.url.insert(0, text)
            except tk.TclError:
                self.set_status("The clipboard contains no text.", error=True)

        def choose_cookies(self):
            path = filedialog.askopenfilename(title="Select a Netscape cookies file",
                                               filetypes=[("Cookies files", "*.txt"), ("All files", "*.*")])
            if path:
                self.cookies = path
                self.cookies_label.configure(text=Path(path).name)
            elif self.cookies and messagebox.askyesno("Cookies", "Remove the selected cookies file?"):
                self.cookies = ""
                self.cookies_label.configure(text="For videos that require signing in")

        def set_status(self, text, detail="", error=False):
            self.status_label.configure(text=text, text_color="#C24C57" if error else ink)
            self.status_detail.configure(text=detail)

        def set_busy(self, busy):
            self.busy = busy
            for widget in self.controls:
                widget.configure(state="disabled" if busy else "normal")
            self.download_button.configure(state="disabled" if busy else "normal")
            self.cancel_button.configure(state="normal" if busy else "disabled")
            if not busy:
                self.progress.stop()
                self.progress.configure(mode="determinate")

        def start_download(self):
            if self.busy:
                return
            try:
                url = validate_url(self.platform, self.url.get())
            except ValueError as error:
                self.set_status("Check the link", str(error), error=True)
                self.url.focus_set()
                return
            self.last_file = ""
            self.last_warning = ""
            self.details = ""
            self.cancelled = False
            self.detail_button.configure(state="disabled")
            request = {"platform": self.platform, "url": url, "format": self.format,
                       "destination": str(self.destination), "cookies": self.cookies}
            try:
                kwargs = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True}
                self.process = subprocess.Popen(worker_command(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                                 stderr=subprocess.PIPE, text=True, encoding="utf-8", **kwargs)
                self.process.stdin.write(json.dumps(request) + "\n")
                self.process.stdin.close()
            except (OSError, BrokenPipeError) as error:
                self.set_status("Could not start the download", str(error), error=True)
                return
            self.set_busy(True)
            self.set_status(f"Connecting to {self.platform}…", "Looking up the video and available formats.")
            self.progress.configure(mode="indeterminate")
            self.progress.start()
            self.percent_label.configure(text="")
            threading.Thread(target=self.read_worker, args=(self.process,), daemon=True).start()

        def read_worker(self, process):
            errors = []
            def read_errors():
                for line in process.stderr:
                    errors.append(line)
                    if len(errors) > 100:
                        errors.pop(0)
            stderr_thread = threading.Thread(target=read_errors, daemon=True)
            stderr_thread.start()
            try:
                for line in process.stdout:
                    try:
                        self.events.put(json.loads(line))
                    except json.JSONDecodeError:
                        continue
                code = process.wait()
                stderr_thread.join(timeout=2)
                self.events.put({"type": "exited", "code": code, "detail": "".join(errors)})
            finally:
                process.stdout.close()
                process.stderr.close()

        def poll(self):
            try:
                while True:
                    event = self.events.get_nowait()
                    kind = event.get("type")
                    if self.cancelled and kind != "exited":
                        continue
                    if kind == "progress":
                        fraction = event.get("fraction")
                        if fraction is not None:
                            self.progress.stop()
                            self.progress.configure(mode="determinate")
                            self.progress.set(fraction)
                            self.percent_label.configure(text=f"{fraction:.0%}")
                        else:
                            self.progress.configure(mode="indeterminate")
                            self.progress.start()
                            self.percent_label.configure(text="")
                        speed = event.get("speed")
                        eta = event.get("eta")
                        parts = [f"{event.get('downloaded', 0) / 1048576:.1f} MB"]
                        if speed:
                            parts.append(f"{speed / 1048576:.1f} MB/s")
                        if eta is not None:
                            parts.append(f"{int(eta) // 60}:{int(eta) % 60:02d} remaining")
                        self.set_status("Downloading…", " · ".join(parts))
                    elif kind == "processing":
                        self.progress.configure(mode="indeterminate")
                        self.progress.start()
                        self.percent_label.configure(text="")
                        self.set_status(event["message"])
                    elif kind == "file":
                        self.last_file = event["path"]
                    elif kind == "warning":
                        self.last_warning = event["message"]
                    elif kind == "error":
                        self.details = event.get("detail", "")
                        self.detail_button.configure(state="normal")
                        self.set_status("Download failed", event["message"], error=True)
                    elif kind == "complete":
                        if self.last_file and Path(self.last_file).is_file():
                            self.set_status("Download complete", Path(self.last_file).name + " · Saved in Downloads")
                            self.progress.stop()
                            self.progress.configure(mode="determinate")
                            self.progress.set(1)
                            self.percent_label.configure(text="100%")
                        else:
                            self.details = self.last_warning or "The download engine did not report a finished file."
                            self.detail_button.configure(state="normal")
                            self.set_status("No file was created", "Try a direct link to a single video.", error=True)
                    elif kind == "exited":
                        if self.cancelled:
                            self.set_status("Download canceled", "Retry the same link to resume from any partial files.")
                            self.progress.set(0)
                            self.percent_label.configure(text="")
                        elif event["code"] and not self.details:
                            self.details = event["detail"] or self.last_warning or "The download process exited without reporting an error."
                            self.detail_button.configure(state="normal")
                            self.set_status("Download interrupted", "Check the details and try again.", error=True)
                        self.process = None
                        self.set_busy(False)
            except queue.Empty:
                pass
            self.after(100, self.poll)

        def stop_process(self, process):
            if process and process.poll() is None:
                if os.name == "nt":
                    result = subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                            capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    if result.returncode and process.poll() is None:
                        process.kill()
                else:
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass

        def cancel(self):
            if not self.busy or self.cancelled:
                return
            self.cancelled = True
            self.cancel_button.configure(state="disabled")
            self.set_status("Canceling…", "Stopping the download and conversion.")
            threading.Thread(target=self.stop_process, args=(self.process,), daemon=True).start()

        def open_downloads(self):
            try:
                self.destination.mkdir(parents=True, exist_ok=True)
                if os.name == "nt":
                    os.startfile(self.destination)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", str(self.destination)])
                else:
                    subprocess.Popen(["xdg-open", str(self.destination)])
            except OSError as error:
                messagebox.showerror("Downloads", str(error))

        def show_details(self):
            messagebox.showinfo("Download details", self.details or self.last_warning or "No additional details.")

        def close(self):
            if self.busy and not messagebox.askyesno("Close Downloader", "Cancel the current download and close Downloader?"):
                return
            self.stop_process(self.process)
            self.destroy()

    return App()


if __name__ == "__main__":
    if "--worker" in sys.argv:
        from downloader import worker_main
        raise SystemExit(worker_main())
    run_gui().mainloop()
