import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest

import yt_dlp

from downloader import build_options, downloads_folder, ffmpeg_executable, runtime_options, validate_url


class ValidationTests(unittest.TestCase):
    def test_platform_links(self):
        links = {
            "YouTube": "https://youtu.be/example", "Twitter (X)": "https://x.com/user/status/123",
            "Facebook": "https://fb.watch/example/", "Instagram": "https://www.instagram.com/reel/example/",
            "TikTok": "https://vm.tiktok.com/example/",
        }
        for platform, link in links.items():
            with self.subTest(platform=platform):
                self.assertEqual(validate_url(platform, link), link)
        self.assertEqual(validate_url("YouTube", "youtu.be/example"), "https://youtu.be/example")

    def test_invalid_or_mismatched_links(self):
        for link in ("", "https://youtube.com", "https://youtube.com.evil.test/video", "https://evilyoutube.com/video",
                     "https://youtube.com@evil.test/video", "file://youtube.com/video", "https://x.com/u/status/1",
                     "https://youtube.com:bad/watch?v=1", "https://youtube.com/playlist?list=1"):
            with self.subTest(link=link), self.assertRaises(ValueError):
                validate_url("YouTube", link)

    def test_windows_destination_and_runtime(self):
        self.assertTrue(downloads_folder().is_absolute())
        self.assertTrue(Path(ffmpeg_executable()).is_file())
        self.assertTrue(runtime_options(), "YouTube requires a JavaScript runtime")

    def test_worker_reports_validation_error(self):
        app = Path(__file__).resolve().parents[1] / "app.py"
        request = {"platform": "YouTube", "url": "https://x.com/user/status/1", "format": "mp4", "destination": "unused"}
        result = subprocess.run([sys.executable, str(app), "--worker"], input=json.dumps(request) + "\n",
                                capture_output=True, text=True, encoding="utf-8", timeout=15)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["type"], "error")


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class MediaIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="downloader-test-", dir=Path(__file__).resolve().parents[1])
        cls.root = Path(cls.temporary.name)
        cls.ffmpeg = ffmpeg_executable()
        commands = [
            ["-f", "lavfi", "-i", "color=c=0x6251DF:s=160x90:r=10", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100",
             "-t", "1", "-c:v", "mpeg4", "-c:a", "pcm_s16le", str(cls.root / "sample.mkv")],
            ["-f", "lavfi", "-i", "color=c=0x6251DF:s=160x90:r=10", "-t", "1", "-c:v", "libx264", "-an", str(cls.root / "video.mp4")],
            ["-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100", "-t", "1", "-c:a", "aac", str(cls.root / "audio.m4a")],
        ]
        for arguments in commands:
            subprocess.run([cls.ffmpeg, "-y", "-loglevel", "error", *arguments], check=True, capture_output=True, timeout=30)
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(cls.root)))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        cls.temporary.cleanup()

    def download(self, output_format, name, info=None):
        events = []
        destination = self.root / name
        destination.mkdir(exist_ok=True)
        with yt_dlp.YoutubeDL(build_options(output_format, destination, events.append)) as downloader:
            if info:
                downloader.process_ie_result(info, download=True)
            else:
                downloader.extract_info(self.base + "/sample.mkv", download=True)
        files = [Path(e["path"]) for e in events if e["type"] == "file"]
        self.assertEqual(len(files), 1, events)
        self.assertTrue(files[0].is_file())
        self.assertGreater(files[0].stat().st_size, 1000)
        self.assertEqual(files[0].suffix, "." + output_format)
        return files[0]

    def decode(self, path, expected_audio=True, expected_video=False):
        result = subprocess.run([self.ffmpeg, "-hide_banner", "-i", str(path), "-f", "null", "-"],
                                capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual("Audio:" in result.stderr, expected_audio)
        self.assertEqual("Video:" in result.stderr, expected_video)

    def test_mp3_conversion_and_no_overwrite(self):
        path = self.download("mp3", "mp3")
        self.decode(path)
        modified = path.stat().st_mtime_ns
        self.assertEqual(self.download("mp3", "mp3"), path)
        self.assertEqual(path.stat().st_mtime_ns, modified)

    def test_mp4_conversion(self):
        path = self.download("mp4", "mp4")
        self.decode(path, expected_video=True)

    def test_separate_audio_video_merge(self):
        info = {"id": "merge-test", "title": "Café at dawn", "extractor": "test", "webpage_url": self.base,
                "formats": [
                    {"format_id": "video", "url": self.base + "/video.mp4", "ext": "mp4", "vcodec": "h264", "acodec": "none", "height": 90},
                    {"format_id": "audio", "url": self.base + "/audio.m4a", "ext": "m4a", "vcodec": "none", "acodec": "aac"},
                ]}
        path = self.download("mp4", "merge", info)
        self.decode(path, expected_video=True)


if __name__ == "__main__":
    unittest.main()
