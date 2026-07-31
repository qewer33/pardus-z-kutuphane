#!/usr/bin/env bash

# Quick .deb builder that works without debhelper. 
# It stages a meson install into a DESTDIR and wraps it with dpkg-deb.

# For a "proper" Debian/Pardus package, build the debian/ dir in a Debian
# container instead (see the README / packaging notes).

set -euo pipefail

cd "$(dirname "$0")/.."

PKG=pardus-z-kutuphane
VERSION=$(dpkg-parsechangelog -SVersion)

builddir=$(mktemp -d)
destdir=$(mktemp -d)

# remove unused files for a manual build 
trap 'rm -rf "$builddir" "$destdir" debian/files' EXIT

echo ">> meson build (prefix=/usr)"
meson setup "$builddir" --prefix=/usr --buildtype=plain >/dev/null
meson compile -C "$builddir" >/dev/null

# DESTDIR install makes meson skip the post-install hooks; we do them in postinst
DESTDIR="$destdir" meson install -C "$builddir" >/dev/null

echo ">> generating control from debian/"
mkdir -p "$destdir/DEBIAN"

dpkg-gencontrol -p"$PKG" -P"$destdir" -Vmisc:Depends=

# refresh schema/icon/desktop caches in postinst
cat > "$destdir/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
if [ "$1" = "configure" ]; then
    glib-compile-schemas /usr/share/glib-2.0/schemas || true
    gtk4-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
    update-desktop-database -q /usr/share/applications || true
fi
EOF
chmod 0755 "$destdir/DEBIAN/postinst"

out="${PKG}_${VERSION}_all.deb"
echo ">> building $out"
fakeroot dpkg-deb --build "$destdir" "$out"
echo ">> done: $out"
dpkg-deb --info "$out" | sed -n '1,20p'
