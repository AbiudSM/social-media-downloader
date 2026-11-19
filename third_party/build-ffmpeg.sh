#!/usr/bin/env bash
set -euo pipefail

# Run from the extracted release source archive in Git Bash on Windows x64.
# Put MSYS2 GNU Make 4.4.1, w64devkit 2.11.0 bin, and NASM 3.01 on PATH first.
root="$(pwd -W)"
prefix="$root/local"
jobs="${NUMBER_OF_PROCESSORS:-4}"
target=x86_64-w64-mingw32
x264=x264-31e19f92f00c7003fa115047ce50978bc98c3a0d

tar -xf lame-3.100.tar.gz
tar -xf "$x264.tar.gz"
tar -xf ffmpeg-9.0.2.tar.xz

(
    cd lame-3.100
    CONFIG_SHELL=/usr/bin/bash ./configure --build="$target" --host="$target" --prefix="$prefix" \
        --enable-static --disable-shared --disable-frontend --disable-decoder --disable-nasm
    make -j"$jobs"
    make install
)

(
    cd "$x264"
    ./configure --host="$target" --prefix="$prefix" --enable-static \
        --disable-cli --disable-lavf --disable-swscale --disable-ffms --disable-gpac --disable-lsmash
    make -j"$jobs"
    make install-lib-static
)

mkdir -p ffmpeg-build
(
    cd ffmpeg-build
    PKG_CONFIG_LIBDIR="$prefix/lib/pkgconfig" ../ffmpeg-9.0.2/configure \
        --prefix=../local --arch=x86_64 --target-os=mingw32 \
        --disable-autodetect --disable-debug --disable-doc --disable-ffplay --disable-ffprobe \
        --enable-gpl --enable-version3 --enable-schannel --enable-w32threads \
        --enable-libx264 --enable-libmp3lame --pkg-config-flags=--static \
        --extra-cflags=-I../local/include --extra-ldflags='-L../local/lib -static'
    make -j"$jobs" "ECFLAGS=-ffile-prefix-map=$root=."
)

mkdir -p "$prefix/bin" "$prefix/licenses"
cp ffmpeg-build/ffmpeg.exe "$prefix/bin/ffmpeg.exe"
cp ffmpeg-9.0.2/COPYING.GPLv3 "$prefix/licenses/FFmpeg-GPLv3.txt"
cp ffmpeg-9.0.2/LICENSE.md "$prefix/licenses/FFmpeg-LICENSE.md"
cp lame-3.100/COPYING "$prefix/licenses/LAME-LGPL.txt"
cp "$x264/COPYING" "$prefix/licenses/x264-GPL.txt"
