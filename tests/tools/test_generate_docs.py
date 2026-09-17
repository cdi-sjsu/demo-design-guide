import json
import shutil
from pathlib import Path

from tools.generate_docs import (
    MANIFEST_NAME,
    create_manifest,
    find_teroshdl_extension,
    validate_manifest,
)
from tools.hdl_sources import discover_sources


def write(path: Path, content: str = "content\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path.resolve()


def test_finds_only_the_pinned_teroshdl_extension(tmp_path: Path, monkeypatch) -> None:
    extension = tmp_path / "teros-technology.teroshdl-7.0.3"
    write(extension / "package.json", json.dumps({"version": "7.0.3"}))
    monkeypatch.setenv("TEROSHDL_EXTENSION", str(extension))

    assert find_teroshdl_extension() == extension.resolve()


def test_manifest_detects_stale_sources_and_outputs(tmp_path: Path) -> None:
    project = tmp_path
    rtl = project / "rtl"
    source = write(rtl / "top.sv", "module top; endmodule\n")
    source_root = rtl
    sources = discover_sources(source_root, project_root=project)
    config = write(project / ".devcontainer" / "teroshdl-config.json", "{}\n")
    generator = write(project / "tools" / "generate_docs.py")
    metadata = write(project / "tools" / "hdl_sources.py")
    adapter = write(project / "tools" / "export_teroshdl_docs.js")
    staged = project / "staged"
    write(staged / "top" / "README.md")
    write(staged / "top" / "index.html")
    write(staged / "top" / "top.svg")
    output = project / "docs" / "generated"
    shutil.copytree(staged, output)

    manifest = create_manifest(
        project_root=project,
        sources=sources,
        source_root=source_root,
        config_path=config,
        generator_paths=[generator, metadata, adapter],
        staged_output=staged,
        final_output=output,
        render_results=[{"source": "rtl/top.sv", "design_unit": "top"}],
    )
    write(output / MANIFEST_NAME, json.dumps(manifest))

    arguments = {
        "project_root": project,
        "sources": sources,
        "source_root": source_root,
        "output_dir": output,
        "config_path": config,
        "generator_paths": [generator, metadata, adapter],
    }
    assert validate_manifest(**arguments) == []

    source.write_text("module top; logic changed; endmodule\n")
    assert "HDL source changed: rtl/top.sv" in validate_manifest(**arguments)

    source.write_text("module top; endmodule\n")
    write(output / "top" / "unexpected.txt")
    assert "generated documentation contains missing or untracked files" in validate_manifest(
        **arguments
    )


def test_manifest_detects_discovered_source_membership_changes(tmp_path: Path) -> None:
    project = tmp_path
    rtl = project / "rtl"
    write(rtl / "top.sv", "module top; endmodule\n")
    config = write(project / "teroshdl-config.json", "{}\n")
    generator = write(project / "generate_docs.py")
    staged = project / "staged"
    write(staged / "top" / "README.md")
    output = project / "docs" / "generated"
    shutil.copytree(staged, output)
    sources = discover_sources(rtl, project_root=project)
    manifest = create_manifest(
        project_root=project,
        sources=sources,
        source_root=rtl,
        config_path=config,
        generator_paths=[generator],
        staged_output=staged,
        final_output=output,
        render_results=[{"source": "rtl/top.sv", "design_unit": "top"}],
    )
    write(output / MANIFEST_NAME, json.dumps(manifest))

    write(rtl / "child.sv", "module child; endmodule\n")
    changed_sources = discover_sources(rtl, project_root=project)
    errors = validate_manifest(
        project_root=project,
        sources=changed_sources,
        source_root=rtl,
        output_dir=output,
        config_path=config,
        generator_paths=[generator],
    )
    assert "documented HDL source membership changed" in errors
