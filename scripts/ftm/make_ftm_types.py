# -*- coding: utf-8 -*-
"""Generates from Follow the Money (followthemoney package, folders schema/ and
translations/) two files for OsintGraph:

    ftm_schema.json     schemata, inheritance, typed properties, edges
                        (source/target/label), captions, labels in
                        en/fr/de/es/ar/ru: ftm.py reads it at runtime to
                        import FtM exports without depending on the package
    ontology_ftm.py     FTM_TYPES: the FtM schemata without an equivalent in
                        OsintGraph as ontology.py types (own fields and
                        'featured'), with Italian labels; FTM_I18N: the
                        translations (it -> en, fr, de, es, ar) for ontology_i18n

Usage: python scripts/ftm/make_ftm_types.py <followthemoney package dir> quaesitor/generated

Requires PyYAML. The Italian labels are in the IT dictionary below:
FtM has no Italian translation. A label without an entry stays in English.
"""
# "Amicus certus in re incerta cernitur." (Ennius, quoted by Cicero in Laelius de Amicitia)
# A sure friend is seen in an unsure matter.
import sys, os, re, json
import yaml

PKG, OUT = sys.argv[1], sys.argv[2]
SCHEMA_DIR = os.path.join(PKG, "schema")
TR_DIR = os.path.join(PKG, "translations")
LANGS = ("en", "fr", "de", "es", "ar", "ru")

# --------------------------------------------------------- Italian labels
IT = {
    "Above or below threshold": "Sopra o sotto soglia", "Amount": "Importo",
    "Amount of tax paid": "Imposte pagate", "Area": "Area", "Authority": "Autorità",
    "Authority-issued identifier": "Identificativo assegnato dall'autorità",
    "Award Notice Date": "Data avviso di aggiudicazione", "Birth date": "Data di nascita",
    "CCD Value": "Valore dichiarazione doganale", "CPV code": "Codice CPV",
    "Call": "Chiamata telefonica", "Call for tenders": "Bando di gara",
    "Call for tenders result": "Esito del bando", "Caller's Number": "Numero chiamante",
    "Certification check": "Verifica certificazione", "CfT unique id": "Id univoco del bando",
    "Commodities": "Merci", "Contract awarded in Lots": "Contratto aggiudicato a lotti",
    "Contract date": "Data del contratto", "Contract notice date": "Data avviso di gara",
    "Contracting authority reference ID": "Riferimento stazione appaltante",
    "Country": "Paese", "Country of departure": "Paese di partenza",
    "Country of destination": "Paese di destinazione", "Country of origin": "Paese di origine",
    "Customs Cargo Declaration Number": "Numero dichiarazione doganale",
    "Customs Procedure": "Procedura doganale", "Customs Value Amount": "Valore doganale",
    "Customs declaration": "Dichiarazione doganale", "Date": "Data",
    "Date of awarding": "Data di aggiudicazione",
    "Date of publication/invitation": "Data di pubblicazione / invito",
    "Description of goods": "Descrizione delle merci",
    "Direction of transportation": "Direzione del trasporto", "Directive": "Direttiva",
    "Dissolution date": "Data di scioglimento",
    "Does this call fall under the scope of GPP?": "Rientra nel GPP (appalti pubblici)?",
    "Duration": "Durata", "EU funding": "Finanziamento UE", "End date": "Data di fine",
    "End of clarification period": "Fine periodo chiarimenti",
    "Evaluation mechanism": "Criterio di valutazione", "FEAC Code": "Codice FEAC",
    "FEAC Code description": "Descrizione codice FEAC", "FIPS code": "Codice FIPS",
    "Given name": "Nome di battesimo", "Inception date": "Data di costituzione",
    "Inclusion of e-Auctions": "Aste elettroniche previste",
    "Invoice Value Amount": "Valore fattura", "Level": "Livello", "License": "Licenza",
    "License review date": "Data di revisione della licenza",
    "Listing date": "Data di inserimento in lista", "Lots names": "Nomi dei lotti",
    "Maximum number of lots": "Numero massimo di lotti",
    "Multiple tenders will be accepted": "Offerte multiple ammesse", "NUTS code": "Codice NUTS",
    "Name": "Nome", "Number of lots": "Numero di lotti",
    "Payment options": "Modalità di pagamento", "Phase": "Fase",
    "Position": "Incarico / posizione", "Procedure": "Procedura",
    "Procurement type": "Tipo di appalto", "Program": "Programma", "Program ID": "Id programma",
    "Program URL": "URL programma", "Project": "Progetto", "Project ID": "Id progetto",
    "Project goal": "Obiettivo del progetto", "Reason": "Motivo",
    "Receiver's Number": "Numero chiamato", "Registered income": "Reddito dichiarato",
    "Registered wealth": "Patrimonio dichiarato", "Risk": "Rischio", "Sanction": "Sanzione",
    "Scope of sanctions": "Ambito delle sanzioni", "Start date": "Data di inizio",
    "Status": "Stato", "Submission deadline": "Termine di presentazione",
    "Subnational area": "Area subnazionale", "Surname": "Cognome",
    "TED link for published notices": "Link TED agli avvisi pubblicati",
    "Tax roll": "Dichiarazione fiscale", "Tenders for lots": "Offerte per lotto",
    "Territory": "Territorio", "Territory code": "Codice territorio", "Title": "Titolo",
    "Topics": "Temi", "Total number of seats": "Numero totale di seggi",
    "Trading Country": "Paese di scambio", "Trip": "Viaggio",
    "UN SC identifier": "Identificativo ONU (Consiglio di sicurezza)",
    "USD Exchange Rate": "Cambio in USD", "ZIP code": "CAP",
    # --- properties of the other node schemata (phase 1: all the native schemata)
    "Abbreviation": "Abbreviazione", "Account ID": "Id conto", "Account number": "Numero di conto",
    "Account type": "Tipo di conto", "Address": "Indirizzo", "Airplane": "Aeromobile",
    "Amount in EUR": "Importo in EUR", "Amount in USD": "Importo in USD", "Article": "Articolo",
    "Asset": "Bene", "Audio": "Audio", "Author": "Autore", "Authored on": "Scritto il",
    "BIK": "BIK (codice banca russo)", "Balance": "Saldo", "Balance date": "Data del saldo",
    "Bank Identifier Code": "Codice identificativo banca (BIC)", "Bank account": "Conto bancario",
    "Bank address": "Indirizzo della banca", "Bank name": "Nome della banca", "Blockchain": "Blockchain",
    "BrightQuery ID": "Id BrightQuery", "Build Date": "Data di costruzione",
    "Bureau van Dijk ID": "Id Bureau van Dijk", "CAGE": "Codice CAGE",
    "COATO / SOATO / OKATO": "Codice territoriale COATO / SOATO / OKATO", "COD CAEM": "Codice CAEM",
    "CRS Number": "Numero CRS", "Cadastral code": "Codice catastale", "Call Sign": "Nominativo radio",
    "Cancelled?": "Annullato?", "Capital": "Capitale", "Case number": "Numero del procedimento",
    "Category": "Categoria", "Census block": "Sezione di censimento", "Checksum": "Checksum",
    "Classification": "Classificazione", "Close date": "Data di chiusura", "Closing date": "Data di chiusura",
    "Collateral": "Garanzia", "Company": "Società", "Confidence score": "Punteggio di confidenza",
    "Contract": "Contratto", "Contract Award Notice ID": "Id avviso di aggiudicazione",
    "Contract award criteria": "Criteri di aggiudicazione", "Contract procedure": "Procedura contrattuale",
    "Court": "Tribunale", "Court case": "Procedimento giudiziario", "Crawler": "Crawler",
    "Creation date": "Data di creazione", "Crypto address": "Indirizzo crypto",
    "Cryptocurrency wallet": "Wallet di criptovalute", "Currency": "Valuta",
    "Currency short code": "Codice valuta", "Custody type": "Tipo di custodia", "DUNS": "Numero DUNS",
    "Date issued": "Data di emissione", "Date of Name Change": "Data del cambio di nome",
    "De-registration Date": "Data di cancellazione", "Deadweight Tonnage": "Portata lorda (DWT)",
    "Document": "Documento", "Document number": "Numero del documento", "Email": "Email",
    "Encumbrance": "Gravame", "Event": "Evento", "FSS": "Codice FSS",
    "Federal tax service code": "Codice del servizio fiscale federale", "File": "File",
    "File date": "Data di deposito", "File encoding": "Codifica del file", "File extension": "Estensione",
    "File name": "Nome del file", "File size": "Dimensione del file",
    "Financial Instrument Global Identifier": "Identificativo globale dello strumento (FIGI)",
    "Flag": "Bandiera", "Folder": "Cartella", "GIIN": "GIIN", "Gender": "Sesso", "Generator": "Generatore",
    "Gross Registered Tonnage": "Stazza lorda (GRT)", "IBAN": "IBAN",
    "ICAO aircraft type designator": "Designatore ICAO del tipo", "ICIJ ID": "Id ICIJ",
    "ID Number": "Numero identificativo", "IMO Number": "Numero IMO", "INN": "INN (codice fiscale russo)",
    "IPO": "IPO", "IRS Number": "Numero IRS", "ISIN": "ISIN", "Identification": "Identificazione",
    "Important": "Importante", "Incorporation date": "Data di costituzione", "Index": "Indice",
    "JIB": "JIB", "Jurisdiction": "Giurisdizione", "KPP": "KPP", "LEI": "LEI", "Land type": "Tipo di terreno",
    "Language": "Lingua", "Latitude": "Latitudine", "Legal entity": "Soggetto giuridico",
    "Legal form": "Forma giuridica", "License Number": "Numero di licenza", "Location": "Luogo",
    "Longitude": "Longitudine", "MBS": "MBS", "MIME type": "Tipo MIME", "MMSI": "MMSI",
    "Managing exchange": "Borsa di quotazione", "Manufacturer": "Costruttore", "Matcher": "Confrontatore",
    "Matching criteria": "Criteri di confronto", "Maturity date": "Data di scadenza",
    "Maximum balance": "Saldo massimo", "Maximum balance date": "Data del saldo massimo",
    "Mention": "Menzione", "Message": "Messaggio", "Message ID": "Id messaggio", "Model": "Modello",
    "NPI": "NPI", "Navigation Area": "Area di navigazione", "Number of awards": "Numero di aggiudicazioni",
    "Number of rows": "Numero di righe", "OGRN": "OGRN", "OKOPF": "OKOPF", "OKPO": "OKPO", "OKSM": "OKSM",
    "OKVED": "OKVED", "OpenCorporates URL": "URL OpenCorporates", "Opening date": "Data di apertura",
    "Organization": "Organizzazione", "PFR Number": "Numero PFR", "Package": "Pacchetto", "Page": "Pagina",
    "Passport": "Passaporto", "Past Flags": "Bandiere precedenti", "Past Types": "Tipi precedenti",
    "PermID": "PermID", "Personal number": "Numero personale", "Phone": "Telefono",
    "Place of birth": "Luogo di nascita", "Port of Registration": "Porto di immatricolazione",
    "Private key": "Chiave privata", "Procedure number": "Numero della procedura",
    "Processing agent": "Agente di elaborazione", "Procurement method": "Metodo di appalto",
    "Property type": "Tipo di immobile", "Public body": "Ente pubblico", "Published on": "Pubblicato il",
    "Real estate": "Immobile", "Record ID": "Id record", "Record date": "Data del record",
    "Registration Date": "Data di registrazione", "Registration number": "Numero di registrazione",
    "Reuters Instrument Code": "Codice strumento Reuters (RIC)", "SEC Central Index Key": "Chiave SEC (CIK)",
    "SWIFT/BIC": "SWIFT/BIC", "Sampling Rate": "Frequenza di campionamento", "Sayari Entity ID": "Id Sayari",
    "Sector": "Settore", "Security": "Strumento finanziario", "Serial Number": "Numero di serie",
    "Similar": "Simile", "Stock ticker symbol": "Ticker di borsa", "Subject": "Oggetto",
    "Summary": "Sintesi", "Table": "Tabella", "Tax Number": "Codice fiscale", "Tax status": "Stato fiscale",
    "Tenure": "Durata dell'incarico", "Text file": "File di testo", "Thread topic": "Argomento della discussione",
    "Title number": "Numero di titolo", "Tonnage": "Stazza", "Type": "Tipo", "USCC": "USCC",
    "Unique Entity ID": "Id entità univoco", "V.A.T. Identifier": "Partita IVA", "VOEN": "VOEN",
    "Vessel": "Nave", "Video": "Video", "Website": "Sito web", "Workbook": "Cartella di lavoro",
    "FtM id": "Id FtM",
    "FtM · Soggetti": "FtM · Soggetti", "FtM · Finanza": "FtM · Finanza",
    "FtM · Documenti d'identità": "FtM · Documenti d'identità", "FtM · Beni e mezzi": "FtM · Beni e mezzi",
    "FtM · Procedimenti": "FtM · Procedimenti", "FtM · Documenti": "FtM · Documenti",
    "Follow the Money": "Follow the Money",
}

# --------------------------------------------------------------- catalogues
def read_po(path):
    out = {}
    if not os.path.isfile(path):
        return out
    s = open(path, encoding="utf-8").read()
    for mid, mstr in re.findall(r'\nmsgid "((?:[^"\\]|\\.)*)"\nmsgstr "((?:[^"\\]|\\.)*)"', s):
        if mid and mstr:
            out[mid.replace('\\"', '"')] = mstr.replace('\\"', '"')
    return out

PO = {l: read_po(os.path.join(TR_DIR, l, "LC_MESSAGES", "followthemoney.po")) for l in LANGS if l != "en"}

def tr(en, lang):
    return en if lang == "en" else PO[lang].get(en, en)

# ---------------------------------------------------------------- schemata
raw = {}
for fn in sorted(os.listdir(SCHEMA_DIR)):
    if fn.endswith(".yaml"):
        raw.update(yaml.safe_load(open(os.path.join(SCHEMA_DIR, fn), encoding="utf-8")))

def ancestors(n, seen=None):
    seen = seen or []
    for p in raw[n].get("extends", []) or []:
        if p not in seen:
            seen.append(p); ancestors(p, seen)
    return seen

def all_props(n):
    out = {}
    for a in reversed(ancestors(n)):
        out.update(raw[a].get("properties", {}) or {})
    out.update(raw[n].get("properties", {}) or {})
    return out

schema_json = {}
for n, s in raw.items():
    props = {}
    for k, p in (s.get("properties") or {}).items():
        p = p or {}
        props[k] = {"type": p.get("type", "string"), "label": p.get("label", k),
                    "labels": {l: tr(p.get("label", k), l) for l in LANGS if l != "en"}}
        if p.get("hidden"):
            props[k]["hidden"] = True
    schema_json[n] = {
        "label": s.get("label", n), "plural": s.get("plural", ""),
        "labels": {l: tr(s.get("label", n), l) for l in LANGS if l != "en"},
        "extends": s.get("extends") or [], "abstract": bool(s.get("abstract")),
        "caption": s.get("caption") or [], "featured": s.get("featured") or [],
        "required": s.get("required") or [], "edge": s.get("edge") or None,
        "properties": props,
    }
with open(os.path.join(OUT, "ftm_schema.json"), "w", encoding="utf-8") as f:
    json.dump(schema_json, f, ensure_ascii=False, separators=(",", ":"))
print(f"ftm_schema.json: {len(schema_json)} schemi")

# ------------------------------------- types without an equivalent in OsintGraph
# FtM schemata that coincide with the OsintGraph built-in types (person, place,
# email, account, photo, text, link, vehicle): they stay built-in, with the FtM id
# and the extra properties in the record. All the OTHER node schemata become
# native types.
BUILTIN = {"Person", "Address", "Vehicle", "Email", "UserAccount", "Image", "Note", "HyperText"}
# generic inherited properties (Thing/Analyzable/Document): not form fields;
# on import they stay as free fields of the record
GENERIC_SKIP = {"summary", "description", "sourceUrl", "alias", "previousName", "weakAlias",
                "keywords", "topics", "notes", "modifiedAt", "retrievedAt", "createdAt",
                "publisher", "publisherUrl", "indexText", "wikidataId", "wikipediaUrl", "program",
                "bodyText", "detectedLanguage", "detectedCountry", "translatedText",
                "translatedLanguage", "processingStatus", "processingError", "processingAgent",
                "processedAt", "proof", "namesMentioned", "peopleMentioned", "companiesMentioned",
                "ibanMentioned", "ipMentioned", "locationMentioned", "phoneMentioned",
                "emailMentioned", "contentHash", "parent", "ancestors", "crawler", "indexUpdatedAt",
                "bodyHtml", "headers", "generator", "encoding", "extension"}
GROUPS = {
    "FtM · Soggetti": {"Company", "Organization", "PublicBody", "LegalEntity"},
    "FtM · Finanza": {"BankAccount", "CryptoWallet", "Security", "Asset", "Contract", "EconomicActivity",
                      "CallForTenders", "TaxRoll", "License"},
    "FtM · Documenti d'identità": {"Passport", "Identification"},
    "FtM · Beni e mezzi": {"RealEstate", "Vessel", "Airplane"},
    "FtM · Procedimenti": {"CourtCase", "Sanction", "Event", "Risk", "Position", "Project", "Trip",
                           "Call", "Territory"},
}
def group_of(n):
    for g, ss in GROUPS.items():
        if n in ss:
            return g
    return "FtM · Documenti"
# alternative identifying keys (without an FtM id): the first one present in the schema
IDENT_PREF = {
    "Company": ["name"], "Organization": ["name"], "PublicBody": ["name"], "LegalEntity": ["name"],
    "BankAccount": ["iban", "accountNumber"], "CryptoWallet": ["publicKey"], "Security": ["isin", "ticker"],
    "Asset": ["name"], "Contract": ["contractNumber", "name"], "Passport": ["number", "passportNumber"],
    "Identification": ["number"], "RealEstate": ["registrationNumber", "address"],
    "Vessel": ["imoNumber", "mmsi", "name"], "Airplane": ["registrationNumber", "serialNumber"],
    "CourtCase": ["fileNumber", "caseNumber"], "Sanction": ["authorityId"], "License": ["number"],
    "Position": ["name"], "Project": ["projectId", "name"], "Risk": ["name"], "Territory": ["code"],
    "Trip": ["number"], "TaxRoll": ["name"], "Call": ["date"], "CallForTenders": ["cftId"],
    "EconomicActivity": ["ccdNumber"], "Event": ["name"],
}
ICONS_MORE = {"Company": "building", "Organization": "building", "PublicBody": "building-columns",
              "LegalEntity": "building", "BankAccount": "money-check", "CryptoWallet": "bitcoin",
              "Security": "file-invoice-dollar", "Asset": "gem", "Contract": "file-contract",
              "Passport": "passport", "Identification": "id-card", "RealEstate": "house",
              "Vessel": "car", "Airplane": "car", "CourtCase": "scale-balanced", "Event": "burst",
              "Message": "envelope", "Mention": "link", "Similar": "link", "Audio": "image",
              "Video": "image", "Image": "image"}
TYPE_MAP = {"string": "text", "text": "text", "name": "text", "date": "date", "number": "number",
            "identifier": "text", "country": "text", "phone": "text", "email": "text", "url": "text",
            "address": "text", "ip": "text", "iban": "text", "checksum": "text", "mimetype": "text",
            "language": "text", "gender": "text", "topic": "text"}
ICONS = {"Sanction": "gavel", "Position": "building-columns", "License": "file-contract",
         "Trip": "location-dot", "Project": "file-lines", "Call": "phone", "Risk": "burst",
         "Territory": "globe", "TaxRoll": "receipt", "CallForTenders": "file-contract",
         "EconomicActivity": "building"}
IDENT = {"Sanction": ["authorityId"], "License": ["number"], "Position": ["name"],
         "Project": ["projectId"], "Risk": ["name"], "Territory": ["code"],
         "Trip": ["number"], "TaxRoll": ["name"], "Call": ["date"],
         "CallForTenders": ["cftId"], "EconomicActivity": ["ccdNumber"]}

def it(en):
    return IT.get(en, en)


# keys already used by ontology.py (Italian types) and by the built-in types: an FtM
# type with the same name gets the 'ftm' prefix (ftmbankaccount, ftmdocument, ftmevent,
# ftmorganization) instead of overwriting the existing type
TAKEN = {"weapon", "explosive", "ammo", "drug", "cash", "cheque", "valuable", "bankaccount",
         "card", "crypto", "document", "findoc", "legaldoc", "device", "organization", "event",
         "property", "sighting", "target", "name", "person", "phone", "email", "username",
         "account", "social", "vehicle", "place", "link", "text", "photo", "latin", "generic",
         "domain", "breach"}


def type_key(schema):
    k = schema.lower()
    return "ftm" + k if k in TAKEN else k

types, rows = {}, {}
def add_row(en):
    i = it(en)
    if i not in rows:
        rows[i] = (en, tr(en, "fr"), tr(en, "de"), tr(en, "es"), tr(en, "ar"))

add_row("Follow the Money")
for g in GROUPS:
    add_row(g)
add_row("FtM · Documenti")
add_row("FtM id")
new = [n for n, s in raw.items() if not s.get("abstract") and not s.get("edge") and n not in BUILTIN]
COLORS = {"FtM · Soggetti": "#7c2d12", "FtM · Finanza": "#0f766e", "FtM · Documenti d'identità": "#1d4ed8",
          "FtM · Beni e mezzi": "#4338ca", "FtM · Procedimenti": "#831843", "FtM · Documenti": "#475569"}
for n in sorted(new):
    s = raw[n]
    props = all_props(n)
    own = set((s.get("properties") or {}).keys()) | set(s.get("featured") or [])
    fields = []
    for k, p in props.items():
        p = p or {}
        t = p.get("type", "string")
        if t not in TYPE_MAP or p.get("hidden") or p.get("deprecated"):
            continue
        if k in GENERIC_SKIP and k not in own:
            continue
        en = p.get("label", k)
        add_row(en)
        fields.append({"key": k, "label": it(en), "en": en, "type": TYPE_MAP[t],
                       "options": [], "ph": ""})
    feat = s.get("featured") or []
    fields.sort(key=lambda f: (f["key"] not in feat, feat.index(f["key"]) if f["key"] in feat else 0))
    # FtM id: hidden field (not in the form, yes in the record), primary identity
    fields.append({"key": "ftmId", "label": it("FtM id"), "en": "FtM id", "type": "text",
                   "options": [], "ph": "", "hidden": True})
    keys = [f["key"] for f in fields if f["key"] != "ftmId"]
    caption = [c for c in (s.get("caption") or []) if c in keys] or keys[:1]
    alt = next((k for k in IDENT_PREF.get(n, []) if k in keys), None) or caption[0]
    en = s.get("label", n)
    add_row(en)
    grp = group_of(n)
    types[type_key(n)] = {
        "label": it(en), "en": en, "group": grp,
        "icon": ICONS.get(n) or ICONS_MORE.get(n, "file-lines"), "color": COLORS[grp],
        "fields": fields,
        "ident": ["ftmId"], "ident_alt": [alt], "norm": {"ftmId": "compact_case"},
        "label_fmt": caption[:3], "value": caption[0],
        "ai": f"{type_key(n)}: {str(s.get('description', '')).strip()[:160]} fields: "
              + ", ".join(keys[:8]) + ".",
        "ftm": n,
    }

def py(obj):
    """Readable JSON that is also valid as a Python literal (true/false/null)."""
    return re.sub(r'(?<=: )(true|false|null)\b',
                  lambda m: {"true": "True", "false": "False", "null": "None"}[m.group(1)],
                  json.dumps(obj, ensure_ascii=False, indent=1))


with open(os.path.join(OUT, "ontology_ftm.py"), "w", encoding="utf-8") as f:
    f.write("# -*- coding: utf-8 -*-\n")
    f.write("# Generato da scripts/ftm/make_ftm_types.py: tipi Follow the Money senza\n")
    f.write("# equivalente in OsintGraph (ontology.TYPES.update(FTM_TYPES)) e le loro\n")
    f.write("# traduzioni (ontology_i18n.ROWS). Non modificare a mano: rigenerare.\n")
    f.write("# \"Nihil est ab omni parte beatum.\" (Horace, Odes)\n")
    f.write("# Nothing is blessed in every respect.\n")
    f.write("FTM_TYPES = " + py(types) + "\n\n")
    f.write("# italiano -> (en, fr, de, es, ar); fr/de/es/ar dai cataloghi di FtM\n")
    f.write("FTM_I18N = " + py(rows) + "\n\n")
    f.write("# schema FtM <-> tipo di OsintGraph (per importazione ed esportazione)\n")
    f.write("FTM_SCHEMA_OF = " + py({t: v["ftm"] for t, v in types.items()}) + "\n")
    f.write("FTM_TYPE_OF = " + py({v["ftm"]: t for t, v in types.items()}) + "\n")
missing = sorted({f["en"] for t in types.values() for f in t["fields"]} - set(IT))
print(f"ontology_ftm.py: {len(types)} tipi, {sum(len(t['fields']) for t in types.values())} campi, "
      f"{len(rows)} righe i18n; etichette senza italiano: {missing}")
