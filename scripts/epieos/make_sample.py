# -*- coding: utf-8 -*-
"""Costruisce dalla specifica OpenAPI di Epieos due risposte di esempio
(email e telefono) con TUTTI i moduli valorizzati, per i test e la
documentazione. Uso: python make_sample.py <openapi.json> <cartella di uscita>"""
# "Vulpem pilum mutare, non mores." (Suetonius, Vespasian)
# The fox changes its fur, not its habits.
import json, sys, os

spec = json.load(open(sys.argv[1], encoding="utf-8"))
OUT = sys.argv[2]
FIX = {  # valori plausibili per chiave (altrimenti '<chiave>_x')
    "query": None, "photo": "https://img.example.com/avatar.jpg", "name": "John Doe", "full_name": "John Doe",
    "display_name": "John Doe", "real_name": "John Doe", "realname": "John Doe", "given_name": "John",
    "family_name": "Doe", "first_name": "John", "last_name": "Doe", "username": "johndoe", "login": "johndoe",
    "handle": "johndoe", "preferred_username": "johndoe", "screen_name": "johndoe", "login_name": "johndoe",
    "alias": "jdoe", "id": "12345", "uuid": "9f1c-2b", "user_id": "777", "guid": "g-1", "email": "john.doe@example.com",
    "profile": "https://service.example.com/johndoe", "profile_url": "https://service.example.com/johndoe",
    "url": "https://service.example.com/johndoe", "member_url": "https://service.example.com/johndoe",
    "city": "Milano", "state": "MI", "country": "Italy", "country_name": "Italy", "home_city": "Roma",
    "location": "Milano, Italy", "address": "Via Roma 1", "found": "true", "exists": "true",
    "leaks": ["LinkedIn", "Adobe", "Canva"], "websites": ["spotify.com", "twitter.com", "instagram.com"],
    "phones": ["+39 333 1234567"], "gender": "male", "bio": "bio di prova", "company_name": "Acme Ltd",
    "headline": "CEO at Acme", "confirmed": "true", "is_public": "true", "auth_method": "password",
    "type": "individual", "status": "active", "domain": "twitter.com", "display": "@johndoe", "userid": "4242",
    "verified": "true", "shortname": "twitter", "value": "+39 333 1234567", "title": "CEO", "period": "2019 - oggi",
    "field": "Informatica", "role": "owner", "created_at": "2020-01-01", "creation_date": "2020-01-01",
    "pgp_key": "-----BEGIN PGP-----", "catch_all_email": "false",
}
def fill(schema, key="", depth=0):
    t = schema.get("type")
    if t == "object":
        props = schema.get("properties") or {}
        if not props and schema.get("patternProperties"):
            return {"twitter": "@johndoe", "phone": "+39 333 1234567"}
        return {k: fill(v, k, depth + 1) for k, v in props.items() if k != "query"}
    if t == "array":
        it = schema.get("items") or {}
        if key in FIX and isinstance(FIX[key], list):
            return FIX[key]
        return [fill(it, key, depth + 1)] if depth < 4 else []
    if key in FIX and FIX[key] is not None:
        return FIX[key]
    return f"{key}_x"
for kind in ("email", "phone"):
    path = f"/v1/search/{kind}/osinter"
    r200 = spec["paths"][path]["post"]["responses"]["200"]["content"]["application/json"]["schema"]
    mods = r200["properties"]["result"]["properties"]
    q = "john.doe@example.com" if kind == "email" else "+39 333 1234567"
    result = {}
    for m, sch in mods.items():
        d = fill(sch, m)
        d["query"] = q
        if m == "facebook":
            d["contactpoints"] = [{"type": "phone", "value": "+39 333 9876543"}, {"type": "email", "value": "jd.alt@example.com"}]
            d["other_accounts"] = [{"name": "Jane Doe", "auth_method": "password", "contactpoints": [{"type": "email", "value": "jane@example.com"}]}]
        if m == "linkedin":
            for c in d.get("companies") or []: c["name"] = "Acme Ltd"
            for s in d.get("schools") or []: s["name"] = "Politecnico di Milano"
        if m == "samsung":
            d["accounts"] = [{"type": "email", "value": "john.doe@example.com"}]
            d["recovery_methods"] = [{"id": "1", "type": "phone", "value": "+39 333 0000001", "created_at": "2021"}]
        result[m] = d
    json.dump({"result": result}, open(os.path.join(OUT, f"sample_{kind}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(kind, "modules:", len(result))
