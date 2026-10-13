"""The investigative types are saved in English and shown in the interface languages."""
import re

from quaesitor import ontology as onto
from quaesitor import ontology_i18n

OWN = [k for k, t in onto.TYPES.items() if not t.get("ftm")]
IT = ontology_i18n.table()["it"]


def test_keys_are_english():
    for t in OWN:
        for f in onto.TYPES[t]["fields"]:
            assert re.fullmatch(r"[a-z][a-z0-9_]*", f["key"]), (t, f["key"])
            assert f["key"] not in onto.FIELD_ALIASES, (t, f["key"])      # an Italian key of 1.x
            assert "en" not in f


def test_labels_groups_and_options_have_an_italian_translation():
    for t in onto.TYPES.values():
        assert t["label"] in IT, t["label"]
        assert t["group"] in IT, t["group"]
    for t in OWN:
        for f in onto.TYPES[t]["fields"]:
            assert f["label"] in IT or f["label"] in ("ICAO24 (hex)", "BIC / SWIFT") or \
                f"{t}:{f['label']}" in IT, (t, f["label"])
            # words have a translation; brands, currencies and calibres stay as they are
            for o in f["options"]:
                assert o in IT or not re.search(r"[a-z]{3}", o) or \
                    re.search(r"\d|Bitcoin|Ethereum|Tether|Monero|Litecoin|Solana|Chain|Visa|Mastercard|Maestro|"
                              r"Express|Postepay|Revolver|Crack|Hashish|Marijuana|Ecstasy|Khat|Kratom|"
                              r"Smartphone|Tablet|Router|Hard disk", o), (t, f["key"], o)


def test_input_in_italian_is_saved_in_english():
    f = onto.clean_fields("weapon", {"categoria": "pistola semiautomatica", "matricola": "abrasa",
                                     "stato": "Sequestrata"})
    assert f == {"category": "Semi-automatic pistol", "serial_removed": True, "status": "Seized"}
    assert onto.clean_fields("drug", {"substance": "Kokain"})["substance"] == "Cocaine"     # German
    assert onto.clean_fields("drug", {"sostanza": "something new"})["substance"] == "something new"


def test_label_and_identity_in_english():
    f = onto.clean_fields("legaldoc", {"tipo": "Verbale di sequestro", "numero": "12/2026", "data": "2026-01-05"})
    assert onto.label_of("legaldoc", f) == "Seizure report no. 12/2026 of 05/01/2026"
    assert onto.ident_of("legaldoc", f) == "seizure report|122026"
    assert onto.label_of("cash", {"amount": "15000.5", "currency": "EUR", "counterfeit": True}) == \
        "15,000.5 EUR (counterfeit)"


def test_node_added_with_italian_fields(qapp):
    _, client = qapp
    r = client.post("/api/node/add", json={"ntype": "drug", "fields": {"sostanza": "Cocaina", "quantita": "12",
                                                                       "unita": "g"}})
    assert r.status_code == 200, r.get_json()
    node = r.get_json()["node"]
    assert node["label"] == "Cocaine 12 g" and node["ficon"] == "vial"
    assert node["records"][0]["raw"]["Substance"] == "Cocaine"


def test_the_page_gets_english_identity(qapp):
    _, client = qapp
    html = client.get("/").get_data(as_text=True)
    assert '"Semi-automatic pistol": "Pistola semiautomatica"' in html


def test_page_defaults_to_english(qapp):
    _, client = qapp
    html = client.get("/").get_data(as_text=True)
    assert '<html lang="en">' in html and 'data-i18n="search.btn">Search<' in html
