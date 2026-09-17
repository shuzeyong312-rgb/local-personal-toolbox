import unittest
from pathlib import Path
from unittest.mock import patch

from services.competitor_monitor import EnvironmentResult
from services.competitor_monitor_window import (
    BackgroundChromeEnvironment,
    MonitorChromeWindowGuard,
    PlaywrightCollector,
    park_monitor_chrome,
)


class CompetitorMonitorWindowTests(unittest.TestCase):
    def test_background_chrome_starts_off_screen_without_minimize_flag(self):
        environment = BackgroundChromeEnvironment()
        chrome = Path("C:/Chrome/chrome.exe")
        with patch.object(environment, "_chrome_path", return_value=chrome), \
             patch("services.competitor_monitor_window.subprocess.Popen") as popen:
            environment._start_chrome()

        command = popen.call_args.args[0]
        self.assertIn("--window-position=-32000,-32000", command)
        self.assertIn("--remote-debugging-port=9222", command)
        self.assertNotIn("--start-minimized", command)

    def test_ready_environment_parks_window_instead_of_minimizing(self):
        environment = BackgroundChromeEnvironment()
        ready = EnvironmentResult(True)
        with patch("services.competitor_monitor.ChromeEnvironment.ensure", return_value=ready), \
             patch("services.competitor_monitor_window.park_monitor_chrome", return_value=True) as park:
            result = environment.ensure()

        self.assertIs(result, ready)
        park.assert_called_once_with(environment.PROFILE)

    def test_park_helper_retries_until_window_is_available(self):
        with patch("services.competitor_monitor_window._monitor_chrome_pids", side_effect=[set(), {1234}]), \
             patch("services.competitor_monitor_window._park_process_windows", return_value=1) as park, \
             patch("services.competitor_monitor_window.time.sleep") as sleep:
            result = park_monitor_chrome(Path("C:/1688-monitor-profile"), retries=3, delay=0.1)

        self.assertTrue(result)
        park.assert_called_once_with({1234})
        sleep.assert_called_once_with(0.1)

    def test_collector_uses_off_screen_guard_for_batch(self):
        collector = PlaywrightCollector()
        context = collector.batch_context()
        self.assertIsInstance(context, MonitorChromeWindowGuard)


if __name__ == "__main__":
    unittest.main()
