from __future__ import annotations

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import QLabel, QPlainTextEdit, QProgressBar, QPushButton

from components.dialogs import BaseDialog
from services.competitor_monitor_benchmark import (
    ABBenchmarkReport,
    BenchmarkCancelled,
    BenchmarkEnvironmentError,
    run_ab_benchmark,
)


class ABBenchmarkWorker(QThread):
    state = Signal(str)
    phase_completed = Signal(int, int, object)
    report_ready = Signal(object)
    failed = Signal(str, str)
    cancelled_done = Signal()

    def __init__(self, competitors: list[dict], cdp_url: str, parent=None) -> None:
        super().__init__(parent)
        self.competitors = competitors
        self.cdp_url = cdp_url
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            report = run_ab_benchmark(
                self.competitors,
                self.cdp_url,
                phase_callback=lambda index, total, phase: self.phase_completed.emit(index, total, phase),
                state_callback=self.state.emit,
                cancelled=lambda: self._cancelled,
            )
        except BenchmarkCancelled:
            self.cancelled_done.emit()
        except BenchmarkEnvironmentError as exc:
            self.failed.emit(str(exc), exc.technical_error)
        except Exception as exc:
            self.failed.emit("A/B 测速执行失败", str(exc))
        else:
            self.report_ready.emit(report)


class ABBenchmarkDialog(BaseDialog):
    """Read-only benchmark UI; benchmark collections are never written to the monitor database."""

    def __init__(self, competitors: list[dict], cdp_url: str, parent=None) -> None:
        super().__init__("串行 vs 并行 A/B 测速", parent)
        self.setMinimumWidth(650)
        self.worker = ABBenchmarkWorker(competitors, cdp_url, self)

        intro = QLabel(
            f"将使用同一批 {len(competitors)} 个商品进行 ABBA 交叉测试："
            "串行 2 轮、3 路并行 2 轮。\n"
            "仅测采集性能，不保存快照、不产生价格/SKU/销量变化事件。"
        )
        intro.setWordWrap(True)
        self.layout.addWidget(intro)

        self.state_label = QLabel("准备测速…")
        self.state_label.setWordWrap(True)
        self.layout.addWidget(self.state_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 4)
        self.progress.setValue(0)
        self.progress.setFormat("%v / %m 轮")
        self.layout.addWidget(self.progress)

        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.result_label.hide()
        self.layout.addWidget(self.result_label)

        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setMinimumHeight(220)
        self.details.hide()
        self.layout.addWidget(self.details)

        self.action = QPushButton("取消测速")
        self.action.clicked.connect(self._handle_action)
        self.layout.addWidget(self.action, alignment=Qt.AlignmentFlag.AlignRight)

        self.worker.state.connect(self.state_label.setText)
        self.worker.phase_completed.connect(self._phase_completed)
        self.worker.report_ready.connect(self._show_report)
        self.worker.failed.connect(self._show_error)
        self.worker.cancelled_done.connect(self._show_cancelled)
        self.worker.start()

    def _handle_action(self) -> None:
        if self.worker.isRunning():
            self.worker.cancel()
            self.action.setEnabled(False)
            self.state_label.setText("正在取消，等待当前页面任务结束…")
            return
        self.accept()

    def _phase_completed(self, index: int, total: int, phase) -> None:
        self.progress.setRange(0, total)
        self.progress.setValue(index)
        self.state_label.setText(
            f"{phase.label} 完成：{phase.elapsed_seconds:.2f}s　"
            f"成功 {phase.success} / 数据缺失 {phase.partial} / 失败 {phase.failed}"
        )

    def _show_report(self, report: ABBenchmarkReport) -> None:
        self.progress.setValue(self.progress.maximum())
        self.state_label.setText("A/B 测速完成")
        self.result_label.setText(
            f"{report.status_summary}\n"
            f"串行平均 {report.serial_seconds:.2f}s　→　"
            f"{report.parallel_workers} 路并行平均 {report.parallel_seconds:.2f}s\n"
            f"速度比 {report.speedup:.2f}×　·　耗时节省 {report.time_saved_percent:+.1f}%"
        )
        quality = {(phase.success, phase.partial, phase.failed) for phase in report.phases}
        if len(quality) > 1:
            self.result_label.setText(
                self.result_label.text()
                + "\n注意：不同轮次采集成功率不完全一致，判断速度时也要结合下面的采集质量。"
            )
        self.result_label.show()
        self.details.setPlainText(report.details_text())
        self.details.show()
        self.action.setText("关闭")
        self.action.setEnabled(True)

    def _show_error(self, message: str, details: str) -> None:
        self.state_label.setText(message)
        self.result_label.setText(details or "测速未完成。")
        self.result_label.show()
        self.action.setText("关闭")
        self.action.setEnabled(True)

    def _show_cancelled(self) -> None:
        self.state_label.setText("A/B 测速已取消")
        self.action.setText("关闭")
        self.action.setEnabled(True)

    def reject(self) -> None:
        if self.worker.isRunning():
            self.worker.cancel()
            return
        super().reject()
