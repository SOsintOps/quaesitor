"""requirements.txt and requirements-audio.txt (used by the installers) match pyproject.toml."""
import re
from pathlib import Path

import pytest

tomllib = pytest.importorskip("tomllib")    # Python 3.11+

ROOT = Path(__file__).resolve().parent.parent


def reqs(name):
    out = []
    for line in (ROOT / name).read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line and not line.startswith("-"):
            out.append(re.sub(r"\s+", "", line))
    return sorted(out)


def test_requirements_match_pyproject():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert reqs("requirements.txt") == sorted(project["dependencies"])
    assert reqs("requirements-audio.txt") == sorted(project["optional-dependencies"]["audio"])
