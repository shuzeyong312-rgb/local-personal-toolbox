from __future__ import annotations

import json
import re
import shutil
import sqlite3
import subprocess
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse


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
    metadata = raw.get("page_metadata", {})

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
        "shop_name": optional(metadata.get("merchant_raw")),
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
    technical_error: str = ""
    recoverable: bool = False
    environment_error: bool = False


@dataclass
class EnvironmentResult:
    ready: bool
    error: str = ""
    technical_error: str = ""


class ChromeEnvironment:
    PROFILE = Path(r"C:\1688-monitor-profile")

    def __init__(self, cdp_url: str = "http://127.0.0.1:9222") -> None:
        self.cdp_url = cdp_url

    def is_ready(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.cdp_url.rstrip('/')}/json/version", timeout=1) as response:
                return response.status == 200
        except Exception:
            return False

    def ensure(self, timeout: float = 15) -> EnvironmentResult:
        if self.is_ready():
            return EnvironmentResult(True)
        try:
            self._start_chrome()
        except Exception as exc:
            return EnvironmentResult(False, "1688采集浏览器启动失败，请检查 Chrome 是否正常安装。", str(exc))
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.is_ready():
                return EnvironmentResult(True)
            time.sleep(0.25)
        return EnvironmentResult(False, "1688采集浏览器启动失败，请检查 Chrome 是否正常安装。", f"CDP在{timeout:g}秒内未就绪：{self.cdp_url}")

    def open_browser(self) -> None:
        self._start_chrome("https://www.1688.com/")

    def _start_chrome(self, url: str | None = None) -> None:
        chrome = self._chrome_path()
        args = [str(chrome), "--remote-debugging-port=9222", f"--user-data-dir={self.PROFILE}"]
        if url:
            args.extend(["--new-window", url])
        subprocess.Popen(args)

    @staticmethod
    def _chrome_path() -> Path:
        candidates = [
            Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
            Path.home() / r"AppData\Local\Google\Chrome\Application\chrome.exe",
        ]
        command = shutil.which("chrome.exe")
        if command:
            candidates.append(Path(command))
        for path in candidates:
            if path.exists():
                return path
        raise FileNotFoundError("未找到 chrome.exe")


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
        columns = {row["name"] for row in self.db.execute("PRAGMA table_info(competitors)")}
        if "shop_name" not in columns:
            self.db.execute("ALTER TABLE competitors ADD COLUMN shop_name TEXT")
        self.db.execute("UPDATE competitors SET status='最近采集失败' WHERE status='采集失败'")
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
              (SELECT COUNT(*) FROM snapshots s WHERE s.competitor_id=c.id) snapshot_count,
              (SELECT e.title FROM events e WHERE e.competitor_id=c.id
               AND e.event_type NOT IN ('collection_failed','collection_partial')
               ORDER BY e.created_at DESC,e.id DESC LIMIT 1) latest_change
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

    def daily_history(self, competitor_id: int, days: int) -> list[sqlite3.Row]:
        since = (datetime.now() - timedelta(days=days - 1)).strftime("%Y-%m-%d")
        return self.db.execute("""
            SELECT s.* FROM snapshots s WHERE s.competitor_id=? AND s.snapshot_date>=?
              AND s.collection_status IN ('success','partial')
              AND NOT EXISTS (
                SELECT 1 FROM snapshots later WHERE later.competitor_id=s.competitor_id
                  AND later.snapshot_date=s.snapshot_date AND later.collection_status IN ('success','partial')
                  AND (later.collected_at>s.collected_at OR (later.collected_at=s.collected_at AND later.id>s.id))
              )
            ORDER BY s.snapshot_date
        """, (competitor_id, since)).fetchall()

    def events(self, *, date: str | None = None, event_type: str | None = None,
               group_id: int | None = None) -> list[sqlite3.Row]:
        clauses, params = [], []
        if date:
            clauses.append("date(e.created_at)=?"); params.append(date)
        if event_type:
            clauses.append("e.event_type=?"); params.append(event_type)
        if group_id is not None:
            clauses.append("c.group_id=?"); params.append(group_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        return self.db.execute(f"""
            SELECT e.*, COALESCE(c.alias,c.title,c.offer_id) competitor_name, g.name group_name
            FROM events e JOIN competitors c ON c.id=e.competitor_id
            LEFT JOIN competitor_groups g ON g.id=c.group_id
            {where}
            ORDER BY CASE e.severity WHEN 'important' THEN 0 WHEN 'warning' THEN 1
                     WHEN 'error' THEN 2 ELSE 3 END, e.created_at DESC, e.id DESC
        """, params).fetchall()

    def today_summary(self) -> dict:
        today = datetime.now().strftime("%Y-%m-%d")
        total = self.db.execute("SELECT COUNT(*) FROM competitors WHERE monitor_enabled=1").fetchone()[0]
        row = self.db.execute("""SELECT
              SUM(CASE WHEN status='正常' THEN 1 ELSE 0 END) success,
              SUM(CASE WHEN status='部分异常' THEN 1 ELSE 0 END) partial,
              SUM(CASE WHEN status='最近采集失败' THEN 1 ELSE 0 END) failed
            FROM competitors WHERE monitor_enabled=1 AND date(last_attempt_at)=?""", (today,)).fetchone()
        counts = {item["event_type"]: item["count"] for item in self.db.execute(
            "SELECT event_type,COUNT(*) count FROM events WHERE date(created_at)=? GROUP BY event_type", (today,)
        )}
        return {"total": total, "success": row["success"] or 0,
                "partial": row["partial"] or 0, "failed": row["failed"] or 0,
                "price": counts.get("price_change", 0) + counts.get("price_structure_change", 0),
                "sku": counts.get("sku_added", 0) + counts.get("sku_removed", 0),
                "sales": counts.get("sales_metric_jump", 0)}

    def latest_failure(self, competitor_id: int) -> str | None:
        details = self.latest_failure_details(competitor_id)
        return details["error"] if details else None

    def latest_failure_details(self, competitor_id: int) -> dict | None:
        row = self.db.execute(
            """SELECT detail_json FROM events WHERE competitor_id=? AND event_type='collection_failed'
               ORDER BY created_at DESC, id DESC LIMIT 1""", (competitor_id,)
        ).fetchone()
        return json.loads(row["detail_json"]) if row else None

    def start_run(self, total: int, trigger_type: str = "manual", now: str | None = None) -> int:
        cursor = self.db.execute(
            """INSERT INTO monitor_runs(started_at,trigger_type,total_count,status)
               VALUES (?,?,?,'preparing_environment')""", (now or _now(), trigger_type, total)
        )
        self.db.commit()
        return cursor.lastrowid

    def finish_run(self, run_id: int, status: str, success: int = 0, partial: int = 0,
                   failed: int = 0, error: str | None = None, now: str | None = None) -> None:
        self.db.execute(
            """UPDATE monitor_runs SET finished_at=?,success_count=?,partial_count=?,failed_count=?,
               status=?,error_summary=? WHERE id=?""",
            (now or _now(), success, partial, failed, status, error, run_id),
        )
        self.db.commit()

    def latest_run(self) -> sqlite3.Row | None:
        return self.db.execute("SELECT * FROM monitor_runs ORDER BY id DESC LIMIT 1").fetchone()

    def completed_scheduled_run(self, date: str) -> bool:
        return self.db.execute("""SELECT 1 FROM monitor_runs
            WHERE trigger_type='scheduled' AND date(started_at)=? AND status='completed' LIMIT 1""",
            (date,)).fetchone() is not None

    def latest_event_id(self) -> int:
        return self.db.execute("SELECT COALESCE(MAX(id),0) FROM events").fetchone()[0]

    def events_after(self, event_id: int) -> list[sqlite3.Row]:
        return self.db.execute("""SELECT e.*, COALESCE(c.alias,c.title,c.offer_id) competitor_name
            FROM events e JOIN competitors c ON c.id=e.competitor_id
            WHERE e.id>? ORDER BY e.id""", (event_id,)).fetchall()

    def save_collection(self, competitor_id: int, result: CollectionResult, *,
                        price_threshold: float = 5, sales_threshold: int = 20) -> int | None:
        now = _now()
        if result.status == "failed" or not result.data:
            self.db.execute(
                "UPDATE competitors SET status='最近采集失败', last_attempt_at=? WHERE id=?", (now, competitor_id)
            )
            self.db.execute(
                """INSERT INTO events(competitor_id,event_type,severity,title,detail_json,created_at)
                   VALUES (?,'collection_failed','error','采集失败',?,?)""",
                (competitor_id, _json({"error": result.error or "未知错误", "technical_error": result.technical_error}), now),
            )
            self.db.commit()
            return None
        previous = self.latest_snapshot(competitor_id)
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
            """UPDATE competitors SET title=?, shop_name=COALESCE(?,shop_name), status=?,
               last_success_at=?, last_attempt_at=? WHERE id=?""",
            (data.get("title"), data.get("shop_name"), label, now, now, competitor_id),
        )
        if status == "partial":
            self.db.execute("""INSERT INTO events(
                competitor_id,snapshot_id,event_type,severity,title,detail_json,created_at
            ) VALUES (?,?,'collection_partial','warning','采集部分异常',?,?)""",
                (competitor_id, cursor.lastrowid, _json({"missing_fields": data.get("missing_fields", [])}), now))
        if previous:
            self._record_changes(competitor_id, cursor.lastrowid, previous, data, now,
                                 price_threshold, sales_threshold)
        self.db.commit()
        return cursor.lastrowid

    def _record_changes(self, competitor_id: int, snapshot_id: int, previous: sqlite3.Row,
                        current: dict, now: str, price_threshold: float, sales_threshold: int) -> None:
        def add(event_type: str, title: str, detail: dict, severity: str = "info") -> None:
            self.db.execute("""INSERT INTO events(
                competitor_id,snapshot_id,event_type,severity,title,detail_json,created_at
            ) VALUES (?,?,?,?,?,?,?)""",
                (competitor_id, snapshot_id, event_type, severity, title, _json(detail), now))

        old_prices = json.loads(previous["price_raw_values_json"])
        new_prices = current.get("price_raw_values", [])
        if old_prices and new_prices and old_prices != new_prices:
            detail = {"before": old_prices, "after": new_prices}
            if len(old_prices) == len(new_prices) == 1:
                old, new = parse_price_range(old_prices)[0], parse_price_range(new_prices)[0]
                if old and new is not None:
                    change = round((new - old) / old * 100, 2)
                    detail["change_percent"] = change
                    add("price_change", "页面展示价格变化", detail,
                        "important" if abs(change) >= price_threshold else "info")
            else:
                old_tiers = {item.get("qty_raw"): item.get("price_raw")
                             for item in json.loads(previous["price_tiers_json"]) if item.get("qty_raw")}
                new_tiers = {item.get("qty_raw"): item.get("price_raw")
                             for item in current.get("price_tiers", []) if item.get("qty_raw")}
                tier_changes = []
                if old_tiers and old_tiers.keys() == new_tiers.keys():
                    for qty in old_tiers:
                        old = parse_price_range([old_tiers[qty]])[0]
                        new = parse_price_range([new_tiers[qty]])[0]
                        if old and new is not None and old != new:
                            tier_changes.append({"qty_raw": qty, "before": old_tiers[qty],
                                                 "after": new_tiers[qty],
                                                 "change_percent": round((new - old) / old * 100, 2)})
                if tier_changes:
                    detail["tier_changes"] = tier_changes
                    add("price_change", "页面展示价格变化", detail,
                        "important" if any(abs(item["change_percent"]) >= price_threshold for item in tier_changes) else "info")
                else:
                    add("price_structure_change", "价格结构发生变化", detail)

        old_skus = json.loads(previous["visible_sku_names_json"])
        new_skus = current.get("visible_sku_names", [])
        if old_skus and new_skus:
            old_normalized = {name.strip(): name for name in old_skus if name.strip()}
            new_normalized = {name.strip(): name for name in new_skus if name.strip()}
            added = [new_normalized[name] for name in new_normalized.keys() - old_normalized.keys()]
            removed = [old_normalized[name] for name in old_normalized.keys() - new_normalized.keys()]
            if added: add("sku_added", "新增SKU", {"items": sorted(added)}, "important")
            if removed: add("sku_removed", "删除SKU", {"items": sorted(removed)}, "important")

        metrics = (
            ("sales_raw", "页面已售展示发生变化", "sales_lower_bound", "sales_metric_jump"),
            ("month_sales_raw", "月成交展示发生变化", "month_sales_lower_bound", "metric_change"),
            ("month_distribution_raw", "月代销展示发生变化", "month_distribution_lower_bound", "metric_change"),
            ("year_sales_quantity_raw", "年成交件数展示发生变化", "year_sales_quantity_lower_bound", "metric_change"),
            ("year_sales_orders_raw", "年成交笔数展示发生变化", "year_sales_orders_lower_bound", "metric_change"),
            ("listed_at", "上架时间发生变化", None, "metric_change"),
            ("review_count_raw", "评论数发生变化", None, "metric_change"),
            ("positive_rate_raw", "好评率发生变化", None, "metric_change"),
        )
        for field, title, lower_field, event_type in metrics:
            old, new = previous[field], current.get(field)
            if old in (None, "") or new in (None, "") or old == new:
                continue
            detail = {"before": old, "after": new, "metric": field}
            severity = "info"
            if lower_field:
                old_lower, _ = parse_metric(old)
                new_lower, _ = parse_metric(new)
                if old_lower is not None and new_lower is not None:
                    detail["lower_bound_change"] = new_lower - old_lower
                    if field == "sales_raw" and new_lower - old_lower >= sales_threshold:
                        severity = "important"
            add(event_type, title, detail, severity)


class PlaywrightCollector:
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
                        return CollectionResult("failed", error="1688商品不存在或已下架", technical_error=f"HTTP 404: {url}")
                    try:
                        page.wait_for_function(
                            "() => document.querySelector('.title-content h1') && document.body.innerText.includes('年成交')",
                            timeout=15000,
                        )
                    except PlaywrightTimeoutError:
                        pass
                    raw = page.evaluate(self.extractor.read_text(encoding="utf-8"))
                    final_url = page.url
                finally:
                    page.close()
            if raw.get("login_evidence_raw") or "login" in urlparse(final_url).path.lower():
                return CollectionResult("failed", error="1688登录状态已失效，请在专用Chrome中重新登录后重试。",
                                        technical_error=_json({"url": final_url, "login_evidence": raw.get("login_evidence_raw", [])}),
                                        environment_error=True)
            if not raw.get("product_detected"):
                return CollectionResult("failed", error="商品数据未完整加载",
                                        technical_error=_json({"url": final_url, "dom": raw.get("dom_structure"),
                                                               "unavailable": raw.get("unavailable_reasons")}),
                                        recoverable=True)
            if not raw.get("assistant_detected"):
                return CollectionResult("failed", error="官方采购助手未加载",
                                        technical_error=_json({"url": final_url, "dom": raw.get("dom_structure"),
                                                               "unavailable": raw.get("unavailable_reasons")}),
                                        recoverable=True)
            data = normalize_collection(raw)
            return CollectionResult(data["collection_status"], data=data,
                                    recoverable=data["collection_status"] == "partial" and len(data["missing_fields"]) >= 5)
        except Exception as exc:
            raw = str(exc)
            if "connect_over_cdp" in raw or "ECONNREFUSED" in raw or "browser has been closed" in raw:
                return CollectionResult("failed", error="采集环境未连接", technical_error=raw,
                                        environment_error=True)
            deterministic = "ERR_NAME_NOT_RESOLVED" in raw or "HTTP 404" in raw
            return CollectionResult("failed", error="1688页面加载失败", technical_error=raw,
                                    recoverable=not deterministic)


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False)
