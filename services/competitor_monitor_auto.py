from __future__ import annotations

import base64
import json
import subprocess
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from services.competitor_monitor import MonitorStore
from services.competitor_monitor_batch import MAX_PARALLEL_COLLECTIONS, collect_batch
from services.competitor_monitor_window import (
    BackgroundChromeEnvironment,
    PlaywrightCollector,
    park_monitor_chrome,
    restore_monitor_chrome,
)


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
        self.environment = environment or BackgroundChromeEnvironment(cdp_url)
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
        pending = list(competitors)
        verification_count = 0
        post_verification_successes = 0

        try:
            while pending:
                serial_recovery = verification_count and post_verification_successes < 2
                parallel = 1 if serial_recovery else min(MAX_PARALLEL_COLLECTIONS, len(pending))
                batch = collect_batch(pending, self.collector, max_workers=parallel)
                verification_item = None
                try:
                    for competitor, result in batch:
                        if result.status == "needs_verification":
                            verification_item = competitor
                            break
                        if result.environment_error:
                            self.store.finish_run(run_id, "environment_failed", **counts,
                                                  error=result.technical_error or result.error, now=_now())
                            if self.notification_enabled: self.notifier("1688竞品监控自动采集失败", result.error)
                            return "environment_failed"
                        counts[result.status] += 1
                        pending = [item for item in pending if item["id"] != competitor["id"]]
                        self.store.save_collection(competitor["id"], result,
                                                   price_threshold=self.price_threshold,
                                                   sales_threshold=self.sales_threshold)
                        if serial_recovery and result.status == "success":
                            post_verification_successes += 1
                            if post_verification_successes >= 2:
                                break
                finally:
                    if verification_item is None:
                        batch.close()

                if verification_item is None:
                    continue

                verification_count += 1
                restore_monitor_chrome(BackgroundChromeEnvironment.PROFILE)
                if verification_count >= 2:
                    message = "1688再次需要人工验证，本轮采集已暂停，请稍后再试。"
                    if self.notification_enabled: self.notifier("1688竞品监控已暂停", message)
                    abandon = getattr(self.collector, "abandon_verification", None)
                    if callable(abandon): abandon()
                    batch.close()
                    self.store.finish_run(run_id, "verification_repeated", **counts, error=message, now=_now())
                    return "verification_repeated"

                message = "1688需要人工验证，请在专用浏览器中完成验证。验证通过后将自动继续采集。"
                self.store.update_run_status(run_id, "needs_verification", message)
                if self.notification_enabled: self.notifier("1688需要人工验证", message)
                wait_for_verification = getattr(self.collector, "wait_for_verification", None)
                verified = callable(wait_for_verification) and wait_for_verification(timeout=300, interval=1.5)
                batch.close()
                if not verified:
                    message = "人工验证等待超时，本轮采集已暂停"
                    if self.notification_enabled: self.notifier("1688竞品监控已暂停", message)
                    abandon = getattr(self.collector, "abandon_verification", None)
                    if callable(abandon): abandon()
                    self.store.finish_run(run_id, "verification_timeout", **counts, error=message, now=_now())
                    return "verification_timeout"

                park_monitor_chrome(BackgroundChromeEnvironment.PROFILE)
                target_url = getattr(self.collector, "verification_target_url", lambda: None)()
                if isinstance(target_url, str):
                    pending.sort(key=lambda item: item["url"] != target_url)
                post_verification_successes = 0
        except Exception as exc:
            self.store.finish_run(run_id, "failed", **counts, error=str(exc), now=_now())
            if self.notification_enabled: self.notifier("1688竞品监控自动采集失败", str(exc))
            return "failed"

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
