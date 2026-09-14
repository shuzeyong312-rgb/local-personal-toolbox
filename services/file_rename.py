from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

SORT_KEYS = {"mtime_asc", "mtime_desc", "ctime_asc", "name"}
INVALID_PREFIX_CHARS = '<>:"/\\|?*'


@dataclass(frozen=True)
class RenamePlan:
    source: Path
    destination: Path
    timestamp: float


def build_rename_plan(
    sources: list[Path],
    prefix: str = "详情页_",
    start: int = 1,
    digits: int | None = None,
    sort_by: str = "mtime_asc",
) -> list[RenamePlan]:
    if not sources:
        return []
    if sort_by not in SORT_KEYS:
        raise ValueError("不支持的排序方式")
    if start < 0 or digits not in {None, 2, 3}:
        raise ValueError("序号设置无效")
    if any(char in INVALID_PREFIX_CHARS or ord(char) < 32 for char in prefix):
        raise ValueError("文件名前缀包含 Windows 不允许的字符")

    resolved = [path.resolve() for path in sources]
    if any(not path.is_file() for path in resolved):
        raise ValueError("待重命名文件不存在")
    if len({str(path).casefold() for path in resolved}) != len(resolved):
        raise ValueError("文件列表中存在重复项")
    parents = {str(path.parent).casefold() for path in resolved}
    if len(parents) != 1:
        raise ValueError("请选择同一文件夹中的文件")

    def time_and_name(path: Path, created: bool = False) -> tuple[int, str]:
        stat = path.stat()
        return (stat.st_ctime_ns if created else stat.st_mtime_ns, path.name.casefold())

    if sort_by == "mtime_asc":
        ordered = sorted(resolved, key=time_and_name)
    elif sort_by == "mtime_desc":
        ordered = sorted(resolved, key=lambda path: (-path.stat().st_mtime_ns, path.name.casefold()))
    elif sort_by == "ctime_asc":
        ordered = sorted(resolved, key=lambda path: time_and_name(path, True))
    else:
        ordered = sorted(resolved, key=lambda path: path.name.casefold())

    plans = []
    for offset, source in enumerate(ordered):
        number = str(start + offset).zfill(digits or 0)
        timestamp = source.stat().st_ctime if sort_by == "ctime_asc" else source.stat().st_mtime
        plans.append(RenamePlan(source, source.with_name(f"{prefix}{number}{source.suffix}"), timestamp))
    return plans


def find_conflicts(plans: list[RenamePlan]) -> list[str]:
    sources = {str(plan.source).casefold() for plan in plans}
    destinations: set[str] = set()
    conflicts: list[str] = []
    for plan in plans:
        key = str(plan.destination).casefold()
        if key in destinations:
            conflicts.append(f"目标文件名重复：{plan.destination.name}")
        elif plan.destination.exists() and key not in sources:
            conflicts.append(f"目标文件已存在：{plan.destination.name}")
        destinations.add(key)
    return conflicts


def execute_rename(plans: list[RenamePlan]) -> tuple[int, list[str]]:
    conflicts = find_conflicts(plans)
    if conflicts:
        return 0, conflicts

    staged: list[tuple[RenamePlan, Path]] = []
    try:
        for plan in plans:
            temporary = plan.source.with_name(f".{plan.source.name}.{uuid4().hex}.rename-tmp")
            plan.source.rename(temporary)
            staged.append((plan, temporary))
    except OSError as exc:
        for plan, temporary in reversed(staged):
            if temporary.exists() and not plan.source.exists():
                temporary.rename(plan.source)
        return 0, [f"准备重命名失败：{exc}"]

    completed: list[tuple[RenamePlan, Path]] = []
    for plan, temporary in staged:
        try:
            if plan.destination.exists():
                raise FileExistsError(f"目标文件已存在：{plan.destination.name}")
            temporary.rename(plan.destination)
            completed.append((plan, temporary))
        except OSError as exc:
            locations: list[tuple[RenamePlan, Path]] = []
            try:
                for finished_plan, _ in completed:
                    recovery = finished_plan.source.with_name(f".{finished_plan.source.name}.{uuid4().hex}.rename-rollback")
                    finished_plan.destination.rename(recovery)
                    locations.append((finished_plan, recovery))
                completed_sources = {item.source for item, _ in completed}
                locations.extend((item, temp) for item, temp in staged if item.source not in completed_sources)
                for original_plan, location in locations:
                    location.rename(original_plan.source)
            except OSError as rollback_exc:
                return 0, [f"重命名失败：{exc}", f"自动恢复失败，请勿删除临时文件：{rollback_exc}"]
            return 0, [f"重命名失败，已恢复原文件名：{exc}"]
    return len(completed), []
