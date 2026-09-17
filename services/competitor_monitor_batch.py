from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from contextlib import nullcontext

from services.competitor_monitor import CollectionResult


MAX_PARALLEL_COLLECTIONS = 3


def collect_batch(
    competitors: Iterable[dict],
    collector,
    *,
    max_workers: int = MAX_PARALLEL_COLLECTIONS,
    cancelled: Callable[[], bool] | None = None,
    isolate_errors: bool = False,
) -> Iterator[tuple[dict, CollectionResult]]:
    """Collect multiple competitors concurrently with a small, bounded worker pool.

    Database writes intentionally stay outside this helper. Callers consume results on their
    own thread and persist them serially, avoiding SQLite cross-thread access while still
    allowing the network/browser work to happen in parallel.

    A collector may expose ``batch_context()`` for resources that must remain active for the
    whole batch. The Playwright collector uses this to keep the dedicated Chrome minimized
    even when CDP creates new tabs and Chrome tries to restore its window.
    """
    items = list(competitors)
    if not items:
        return

    worker_count = max(1, min(int(max_workers), MAX_PARALLEL_COLLECTIONS, len(items)))
    batch_context = getattr(collector, "batch_context", None)
    context = batch_context() if callable(batch_context) else nullcontext()

    with context:
        executor = ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="1688-monitor")
        futures: dict[Future, dict] = {}

        try:
            for item in items:
                if cancelled and cancelled():
                    break
                futures[executor.submit(collector.collect, item["url"])] = item

            for future in as_completed(futures):
                if cancelled and cancelled():
                    _cancel_pending(futures)
                    break

                item = futures[future]
                if isolate_errors:
                    try:
                        result = future.result()
                    except Exception as exc:
                        result = CollectionResult(
                            "failed",
                            error="1688页面采集失败",
                            technical_error=str(exc),
                        )
                else:
                    result = future.result()

                yield item, result

                if result.environment_error:
                    _cancel_pending(futures)
                    break
        finally:
            if cancelled and cancelled():
                _cancel_pending(futures)
            executor.shutdown(wait=True, cancel_futures=True)


def _cancel_pending(futures: dict[Future, dict]) -> None:
    for future in futures:
        if not future.done():
            future.cancel()
