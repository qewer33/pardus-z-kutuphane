#!/usr/bin/env bash

meson setup --reconfigure build --prefix="$(pwd)/prefix" --datadir="data"
meson compile -C build
meson install -C build

./prefix/bin/pardus-z-kutuphane
