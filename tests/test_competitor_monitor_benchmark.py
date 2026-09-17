import time
import unittest

from services.competitor_monitor import CollectionResult, EnvironmentResult
from services.competitor_monitor_benchmark import BenchmarkEnvironmentError, run_ab_benchmark


class ReadyEnvironment:
    def ensure(self):
        return EnvironmentResult(True)


class FailedEnvironment:
    def ensure(self):
        return EnvironmentResult(False, "浏览器不可用", "CDP failed")


class SlowCollector:
    def __init__(self, _cdp_url: str) -> None:
        pass

    def collect(self, _url: str) -> CollectionResult:
        time.sleep(0.02)
        return CollectionResult("success", data={})


class CompetitorBenchmarkTests(unittest.TestCase):
    def competitors(self, count=6):
        return [
            {"id": index, "url": f"https://detail.1688.com/offer/{1000 + index}.html"}
            for index in range(count)
        ]

    def test_abba_benchmark_compares_serial_and_parallel_without_persistence(self):
        report = run_ab_benchmark(
            self.competitors(),
            "http://127.0.0.1:9222",
            environment=ReadyEnvironment(),
            collector_factory=SlowCollector,
            cooldown_seconds=0,
        )

        self.assertEqual(6, report.sample_size)
        self.assertEqual(3, report.parallel_workers)
        self.assertEqual(
            ["serial", "parallel", "parallel", "serial"],
            [phase.mode for phase in report.phases],
        )
        self.assertTrue(all(phase.success == 6 for phase in report.phases))
        self.assertGreater(report.speedup, 1.5)
        self.assertGreater(report.time_saved_percent, 0)
        self.assertIn("ABBA", report.details_text())

    def test_benchmark_requires_at_least_three_products(self):
        with self.assertRaises(ValueError):
            run_ab_benchmark(
                self.competitors(2),
                "http://127.0.0.1:9222",
                environment=ReadyEnvironment(),
                collector_factory=SlowCollector,
                cooldown_seconds=0,
            )

    def test_environment_failure_stops_benchmark_before_collection(self):
        with self.assertRaises(BenchmarkEnvironmentError) as raised:
            run_ab_benchmark(
                self.competitors(3),
                "http://127.0.0.1:9222",
                environment=FailedEnvironment(),
                collector_factory=SlowCollector,
                cooldown_seconds=0,
            )
        self.assertEqual("CDP failed", raised.exception.technical_error)


if __name__ == "__main__":
    unittest.main()
