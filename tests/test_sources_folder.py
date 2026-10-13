"""The documents folder next to the program: 'sources', or 'fonti' on installs older than 1.8.0."""
import conftest  # noqa: F401  (puts the program on sys.path)
from quaesitor import sources


def test_new_install_uses_sources(tmp_path):
    assert sources.sources_folder(str(tmp_path)) == str(tmp_path / "sources")


def test_old_install_keeps_fonti(tmp_path):
    (tmp_path / "fonti").mkdir()
    assert sources.sources_folder(str(tmp_path)) == str(tmp_path / "fonti")


def test_sources_wins_when_both_exist(tmp_path):
    (tmp_path / "fonti").mkdir()
    (tmp_path / "sources").mkdir()
    assert sources.sources_folder(str(tmp_path)) == str(tmp_path / "sources")
