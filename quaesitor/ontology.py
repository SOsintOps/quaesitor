# -*- coding: utf-8 -*-
# OSInt Graph - esplorazione grafica di dati OSINT per casi investigativi
# Copyright (C) 2025-2026 Andrea Cumini <andrea@osintinfo.net> - www.osintinfo.net
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version, with the additional terms in the file NOTICE.
# See the files LICENSE and NOTICE for details. Distributed WITHOUT ANY WARRANTY.

"""Ontology items of investigative interest (besides persons, phones,
emails, accounts, places, vehicles... which are handled separately in app.py).

Each type describes in a single place:
    fields   the fields of the manual entry form (and of the card)
    ident    the fields that identify the object: if all are filled in, two
             identical entries are THE SAME node (one more card);
             if they are missing, each entry is an exhibit of its own (new node)
    label    how the node label is built
    ai       the instructions for AI extraction
    icon     the icon (Font Awesome Free, static/vendor/fa)

Field types: text, number, date, select (options), check.
"""
# "Quot homines, tot sententiae." (Terence, Phormio)
# As many opinions as there are men.
import re
import unicodedata

# -------------------------------------------------------------- lists ---
WEAPON_CATEGORIES = [
    "Pistola semiautomatica", "Revolver", "Pistola mitragliatrice", "Fucile da caccia",
    "Fucile a pompa", "Carabina", "Fucile di precisione", "Fucile d'assalto",
    "Mitragliatrice", "Arma a salve / modificata", "Arma ad aria compressa",
    "Arma artigianale", "Arma bianca (coltello, machete…)", "Balestra / arco",
    "Storditore elettrico / spray", "Altro",
]
CALIBERS = [
    "9x19 Parabellum", "9x21 IMI", "7,65 Browning (.32 ACP)", "6,35 Browning (.25 ACP)",
    ".22 LR", ".38 Special", ".357 Magnum", ".44 Magnum", ".45 ACP", ".40 S&W",
    "7,62x39", "5,56x45 NATO", "7,62x51 NATO (.308 Win)", ".30-06", "12 gauge",
    "16 gauge", "20 gauge", "4,5 mm (aria compressa)",
]
EXPLOSIVES = [
    "Dinamite", "TNT (tritolo)", "Esplosivo plastico (C4 / Semtex)", "Pentrite (PETN)",
    "Polvere nera", "Polvere da sparo infume", "ANFO", "TATP", "Nitroglicerina",
    "Gelatina esplosiva", "Ordigno esplosivo improvvisato (IED)", "Bomba a mano",
    "Detonatori / inneschi", "Miccia detonante", "Artifici pirotecnici illegali",
    "Altro",
]
DRUGS = [
    "Cocaina", "Crack", "Eroina", "Hashish", "Marijuana", "Olio di cannabis",
    "Piante di cannabis", "MDMA / Ecstasy", "Anfetamina", "Metanfetamina",
    "Ketamina", "LSD", "Funghi allucinogeni (psilocibina)", "Mescalina",
    "Fentanyl e derivati", "Oppio", "Morfina", "Metadone", "Buprenorfina",
    "Ossicodone / oppioidi farmaceutici", "Benzodiazepine", "GHB / GBL",
    "Cannabinoidi sintetici", "Catinoni sintetici (mefedrone…)", "Khat", "Kratom",
    "Precursori chimici", "Sostanza da taglio", "Sostanza non identificata", "Altro",
]
DRUG_UNITS = ["g", "kg", "mg", "dosi", "pasticche", "piante", "ml", "francobolli", "confezioni"]
CURRENCIES = ["EUR", "USD", "GBP", "CHF", "LYD", "TND", "MAD", "EGP", "DZD", "TRY",
              "ALL", "RON", "RUB", "UAH", "CNY", "AED", "SAR", "Altro"]
CRYPTO_CHAINS = ["Bitcoin", "Ethereum", "Tether (USDT) - TRON", "Tether (USDT) - Ethereum",
                 "Monero", "Litecoin", "Solana", "BNB Chain", "Altro"]
ID_DOCS = ["Carta d'identità", "Passaporto", "Patente di guida", "Permesso di soggiorno",
           "Codice fiscale / tessera sanitaria", "Visto", "Documento di viaggio",
           "Tessera di riconoscimento", "Altro"]
DEVICES = ["Smartphone", "Cellulare", "Tablet", "PC portatile", "PC fisso", "Hard disk / SSD",
           "Chiavetta USB / memory card", "Router / modem", "Dispositivo GPS", "Criptofonino",
           "Altro"]
ORG_TYPES = ["Società di capitali", "Società di persone", "Ditta individuale",
             "Associazione", "Ente pubblico", "Gruppo criminale", "Clan / cosca",
             "Organizzazione terroristica", "Altro"]
CRIMES = [
    "Spaccio di stupefacenti", "Traffico di stupefacenti", "Detenzione di stupefacenti",
    "Detenzione / porto illegale di armi", "Traffico di armi", "Rapina", "Furto",
    "Ricettazione", "Estorsione", "Usura", "Riciclaggio", "Autoriciclaggio",
    "Truffa", "Frode informatica", "Accesso abusivo a sistema informatico",
    "Falso documentale", "Omicidio", "Tentato omicidio", "Lesioni", "Minacce",
    "Sequestro di persona", "Violenza sessuale", "Maltrattamenti",
    "Sfruttamento della prostituzione", "Tratta di esseri umani",
    "Favoreggiamento dell'immigrazione clandestina", "Associazione per delinquere",
    "Associazione di tipo mafioso", "Terrorismo", "Contrabbando", "Corruzione",
    "Incendio / danneggiamento", "Arresto / fermo", "Perquisizione / sequestro",
    "Altro",
]
FIN_DOCS = [
    "Fattura", "Ricevuta / scontrino", "Estratto conto", "Bonifico / disposizione di pagamento",
    "Contratto", "Contratto di locazione", "Atto di compravendita", "Polizza assicurativa",
    "Bilancio / nota integrativa", "Busta paga", "Dichiarazione dei redditi",
    "Documento di trasporto (DDT)", "Libro contabile / registro",
    "Contabilità occulta / pizzino", "Visura camerale", "Altro",
]
LEGAL_DOCS = [
    "Verbale di perquisizione", "Verbale di sequestro", "Verbale di arresto / fermo",
    "Verbale di sommarie informazioni", "Verbale di interrogatorio", "Denuncia / querela",
    "Esposto", "Informativa di reato", "Annotazione di polizia giudiziaria",
    "Decreto di perquisizione", "Decreto di sequestro", "Decreto di intercettazione",
    "Ordinanza di custodia cautelare", "Avviso di garanzia",
    "Avviso di conclusione indagini (415-bis)", "Richiesta di rinvio a giudizio",
    "Decreto che dispone il giudizio", "Sentenza", "Mandato di arresto europeo",
    "Rogatoria internazionale", "Relazione di servizio", "Altro",
]
PROPERTY_TYPES = ["Appartamento", "Villa / casa indipendente", "Box / garage", "Cantina",
                  "Magazzino / capannone", "Negozio / locale", "Ufficio", "Terreno", "Altro"]
VALUABLE_TYPES = ["Oro / gioielli", "Orologi di pregio", "Metalli preziosi (lingotti)",
                  "Pietre preziose", "Opere d'arte", "Titoli / obbligazioni",
                  "Buoni fruttiferi", "Beni di lusso", "Altro"]
CARD_CIRCUITS = ["Visa", "Mastercard", "Maestro", "American Express", "Postepay",
                 "Carta prepagata", "Altro"]


def F(key, label, kind="text", options=None, en=None, ph=""):
    return {"key": key, "label": label, "en": en or label, "type": kind,
            "options": options or [], "ph": ph}


# -------------------------------------------------------------- types ---
TYPES = {
    "weapon": {
        "label": "Arma", "en": "Weapon", "group": "Armi",
        "icon": "gun", "color": "#475569",
        "fields": [
            F("categoria", "Categoria", "select", WEAPON_CATEGORIES, "Category"),
            F("marca", "Marca", en="Make", ph="es. Beretta"),
            F("modello", "Modello", en="Model", ph="es. 92FS"),
            F("calibro", "Calibro", "select", CALIBERS + ["Altro"], "Calibre"),
            F("matricola", "Matricola", en="Serial number", ph="numero di matricola"),
            F("matricola_abrasa", "Matricola abrasa / illeggibile", "check", en="Serial number removed"),
            F("stato", "Stato", "select", ["Sequestrata", "Detenuta legalmente", "Denunciata rubata",
                                           "Rinvenuta", "Consegnata", "Altro"], "Status"),
        ],
        # with the serial number the weapon is unique: two seizures of the same weapon
        # are the same node (the make is often not written down: it does not count).
        # Without a serial number (or with it removed) each entry is an exhibit of its own.
        "ident": ["matricola"],
        "label_fmt": ["categoria", "marca", "modello", "calibro:cal. {}", "matricola:matr. {}"],
        "value": "modello",
        "ai": 'weapon: firearms, bladed weapons and similar. fields: categoria (one of the list), '
              'marca, modello, calibro, matricola (serial number, "" if unknown), '
              'matricola_abrasa (true if the serial number is removed), stato.',
    },
    "explosive": {
        "label": "Esplosivo / ordigno", "en": "Explosive", "group": "Armi",
        "icon": "explosion", "color": "#9a3412",
        "fields": [
            F("tipo", "Tipo", "select", EXPLOSIVES, "Type"),
            F("quantita", "Quantità", "number", en="Quantity"),
            F("unita", "Unità", "select", ["g", "kg", "pezzi", "metri"], "Unit"),
            F("descrizione", "Descrizione", en="Description", ph="es. innesco elettrico, timer"),
        ],
        "ident": [], "label_fmt": ["tipo", "quantita+unita"], "value": "tipo",
        "ai": 'explosive: explosives and devices. fields: tipo (one of the list), quantita (number), '
              'unita (g, kg, pezzi, metri), descrizione.',
    },
    "ammo": {
        "label": "Munizioni", "en": "Ammunition", "group": "Armi",
        "icon": "burst", "color": "#78716c",
        "fields": [
            F("calibro", "Calibro", "select", CALIBERS + ["Altro"], "Calibre"),
            F("quantita", "Quantità (colpi)", "number", en="Rounds"),
            F("marca", "Marca", en="Make"),
            F("descrizione", "Descrizione", en="Description"),
        ],
        "ident": [], "label_fmt": ["Munizioni", "calibro:cal. {}", "quantita:{} colpi"], "value": "calibro",
        "ai": 'ammo: ammunition. fields: calibro, quantita (number of rounds), marca, descrizione.',
    },
    "drug": {
        "label": "Sostanza stupefacente", "en": "Narcotic drug", "group": "Stupefacenti",
        "icon": "pills", "color": "#16a34a",
        "fields": [
            F("sostanza", "Sostanza", "select", DRUGS, "Substance"),
            F("quantita", "Quantità", "number", en="Quantity"),
            F("unita", "Unità", "select", DRUG_UNITS, "Unit"),
            F("purezza", "Principio attivo / purezza (%)", "number", en="Purity (%)"),
            F("confezionamento", "Confezionamento", en="Packaging", ph="es. 10 involucri in cellophane"),
            F("descrizione", "Descrizione", en="Description"),
        ],
        # every seizure of a substance is an exhibit of its own
        "ident": [], "label_fmt": ["sostanza", "quantita+unita"], "value": "sostanza",
        "ai": 'drug: narcotic drugs / seizures. fields: sostanza (one of the list), quantita (number), '
              'unita (g, kg, mg, dosi, pasticche, piante, ml, francobolli, confezioni), '
              'purezza (percentage, number), confezionamento, descrizione. '
              'One node per substance and quantity.',
    },
    "cash": {
        "label": "Denaro contante", "en": "Cash", "group": "Valori",
        "icon": "money-bill-wave", "color": "#15803d",
        "fields": [
            F("importo", "Importo", "number", en="Amount"),
            F("valuta", "Valuta", "select", CURRENCIES, "Currency"),
            F("tagli", "Tagli", en="Denominations", ph="es. 30 da 50 €, 20 da 20 €"),
            F("seriali", "Numeri di serie", en="Serial numbers"),
            F("false", "Banconote false", "check", en="Counterfeit"),
            F("descrizione", "Descrizione", en="Description"),
        ],
        "ident": [], "label_fmt": ["importo+valuta", "false:(false)"], "value": "importo",
        "ai": 'cash: cash money. fields: importo (number), valuta (EUR, USD...), tagli, seriali, '
              'false (true if counterfeit), descrizione.',
    },
    "cheque": {
        "label": "Assegno / titolo di credito", "en": "Cheque", "group": "Valori",
        "icon": "money-check", "color": "#0f766e",
        "fields": [
            F("tipo", "Tipo", "select", ["Assegno bancario", "Assegno circolare", "Assegno postale",
                                         "Cambiale", "Vaglia", "Altro"], "Type"),
            F("banca", "Banca / emittente", en="Bank"),
            F("numero", "Numero", en="Number"),
            F("importo", "Importo", "number", en="Amount"),
            F("valuta", "Valuta", "select", CURRENCIES, "Currency"),
            F("data", "Data", "date", en="Date"),
            F("traente", "Traente / emittente", en="Drawer"),
            F("beneficiario", "Beneficiario", en="Payee"),
        ],
        "ident": ["numero"],
        "label_fmt": ["tipo", "numero:n. {}", "importo+valuta"], "value": "numero",
        "ai": 'cheque: cheques, bills of exchange. fields: tipo, banca, numero, importo (number), valuta, '
              'data (YYYY-MM-DD), traente, beneficiario.',
    },
    "valuable": {
        "label": "Beni di valore", "en": "Valuables", "group": "Valori",
        "icon": "gem", "color": "#a16207",
        "fields": [
            F("tipo", "Tipo", "select", VALUABLE_TYPES, "Type"),
            F("descrizione", "Descrizione", en="Description", ph="es. Rolex Submariner"),
            F("valore", "Valore stimato", "number", en="Estimated value"),
            F("valuta", "Valuta", "select", CURRENCIES, "Currency"),
            F("seriale", "Numero di serie", en="Serial number"),
        ],
        "ident": ["seriale"], "label_fmt": ["tipo", "descrizione", "valore+valuta"], "value": "descrizione",
        "ai": 'valuable: gold, jewels, watches, works of art, securities. fields: tipo, descrizione, '
              'valore (number), valuta, seriale.',
    },
    "bankaccount": {
        "label": "Conto bancario (IBAN)", "en": "Bank account", "group": "Finanza",
        "icon": "building-columns", "color": "#1d4ed8",
        "fields": [
            F("iban", "IBAN / numero di conto", en="IBAN / account number"),
            F("banca", "Banca", en="Bank"),
            F("bic", "BIC / SWIFT"),
            F("intestatario", "Intestatario", en="Holder"),
        ],
        "ident": ["iban"], "label_fmt": ["iban", "banca"], "value": "iban", "norm": {"iban": "compact"},
        "ai": 'bankaccount: bank accounts. fields: iban (IBAN or account number), banca, bic, intestatario.',
    },
    "card": {
        "label": "Carta di pagamento", "en": "Payment card", "group": "Finanza",
        "icon": "credit-card", "color": "#1e40af",
        "fields": [
            F("numero", "Numero carta", en="Card number"),
            F("circuito", "Circuito", "select", CARD_CIRCUITS, "Network"),
            F("banca", "Banca emittente", en="Issuer"),
            F("intestatario", "Intestatario", en="Holder"),
            F("scadenza", "Scadenza", en="Expiry", ph="MM/AA"),
        ],
        "ident": ["numero"], "label_fmt": ["circuito", "numero"], "value": "numero", "norm": {"numero": "digits"},
        "ai": 'card: payment cards. fields: numero, circuito, banca, intestatario, scadenza.',
    },
    "crypto": {
        "label": "Wallet criptovalute", "en": "Crypto wallet", "group": "Finanza",
        "icon": "bitcoin", "color": "#c2410c",
        "fields": [
            F("indirizzo", "Indirizzo del wallet", en="Wallet address"),
            F("blockchain", "Blockchain", "select", CRYPTO_CHAINS),
            F("exchange", "Exchange / servizio", en="Exchange"),
        ],
        "ident": ["indirizzo"], "label_fmt": ["blockchain", "indirizzo"], "value": "indirizzo",
        "norm": {"indirizzo": "compact_case"},
        "ai": 'crypto: cryptocurrency wallets. fields: indirizzo (address), blockchain, exchange.',
    },
    "document": {
        "label": "Documento d'identità", "en": "ID document", "group": "Documenti",
        "icon": "id-card", "color": "#0e7490",
        "fields": [
            F("tipo", "Tipo", "select", ID_DOCS, "Type"),
            F("numero", "Numero", en="Number"),
            F("paese", "Paese / autorità di rilascio", en="Issuing country"),
            F("rilascio", "Data di rilascio", "date", en="Issue date"),
            F("scadenza", "Scadenza", "date", en="Expiry date"),
            F("falso", "Documento falso / contraffatto", "check", en="Forged"),
        ],
        "ident": ["numero"],
        "label_fmt": ["tipo", "numero", "falso:(falso)"], "value": "numero", "norm": {"numero": "compact"},
        "ai": 'document: identity documents (carta d\'identità, passaporto, patente, permesso di '
              'soggiorno, codice fiscale...). fields: tipo (one of the list), numero, paese, '
              'rilascio (YYYY-MM-DD), scadenza (YYYY-MM-DD), falso (true if forged).',
    },
    "findoc": {
        "label": "Documento finanziario / commerciale", "en": "Financial document", "group": "Documenti",
        "icon": "file-invoice-dollar", "color": "#0f766e",
        "fields": [
            F("tipo", "Tipo", "select", FIN_DOCS, "Type"),
            F("numero", "Numero", en="Number"),
            F("data", "Data", "date", en="Date"),
            F("emittente", "Emittente", en="Issuer", ph="es. ditta, banca"),
            F("destinatario", "Destinatario / controparte", en="Recipient"),
            F("importo", "Importo", "number", en="Amount"),
            F("valuta", "Valuta", "select", CURRENCIES, "Currency"),
            F("descrizione", "Descrizione / causale", en="Description"),
        ],
        # an invoice is unique by issuer + number
        "ident": ["emittente", "numero"],
        "label_fmt": ["tipo", "numero:n. {}", "data:del {date}", "importo+valuta"], "value": "numero",
        "ai": 'findoc: financial and commercial documents (invoices, receipts, bank statements, '
              'transfers, contracts, leases, deeds, insurance, payslips, tax returns, ledgers, '
              '"pizzini" with accounts). fields: tipo (one of the list), numero, data (YYYY-MM-DD), '
              'emittente, destinatario, importo (number), valuta, descrizione.',
    },
    "legaldoc": {
        "label": "Atto / documento legale", "en": "Legal document", "group": "Documenti",
        "icon": "file-contract", "color": "#57534e",
        "fields": [
            F("tipo", "Tipo di atto", "select", LEGAL_DOCS, "Type"),
            F("numero", "Numero / protocollo", en="Number / reference"),
            F("data", "Data", "date", en="Date"),
            F("autorita", "Autorità / ufficio", en="Authority", ph="es. Procura della Repubblica di Napoli"),
            F("procedimento", "N. procedimento (RGNR)", en="Case number"),
            F("redattore", "Redatto da", en="Author", ph="es. ufficiale di PG"),
            F("descrizione", "Oggetto / descrizione", en="Subject"),
        ],
        "ident": ["tipo", "numero"],
        "label_fmt": ["tipo", "numero:n. {}", "data:del {date}"], "value": "numero",
        "ai": 'legaldoc: legal and police documents (verbali, denunce, informative, annotazioni, '
              'decreti, ordinanze, avvisi, sentenze, MAE, rogatorie). fields: tipo (one of the list), '
              'numero (reference number), data (YYYY-MM-DD), autorita (issuing office), '
              'procedimento (case number), redattore, descrizione.',
    },
    "device": {
        "label": "Dispositivo elettronico", "en": "Device", "group": "Dispositivi",
        "icon": "mobile-screen", "color": "#334155",
        "fields": [
            F("tipo", "Tipo", "select", DEVICES, "Type"),
            F("marca", "Marca", en="Make"),
            F("modello", "Modello", en="Model"),
            F("imei", "IMEI / numero di serie", en="IMEI / serial number"),
            F("descrizione", "Descrizione", en="Description"),
        ],
        "ident": ["imei"], "label_fmt": ["tipo", "marca", "modello", "imei:IMEI {}"], "value": "imei",
        "norm": {"imei": "compact"},
        "ai": 'device: phones, computers, storage. fields: tipo, marca, modello, imei (IMEI or serial), '
              'descrizione. A phone NUMBER is a "phone" node, not a device.',
    },
    "organization": {
        "label": "Organizzazione / azienda", "en": "Organization", "group": "Soggetti",
        "icon": "building", "color": "#7c2d12",
        "fields": [
            F("nome", "Denominazione", en="Name"),
            F("tipo", "Tipo", "select", ORG_TYPES, "Type"),
            F("piva", "Partita IVA / codice fiscale", en="VAT / tax number"),
            F("sede", "Sede", en="Registered office"),
        ],
        # with the VAT number it is unique; without it, the name is
        "ident": ["piva"], "ident_alt": ["nome"], "label_fmt": ["nome", "piva:P.IVA {}"], "value": "nome",
        "norm": {"piva": "compact"},
        "ai": 'organization: companies, associations, criminal groups/clans. fields: nome, tipo, '
              'piva (VAT or tax number), sede.',
    },
    "event": {
        "label": "Evento / reato", "en": "Event / offence", "group": "Fatti",
        "icon": "gavel", "color": "#831843",
        "fields": [
            F("tipo", "Tipo di reato / evento", "select", CRIMES, "Type"),
            F("data", "Data", "date", en="Date"),
            F("luogo", "Luogo", en="Place"),
            F("procedimento", "N. procedimento (RGNR)", en="Case number"),
            F("descrizione", "Descrizione", en="Description"),
        ],
        "ident": ["procedimento", "tipo"],
        "label_fmt": ["tipo", "data:{date}", "procedimento:RGNR {}"], "value": "tipo",
        "ai": 'event: offences and investigative events (arrests, searches, seizures). fields: tipo '
              '(one of the list), data (YYYY-MM-DD), luogo, procedimento (case number), descrizione. '
              'Link the people involved to it (label e.g. "indagato", "vittima", "arrestato").',
    },
    "property": {
        "label": "Immobile", "en": "Real estate", "group": "Beni",
        "icon": "house", "color": "#4338ca",
        "fields": [
            F("tipo", "Tipo", "select", PROPERTY_TYPES, "Type"),
            F("comune", "Comune", en="Town"),
            F("indirizzo", "Indirizzo", en="Address"),
            F("catasto", "Dati catastali (foglio / particella / sub)", en="Land registry data"),
            F("descrizione", "Descrizione", en="Description"),
        ],
        "ident": ["comune", "catasto"],
        "label_fmt": ["tipo", "comune", "indirizzo"], "value": "indirizzo",
        "ai": 'property: real estate (flats, garages, warehouses, land). fields: tipo, comune, '
              'indirizzo, catasto (land registry data), descrizione.',
    },
    "sighting": {
        "label": "Avvistamento aereo", "en": "Aircraft sighting", "group": "Volo",
        "icon": "image", "color": "#0e7490",
        "fields": [
            F("callsign", "Callsign / volo", en="Callsign / flight", ph="es. AZA123"),
            F("icao24", "ICAO24 (hex)", en="ICAO24 (hex)"),
            F("tipo", "Tipo aeromobile", en="Aircraft type", ph="es. A320"),
            F("quando", "Istante stimato (UTC)", en="Estimated time (UTC)"),
            F("azimut", "Azimut (deg)", "number", en="Azimuth (deg)"),
            F("elevazione", "Elevazione (deg)", "number", en="Elevation (deg)"),
            F("confidenza", "Confidenza", "select", ["alta", "media", "bassa"], "Confidence"),
            F("descrizione", "Descrizione", en="Description"),
        ],
        "ident": ["callsign", "quando"],
        "label_fmt": ["callsign", "tipo", "quando"], "value": "callsign",
        "ai": 'sighting: an aircraft seen in a photograph. fields: callsign, icao24, tipo, quando, azimut, elevazione, confidenza, descrizione.',
    },
}

from .generated.ontology_ftm import FTM_TYPES
TYPES.update(FTM_TYPES)

# icon per substance (more recognisable than the generic pill)
DRUG_ICONS = {
    "Hashish": "cannabis", "Marijuana": "cannabis", "Olio di cannabis": "cannabis",
    "Piante di cannabis": "cannabis", "Cannabinoidi sintetici": "cannabis",
    "Eroina": "syringe", "Fentanyl e derivati": "syringe", "Morfina": "syringe",
    "Oppio": "syringe", "Metadone": "syringe",
    "Cocaina": "vial", "Crack": "vial", "Precursori chimici": "vial", "Ketamina": "vial",
    "MDMA / Ecstasy": "prescription-bottle-medical", "Anfetamina": "prescription-bottle-medical",
    "Metanfetamina": "prescription-bottle-medical", "Buprenorfina": "prescription-bottle-medical",
    "Ossicodone / oppioidi farmaceutici": "prescription-bottle-medical",
    "Benzodiazepine": "prescription-bottle-medical",
    "Catinoni sintetici (mefedrone…)": "prescription-bottle-medical",
    "Khat": "leaf", "Kratom": "leaf", "Mescalina": "leaf",
    "GHB / GBL": "droplet", "Sostanza non identificata": "microscope",
}
DOC_ICONS = {"Passaporto": "passport", "Carta d'identità": "address-card",
             "Patente di guida": "id-card-clip", "Permesso di soggiorno": "stamp",
             "Codice fiscale / tessera sanitaria": "notes-medical", "Visto": "plane-departure",
             "Documento di viaggio": "plane-departure", "Tessera di riconoscimento": "id-badge"}
FINDOC_ICONS = {"Ricevuta / scontrino": "receipt", "Estratto conto": "receipt",
                "Bonifico / disposizione di pagamento": "receipt", "Contratto": "file-contract",
                "Contratto di locazione": "file-contract", "Atto di compravendita": "file-contract",
                "Fattura": "file-invoice", "Polizza assicurativa": "file-shield",
                "Bilancio / nota integrativa": "chart-column", "Libro contabile / registro": "book",
                "Contabilità occulta / pizzino": "note-sticky",
                "Documento di trasporto (DDT)": "truck-ramp-box",
                "Visura camerale": "certificate", "Dichiarazione dei redditi": "certificate"}
LEGALDOC_ICONS = {
    "Sentenza": "scale-balanced", "Decreto che dispone il giudizio": "scale-balanced",
    "Verbale di arresto / fermo": "handcuffs", "Ordinanza di custodia cautelare": "handcuffs",
    "Mandato di arresto europeo": "handcuffs",
    "Verbale di perquisizione": "magnifying-glass", "Decreto di perquisizione": "magnifying-glass",
    "Verbale di sequestro": "magnifying-glass", "Decreto di sequestro": "magnifying-glass",
    "Verbale di sommarie informazioni": "microphone", "Verbale di interrogatorio": "microphone",
    "Decreto di intercettazione": "satellite-dish",
    "Denuncia / querela": "file-pen", "Esposto": "file-pen",
    "Informativa di reato": "shield", "Annotazione di polizia giudiziaria": "shield",
    "Relazione di servizio": "shield",
    "Avviso di garanzia": "clipboard-list", "Avviso di conclusione indagini (415-bis)": "clipboard-list",
    "Richiesta di rinvio a giudizio": "clipboard-list",
    "Rogatoria internazionale": "earth-europe",
}
DEVICE_ICONS = {"PC portatile": "laptop", "PC fisso": "desktop",
                "Smartphone": "mobile-screen-button", "Cellulare": "mobile-screen-button",
                "Tablet": "mobile-screen-button", "Hard disk / SSD": "hard-drive",
                "Chiavetta USB / memory card": "usb", "Router / modem": "router",
                "Dispositivo GPS": "location-crosshairs", "Criptofonino": "user-lock"}

# icons of the pre-existing types (Font Awesome Free)
BASE_ICONS = {
    "target": "user-secret", "name": "user", "phone": "phone", "email": "envelope",
    "username": "at", "generic": "circle-question", "vehicle": "car", "link": "link",
    "text": "file-lines", "place": "location-dot", "latin": "language", "photo": "image",
    "domain": "globe", "breach": "shield-halved",
}

# names the user or the AI use for the types (CSV import, AI)
ALIASES = {
    "sighting": {"avvistamento", "sighting", "aereo", "aircraft", "volo", "flight"},
    "weapon": {"arma", "armi", "weapon", "pistola", "fucile", "revolver", "firearm", "gun", "rifle"},
    "explosive": {"esplosivo", "esplosivi", "ordigno", "bomba", "explosive", "explosives"},
    "ammo": {"munizioni", "munizione", "cartucce", "proiettili", "ammo", "ammunition"},
    "drug": {"droga", "stupefacente", "stupefacenti", "sostanza", "narcotic", "drug", "drugs"},
    "cash": {"contanti", "denaro", "soldi", "banconote", "cash", "money"},
    "cheque": {"assegno", "assegni", "cambiale", "cheque", "check"},
    "valuable": {"preziosi", "gioielli", "valori", "orologio", "valuable", "valuables", "jewels"},
    "bankaccount": {"conto", "iban", "contocorrente", "bankaccount", "account bancario"},
    "card": {"carta", "cartadicredito", "bancomat", "card", "creditcard"},
    "crypto": {"crypto", "wallet", "bitcoin", "criptovaluta", "criptovalute"},
    "document": {"documento", "passaporto", "patente", "cartaidentita", "document", "passport", "id"},
    "findoc": {"fattura", "fatture", "ricevuta", "estrattoconto", "contratto", "bonifico",
               "documentofinanziario", "invoice", "receipt", "contract"},
    "legaldoc": {"verbale", "denuncia", "querela", "decreto", "ordinanza", "sentenza",
                 "informativa", "annotazione", "atto", "documentolegale", "legaldocument"},
    "device": {"dispositivo", "imei", "smartphone", "cellulare", "computer", "device"},
    "organization": {"organizzazione", "azienda", "societa", "ditta", "impresa", "clan",
                     "organization", "organisation", "company"},
    "event": {"evento", "reato", "fatto", "arresto", "perquisizione", "sequestro", "event", "crime"},
    "property": {"immobile", "appartamento", "casa", "garage", "box", "terreno", "property"},
}


# ---------------------------------------------------------- functions ---
def _fold(s):
    s = unicodedata.normalize("NFKD", str(s or "")).casefold()
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^\w/]+", " ", s)).strip()


def _norm_value(kind, v):
    v = str(v or "").strip()
    if kind == "compact":
        return re.sub(r"[\s.\-/]+", "", v).upper()
    if kind == "compact_case":                      # crypto addresses: case-sensitive
        return re.sub(r"\s+", "", v)
    if kind == "digits":
        return re.sub(r"\D", "", v)
    return _fold(v)


def type_of(name):
    """'pistola' / 'Arma' / 'weapon' -> 'weapon' (None if it is not an ontology type)."""
    n = re.sub(r"[^a-z]", "", _fold(name))
    if n in TYPES:
        return n
    for t, al in ALIASES.items():
        if n in {re.sub(r"[^a-z]", "", _fold(a)) for a in al}:
            return t
    return None


_SERIAL_GONE = re.compile(r"^\W*(abras|limat|cancellat|illeggibil|assent|rimoss|non leggibil|"
                          r"removed|obliterat|none|n\.?d\.?|nessuna)", re.I)


def key_is_serial(ntype, key):
    return ntype == "weapon" and key == "matricola"


def clean_fields(ntype, raw):
    """Only the fields defined by the type, cleaned up. Options outside the list
    are kept (the user or the AI may write an unlisted value)."""
    spec = TYPES[ntype]
    out = {}
    raw = raw if isinstance(raw, dict) else {}
    for f in spec["fields"]:
        v = raw.get(f["key"])
        if f["type"] == "check":
            if v is True or str(v or "").strip().lower() in ("1", "true", "si", "sì", "yes", "on", "x"):
                out[f["key"]] = True
            continue
        v = re.sub(r"\s+", " ", str(v if v is not None else "")).strip()[:300]
        if not v:
            continue
        if f["type"] == "number":
            n = v.replace(" ", "").replace("€", "").replace("$", "")
            if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", n):      # 15.000,50
                n = n.replace(".", "").replace(",", ".")
            else:
                n = n.replace(",", ".")
            try:
                float(n)
                v = n
            except ValueError:
                pass                                          # keep the text
        if key_is_serial(ntype, f["key"]) and _SERIAL_GONE.search(v):
            out["matricola_abrasa"] = True                    # "abrasa", "limata"...
            continue
        if f["type"] == "select" and f["options"]:
            hit = next((o for o in f["options"] if _fold(o) == _fold(v)), None)
            v = hit or v
        out[f["key"]] = v
    return out


def _fmt_num(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return str(v)
    if x == int(x):
        return f"{int(x):,}".replace(",", ".")
    s = f"{x:,.2f}".rstrip("0")                      # 1.50 -> 1.5
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def label_of(ntype, fields):
    """Node label from the fields, following 'label_fmt'."""
    parts = []
    for item in TYPES[ntype]["label_fmt"]:
        if ":" in item:                                  # field:format
            key, fmt = item.split(":", 1)
            v = fields.get(key)
            if not v:
                continue
            if v is True:
                parts.append(fmt)
            elif "{date}" in fmt:
                d = f"{v[8:10]}/{v[5:7]}/{v[:4]}" if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v) else v
                parts.append(fmt.replace("{date}", d))
            else:
                pre = fmt.split("{}")[0].strip()
                # 'RGNR 1234/2026' with format 'RGNR {}': no doubled prefix
                parts.append(str(v) if pre and _fold(str(v)).startswith(_fold(pre)) else fmt.format(v))
        elif "+" in item:                                # quantita+unita, importo+valuta
            a, b = item.split("+", 1)
            if fields.get(a):
                num = _fmt_num(fields[a])
                parts.append(f"{num} {fields.get(b, '')}".strip())
        elif item in fields:
            v = fields[item]
            if v is not True:
                parts.append(str(v))
        elif not any(f["key"] == item for f in TYPES[ntype]["fields"]):
            parts.append(item)                           # fixed text ("Munizioni")
    # no repetitions: for FtM schemas the caption may land twice on the
    # same value (e.g. unnamed account: name = IBAN = IBAN)
    seen, uniq = set(), []
    for p in parts:
        if p and p.casefold() not in seen:
            seen.add(p.casefold())
            uniq.append(p)
    lab = " ".join(uniq).strip()
    return lab or TYPES[ntype]["label"]


# identifying fields that are words (compared ignoring accents and case);
# the others are codes (serial number, number, IBAN...): no spaces or punctuation
_WORD_KEYS = {"marca", "banca", "tipo", "comune", "nome", "blockchain"}


def ident_of(ntype, fields):
    """Identity key ('' = exhibit with no identifier: new node)."""
    spec = TYPES[ntype]
    norm = spec.get("norm", {})
    need = spec.get("ident_min") or spec.get("ident") or []
    if not need:
        return ""
    if fields.get("matricola_abrasa") and ntype == "weapon":
        return ""
    if all(fields.get(k) for k in need):
        keys = spec["ident"]
        vals = [_norm_value(norm.get(k) or ("fold" if k in _WORD_KEYS else "compact"),
                            fields.get(k, "")) for k in keys]
        return "|".join(vals)
    alt = spec.get("ident_alt")
    if alt and all(fields.get(k) for k in alt):
        return "name|" + "|".join(_fold(fields[k]) for k in alt)
    return ""


def icon_of(ntype, fields):
    if ntype == "drug":
        return DRUG_ICONS.get(fields.get("sostanza"), TYPES[ntype]["icon"])
    if ntype == "document":
        return DOC_ICONS.get(fields.get("tipo"), TYPES[ntype]["icon"])
    if ntype == "findoc":
        return FINDOC_ICONS.get(fields.get("tipo"), TYPES[ntype]["icon"])
    if ntype == "legaldoc":
        return LEGALDOC_ICONS.get(fields.get("tipo"), TYPES[ntype]["icon"])
    if ntype == "device":
        return DEVICE_ICONS.get(fields.get("tipo"), TYPES[ntype]["icon"])
    return TYPES[ntype]["icon"] if ntype in TYPES else BASE_ICONS.get(ntype, "circle-question")


def raw_of(ntype, fields):
    """Readable fields for the card: {'Categoria': 'Pistola', ...}."""
    out = {}
    for f in TYPES[ntype]["fields"]:
        v = fields.get(f["key"])
        if v in (None, "", False):
            continue
        out[f["label"]] = "sì" if v is True else v
    return out


def ai_rules():
    """Instructions for the AI prompt (one line per type, with the lists)."""
    lines = ["  For select fields choose the option whose words best match the TEXT "
             "(e.g. \"traffico di stupefacenti\" -> \"Traffico di stupefacenti\", not \"Spaccio\").",
             "  Link labels for items: seized items linked from the person with \"sequestrato\" "
             "(or \"detiene\", \"possiede\", \"utilizza\", \"intestatario\" when the TEXT says so); "
             "the person linked to an offence with \"indagato\" / \"arrestato\" / \"vittima\"; "
             "seized items linked to the offence/event with \"sequestrato nel\"."]
    for t, spec in TYPES.items():
        lines.append(f"- {spec['ai']}")
        for f in spec["fields"]:
            if f["type"] == "select" and len(f["options"]) > 2:
                lines.append(f"    {f['key']} options: " + "; ".join(f["options"]))
    return "\n".join(lines)


def public():
    """Configuration for the client (entry form, icons, colours)."""
    return {t: {"label": s["label"], "en": s["en"], "group": s["group"], "icon": s["icon"],
                "color": s["color"], "fields": s["fields"], "order": i}
            for i, (t, s) in enumerate(TYPES.items())}
