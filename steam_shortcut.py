#!/usr/bin/env python3
"""Add or update the Jellyfin non-Steam shortcut so it runs the jellyfin-ally launcher.

Usage: steam_shortcut.py LAUNCHER_PATH [shortcuts.vdf ...]
With no vdf paths, every ~/.local/share/Steam/userdata/*/config/shortcuts.vdf is
used (a userdata/<id>/config dir without one gets a new file).
Steam must NOT be running: it rewrites shortcuts.vdf from memory on exit.
"""
import glob
import os
import shutil
import struct
import sys
import time
import zlib

APP_ID = "org.jellyfin.JellyfinDesktop"
APP_NAME = "Jellyfin Desktop"
ICON = "/var/lib/flatpak/exports/share/icons/hicolor/scalable/apps/org.jellyfin.JellyfinDesktop.svg"


# --- binary VDF ------------------------------------------------------------
def _cstr(data, i):
    j = data.index(b"\x00", i)
    return data[i:j].decode("utf-8", "surrogateescape"), j + 1


def _parse_map(data, i):
    out = []  # keep order: list of (key, value)
    while True:
        t = data[i]
        i += 1
        if t == 0x08:
            return out, i
        key, i = _cstr(data, i)
        if t == 0x00:
            val, i = _parse_map(data, i)
        elif t == 0x01:
            val, i = _cstr(data, i)
        elif t == 0x02:
            val = ("int", struct.unpack_from("<i", data, i)[0])
            i += 4
        else:
            raise ValueError(f"unknown VDF type 0x{t:02x} at {i - 1}")
        out.append((key, val))


def load(path):
    data = open(path, "rb").read()
    root, i = _parse_map(data, 0)
    if i != len(data):
        raise ValueError(f"trailing bytes in {path}")
    return root


def _dump_map(items):
    b = bytearray()
    for key, val in items:
        k = key.encode("utf-8", "surrogateescape") + b"\x00"
        if isinstance(val, list):
            b += b"\x00" + k + _dump_map(val)
        elif isinstance(val, tuple):
            b += b"\x02" + k + struct.pack("<i", val[1])
        else:
            b += b"\x01" + k + val.encode("utf-8", "surrogateescape") + b"\x00"
    return bytes(b) + b"\x08"


def dump(root):
    return _dump_map(root)


# --- shortcut logic --------------------------------------------------------
def _get(entry, name):
    for k, v in entry:
        if k.lower() == name.lower():
            return v
    return None


def _set(entry, name, value):
    for n, (k, _) in enumerate(entry):
        if k.lower() == name.lower():
            entry[n] = (k, value)
            return
    entry.append((name, value))


def _is_jellyfin(entry, launcher):
    exe = _get(entry, "Exe") or ""
    opts = _get(entry, "LaunchOptions") or ""
    return APP_ID in exe or APP_ID in opts or launcher in exe


def _appid(exe, name):
    crc = zlib.crc32((exe + name).encode()) | 0x80000000
    return ("int", struct.unpack("<i", struct.pack("<I", crc))[0])


def update(path, launcher):
    exe = f'"{launcher}"'
    start_dir = f'"{os.path.dirname(launcher)}/"'
    if os.path.exists(path):
        root = load(path)
        if dump(root) != open(path, "rb").read():
            raise ValueError("round-trip mismatch, refusing to touch " + path)
    else:
        root = [("shortcuts", [])]
    shortcuts = _get(root, "shortcuts")
    if shortcuts is None:
        raise ValueError("no 'shortcuts' map in " + path)

    hits = [v for _, v in shortcuts if isinstance(v, list) and _is_jellyfin(v, launcher)]
    if hits:
        for e in hits:
            _set(e, "Exe", exe)
            _set(e, "StartDir", start_dir)
            _set(e, "LaunchOptions", "")
        action = f"updated {len(hits)} existing shortcut(s)"
    else:
        entry = [
            ("appid", _appid(exe, APP_NAME)),
            ("AppName", APP_NAME),
            ("Exe", exe),
            ("StartDir", start_dir),
            ("icon", ICON if os.path.exists(ICON) else ""),
            ("ShortcutPath", ""),
            ("LaunchOptions", ""),
            ("IsHidden", ("int", 0)),
            ("AllowDesktopConfig", ("int", 1)),
            ("AllowOverlay", ("int", 1)),
            ("OpenVR", ("int", 0)),
            ("Devkit", ("int", 0)),
            ("DevkitGameID", ""),
            ("DevkitOverrideAppID", ("int", 0)),
            ("LastPlayTime", ("int", 0)),
            ("FlatpakAppID", ""),
            ("sortas", ""),
            ("tags", []),
        ]
        idx = max([int(k) for k, _ in shortcuts if k.isdigit()], default=-1) + 1
        shortcuts.append((str(idx), entry))
        action = "added new shortcut"

    if os.path.exists(path):
        shutil.copy2(path, f"{path}.bak-jellyfin-ally-{time.strftime('%Y%m%d%H%M%S')}")
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(dump(root))
    os.replace(tmp, path)
    print(f"{path}: {action}")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    launcher = os.path.abspath(sys.argv[1])
    paths = sys.argv[2:]
    if not paths:
        for cfg in glob.glob(os.path.expanduser("~/.local/share/Steam/userdata/*/config")):
            if os.path.basename(os.path.dirname(cfg)) != "0":
                paths.append(os.path.join(cfg, "shortcuts.vdf"))
    if not paths:
        sys.exit("no Steam userdata found; log in to Steam once first")
    for p in paths:
        update(p, launcher)


if __name__ == "__main__":
    main()
