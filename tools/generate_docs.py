#!/usr/bin/env python3
"""Generate and validate committed documentation using TerosHDL's renderer."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from tools.hdl_sources import SYSTEMVERILOG_PATTERN, HdlSource, discover_sources

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HDL_SOURCES_PATH = PROJECT_ROOT / "tools" / "hdl_sources.py"
TEROSHDL_VERSION = "7.0.3"
MANIFEST_VERSION = 2
MANIFEST_NAME = "manifest.json"
DOCUMENTATION_LANGUAGES = {
    "systemVerilogSource": "systemVerilogSource",
    "verilogSource": "verilogSource",
    "verilogSource-2005": "verilogSource",
    "vhdlSource": "vhdlSource",
    "vhdlSource-2008": "vhdlSource",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--source-root", type=Path, default=PROJECT_ROOT / "rtl")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "docs" / "generated")
    parser.add_argument(
        "--config", type=Path, default=PROJECT_ROOT / ".devcontainer" / "teroshdl-config.json"
    )
    parser.add_argument(
        "--adapter", type=Path, default=PROJECT_ROOT / "tools" / "export_teroshdl_docs.js"
    )
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def output_subdirectory(source: Path, source_root: Path) -> Path:
    return source.resolve().relative_to(source_root.resolve()).with_suffix("")


def find_node(home: Path | None = None) -> Path:
    override = os.environ.get("VSCODE_NODE")
    if override:
        candidates = [Path(override)]
    else:
        home = (home or Path.home()).resolve()
        candidates = []
        for server_dir in (home / ".vscode-server", home / ".vscode-server-insiders"):
            candidates.extend(sorted(server_dir.glob("bin/*/node"), reverse=True))
        system_node = shutil.which("node")
        if system_node:
            candidates.append(Path(system_node))
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve()
    raise FileNotFoundError(
        "VS Code Server's Node runtime was not found; run 'make docs' inside the dev container"
    )


def find_teroshdl_extension(home: Path | None = None) -> Path:
    override = os.environ.get("TEROSHDL_EXTENSION")
    if override:
        candidates = [Path(override)]
    else:
        home = (home or Path.home()).resolve()
        candidates = []
        for server_dir in (home / ".vscode-server", home / ".vscode-server-insiders"):
            candidates.extend(
                sorted(
                    (server_dir / "extensions").glob("teros-technology.teroshdl-*"), reverse=True
                )
            )
    installed_versions = []
    for candidate in candidates:
        package_path = candidate / "package.json"
        if not package_path.is_file():
            continue
        package = json.loads(package_path.read_text(encoding="utf-8"))
        version = package.get("version")
        installed_versions.append(str(version))
        if version == TEROSHDL_VERSION:
            return candidate.resolve()
    found = ", ".join(installed_versions) or "none"
    raise FileNotFoundError(
        f"TerosHDL {TEROSHDL_VERSION} is required for documentation generation; found: {found}"
    )


def file_record(path: Path, project_root: Path) -> dict[str, str]:
    return {"path": relative_path(path, project_root), "sha256": sha256(path)}


def create_manifest(
    *,
    project_root: Path,
    sources: tuple[HdlSource, ...],
    source_root: Path,
    config_path: Path,
    generator_paths: list[Path],
    staged_output: Path,
    final_output: Path,
    render_results: list[dict[str, str]],
) -> dict[str, object]:
    result_by_source = {result["source"]: result for result in render_results}
    source_records = []
    for hdl_source in sources:
        source = hdl_source.path
        source_name = hdl_source.relative_path
        if source_name not in result_by_source:
            raise RuntimeError(f"TerosHDL did not report documentation for {source_name}")
        subdirectory = output_subdirectory(source, source_root)
        staged_source = staged_output / subdirectory
        output_files = sorted(path for path in staged_source.rglob("*") if path.is_file())
        if not output_files:
            raise RuntimeError(f"TerosHDL produced no documentation for {source_name}")
        outputs = []
        for output_file in output_files:
            published = final_output / subdirectory / output_file.relative_to(staged_source)
            outputs.append(
                {
                    "path": relative_path(published, project_root),
                    "sha256": sha256(output_file),
                }
            )
        source_records.append(
            {
                "path": source_name,
                "sha256": sha256(source),
                "design_unit": result_by_source[source_name]["design_unit"],
                "outputs": outputs,
            }
        )
    return {
        "manifest_version": MANIFEST_VERSION,
        "teroshdl_version": TEROSHDL_VERSION,
        "source_discovery": {
            "root": relative_path(source_root, project_root),
            "pattern": SYSTEMVERILOG_PATTERN,
        },
        "config": file_record(config_path, project_root),
        "generators": [file_record(path, project_root) for path in generator_paths],
        "sources": source_records,
    }


def validate_manifest(
    *,
    project_root: Path,
    sources: tuple[HdlSource, ...],
    source_root: Path,
    output_dir: Path,
    config_path: Path,
    generator_paths: list[Path],
) -> list[str]:
    manifest_path = output_dir / MANIFEST_NAME
    if not manifest_path.is_file():
        return [f"missing {relative_path(manifest_path, project_root)}"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid documentation manifest: {exc}"]

    errors = []
    if manifest.get("manifest_version") != MANIFEST_VERSION:
        errors.append("documentation manifest version is unsupported")
    if manifest.get("teroshdl_version") != TEROSHDL_VERSION:
        errors.append(f"documentation was not generated with TerosHDL {TEROSHDL_VERSION}")

    expected_discovery = {
        "root": relative_path(source_root, project_root),
        "pattern": SYSTEMVERILOG_PATTERN,
    }
    if manifest.get("source_discovery") != expected_discovery:
        errors.append("HDL source discovery configuration changed")
    expected_config = file_record(config_path, project_root)
    if manifest.get("config") != expected_config:
        errors.append("TerosHDL documentation configuration changed")
    expected_generators = [file_record(path, project_root) for path in generator_paths]
    if manifest.get("generators") != expected_generators:
        errors.append("documentation generator changed")

    current_sources = {source.relative_path: source.path for source in sources}
    recorded_sources = {record.get("path"): record for record in manifest.get("sources", [])}
    if set(current_sources) != set(recorded_sources):
        errors.append("documented HDL source membership changed")

    recorded_outputs = set()
    for source_name, source in current_sources.items():
        record = recorded_sources.get(source_name)
        if record is None:
            continue
        if record.get("sha256") != sha256(source):
            errors.append(f"HDL source changed: {source_name}")
        for output in record.get("outputs", []):
            output_name = output.get("path")
            if not isinstance(output_name, str):
                errors.append(f"invalid output record for {source_name}")
                continue
            recorded_outputs.add(output_name)
            output_path = project_root / output_name
            if not output_path.is_file():
                errors.append(f"generated documentation is missing: {output_name}")
            elif output.get("sha256") != sha256(output_path):
                errors.append(f"generated documentation changed: {output_name}")

    actual_outputs = {
        relative_path(path, project_root)
        for path in output_dir.rglob("*")
        if path.is_file() and path.name != MANIFEST_NAME
    }
    if actual_outputs != recorded_outputs:
        errors.append("generated documentation contains missing or untracked files")
    return errors


def replace_output(staged_output: Path, output_dir: Path) -> None:
    backup = output_dir.with_name(f".{output_dir.name}.backup")
    if backup.exists():
        raise FileExistsError(f"stale documentation backup exists: {backup}")
    if output_dir.exists():
        output_dir.rename(backup)
    try:
        staged_output.rename(output_dir)
    except BaseException:
        if backup.exists() and not output_dir.exists():
            backup.rename(output_dir)
        raise
    if backup.exists():
        shutil.rmtree(backup)


def generate(args: argparse.Namespace) -> None:
    project_root = PROJECT_ROOT.resolve()
    source_root = args.source_root.resolve()
    sources = discover_sources(source_root, project_root=project_root)
    output_dir = args.output_dir.resolve()
    config_path = args.config.resolve()
    adapter_path = args.adapter.resolve()
    for required in (config_path, adapter_path):
        if not required.is_file():
            raise FileNotFoundError(f"required documentation input is missing: {required}")

    subdirectories = [output_subdirectory(source.path, source_root) for source in sources]
    if len(set(subdirectories)) != len(subdirectories):
        raise ValueError(
            "HDL sources with different extensions resolve to the same output directory"
        )

    node = find_node()
    extension = find_teroshdl_extension()
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="teroshdl-docs-", dir=output_dir.parent) as temporary:
        temporary_path = Path(temporary)
        staged_output = temporary_path / "generated"
        staged_output.mkdir()
        payload_path = temporary_path / "payload.json"
        result_path = temporary_path / "result.json"
        payload = {
            "extension": str(extension),
            "config": str(config_path),
            "result": str(result_path),
            "sources": [
                {
                    "path": str(source.path),
                    "relative_path": source.relative_path,
                    "language": DOCUMENTATION_LANGUAGES[source.file_type],
                    "output_dir": str(
                        staged_output / output_subdirectory(source.path, source_root)
                    ),
                }
                for source in sources
            ],
        }
        payload_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        subprocess.run([str(node), str(adapter_path), str(payload_path)], check=True)
        render_results = json.loads(result_path.read_text(encoding="utf-8"))
        manifest = create_manifest(
            project_root=project_root,
            sources=sources,
            source_root=source_root,
            config_path=config_path,
            generator_paths=[Path(__file__).resolve(), HDL_SOURCES_PATH, adapter_path],
            staged_output=staged_output,
            final_output=output_dir,
            render_results=render_results,
        )
        (staged_output / MANIFEST_NAME).write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        replace_output(staged_output, output_dir)
    print(f"Generated TerosHDL documentation in {relative_path(output_dir, project_root)}")


def main() -> int:
    args = parse_args()
    try:
        if args.check:
            source_root = args.source_root.resolve()
            sources = discover_sources(source_root, project_root=PROJECT_ROOT)
            errors = validate_manifest(
                project_root=PROJECT_ROOT,
                sources=sources,
                source_root=source_root,
                output_dir=args.output_dir,
                config_path=args.config,
                generator_paths=[
                    Path(__file__).resolve(),
                    HDL_SOURCES_PATH,
                    args.adapter.resolve(),
                ],
            )
            if errors:
                print(
                    "Documentation is stale; run 'make docs' in the dev container:", file=sys.stderr
                )
                print("\n".join(f"  {error}" for error in errors), file=sys.stderr)
                return 1
            print("Generated documentation is current")
            return 0
        generate(args)
        return 0
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
