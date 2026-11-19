# Third-party software

The portable build includes third-party software. License notices are kept in
`_internal/licenses` and in the components' metadata directories.

- yt-dlp uses the Unlicense. [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- yt-dlp-ejs uses the Unlicense and includes MIT- and ISC-licensed components. [yt-dlp-ejs](https://github.com/yt-dlp/ejs)
- CustomTkinter uses the MIT License. [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- imageio-ffmpeg uses the BSD 2-Clause License. [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg)
- The FFmpeg license depends on the build configuration. The binary distributed
  by imageio-ffmpeg includes GPL components. Run
  `_internal/tools/ffmpeg.exe -version` to see its configuration.
  [FFmpeg licensing](https://ffmpeg.org/legal.html) · [FFmpeg source](https://ffmpeg.org/download.html)
- If bundled, Node.js uses the MIT License and includes components under their
  own licenses. [Node.js](https://nodejs.org/)
- If bundled, Deno uses the MIT License and includes components under their
  own licenses. [Deno](https://deno.com/)
- Python, Tcl/Tk, PyInstaller, and yt-dlp's dependencies retain their respective
  licenses. The PyInstaller license includes an exception for distributing
  applications built with it.

Before redistributing the portable build publicly, review the licenses of the
bundled binaries and any corresponding source distribution obligations.
