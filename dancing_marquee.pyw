"""
dancing_marquee.pyw
===================
A classic <marquee>-style banner anchored to the very bottom of the desktop.

Behaviour:
  • Dark semi-transparent strip spanning the full screen width
  • Text scrolls right → left continuously
  • Font SIZE cycles chaotically between tiny (8 pt) and massive (140 pt)
  • Scroll SPEED changes randomly from a crawl (0.4 px/frame) to
    hyper-sonic sprint (70 px/frame)
  • Text colour shifts through the rainbow each cycle
  • Cannot be closed by the user

No external dependencies — only tkinter (bundled with CPython on Windows).
"""

import tkinter as tk
import ctypes
import ctypes.wintypes
import random
import time
import threading

user32 = ctypes.windll.user32

GWL_EXSTYLE      = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW  = 0x00040000

# ── Content ────────────────────────────────────────────────────────────────────
MARQUEE_TEXT = (
    "  🌈 CHAOS MODE: FULLY ACTIVATED 🌈  •  "
    "LEVI'S JOKE PROGRAM IS RUNNING  •  "
    "IS THIS FINE? 🔥  •  "
    "BOING BOING BOING  •  "
    "GREETINGS FROM THE MARQUEE  •  "
    "HELP I CANNOT STOP SCROLLING  •  "
    "HAVE YOU TRIED TURNING IT OFF?  •  "
    "HONK 🤡  •  "
    "YOUR CPU IS FINE... PROBABLY  •  "
    "LEVI SENDS HIS REGARDS  •  "
    "THIS IS PERFECTLY NORMAL BEHAVIOUR  •  "
    "ERROR 404: SANITY NOT FOUND  •  "
    "I AM SPEED 🏎️  •  "
    "NO TAKE BACKS  •  "
    "404 WALLPAPER NOT FOUND ... JUST KIDDING  •  "
    "UH OH SPAGHETTI-O  •  "
    "RESISTANCE IS FUTILE  •  "
)

# ── Font size pool ─────────────────────────────────────────────────────────────
FONT_SIZES = [8, 11, 14, 18, 24, 32, 42, 54, 68, 84, 100, 120, 140]

# ── Speed pool (pixels per frame at ~60 fps) ───────────────────────────────────
SPEEDS = [0.4, 0.7, 1.0, 1.5, 2.5, 4.0, 7.0, 12.0, 20.0, 35.0, 55.0, 70.0]

# ── Dimensions ─────────────────────────────────────────────────────────────────
STRIP_HEIGHT = 200      # fixed height of the strip (accommodates largest font)
FRAME_MS     = 16       # ~60 fps
BG_COLOR     = "#0D0D0D"  # very dark background for the strip

# ── Colour helpers ─────────────────────────────────────────────────────────────
def hsv_to_hex(h, s=1.0, v=1.0):
    h %= 360
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if   h < 60:  r, g, b = c, x, 0
    elif h < 120: r, g, b = x, c, 0
    elif h < 180: r, g, b = 0, c, x
    elif h < 240: r, g, b = 0, x, c
    elif h < 300: r, g, b = x, 0, c
    else:         r, g, b = c, 0, x
    r, g, b = int((r+m)*255), int((g+m)*255), int((b+m)*255)
    return f"#{r:02X}{g:02X}{b:02X}"


class DancingMarqueeApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("")

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.sw = sw

        # ── Position at the very bottom of the screen ─────────────────────────
        self.root.geometry(f"{sw}x{STRIP_HEIGHT}+0+{sh - STRIP_HEIGHT}")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.92)   # slight transparency
        self.root.configure(bg=BG_COLOR)
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        # Remove from taskbar
        hwnd  = self.root.winfo_id()
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE,
                              (style | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW)

        # ── Canvas ─────────────────────────────────────────────────────────────
        self.canvas = tk.Canvas(
            self.root, width=sw, height=STRIP_HEIGHT,
            bg=BG_COLOR, highlightthickness=0, bd=0
        )
        self.canvas.pack()

        # ── State ──────────────────────────────────────────────────────────────
        self.font_size    = random.choice(FONT_SIZES)
        self.speed        = random.choice(SPEEDS)
        self.text_x       = float(sw)       # starts off-screen right
        self.hue          = random.uniform(0, 360)
        self.tick         = 0
        self.text_width   = self._measure_text_width()

        # ── Repeated text buffer for seamless looping ─────────────────────────
        # We repeat the marquee text 3× so there's always content visible
        self.display_text = MARQUEE_TEXT * 3

        # ── Schedule size & speed changes ─────────────────────────────────────
        self._schedule_size_change()
        self._schedule_speed_change()

        # ── Animate ────────────────────────────────────────────────────────────
        self._animate()
        self.root.mainloop()

    # ── Measurement ───────────────────────────────────────────────────────────
    def _measure_text_width(self):
        """Approximate text width: each character ≈ font_size * 0.62."""
        return int(len(self.display_text) * self.font_size * 0.62)

    # ── Scheduled random chaos ─────────────────────────────────────────────────
    def _schedule_size_change(self):
        new_size = random.choice(FONT_SIZES)
        self.font_size  = new_size
        self.text_width = self._measure_text_width()
        delay = random.randint(1500, 5000)   # 1.5 – 5 seconds
        self.root.after(delay, self._schedule_size_change)

    def _schedule_speed_change(self):
        self.speed = random.choice(SPEEDS)
        delay = random.randint(800, 4000)    # 0.8 – 4 seconds
        self.root.after(delay, self._schedule_speed_change)

    # ── Animation loop ─────────────────────────────────────────────────────────
    def _animate(self):
        self.tick += 1
        self.text_x -= self.speed

        # Loop: when text has fully scrolled off the left edge, reset
        if self.text_x + self.text_width < 0:
            self.text_x = float(self.sw)

        # Cycle text colour
        self.hue = (self.hue + 1.2) % 360
        color    = hsv_to_hex(self.hue)

        # ── Draw ───────────────────────────────────────────────────────────────
        self.canvas.delete("all")

        # Background strip (in case alpha isn't perfect)
        self.canvas.create_rectangle(
            0, 0, self.sw, STRIP_HEIGHT,
            fill=BG_COLOR, outline=""
        )

        # Speed indicator glow (subtle line at the top of the strip)
        spd_ratio = SPEEDS.index(self.speed) / (len(SPEEDS) - 1)
        glow_w    = int(self.sw * spd_ratio)
        glow_col  = hsv_to_hex((self.hue + 180) % 360, 1, 0.7)
        self.canvas.create_rectangle(
            0, 0, glow_w, 4,
            fill=glow_col, outline=""
        )

        # Shadow text (depth effect)
        font_spec = ("Impact", self.font_size, "bold")
        y_center  = STRIP_HEIGHT // 2
        self.canvas.create_text(
            int(self.text_x) + 3, y_center + 3,
            text=self.display_text,
            font=font_spec,
            fill="#111111",
            anchor="w",
        )
        # Main text
        self.canvas.create_text(
            int(self.text_x), y_center,
            text=self.display_text,
            font=font_spec,
            fill=color,
            anchor="w",
        )

        self.root.after(FRAME_MS, self._animate)


if __name__ == "__main__":
    DancingMarqueeApp()
