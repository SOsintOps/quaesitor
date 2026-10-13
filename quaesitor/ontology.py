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

Keys, labels and options are English: that is what is saved and compared. The
interface shows them in its language through ontology_i18n; the input (forms,
imports, AI) may still use the Italian keys and the options of any interface
language: clean_fields brings them back to the English ones.
"""
# "Quot homines, tot sententiae." (Terence, Phormio)
# As many opinions as there are men.
import re
import unicodedata

# -------------------------------------------------------------- lists ---
WEAPON_CATEGORIES = [
    "Semi-automatic pistol", "Revolver", "Submachine gun", "Hunting rifle",
    "Pump-action shotgun", "Carbine", "Sniper rifle", "Assault rifle",
    "Machine gun", "Blank-firing / converted gun", "Air gun",
    "Improvised / home-made gun", "Bladed weapon (knife, machete…)", "Crossbow / bow",
    "Stun gun / spray", "Other",
]
CALIBERS = [
    "9x19 Parabellum", "9x21 IMI", "7.65 Browning (.32 ACP)", "6.35 Browning (.25 ACP)",
    ".22 LR", ".38 Special", ".357 Magnum", ".44 Magnum", ".45 ACP", ".40 S&W",
    "7.62x39", "5.56x45 NATO", "7.62x51 NATO (.308 Win)", ".30-06", "12 gauge",
    "16 gauge", "20 gauge", "4.5 mm (air gun)",
]
EXPLOSIVES = [
    "Dynamite", "TNT", "Plastic explosive (C4 / Semtex)", "PETN",
    "Black powder", "Smokeless powder", "ANFO", "TATP", "Nitroglycerin",
    "Blasting gelatin", "Improvised explosive device (IED)", "Hand grenade",
    "Detonators / primers", "Detonating cord", "Illegal fireworks",
    "Other",
]
DRUGS = [
    "Cocaine", "Crack", "Heroin", "Hashish", "Marijuana", "Cannabis oil",
    "Cannabis plants", "MDMA / Ecstasy", "Amphetamine", "Methamphetamine",
    "Ketamine", "LSD", "Magic mushrooms (psilocybin)", "Mescaline",
    "Fentanyl and analogues", "Opium", "Morphine", "Methadone", "Buprenorphine",
    "Oxycodone / pharmaceutical opioids", "Benzodiazepines", "GHB / GBL",
    "Synthetic cannabinoids", "Synthetic cathinones (mephedrone…)", "Khat", "Kratom",
    "Chemical precursors", "Cutting agent", "Unidentified substance", "Other",
]
DRUG_UNITS = ["g", "kg", "mg", "doses", "pills", "plants", "ml", "blotters", "packs"]
CURRENCIES = ["EUR", "USD", "GBP", "CHF", "LYD", "TND", "MAD", "EGP", "DZD", "TRY",
              "ALL", "RON", "RUB", "UAH", "CNY", "AED", "SAR", "Other"]
CRYPTO_CHAINS = ["Bitcoin", "Ethereum", "Tether (USDT) - TRON", "Tether (USDT) - Ethereum",
                 "Monero", "Litecoin", "Solana", "BNB Chain", "Other"]
ID_DOCS = ["Identity card", "Passport", "Driving licence", "Residence permit",
           "Tax code / health card", "Visa", "Travel document",
           "ID badge", "Other"]
DEVICES = ["Smartphone", "Mobile phone", "Tablet", "Laptop", "Desktop PC", "Hard disk / SSD",
           "USB stick / memory card", "Router / modem", "GPS device", "Encrypted phone",
           "Other"]
ORG_TYPES = ["Limited company", "Partnership", "Sole proprietorship",
             "Association", "Public body", "Criminal group", "Clan / mafia family",
             "Terrorist organization", "Other"]
CRIMES = [
    "Drug dealing", "Drug trafficking", "Drug possession",
    "Illegal possession / carrying of weapons", "Arms trafficking", "Robbery", "Theft",
    "Handling stolen goods", "Extortion", "Usury / loan sharking", "Money laundering", "Self-laundering",
    "Fraud", "Computer fraud", "Unauthorised computer access",
    "Document forgery", "Homicide", "Attempted homicide", "Assault / bodily harm", "Threats",
    "Kidnapping", "Sexual assault", "Domestic abuse",
    "Exploitation of prostitution", "Human trafficking",
    "Migrant smuggling", "Criminal conspiracy",
    "Mafia-type association", "Terrorism", "Smuggling", "Corruption",
    "Arson / criminal damage", "Arrest", "Search / seizure",
    "Other",
]
FIN_DOCS = [
    "Invoice", "Receipt", "Bank statement", "Bank transfer / payment order",
    "Contract", "Lease", "Deed of sale", "Insurance policy",
    "Financial statement", "Payslip", "Tax return",
    "Delivery note", "Ledger / register",
    "Hidden accounts / crime note", "Company register extract", "Other",
]
LEGAL_DOCS = [
    "Search report", "Seizure report", "Arrest report",
    "Witness statement", "Interrogation report", "Complaint / report",
    "Petition / complaint", "Crime report to prosecutor", "Police report note",
    "Search warrant", "Seizure order", "Interception order",
    "Pre-trial detention order", "Notice of investigation",
    "Notice of end of investigation", "Request for indictment",
    "Committal for trial", "Judgment", "European arrest warrant",
    "Letter rogatory", "Service report", "Other",
]
PROPERTY_TYPES = ["Flat", "Detached house", "Garage", "Cellar",
                  "Warehouse", "Shop / premises", "Office", "Land", "Other"]
VALUABLE_TYPES = ["Gold / jewellery", "Luxury watches", "Precious metals (bullion)",
                  "Precious stones", "Works of art", "Securities / bonds",
                  "Savings bonds", "Luxury goods", "Other"]
CARD_CIRCUITS = ["Visa", "Mastercard", "Maestro", "American Express", "Postepay",
                 "Prepaid card", "Other"]


def F(key, label, kind="text", options=None, ph=""):
    return {"key": key, "label": label, "type": kind, "options": options or [], "ph": ph}


# -------------------------------------------------------------- types ---
TYPES = {
    "weapon": {
        "label": "Weapon", "group": "Weapons",
        "icon": "gun", "color": "#475569",
        "fields": [
            F("category", "Category", "select", WEAPON_CATEGORIES),
            F("make", "Make", ph="e.g. Beretta"),
            F("model", "Model", ph="e.g. 92FS"),
            F("calibre", "Calibre", "select", CALIBERS + ["Other"]),
            F("serial_number", "Serial number", ph="serial number"),
            F("serial_removed", "Serial number removed / illegible", "check"),
            F("status", "Status", "select", ["Seized", "Legally held", "Reported stolen",
                                             "Found", "Handed over", "Other"]),
        ],
        # with the serial number the weapon is unique: two seizures of the same weapon
        # are the same node (the make is often not written down: it does not count).
        # Without a serial number (or with it removed) each entry is an exhibit of its own.
        "ident": ["serial_number"],
        "label_fmt": ["category", "make", "model", "calibre:cal. {}", "serial_number:s/n {}"],
        "value": "model",
        "ai": 'weapon: firearms, bladed weapons and similar. fields: category (one of the list), '
              'make, model, calibre, serial_number ("" if unknown), '
              'serial_removed (true if the serial number is removed), status.',
    },
    "explosive": {
        "label": "Explosive / device", "group": "Weapons",
        "icon": "explosion", "color": "#9a3412",
        "fields": [
            F("type", "Type", "select", EXPLOSIVES),
            F("quantity", "Quantity", "number"),
            F("unit", "Unit", "select", ["g", "kg", "pieces", "metres"]),
            F("description", "Description", ph="e.g. electric detonator, timer"),
        ],
        "ident": [], "label_fmt": ["type", "quantity+unit"], "value": "type",
        "ai": 'explosive: explosives and devices. fields: type (one of the list), quantity (number), '
              'unit (g, kg, pieces, metres), description.',
    },
    "ammo": {
        "label": "Ammunition", "group": "Weapons",
        "icon": "burst", "color": "#78716c",
        "fields": [
            F("calibre", "Calibre", "select", CALIBERS + ["Other"]),
            F("quantity", "Quantity (rounds)", "number"),
            F("make", "Make"),
            F("description", "Description"),
        ],
        "ident": [], "label_fmt": ["Ammunition", "calibre:cal. {}", "quantity:{} rounds"], "value": "calibre",
        "ai": 'ammo: ammunition. fields: calibre, quantity (number of rounds), make, description.',
    },
    "drug": {
        "label": "Narcotic drug", "group": "Drugs",
        "icon": "pills", "color": "#16a34a",
        "fields": [
            F("substance", "Substance", "select", DRUGS),
            F("quantity", "Quantity", "number"),
            F("unit", "Unit", "select", DRUG_UNITS),
            F("purity", "Active ingredient / purity (%)", "number"),
            F("packaging", "Packaging", ph="e.g. 10 cellophane wraps"),
            F("description", "Description"),
        ],
        # every seizure of a substance is an exhibit of its own
        "ident": [], "label_fmt": ["substance", "quantity+unit"], "value": "substance",
        "ai": 'drug: narcotic drugs / seizures. fields: substance (one of the list), quantity (number), '
              'unit (g, kg, mg, doses, pills, plants, ml, blotters, packs), '
              'purity (percentage, number), packaging, description. '
              'One node per substance and quantity.',
    },
    "cash": {
        "label": "Cash", "group": "Money and valuables",
        "icon": "money-bill-wave", "color": "#15803d",
        "fields": [
            F("amount", "Amount", "number"),
            F("currency", "Currency", "select", CURRENCIES),
            F("denominations", "Denominations", ph="e.g. 30 × €50, 20 × €20"),
            F("serial_numbers", "Serial numbers"),
            F("counterfeit", "Counterfeit banknotes", "check"),
            F("description", "Description"),
        ],
        "ident": [], "label_fmt": ["amount+currency", "counterfeit:(counterfeit)"], "value": "amount",
        "ai": 'cash: cash money. fields: amount (number), currency (EUR, USD...), denominations, '
              'serial_numbers, counterfeit (true if counterfeit), description.',
    },
    "cheque": {
        "label": "Cheque / negotiable instrument", "group": "Money and valuables",
        "icon": "money-check", "color": "#0f766e",
        "fields": [
            F("type", "Type", "select", ["Bank cheque", "Cashier's cheque", "Postal cheque",
                                         "Bill of exchange", "Money order", "Other"]),
            F("bank", "Bank / issuer"),
            F("number", "Number"),
            F("amount", "Amount", "number"),
            F("currency", "Currency", "select", CURRENCIES),
            F("date", "Date", "date"),
            F("drawer", "Drawer / issuer"),
            F("payee", "Payee"),
        ],
        "ident": ["number"],
        "label_fmt": ["type", "number:no. {}", "amount+currency"], "value": "number",
        "ai": 'cheque: cheques, bills of exchange. fields: type, bank, number, amount (number), currency, '
              'date (YYYY-MM-DD), drawer, payee.',
    },
    "valuable": {
        "label": "Valuables", "group": "Money and valuables",
        "icon": "gem", "color": "#a16207",
        "fields": [
            F("type", "Type", "select", VALUABLE_TYPES),
            F("description", "Description", ph="e.g. Rolex Submariner"),
            F("estimated_value", "Estimated value", "number"),
            F("currency", "Currency", "select", CURRENCIES),
            F("serial_number", "Serial number"),
        ],
        "ident": ["serial_number"], "label_fmt": ["type", "description", "estimated_value+currency"], "value": "description",
        "ai": 'valuable: gold, jewels, watches, works of art, securities. fields: type, description, '
              'estimated_value (number), currency, serial_number.',
    },
    "bankaccount": {
        "label": "Bank account (IBAN)", "group": "Finance",
        "icon": "building-columns", "color": "#1d4ed8",
        "fields": [
            F("iban", "IBAN / account number"),
            F("bank", "Bank"),
            F("bic", "BIC / SWIFT"),
            F("holder", "Holder"),
        ],
        "ident": ["iban"], "label_fmt": ["iban", "bank"], "value": "iban", "norm": {"iban": "compact"},
        "ai": 'bankaccount: bank accounts. fields: iban (IBAN or account number), bank, bic, holder.',
    },
    "card": {
        "label": "Payment card", "group": "Finance",
        "icon": "credit-card", "color": "#1e40af",
        "fields": [
            F("number", "Card number"),
            F("network", "Network", "select", CARD_CIRCUITS),
            F("bank", "Issuing bank"),
            F("holder", "Holder"),
            F("expiry", "Expiry", ph="MM/YY"),
        ],
        "ident": ["number"], "label_fmt": ["network", "number"], "value": "number", "norm": {"number": "digits"},
        "ai": 'card: payment cards. fields: number, network, bank, holder, expiry.',
    },
    "crypto": {
        "label": "Crypto wallet", "group": "Finance",
        "icon": "bitcoin", "color": "#c2410c",
        "fields": [
            F("address", "Wallet address"),
            F("blockchain", "Blockchain", "select", CRYPTO_CHAINS),
            F("exchange", "Exchange / service"),
        ],
        "ident": ["address"], "label_fmt": ["blockchain", "address"], "value": "address",
        "norm": {"address": "compact_case"},
        "ai": 'crypto: cryptocurrency wallets. fields: address, blockchain, exchange.',
    },
    "document": {
        "label": "ID document", "group": "Documents",
        "icon": "id-card", "color": "#0e7490",
        "fields": [
            F("type", "Type", "select", ID_DOCS),
            F("number", "Number"),
            F("country", "Issuing country / authority"),
            F("issue_date", "Issue date", "date"),
            F("expiry", "Expiry", "date"),
            F("forged", "Forged / counterfeit document", "check"),
        ],
        "ident": ["number"],
        "label_fmt": ["type", "number", "forged:(forged)"], "value": "number", "norm": {"number": "compact"},
        "ai": 'document: identity documents (identity card, passport, driving licence, residence '
              'permit, tax code...). fields: type (one of the list), number, country, '
              'issue_date (YYYY-MM-DD), expiry (YYYY-MM-DD), forged (true if forged).',
    },
    "findoc": {
        "label": "Financial / commercial document", "group": "Documents",
        "icon": "file-invoice-dollar", "color": "#0f766e",
        "fields": [
            F("type", "Type", "select", FIN_DOCS),
            F("number", "Number"),
            F("date", "Date", "date"),
            F("issuer", "Issuer", ph="e.g. company, bank"),
            F("recipient", "Recipient / counterparty"),
            F("amount", "Amount", "number"),
            F("currency", "Currency", "select", CURRENCIES),
            F("description", "Description / purpose"),
        ],
        # an invoice is unique by issuer + number
        "ident": ["issuer", "number"],
        "label_fmt": ["type", "number:no. {}", "date:of {date}", "amount+currency"], "value": "number",
        "ai": 'findoc: financial and commercial documents (invoices, receipts, bank statements, '
              'transfers, contracts, leases, deeds, insurance, payslips, tax returns, ledgers, '
              'notes with hidden accounts). fields: type (one of the list), number, date (YYYY-MM-DD), '
              'issuer, recipient, amount (number), currency, description.',
    },
    "legaldoc": {
        "label": "Legal document", "group": "Documents",
        "icon": "file-contract", "color": "#57534e",
        "fields": [
            F("type", "Document type", "select", LEGAL_DOCS),
            F("number", "Number / reference"),
            F("date", "Date", "date"),
            F("authority", "Authority / office", ph="e.g. Public Prosecutor's Office of Naples"),
            F("case_number", "Case number"),
            F("author", "Drawn up by", ph="e.g. police officer"),
            F("description", "Subject / description"),
        ],
        "ident": ["type", "number"],
        "label_fmt": ["type", "number:no. {}", "date:of {date}"], "value": "number",
        "ai": 'legaldoc: legal and police documents (reports, complaints, warrants, orders, notices, '
              'judgments, European arrest warrants, letters rogatory). fields: type (one of the list), '
              'number (reference number), date (YYYY-MM-DD), authority (issuing office), '
              'case_number, author, description.',
    },
    "device": {
        "label": "Electronic device", "group": "Devices",
        "icon": "mobile-screen", "color": "#334155",
        "fields": [
            F("type", "Type", "select", DEVICES),
            F("make", "Make"),
            F("model", "Model"),
            F("imei", "IMEI / serial number"),
            F("description", "Description"),
        ],
        "ident": ["imei"], "label_fmt": ["type", "make", "model", "imei:IMEI {}"], "value": "imei",
        "norm": {"imei": "compact"},
        "ai": 'device: phones, computers, storage. fields: type, make, model, imei (IMEI or serial), '
              'description. A phone NUMBER is a "phone" node, not a device.',
    },
    "organization": {
        "label": "Organization / company", "group": "Organizations",
        "icon": "building", "color": "#7c2d12",
        "fields": [
            F("name", "Name"),
            F("type", "Type", "select", ORG_TYPES),
            F("tax_number", "VAT / tax number"),
            F("registered_office", "Registered office"),
        ],
        # with the VAT number it is unique; without it, the name is
        "ident": ["tax_number"], "ident_alt": ["name"], "label_fmt": ["name", "tax_number:VAT {}"], "value": "name",
        "norm": {"tax_number": "compact"},
        "ai": 'organization: companies, associations, criminal groups/clans. fields: name, type, '
              'tax_number (VAT or tax number), registered_office.',
    },
    "event": {
        "label": "Event / offence", "group": "Events / offences",
        "icon": "gavel", "color": "#831843",
        "fields": [
            F("type", "Offence / event type", "select", CRIMES),
            F("date", "Date", "date"),
            F("place", "Place"),
            F("case_number", "Case number"),
            F("description", "Description"),
        ],
        "ident": ["case_number", "type"],
        "label_fmt": ["type", "date:{date}", "case_number:case {}"], "value": "type",
        "ai": 'event: offences and investigative events (arrests, searches, seizures). fields: type '
              '(one of the list), date (YYYY-MM-DD), place, case_number, description. '
              'Link the people involved to it (label e.g. "suspect", "victim", "arrested").',
    },
    "property": {
        "label": "Real estate", "group": "Properties",
        "icon": "house", "color": "#4338ca",
        "fields": [
            F("type", "Type", "select", PROPERTY_TYPES),
            F("town", "Town"),
            F("address", "Address"),
            F("land_registry", "Land registry data"),
            F("description", "Description"),
        ],
        "ident": ["town", "land_registry"],
        "label_fmt": ["type", "town", "address"], "value": "address",
        "ai": 'property: real estate (flats, garages, warehouses, land). fields: type, town, '
              'address, land_registry (land registry data), description.',
    },
    "sighting": {
        "label": "Aircraft sighting", "group": "Flight",
        "icon": "image", "color": "#0e7490",
        "fields": [
            F("callsign", "Callsign / flight", ph="e.g. AZA123"),
            F("icao24", "ICAO24 (hex)"),
            F("type", "Aircraft type", ph="e.g. A320"),
            F("time", "Estimated time (UTC)"),
            F("azimuth", "Azimuth (deg)", "number"),
            F("elevation", "Elevation (deg)", "number"),
            F("confidence", "Confidence", "select", ["high", "medium", "low"]),
            F("description", "Description"),
        ],
        "ident": ["callsign", "time"],
        "label_fmt": ["callsign", "type", "time"], "value": "callsign",
        "ai": 'sighting: an aircraft seen in a photograph. fields: callsign, icao24, type, time, '
              'azimuth, elevation, confidence (high, medium, low), description.',
    },
}

from .generated.ontology_ftm import FTM_TYPES
TYPES.update(FTM_TYPES)

# icon per substance (more recognisable than the generic pill)
DRUG_ICONS = {
    "Hashish": "cannabis", "Marijuana": "cannabis", "Cannabis oil": "cannabis",
    "Cannabis plants": "cannabis", "Synthetic cannabinoids": "cannabis",
    "Heroin": "syringe", "Fentanyl and analogues": "syringe", "Morphine": "syringe",
    "Opium": "syringe", "Methadone": "syringe",
    "Cocaine": "vial", "Crack": "vial", "Chemical precursors": "vial", "Ketamine": "vial",
    "MDMA / Ecstasy": "prescription-bottle-medical", "Amphetamine": "prescription-bottle-medical",
    "Methamphetamine": "prescription-bottle-medical", "Buprenorphine": "prescription-bottle-medical",
    "Oxycodone / pharmaceutical opioids": "prescription-bottle-medical",
    "Benzodiazepines": "prescription-bottle-medical",
    "Synthetic cathinones (mephedrone…)": "prescription-bottle-medical",
    "Khat": "leaf", "Kratom": "leaf", "Mescaline": "leaf",
    "GHB / GBL": "droplet", "Unidentified substance": "microscope",
}
DOC_ICONS = {"Passport": "passport", "Identity card": "address-card",
             "Driving licence": "id-card-clip", "Residence permit": "stamp",
             "Tax code / health card": "notes-medical", "Visa": "plane-departure",
             "Travel document": "plane-departure", "ID badge": "id-badge"}
FINDOC_ICONS = {"Receipt": "receipt", "Bank statement": "receipt",
                "Bank transfer / payment order": "receipt", "Contract": "file-contract",
                "Lease": "file-contract", "Deed of sale": "file-contract",
                "Invoice": "file-invoice", "Insurance policy": "file-shield",
                "Financial statement": "chart-column", "Ledger / register": "book",
                "Hidden accounts / crime note": "note-sticky",
                "Delivery note": "truck-ramp-box",
                "Company register extract": "certificate", "Tax return": "certificate"}
LEGALDOC_ICONS = {
    "Judgment": "scale-balanced", "Committal for trial": "scale-balanced",
    "Arrest report": "handcuffs", "Pre-trial detention order": "handcuffs",
    "European arrest warrant": "handcuffs",
    "Search report": "magnifying-glass", "Search warrant": "magnifying-glass",
    "Seizure report": "magnifying-glass", "Seizure order": "magnifying-glass",
    "Witness statement": "microphone", "Interrogation report": "microphone",
    "Interception order": "satellite-dish",
    "Complaint / report": "file-pen", "Petition / complaint": "file-pen",
    "Crime report to prosecutor": "shield", "Police report note": "shield",
    "Service report": "shield",
    "Notice of investigation": "clipboard-list", "Notice of end of investigation": "clipboard-list",
    "Request for indictment": "clipboard-list",
    "Letter rogatory": "earth-europe",
}
DEVICE_ICONS = {"Laptop": "laptop", "Desktop PC": "desktop",
                "Smartphone": "mobile-screen-button", "Mobile phone": "mobile-screen-button",
                "Tablet": "mobile-screen-button", "Hard disk / SSD": "hard-drive",
                "USB stick / memory card": "usb", "Router / modem": "router",
                "GPS device": "location-crosshairs", "Encrypted phone": "user-lock"}

# icons of the pre-existing types (Font Awesome Free)
BASE_ICONS = {
    "target": "user-secret", "name": "user", "phone": "phone", "email": "envelope",
    "username": "at", "generic": "circle-question", "vehicle": "car", "link": "link",
    "text": "file-lines", "place": "location-dot", "latin": "language", "photo": "image",
    "domain": "globe", "breach": "shield-halved",
}

# field keys of the versions before 2.0 (Italian): accepted on input
FIELD_ALIASES = {
    "categoria": "category", "marca": "make", "modello": "model", "calibro": "calibre",
    "matricola": "serial_number", "matricola_abrasa": "serial_removed", "stato": "status",
    "tipo": "type", "quantita": "quantity", "unita": "unit", "descrizione": "description",
    "sostanza": "substance", "purezza": "purity", "confezionamento": "packaging",
    "importo": "amount", "valuta": "currency", "tagli": "denominations", "seriali": "serial_numbers",
    "false": "counterfeit", "banca": "bank", "numero": "number", "data": "date", "traente": "drawer",
    "beneficiario": "payee", "valore": "estimated_value", "seriale": "serial_number",
    "intestatario": "holder", "circuito": "network", "scadenza": "expiry", "indirizzo": "address",
    "paese": "country", "rilascio": "issue_date", "falso": "forged", "emittente": "issuer",
    "destinatario": "recipient", "autorita": "authority", "procedimento": "case_number",
    "redattore": "author", "nome": "name", "piva": "tax_number", "sede": "registered_office",
    "luogo": "place", "comune": "town", "catasto": "land_registry", "quando": "time",
    "azimut": "azimuth", "elevazione": "elevation", "confidenza": "confidence",
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
    return ntype == "weapon" and key == "serial_number"


def _option_names():
    """{folded name in any interface language: English option}."""
    from . import ontology_i18n
    out = {}
    for en, tr in ontology_i18n.ROWS.items():
        for name in tr:
            out.setdefault(_fold(name), en.split(":", 1)[-1])
    return out


_OPTIONS = None


def _option(options, v):
    """The English option written as v (in English or in an interface language)."""
    global _OPTIONS
    hit = next((o for o in options if _fold(o) == _fold(v)), None)
    if hit:
        return hit
    if _OPTIONS is None:
        _OPTIONS = _option_names()
    en = _OPTIONS.get(_fold(v))
    return en if en in options else None


def clean_fields(ntype, raw):
    """Only the fields defined by the type, cleaned up. Options outside the list
    are kept (the user or the AI may write an unlisted value)."""
    spec = TYPES[ntype]
    out = {}
    raw = raw if isinstance(raw, dict) else {}
    keys = {f["key"] for f in spec["fields"]}
    raw = {(k if k in keys else FIELD_ALIASES.get(k, k)): v for k, v in raw.items()}
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
            out["serial_removed"] = True                      # "abrasa", "removed"...
            continue
        if f["type"] == "select" and f["options"]:
            v = _option(f["options"], v) or v
        out[f["key"]] = v
    return out


def _fmt_num(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return str(v)
    if x == int(x):
        return f"{int(x):,}"
    return f"{x:,.2f}".rstrip("0")                   # 1.50 -> 1.5


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
_WORD_KEYS = {"make", "bank", "type", "town", "name", "blockchain"}


def ident_of(ntype, fields):
    """Identity key ('' = exhibit with no identifier: new node)."""
    spec = TYPES[ntype]
    norm = spec.get("norm", {})
    need = spec.get("ident_min") or spec.get("ident") or []
    if not need:
        return ""
    if fields.get("serial_removed") and ntype == "weapon":
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


# person nodes: colour icon by sex (scripts/icons/mapping.json); not known = the
# icon of the type
PERSON_ICONS = {"male": "person-male", "female": "person-female"}


def icon_of(ntype, fields):
    if ntype == "drug":
        return DRUG_ICONS.get(fields.get("substance"), TYPES[ntype]["icon"])
    if ntype == "document":
        return DOC_ICONS.get(fields.get("type"), TYPES[ntype]["icon"])
    if ntype == "findoc":
        return FINDOC_ICONS.get(fields.get("type"), TYPES[ntype]["icon"])
    if ntype == "legaldoc":
        return LEGALDOC_ICONS.get(fields.get("type"), TYPES[ntype]["icon"])
    if ntype == "device":
        return DEVICE_ICONS.get(fields.get("type"), TYPES[ntype]["icon"])
    return TYPES[ntype]["icon"] if ntype in TYPES else BASE_ICONS.get(ntype, "circle-question")


def raw_of(ntype, fields):
    """Readable fields for the card: {'Category': 'Revolver', ...}; the interface
    translates the labels and the options (ontology_i18n)."""
    out = {}
    for f in TYPES[ntype]["fields"]:
        v = fields.get(f["key"])
        if v in (None, "", False):
            continue
        out[f["label"]] = "yes" if v is True else v
    return out


def ai_rules():
    """Instructions for the AI prompt (one line per type, with the lists)."""
    lines = ["  For select fields write the English option whose meaning best matches the TEXT, "
             "whatever the language of the TEXT (e.g. \"traffico di stupefacenti\" -> \"Drug trafficking\", "
             "not \"Drug dealing\").",
             "  Link labels for items: seized items linked from the person with \"seized\" "
             "(or \"holds\", \"owns\", \"uses\", \"holder\" when the TEXT says so); "
             "the person linked to an offence with \"suspect\" / \"arrested\" / \"victim\"; "
             "seized items linked to the offence/event with \"seized in\"."]
    for t, spec in TYPES.items():
        lines.append(f"- {spec['ai']}")
        for f in spec["fields"]:
            if f["type"] == "select" and len(f["options"]) > 2:
                lines.append(f"    {f['key']} options: " + "; ".join(f["options"]))
    return "\n".join(lines)


def public():
    """Configuration for the client (entry form, icons, colours)."""
    return {t: {"label": s["label"], "group": s["group"], "icon": s["icon"],
                "color": s["color"], "fields": s["fields"], "order": i}
            for i, (t, s) in enumerate(TYPES.items())}
