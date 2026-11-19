# Third-party software

The portable build includes third-party software. License notices are kept in
`_internal/licenses` and in the components' metadata directories.

- yt-dlp uses the Unlicense. [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- yt-dlp-ejs uses the Unlicense and includes MIT- and ISC-licensed components. [yt-dlp-ejs](https://github.com/yt-dlp/ejs)
- CustomTkinter uses the MIT License. [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- imageio-ffmpeg uses the BSD 2-Clause License. [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg)
- The v1.0.0 installer includes FFmpeg 9.0.2 with x264 and LAME under GPLv3 or
  later. Its license files are in `_internal/licenses/ffmpeg`. Run
  `_internal/tools/ffmpeg.exe -version` to see its configuration.
  [Corresponding source archive](https://github.com/AbiudSM/social-media-downloader/releases/download/v1.0.0/Downloader-FFmpeg-Source-1.0.0.tar.gz) · [FFmpeg licensing](https://ffmpeg.org/legal.html)
- If bundled, Node.js uses the MIT License and includes components under their
  own licenses. [Node.js](https://nodejs.org/)
- If bundled, Deno uses the MIT License and includes components under their
  own licenses. [Deno](https://deno.com/)
- Python, Tcl/Tk, PyInstaller, and yt-dlp's dependencies retain their respective
  licenses. The PyInstaller license includes an exception for distributing
  applications built with it.

## Build the FFmpeg used in v1.0.0

Extract the corresponding source archive and open its top-level directory in
Git Bash on Windows x64. Add [GNU Make from MSYS2](https://packages.msys2.org/packages/make),
the `bin` directory of [w64devkit 2.11.0](https://github.com/skeeto/w64devkit/releases/tag/v2.11.0),
and the directory containing [NASM 3.01](https://www.nasm.us/pub/nasm/releasebuilds/3.01/win64/)
to `PATH` in that order. Run `bash build-ffmpeg.sh`. The script places the binary
and license notices in `local/`.

Local builds use the binary from imageio-ffmpeg by default. That binary has a
different configuration and its own corresponding source requirements.
