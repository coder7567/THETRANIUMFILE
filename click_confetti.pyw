"""
click_confetti.pyw
==================
Transparent, click-through, fullscreen overlay.

Uses a Windows low-level mouse hook (WH_MOUSE_LL) to intercept every
left-button-down event system-wide WITHOUT blocking it.

On each click:
  1. Plays pop.mp3 via Windows MCI (no external libs required)
  2. Spawns ~400 confetti particles exploding from the click point
  3. Flashes a bright colour burst that lasts a few frames,
     obscuring the screen for ~0.5 seconds

Cannot be closed by the user.
"""

import tkinter as tk
import ctypes
import ctypes.wintypes
import random
import math
import time
import threading
import queue
import os
import sys

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
POP_PATH  = os.path.join(BASE_DIR, "assets", "pop.mp3")

# ── Win32 bindings ─────────────────────────────────────────────────────────────
user32   = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
winmm    = ctypes.windll.winmm

GWL_EXSTYLE       = -20
WS_EX_LAYERED     = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW  = 0x00000080
WH_MOUSE_LL       = 14
WM_LBUTTONDOWN    = 0x0201

# ── Shared click queue (hook thread → tkinter thread) ─────────────────────────
click_queue = queue.Queue()

# ── Sound playback (Windows MCI — plays MP3 natively) ─────────────────────────
_mci_id   = 0
_mci_lock = threading.Lock()

def play_pop():
    global _mci_id
    with _mci_lock:
        alias = f"pop{_mci_id}"
        _mci_id += 1
    try:
        winmm.mciSendStringW(
            f'open "{POP_PATH}" type mpegvideo alias {alias}',
            None, 0, None
        )
        winmm.mciSendStringW(f'play {alias}', None, 0, None)
        def _close():
            time.sleep(5)
            winmm.mciSendStringW(f'close {alias}', None, 0, None)
        threading.Thread(target=_close, daemon=True).start()
    except Exception:
        pass

# ── Global mouse hook ──────────────────────────────────────────────────────────
class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt",          ctypes.wintypes.POINT),
        ("mouseData",   ctypes.wintypes.DWORD),
        ("flags",       ctypes.wintypes.DWORD),
        ("time",        ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

HOOKPROC = ctypes.WINFUNCTYPE(
    ctypes.c_long, ctypes.c_int,
    ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM
)

_hook_handle = None
_hook_proc   = None   # keep alive — GC would break the hook

def _hook_callback(nCode, wParam, lParam):
    if nCode >= 0 and wParam == WM_LBUTTONDOWN:
        ms = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
        click_queue.put((ms.pt.x, ms.pt.y))
        threading.Thread(target=play_pop, daemon=True).start()
    return user32.CallNextHookEx(_hook_handle, nCode, wParam, lParam)

def _install_hook():
    global _hook_handle, _hook_proc
    _hook_proc   = HOOKPROC(_hook_callback)
    _hook_handle = user32.SetWindowsHookExW(WH_MOUSE_LL, _hook_proc, None, 0)
    msg = ctypes.wintypes.MSG()
    # Pump the message loop so the hook receives events
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))
    if _hook_handle:
        user32.UnhookWindowsHookEx(_hook_handle)

# ── Confetti particle ──────────────────────────────────────────────────────────
CONFETTI_COLORS = [
    "#FF0055", "#FF6A00", "#FFEA00", "#00FF41", "#00E5FF",
    "#AA00FF", "#FF00AA", "#ADFF2F", "#FF69B4", "#FFA500",
    "#FFD700", "#40E0D0", "#FF1493", "#7FFF00", "#00BFFF",
    "#FFFFFF", "#FF4500", "#DC143C", "#00CED1", "#FF6347",
    "#7B68EE", "#32CD32", "#FF8C00", "#1E90FF", "#ADFF2F",
]

PARTICLES_PER_CLICK = 420
FRAME_MS            = 16    # ~60 fps

class ConfettiParticle:
    __slots__ = ("x", "y", "vx", "vy", "color", "w", "h",
                 "rot", "rot_spd", "life", "max_life", "shape")

    def __init__(self, x, y):
        angle        = random.uniform(0, 2 * math.pi)
        # High speed so they spread across the screen fast
        speed        = random.uniform(6, 70)
        self.x       = float(x)
        self.y       = float(y)
        self.vx      = math.cos(angle) * speed
        self.vy      = math.sin(angle) * speed - random.uniform(5, 25)
        self.color   = random.choice(CONFETTI_COLORS)
        self.w       = random.randint(8, 22)
        self.h       = random.randint(4, 12)
        self.rot     = random.uniform(0, 360)
        self.rot_spd = random.uniform(-15, 15)
        self.life    = random.randint(35, 70)
        self.max_life = self.life
        self.shape   = random.choice(["rect", "oval", "line", "rect"])

    def update(self):
        self.x   += self.vx
        self.y   += self.vy
        self.vy  += 1.2     # gravity
        self.vx  *= 0.97    # air drag
        self.vy  *= 0.97
        self.rot += self.rot_spd
        self.life -= 1

    @property
    def alive(self):
        return self.life > 0

    @property
    def alpha_ratio(self):
        return self.life / self.max_life


# ── Flash burst state ──────────────────────────────────────────────────────────
class FlashBurst:
    __slots__ = ("x", "y", "life", "max_life", "color")

    def __init__(self, x, y):
        self.x        = x
        self.y        = y
        self.life     = 8
        self.max_life = 8
        self.color    = random.choice(CONFETTI_COLORS)

    @property
    def alive(self):
        return self.life > 0


# ── Main app ───────────────────────────────────────────────────────────────────
class ClickConfettiApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("")

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.sw = sw
        self.sh = sh

        # ── Full-screen transparent, click-through overlay ────────────────────
        self.root.geometry(f"{sw}x{sh}+0+0")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", "#000001")
        self.root.configure(bg="#000001")
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        # Apply WS_EX_TRANSPARENT so clicks pass through the window
        hwnd  = self.root.winfo_id()
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(
            hwnd, GWL_EXSTYLE,
            style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW
        )

        self.canvas = tk.Canvas(
            self.root, width=sw, height=sh,
            bg="#000001", highlightthickness=0, bd=0
        )
        self.canvas.pack()

        # ── Particle / flash state ─────────────────────────────────────────────
        self.particles: list[ConfettiParticle] = []
        self.flashes:   list[FlashBurst]       = []

        # ── Start hook in background thread ───────────────────────────────────
        t = threading.Thread(target=_install_hook, daemon=True)
        t.start()

        # ── Begin animation loop ───────────────────────────────────────────────
        self._animate()
        self.root.mainloop()

    # ── Main animation loop ────────────────────────────────────────────────────
    def _animate(self):
        # Drain the click queue and spawn bursts
        try:
            while True:
                x, y = click_queue.get_nowait()
                self._spawn_burst(x, y)
        except queue.Empty:
            pass

        self.canvas.delete("all")

        # Draw flash overlays first (behind particles)
        for fl in self.flashes:
            ratio = fl.life / fl.max_life
            r = int(fl.life / fl.max_life * self.sw * 1.5)
            if r > 0:
                # Expanding coloured circle flash
                self.canvas.create_oval(
                    fl.x - r, fl.y - r, fl.x + r, fl.y + r,
                    fill=fl.color, outline="",
                    tags="flash"
                )
            fl.life -= 1

        self.flashes = [f for f in self.flashes if f.alive]

        # Draw particles
        for p in self.particles:
            p.update()
            ratio = p.alpha_ratio
            if ratio <= 0:
                continue
            # Dim color as particle fades
            col = self._fade_color(p.color, ratio)
            rx  = p.w // 2
            ry  = p.h // 2
            if p.shape == "oval":
                self.canvas.create_oval(
                    p.x - rx, p.y - ry, p.x + rx, p.y + ry,
                    fill=col, outline=""
                )
            elif p.shape == "line":
                angle_r = math.radians(p.rot)
                ex = p.x + math.cos(angle_r) * p.w
                ey = p.y + math.sin(angle_r) * p.w
                self.canvas.create_line(
                    p.x, p.y, ex, ey,
                    fill=col, width=max(1, p.h // 2)
                )
            else:  # rect (approximate with a rotated polygon)
                angle_r = math.radians(p.rot)
                cos_a, sin_a = math.cos(angle_r), math.sin(angle_r)
                corners = [
                    (-rx, -ry), (rx, -ry), (rx, ry), (-rx, ry)
                ]
                pts = []
                for cx, cy in corners:
                    pts.append(p.x + cx * cos_a - cy * sin_a)
                    pts.append(p.y + cx * sin_a + cy * cos_a)
                self.canvas.create_polygon(pts, fill=col, outline="")

        self.particles = [p for p in self.particles if p.alive]

        self.root.after(FRAME_MS, self._animate)

    def _spawn_burst(self, x, y):
        # Add a screen flash
        self.flashes.append(FlashBurst(x, y))
        # Spawn confetti particles
        for _ in range(PARTICLES_PER_CLICK):
            self.particles.append(ConfettiParticle(x, y))

    @staticmethod
    def _fade_color(hex_col: str, ratio: float) -> str:
        """Darken a hex colour by alpha ratio."""
        hex_col = hex_col.lstrip("#")
        r = int(int(hex_col[0:2], 16) * ratio)
        g = int(int(hex_col[2:4], 16) * ratio)
        b = int(int(hex_col[4:6], 16) * ratio)
        return f"#{r:02X}{g:02X}{b:02X}"


if __name__ == "__main__":
    ClickConfettiApp()
