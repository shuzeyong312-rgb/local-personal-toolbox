from __future__ import annotations

import ctypes
import subprocess
import sys
import threading
import time
from ctypes import wintypes
from pathlib import Path

from services.competitor_monitor import ChromeEnvironment
from services.competitor_monitor_collection import PlaywrightCollector as CorePlaywrightCollector


CREATE_NO_WINDOW = 0x08000000
SW_RESTORE = 9
SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_ASYNCWINDOWPOS = 0x4000
OFFSCREEN_X = -32000
OFFSCREEN_Y = -32000
RESTORE_X = 80
RESTORE_Y = 80


def _monitor_chrome_pids(profile: Path) -> set[int]:
    if not sys.platform.startswith("win"):
        return set()

    profile_text = str(profile).replace("'", "''")
    script = (
        f"$profile='{profile_text}';"
        "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
        "Where-Object { $_.CommandLine -and ("
        "$_.CommandLine -like ('*' + $profile + '*') -or "
        "$_.CommandLine -like '*--remote-debugging-port=9222*') } | "
        "Select-Object -ExpandProperty ProcessId"
    )
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            check=False,
            creationflags=CREATE_NO_WINDOW,
        )
    except OSError:
        return set()
    if result.returncode:
        return set()

    pids: set[int] = set()
    for line in result.stdout.splitlines():
        try:
            pids.add(int(line.strip()))
        except ValueError:
            continue
    return pids


def _park_process_windows(pids: set[int]) -> int:
    """Move dedicated Chrome windows off-screen instead of repeatedly minimizing them.

    A visible off-screen window keeps Chrome's normal headed rendering and login session, while
    avoiding the minimize/restore loop that causes visible flashing when Playwright creates tabs.
    """
    if not pids or not sys.platform.startswith("win"):
        return 0

    user32 = ctypes.windll.user32
    moved = 0
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    @callback_type
    def callback(hwnd, _lparam):
        nonlocal moved
        process_id = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        if process_id.value not in pids or not user32.IsWindowVisible(hwnd):
            return True

        rect = wintypes.RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return True
        if rect.left <= -10000 and rect.top <= -10000:
            return True

        flags = SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_ASYNCWINDOWPOS
        if user32.SetWindowPos(hwnd, 0, OFFSCREEN_X, OFFSCREEN_Y, 0, 0, flags):
            moved += 1
        return True

    user32.EnumWindows(callback, 0)
    return moved


def park_monitor_chrome(profile: Path, retries: int = 10, delay: float = 0.15) -> bool:
    """Park an existing or newly-created dedicated Chrome window outside the visible desktop."""
    for attempt in range(max(1, retries)):
        pids = _monitor_chrome_pids(profile)
        if pids:
            moved = _park_process_windows(pids)
            if moved:
                return True
            # A matching window may already be parked, which is also a success state.
            if attempt:
                return True
        if attempt + 1 < retries:
            time.sleep(delay)
    return False


def _restore_process_windows(pids: set[int]) -> int:
    if not pids or not sys.platform.startswith("win"):
        return 0

    user32 = ctypes.windll.user32
    restored = 0
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    @callback_type
    def callback(hwnd, _lparam):
        nonlocal restored
        process_id = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        if process_id.value not in pids:
            return True

        user32.ShowWindowAsync(hwnd, SW_RESTORE)
        flags = SWP_NOSIZE | SWP_NOZORDER | SWP_ASYNCWINDOWPOS
        user32.SetWindowPos(hwnd, 0, RESTORE_X, RESTORE_Y, 0, 0, flags)
        restored += 1
        return True

    user32.EnumWindows(callback, 0)
    return restored


def restore_monitor_chrome(profile: Path, retries: int = 10, delay: float = 0.15) -> bool:
    for attempt in range(max(1, retries)):
        pids = _monitor_chrome_pids(profile)
        if pids and _restore_process_windows(pids):
            return True
        if attempt + 1 < retries:
            time.sleep(delay)
    return False


class MonitorChromeWindowGuard:
    """Keep the dedicated Chrome parked off-screen during the complete collection batch."""

    def __init__(self, profile: Path, *, interval: float = 0.5, refresh_pids_every: float = 2.0) -> None:
        self.profile = profile
        self.interval = interval
        self.refresh_pids_every = refresh_pids_every
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        self.stop()

    def start(self) -> None:
        if not sys.platform.startswith("win"):
            return
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="1688-monitor-window-guard",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive() and self._thread is not threading.current_thread():
            self._thread.join(timeout=1.0)
        self._thread = None

    def _run(self) -> None:
        pids: set[int] = set()
        next_refresh = 0.0
        while not self._stop.is_set():
            now = time.monotonic()
            if not pids or now >= next_refresh:
                pids = _monitor_chrome_pids(self.profile)
                next_refresh = now + self.refresh_pids_every
            if pids:
                _park_process_windows(pids)
            self._stop.wait(self.interval)


class BackgroundChromeEnvironment(ChromeEnvironment):
    """Run the real dedicated Chrome session outside the visible desktop."""

    def ensure(self, timeout: float = 15):
        # Call the base implementation directly so the old force-minimize behavior is bypassed.
        result = ChromeEnvironment.ensure(self, timeout)
        if result.ready:
            park_monitor_chrome(self.PROFILE)
        return result

    def _start_chrome(self, url: str | None = None) -> None:
        if url:
            ChromeEnvironment._start_chrome(self, url)
            return
        chrome = self._chrome_path()
        subprocess.Popen([
            str(chrome),
            "--remote-debugging-port=9222",
            f"--user-data-dir={self.PROFILE}",
            f"--window-position={OFFSCREEN_X},{OFFSCREEN_Y}",
            "--window-size=1280,900",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-background-timer-throttling",
            "--no-first-run",
            "--no-default-browser-check",
        ])

    def open_browser(self) -> None:
        # Explicit user recovery should be visible again.
        ChromeEnvironment._start_chrome(self, "https://www.1688.com/")
        restore_monitor_chrome(self.PROFILE)


class PlaywrightCollector(CorePlaywrightCollector):
    """Use the existing collector while replacing the flashing minimize guard."""

    def batch_context(self) -> MonitorChromeWindowGuard:
        return MonitorChromeWindowGuard(ChromeEnvironment.PROFILE)
