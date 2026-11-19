# Downloader

Downloader is a Windows desktop app that saves a video from YouTube, Twitter (X),
Facebook, Instagram, or TikTok as **MP4** or **MP3**.

## Install on Windows x64

Open **`Downloader-Setup-1.0.0-x64.exe`** and follow the setup wizard. Setup
works offline, includes all runtime dependencies, and installs for the current
user without administrator permissions. You can open Downloader when setup
finishes or find it in the Start menu. The wizard also offers an optional
desktop shortcut.

To uninstall, open **Settings > Apps > Installed apps**, find **Downloader**,
and choose **Uninstall**. Your downloaded media remains in Downloads.

## Run and use Downloader

From a fresh copy of the source, install Python 3.10 or later with Tkinter and pip.
For YouTube, install Node.js 22 or later or Deno 2.3 or later and make it available
on PATH. Double-click **`Start.cmd`**. On the first launch, the script creates
a local virtual environment and installs the dependencies, including FFmpeg.

1. Select a platform in the sidebar.
2. Paste the video or post URL.
3. Choose **MP4** for video and audio or **MP3** for audio only.
4. Click **Download MP4** or **Download MP3**.

Downloader saves files to the Downloads folder configured in Windows, including
folders that have been moved. Click **Open Downloads** to view the files.

The app downloads one video at a time. It uses the best available quality for
the selected format and converts MP3 audio at 192 kbps. Conversion cannot
improve the source quality. **Cancel** stops the download and conversion.
File names include the video title and ID. Existing files are preserved, and
retrying the same link can resume from partial files.

## Videos that require signing in

Some posts require a valid session. Click **Cookies (optional)** and select a
Netscape-format cookies file, such as `cookies.txt`. To clear the selection, click
the button again, cancel the file picker, and confirm removal. Keep your cookies
file private.

Downloads depend on platform availability, regional restrictions, and access
to the post. Downloader cannot bypass DRM or access private content without
authorization. [yt-dlp supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)

## Run from PowerShell

From the project folder, create the environment and start the application:

```powershell
python -m venv --without-pip .venv
python -m pip --python .venv/Scripts/python.exe install -r requirements.txt
.venv/Scripts/python.exe app.py
```

## Build the portable app

Close Downloader and double-click **`Build.cmd`**. The script installs or updates
the dependencies and builds `dist/Downloader/Downloader.exe` with PyInstaller.
The build requires Node.js 22 or later or Deno 2.3 or later on PATH. The
`yt-dlp[default]` dependency installs the downloader and its matching EJS package.

The equivalent PowerShell commands, after creating the environment above, are:

```powershell
python -m pip --python .venv/Scripts/python.exe install --upgrade -r requirements.txt "pyinstaller>=6.16"
.venv/Scripts/python.exe -m PyInstaller --noconfirm --clean Downloader.spec
```

`Start.cmd` opens the portable build when it is available. To run it on another
Windows x64 PC, copy the entire `dist/Downloader` folder, including `_internal`
and `DownloaderWorker.exe`. Open `Downloader.exe` on that PC. The bundle includes
Python, FFmpeg, and a JavaScript runtime.

## Build the Windows installer

From a clean source copy on Windows x64, build the portable app with `Build.cmd`
using x64 Python and an x64 JavaScript runtime. Install [Inno Setup 6](https://jrsoftware.org/inno-setup/downloads#6)
and run `BuildInstaller.cmd` from PowerShell or Command Prompt. If the compiler
is in a custom folder, set the `ISCC` environment variable to its full path
before running the script:

```powershell
$env:ISCC = 'C:\Path\To\Inno Setup 6\ISCC.exe'
.\BuildInstaller.cmd
```

The single-file installer is generated at `dist/Downloader-Setup-1.0.0-x64.exe`.
The installer is unsigned, so Windows may show a SmartScreen warning if it was
downloaded from the internet. Before publishing it, review the distribution
requirements for the bundled components in [THIRD_PARTY.md](THIRD_PARTY.md).

## Run tests

With the source dependencies and JavaScript runtime installed, run:

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

The tests use synthetic media served over local HTTP. They cover URL validation,
the worker protocol, MP3 and MP4 conversion, merging audio and video tracks,
and retrying without overwriting an existing file. They do not use social media
accounts or download real posts.

## Project files

- `app.py` contains the desktop interface and manages the download worker.
- `downloader.py` validates URLs, locates Downloads, and configures yt-dlp and FFmpeg.
- `Downloader.spec` defines the portable Windows build.
- `Downloader.iss` defines the Windows installer and its version.
- `requirements.txt` declares runtime dependencies. `requirements-lock.txt` records the versions used for the portable build.
- [THIRD_PARTY.md](THIRD_PARTY.md) lists bundled components and their licenses.
