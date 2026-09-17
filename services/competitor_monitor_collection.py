from __future__ import annotations

import copy
import ctypes
import json
import subprocess
import sys
import threading
import time
from ctypes import wintypes
from pathlib import Path
from urllib.parse import urlparse

from services.competitor_monitor import (
    ChromeEnvironment,
    CollectionResult,
    normalize_collection as _legacy_normalize_collection,
)


# A snapshot is usable for competitor monitoring when these stable page/assistant fields exist.
# ``sales_raw`` is deliberately excluded: 1688 rotates “已售…” and “…人想买” through the
# same hero slot, and some offers do not expose a cumulative sold count at all.
MONITOR_FIELDS = (
    "price_raw_values",
    "visible_sku_names",
    "month_sales_raw",
)

OPTIONAL_DYNAMIC_FIELDS = (
    "sales_raw",
    "interest_raw",
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

SW_FORCEMINIMIZE = 11
CREATE_NO_WINDOW = 0x08000000
CAROUSEL_SAMPLE_COUNT = 4
CAROUSEL_SAMPLE_INTERVAL_MS = 800


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
    """Force-minimize visible top-level windows owned by the supplied process ids."""
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
            user32.ShowWindowAsync(hwnd, SW_FORCEMINIMIZE)
            minimized += 1
        return True

    user32.EnumWindows(callback, 0)
    return minimized


def minimize_monitor_chrome(profile: Path, retries: int = 8, delay: float = 0.25) -> bool:
    """Force an already-running or newly-started monitor Chrome window to the taskbar."""
    for attempt in range(max(1, retries)):
        pids = _monitor_chrome_pids(profile)
        if pids and _minimize_process_windows(pids):
            return True
        if attempt + 1 < retries:
            time.sleep(delay)
    return False


class MonitorChromeWindowGuard:
    """Legacy minimize guard retained for compatibility with older callers/tests."""

    def __init__(self, profile: Path, *, interval: float = 0.2, refresh_pids_every: float = 2.0) -> None:
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
                _minimize_process_windows(pids)
            self._stop.wait(self.interval)


class BackgroundChromeEnvironment(ChromeEnvironment):
    """Legacy environment retained for compatibility; active runtime is in competitor_monitor_window."""

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


def _usable(value) -> bool:
    return value not in (None, "", "unavailable", [], {})


def _pick_first_available(samples: list[dict], section: str, field: str):
    for sample in samples:
        value = sample.get(section, {}).get(field)
        if _usable(value):
            return copy.deepcopy(value)
    return None


def merge_raw_samples(samples: list[dict]) -> dict:
    """Merge several observations from one loaded offer page.

    The main purpose is to observe 1688's rotating “已售/人想买” hero metric without forcing
    the user to wait for one specific carousel frame. Stable fields also benefit from the merge:
    if one observation briefly misses a late-rendered node, another observation can fill it.
    """
    if not samples:
        return {}

    merged = copy.deepcopy(samples[-1])
    merged["assistant_detected"] = any(bool(item.get("assistant_detected")) for item in samples)
    merged["product_detected"] = any(bool(item.get("product_detected")) for item in samples)

    product_fields = (
        "title", "price_raw_values", "price_tiers", "min_order_qty", "sales_raw", "interest_raw",
    )
    product = merged.setdefault("product", {})
    for field in product_fields:
        value = _pick_first_available(samples, "product", field)
        if value is not None:
            product[field] = value

    assistant = merged.setdefault("assistant", {})
    assistant_fields = (
        "listed_at", "month_sales_raw", "month_distribution_raw", "year_sales_quantity_raw",
        "year_sales_orders_raw", "review_count_raw", "positive_rate_raw", "stock_rate_raw",
    )
    for field in assistant_fields:
        value = _pick_first_available(samples, "assistant", field)
        if value is not None:
            assistant[field] = value

    metadata = merged.setdefault("page_metadata", {})
    for field in ("merchant_raw", "category_raw"):
        value = _pick_first_available(samples, "page_metadata", field)
        if value is not None:
            metadata[field] = value

    # Prefer the SKU observation that exposes the most usable names.
    def sku_score(sample: dict) -> tuple[int, int]:
        skus = sample.get("skus") or []
        names = [sku.get("name") for sku in skus if _usable(sku.get("name"))]
        return len(names), len(skus)

    best_sku_sample = max(samples, key=sku_score)
    if best_sku_sample.get("skus"):
        merged["skus"] = copy.deepcopy(best_sku_sample["skus"])

    login_evidence = []
    for sample in samples:
        for item in sample.get("login_evidence_raw") or []:
            if item not in login_evidence:
                login_evidence.append(item)
    merged["login_evidence_raw"] = login_evidence

    reasons = {}
    for sample in samples:
        reasons.update(sample.get("unavailable_reasons") or {})

    resolved_keys = []
    field_map = {
        "product.title": product.get("title"),
        "product.price_raw_values": product.get("price_raw_values"),
        "product.min_order_qty": product.get("min_order_qty"),
        "product.sales_raw": product.get("sales_raw"),
        "product.interest_raw": product.get("interest_raw"),
        "assistant.listed_at": assistant.get("listed_at"),
        "assistant.month_sales_raw": assistant.get("month_sales_raw"),
        "assistant.month_distribution_raw": assistant.get("month_distribution_raw"),
        "assistant.year_sales_quantity_raw": assistant.get("year_sales_quantity_raw"),
        "assistant.year_sales_orders_raw": assistant.get("year_sales_orders_raw"),
        "assistant.review_count_raw": assistant.get("review_count_raw"),
        "assistant.positive_rate_raw": assistant.get("positive_rate_raw"),
    }
    for key, value in field_map.items():
        if _usable(value):
            resolved_keys.append(key)
    for key in resolved_keys:
        reasons.pop(key, None)

    merged["unavailable_reasons"] = reasons
    merged["unavailable_fields"] = sorted(reasons)
    merged["carousel_observations"] = {
        "samples": len(samples),
        "sales_seen": _usable(product.get("sales_raw")),
        "interest_seen": _usable(product.get("interest_raw")),
    }
    return merged


def normalize_collection(raw: dict) -> dict:
    """Classify collection health by stable monitor-critical fields only."""
    data = _legacy_normalize_collection(raw)
    product = raw.get("product", {})
    interest = product.get("interest_raw")
    data["interest_raw"] = None if interest in (None, "", "unavailable") else interest

    core_missing = _missing(data, MONITOR_FIELDS)
    data["collection_status"] = "partial" if core_missing else "success"
    data["missing_fields"] = core_missing
    data["basic_missing_fields"] = _missing(data, BASIC_FIELDS)
    data["auxiliary_missing_fields"] = _missing(data, AUXILIARY_FIELDS)
    data["optional_dynamic_missing_fields"] = _missing(data, OPTIONAL_DYNAMIC_FIELDS)
    data["collection_diagnostics"] = {
        "unavailable_reasons": raw.get("unavailable_reasons", {}),
        "carousel_observations": raw.get("carousel_observations", {}),
    }
    return data


class PlaywrightCollector:
    """1688 collector that waits for stable fields and samples rotating hero metrics."""

    def __init__(self, cdp_url: str = "http://127.0.0.1:9222", extractor: Path | None = None) -> None:
        self.cdp_url = cdp_url
        self.extractor = extractor or Path(__file__).parents[1] / "tools" / "competitor_monitor" / "extract.js"

    def batch_context(self) -> MonitorChromeWindowGuard:
        return MonitorChromeWindowGuard(ChromeEnvironment.PROFILE)

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

                    extractor = self.extractor.read_text(encoding="utf-8")
                    samples = []
                    for sample_index in range(CAROUSEL_SAMPLE_COUNT):
                        samples.append(page.evaluate(extractor))
                        if sample_index + 1 < CAROUSEL_SAMPLE_COUNT:
                            page.wait_for_timeout(CAROUSEL_SAMPLE_INTERVAL_MS)
                    raw = merge_raw_samples(samples)
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
