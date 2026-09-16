import json
import tempfile
import unittest
from unittest.mock import patch
from datetime import date
from pathlib import Path

from services.order_calendar import CalendarStore, OrderCalendar, review_status, task_status


def y35_plan(platform: str = "jd", plan_id: str = "plan_y35") -> dict:
    return {
        "id": plan_id, "platform": platform, "custom_platform_name": "", "model": "Y35",
        "start_date": "2026-09-16", "initial_completed_quantity": 0, "status": "active", "note": "",
        "stages": [
            {"type": "fixed_count", "count": 3, "frequency_days": 1, "target_quantity": 1},
            {"type": "until_total", "until_total": 10, "frequency_days": 2, "target_quantity": 1},
            {"type": "continuous", "frequency_days": 7, "target_quantity": 1},
        ],
    }


class OrderCalendarTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.store = CalendarStore(Path(self.temp.name) / "data" / "order_calendar.json")
        self.calendar = OrderCalendar(self.store)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_y35_schedule_completion_review_and_missed_status(self) -> None:
        self.calendar.add_plan(y35_plan())
        dates = [task["date"] for task in self.calendar.tasks_between(date(2026, 9, 1), date(2026, 10, 30))]
        self.assertEqual([
            "2026-09-16", "2026-09-17", "2026-09-18",
            "2026-09-20", "2026-09-22", "2026-09-24", "2026-09-26", "2026-09-28", "2026-09-30", "2026-10-02",
            "2026-10-09", "2026-10-16", "2026-10-23", "2026-10-30",
        ], dates)
        record = self.calendar.upsert_record("plan_y35", date(2026, 9, 16), actual_quantity=1)
        self.assertEqual("completed", task_status(1, record["actual_quantity"], date(2026, 9, 16)))
        self.assertEqual("unreviewed", review_status(1, 0))
        record = self.calendar.upsert_record("plan_y35", date(2026, 9, 16), reviewed_quantity=1, review_date="2026-09-19")
        self.assertEqual("reviewed", review_status(1, record["reviewed_quantity"]))
        self.assertEqual("missed", task_status(1, 0, date(2026, 9, 20), date(2026, 9, 21)))

    def test_initial_quantity_and_target_quantity_control_occurrence_count(self) -> None:
        plan = y35_plan()
        plan["stages"] = [{"type": "until_total", "until_total": 10, "frequency_days": 2, "target_quantity": 2}]
        plan["initial_completed_quantity"] = 5
        self.calendar.add_plan(plan)
        dates = [task["date"] for task in self.calendar.tasks_between(date(2026, 9, 1), date(2026, 10, 10))]
        self.assertEqual(["2026-09-16", "2026-09-18", "2026-09-20"], dates)

    def test_actual_quantity_does_not_move_future_schedule(self) -> None:
        self.calendar.add_plan(y35_plan())
        before = [task["date"] for task in self.calendar.tasks_between(date(2026, 9, 1), date(2026, 10, 10))]
        self.calendar.upsert_record("plan_y35", date(2026, 9, 16), actual_quantity=99)
        after = [task["date"] for task in self.calendar.tasks_between(date(2026, 9, 1), date(2026, 10, 10))]
        self.assertEqual(before, after)

    def test_stage_display_uses_planned_not_actual_quantity(self) -> None:
        from tools.order_calendar.page import PlanManagerDialog

        plan = y35_plan()
        self.assertEqual("前 3 次", PlanManagerDialog._stage(plan, 0))
        self.assertEqual("每 2 天", PlanManagerDialog._stage(plan, 3))
        self.assertEqual("每 7 天", PlanManagerDialog._stage(plan, 10))

    def test_preview_and_saved_schedule_match_without_mutating_stages(self) -> None:
        plan = y35_plan()
        original = json.loads(json.dumps(plan["stages"]))
        preview = self.calendar.preview(plan)
        self.assertEqual(original, plan["stages"])
        self.calendar.add_plan(plan)
        saved = self.calendar.tasks_between(date(2026, 9, 16), date(2036, 9, 16))[:10]
        self.assertEqual([task["date"] for task in preview], [task["date"] for task in saved])
        self.assertEqual(original, self.calendar.plan("plan_y35")["stages"])

    def test_manual_record_and_day_override_are_preserved(self) -> None:
        self.calendar.add_plan(y35_plan())
        self.calendar.upsert_record("plan_y35", date(2026, 9, 20), target_quantity=2, actual_quantity=1)
        self.calendar.upsert_record(None, date(2026, 9, 25), source="manual", platform="1688", model="A404", target_quantity=1)
        tasks = self.calendar.tasks_between(date(2026, 9, 20), date(2026, 9, 25))
        self.assertEqual(2, next(task for task in tasks if task["date"] == "2026-09-20")["target_quantity"])
        self.assertEqual("manual", next(task for task in tasks if task["date"] == "2026-09-25")["source"])
        manual = next(task for task in tasks if task["date"] == "2026-09-25")
        self.assertEqual(("1688", "A404"), (manual["platform"], manual["model"]))

    def test_plan_edit_freezes_past_and_recalculates_today_forward(self) -> None:
        self.calendar.add_plan(y35_plan())
        with patch("services.order_calendar.date") as clock:
            clock.today.return_value = date(2026, 9, 21)
            clock.fromisoformat.side_effect = date.fromisoformat
            self.calendar.update_plan("plan_y35", {"stages": [{"type": "continuous", "frequency_days": 7, "target_quantity": 2}]})
        historical = self.calendar.tasks_between(date(2026, 9, 16), date(2026, 9, 20))
        self.assertEqual(["2026-09-16", "2026-09-17", "2026-09-18", "2026-09-20"], [task["date"] for task in historical])
        self.assertEqual(1, historical[0]["target_quantity"])

    def clock(self, day):
        clock = patch("services.order_calendar.date").start()
        self.addCleanup(patch.stopall)
        clock.today.return_value = date(2026, 9, day)
        clock.fromisoformat.side_effect = date.fromisoformat
        return clock

    def daily(self):
        plan = y35_plan()
        plan["stages"] = [{"type": "continuous", "frequency_days": 1, "target_quantity": 1}]
        return self.calendar.add_plan(plan)

    def dates(self):
        return [t["date"] for t in self.calendar.tasks_between(date(2026, 9, 10), date(2026, 9, 25))]

    def test_change_start_date_today_to_tomorrow(self):
        self.clock(16)
        self.daily()
        self.calendar.update_plan("plan_y35", {"start_date": "2026-09-17"})
        self.assertEqual("2026-09-17", self.dates()[0])

    def test_change_start_date_to_future(self):
        self.clock(16)
        self.daily()
        self.calendar.update_plan("plan_y35", {"start_date": "2026-09-20"})
        self.assertEqual("2026-09-20", self.dates()[0])

    def test_save_plan_without_changes_does_not_reschedule(self):
        self.clock(20)
        plan = self.daily()
        before = self.calendar.tasks_between(date(2026, 9, 10), date(2026, 9, 25))
        self.calendar.update_plan(plan["id"], json.loads(json.dumps(plan)))
        self.assertEqual(before, self.calendar.tasks_between(date(2026, 9, 10), date(2026, 9, 25)))
        self.assertNotIn("effective_date", self.calendar.plan(plan["id"]))
        self.assertEqual([], self.calendar.records)

    def test_edit_note_does_not_reschedule(self):
        self.clock(20)
        self.daily()
        before = self.dates()
        self.calendar.update_plan("plan_y35", {"note": "changed"})
        self.assertEqual(before, self.dates())
        self.assertNotIn("effective_date", self.calendar.plan("plan_y35"))

    def test_edit_model_does_not_reschedule(self):
        self.clock(20)
        self.daily()
        before = self.dates()
        self.calendar.update_plan("plan_y35", {"model": "A404"})
        self.assertEqual(before, self.dates())
        self.assertNotIn("effective_date", self.calendar.plan("plan_y35"))

    def test_preview_matches_saved_schedule(self):
        self.clock(20)
        plan = self.daily()
        self.calendar.upsert_record(plan["id"], date(2026, 9, 21), target_quantity=9)
        changes = {**plan, "start_date": "2026-09-21"}
        preview = self.calendar.preview(changes, 5)
        saved = self.calendar.update_plan(plan["id"], changes)
        self.assertEqual(preview, self.calendar.scheduled(saved, date(2026, 9, 20), date(2026, 9, 25)))

    def test_schedule_edit_preserves_past(self):
        self.clock(20)
        self.daily()
        before = self.calendar.tasks_between(date(2026, 9, 16), date(2026, 9, 19))
        self.calendar.update_plan("plan_y35", {"start_date": "2026-09-25"})
        after = self.calendar.tasks_between(date(2026, 9, 16), date(2026, 9, 19))
        for task in after:
            task.pop("id", None)
        self.assertEqual(before, after)

    def test_schedule_edit_recalculates_today_and_future(self):
        self.clock(20)
        self.daily()
        self.calendar.update_plan("plan_y35", {"start_date": "2026-09-10"})
        self.assertEqual(["2026-09-16", "2026-09-17", "2026-09-18", "2026-09-19"], self.dates()[:4])
        self.assertEqual("2026-09-20", self.dates()[4])
        self.assertNotIn("2026-09-10", self.dates())

    def test_future_schedule_override_does_not_create_ghost_task(self):
        self.clock(16)
        plan = self.daily()
        self.calendar.upsert_record(plan["id"], date(2026, 9, 18), target_quantity=9)
        self.calendar.update_plan(plan["id"], {"start_date": "2026-09-17", "stages": [
            {"type": "continuous", "frequency_days": 2, "target_quantity": 1}]})
        self.assertNotIn("2026-09-18", self.dates())
        self.assertEqual([], self.calendar.records)

    def test_future_actual_record_is_not_lost(self):
        self.clock(16)
        plan = self.daily()
        actual = self.calendar.upsert_record(plan["id"], date(2026, 9, 18), actual_quantity=2)
        self.calendar.update_plan(plan["id"], {"start_date": "2026-09-20"})
        self.assertEqual(actual, self.calendar.record(actual["id"]))
        self.assertIn("2026-09-18", self.dates())

    def manual_update(self, **changes):
        record = self.calendar.upsert_record(None, date(2026, 9, 18), source="manual", platform="jd", model="A404")
        self.calendar.upsert_record(None, date(2026, 9, 18), record_id=record["id"], **changes)
        self.assertEqual(1, len(self.calendar.records))
        self.assertEqual(record["id"], self.calendar.records[0]["id"])

    def test_manual_task_edit_does_not_duplicate(self):
        self.manual_update(note="edited")

    def test_manual_task_complete_does_not_duplicate(self):
        self.manual_update(actual_quantity=1)

    def test_manual_task_review_does_not_duplicate(self):
        self.manual_update(actual_quantity=1, reviewed_quantity=1)

    def test_pause_does_not_generate_tasks(self):
        self.clock(17)
        self.daily()
        self.calendar.update_plan("plan_y35", {"status": "paused"})
        self.assertEqual(["2026-09-16"], self.dates())

    def test_resume_does_not_backfill_paused_dates(self):
        clock = self.clock(17)
        self.daily()
        self.calendar.update_plan("plan_y35", {"status": "paused"})
        clock.today.return_value = date(2026, 9, 20)
        self.calendar.update_plan("plan_y35", {"status": "active"})
        self.assertEqual(["2026-09-16", "2026-09-20"], self.dates()[:2])
        reloaded = OrderCalendar(self.store)
        self.assertEqual(self.dates(), [t["date"] for t in reloaded.tasks_between(date(2026, 9, 10), date(2026, 9, 25))])

    def test_invalid_plan_update_is_transactional(self):
        self.clock(20)
        self.daily()
        before = json.loads(json.dumps(self.calendar.data))
        tasks = self.dates()
        payload = self.store.path.read_bytes()
        with self.assertRaises(ValueError):
            self.calendar.update_plan("plan_y35", {"model": "", "start_date": "2026-09-25"})
        self.assertEqual(before, self.calendar.data)
        self.assertEqual(tasks, self.dates())
        self.assertEqual(payload, self.store.path.read_bytes())

    def test_edit_plan_duplicate_platform_model(self):
        self.clock(16)
        self.daily()
        self.calendar.add_plan({**y35_plan(plan_id="other"), "model": "A404"})
        before = json.loads(json.dumps(self.calendar.data))
        with self.assertRaises(ValueError):
            self.calendar.update_plan("other", {"model": "y35"})
        self.assertEqual(before, self.calendar.data)
        self.calendar.update_plan("plan_y35", {"model": "Y35"})

    def test_start_date_is_never_bypassed_by_effective_date(self):
        plan = {**y35_plan(), "start_date": "2026-09-20", "effective_date": "2026-09-16"}
        self.calendar.add_plan(plan)
        self.assertEqual("2026-09-20", self.dates()[0])

    def test_resume_continues_remaining_stage_occurrences(self):
        clock = self.clock(18)
        self.calendar.add_plan(y35_plan())
        self.calendar.update_plan("plan_y35", {"status": "paused"})
        clock.today.return_value = date(2026, 9, 22)
        plan = self.calendar.update_plan("plan_y35", {"status": "active"})
        dates = [t["date"] for t in self.calendar.scheduled(plan, date(2026, 9, 22), date(2026, 9, 28))]
        self.assertEqual(["2026-09-22", "2026-09-24", "2026-09-26", "2026-09-28"], dates)

    def test_ended_plan_keeps_history_and_facts(self):
        self.clock(20)
        plan = self.daily()
        actual = self.calendar.upsert_record(plan["id"], date(2026, 9, 21), actual_quantity=1)
        self.calendar.update_plan(plan["id"], {"status": "ended"})
        self.assertEqual(["2026-09-16", "2026-09-17", "2026-09-18", "2026-09-19", "2026-09-21"], self.dates())
        self.assertEqual(actual, self.calendar.record(actual["id"]))
        with self.assertRaises(ValueError):
            self.calendar.update_plan(plan["id"], {"status": "active"})

    def test_save_failure_does_not_publish_candidate(self):
        self.clock(20)
        self.daily()
        before = json.loads(json.dumps(self.calendar.data))
        with patch.object(self.store, "save", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self.calendar.update_plan("plan_y35", {"start_date": "2026-09-25"})
        self.assertEqual(before, self.calendar.data)

    def test_revision_preserves_manual_and_noted_records(self):
        self.clock(16)
        self.daily()
        manual = self.calendar.upsert_record(None, date(2026, 9, 18), source="manual", model="A404", platform="jd")
        noted = self.calendar.upsert_record("plan_y35", date(2026, 9, 18), note="keep")
        self.calendar.update_plan("plan_y35", {"start_date": "2026-09-20"})
        self.assertEqual(manual, self.calendar.record(manual["id"]))
        self.assertEqual(noted, self.calendar.record(noted["id"]))

    def test_atomic_save_keeps_five_backups_and_loads_latest_valid_backup(self) -> None:
        self.calendar.add_plan(y35_plan())
        for quantity in range(7):
            self.calendar.upsert_record("plan_y35", date(2026, 9, 16), actual_quantity=quantity)
        self.assertEqual(5, len(list(self.store.backup_dir.glob("*.json"))))
        expected = self.calendar.data
        self.store.path.write_text("broken", encoding="utf-8")
        recovered = CalendarStore(self.store.path)
        self.assertEqual(expected["plans"], recovered.load()["plans"])
        self.assertEqual("已从最近备份恢复出单日历数据", recovered.recovery_message)
        self.assertEqual("broken", self.store.path.read_text(encoding="utf-8"))

    def test_invalid_primary_is_not_overwritten_without_backup(self) -> None:
        self.store.path.parent.mkdir(parents=True)
        self.store.path.write_text("broken", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "原文件已保留"):
            self.store.load()
        self.assertEqual("broken", self.store.path.read_text(encoding="utf-8"))

    def test_v1_data_migrates_in_memory_without_losing_history(self) -> None:
        legacy = {
            "version": 1,
            "plans": [{**y35_plan(), "product_name": "Y35 磁吸暖手宝", "short_name": "Y35"}],
            "records": [{"id": "record_old", "plan_id": "plan_y35", "date": "2026-09-16", "source": "schedule",
                         "target_quantity": 1, "actual_quantity": 1, "reviewed_quantity": 0, "review_date": None, "note": ""}],
        }
        legacy["plans"][0].pop("platform")
        legacy["plans"][0].pop("model")
        self.store.path.parent.mkdir(parents=True)
        self.store.path.write_text(json.dumps(legacy, ensure_ascii=False), encoding="utf-8")
        migrated = OrderCalendar(self.store)
        self.assertEqual((2, "unknown", "Y35"), (migrated.data["version"], migrated.plans[0]["platform"], migrated.plans[0]["model"]))
        self.assertEqual(1, migrated.records[0]["actual_quantity"])
        self.assertEqual(1, migrated.tasks_between(date(2026, 9, 16), date(2026, 9, 16))[0]["actual_quantity"])
        self.assertEqual(1, json.loads(self.store.path.read_text(encoding="utf-8"))["version"])
        migrated.update_plan("plan_y35", {"platform": "jd", "model": "Y35"})
        self.assertEqual(2, json.loads(self.store.path.read_text(encoding="utf-8"))["version"])

    def test_same_model_on_different_platforms_remains_independent(self) -> None:
        self.calendar.add_plan(y35_plan("jd", "plan_jd_y35"))
        self.calendar.add_plan(y35_plan("1688", "plan_1688_y35"))
        self.calendar.upsert_record("plan_jd_y35", date(2026, 9, 16), actual_quantity=1)
        tasks = self.calendar.tasks_between(date(2026, 9, 16), date(2026, 9, 16))
        self.assertEqual([("1688", 0), ("jd", 1)], sorted((task["platform"], task["actual_quantity"]) for task in tasks))
        self.assertEqual("plan_jd_y35", self.calendar.active_plan("jd", "y35")["id"])
        self.assertEqual("plan_1688_y35", self.calendar.active_plan("1688", "Y35")["id"])
        self.assertIsNone(self.calendar.active_plan("taobao", "Y35"))


if __name__ == "__main__":
    unittest.main()
