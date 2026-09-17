#!/usr/bin/env python3
"""Discover the repository's SystemVerilog sources."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SYSTEMVERILOG_PATTERN = "**/*.sv"


@dataclass(frozen=True)
class HdlSource:
    path: Path
    relative_path: str
    file_type: str = "systemVerilogSource"


def discover_sources(
    source_root: Path, *, project_root: Path = PROJECT_ROOT
) -> tuple[HdlSource, ...]:
    """Return all SystemVerilog sources below *source_root* in stable path order."""
    project_root = project_root.resolve()
    source_root = source_root.resolve()
    if not source_root.is_dir():
        raise FileNotFoundError(f"HDL source root is missing: {source_root}")
    try:
        source_root.relative_to(project_root)
    except ValueError as exc:
        raise ValueError(f"HDL source root is outside the project: {source_root}") from exc

    paths = sorted(
        path.resolve() for path in source_root.glob(SYSTEMVERILOG_PATTERN) if path.is_file()
    )
    if not paths:
        raise ValueError(f"no SystemVerilog sources found below: {source_root}")
    return tuple(
        HdlSource(path=path, relative_path=path.relative_to(project_root).as_posix())
        for path in paths
    )
