import yaml

from tools.hdl_sources import PROJECT_ROOT, discover_sources


def test_edam_yml_exists_and_matches_rtl_sources() -> None:
    edam_yaml_path = PROJECT_ROOT / "edam.yml"
    assert edam_yaml_path.is_file(), "edam.yml must exist at project root"

    with edam_yaml_path.open("r", encoding="utf-8") as source:
        data = yaml.safe_load(source)

    expected_sources = discover_sources(PROJECT_ROOT / "rtl")
    assert data == {
        "name": "q16x16_multiplier",
        "toplevel": "top",
        "files": [
            {"name": source.relative_path, "file_type": source.file_type}
            for source in expected_sources
        ],
    }
