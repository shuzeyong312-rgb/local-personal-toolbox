import threading
import time
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from services.competitor_monitor import CollectionResult, EnvironmentResult
from services.competitor_monitor_batch import MAX_PARALLEL_COLLECTIONS, collect_batch
from services.competitor_monitor_collection import BackgroundChromeEnvironment, minimize_monitor_chrome


class SlowCollector:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.active = 0
        self.max_active = 0

    def collect(self, url: str) -> CollectionResult:
        with self.lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        try:
            time.sleep(0.04)
            return CollectionResult("success", data={"url": url})
        finally:
            with self.lock:
                self.active -= 1


class CompetitorBatchTests(unittest.TestCase):
    def test_batch_collects_multiple_products_concurrently_with_cap_of_three(self):
        collector = SlowCollector()
        competitors = [
            {"id": index, "url": f"https://detail.1688.com/offer/{index}.html"}
            for index in range(1, 7)
        ]

        results = list(collect_batch(competitors, collector, max_workers=10))

        self.assertEqual(6, len(results))
        self.assertEqual(MAX_PARALLEL_COLLECTIONS, collector.max_active)
        self.assertLessEqual(collector.max_active, 3)

    def test_batch_context_stays_active_for_entire_parallel_collection(self):
        events = []

        class Collector:
            @contextmanager
            def batch_context(self):
                events.append("enter")
                try:
                    yield
                finally:
                    events.append("exit")

            def collect(self, url: str) -> CollectionResult:
                events.append(f"collect:{url.rsplit('/', 1)[-1]}")
                return CollectionResult("success", data={})

        competitors = [
            {"id": index, "url": f"https://detail.1688.com/offer/{index}.html"}
            for index in range(1, 4)
        ]
        results = list(collect_batch(competitors, Collector()))

        self.assertEqual(3, len(results))
        self.assertEqual("enter", events[0])
        self.assertEqual("exit", events[-1])
        self.assertEqual(3, len([item for item in events if item.startswith("collect:")]))

    def test_interactive_batch_can_isolate_one_unexpected_item_error(self):
        class Collector:
            def collect(self, url: str) -> CollectionResult:
                if url.endswith("/2.html"):
                    raise RuntimeError("broken page")
                return CollectionResult("success", data={})

        competitors = [
            {"id": index, "url": f"https://detail.1688.com/offer/{index}.html"}
            for index in range(1, 4)
        ]
        results = dict(
            (item["id"], result)
            for item, result in collect_batch(competitors, Collector(), isolate_errors=True)
        )

        self.assertEqual("failed", results[2].status)
        self.assertIn("broken page", results[2].technical_error)
        self.assertEqual("success", results[1].status)
        self.assertEqual("success", results[3].status)

    def test_verification_stops_replenishing_and_stops_window_guard(self):
        class Guard:
            stopped = False

            def __enter__(self): return self
            def __exit__(self, *_args): pass
            def stop(self): self.stopped = True

        class Collector:
            def __init__(self):
                self.guard = Guard()
                self.started = []

            def batch_context(self): return self.guard

            def collect(self, url: str) -> CollectionResult:
                self.started.append(url)
                if url.endswith("/1.html"):
                    return CollectionResult("needs_verification")
                time.sleep(0.05)
                return CollectionResult("success", data={})

        collector = Collector()
        competitors = [{"id": index, "url": f"https://detail.1688.com/offer/{index}.html"} for index in range(1, 6)]

        results = list(collect_batch(competitors, collector, max_workers=3))

        self.assertEqual([(1, "needs_verification")], [(item["id"], result.status) for item, result in results])
        self.assertTrue(collector.guard.stopped)
        self.assertLessEqual(len(collector.started), 3)

    def test_monitor_chrome_starts_minimized_but_manual_open_stays_visible(self):
        environment = BackgroundChromeEnvironment()
        chrome = Path("C:/Chrome/chrome.exe")
        with patch.object(environment, "_chrome_path", return_value=chrome), \
             patch("services.competitor_monitor_collection.subprocess.Popen") as popen, \
             patch("services.competitor_monitor.ChromeEnvironment._start_chrome") as visible_start:
            environment._start_chrome()
            command = popen.call_args.args[0]
            self.assertIn("--start-minimized", command)
            self.assertIn("--remote-debugging-port=9222", command)

            environment._start_chrome("https://www.1688.com/")
            visible_start.assert_called_once_with("https://www.1688.com/")

    def test_ready_environment_force_minimizes_even_when_chrome_was_already_running(self):
        environment = BackgroundChromeEnvironment()
        ready = EnvironmentResult(True)
        with patch("services.competitor_monitor.ChromeEnvironment.ensure", return_value=ready), \
             patch("services.competitor_monitor_collection.minimize_monitor_chrome", return_value=True) as minimize:
            result = environment.ensure()

        self.assertIs(result, ready)
        minimize.assert_called_once_with(environment.PROFILE)

    def test_failed_environment_does_not_try_to_minimize(self):
        environment = BackgroundChromeEnvironment()
        failed = EnvironmentResult(False, "浏览器启动失败", "CDP error")
        with patch("services.competitor_monitor.ChromeEnvironment.ensure", return_value=failed), \
             patch("services.competitor_monitor_collection.minimize_monitor_chrome") as minimize:
            result = environment.ensure()

        self.assertIs(result, failed)
        minimize.assert_not_called()

    def test_minimize_helper_retries_until_monitor_window_exists(self):
        with patch("services.competitor_monitor_collection._monitor_chrome_pids", return_value={1234}), \
             patch("services.competitor_monitor_collection._minimize_process_windows", side_effect=[0, 1]) as minimize, \
             patch("services.competitor_monitor_collection.time.sleep") as sleep:
            result = minimize_monitor_chrome(Path("C:/1688-monitor-profile"), retries=3, delay=0.1)

        self.assertTrue(result)
        self.assertEqual(2, minimize.call_count)
        sleep.assert_called_once_with(0.1)


if __name__ == "__main__":
    unittest.main()
