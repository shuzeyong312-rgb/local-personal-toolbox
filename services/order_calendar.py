from __future__ import annotations

import json
import math
import os
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

DATA_VERSION = 2
PLATFORMS = (
    ("jd", "京东"), ("1688", "1688"), ("taobao", "淘宝 / 天猫"),
    ("pdd", "拼多多"), ("douyin", "抖音电商"), ("other", "其他"),
)
PLATFORM_NAMES = dict(PLATFORMS) | {"unknown": "未设置平台"}


def platform_name(item: dict) -> str:
    if item.get("platform") == "other" and str(item.get("custom_platform_name", "")).strip():
        return item["custom_platform_name"].strip()
    return PLATFORM_NAMES.get(item.get("platform", "unknown"), "未设置平台")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def task_status(target: int, actual: int, task_date: date, today: date | None = None) -> str:
    if actual >= target:
        return "completed"
    if actual > 0:
        return "partial"
    return "missed" if task_date < (today or date.today()) else "pending"


def review_status(actual: int, reviewed: int) -> str:
    if reviewed >= actual:
        return "reviewed"
    return "partial" if reviewed else "unreviewed"


def validate_data(data: dict) -> dict:
    if not isinstance(data, dict) or data.get("version") != DATA_VERSION:
        raise ValueError("不支持的数据格式")
    if not isinstance(data.get("plans"), list) or not isinstance(data.get("records"), list):
        raise ValueError("计划或记录格式错误")
    return data


def migrate_data(data: dict) -> dict:
    if not isinstance(data, dict) or data.get("version") not in {1, DATA_VERSION}:
        raise ValueError("不支持的数据格式")
    if not isinstance(data.get("plans"), list) or not isinstance(data.get("records"), list):
        raise ValueError("计划或记录格式错误")
    migrated = json.loads(json.dumps(data, ensure_ascii=False))
    for plan in migrated["plans"]:
        plan["model"] = str(plan.get("model") or plan.get("short_name") or plan.get("product_name") or "未命名").strip()
        plan.setdefault("platform", "unknown")
        plan.setdefault("custom_platform_name", "")
        plan.pop("product_name", None)
        plan.pop("short_name", None)
    for record in migrated["records"]:
        if not record.get("plan_id"):
            record["model"] = str(record.get("model") or record.get("short_name") or record.get("product_name") or "临时任务").strip()
            record.setdefault("platform", "unknown")
            record.setdefault("custom_platform_name", "")
        record.pop("product_name", None)
        record.pop("short_name", None)
    migrated["version"] = DATA_VERSION
    return validate_data(migrated)


class CalendarStore:
    def __init__(self, path: Path | str = Path("data/order_calendar.json")) -> None:
        self.path = Path(path)
        self.backup_dir = self.path.parent / "backups"
        self.recovery_message = ""

    def load(self) -> dict:
        if not self.path.exists():
            return {"version": DATA_VERSION, "plans": [], "records": []}
        try:
            return migrate_data(json.loads(self.path.read_text(encoding="utf-8")))
        except (OSError, ValueError, json.JSONDecodeError):
            for backup in sorted(self.backup_dir.glob("order_calendar_*.json"), reverse=True):
                try:
                    data = migrate_data(json.loads(backup.read_text(encoding="utf-8")))
                    self.recovery_message = "已从最近备份恢复出单日历数据"
                    return data
                except (OSError, ValueError, json.JSONDecodeError):
                    continue
            raise ValueError("数据读取失败，原文件已保留。")

    def save(self, data: dict) -> None:
        validate_data(data)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            shutil.copy2(self.path, self.backup_dir / f"order_calendar_{stamp}.json")
        temporary = self.path.with_suffix(".tmp")
        payload = json.dumps(data, ensure_ascii=False, indent=2)
        temporary.write_text(payload, encoding="utf-8")
        validate_data(json.loads(temporary.read_text(encoding="utf-8")))
        os.replace(temporary, self.path)
        backups = sorted(self.backup_dir.glob("order_calendar_*.json"), reverse=True)
        for old in backups[5:]:
            old.unlink()


class OrderCalendar:
    def __init__(self, store: CalendarStore | None = None) -> None:
        self.store = store or CalendarStore()
        self.data = self.store.load()

    @property
    def plans(self) -> list[dict]:
        return self.data["plans"]

    @property
    def records(self) -> list[dict]:
        return self.data["records"]

    def save(self) -> None:
        self.store.save(self.data)

    def add_plan(self, plan: dict) -> dict:
        plan = {**plan, "id": plan.get("id") or new_id("plan"), "status": plan.get("status", "active")}
        self._validate_plan(plan)
        self.plans.append(plan)
        self.save()
        return plan

    def update_plan(self, plan_id: str, changes: dict) -> dict:
        plan = self.plan(plan_id)
        yesterday = date.today() - timedelta(days=1)
        if parse_date(plan["start_date"]) <= yesterday:
            for task in self.scheduled(plan, parse_date(plan["start_date"]), yesterday):
                if not self.record_for(plan_id, parse_date(task["date"])):
                    self.records.append({
                        "id": new_id("record"), "plan_id": plan_id, "date": task["date"], "source": "schedule",
                        "target_quantity": task["target_quantity"], "actual_quantity": 0,
                        "reviewed_quantity": 0, "review_date": None, "note": "",
                    })
        if {"stages", "start_date", "initial_completed_quantity"} & changes.keys():
            changes["effective_date"] = date.today().isoformat()
        plan.update(changes)
        self._validate_plan(plan, allow_unknown=set(changes) <= {"status"})
        self.save()
        return plan

    def delete_plan(self, plan_id: str) -> None:
        self.data["plans"] = [item for item in self.plans if item["id"] != plan_id]
        self.data["records"] = [item for item in self.records if item.get("plan_id") != plan_id]
        self.save()

    def plan(self, plan_id: str) -> dict:
        return next(item for item in self.plans if item["id"] == plan_id)

    def active_plan(self, platform: str, model: str, exclude_id: str | None = None) -> dict | None:
        return next((plan for plan in self.plans if plan["id"] != exclude_id and plan.get("status") == "active"
                     and plan.get("platform") == platform and plan.get("model", "").casefold() == model.casefold()), None)

    @staticmethod
    def _validate_plan(plan: dict, allow_unknown: bool = False) -> None:
        if not str(plan.get("model", "")).strip():
            raise ValueError("型号不能为空")
        if plan.get("platform") not in PLATFORM_NAMES or (plan.get("platform") == "unknown" and not allow_unknown):
            raise ValueError("请选择平台")
        if plan.get("platform") == "other" and not str(plan.get("custom_platform_name", "")).strip():
            raise ValueError("请输入平台名称")
        parse_date(plan["start_date"])
        if not plan.get("stages"):
            raise ValueError("至少需要一个阶段")
        for stage in plan["stages"]:
            if stage.get("type") not in {"fixed_count", "until_total", "continuous"}:
                raise ValueError("阶段类型无效")
            if int(stage.get("frequency_days", 0)) < 1 or int(stage.get("target_quantity", 0)) < 1:
                raise ValueError("频率和目标数量必须大于 0")

    def record_for(self, plan_id: str, day: date) -> dict | None:
        key = day.isoformat()
        return next((item for item in self.records if item.get("plan_id") == plan_id and item["date"] == key), None)

    def upsert_record(self, plan_id: str | None, day: date, **changes) -> dict:
        if plan_id:
            changes.pop("platform", None)
            changes.pop("custom_platform_name", None)
            changes.pop("model", None)
        record = self.record_for(plan_id, day) if plan_id else None
        if record is None:
            record = {
                "id": new_id("record"), "plan_id": plan_id, "date": day.isoformat(),
                "source": changes.pop("source", "schedule"), "target_quantity": 1,
                "actual_quantity": 0, "reviewed_quantity": 0, "review_date": None, "note": "",
            }
            self.records.append(record)
        record.update(changes)
        if int(record["target_quantity"]) < 1 or int(record["actual_quantity"]) < 0:
            raise ValueError("数量无效")
        record["reviewed_quantity"] = min(max(int(record["reviewed_quantity"]), 0), int(record["actual_quantity"]))
        self.save()
        return record

    def scheduled(self, plan: dict, start: date, end: date) -> list[dict]:
        if plan.get("status") != "active":
            return []
        first_date = parse_date(plan.get("effective_date", plan["start_date"]))
        last_date: date | None = None
        planned_total = int(plan.get("initial_completed_quantity", 0))
        result: list[dict] = []
        for stage in plan["stages"]:
            kind = stage["type"]
            frequency = int(stage["frequency_days"])
            target = int(stage["target_quantity"])
            if kind == "fixed_count":
                occurrences = int(stage["count"])
            elif kind == "until_total":
                occurrences = math.ceil(max(int(stage["until_total"]) - planned_total, 0) / target)
            else:
                occurrences = None

            current = first_date if last_date is None else last_date + timedelta(days=frequency)
            generated = 0
            while current <= end and (occurrences is None or generated < occurrences):
                if current >= start:
                    result.append(self._task(plan, current, target))
                last_date = current
                planned_total += target
                generated += 1
                current += timedelta(days=frequency)
            if occurrences is None or generated < occurrences:
                return result
        return result

    def tasks_between(self, start: date, end: date) -> list[dict]:
        tasks = [task for plan in self.plans for task in self.scheduled(plan, start, end)]
        scheduled_keys = {(task["plan_id"], task["date"]) for task in tasks}
        for record in self.records:
            day = parse_date(record["date"])
            if start <= day <= end and (record.get("plan_id"), record["date"]) not in scheduled_keys:
                plan = next((p for p in self.plans if p["id"] == record.get("plan_id")), None)
                tasks.append({**record, "platform": plan["platform"] if plan else record.get("platform", "unknown"),
                              "custom_platform_name": plan.get("custom_platform_name", "") if plan else record.get("custom_platform_name", ""),
                              "model": plan["model"] if plan else record.get("model", "临时任务")})
        return sorted(tasks, key=lambda item: (item["date"], item["platform"], item["model"]))

    def _task(self, plan: dict, day: date, target: int) -> dict:
        record = self.record_for(plan["id"], day) or {}
        return {
            "plan_id": plan["id"], "date": day.isoformat(), "source": "schedule",
            "platform": plan["platform"], "custom_platform_name": plan.get("custom_platform_name", ""), "model": plan["model"],
            "target_quantity": int(record.get("target_quantity", target)),
            "actual_quantity": int(record.get("actual_quantity", 0)),
            "reviewed_quantity": int(record.get("reviewed_quantity", 0)),
            "review_date": record.get("review_date"), "note": record.get("note", ""),
        }

    def pending_reviews(self) -> list[dict]:
        tasks = []
        for record in self.records:
            if int(record.get("actual_quantity", 0)) <= int(record.get("reviewed_quantity", 0)):
                continue
            plan = next((item for item in self.plans if item["id"] == record.get("plan_id")), None)
            tasks.append({**record, "platform": plan["platform"] if plan else record.get("platform", "unknown"),
                          "custom_platform_name": plan.get("custom_platform_name", "") if plan else record.get("custom_platform_name", ""),
                          "model": plan["model"] if plan else record.get("model", "临时任务")})
        return sorted(tasks, key=lambda item: item["date"], reverse=True)

    def preview(self, plan: dict, count: int = 10) -> list[dict]:
        temporary = {**plan, "id": plan.get("id") or "preview", "status": "active"}
        return self.scheduled(temporary, parse_date(temporary["start_date"]),
                              parse_date(temporary["start_date"]) + timedelta(days=3650))[:count]
