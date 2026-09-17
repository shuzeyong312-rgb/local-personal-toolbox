from __future__ import annotations

import base64
import json
import subprocess
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from services.competitor_monitor import ChromeEnvironment, MonitorStore, PlaywrightCollector


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def windows_toast(title: str, body: str) -> None:
    def quote(value: str) -> str:
        return escape(value).replace("'", "''")

    script = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
[Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml('<toast><visual><binding template="ToastGeneric"><text>{quote(title)}</text><text>{quote(body)}</text></binding></visual></toast>')
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('本地个人工具箱').Show([Windows.UI.Notifications.ToastNotification]::new($xml))
"""
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
                   check=False, capture_output=True, text=True, creationflags=0x08000000)


class TaskScheduler:
    DAILY = "LocalToolbox-1688Monitor-Daily"
    LOGON = "LocalToolbox-1688Monitor-CatchUp"

    def __init__(self, python: Path, main: Path) -> None:
        self.command = f'"{python}" "{main}" --competitor-monitor-auto'

    def install(self, scheduled_time: str, catch_up: bool = True) -> None:
        commands = [["schtasks", "/Create", "/TN", self.DAILY, "/TR", self.command,
                     "/SC", "DAILY", "/ST", scheduled_time, "/F"]]
        if catch_up:
            commands.append(["schtasks", "/Create", "/TN", self.LOGON, "/TR", self.command,
                             "/SC", "ONLOGON", "/F"])
        else:
            subprocess.run(["schtasks", "/Delete", "/TN", self.LOGON, "/F"],
                           capture_output=True, text=True, creationflags=0x08000000)
        for command in commands:
            result = subprocess.run(command, capture_output=True, text=True, creationflags=0x08000000)
            if result.returncode:
                raise RuntimeError(result.stderr.strip() or "无法创建 Windows 计划任务")

    def remove(self) -> None:
        for name in (self.DAILY, self.LOGON):
            subprocess.run(["schtasks", "/Delete", "/TN", name, "/F"],
                           capture_output=True, text=True, creationflags=0x08000000)


class AutoMonitor:
    def __init__(self, store: MonitorStore, *, scheduled_time: str = "09:00",
                 cdp_url: str = "http://127.0.0.1:9222", price_threshold: float = 5,
                 sales_threshold: int = 20, notification_enabled: bool = True,
                 environment=None, collector=None, notifier=windows_toast) -> None:
        self.store = store; self.scheduled_time = scheduled_time
        self.price_threshold = price_threshold; self.sales_threshold = sales_threshold
        self.notification_enabled = notification_enabled
        self.environment = environment or ChromeEnvironment(cdp_url)
        self.collector = collector or PlaywrightCollector(cdp_url)
        self.notifier = notifier

    def run(self, now: datetime | None = None) -> str:
        now = now or datetime.now()
        if now.strftime("%H:%M") < self.scheduled_time:
            return "not_due"
        if self.store.completed_scheduled_run(now.strftime("%Y-%m-%d")):
            return "already_completed"
        competitors = [dict(row) for row in self.store.competitors(enabled_only=True)]
        timestamp = _now(); run_id = self.store.start_run(len(competitors), "scheduled", timestamp)
        ready = self.environment.ensure()
        if not ready.ready:
            self.store.finish_run(run_id, "environment_failed", error=ready.technical_error or ready.error, now=timestamp)
            if self.notification_enabled: self.notifier("1688竞品监控自动采集失败", ready.error)
            return "environment_failed"
        first_event = self.store.latest_event_id()
        counts = {"success": 0, "partial": 0, "failed": 0}
        for competitor in competitors:
            try:
                result = self.collector.collect(competitor["url"])
            except Exception as exc:
                self.store.finish_run(run_id, "failed", **counts, error=str(exc), now=_now())
                if self.notification_enabled: self.notifier("1688竞品监控自动采集失败", str(exc))
                return "failed"
            if result.environment_error:
                self.store.finish_run(run_id, "environment_failed", **counts,
                                      error=result.technical_error or result.error, now=_now())
                if self.notification_enabled: self.notifier("1688竞品监控自动采集失败", result.error)
                return "environment_failed"
            counts[result.status] += 1
            self.store.save_collection(competitor["id"], result,
                                       price_threshold=self.price_threshold,
                                       sales_threshold=self.sales_threshold)
        self.store.finish_run(run_id, "completed", **counts, now=_now())
        if self.notification_enabled:
            self._notify(self.store.events_after(first_event))
            if counts["failed"]:
                self.notifier("1688竞品监控存在采集失败", f"本轮有 {counts['failed']} 个商品采集失败，请打开异常事件查看原因。")
        return "completed"

    def _notify(self, events) -> None:
        grouped = {}
        for event in events:
            if event["event_type"] not in ("price_change", "sku_added", "sku_removed", "sales_metric_jump"):
                continue
            if event["event_type"] in ("price_change", "sales_metric_jump") and event["severity"] != "important":
                continue
            grouped.setdefault((event["competitor_id"], event["competitor_name"]), []).append(event)
        for (_competitor_id, name), items in grouped.items():
            lines = []
            for event in items:
                detail = json.loads(event["detail_json"])
                if detail.get("items"):
                    lines.append(f"{event['title']}：{'、'.join(detail['items'])}")
                elif "lower_bound_change" in detail:
                    lines.append(f"页面已售：{detail['before']} → {detail['after']}，展示下界 {detail['lower_bound_change']:+d}")
                elif "change_percent" in detail:
                    lines.append(f"价格：{detail['before']} → {detail['after']}（{detail['change_percent']:+g}%）")
                elif detail.get("tier_changes"):
                    lines.append("价格：" + "；".join(
                        f"{change['qty_raw']} {change['before']} → {change['after']}（{change['change_percent']:+g}%）"
                        for change in detail["tier_changes"]
                    ))
            if lines: self.notifier(f"{name}发生重要变化", "\n".join(lines))
