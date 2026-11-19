# Build two executables sharing one dependency folder. The GUI has no console;
# the worker has redirected standard streams and is started with CREATE_NO_WINDOW.
from pathlib import Path
import importlib.metadata
import os
import shutil
import sys

import imageio_ffmpeg
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, get_package_paths

root = Path(SPECPATH)
runtime = shutil.which('deno') or shutil.which('node')
if not runtime:
    raise RuntimeError('Install Node.js 22 or later, or Deno 2.3 or later, before building.')

_, customtkinter_dir = get_package_paths('customtkinter')
icon = Path(customtkinter_dir) / 'assets' / 'icons' / 'CustomTkinter_icon_Windows.ico'
datas = collect_data_files('customtkinter') + collect_data_files('yt_dlp_ejs')
for dist in importlib.metadata.distributions():
    package = dist.metadata['Name']
    for item in dist.files or []:
        if 'license' in str(item).lower() and dist.locate_file(item).is_file():
            datas.append((str(dist.locate_file(item)), 'licenses/' + package))
node_license = Path(runtime).parent / 'LICENSE'
if node_license.is_file():
    datas.append((str(node_license), 'licenses/javascript-runtime'))
elif Path(runtime).stem.lower() == 'node':
    datas.append((str(root / 'third_party' / 'NODE-LICENSE.txt'), 'licenses/javascript-runtime'))
python_license = Path(sys.base_prefix) / 'LICENSE.txt'
if python_license.is_file():
    datas.append((str(python_license), 'licenses/python'))
datas += [(str(root / filename), '.') for filename in ['README.md', 'THIRD_PARTY.md', 'LICENSE']]

ffmpeg_build = os.environ.get('DOWNLOADER_FFMPEG_BUILD')
if ffmpeg_build:
    ffmpeg_dir = Path(ffmpeg_build).resolve()
    ffmpeg_binary = ffmpeg_dir / 'bin' / 'ffmpeg.exe'
    ffmpeg_licenses = ffmpeg_dir / 'licenses'
    if not ffmpeg_binary.is_file() or not ffmpeg_licenses.is_dir():
        raise RuntimeError('DOWNLOADER_FFMPEG_BUILD must contain bin/ffmpeg.exe and licenses/.')
    datas.append((str(ffmpeg_licenses), 'licenses/ffmpeg'))
else:
    ffmpeg_binary = imageio_ffmpeg.get_ffmpeg_exe()

a = Analysis(
    ['app.py'], pathex=[str(root)],
    binaries=[(str(ffmpeg_binary), 'tools'), (runtime, 'runtime')],
    datas=datas,
    hiddenimports=collect_submodules('yt_dlp') + ['yt_dlp_ejs', 'certifi'],
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False,
)
# Normalize the FFmpeg filename so the app can discover it without imageio imports.
a.binaries = [
    ('tools/ffmpeg.exe' if name.replace('\\', '/').startswith('tools/') and 'ffmpeg' in name else name, src, kind)
    for name, src, kind in a.binaries
    if not name.replace('\\', '/').startswith('imageio_ffmpeg/binaries/')
]
pyz = PYZ(a.pure)
gui = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Downloader',
          debug=False, strip=False, upx=False, console=False, icon=str(icon))
worker = EXE(pyz, a.scripts, [], exclude_binaries=True, name='DownloaderWorker',
             debug=False, strip=False, upx=False, console=True)
bundle = COLLECT(gui, worker, a.binaries, a.datas, strip=False, upx=False, name='Downloader')
