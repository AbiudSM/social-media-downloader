"""Download engine and JSON worker protocol, independent of the interface."""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
from urllib.parse import urlsplit

PLATFORMS = {
    "YouTube": ("youtube.com", "youtu.be", "youtube-nocookie.com"),
    "Twitter (X)": ("x.com", "twitter.com"),
    "Facebook": ("facebook.com", "fb.watch", "fb.com"),
    "Instagram": ("instagram.com",),
    "TikTok": ("tiktok.com",),
}


def validate_url(platform: str, url: str) -> str:
    url = url.strip()
    if platform not in PLATFORMS:
        raise ValueError("Select a supported platform.")
    if not url:
        raise ValueError("Paste the URL of the video you want to download.")
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        url = "https://" + url
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower().rstrip(".")
        port = parsed.port
    except ValueError:
        raise ValueError("The URL is invalid.") from None
    if parsed.scheme not in ("https", "http") or parsed.username or parsed.password or port not in (None, 80, 443):
        raise ValueError("Enter a valid web link for the video.")
    if not any(host == domain or host.endswith("." + domain) for domain in PLATFORMS[platform]):
        raise ValueError(f"This link does not match {platform}. Change the platform or check the URL.")
    if not parsed.path.strip("/"):
        raise ValueError("Enter a direct link to a video.")
    if platform == "YouTube" and parsed.path.rstrip("/") == "/playlist":
        raise ValueError("Enter a link to a single video.")
    return url


def downloads_folder() -> Path:
    """Resolve the real Windows Downloads known folder, including moved folders."""
    if sys.platform == "win32":
        from ctypes import wintypes

        class GUID(ctypes.Structure):
            _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD),
                        ("Data3", wintypes.WORD), ("Data4", ctypes.c_ubyte * 8)]

        folder_id = GUID(0x374DE290, 0x123F, 0x4565,
                         (ctypes.c_ubyte * 8)(0x91, 0x64, 0x39, 0xC4, 0x92, 0x5E, 0x46, 0x7B))
        pointer = ctypes.c_wchar_p()
        shell = ctypes.windll.shell32.SHGetKnownFolderPath
        shell.argtypes = [ctypes.POINTER(GUID), wintypes.DWORD, wintypes.HANDLE,
                          ctypes.POINTER(ctypes.c_wchar_p)]
        shell.restype = ctypes.c_long
        if shell(ctypes.byref(folder_id), 0, None, ctypes.byref(pointer)) == 0:
            try:
                return Path(pointer.value)
            finally:
                ctypes.windll.ole32.CoTaskMemFree(ctypes.cast(pointer, ctypes.c_void_p))
    return Path.home() / "Downloads"


def runtime_options() -> dict:
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    for runtime in ("deno", "node"):
        bundled = root / "runtime" / (runtime + (".exe" if os.name == "nt" else ""))
        executable = str(bundled) if bundled.is_file() else shutil.which(runtime)
        if executable:
            return {runtime: {"path": executable}}
    return {}


def ffmpeg_executable() -> str:
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    bundled = root / "tools" / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    if bundled.is_file():
        return str(bundled)
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def build_options(output_format: str, destination: Path, emit, cookies: str = "") -> dict:
    if output_format not in ("mp4", "mp3"):
        raise ValueError("Choose MP4 or MP3.")
    last_update = 0.0

    def progress(data):
        nonlocal last_update
        if data["status"] == "finished":
            emit({"type": "processing", "message": "Preparing the file…"})
            return
        if data["status"] != "downloading" or time.monotonic() - last_update < 0.15:
            return
        last_update = time.monotonic()
        total = data.get("total_bytes") or data.get("total_bytes_estimate")
        downloaded = data.get("downloaded_bytes", 0)
        emit({"type": "progress", "fraction": min(downloaded / total, 1) if total else None,
              "downloaded": downloaded, "total": total, "speed": data.get("speed"),
              "eta": data.get("eta"), "title": data.get("info_dict", {}).get("title", "")})

    class Logger:
        def debug(self, message):
            pass

        def warning(self, message):
            emit({"type": "warning", "message": message})

        def error(self, message):
            pass  # The raised DownloadError is reported once by the worker.

    options = {
        "paths": {"home": str(destination)},
        "outtmpl": "%(title).140B [%(id)s].%(ext)s",
        "windowsfilenames": True,
        "noplaylist": True,
        "playlist_items": "1",
        "overwrites": False,
        "final_ext": output_format,
        "continuedl": True,
        "quiet": True,
        "noprogress": True,
        "logger": Logger(),
        "progress_hooks": [progress],
        "postprocessor_hooks": [lambda d: emit({"type": "processing", "message": f"Converting to {output_format.upper()}…"}) if d["status"] == "started" else None],
        "post_hooks": [lambda path: emit({"type": "file", "path": path})],
        "ffmpeg_location": ffmpeg_executable(),
        "js_runtimes": runtime_options(),
        "socket_timeout": 25,
        "retries": 3,
        "fragment_retries": 3,
        "concurrent_fragment_downloads": 3,
        "color": "never",
    }
    if cookies:
        if not Path(cookies).is_file():
            raise ValueError("The selected cookies file could not be found.")
        options["cookiefile"] = cookies
    if output_format == "mp3":
        options.update(format="bestaudio/best", postprocessors=[{
            "key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192",
        }])
    else:
        options.update(
            format="bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b",
            merge_output_format="mp4",
            postprocessors=[{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
        )
    return options


def friendly_error(message: str) -> str:
    message = re.sub(r"\x1b\[[0-9;]*m", "", message)
    lower = message.lower()
    if any(word in lower for word in ("sign in", "login", "log in", "cookies", "private video", "authentication")):
        return "The video is private or requires signing in. If you have access, select a cookies file and try again."
    if any(word in lower for word in ("getaddrinfo", "name resolution", "unable to download webpage", "timed out")):
        return "Could not connect to the platform. Check your connection and try again."
    if "unsupported url" in lower:
        return "This link was not recognized as a video. Try a direct link to the post."
    if any(word in lower for word in ("not available", "unavailable", "removed", "does not exist")):
        return "The video is unavailable. It may have been removed or restricted by account or region."
    return "Could not download the video. Check the link or update Downloader."


def worker_main() -> int:
    # Packaged downloads run in the console-mode worker with redirected streams.
    def emit(event):
        print(json.dumps(event, ensure_ascii=True), flush=True)

    try:
        request = json.loads(sys.stdin.readline())
        url = validate_url(request["platform"], request["url"])
        destination = Path(request["destination"])
        destination.mkdir(parents=True, exist_ok=True)
        import yt_dlp
        options = build_options(request["format"], destination, emit, request.get("cookies", ""))
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(url, download=True)
        if not info:
            raise RuntimeError("The platform did not return a video.")
        emit({"type": "complete"})
        return 0
    except Exception as error:
        emit({"type": "error", "message": friendly_error(str(error)), "detail": str(error)})
        return 1
