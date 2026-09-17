from __future__ import annotations

import ctypes
import json
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path
from urllib.parse import urlparse

from services.competitor_monitor import (
    ChromeEnvironment,
    CollectionResult,
    normalize_collection as _legacy_normalize_collection,
)


MONITOR_FIELDS = (
    "price_raw_values",
    "sales_raw",
    "visible_sku_names",
    "month_sales_raw",
)

AUXILIARY_FIELDS = (
    "listed_at",
    "month_distribution_raw",
    "year_sales_quantity_raw",
    "year_sales_orders_raw",
    "review_count_raw",
    "positive_rate_raw",
)

BASIC_FIELDS = (
    "min_order_qty",
)

SW_MINIMIZE = 6
CREATE_NO_WINDOW = 0x08000000


def _monitor_chrome_pids(profile: Path) -> set[int]:
    """Return Chrome process ids that belong to the dedicated monitor profile."""
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

    pids = set()
    for line in result.stdout.splitlines():
        try:
            pids.add(int(line.strip()))
        except ValueError:
            continue
    return pids


def _minimize_process_windows(pids: set[int]) -> int:
    """Minimize visible top-level windows owned by the supplied process ids."""
    if not pids or not sys.platform.startswith("win"):
        return 0

    user32 = ctypes.windll.user32
    minimized = 0
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    @callback_type
    def callback(hwnd, _lparam):
        nonlocal minimized
        process_id = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        if process_id.value in pids and user32.IsWindowVisible(hwnd):
            user32.ShowWindow(hwnd, SW_MINIMIZE)
            minimized += 1
        return True

    user32.EnumWindows(callback, 0)
    return minimized


def minimize_monitor_chrome(profile: Path, retries: int = 8, delay: float = 0.25) -> bool:
    """Force an already-running or newly-started monitor Chrome window to the taskbar."""
    pids = _monitor_chrome_pids(profile)
    if not pids:
        return False
    for attempt in range(max(1, retries)):
        if _minimize_process_windows(pids):
            return True
        if attempt + 1 < retries:
            time.sleep(delay)
    return False


class BackgroundChromeEnvironment(ChromeEnvironment):
    """Use the real dedicated Chrome session while keeping its window out of the way.

    ``--start-minimized`` alone is not reliable when Chrome restores a previous window or is
    already running. After CDP is ready we therefore locate the dedicated Chrome process and
    explicitly minimize its top-level Windows window. Manual recovery still opens Chrome
    visibly so login or verification can be handled by the user.
    """

    def ensure(self, timeout: float = 15):
        result = super().ensure(timeout)
        if result.ready:
            minimize_monitor_chrome(self.PROFILE)
        return result

    def _start_chrome(self, url: str | None = None) -> None:
        if url:
            super()._start_chrome(url)
            return
        chrome = self._chrome_path()
        subprocess.Popen([
            str(chrome),
            "--remote-debugging-port=9222",
            f"--user-data-dir={self.PROFILE}",
            "--start-minimized",
            "--no-first-run",
            "--no-default-browser-check",
        ])


def _missing(data: dict, fields: tuple[str, ...]) -> list[str]:
    return [name for name in fields if data.get(name) in (None, [], "")]


def normalize_collection(raw: dict) -> dict:
    """Classify collection health by monitor-critical fields only.

    Auxiliary analytics fields remain in the snapshot when available, but their absence does
    not turn an otherwise usable competitor snapshot into a warning state.
    """
    data = _legacy_normalize_collection(raw)
    core_missing = _missing(data, MONITOR_FIELDS)
    data["collection_status"] = "partial" if core_missing else "success"
    data["missing_fields"] = core_missing
    data["basic_missing_fields"] = _missing(data, BASIC_FIELDS)
    data["auxiliary_missing_fields"] = _missing(data, AUXILIARY_FIELDS)
    return data


class PlaywrightCollector:
    """1688 collector that waits for the useful page structure and retries core-field gaps once."""

    def __init__(self, cdp_url: str = "http://127.0.0.1:9222", extractor: Path | None = None) -> None:
        self.cdp_url = cdp_url
        self.extractor = extractor or Path(__file__).parents[1] / "tools" / "competitor_monitor" / "extract.js"

    def collect(self, url: str) -> CollectionResult:
        first = self._collect_once(url)
        if not first.recoverable:
            return first
        time.sleep(2)
        return self._collect_once(url)

    def _collect_once(self, url: str) -> CollectionResult:
        try:
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

            with sync_playwright() as pw:
                browser = pw.chromium.connect_over_cdp(self.cdp_url, timeout=5000)
                if not browser.contexts:
                    raise RuntimeError("Chrome没有可用上下文")

                page = browser.contexts[0].new_page()
                try:
                    response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    if response and response.status == 404:
                        return CollectionResult(
                            "failed",
                            error="1688商品不存在或已下架",
                            technical_error=f"HTTP 404: {url}",
                        )

                    try:
                        page.wait_for_function(
                            """() => {
                                const visible = e => e && e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden';
                                const title = Array.from(document.querySelectorAll('.title-content h1')).find(visible);
                                const price = Array.from(document.querySelectorAll('.price-component .price-info')).find(visible);
                                const body = document.body?.innerText || '';
                                return Boolean(title && price && body.includes('月成交'));
                            }""",
                            timeout=20000,
                        )
                        page.wait_for_timeout(1200)
                    except PlaywrightTimeoutError:
                        pass

                    raw = page.evaluate(self.extractor.read_text(encoding="utf-8"))
                    final_url = page.url
                finally:
                    page.close()

            if raw.get("login_evidence_raw") or "login" in urlparse(final_url).path.lower():
                return CollectionResult(
                    "failed",
                    error="1688登录状态已失效，请在专用Chrome中重新登录后重试。",
                    technical_error=json.dumps(
                        {"url": final_url, "login_evidence": raw.get("login_evidence_raw", [])},
                        ensure_ascii=False,
                    ),
                    environment_error=True,
                )

            if not raw.get("product_detected"):
                return CollectionResult(
                    "failed",
                    error="商品数据未完整加载",
                    technical_error=json.dumps(
                        {
                            "url": final_url,
                            "dom": raw.get("dom_structure"),
                            "unavailable": raw.get("unavailable_reasons"),
                        },
                        ensure_ascii=False,
                    ),
                    recoverable=True,
                )

            if not raw.get("assistant_detected"):
                return CollectionResult(
                    "failed",
                    error="官方采购助手未加载",
                    technical_error=json.dumps(
                        {
                            "url": final_url,
                            "dom": raw.get("dom_structure"),
                            "unavailable": raw.get("unavailable_reasons"),
                        },
                        ensure_ascii=False,
                    ),
                    recoverable=True,
                )

            data = normalize_collection(raw)
            return CollectionResult(
                data["collection_status"],
                data=data,
                recoverable=data["collection_status"] == "partial",
            )
        except Exception as exc:
            raw_error = str(exc)
            if "connect_over_cdp" in raw_error or "ECONNREFUSED" in raw_error or "browser has been closed" in raw_error:
                return CollectionResult(
                    "failed",
                    error="采集环境未连接",
                    technical_error=raw_error,
                    environment_error=True,
                )
            deterministic = "ERR_NAME_NOT_RESOLVED" in raw_error or "HTTP 404" in raw_error
            return CollectionResult(
                "failed",
                error="1688页面加载失败",
                technical_error=raw_error,
                recoverable=not deterministic,
            )
