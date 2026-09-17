from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable


OFFER_URL = re.compile(r"^https://detail\.1688\.com/offer/(\d+)\.html(?:[?#].*)?$")
CORE_FIELDS = (
    "title", "price_raw_values", "min_order_qty", "sales_raw", "visible_sku_names",
    "listed_at", "month_sales_raw", "month_distribution_raw",
    "year_sales_quantity_raw", "year_sales_orders_raw",
)


def parse_offer_url(url: str) -> tuple[str, str]:
    url = url.strip()
    match = OFFER_URL.fullmatch(url)
    if not match:
        raise ValueError("不是有效的1688商品详情链接")
    return match.group(1), f"https://detail.1688.com/offer/{match.group(1)}.html"


def normalize_collection(raw: dict) -> dict:
    product = raw.get("product", {})
    assistant = raw.get("assistant", {})
    skus = raw.get("skus", [])

    def value(name: str):
        item = product.get(name, assistant.get(name))
        return None if item in (None, "unavailable") else item

    def optional(item):
        return None if item in (None, "unavailable") else item

    selected = next((sku for sku in skus if sku.get("selected")), {})
    result = {
        "title": value("title"),
        "price_raw_values": value("price_raw_values") or [],
        "price_tiers": value("price_tiers") or [],
        "min_order_qty": value("min_order_qty"),
        "sales_raw": value("sales_raw"),
        "visible_sku_names": [sku["name"] for sku in skus if sku.get("name") not in (None, "unavailable")],
        "listed_at": value("listed_at"),
        "month_sales_raw": value("month_sales_raw"),
        "month_distribution_raw": value("month_distribution_raw"),
        "year_sales_quantity_raw": value("year_sales_quantity_raw"),
        "year_sales_orders_raw": value("year_sales_orders_raw"),
        "selected_sku_name": optional(selected.get("selected_sku_name") or selected.get("specification_raw")),
        "selected_sku_price_raw": optional(selected.get("selected_sku_price_raw") or selected.get("price_raw")),
        "selected_sku_availability": optional(selected.get("selected_sku_availability") or selected.get("availability")),
        "selected_sku_stock_raw": optional(selected.get("selected_sku_stock_raw") or selected.get("stock_raw")),
        "review_count_raw": value("review_count_raw"),
        "positive_rate_raw": value("positive_rate_raw"),
    }
    missing = [name for name in CORE_FIELDS if result[name] in (None, [], "")]
    result["collection_status"] = "partial" if missing else "success"
    result["missing_fields"] = missing
    return result


def parse_price_range(values: list[str]) -> tuple[float | None, float | None]:
    numbers = [float(match.group()) for value in values if (match := re.search(r"\d+(?:\.\d+)?", value))]
    return (min(numbers), max(numbers)) if numbers else (None, None)


def parse_metric(value: str | None) -> tuple[int | None, str | None]:
    if not value:
        return None, None
    text = value.replace(",", "")
    match = re.search(r"(\d+(?:\.\d+)?)\s*(万|千)?", text)
    if not match:
        return None, None
    number = int(float(match.group(1)) * {"万": 10000, "千": 1000}.get(match.group(2), 1))
    if "<" in text or "＜" in text:
        return 0, "lt"
    return number, "gte" if "+" in text else "exact"


@dataclass
class CollectionResult:
    status: str
    data: dict | None = None
    error: str = ""


class MonitorStore:
    def __init__(self, path: Path | str = Path("data/competitor_monitor.db")) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self._create_schema()

    def close(self) -> None:
        self.db.close()

    def _create_schema(self) -> None:
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS competitor_groups (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS competitors (
                id INTEGER PRIMARY KEY, offer_id TEXT NOT NULL UNIQUE, url TEXT NOT NULL,
                title TEXT, alias TEXT, group_id INTEGER REFERENCES competitor_groups(id) ON DELETE SET NULL,
                note TEXT, monitor_enabled INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL DEFAULT '待验证', created_at TEXT NOT NULL,
                last_success_at TEXT, last_attempt_at TEXT
            );
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY, competitor_id INTEGER NOT NULL REFERENCES competitors(id) ON DELETE CASCADE,
                collected_at TEXT NOT NULL, snapshot_date TEXT NOT NULL, title TEXT,
                price_raw_values_json TEXT NOT NULL, price_tiers_json TEXT NOT NULL,
                display_price_min REAL, display_price_max REAL, min_order_qty TEXT,
                sales_raw TEXT, sales_lower_bound INTEGER, sales_value_type TEXT,
                visible_sku_names_json TEXT NOT NULL, listed_at TEXT,
                month_sales_raw TEXT, month_sales_lower_bound INTEGER,
                month_distribution_raw TEXT, month_distribution_lower_bound INTEGER,
                year_sales_quantity_raw TEXT, year_sales_quantity_lower_bound INTEGER,
                year_sales_orders_raw TEXT, year_sales_orders_lower_bound INTEGER,
                selected_sku_name TEXT, selected_sku_price_raw TEXT,
                selected_sku_availability TEXT, selected_sku_stock_raw TEXT,
                review_count_raw TEXT, positive_rate_raw TEXT,
                collection_status TEXT NOT NULL, missing_fields_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_snapshots_collected ON snapshots(competitor_id, collected_at);
            CREATE INDEX IF NOT EXISTS idx_snapshots_date ON snapshots(competitor_id, snapshot_date);
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY, competitor_id INTEGER NOT NULL REFERENCES competitors(id) ON DELETE CASCADE,
                snapshot_id INTEGER REFERENCES snapshots(id) ON DELETE CASCADE, event_type TEXT NOT NULL,
                severity TEXT NOT NULL, title TEXT NOT NULL, detail_json TEXT NOT NULL,
                created_at TEXT NOT NULL, notified INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS monitor_runs (
                id INTEGER PRIMARY KEY, started_at TEXT NOT NULL, finished_at TEXT, trigger_type TEXT NOT NULL,
                total_count INTEGER NOT NULL, success_count INTEGER NOT NULL DEFAULT 0,
                partial_count INTEGER NOT NULL DEFAULT 0, failed_count INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL, error_summary TEXT
            );
        """)
        self.db.commit()

    def groups(self) -> list[sqlite3.Row]:
        return self.db.execute("SELECT * FROM competitor_groups ORDER BY name").fetchall()

    def add_group(self, name: str) -> int:
        name = name.strip()
        if not name:
            raise ValueError("分组名称不能为空")
        cursor = self.db.execute(
            "INSERT INTO competitor_groups(name, created_at) VALUES (?, ?)", (name, _now())
        )
        self.db.commit()
        return cursor.lastrowid

    def rename_group(self, group_id: int, name: str) -> None:
        name = name.strip()
        if not name:
            raise ValueError("分组名称不能为空")
        self.db.execute("UPDATE competitor_groups SET name=? WHERE id=?", (name, group_id))
        self.db.commit()

    def delete_group(self, group_id: int) -> None:
        self.db.execute("DELETE FROM competitor_groups WHERE id=?", (group_id,))
        self.db.commit()

    def add_competitor(self, url: str, group_id: int | None = None, alias: str = "", note: str = "") -> tuple[int, bool]:
        offer_id, canonical = parse_offer_url(url)
        existing = self.db.execute("SELECT id FROM competitors WHERE offer_id=?", (offer_id,)).fetchone()
        if existing:
            return existing["id"], False
        cursor = self.db.execute(
            """INSERT INTO competitors(offer_id,url,alias,group_id,note,created_at)
               VALUES (?,?,?,?,?,?)""",
            (offer_id, canonical, alias.strip() or None, group_id, note.strip() or None, _now()),
        )
        self.db.commit()
        return cursor.lastrowid, True

    def competitors(self, group_id: int | None = None, enabled_only: bool = False) -> list[sqlite3.Row]:
        clauses, params = [], []
        if group_id is not None:
            clauses.append("c.group_id=?"); params.append(group_id)
        if enabled_only:
            clauses.append("c.monitor_enabled=1")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        return self.db.execute(f"""
            SELECT c.*, g.name group_name,
              (SELECT COUNT(*) FROM snapshots s WHERE s.competitor_id=c.id) snapshot_count
            FROM competitors c LEFT JOIN competitor_groups g ON g.id=c.group_id
            {where} ORDER BY COALESCE(c.alias,c.title,c.offer_id)
        """, params).fetchall()

    def competitor(self, competitor_id: int) -> sqlite3.Row | None:
        return self.db.execute("SELECT * FROM competitors WHERE id=?", (competitor_id,)).fetchone()

    def update_competitor(self, competitor_id: int, *, alias: str, note: str, group_id: int | None) -> None:
        self.db.execute(
            "UPDATE competitors SET alias=?, note=?, group_id=? WHERE id=?",
            (alias.strip() or None, note.strip() or None, group_id, competitor_id),
        )
        self.db.commit()

    def set_enabled(self, competitor_id: int, enabled: bool) -> None:
        self.db.execute(
            "UPDATE competitors SET monitor_enabled=?, status=? WHERE id=?",
            (int(enabled), "待验证" if enabled else "暂停", competitor_id),
        )
        self.db.commit()

    def delete_competitor(self, competitor_id: int) -> None:
        self.db.execute("DELETE FROM competitors WHERE id=?", (competitor_id,))
        self.db.commit()

    def latest_snapshot(self, competitor_id: int) -> sqlite3.Row | None:
        return self.db.execute(
            "SELECT * FROM snapshots WHERE competitor_id=? ORDER BY collected_at DESC, id DESC LIMIT 1", (competitor_id,)
        ).fetchone()

    def latest_failure(self, competitor_id: int) -> str | None:
        row = self.db.execute(
            """SELECT detail_json FROM events WHERE competitor_id=? AND event_type='collection_failed'
               ORDER BY created_at DESC, id DESC LIMIT 1""", (competitor_id,)
        ).fetchone()
        return json.loads(row["detail_json"])["error"] if row else None

    def save_collection(self, competitor_id: int, result: CollectionResult) -> int | None:
        now = _now()
        if result.status == "failed" or not result.data:
            self.db.execute(
                "UPDATE competitors SET status='采集失败', last_attempt_at=? WHERE id=?", (now, competitor_id)
            )
            self.db.execute(
                """INSERT INTO events(competitor_id,event_type,severity,title,detail_json,created_at)
                   VALUES (?,'collection_failed','error','采集失败',?,?)""",
                (competitor_id, _json({"error": result.error or "未知错误"}), now),
            )
            self.db.commit()
            return None
        data = result.data
        status = data["collection_status"]
        price_min, price_max = parse_price_range(data.get("price_raw_values", []))
        sales_lower, sales_type = parse_metric(data.get("sales_raw"))
        month_lower, _ = parse_metric(data.get("month_sales_raw"))
        distribution_lower, _ = parse_metric(data.get("month_distribution_raw"))
        year_quantity_lower, _ = parse_metric(data.get("year_sales_quantity_raw"))
        year_orders_lower, _ = parse_metric(data.get("year_sales_orders_raw"))
        cursor = self.db.execute("""
            INSERT INTO snapshots(
              competitor_id,collected_at,snapshot_date,title,price_raw_values_json,price_tiers_json,
              display_price_min,display_price_max,min_order_qty,sales_raw,sales_lower_bound,sales_value_type,
              visible_sku_names_json,listed_at,month_sales_raw,month_sales_lower_bound,
              month_distribution_raw,month_distribution_lower_bound,
              year_sales_quantity_raw,year_sales_quantity_lower_bound,
              year_sales_orders_raw,year_sales_orders_lower_bound,
              selected_sku_name,selected_sku_price_raw,selected_sku_availability,
              selected_sku_stock_raw,review_count_raw,positive_rate_raw,collection_status,missing_fields_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            competitor_id, now, now[:10], data.get("title"), _json(data.get("price_raw_values", [])),
            _json(data.get("price_tiers", [])), price_min, price_max, data.get("min_order_qty"), data.get("sales_raw"),
            sales_lower, sales_type, _json(data.get("visible_sku_names", [])), data.get("listed_at"),
            data.get("month_sales_raw"), month_lower, data.get("month_distribution_raw"), distribution_lower,
            data.get("year_sales_quantity_raw"), year_quantity_lower,
            data.get("year_sales_orders_raw"), year_orders_lower,
            data.get("selected_sku_name"), data.get("selected_sku_price_raw"),
            data.get("selected_sku_availability"), data.get("selected_sku_stock_raw"),
            data.get("review_count_raw"), data.get("positive_rate_raw"), status, _json(data.get("missing_fields", [])),
        ))
        label = "正常" if status == "success" else "部分异常"
        self.db.execute(
            "UPDATE competitors SET title=?, status=?, last_success_at=?, last_attempt_at=? WHERE id=?",
            (data.get("title"), label, now, now, competitor_id),
        )
        self.db.commit()
        return cursor.lastrowid


class PlaywrightCollector:
    def __init__(self, cdp_url: str = "http://127.0.0.1:9222", extractor: Path | None = None) -> None:
        self.cdp_url = cdp_url
        self.extractor = extractor or Path(__file__).parents[1] / "tools" / "competitor_monitor" / "extract.js"

    def collect(self, url: str) -> CollectionResult:
        try:
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright
            with sync_playwright() as pw:
                browser = pw.chromium.connect_over_cdp(self.cdp_url, timeout=5000)
                if not browser.contexts:
                    raise RuntimeError("Chrome没有可用上下文")
                page = browser.contexts[0].new_page()
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    try:
                        page.wait_for_function(
                            "() => document.querySelector('.title-content h1') && document.body.innerText.includes('年成交')",
                            timeout=15000,
                        )
                    except PlaywrightTimeoutError:
                        pass
                    raw = page.evaluate(self.extractor.read_text(encoding="utf-8"))
                finally:
                    page.close()
            if not raw.get("product_detected"):
                return CollectionResult("failed", error="1688商品区未正常显示")
            if not raw.get("assistant_detected"):
                return CollectionResult("failed", error="1688官方采购助手未出现")
            data = normalize_collection(raw)
            return CollectionResult(data["collection_status"], data=data)
        except Exception as exc:
            return CollectionResult("failed", error=str(exc))


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False)
