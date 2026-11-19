@echo off
setlocal
cd /d "%~dp0"

set "bundle=dist\Downloader"
for %%F in (
    Downloader.exe
    DownloaderWorker.exe
    _internal\base_library.zip
    _internal\customtkinter\assets\icons\CustomTkinter_icon_Windows.ico
    _internal\python3*.dll
    _internal\tools\ffmpeg.exe
    _internal\yt_dlp_ejs
    _internal\licenses
    _internal\THIRD_PARTY.md
) do if not exist "%bundle%\%%F" (
    echo The portable build is incomplete. Missing: %bundle%\%%F 1>&2
    goto :missing_bundle
)
if not exist "%bundle%\_internal\runtime\node.exe" if not exist "%bundle%\_internal\runtime\deno.exe" (
    echo The portable build is missing its JavaScript runtime. 1>&2
    goto :missing_bundle
)

if not defined ISCC for /f "delims=" %%I in ('where ISCC.exe 2^>nul') do if not defined ISCC set "ISCC=%%I"
if not defined ISCC if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
    echo Inno Setup 6 compiler was not found. Install Inno Setup 6 or set ISCC to the full path of ISCC.exe. 1>&2
    exit /b 1
)

"%ISCC%" "%~dp0Downloader.iss"
if errorlevel 1 (
    echo The installer build failed. See the compiler output above. 1>&2
    exit /b 1
)
exit /b 0

:missing_bundle
echo Run Build.cmd before building the installer. 1>&2
exit /b 1
