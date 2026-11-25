"""The KKBP Version (ADR 0060): one release date, YYYY.MM.DD, shared by the importer and the exporters."""

import datetime
import re
import tomllib

from conftest import ADDON, REPO


def _version():
    return (REPO / "VERSION").read_text(encoding="utf-8").strip()


def test_version_is_a_real_date():
    version = _version()
    assert re.fullmatch(r"\d{4}\.\d{2}\.\d{2}", version), f"VERSION holds {version!r}, not YYYY.MM.DD"
    datetime.datetime.strptime(version, "%Y.%m.%d")


def test_the_blender_manifest_has_the_same_date_without_leading_zeros():
    """Blender only accepts strict semantic versions, which have no leading zeros."""
    manifest = tomllib.loads((ADDON / "blender_manifest.toml").read_text(encoding="utf-8"))
    plain = ".".join(str(int(part)) for part in _version().split("."))
    assert manifest["version"] == plain, "run scripts/set-version.sh to set both"


def test_the_exporters_read_the_version_file():
    props = (REPO / "exporters" / "Exporter.props").read_text(encoding="utf-8")
    exporter = re.search(r"<KKBPExporterVersion>(.*?)</KKBPExporterVersion>", props).group(1)
    assert "VERSION" in exporter and not re.search(r"\d+\.\d+\.\d+", exporter), \
        "Exporter.props must read VERSION, not hold a version of its own"
