"""Colour node icons (static/icons/entities): files, keys and how the page receives them."""
import json
from pathlib import Path

from quaesitor import ontology as onto

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "quaesitor" / "static" / "icons" / "entities"


def _known():
    keys = set(onto.TYPES) | set(onto.BASE_ICONS) | {"account", "photo", "audio", "video"}
    for table in (onto.DRUG_ICONS, onto.DOC_ICONS, onto.FINDOC_ICONS, onto.LEGALDOC_ICONS, onto.DEVICE_ICONS,
                  onto.PERSON_ICONS):
        keys |= set(table.values())
    return keys


def test_index_matches_files_and_known_types():
    keys = json.loads((DEST / "index.json").read_text(encoding="utf-8"))
    files = {p.stem for p in DEST.glob("*.png")}
    assert set(keys) == files
    assert set(keys) <= _known()
    assert {"name", "target", "phone", "email", "company", "vessel", "video", "weapon", "article", "call"} <= set(keys)


def test_every_sub_type_icon_is_installed():
    keys = set(json.loads((DEST / "index.json").read_text(encoding="utf-8")))
    for table in (onto.DRUG_ICONS, onto.DOC_ICONS, onto.FINDOC_ICONS, onto.LEGALDOC_ICONS, onto.DEVICE_ICONS):
        assert set(table.values()) <= keys, set(table.values()) - keys
    assert onto.icon_of("drug", {"substance": "MDMA / Ecstasy"}) == "prescription-bottle-medical"
    assert onto.icon_of("device", {"type": "Router / modem"}) == "router"
    assert onto.icon_of("device", {"type": "Other"}) == onto.TYPES["device"]["icon"]


def test_icons_are_square_with_transparent_corners():
    from PIL import Image
    for p in DEST.glob("*.png"):
        im = Image.open(p)
        assert im.size == (128, 128) and im.mode == "RGBA", p.name
        assert im.getpixel((0, 0))[3] == 0 and im.getpixel((127, 127))[3] == 0, p.name


def test_the_page_receives_the_icon_list(qapp):
    _, client = qapp
    html = client.get("/").get_data(as_text=True)
    assert "window.ENTITY_ICONS = [" in html and '"vessel"' in html
    assert client.get("/static/icons/entities/name.png").status_code == 200
