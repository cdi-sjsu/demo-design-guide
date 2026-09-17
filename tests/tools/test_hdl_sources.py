from pathlib import Path

import pytest

from tools.hdl_sources import discover_sources


def write(path: Path, content: str = "module example; endmodule\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path.resolve()


def test_discovers_systemverilog_sources_recursively_in_stable_order(tmp_path: Path) -> None:
    rtl = tmp_path / "rtl"
    nested = write(rtl / "blocks" / "child.sv")
    top = write(rtl / "top.sv")
    write(rtl / "ignored.v")
    write(rtl / "notes.txt")

    sources = discover_sources(rtl, project_root=tmp_path)

    assert [source.path for source in sources] == [nested, top]
    assert [source.relative_path for source in sources] == [
        "rtl/blocks/child.sv",
        "rtl/top.sv",
    ]
    assert {source.file_type for source in sources} == {"systemVerilogSource"}


def test_rejects_missing_empty_or_external_source_roots(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="source root is missing"):
        discover_sources(tmp_path / "missing", project_root=tmp_path)

    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ValueError, match="no SystemVerilog sources"):
        discover_sources(empty, project_root=tmp_path)

    external = tmp_path.parent / "external-rtl"
    external.mkdir(exist_ok=True)
    with pytest.raises(ValueError, match="outside the project"):
        discover_sources(external, project_root=tmp_path)
