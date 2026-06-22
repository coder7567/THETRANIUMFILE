"""
chaos_launcher.pyw
==================
Silent entry point for the chaos program.

IMMEDIATE (before any timer):
  • Changes the desktop wallpaper to assets/background.jpeg

Then waits 5 minutes in total silence before handing off to chaos_main.pyw.
The user will think the script did nothing.  They are wrong.
"""
import subprocess
import sys
import os
import time
import ctypes

# ── Resolve paths ─────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PYTHON     = sys.executable
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

def silent_spawn(script, *args):
    """Launch a .pyw script with pythonw so no console appears."""
    cmd = [PYTHON, os.path.join(BASE_DIR, script)] + list(args)
    subprocess.Popen(
        cmd,
        creationflags=subprocess.CREATE_NO_WINDOW,
        close_fds=True,
    )

# ── IMMEDIATE: swap the desktop wallpaper ─────────────────────────────────────
wallpaper = os.path.join(ASSETS_DIR, "background.jpeg")
if os.path.exists(wallpaper):
    # SPI_SETDESKWALLPAPER = 0x0014
    # SPIF_UPDATEINIFILE | SPIF_SENDCHANGE = 0x0003
    ctypes.windll.user32.SystemParametersInfoW(0x0014, 0, wallpaper, 0x0003)

# ── Silence for 5 minutes (300 s) ─────────────────────────────────────────────
time.sleep(300)

# ── Kick off the main chaos controller ────────────────────────────────────────
silent_spawn("chaos_main.pyw")
