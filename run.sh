#!/usr/bin/env bash

meson setup build --prefix="$(pwd)/prefix" --datadir="data"
meson compile -C build
meson install -C build

./prefix/bin/pardus-z-kutuphane
