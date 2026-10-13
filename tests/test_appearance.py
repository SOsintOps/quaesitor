"""Appearance of the nodes: the detectors that read a value."""
from datetime import date

import pytest

from quaesitor import appearance as ap


@pytest.mark.parametrize("number, network", [
    ("4111 1111 1111 1111", "Visa"), ("5555555555554444", "Mastercard"),
    ("2223003122003222", "Mastercard"), ("378282246310005", "American Express"),
    ("36227206271667", "Diners Club"), ("6011111111111117", "Discover"),
    ("3530111333300000", "JCB"), ("6200000000000005", "UnionPay"),
    ("6759649826438453", "Maestro"), ("2200 0000 0000 0004", "Mir"),
    ("4111 **** **** 1111", "Visa"), ("9999 9999 9999 9999", None), ("", None)])
def test_card_network(number, network):
    assert ap.card_network(number) == network


def test_luhn():
    assert ap.luhn_ok("4111 1111 1111 1111") is True
    assert ap.luhn_ok("4111 1111 1111 1112") is False
    assert ap.luhn_ok("4111 **** **** 1111") is None
    assert ap.luhn_ok("1234") is None


def test_iban_and_bic():
    assert ap.iban_country("IT60 X054 2811 1010 0000 0123 456") == "it"
    assert ap.iban_ok("IT60X0542811101000000123456") is True
    assert ap.iban_ok("IT61X0542811101000000123456") is False
    assert ap.iban_ok("GB82 WEST 1234 5698 7654 32") is True
    assert ap.iban_ok("not an iban") is None
    assert ap.bic_country("DEUTDEFF500") == "de" and ap.bic_country("UNCRITMM") == "it"


@pytest.mark.parametrize("address, chain", [
    ("bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq", "Bitcoin"),
    ("1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2", "Bitcoin"),
    ("0x32Be343B94f860124dC4fEe278FDCBD38C102D88", "Ethereum"),
    ("TNPeeaaFB7K9cmo4uQpcU32zGK8G1NYqeL", "Tether (USDT) - TRON"),
    ("LM2WMpR1Rp6j3Sa59cMXMs1SPzj9eXpGc1", "Litecoin"),
    ("4AdUndXHHZ6cfufTMvppY6JwXNouMBzSkbLYfpAV5Usx3skxNgYeYTRj5UzqtReoS44qo9mtmXCqY45DJ852K5Jv2684Rge",
     "Monero"),
    ("7EcDhSYGxXyscszYEp35KHN8vvw3svAuLKTzXwCFLtV", "Solana"),
    ("not an address", None)])
def test_crypto_chain(address, chain):
    assert ap.crypto_chain(address) == chain


def test_chain_named_in_a_field():
    assert ap.chain_of("BTC") == "Bitcoin" and ap.chain_of("Monero") == "Monero"


@pytest.mark.parametrize("number, cc", [
    ("+39 333 1234567", "it"), ("0039 06 1234567", "it"), ("+39 06698 12345", "va"),
    ("+44 7700 900123", "gb"), ("+49 30 123456", "de"), ("+7 495 123 4567", "ru"),
    ("+7 727 123 4567", "kz"), ("+1 242 555 0100", "bs"), ("+1 202 555 0100", None),
    ("333 1234567", None), ("+999 12", None)])
def test_phone_country(number, cc):
    assert ap.phone_country(number) == cc


@pytest.mark.parametrize("text, cc", [
    ("IT", "it"), ("it", "it"), ("Italy", "it"), ("Italia", "it"), ("Allemagne", "de"),
    ("Regno Unito", "gb"), ("UK", "gb"), ("USA", "us"), ("Atlantis", None), ("", None)])
def test_country_code(text, cc):
    assert ap.country_code(text) == cc


def test_vehicle_country():
    assert ap.vehicle_country("I") == "it" and ap.vehicle_country("LAR") == "ly"
    assert ap.vehicle_country("LY") == "ly" and ap.vehicle_country("GB") == "gb"


def test_email_provider():
    assert ap.email_provider("mario.rossi@gmail.com")[0] == "Gmail"
    assert ap.email_provider("x@hotmail.it")[0] == "Outlook"
    assert ap.email_provider("x@proton.me")[1] == ("logo", "protonmail")
    assert ap.email_provider("x@example.com") is None


def test_expiry():
    today = date(2026, 10, 13)
    assert ap.expired("09/26", today) and not ap.expired("10/26", today)
    assert ap.expired("2026-10-12", today) and not ap.expired("13/10/2026", today)
    assert not ap.expired("", today) and not ap.expired("13/2026", today)


# ------------------------------------------------------------ on the graph ---
def _add(client, **body):
    r = client.post("/api/node/add", json=body)
    assert r.status_code == 200, r.get_json()
    return r.get_json()["id"]


def _marks(client, nid):
    n = next(n for n in client.get("/api/graph").get_json()["nodes"] if n["id"] == nid)
    return n.get("ficon"), {b["pos"]: (b["kind"], b["key"]) for b in n.get("badges") or []}


def test_card_marks(qapp):
    _, client = qapp
    ok = _add(client, ntype="card", fields={"number": "4111 1111 1111 1111", "expiry": "12/99"})
    bad = _add(client, ntype="card", fields={"number": "5555 5555 5555 4440"})
    old = _add(client, ntype="card", fields={"number": "3782 822463 10005", "expiry": "01/20"})
    assert _marks(client, ok)[1] == {"ne": ("logo", "visa")}
    assert _marks(client, bad)[1] == {"ne": ("logo", "mastercard"), "se": ("alert", "triangle-exclamation")}
    assert _marks(client, old)[1] == {"ne": ("logo", "americanexpress"), "se": ("alert", "clock")}


def test_account_wallet_document_marks(qapp):
    _, client = qapp
    iban = _add(client, ntype="bankaccount", fields={"iban": "IT60 X054 2811 1010 0000 0123 456"})
    bad = _add(client, ntype="bankaccount", fields={"iban": "IT61 X054 2811 1010 0000 0123 456"})
    tron = _add(client, ntype="crypto", fields={"address": "TNPeeaaFB7K9cmo4uQpcU32zGK8G1NYqeL"})
    doc = _add(client, ntype="document", fields={"type": "Passport", "number": "YA1234567",
                                                 "country": "Italia", "expiry": "2020-01-01"})
    fake = _add(client, ntype="document", fields={"number": "AB99", "country": "FR", "forged": True})
    assert _marks(client, iban)[1] == {"sw": ("flag", "it")}
    assert _marks(client, bad)[1] == {"sw": ("flag", "it"), "se": ("alert", "triangle-exclamation")}
    assert _marks(client, tron)[1] == {"ne": ("letter", "T:#eb0029")}
    assert _marks(client, doc) == ("passport", {"sw": ("flag", "it"), "se": ("alert", "clock")})
    assert _marks(client, fake)[1]["se"] == ("alert", "triangle-exclamation")


def test_phone_email_weapon_marks(qapp):
    _, client = qapp
    ph = _add(client, ntype="phone", value="+44 7700 900123")
    mail = _add(client, ntype="email", value="mario.rossi@gmail.com")
    gun = _add(client, ntype="weapon", fields={"category": "Fucile d'assalto", "serial_number": "abrasa"})
    assert _marks(client, ph)[1] == {"sw": ("flag", "gb")}
    assert _marks(client, mail)[1] == {"ne": ("logo", "gmail")}
    assert _marks(client, gun) == ("rifle", {"se": ("alert", "triangle-exclamation")})


def test_ftm_vessel_and_person_nationality(qapp):
    import base64
    import json
    _, client = qapp
    ents = [{"id": "v1", "schema": "Vessel", "properties": {"name": ["Ever Given"], "flag": ["pa"]}},
            {"id": "p1", "schema": "Person", "properties": {"name": ["Ivan Petrov"], "nationality": ["ru"]}}]
    body = "\n".join(json.dumps(e) for e in ents).encode()
    data = "data:application/json;base64," + base64.b64encode(body).decode()
    assert client.post("/api/ftm/import", json={"data": data, "dataset": "t"}).status_code == 200
    from conftest import wait
    assert not wait(client, "/api/ftm/progress")["error"]
    nodes = client.get("/api/graph").get_json()["nodes"]
    vessel = next(n for n in nodes if n["ntype"] == "vessel")
    person = next(n for n in nodes if n["label"] == "Ivan Petrov")
    assert {b["pos"]: b["key"] for b in vessel["badges"]} == {"sw": "pa"}
    assert {b["pos"]: b["key"] for b in person["badges"]} == {"sw": "ru"}
