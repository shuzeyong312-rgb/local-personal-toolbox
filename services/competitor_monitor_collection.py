from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import urlparse

from services.competitor_monitor import CollectionResult, normalize_collection as _legacy_normalize_collection


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

                    # Wait for the structures that feed the actual monitor columns instead of
                    # using a fixed sleep or waiting on every optional analytics field.
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
                        # Let late-rendered counters settle after the main structures appear.
                        page.wait_for_timeout(1200)
                    except PlaywrightTimeoutError:
                        # Still inspect the page. Missing monitor fields below will trigger the
                        # single retry instead of silently accepting an early partial snapshot.
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
            # Any missing monitor-critical field deserves one fresh-page retry. Auxiliary or
            # basic-field gaps do not trigger a retry and do not mark the row as incomplete.
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
