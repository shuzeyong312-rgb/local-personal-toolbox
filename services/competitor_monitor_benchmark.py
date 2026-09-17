from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Iterable

from services.competitor_monitor_batch import MAX_PARALLEL_COLLECTIONS, collect_batch
from services.competitor_monitor_window import BackgroundChromeEnvironment, PlaywrightCollector


class BenchmarkCancelled(RuntimeError):
    pass


class BenchmarkEnvironmentError(RuntimeError):
    def __init__(self, message: str, technical_error: str = "") -> None:
        super().__init__(message)
        self.technical_error = technical_error


@dataclass(frozen=True)
class BenchmarkPhaseResult:
    label: str
    mode: str
    workers: int
    elapsed_seconds: float
    completed: int
    success: int
    partial: int
    failed: int


@dataclass(frozen=True)
class ABBenchmarkReport:
    sample_size: int
    parallel_workers: int
    phases: tuple[BenchmarkPhaseResult, ...]
    serial_seconds: float
    parallel_seconds: float
    speedup: float
    time_saved_percent: float
    serial_items_per_minute: float
    parallel_items_per_minute: float

    @property
    def status_summary(self) -> str:
        if self.speedup >= 1.20:
            return "并行采集有明显提速"
        if self.speedup >= 1.05:
            return "并行采集有轻微提速"
        if self.speedup >= 0.95:
            return "串行与并行速度基本相同"
        return "当前并行采集反而更慢"

    def details_text(self) -> str:
        lines = [
            "测试方法：ABBA 交叉测试；同一批商品共跑 4 轮，不写入监控数据库。",
            f"样本：{self.sample_size} 个商品；并行度：{self.parallel_workers}",
            "",
        ]
        for phase in self.phases:
            lines.append(
                f"{phase.label}：{phase.elapsed_seconds:.2f}s  "
                f"成功 {phase.success} / 数据缺失 {phase.partial} / 失败 {phase.failed}"
            )
        lines.extend([
            "",
            f"串行平均：{self.serial_seconds:.2f}s（{self.serial_items_per_minute:.1f} 个/分钟）",
            f"并行平均：{self.parallel_seconds:.2f}s（{self.parallel_items_per_minute:.1f} 个/分钟）",
            f"速度比：{self.speedup:.2f}×",
            f"耗时变化：{self.time_saved_percent:+.1f}%（正数代表节省时间）",
        ])
        return "\n".join(lines)


def run_ab_benchmark(
    competitors: Iterable[dict],
    cdp_url: str,
    *,
    max_parallel: int = MAX_PARALLEL_COLLECTIONS,
    environment=None,
    collector_factory=PlaywrightCollector,
    phase_callback: Callable[[int, int, BenchmarkPhaseResult], None] | None = None,
    state_callback: Callable[[str], None] | None = None,
    cancelled: Callable[[], bool] | None = None,
    cooldown_seconds: float = 1.0,
) -> ABBenchmarkReport:
    """Measure serial vs bounded-parallel collection on the same product set.

    The phase order is A1 -> B1 -> B2 -> A2. The second pair reverses product order so cache,
    warm-up and page-order effects are less likely to make either mode look artificially fast.
    Results are intentionally not persisted to MonitorStore; this is a read-only performance
    benchmark of the collector itself.
    """
    items = [dict(item) for item in competitors]
    if len(items) < 3:
        raise ValueError("A/B 测速至少需要 3 个启用中的竞品商品。")

    parallel_workers = max(2, min(int(max_parallel), MAX_PARALLEL_COLLECTIONS, len(items)))
    env = environment or BackgroundChromeEnvironment(cdp_url)
    if state_callback:
        state_callback("正在准备 1688 采集环境…")
    ready = env.ensure()
    if not ready.ready:
        raise BenchmarkEnvironmentError(ready.error or "采集环境不可用", ready.technical_error)

    forward = list(items)
    reverse = list(reversed(items))
    plan = (
        ("A1 串行", "serial", 1, forward),
        (f"B1 {parallel_workers}路并行", "parallel", parallel_workers, forward),
        (f"B2 {parallel_workers}路并行", "parallel", parallel_workers, reverse),
        ("A2 串行", "serial", 1, reverse),
    )

    phases: list[BenchmarkPhaseResult] = []
    total_phases = len(plan)
    for phase_index, (label, mode, workers, phase_items) in enumerate(plan, 1):
        if cancelled and cancelled():
            raise BenchmarkCancelled("测速已取消")
        if state_callback:
            state_callback(f"正在执行 {label}（第 {phase_index}/{total_phases} 轮）…")

        collector = collector_factory(cdp_url)
        counts = {"success": 0, "partial": 0, "failed": 0}
        completed = 0
        started = time.perf_counter()
        for _item, result in collect_batch(
            phase_items,
            collector,
            max_workers=workers,
            cancelled=cancelled,
            isolate_errors=True,
        ):
            if result.environment_error:
                raise BenchmarkEnvironmentError(
                    result.error or "采集环境异常",
                    result.technical_error,
                )
            counts[result.status] = counts.get(result.status, 0) + 1
            completed += 1
        elapsed = time.perf_counter() - started

        if cancelled and cancelled():
            raise BenchmarkCancelled("测速已取消")
        if completed != len(phase_items):
            raise BenchmarkCancelled("测速未完整执行")

        phase_result = BenchmarkPhaseResult(
            label=label,
            mode=mode,
            workers=workers,
            elapsed_seconds=elapsed,
            completed=completed,
            success=counts.get("success", 0),
            partial=counts.get("partial", 0),
            failed=counts.get("failed", 0),
        )
        phases.append(phase_result)
        if phase_callback:
            phase_callback(phase_index, total_phases, phase_result)

        if phase_index < total_phases and cooldown_seconds > 0:
            deadline = time.monotonic() + cooldown_seconds
            while time.monotonic() < deadline:
                if cancelled and cancelled():
                    raise BenchmarkCancelled("测速已取消")
                time.sleep(min(0.1, max(0.0, deadline - time.monotonic())))

    serial_values = [phase.elapsed_seconds for phase in phases if phase.mode == "serial"]
    parallel_values = [phase.elapsed_seconds for phase in phases if phase.mode == "parallel"]
    serial_seconds = sum(serial_values) / len(serial_values)
    parallel_seconds = sum(parallel_values) / len(parallel_values)
    speedup = serial_seconds / parallel_seconds if parallel_seconds > 0 else float("inf")
    time_saved_percent = (
        (serial_seconds - parallel_seconds) / serial_seconds * 100 if serial_seconds > 0 else 0.0
    )

    return ABBenchmarkReport(
        sample_size=len(items),
        parallel_workers=parallel_workers,
        phases=tuple(phases),
        serial_seconds=serial_seconds,
        parallel_seconds=parallel_seconds,
        speedup=speedup,
        time_saved_percent=time_saved_percent,
        serial_items_per_minute=len(items) * 60 / serial_seconds if serial_seconds > 0 else 0.0,
        parallel_items_per_minute=len(items) * 60 / parallel_seconds if parallel_seconds > 0 else 0.0,
    )
