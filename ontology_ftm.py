# -*- coding: utf-8 -*-
# Generato da scripts/ftm/make_ftm_types.py: tipi Follow the Money senza
# equivalente in OsintGraph (ontology.TYPES.update(FTM_TYPES)) e le loro
# traduzioni (ontology_i18n.ROWS). Non modificare a mano: rigenerare.
# "Nihil est ab omni parte beatum." (Horace, Odes)
# Nothing is blessed in every respect.
FTM_TYPES = {
 "airplane": {
  "label": "Aeromobile",
  "en": "Airplane",
  "group": "FtM · Beni e mezzi",
  "icon": "car",
  "color": "#4338ca",
  "fields": [
   {
    "key": "type",
    "label": "Tipo",
    "en": "Type",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "registrationNumber",
    "label": "Numero di registrazione",
    "en": "Registration number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "amount",
    "label": "Importo",
    "en": "Amount",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "currency",
    "label": "Valuta",
    "en": "Currency",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "amountUsd",
    "label": "Importo in USD",
    "en": "Amount in USD",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "amountEur",
    "label": "Importo in EUR",
    "en": "Amount in EUR",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "model",
    "label": "Modello",
    "en": "Model",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "buildDate",
    "label": "Data di costruzione",
    "en": "Build Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "registrationDate",
    "label": "Data di registrazione",
    "en": "Registration Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "deregistrationDate",
    "label": "Data di cancellazione",
    "en": "De-registration Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "serialNumber",
    "label": "Numero di serie",
    "en": "Serial Number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "icaoCode",
    "label": "Designatore ICAO del tipo",
    "en": "ICAO aircraft type designator",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "manufacturer",
    "label": "Costruttore",
    "en": "Manufacturer",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "registrationNumber"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "name",
   "registrationNumber"
  ],
  "value": "name",
  "ai": "airplane: An airplane, helicopter or other flying vehicle. fields: type, registrationNumber, country, amount, currency, amountUsd, amountEur, name.",
  "ftm": "Airplane"
 },
 "article": {
  "label": "Articolo",
  "en": "Article",
  "group": "FtM · Documenti",
  "icon": "file-lines",
  "color": "#475569",
  "fields": [
   {
    "key": "title",
    "label": "Titolo",
    "en": "Title",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "author",
    "label": "Autore",
    "en": "Author",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "publishedAt",
    "label": "Pubblicato il",
    "en": "Published on",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "fileSize",
    "label": "Dimensione del file",
    "en": "File size",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "fileName",
    "label": "Nome del file",
    "en": "File name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "messageId",
    "label": "Id messaggio",
    "en": "Message ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "mimeType",
    "label": "Tipo MIME",
    "en": "MIME type",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "language",
    "label": "Lingua",
    "en": "Language",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "date",
    "label": "Data",
    "en": "Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "authoredAt",
    "label": "Scritto il",
    "en": "Authored on",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "title"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "title",
   "fileName"
  ],
  "value": "title",
  "ai": "article: A piece of media reporting about a subject. fields: title, author, publishedAt, name, country, address, fileSize, fileName.",
  "ftm": "Article"
 },
 "asset": {
  "label": "Bene",
  "en": "Asset",
  "group": "FtM · Finanza",
  "icon": "gem",
  "color": "#0f766e",
  "fields": [
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "amount",
    "label": "Importo",
    "en": "Amount",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "currency",
    "label": "Valuta",
    "en": "Currency",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "amountUsd",
    "label": "Importo in USD",
    "en": "Amount in USD",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "amountEur",
    "label": "Importo in EUR",
    "en": "Amount in EUR",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "name"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "name"
  ],
  "value": "name",
  "ai": "asset: A piece of property which can be owned and assigned a monetary value. fields: name, amount, currency, amountUsd, amountEur, country, address.",
  "ftm": "Asset"
 },
 "audio": {
  "label": "Audio",
  "en": "Audio",
  "group": "FtM · Documenti",
  "icon": "image",
  "color": "#475569",
  "fields": [
   {
    "key": "title",
    "label": "Titolo",
    "en": "Title",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "fileName",
    "label": "Nome del file",
    "en": "File name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "mimeType",
    "label": "Tipo MIME",
    "en": "MIME type",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "author",
    "label": "Autore",
    "en": "Author",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "fileSize",
    "label": "Dimensione del file",
    "en": "File size",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "messageId",
    "label": "Id messaggio",
    "en": "Message ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "language",
    "label": "Lingua",
    "en": "Language",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "date",
    "label": "Data",
    "en": "Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "authoredAt",
    "label": "Scritto il",
    "en": "Authored on",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "publishedAt",
    "label": "Pubblicato il",
    "en": "Published on",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "duration",
    "label": "Durata",
    "en": "Duration",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "samplingRate",
    "label": "Frequenza di campionamento",
    "en": "Sampling Rate",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "fileName"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "fileName",
   "title"
  ],
  "value": "fileName",
  "ai": "audio:  fields: title, fileName, mimeType, name, country, address, author, fileSize.",
  "ftm": "Audio"
 },
 "ftmbankaccount": {
  "label": "Conto bancario",
  "en": "Bank account",
  "group": "FtM · Finanza",
  "icon": "money-check",
  "color": "#0f766e",
  "fields": [
   {
    "key": "accountNumber",
    "label": "Numero di conto",
    "en": "Account number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "bankName",
    "label": "Nome della banca",
    "en": "Bank name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "amount",
    "label": "Importo",
    "en": "Amount",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "currency",
    "label": "Valuta",
    "en": "Currency",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "amountUsd",
    "label": "Importo in USD",
    "en": "Amount in USD",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "amountEur",
    "label": "Importo in EUR",
    "en": "Amount in EUR",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "iban",
    "label": "IBAN",
    "en": "IBAN",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "bic",
    "label": "Codice identificativo banca (BIC)",
    "en": "Bank Identifier Code",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "accountType",
    "label": "Tipo di conto",
    "en": "Account type",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "openingDate",
    "label": "Data di apertura",
    "en": "Opening date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "closingDate",
    "label": "Data di chiusura",
    "en": "Closing date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "balance",
    "label": "Saldo",
    "en": "Balance",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "balanceDate",
    "label": "Data del saldo",
    "en": "Balance date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "maxBalance",
    "label": "Saldo massimo",
    "en": "Maximum balance",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "maxBalanceDate",
    "label": "Data del saldo massimo",
    "en": "Maximum balance date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "bankAddress",
    "label": "Indirizzo della banca",
    "en": "Bank address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "iban"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "name",
   "iban",
   "accountNumber"
  ],
  "value": "name",
  "ai": "ftmbankaccount: An account held at a bank and controlled by an owner. This may also be used to describe more complex arrangements like correspondent bank settlement accounts. fields: accountNumber, bankName, amount, currency, amountUsd, amountEur, name, country.",
  "ftm": "BankAccount"
 },
 "call": {
  "label": "Chiamata telefonica",
  "en": "Call",
  "group": "FtM · Procedimenti",
  "icon": "phone",
  "color": "#831843",
  "fields": [
   {
    "key": "callerNumber",
    "label": "Numero chiamante",
    "en": "Caller's Number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "receiverNumber",
    "label": "Numero chiamato",
    "en": "Receiver's Number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "date",
    "label": "Data",
    "en": "Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "startDate",
    "label": "Data di inizio",
    "en": "Start date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "endDate",
    "label": "Data di fine",
    "en": "End date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "recordId",
    "label": "Id record",
    "en": "Record ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "duration",
    "label": "Durata",
    "en": "Duration",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "date"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "callerNumber",
   "receiverNumber"
  ],
  "value": "callerNumber",
  "ai": "call:  fields: callerNumber, receiverNumber, date, startDate, endDate, recordId, duration.",
  "ftm": "Call"
 },
 "callfortenders": {
  "label": "Bando di gara",
  "en": "Call for tenders",
  "group": "FtM · Finanza",
  "icon": "file-contract",
  "color": "#0f766e",
  "fields": [
   {
    "key": "title",
    "label": "Titolo",
    "en": "Title",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "startDate",
    "label": "Data di inizio",
    "en": "Start date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "endDate",
    "label": "Data di fine",
    "en": "End date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "date",
    "label": "Data",
    "en": "Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "recordId",
    "label": "Id record",
    "en": "Record ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "callId",
    "label": "Id univoco del bando",
    "en": "CfT unique id",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "authorityReferenceId",
    "label": "Riferimento stazione appaltante",
    "en": "Contracting authority reference ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "publicationDate",
    "label": "Data di pubblicazione / invito",
    "en": "Date of publication/invitation",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "evaluationMechanism",
    "label": "Criterio di valutazione",
    "en": "Evaluation mechanism",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "procurementType",
    "label": "Tipo di appalto",
    "en": "Procurement type",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "directive",
    "label": "Direttiva",
    "en": "Directive",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "procedure",
    "label": "Procedura",
    "en": "Procedure",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "involvesOutcome",
    "label": "Esito del bando",
    "en": "Call for tenders result",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "cpvCode",
    "label": "Codice CPV",
    "en": "CPV code",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "reverseAuctionsIncluded",
    "label": "Aste elettroniche previste",
    "en": "Inclusion of e-Auctions",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "nutsCode",
    "label": "Codice NUTS",
    "en": "NUTS code",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "relationToThreshold",
    "label": "Sopra o sotto soglia",
    "en": "Above or below threshold",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "paymentOptions",
    "label": "Modalità di pagamento",
    "en": "Payment options",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "submissionDeadline",
    "label": "Termine di presentazione",
    "en": "Submission deadline",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "clarificationDeadline",
    "label": "Fine periodo chiarimenti",
    "en": "End of clarification period",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "awardedInLots",
    "label": "Contratto aggiudicato a lotti",
    "en": "Contract awarded in Lots",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "numberOfLots",
    "label": "Numero di lotti",
    "en": "Number of lots",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "lotsNames",
    "label": "Nomi dei lotti",
    "en": "Lots names",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "tendersForLots",
    "label": "Offerte per lotto",
    "en": "Tenders for lots",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "maximumNumberOfLots",
    "label": "Numero massimo di lotti",
    "en": "Maximum number of lots",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "euFunding",
    "label": "Finanziamento UE",
    "en": "EU funding",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "multipleTenders",
    "label": "Offerte multiple ammesse",
    "en": "Multiple tenders will be accepted",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "tedUrl",
    "label": "Link TED agli avvisi pubblicati",
    "en": "TED link for published notices",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "fallsUnderGPPScope",
    "label": "Rientra nel GPP (appalti pubblici)?",
    "en": "Does this call fall under the scope of GPP?",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "certificationCheck",
    "label": "Verifica certificazione",
    "en": "Certification check",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "awardingDate",
    "label": "Data di aggiudicazione",
    "en": "Date of awarding",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "contractNoticeDate",
    "label": "Data avviso di gara",
    "en": "Contract notice date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "awardNoticeDate",
    "label": "Data avviso di aggiudicazione",
    "en": "Award Notice Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "title"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "title"
  ],
  "value": "title",
  "ai": "callfortenders: A public appeal issued by an authority, possibly on behalf of another, for buying a specific work, supply or service. fields: title, startDate, endDate, date, recordId, name, country, address.",
  "ftm": "CallForTenders"
 },
 "company": {
  "label": "Società",
  "en": "Company",
  "group": "FtM · Soggetti",
  "icon": "building",
  "color": "#7c2d12",
  "fields": [
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "jurisdiction",
    "label": "Giurisdizione",
    "en": "Jurisdiction",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "registrationNumber",
    "label": "Numero di registrazione",
    "en": "Registration number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "incorporationDate",
    "label": "Data di costituzione",
    "en": "Incorporation date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "amount",
    "label": "Importo",
    "en": "Amount",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "currency",
    "label": "Valuta",
    "en": "Currency",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "amountUsd",
    "label": "Importo in USD",
    "en": "Amount in USD",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "amountEur",
    "label": "Importo in EUR",
    "en": "Amount in EUR",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "abbreviation",
    "label": "Abbreviazione",
    "en": "Abbreviation",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "email",
    "label": "Email",
    "en": "Email",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "phone",
    "label": "Telefono",
    "en": "Phone",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "website",
    "label": "Sito web",
    "en": "Website",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "legalForm",
    "label": "Forma giuridica",
    "en": "Legal form",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "dissolutionDate",
    "label": "Data di scioglimento",
    "en": "Dissolution date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "taxStatus",
    "label": "Stato fiscale",
    "en": "Tax status",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "status",
    "label": "Stato",
    "en": "Status",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "sector",
    "label": "Settore",
    "en": "Sector",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "classification",
    "label": "Classificazione",
    "en": "Classification",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "idNumber",
    "label": "Numero identificativo",
    "en": "ID Number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "taxNumber",
    "label": "Codice fiscale",
    "en": "Tax Number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "licenseNumber",
    "label": "Numero di licenza",
    "en": "License Number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "vatCode",
    "label": "Partita IVA",
    "en": "V.A.T. Identifier",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "mainCountry",
    "label": "Paese di origine",
    "en": "Country of origin",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "opencorporatesUrl",
    "label": "URL OpenCorporates",
    "en": "OpenCorporates URL",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "bvdId",
    "label": "Id Bureau van Dijk",
    "en": "Bureau van Dijk ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "sayariId",
    "label": "Id Sayari",
    "en": "Sayari Entity ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "brightQueryId",
    "label": "Id BrightQuery",
    "en": "BrightQuery ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "uscCode",
    "label": "USCC",
    "en": "USCC",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "icijId",
    "label": "Id ICIJ",
    "en": "ICIJ ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "okpoCode",
    "label": "OKPO",
    "en": "OKPO",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "innCode",
    "label": "INN (codice fiscale russo)",
    "en": "INN",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ogrnCode",
    "label": "OGRN",
    "en": "OGRN",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "okvedCode",
    "label": "OKVED",
    "en": "OKVED",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "leiCode",
    "label": "LEI",
    "en": "LEI",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "dunsCode",
    "label": "Numero DUNS",
    "en": "DUNS",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "uniqueEntityId",
    "label": "Id entità univoco",
    "en": "Unique Entity ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "npiCode",
    "label": "NPI",
    "en": "NPI",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "swiftBic",
    "label": "SWIFT/BIC",
    "en": "SWIFT/BIC",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "cageCode",
    "label": "Codice CAGE",
    "en": "CAGE",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "permId",
    "label": "PermID",
    "en": "PermID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "imoNumber",
    "label": "Numero IMO",
    "en": "IMO Number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "giiNumber",
    "label": "GIIN",
    "en": "GIIN",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "capital",
    "label": "Capitale",
    "en": "Capital",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "voenCode",
    "label": "VOEN",
    "en": "VOEN",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "coatoCode",
    "label": "Codice territoriale COATO / SOATO / OKATO",
    "en": "COATO / SOATO / OKATO",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "irsCode",
    "label": "Numero IRS",
    "en": "IRS Number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ipoCode",
    "label": "IPO",
    "en": "IPO",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "cikCode",
    "label": "Chiave SEC (CIK)",
    "en": "SEC Central Index Key",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "jibCode",
    "label": "JIB",
    "en": "JIB",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "mbsCode",
    "label": "MBS",
    "en": "MBS",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "caemCode",
    "label": "Codice CAEM",
    "en": "COD CAEM",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "kppCode",
    "label": "KPP",
    "en": "KPP",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "okopfCode",
    "label": "OKOPF",
    "en": "OKOPF",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "fnsCode",
    "label": "Codice del servizio fiscale federale",
    "en": "Federal tax service code",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "fssCode",
    "label": "Codice FSS",
    "en": "FSS",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "bikCode",
    "label": "BIK (codice banca russo)",
    "en": "BIK",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "pfrNumber",
    "label": "Numero PFR",
    "en": "PFR Number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "oksmCode",
    "label": "OKSM",
    "en": "OKSM",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ticker",
    "label": "Ticker di borsa",
    "en": "Stock ticker symbol",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ricCode",
    "label": "Codice strumento Reuters (RIC)",
    "en": "Reuters Instrument Code",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "name"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "name",
   "abbreviation",
   "registrationNumber"
  ],
  "value": "name",
  "ai": "company: A corporation, usually for profit. Does not distinguish between private and public companies, and can also be used to model more specific constructs like trusts fields: name, jurisdiction, registrationNumber, incorporationDate, amount, currency, amountUsd, amountEur.",
  "ftm": "Company"
 },
 "contract": {
  "label": "Contratto",
  "en": "Contract",
  "group": "FtM · Finanza",
  "icon": "file-contract",
  "color": "#0f766e",
  "fields": [
   {
    "key": "title",
    "label": "Titolo",
    "en": "Title",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "amount",
    "label": "Importo",
    "en": "Amount",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "contractDate",
    "label": "Data del contratto",
    "en": "Contract date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "currency",
    "label": "Valuta",
    "en": "Currency",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "amountUsd",
    "label": "Importo in USD",
    "en": "Amount in USD",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "amountEur",
    "label": "Importo in EUR",
    "en": "Amount in EUR",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "type",
    "label": "Tipo",
    "en": "Type",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "procedureNumber",
    "label": "Numero della procedura",
    "en": "Procedure number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "procedure",
    "label": "Procedura contrattuale",
    "en": "Contract procedure",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "noticeId",
    "label": "Id avviso di aggiudicazione",
    "en": "Contract Award Notice ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "numberAwards",
    "label": "Numero di aggiudicazioni",
    "en": "Number of awards",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "status",
    "label": "Stato",
    "en": "Status",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "method",
    "label": "Metodo di appalto",
    "en": "Procurement method",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "criteria",
    "label": "Criteri di aggiudicazione",
    "en": "Contract award criteria",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "classification",
    "label": "Classificazione",
    "en": "Classification",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "cancelled",
    "label": "Annullato?",
    "en": "Cancelled?",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "language",
    "label": "Lingua",
    "en": "Language",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "name"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "title",
   "name",
   "procedureNumber"
  ],
  "value": "title",
  "ai": "contract: A contract or contract lot issued by an authority. Multiple lots may be awarded to different suppliers (see `ContractAward`). fields: title, amount, contractDate, currency, amountUsd, amountEur, name, country.",
  "ftm": "Contract"
 },
 "courtcase": {
  "label": "Procedimento giudiziario",
  "en": "Court case",
  "group": "FtM · Procedimenti",
  "icon": "scale-balanced",
  "color": "#831843",
  "fields": [
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "fileDate",
    "label": "Data di deposito",
    "en": "File date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "caseNumber",
    "label": "Numero del procedimento",
    "en": "Case number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "category",
    "label": "Categoria",
    "en": "Category",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "type",
    "label": "Tipo",
    "en": "Type",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "status",
    "label": "Stato",
    "en": "Status",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "court",
    "label": "Tribunale",
    "en": "Court",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "closeDate",
    "label": "Data di chiusura",
    "en": "Close date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "caseNumber"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "name",
   "caseNumber"
  ],
  "value": "name",
  "ai": "courtcase:  fields: name, fileDate, caseNumber, country, address, category, type, status.",
  "ftm": "CourtCase"
 },
 "cryptowallet": {
  "label": "Wallet di criptovalute",
  "en": "Cryptocurrency wallet",
  "group": "FtM · Finanza",
  "icon": "bitcoin",
  "color": "#0f766e",
  "fields": [
   {
    "key": "currency",
    "label": "Valuta",
    "en": "Currency",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "publicKey",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "amount",
    "label": "Importo",
    "en": "Amount",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "amountUsd",
    "label": "Importo in USD",
    "en": "Amount in USD",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "amountEur",
    "label": "Importo in EUR",
    "en": "Amount in EUR",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "cryptoAddress",
    "label": "Indirizzo crypto",
    "en": "Crypto address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "privateKey",
    "label": "Chiave privata",
    "en": "Private key",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "accountId",
    "label": "Id conto",
    "en": "Account ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "creationDate",
    "label": "Data di creazione",
    "en": "Creation date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "currencySymbol",
    "label": "Codice valuta",
    "en": "Currency short code",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "blockchain",
    "label": "Blockchain",
    "en": "Blockchain",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "managingExchange",
    "label": "Borsa di quotazione",
    "en": "Managing exchange",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "balance",
    "label": "Saldo",
    "en": "Balance",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "balanceDate",
    "label": "Data del saldo",
    "en": "Balance date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "custodyType",
    "label": "Tipo di custodia",
    "en": "Custody type",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "publicKey"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "publicKey",
   "name"
  ],
  "value": "publicKey",
  "ai": "cryptowallet: A cryptocurrency wallet is a view on the transactions conducted by one participant on a blockchain / distributed ledger system. fields: currency, publicKey, amount, amountUsd, amountEur, name, country, address.",
  "ftm": "CryptoWallet"
 },
 "ftmdocument": {
  "label": "File",
  "en": "File",
  "group": "FtM · Documenti",
  "icon": "file-lines",
  "color": "#475569",
  "fields": [
   {
    "key": "title",
    "label": "Titolo",
    "en": "Title",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "fileName",
    "label": "Nome del file",
    "en": "File name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "mimeType",
    "label": "Tipo MIME",
    "en": "MIME type",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "contentHash",
    "label": "Checksum",
    "en": "Checksum",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "author",
    "label": "Autore",
    "en": "Author",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "generator",
    "label": "Generatore",
    "en": "Generator",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "crawler",
    "label": "Crawler",
    "en": "Crawler",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "fileSize",
    "label": "Dimensione del file",
    "en": "File size",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "extension",
    "label": "Estensione",
    "en": "File extension",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "encoding",
    "label": "Codifica del file",
    "en": "File encoding",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "messageId",
    "label": "Id messaggio",
    "en": "Message ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "language",
    "label": "Lingua",
    "en": "Language",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "date",
    "label": "Data",
    "en": "Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "authoredAt",
    "label": "Scritto il",
    "en": "Authored on",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "publishedAt",
    "label": "Pubblicato il",
    "en": "Published on",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "processingAgent",
    "label": "Agente di elaborazione",
    "en": "Processing agent",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "fileName"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "fileName",
   "title"
  ],
  "value": "fileName",
  "ai": "ftmdocument:  fields: title, fileName, mimeType, name, country, address, contentHash, author.",
  "ftm": "Document"
 },
 "economicactivity": {
  "label": "Dichiarazione doganale",
  "en": "Customs declaration",
  "group": "FtM · Finanza",
  "icon": "building",
  "color": "#0f766e",
  "fields": [
   {
    "key": "goodsDescription",
    "label": "Descrizione delle merci",
    "en": "Description of goods",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "startDate",
    "label": "Data di inizio",
    "en": "Start date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "endDate",
    "label": "Data di fine",
    "en": "End date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "date",
    "label": "Data",
    "en": "Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "recordId",
    "label": "Id record",
    "en": "Record ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ccdNumber",
    "label": "Numero dichiarazione doganale",
    "en": "Customs Cargo Declaration Number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ccdValue",
    "label": "Valore dichiarazione doganale",
    "en": "CCD Value",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "directionOfTransportation",
    "label": "Direzione del trasporto",
    "en": "Direction of transportation",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "customsProcedure",
    "label": "Procedura doganale",
    "en": "Customs Procedure",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "vedCode",
    "label": "Codice FEAC",
    "en": "FEAC Code",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "vedCodeDescription",
    "label": "Descrizione codice FEAC",
    "en": "FEAC Code description",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "invoiceAmount",
    "label": "Valore fattura",
    "en": "Invoice Value Amount",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "customsAmount",
    "label": "Valore doganale",
    "en": "Customs Value Amount",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "dollarExchRate",
    "label": "Cambio in USD",
    "en": "USD Exchange Rate",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "tradingCountry",
    "label": "Paese di scambio",
    "en": "Trading Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "departureCountry",
    "label": "Paese di partenza",
    "en": "Country of departure",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "destinationCountry",
    "label": "Paese di destinazione",
    "en": "Country of destination",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "originCountry",
    "label": "Paese di origine",
    "en": "Country of origin",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "ccdNumber"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "goodsDescription",
   "ccdNumber"
  ],
  "value": "goodsDescription",
  "ai": "economicactivity: A foreign economic activity. fields: goodsDescription, startDate, endDate, date, recordId, ccdNumber, ccdValue, directionOfTransportation.",
  "ftm": "EconomicActivity"
 },
 "ftmevent": {
  "label": "Evento",
  "en": "Event",
  "group": "FtM · Procedimenti",
  "icon": "burst",
  "color": "#831843",
  "fields": [
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "summary",
    "label": "Sintesi",
    "en": "Summary",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "date",
    "label": "Data",
    "en": "Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "location",
    "label": "Luogo",
    "en": "Location",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "startDate",
    "label": "Data di inizio",
    "en": "Start date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "endDate",
    "label": "Data di fine",
    "en": "End date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "recordId",
    "label": "Id record",
    "en": "Record ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "important",
    "label": "Importante",
    "en": "Important",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "name"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "name",
   "summary",
   "date"
  ],
  "value": "name",
  "ai": "ftmevent:  fields: name, summary, date, location, country, address, startDate, endDate.",
  "ftm": "Event"
 },
 "folder": {
  "label": "Cartella",
  "en": "Folder",
  "group": "FtM · Documenti",
  "icon": "file-lines",
  "color": "#475569",
  "fields": [
   {
    "key": "title",
    "label": "Titolo",
    "en": "Title",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "author",
    "label": "Autore",
    "en": "Author",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "fileSize",
    "label": "Dimensione del file",
    "en": "File size",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "fileName",
    "label": "Nome del file",
    "en": "File name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "messageId",
    "label": "Id messaggio",
    "en": "Message ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "mimeType",
    "label": "Tipo MIME",
    "en": "MIME type",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "language",
    "label": "Lingua",
    "en": "Language",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "date",
    "label": "Data",
    "en": "Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "authoredAt",
    "label": "Scritto il",
    "en": "Authored on",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "publishedAt",
    "label": "Pubblicato il",
    "en": "Published on",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "fileName"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "fileName",
   "title"
  ],
  "value": "fileName",
  "ai": "folder:  fields: title, name, country, address, author, fileSize, fileName, messageId.",
  "ftm": "Folder"
 },
 "identification": {
  "label": "Identificazione",
  "en": "Identification",
  "group": "FtM · Documenti d'identità",
  "icon": "id-card",
  "color": "#1d4ed8",
  "fields": [
   {
    "key": "number",
    "label": "Numero del documento",
    "en": "Document number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "type",
    "label": "Tipo",
    "en": "Type",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "startDate",
    "label": "Data di inizio",
    "en": "Start date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "endDate",
    "label": "Data di fine",
    "en": "End date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "date",
    "label": "Data",
    "en": "Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "recordId",
    "label": "Id record",
    "en": "Record ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "authority",
    "label": "Autorità",
    "en": "Authority",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "number"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "number"
  ],
  "value": "number",
  "ai": "identification: A form of identification associated with its holder and some issuing country. This can be used for national ID cards, voter enrollments, and similar instruments fields: number, country, type, startDate, endDate, date, recordId, authority.",
  "ftm": "Identification"
 },
 "legalentity": {
  "label": "Soggetto giuridico",
  "en": "Legal entity",
  "group": "FtM · Soggetti",
  "icon": "building",
  "color": "#7c2d12",
  "fields": [
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "legalForm",
    "label": "Forma giuridica",
    "en": "Legal form",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "status",
    "label": "Stato",
    "en": "Status",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "abbreviation",
    "label": "Abbreviazione",
    "en": "Abbreviation",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "email",
    "label": "Email",
    "en": "Email",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "phone",
    "label": "Telefono",
    "en": "Phone",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "website",
    "label": "Sito web",
    "en": "Website",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "incorporationDate",
    "label": "Data di costituzione",
    "en": "Incorporation date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "dissolutionDate",
    "label": "Data di scioglimento",
    "en": "Dissolution date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "taxStatus",
    "label": "Stato fiscale",
    "en": "Tax status",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "sector",
    "label": "Settore",
    "en": "Sector",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "classification",
    "label": "Classificazione",
    "en": "Classification",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "registrationNumber",
    "label": "Numero di registrazione",
    "en": "Registration number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "idNumber",
    "label": "Numero identificativo",
    "en": "ID Number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "taxNumber",
    "label": "Codice fiscale",
    "en": "Tax Number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "licenseNumber",
    "label": "Numero di licenza",
    "en": "License Number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "vatCode",
    "label": "Partita IVA",
    "en": "V.A.T. Identifier",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "jurisdiction",
    "label": "Giurisdizione",
    "en": "Jurisdiction",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "mainCountry",
    "label": "Paese di origine",
    "en": "Country of origin",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "opencorporatesUrl",
    "label": "URL OpenCorporates",
    "en": "OpenCorporates URL",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "bvdId",
    "label": "Id Bureau van Dijk",
    "en": "Bureau van Dijk ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "sayariId",
    "label": "Id Sayari",
    "en": "Sayari Entity ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "brightQueryId",
    "label": "Id BrightQuery",
    "en": "BrightQuery ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "uscCode",
    "label": "USCC",
    "en": "USCC",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "icijId",
    "label": "Id ICIJ",
    "en": "ICIJ ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "okpoCode",
    "label": "OKPO",
    "en": "OKPO",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "innCode",
    "label": "INN (codice fiscale russo)",
    "en": "INN",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ogrnCode",
    "label": "OGRN",
    "en": "OGRN",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "okvedCode",
    "label": "OKVED",
    "en": "OKVED",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "leiCode",
    "label": "LEI",
    "en": "LEI",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "dunsCode",
    "label": "Numero DUNS",
    "en": "DUNS",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "uniqueEntityId",
    "label": "Id entità univoco",
    "en": "Unique Entity ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "npiCode",
    "label": "NPI",
    "en": "NPI",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "swiftBic",
    "label": "SWIFT/BIC",
    "en": "SWIFT/BIC",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "name"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "name",
   "abbreviation",
   "email"
  ],
  "value": "name",
  "ai": "legalentity: Any party to legal proceedings, such as asset ownership, corporate governance or social interactions. Often used when raw data does not specify if something is  fields: name, country, legalForm, status, address, abbreviation, email, phone.",
  "ftm": "LegalEntity"
 },
 "license": {
  "label": "Licenza",
  "en": "License",
  "group": "FtM · Finanza",
  "icon": "file-contract",
  "color": "#0f766e",
  "fields": [
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "amount",
    "label": "Importo",
    "en": "Amount",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "contractDate",
    "label": "Data del contratto",
    "en": "Contract date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "commodities",
    "label": "Merci",
    "en": "Commodities",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "currency",
    "label": "Valuta",
    "en": "Currency",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "amountUsd",
    "label": "Importo in USD",
    "en": "Amount in USD",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "amountEur",
    "label": "Importo in EUR",
    "en": "Amount in EUR",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "title",
    "label": "Titolo",
    "en": "Title",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "type",
    "label": "Tipo",
    "en": "Type",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "procedureNumber",
    "label": "Numero della procedura",
    "en": "Procedure number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "procedure",
    "label": "Procedura contrattuale",
    "en": "Contract procedure",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "noticeId",
    "label": "Id avviso di aggiudicazione",
    "en": "Contract Award Notice ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "numberAwards",
    "label": "Numero di aggiudicazioni",
    "en": "Number of awards",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "status",
    "label": "Stato",
    "en": "Status",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "method",
    "label": "Metodo di appalto",
    "en": "Procurement method",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "criteria",
    "label": "Criteri di aggiudicazione",
    "en": "Contract award criteria",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "classification",
    "label": "Classificazione",
    "en": "Classification",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "cancelled",
    "label": "Annullato?",
    "en": "Cancelled?",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "language",
    "label": "Lingua",
    "en": "Language",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "area",
    "label": "Area",
    "en": "Area",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "reviewDate",
    "label": "Data di revisione della licenza",
    "en": "License review date",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "name"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "name"
  ],
  "value": "name",
  "ai": "license: A grant of land, rights or property. A type of `Contract`. fields: name, amount, contractDate, commodities, currency, amountUsd, amountEur, country.",
  "ftm": "License"
 },
 "mention": {
  "label": "Menzione",
  "en": "Mention",
  "group": "FtM · Documenti",
  "icon": "link",
  "color": "#475569",
  "fields": [
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "name"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "name"
  ],
  "value": "name",
  "ai": "mention:  fields: name.",
  "ftm": "Mention"
 },
 "message": {
  "label": "Messaggio",
  "en": "Message",
  "group": "FtM · Documenti",
  "icon": "envelope",
  "color": "#475569",
  "fields": [
   {
    "key": "subject",
    "label": "Oggetto",
    "en": "Subject",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "date",
    "label": "Data",
    "en": "Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "title",
    "label": "Titolo",
    "en": "Title",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "author",
    "label": "Autore",
    "en": "Author",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "fileSize",
    "label": "Dimensione del file",
    "en": "File size",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "fileName",
    "label": "Nome del file",
    "en": "File name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "messageId",
    "label": "Id messaggio",
    "en": "Message ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "mimeType",
    "label": "Tipo MIME",
    "en": "MIME type",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "language",
    "label": "Lingua",
    "en": "Language",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "authoredAt",
    "label": "Scritto il",
    "en": "Authored on",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "publishedAt",
    "label": "Pubblicato il",
    "en": "Published on",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "startDate",
    "label": "Data di inizio",
    "en": "Start date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "endDate",
    "label": "Data di fine",
    "en": "End date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "recordId",
    "label": "Id record",
    "en": "Record ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "threadTopic",
    "label": "Argomento della discussione",
    "en": "Thread topic",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "subject"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "subject",
   "title",
   "threadTopic"
  ],
  "value": "subject",
  "ai": "message:  fields: subject, date, name, country, address, title, author, fileSize.",
  "ftm": "Message"
 },
 "ftmorganization": {
  "label": "Organizzazione",
  "en": "Organization",
  "group": "FtM · Soggetti",
  "icon": "building",
  "color": "#7c2d12",
  "fields": [
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "legalForm",
    "label": "Forma giuridica",
    "en": "Legal form",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "status",
    "label": "Stato",
    "en": "Status",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "abbreviation",
    "label": "Abbreviazione",
    "en": "Abbreviation",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "email",
    "label": "Email",
    "en": "Email",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "phone",
    "label": "Telefono",
    "en": "Phone",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "website",
    "label": "Sito web",
    "en": "Website",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "incorporationDate",
    "label": "Data di costituzione",
    "en": "Incorporation date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "dissolutionDate",
    "label": "Data di scioglimento",
    "en": "Dissolution date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "taxStatus",
    "label": "Stato fiscale",
    "en": "Tax status",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "sector",
    "label": "Settore",
    "en": "Sector",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "classification",
    "label": "Classificazione",
    "en": "Classification",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "registrationNumber",
    "label": "Numero di registrazione",
    "en": "Registration number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "idNumber",
    "label": "Numero identificativo",
    "en": "ID Number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "taxNumber",
    "label": "Codice fiscale",
    "en": "Tax Number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "licenseNumber",
    "label": "Numero di licenza",
    "en": "License Number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "vatCode",
    "label": "Partita IVA",
    "en": "V.A.T. Identifier",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "jurisdiction",
    "label": "Giurisdizione",
    "en": "Jurisdiction",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "mainCountry",
    "label": "Paese di origine",
    "en": "Country of origin",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "opencorporatesUrl",
    "label": "URL OpenCorporates",
    "en": "OpenCorporates URL",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "bvdId",
    "label": "Id Bureau van Dijk",
    "en": "Bureau van Dijk ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "sayariId",
    "label": "Id Sayari",
    "en": "Sayari Entity ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "brightQueryId",
    "label": "Id BrightQuery",
    "en": "BrightQuery ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "uscCode",
    "label": "USCC",
    "en": "USCC",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "icijId",
    "label": "Id ICIJ",
    "en": "ICIJ ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "okpoCode",
    "label": "OKPO",
    "en": "OKPO",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "innCode",
    "label": "INN (codice fiscale russo)",
    "en": "INN",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ogrnCode",
    "label": "OGRN",
    "en": "OGRN",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "okvedCode",
    "label": "OKVED",
    "en": "OKVED",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "leiCode",
    "label": "LEI",
    "en": "LEI",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "dunsCode",
    "label": "Numero DUNS",
    "en": "DUNS",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "uniqueEntityId",
    "label": "Id entità univoco",
    "en": "Unique Entity ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "npiCode",
    "label": "NPI",
    "en": "NPI",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "swiftBic",
    "label": "SWIFT/BIC",
    "en": "SWIFT/BIC",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "cageCode",
    "label": "Codice CAGE",
    "en": "CAGE",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "permId",
    "label": "PermID",
    "en": "PermID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "imoNumber",
    "label": "Numero IMO",
    "en": "IMO Number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "giiNumber",
    "label": "GIIN",
    "en": "GIIN",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "name"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "name",
   "abbreviation",
   "registrationNumber"
  ],
  "value": "name",
  "ai": "ftmorganization: Any type of incorporated entity that cannot be owned by another (see `Company`). This might include charities, foundations or state-owned enterprises, depending fields: name, country, legalForm, status, address, abbreviation, email, phone.",
  "ftm": "Organization"
 },
 "package": {
  "label": "Pacchetto",
  "en": "Package",
  "group": "FtM · Documenti",
  "icon": "file-lines",
  "color": "#475569",
  "fields": [
   {
    "key": "title",
    "label": "Titolo",
    "en": "Title",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "fileName",
    "label": "Nome del file",
    "en": "File name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "mimeType",
    "label": "Tipo MIME",
    "en": "MIME type",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "author",
    "label": "Autore",
    "en": "Author",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "fileSize",
    "label": "Dimensione del file",
    "en": "File size",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "messageId",
    "label": "Id messaggio",
    "en": "Message ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "language",
    "label": "Lingua",
    "en": "Language",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "date",
    "label": "Data",
    "en": "Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "authoredAt",
    "label": "Scritto il",
    "en": "Authored on",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "publishedAt",
    "label": "Pubblicato il",
    "en": "Published on",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "fileName"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "fileName",
   "title"
  ],
  "value": "fileName",
  "ai": "package: A bundle of files that have been packaged together into some form of archive. fields: title, fileName, mimeType, name, country, address, author, fileSize.",
  "ftm": "Package"
 },
 "page": {
  "label": "Pagina",
  "en": "Page",
  "group": "FtM · Documenti",
  "icon": "file-lines",
  "color": "#475569",
  "fields": [
   {
    "key": "index",
    "label": "Indice",
    "en": "Index",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "index"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "index"
  ],
  "value": "index",
  "ai": "page:  fields: index.",
  "ftm": "Page"
 },
 "pages": {
  "label": "Documento",
  "en": "Document",
  "group": "FtM · Documenti",
  "icon": "file-lines",
  "color": "#475569",
  "fields": [
   {
    "key": "title",
    "label": "Titolo",
    "en": "Title",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "fileName",
    "label": "Nome del file",
    "en": "File name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "mimeType",
    "label": "Tipo MIME",
    "en": "MIME type",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "author",
    "label": "Autore",
    "en": "Author",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "fileSize",
    "label": "Dimensione del file",
    "en": "File size",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "messageId",
    "label": "Id messaggio",
    "en": "Message ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "language",
    "label": "Lingua",
    "en": "Language",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "date",
    "label": "Data",
    "en": "Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "authoredAt",
    "label": "Scritto il",
    "en": "Authored on",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "publishedAt",
    "label": "Pubblicato il",
    "en": "Published on",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "fileName"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "fileName",
   "title"
  ],
  "value": "fileName",
  "ai": "pages: A multi-page document, such as a PDF or Word file or slide-show presentation. fields: title, fileName, mimeType, name, country, address, author, fileSize.",
  "ftm": "Pages"
 },
 "passport": {
  "label": "Passaporto",
  "en": "Passport",
  "group": "FtM · Documenti d'identità",
  "icon": "passport",
  "color": "#1d4ed8",
  "fields": [
   {
    "key": "number",
    "label": "Numero del documento",
    "en": "Document number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "type",
    "label": "Tipo",
    "en": "Type",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "startDate",
    "label": "Data di inizio",
    "en": "Start date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "endDate",
    "label": "Data di fine",
    "en": "End date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "date",
    "label": "Data",
    "en": "Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "recordId",
    "label": "Id record",
    "en": "Record ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "authority",
    "label": "Autorità",
    "en": "Authority",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "birthDate",
    "label": "Data di nascita",
    "en": "Birth date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "birthPlace",
    "label": "Luogo di nascita",
    "en": "Place of birth",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "gender",
    "label": "Sesso",
    "en": "Gender",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "personalNumber",
    "label": "Numero personale",
    "en": "Personal number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "number"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "number"
  ],
  "value": "number",
  "ai": "passport: A passport held by a person. fields: number, country, type, startDate, endDate, date, recordId, authority.",
  "ftm": "Passport"
 },
 "plaintext": {
  "label": "File di testo",
  "en": "Text file",
  "group": "FtM · Documenti",
  "icon": "file-lines",
  "color": "#475569",
  "fields": [
   {
    "key": "title",
    "label": "Titolo",
    "en": "Title",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "fileName",
    "label": "Nome del file",
    "en": "File name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "mimeType",
    "label": "Tipo MIME",
    "en": "MIME type",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "author",
    "label": "Autore",
    "en": "Author",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "fileSize",
    "label": "Dimensione del file",
    "en": "File size",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "messageId",
    "label": "Id messaggio",
    "en": "Message ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "language",
    "label": "Lingua",
    "en": "Language",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "date",
    "label": "Data",
    "en": "Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "authoredAt",
    "label": "Scritto il",
    "en": "Authored on",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "publishedAt",
    "label": "Pubblicato il",
    "en": "Published on",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "fileName"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "fileName",
   "title"
  ],
  "value": "fileName",
  "ai": "plaintext: Text files, like .txt or source code. fields: title, fileName, mimeType, name, country, address, author, fileSize.",
  "ftm": "PlainText"
 },
 "position": {
  "label": "Incarico / posizione",
  "en": "Position",
  "group": "FtM · Procedimenti",
  "icon": "building-columns",
  "color": "#831843",
  "fields": [
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "subnationalArea",
    "label": "Area subnazionale",
    "en": "Subnational area",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "inceptionDate",
    "label": "Data di costituzione",
    "en": "Inception date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "dissolutionDate",
    "label": "Data di scioglimento",
    "en": "Dissolution date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "numberOfSeats",
    "label": "Numero totale di seggi",
    "en": "Total number of seats",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "name"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "name"
  ],
  "value": "name",
  "ai": "position: A post, role or position within an organization or body. This describes a position one or more people may occupy and not the occupation of the post by a specifi fields: name, country, subnationalArea, address, inceptionDate, dissolutionDate, numberOfSeats.",
  "ftm": "Position"
 },
 "project": {
  "label": "Progetto",
  "en": "Project",
  "group": "FtM · Procedimenti",
  "icon": "file-lines",
  "color": "#831843",
  "fields": [
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "projectId",
    "label": "Id progetto",
    "en": "Project ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "startDate",
    "label": "Data di inizio",
    "en": "Start date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "amount",
    "label": "Importo",
    "en": "Amount",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "currency",
    "label": "Valuta",
    "en": "Currency",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "amountUsd",
    "label": "Importo in USD",
    "en": "Amount in USD",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "amountEur",
    "label": "Importo in EUR",
    "en": "Amount in EUR",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "endDate",
    "label": "Data di fine",
    "en": "End date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "date",
    "label": "Data",
    "en": "Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "recordId",
    "label": "Id record",
    "en": "Record ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "status",
    "label": "Stato",
    "en": "Status",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "phase",
    "label": "Fase",
    "en": "Phase",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "goal",
    "label": "Obiettivo del progetto",
    "en": "Project goal",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "projectId"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "name",
   "projectId"
  ],
  "value": "name",
  "ai": "project: An activity carried out by a group of `participants`. fields: name, projectId, startDate, amount, currency, amountUsd, amountEur, country.",
  "ftm": "Project"
 },
 "publicbody": {
  "label": "Ente pubblico",
  "en": "Public body",
  "group": "FtM · Soggetti",
  "icon": "building-columns",
  "color": "#7c2d12",
  "fields": [
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "legalForm",
    "label": "Forma giuridica",
    "en": "Legal form",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "status",
    "label": "Stato",
    "en": "Status",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "abbreviation",
    "label": "Abbreviazione",
    "en": "Abbreviation",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "email",
    "label": "Email",
    "en": "Email",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "phone",
    "label": "Telefono",
    "en": "Phone",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "website",
    "label": "Sito web",
    "en": "Website",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "incorporationDate",
    "label": "Data di costituzione",
    "en": "Incorporation date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "dissolutionDate",
    "label": "Data di scioglimento",
    "en": "Dissolution date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "taxStatus",
    "label": "Stato fiscale",
    "en": "Tax status",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "sector",
    "label": "Settore",
    "en": "Sector",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "classification",
    "label": "Classificazione",
    "en": "Classification",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "registrationNumber",
    "label": "Numero di registrazione",
    "en": "Registration number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "idNumber",
    "label": "Numero identificativo",
    "en": "ID Number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "taxNumber",
    "label": "Codice fiscale",
    "en": "Tax Number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "licenseNumber",
    "label": "Numero di licenza",
    "en": "License Number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "vatCode",
    "label": "Partita IVA",
    "en": "V.A.T. Identifier",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "jurisdiction",
    "label": "Giurisdizione",
    "en": "Jurisdiction",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "mainCountry",
    "label": "Paese di origine",
    "en": "Country of origin",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "opencorporatesUrl",
    "label": "URL OpenCorporates",
    "en": "OpenCorporates URL",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "bvdId",
    "label": "Id Bureau van Dijk",
    "en": "Bureau van Dijk ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "sayariId",
    "label": "Id Sayari",
    "en": "Sayari Entity ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "brightQueryId",
    "label": "Id BrightQuery",
    "en": "BrightQuery ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "uscCode",
    "label": "USCC",
    "en": "USCC",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "icijId",
    "label": "Id ICIJ",
    "en": "ICIJ ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "okpoCode",
    "label": "OKPO",
    "en": "OKPO",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "innCode",
    "label": "INN (codice fiscale russo)",
    "en": "INN",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ogrnCode",
    "label": "OGRN",
    "en": "OGRN",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "okvedCode",
    "label": "OKVED",
    "en": "OKVED",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "leiCode",
    "label": "LEI",
    "en": "LEI",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "dunsCode",
    "label": "Numero DUNS",
    "en": "DUNS",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "uniqueEntityId",
    "label": "Id entità univoco",
    "en": "Unique Entity ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "npiCode",
    "label": "NPI",
    "en": "NPI",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "swiftBic",
    "label": "SWIFT/BIC",
    "en": "SWIFT/BIC",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "cageCode",
    "label": "Codice CAGE",
    "en": "CAGE",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "permId",
    "label": "PermID",
    "en": "PermID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "imoNumber",
    "label": "Numero IMO",
    "en": "IMO Number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "giiNumber",
    "label": "GIIN",
    "en": "GIIN",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "name"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "name",
   "abbreviation"
  ],
  "value": "name",
  "ai": "publicbody: A public body, such as a ministry, department or state company. fields: name, country, legalForm, status, address, abbreviation, email, phone.",
  "ftm": "PublicBody"
 },
 "realestate": {
  "label": "Immobile",
  "en": "Real estate",
  "group": "FtM · Beni e mezzi",
  "icon": "house",
  "color": "#4338ca",
  "fields": [
   {
    "key": "registrationNumber",
    "label": "Numero di registrazione",
    "en": "Registration number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "amount",
    "label": "Importo",
    "en": "Amount",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "currency",
    "label": "Valuta",
    "en": "Currency",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "amountUsd",
    "label": "Importo in USD",
    "en": "Amount in USD",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "amountEur",
    "label": "Importo in EUR",
    "en": "Amount in EUR",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "latitude",
    "label": "Latitudine",
    "en": "Latitude",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "longitude",
    "label": "Longitudine",
    "en": "Longitude",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "censusBlock",
    "label": "Sezione di censimento",
    "en": "Census block",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "cadastralCode",
    "label": "Codice catastale",
    "en": "Cadastral code",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "area",
    "label": "Area",
    "en": "Area",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "titleNumber",
    "label": "Numero di titolo",
    "en": "Title number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "tenure",
    "label": "Durata dell'incarico",
    "en": "Tenure",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "encumbrance",
    "label": "Gravame",
    "en": "Encumbrance",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "propertyType",
    "label": "Tipo di immobile",
    "en": "Property type",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "landType",
    "label": "Tipo di terreno",
    "en": "Land type",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "createDate",
    "label": "Data del record",
    "en": "Record date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "registrationNumber"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "name",
   "address",
   "registrationNumber"
  ],
  "value": "name",
  "ai": "realestate: A piece of land or property. fields: registrationNumber, address, country, amount, currency, amountUsd, amountEur, name.",
  "ftm": "RealEstate"
 },
 "risk": {
  "label": "Rischio",
  "en": "Risk",
  "group": "FtM · Procedimenti",
  "icon": "burst",
  "color": "#831843",
  "fields": [
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "authority",
    "label": "Autorità",
    "en": "Authority",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "program",
    "label": "Programma",
    "en": "Program",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "startDate",
    "label": "Data di inizio",
    "en": "Start date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "endDate",
    "label": "Data di fine",
    "en": "End date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "date",
    "label": "Data",
    "en": "Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "recordId",
    "label": "Id record",
    "en": "Record ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "programId",
    "label": "Id programma",
    "en": "Program ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "programUrl",
    "label": "URL programma",
    "en": "Program URL",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "topics",
    "label": "Temi",
    "en": "Topics",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "status",
    "label": "Stato",
    "en": "Status",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "duration",
    "label": "Durata",
    "en": "Duration",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "reason",
    "label": "Motivo",
    "en": "Reason",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "listingDate",
    "label": "Data di inserimento in lista",
    "en": "Listing date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "reason"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "reason",
   "status"
  ],
  "value": "reason",
  "ai": "risk: A risk designation attached to an entity by an authority. Distinct from `Sanction`: a `Risk` flags heightened exposure or scrutiny, not a legally binding restri fields: country, authority, program, startDate, endDate, date, recordId, programId.",
  "ftm": "Risk"
 },
 "sanction": {
  "label": "Sanzione",
  "en": "Sanction",
  "group": "FtM · Procedimenti",
  "icon": "gavel",
  "color": "#831843",
  "fields": [
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "authority",
    "label": "Autorità",
    "en": "Authority",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "program",
    "label": "Programma",
    "en": "Program",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "startDate",
    "label": "Data di inizio",
    "en": "Start date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "endDate",
    "label": "Data di fine",
    "en": "End date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "date",
    "label": "Data",
    "en": "Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "recordId",
    "label": "Id record",
    "en": "Record ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "authorityId",
    "label": "Identificativo assegnato dall'autorità",
    "en": "Authority-issued identifier",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "unscId",
    "label": "Identificativo ONU (Consiglio di sicurezza)",
    "en": "UN SC identifier",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "programId",
    "label": "Id programma",
    "en": "Program ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "programUrl",
    "label": "URL programma",
    "en": "Program URL",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "provisions",
    "label": "Ambito delle sanzioni",
    "en": "Scope of sanctions",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "status",
    "label": "Stato",
    "en": "Status",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "duration",
    "label": "Durata",
    "en": "Duration",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "reason",
    "label": "Motivo",
    "en": "Reason",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "listingDate",
    "label": "Data di inserimento in lista",
    "en": "Listing date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "authorityId"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "program"
  ],
  "value": "program",
  "ai": "sanction: A sanction designation. fields: country, authority, program, startDate, endDate, date, recordId, authorityId.",
  "ftm": "Sanction"
 },
 "security": {
  "label": "Strumento finanziario",
  "en": "Security",
  "group": "FtM · Finanza",
  "icon": "file-invoice-dollar",
  "color": "#0f766e",
  "fields": [
   {
    "key": "isin",
    "label": "ISIN",
    "en": "ISIN",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "amount",
    "label": "Importo",
    "en": "Amount",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "currency",
    "label": "Valuta",
    "en": "Currency",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "amountUsd",
    "label": "Importo in USD",
    "en": "Amount in USD",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "amountEur",
    "label": "Importo in EUR",
    "en": "Amount in EUR",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "registrationNumber",
    "label": "Numero di registrazione",
    "en": "Registration number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ticker",
    "label": "Ticker di borsa",
    "en": "Stock ticker symbol",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "figiCode",
    "label": "Identificativo globale dello strumento (FIGI)",
    "en": "Financial Instrument Global Identifier",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "issueDate",
    "label": "Data di emissione",
    "en": "Date issued",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "maturityDate",
    "label": "Data di scadenza",
    "en": "Maturity date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "type",
    "label": "Tipo",
    "en": "Type",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "classification",
    "label": "Classificazione",
    "en": "Classification",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "collateral",
    "label": "Garanzia",
    "en": "Collateral",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "isin"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "name",
   "isin",
   "registrationNumber"
  ],
  "value": "name",
  "ai": "security: A tradeable financial asset. fields: isin, name, country, amount, currency, amountUsd, amountEur, address.",
  "ftm": "Security"
 },
 "similar": {
  "label": "Simile",
  "en": "Similar",
  "group": "FtM · Documenti",
  "icon": "link",
  "color": "#475569",
  "fields": [
   {
    "key": "confidenceScore",
    "label": "Punteggio di confidenza",
    "en": "Confidence score",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "criteria",
    "label": "Criteri di confronto",
    "en": "Matching criteria",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "matcher",
    "label": "Confrontatore",
    "en": "Matcher",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "confidenceScore"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "confidenceScore",
   "criteria"
  ],
  "value": "confidenceScore",
  "ai": "similar: A link between two entities that are presumed to be the same, e.g. as the outcome of a probabilistic record linkage process. fields: confidenceScore, criteria, matcher.",
  "ftm": "Similar"
 },
 "table": {
  "label": "Tabella",
  "en": "Table",
  "group": "FtM · Documenti",
  "icon": "file-lines",
  "color": "#475569",
  "fields": [
   {
    "key": "title",
    "label": "Titolo",
    "en": "Title",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "fileName",
    "label": "Nome del file",
    "en": "File name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "mimeType",
    "label": "Tipo MIME",
    "en": "MIME type",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "author",
    "label": "Autore",
    "en": "Author",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "fileSize",
    "label": "Dimensione del file",
    "en": "File size",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "messageId",
    "label": "Id messaggio",
    "en": "Message ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "language",
    "label": "Lingua",
    "en": "Language",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "date",
    "label": "Data",
    "en": "Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "authoredAt",
    "label": "Scritto il",
    "en": "Authored on",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "publishedAt",
    "label": "Pubblicato il",
    "en": "Published on",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "rowCount",
    "label": "Numero di righe",
    "en": "Number of rows",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "title"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "title",
   "name",
   "fileName"
  ],
  "value": "title",
  "ai": "table: A document structured into rows and cells. This includes simple CSV files, spreadsheet sheets or database relations. fields: title, fileName, mimeType, name, country, address, author, fileSize.",
  "ftm": "Table"
 },
 "taxroll": {
  "label": "Dichiarazione fiscale",
  "en": "Tax roll",
  "group": "FtM · Finanza",
  "icon": "receipt",
  "color": "#0f766e",
  "fields": [
   {
    "key": "date",
    "label": "Data",
    "en": "Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "income",
    "label": "Reddito dichiarato",
    "en": "Registered income",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "wealth",
    "label": "Patrimonio dichiarato",
    "en": "Registered wealth",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "taxPaid",
    "label": "Imposte pagate",
    "en": "Amount of tax paid",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "startDate",
    "label": "Data di inizio",
    "en": "Start date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "endDate",
    "label": "Data di fine",
    "en": "End date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "recordId",
    "label": "Id record",
    "en": "Record ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "surname",
    "label": "Cognome",
    "en": "Surname",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "givenName",
    "label": "Nome di battesimo",
    "en": "Given name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "birthDate",
    "label": "Data di nascita",
    "en": "Birth date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "date"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "date"
  ],
  "value": "date",
  "ai": "taxroll: A tax declaration of an individual. fields: date, income, wealth, taxPaid, startDate, endDate, recordId, country.",
  "ftm": "TaxRoll"
 },
 "territory": {
  "label": "Territorio",
  "en": "Territory",
  "group": "FtM · Procedimenti",
  "icon": "globe",
  "color": "#831843",
  "fields": [
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "territoryCode",
    "label": "Codice territorio",
    "en": "Territory code",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "level",
    "label": "Livello",
    "en": "Level",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "fipsCode",
    "label": "Codice FIPS",
    "en": "FIPS code",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "zipCode",
    "label": "CAP",
    "en": "ZIP code",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "nutsCode",
    "label": "Codice NUTS",
    "en": "NUTS code",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "name"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "name"
  ],
  "value": "name",
  "ai": "territory: A country, subnational division or other administrative area. Territories are reference data with deterministic identifiers, not a geospatial model. fields: name, territoryCode, country, level, address, fipsCode, zipCode, nutsCode.",
  "ftm": "Territory"
 },
 "trip": {
  "label": "Viaggio",
  "en": "Trip",
  "group": "FtM · Procedimenti",
  "icon": "location-dot",
  "color": "#831843",
  "fields": [
   {
    "key": "startDate",
    "label": "Data di inizio",
    "en": "Start date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "endDate",
    "label": "Data di fine",
    "en": "End date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "date",
    "label": "Data",
    "en": "Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "recordId",
    "label": "Id record",
    "en": "Record ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "location",
    "label": "Luogo",
    "en": "Location",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "important",
    "label": "Importante",
    "en": "Important",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "name"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "name",
   "startDate",
   "endDate"
  ],
  "value": "name",
  "ai": "trip:  fields: startDate, endDate, name, country, address, date, recordId, location.",
  "ftm": "Trip"
 },
 "vessel": {
  "label": "Nave",
  "en": "Vessel",
  "group": "FtM · Beni e mezzi",
  "icon": "car",
  "color": "#4338ca",
  "fields": [
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "imoNumber",
    "label": "Numero IMO",
    "en": "IMO Number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "type",
    "label": "Tipo",
    "en": "Type",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "flag",
    "label": "Bandiera",
    "en": "Flag",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "amount",
    "label": "Importo",
    "en": "Amount",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "currency",
    "label": "Valuta",
    "en": "Currency",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "amountUsd",
    "label": "Importo in USD",
    "en": "Amount in USD",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "amountEur",
    "label": "Importo in EUR",
    "en": "Amount in EUR",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "registrationNumber",
    "label": "Numero di registrazione",
    "en": "Registration number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "model",
    "label": "Modello",
    "en": "Model",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "buildDate",
    "label": "Data di costruzione",
    "en": "Build Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "registrationDate",
    "label": "Data di registrazione",
    "en": "Registration Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "deregistrationDate",
    "label": "Data di cancellazione",
    "en": "De-registration Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "crsNumber",
    "label": "Numero CRS",
    "en": "CRS Number",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "registrationPort",
    "label": "Porto di immatricolazione",
    "en": "Port of Registration",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "navigationArea",
    "label": "Area di navigazione",
    "en": "Navigation Area",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "tonnage",
    "label": "Stazza",
    "en": "Tonnage",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "grossRegisteredTonnage",
    "label": "Stazza lorda (GRT)",
    "en": "Gross Registered Tonnage",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "deadweightTonnage",
    "label": "Portata lorda (DWT)",
    "en": "Deadweight Tonnage",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "nameChangeDate",
    "label": "Data del cambio di nome",
    "en": "Date of Name Change",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "callSign",
    "label": "Nominativo radio",
    "en": "Call Sign",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "pastFlags",
    "label": "Bandiere precedenti",
    "en": "Past Flags",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "pastTypes",
    "label": "Tipi precedenti",
    "en": "Past Types",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "mmsi",
    "label": "MMSI",
    "en": "MMSI",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "imoNumber"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "name",
   "imoNumber"
  ],
  "value": "name",
  "ai": "vessel: A boat or ship. Typically flying some sort of national flag. fields: name, imoNumber, type, flag, amount, currency, amountUsd, amountEur.",
  "ftm": "Vessel"
 },
 "video": {
  "label": "Video",
  "en": "Video",
  "group": "FtM · Documenti",
  "icon": "image",
  "color": "#475569",
  "fields": [
   {
    "key": "title",
    "label": "Titolo",
    "en": "Title",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "fileName",
    "label": "Nome del file",
    "en": "File name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "mimeType",
    "label": "Tipo MIME",
    "en": "MIME type",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "author",
    "label": "Autore",
    "en": "Author",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "fileSize",
    "label": "Dimensione del file",
    "en": "File size",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "messageId",
    "label": "Id messaggio",
    "en": "Message ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "language",
    "label": "Lingua",
    "en": "Language",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "date",
    "label": "Data",
    "en": "Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "authoredAt",
    "label": "Scritto il",
    "en": "Authored on",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "publishedAt",
    "label": "Pubblicato il",
    "en": "Published on",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "duration",
    "label": "Durata",
    "en": "Duration",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "fileName"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "fileName",
   "title"
  ],
  "value": "fileName",
  "ai": "video:  fields: title, fileName, mimeType, name, country, address, author, fileSize.",
  "ftm": "Video"
 },
 "workbook": {
  "label": "Cartella di lavoro",
  "en": "Workbook",
  "group": "FtM · Documenti",
  "icon": "file-lines",
  "color": "#475569",
  "fields": [
   {
    "key": "title",
    "label": "Titolo",
    "en": "Title",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "fileName",
    "label": "Nome del file",
    "en": "File name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "name",
    "label": "Nome",
    "en": "Name",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "country",
    "label": "Paese",
    "en": "Country",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "address",
    "label": "Indirizzo",
    "en": "Address",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "author",
    "label": "Autore",
    "en": "Author",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "fileSize",
    "label": "Dimensione del file",
    "en": "File size",
    "type": "number",
    "options": [],
    "ph": ""
   },
   {
    "key": "messageId",
    "label": "Id messaggio",
    "en": "Message ID",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "mimeType",
    "label": "Tipo MIME",
    "en": "MIME type",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "language",
    "label": "Lingua",
    "en": "Language",
    "type": "text",
    "options": [],
    "ph": ""
   },
   {
    "key": "date",
    "label": "Data",
    "en": "Date",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "authoredAt",
    "label": "Scritto il",
    "en": "Authored on",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "publishedAt",
    "label": "Pubblicato il",
    "en": "Published on",
    "type": "date",
    "options": [],
    "ph": ""
   },
   {
    "key": "ftmId",
    "label": "Id FtM",
    "en": "FtM id",
    "type": "text",
    "options": [],
    "ph": "",
    "hidden": True
   }
  ],
  "ident": [
   "ftmId"
  ],
  "ident_alt": [
   "fileName"
  ],
  "norm": {
   "ftmId": "compact_case"
  },
  "label_fmt": [
   "fileName",
   "title"
  ],
  "value": "fileName",
  "ai": "workbook: A spreadsheet document, for example from Excel. Each spreadsheet contains a set of sheets that hold actual data. fields: title, fileName, name, country, address, author, fileSize, messageId.",
  "ftm": "Workbook"
 }
}

# italiano -> (en, fr, de, es, ar); fr/de/es/ar dai cataloghi di FtM
FTM_I18N = {
 "Follow the Money": [
  "Follow the Money",
  "Follow the Money",
  "Follow the Money",
  "Follow the Money",
  "Follow the Money"
 ],
 "FtM · Soggetti": [
  "FtM · Soggetti",
  "FtM · Soggetti",
  "FtM · Soggetti",
  "FtM · Soggetti",
  "FtM · Soggetti"
 ],
 "FtM · Finanza": [
  "FtM · Finanza",
  "FtM · Finanza",
  "FtM · Finanza",
  "FtM · Finanza",
  "FtM · Finanza"
 ],
 "FtM · Documenti d'identità": [
  "FtM · Documenti d'identità",
  "FtM · Documenti d'identità",
  "FtM · Documenti d'identità",
  "FtM · Documenti d'identità",
  "FtM · Documenti d'identità"
 ],
 "FtM · Beni e mezzi": [
  "FtM · Beni e mezzi",
  "FtM · Beni e mezzi",
  "FtM · Beni e mezzi",
  "FtM · Beni e mezzi",
  "FtM · Beni e mezzi"
 ],
 "FtM · Procedimenti": [
  "FtM · Procedimenti",
  "FtM · Procedimenti",
  "FtM · Procedimenti",
  "FtM · Procedimenti",
  "FtM · Procedimenti"
 ],
 "FtM · Documenti": [
  "FtM · Documenti",
  "FtM · Documenti",
  "FtM · Documenti",
  "FtM · Documenti",
  "FtM · Documenti"
 ],
 "Id FtM": [
  "FtM id",
  "FtM id",
  "FtM id",
  "FtM id",
  "FtM id"
 ],
 "Importo": [
  "Amount",
  "Montant",
  "Betrag",
  "Cantidad",
  "المبلغ"
 ],
 "Valuta": [
  "Currency",
  "Monnaie",
  "Währung",
  "Moneda",
  "عملة"
 ],
 "Importo in USD": [
  "Amount in USD",
  "Montant en USD",
  "Betrag in USD",
  "Cantidad en USD",
  "المبلغ بالدولار الأمريكي"
 ],
 "Importo in EUR": [
  "Amount in EUR",
  "Montant en EUR",
  "Betrag in EUR",
  "Cantidad en EUR",
  "المبلغ باليورو"
 ],
 "Nome": [
  "Name",
  "Nom",
  "Name",
  "Nombre",
  "الاسم"
 ],
 "Paese": [
  "Country",
  "Pays",
  "Land",
  "País",
  "الدولة"
 ],
 "Indirizzo": [
  "Address",
  "Adresse",
  "Adresse",
  "Dirección",
  "العنوان"
 ],
 "Numero di registrazione": [
  "Registration number",
  "Numéro d’enregistrement",
  "Registrierungsnummer",
  "Número de registro",
  "رقم التسجيل"
 ],
 "Tipo": [
  "Type",
  "Type",
  "Art",
  "Tipo",
  "النوع"
 ],
 "Modello": [
  "Model",
  "Modèle",
  "Modell",
  "Modelo",
  "نموذج"
 ],
 "Data di costruzione": [
  "Build Date",
  "Date de construction",
  "Fertigstellungsdatum",
  "Fecha de elaboración",
  "تاريخ الإنشاء"
 ],
 "Data di registrazione": [
  "Registration Date",
  "Date d’enregistrement",
  "Eintragungsdatum",
  "Fecha de registro",
  "تاريخ التسجيل"
 ],
 "Data di cancellazione": [
  "De-registration Date",
  "De-registration Date",
  "De-registration Date",
  "De-registration Date",
  "De-registration Date"
 ],
 "Numero di serie": [
  "Serial Number",
  "Numéro de série",
  "Seriennummer",
  "Número de serial",
  "الرقم التسلسلي"
 ],
 "Designatore ICAO del tipo": [
  "ICAO aircraft type designator",
  "Code de type d’aéronef OACI",
  "ICAO Flugzeug-Designation",
  "Indicador de tipo de aeronave de la OACI",
  "طائرات الايكاو المدنية"
 ],
 "Costruttore": [
  "Manufacturer",
  "Fabricant",
  "Hersteller",
  "Fabricante",
  "الصانع"
 ],
 "Aeromobile": [
  "Airplane",
  "Avion",
  "Flugzeug",
  "Aeronave",
  "طائرة"
 ],
 "Titolo": [
  "Title",
  "Titre",
  "TItel",
  "Título",
  "عنوان"
 ],
 "Autore": [
  "Author",
  "Auteur",
  "Autor",
  "Autor",
  "المؤلف"
 ],
 "Dimensione del file": [
  "File size",
  "Taille du fichier",
  "Dateigröße",
  "Tamaño del archivo",
  "حجم الملف"
 ],
 "Nome del file": [
  "File name",
  "Nom du fichier",
  "Dateiname",
  "Nombre del archivo",
  "اسم الملف"
 ],
 "Id messaggio": [
  "Message ID",
  "Identifiant de message",
  "Nachrichten-ID",
  "Identificación del mensaje",
  "معرف الرسائل"
 ],
 "Tipo MIME": [
  "MIME type",
  "Type MIME",
  "MIME-Typ",
  "Tipo de MIME",
  "التمثيل الصامت"
 ],
 "Lingua": [
  "Language",
  "Langue",
  "Sprache",
  "Idioma",
  "اللغة"
 ],
 "Data": [
  "Date",
  "Date",
  "Datum",
  "Fecha",
  "تاريخ"
 ],
 "Scritto il": [
  "Authored on",
  "Créé le",
  "Verfasst am",
  "Elaborado el",
  "ألف في"
 ],
 "Pubblicato il": [
  "Published on",
  "Publié le",
  "Veröffentlicht am",
  "Publicado el",
  "تم النشر بتاريخ:"
 ],
 "Articolo": [
  "Article",
  "Article",
  "Artikel",
  "Article",
  "Article"
 ],
 "Bene": [
  "Asset",
  "Actif",
  "Vermögenswert",
  "Activo",
  "أصل "
 ],
 "Durata": [
  "Duration",
  "Durée",
  "Dauer",
  "Duración",
  "المدة الزمنية"
 ],
 "Frequenza di campionamento": [
  "Sampling Rate",
  "Taux d’échantillonnage",
  "Sample-Rate",
  "Tasa de muestreo",
  "معدل أخذ عينات /  معدل العينة"
 ],
 "Audio": [
  "Audio",
  "Audio",
  "Audio",
  "Audio",
  "صوت"
 ],
 "Nome della banca": [
  "Bank name",
  "Nom de la banque",
  "Name der Bank",
  "Bank name",
  "Bank name"
 ],
 "Numero di conto": [
  "Account number",
  "Numéro de compte",
  "Kontonummer",
  "Account number",
  "Account number"
 ],
 "IBAN": [
  "IBAN",
  "IBAN",
  "IBAN",
  "IBAN",
  "رقم الحساب المصرفي الدولي"
 ],
 "Codice identificativo banca (BIC)": [
  "Bank Identifier Code",
  "Code d’identification de banque",
  "Bankleitzahl",
  "Código de identificación del banco",
  "الرمز التعريفي للبنك"
 ],
 "Tipo di conto": [
  "Account type",
  "Type de compte",
  "Kontenart",
  "Account type",
  "Account type"
 ],
 "Data di apertura": [
  "Opening date",
  "Opening date",
  "Opening date",
  "Opening date",
  "Opening date"
 ],
 "Data di chiusura": [
  "Closing date",
  "Closing date",
  "Closing date",
  "Closing date",
  "Closing date"
 ],
 "Saldo": [
  "Balance",
  "Solde",
  "Kontostand",
  "Saldo",
  "رصيد حساب"
 ],
 "Data del saldo": [
  "Balance date",
  "Date du solde",
  "Konstostands-Datum",
  "Balance date",
  "Balance date"
 ],
 "Saldo massimo": [
  "Maximum balance",
  "Solde maximum",
  "Maximaler Kontostand",
  "Maximum balance",
  "Maximum balance"
 ],
 "Data del saldo massimo": [
  "Maximum balance date",
  "Date du solde maximum",
  "Datum des maximalen Kontostands",
  "Maximum balance date",
  "Maximum balance date"
 ],
 "Indirizzo della banca": [
  "Bank address",
  "Adresse de la banque",
  "Bank address",
  "Bank address",
  "Bank address"
 ],
 "Conto bancario": [
  "Bank account",
  "Compte bancaire",
  "Bankkonto",
  "Bank account",
  "Bank account"
 ],
 "Data di inizio": [
  "Start date",
  "Date de commencement",
  "Startdatum",
  "Fecha de inicio",
  "تاريخ البدء"
 ],
 "Data di fine": [
  "End date",
  "Date de fin",
  "Enddatum",
  "Fecha de finalización",
  "تاريخ الإنتهاء"
 ],
 "Id record": [
  "Record ID",
  "Identifiant du registre",
  "Eintrags-ID",
  "Identificador del registro",
  "رقم التسجيل"
 ],
 "Numero chiamante": [
  "Caller's Number",
  "Numéro de l’appelant",
  "Anfrufernummer",
  "Número del interlocutor",
  "رقم المتصل"
 ],
 "Numero chiamato": [
  "Receiver's Number",
  "Numéro du destinataire",
  "Empfängernummer",
  "Número del receptor",
  "رقم المستلم"
 ],
 "Chiamata telefonica": [
  "Call",
  "Appel",
  "Anruf",
  "Llamada",
  "مكالمة"
 ],
 "Id univoco del bando": [
  "CfT unique id",
  "CfT unique id",
  "CfT unique id",
  "CfT unique id",
  "CfT unique id"
 ],
 "Riferimento stazione appaltante": [
  "Contracting authority reference ID",
  "Contracting authority reference ID",
  "Contracting authority reference ID",
  "Contracting authority reference ID",
  "Contracting authority reference ID"
 ],
 "Data di pubblicazione / invito": [
  "Date of publication/invitation",
  "Date of publication/invitation",
  "Date of publication/invitation",
  "Date of publication/invitation",
  "Date of publication/invitation"
 ],
 "Criterio di valutazione": [
  "Evaluation mechanism",
  "Evaluation mechanism",
  "Evaluation mechanism",
  "Evaluation mechanism",
  "Evaluation mechanism"
 ],
 "Tipo di appalto": [
  "Procurement type",
  "Procurement type",
  "Procurement type",
  "Procurement type",
  "Procurement type"
 ],
 "Direttiva": [
  "Directive",
  "Directive",
  "Directive",
  "Directive",
  "Directive"
 ],
 "Procedura": [
  "Procedure",
  "Procedure",
  "Procedure",
  "Procedure",
  "Procedure"
 ],
 "Esito del bando": [
  "Call for tenders result",
  "Call for tenders result",
  "Call for tenders result",
  "Call for tenders result",
  "Call for tenders result"
 ],
 "Codice CPV": [
  "CPV code",
  "Code CPV",
  "CPV-Code",
  "Código CPV",
  "رمز الشراء العام"
 ],
 "Aste elettroniche previste": [
  "Inclusion of e-Auctions",
  "Inclusion of e-Auctions",
  "Inclusion of e-Auctions",
  "Inclusion of e-Auctions",
  "Inclusion of e-Auctions"
 ],
 "Codice NUTS": [
  "NUTS code",
  "Code NUTS",
  "NUTS-Code",
  "Código NUTS",
  "رقم  الوحدات الإقليمية للإحصاءات"
 ],
 "Sopra o sotto soglia": [
  "Above or below threshold",
  "Above or below threshold",
  "Above or below threshold",
  "Above or below threshold",
  "Above or below threshold"
 ],
 "Modalità di pagamento": [
  "Payment options",
  "Payment options",
  "Payment options",
  "Payment options",
  "Payment options"
 ],
 "Termine di presentazione": [
  "Submission deadline",
  "Submission deadline",
  "Submission deadline",
  "Submission deadline",
  "Submission deadline"
 ],
 "Fine periodo chiarimenti": [
  "End of clarification period",
  "End of clarification period",
  "End of clarification period",
  "End of clarification period",
  "End of clarification period"
 ],
 "Contratto aggiudicato a lotti": [
  "Contract awarded in Lots",
  "Contract awarded in Lots",
  "Contract awarded in Lots",
  "Contract awarded in Lots",
  "Contract awarded in Lots"
 ],
 "Numero di lotti": [
  "Number of lots",
  "Number of lots",
  "Number of lots",
  "Number of lots",
  "Number of lots"
 ],
 "Nomi dei lotti": [
  "Lots names",
  "Lots names",
  "Lots names",
  "Lots names",
  "Lots names"
 ],
 "Offerte per lotto": [
  "Tenders for lots",
  "Tenders for lots",
  "Tenders for lots",
  "Tenders for lots",
  "Tenders for lots"
 ],
 "Numero massimo di lotti": [
  "Maximum number of lots",
  "Maximum number of lots",
  "Maximum number of lots",
  "Maximum number of lots",
  "Maximum number of lots"
 ],
 "Finanziamento UE": [
  "EU funding",
  "EU funding",
  "EU funding",
  "EU funding",
  "EU funding"
 ],
 "Offerte multiple ammesse": [
  "Multiple tenders will be accepted",
  "Multiple tenders will be accepted",
  "Multiple tenders will be accepted",
  "Multiple tenders will be accepted",
  "Multiple tenders will be accepted"
 ],
 "Link TED agli avvisi pubblicati": [
  "TED link for published notices",
  "TED link for published notices",
  "TED link for published notices",
  "TED link for published notices",
  "TED link for published notices"
 ],
 "Rientra nel GPP (appalti pubblici)?": [
  "Does this call fall under the scope of GPP?",
  "Does this call fall under the scope of GPP?",
  "Does this call fall under the scope of GPP?",
  "Does this call fall under the scope of GPP?",
  "Does this call fall under the scope of GPP?"
 ],
 "Verifica certificazione": [
  "Certification check",
  "Certification check",
  "Certification check",
  "Certification check",
  "Certification check"
 ],
 "Data di aggiudicazione": [
  "Date of awarding",
  "Date of awarding",
  "Date of awarding",
  "Date of awarding",
  "Date of awarding"
 ],
 "Data avviso di gara": [
  "Contract notice date",
  "Contract notice date",
  "Contract notice date",
  "Contract notice date",
  "Contract notice date"
 ],
 "Data avviso di aggiudicazione": [
  "Award Notice Date",
  "Award Notice Date",
  "Award Notice Date",
  "Award Notice Date",
  "Award Notice Date"
 ],
 "Bando di gara": [
  "Call for tenders",
  "Call for tenders",
  "Call for tenders",
  "Call for tenders",
  "Call for tenders"
 ],
 "Abbreviazione": [
  "Abbreviation",
  "Abbreviation",
  "Abbreviation",
  "Abbreviation",
  "Abbreviation"
 ],
 "Email": [
  "Email",
  "Email",
  "Email",
  "Email",
  "Email"
 ],
 "Telefono": [
  "Phone",
  "Téléphone",
  "Telefon",
  "Teléfono",
  "الهاتف"
 ],
 "Sito web": [
  "Website",
  "Site Internet",
  "Webseite",
  "Sitio web",
  "الموقع الإلكتروني"
 ],
 "Forma giuridica": [
  "Legal form",
  "Forme juridique",
  "Rechtsform",
  "Forma jurídica",
  "استمارة قانونية"
 ],
 "Data di costituzione": [
  "Incorporation date",
  "Date de constitution",
  "Eintragungsdatum",
  "Fecha de constitución",
  "تاريخ التأسيس"
 ],
 "Data di scioglimento": [
  "Dissolution date",
  "Date de dissolution",
  "Auflösungsdatum",
  "Fecha de disolución",
  "تاريخ حلّ / تصفية الشركة"
 ],
 "Stato fiscale": [
  "Tax status",
  "Statut fiscal",
  "Steuerkategorie",
  "Situación fiscal",
  "الوضع الضريبي"
 ],
 "Stato": [
  "Status",
  "État",
  "Status",
  "Estado",
  "الحالة"
 ],
 "Settore": [
  "Sector",
  "Secteur",
  "Sektor",
  "Sector",
  "قطاع"
 ],
 "Classificazione": [
  "Classification",
  "Classification",
  "Klassifizierung",
  "Clasificación",
  "التصنيف"
 ],
 "Numero identificativo": [
  "ID Number",
  "Numéro ID",
  "ID-Nummer",
  "Número de identificación",
  "رقم الهوية"
 ],
 "Codice fiscale": [
  "Tax Number",
  "Numéro fiscal",
  "Steuernummer",
  "Número fiscal",
  "الرقم الضريبي"
 ],
 "Numero di licenza": [
  "License Number",
  "License Number",
  "License Number",
  "License Number",
  "License Number"
 ],
 "Partita IVA": [
  "V.A.T. Identifier",
  "Numéro de TVA",
  "USt-ID",
  "Identificador de IVA",
  "معرف V.A.T. "
 ],
 "Giurisdizione": [
  "Jurisdiction",
  "Juridiction",
  "Rechtsprechung",
  "Jurisdicción",
  "سلطة القضاء"
 ],
 "Paese di origine": [
  "Country of origin",
  "Pays d’origine",
  "Ursprungsland",
  "País de origen",
  "بلد المنشأ"
 ],
 "URL OpenCorporates": [
  "OpenCorporates URL",
  "URL d’OpenCorporates",
  "OpenCorporates-URL",
  "URL de OpenCorporates",
  "رابط OpenCorporates "
 ],
 "Id Bureau van Dijk": [
  "Bureau van Dijk ID",
  "Identification de Bureau van Dijk",
  "Bureau van Dijk-ID",
  "Identificación de Bureau van Dijk",
  "قاعدة بيانات Bureau van Dijk "
 ],
 "Id Sayari": [
  "Sayari Entity ID",
  "Sayari Entity ID",
  "Sayari Entity ID",
  "Sayari Entity ID",
  "Sayari Entity ID"
 ],
 "Id BrightQuery": [
  "BrightQuery ID",
  "BrightQuery ID",
  "BrightQuery ID",
  "BrightQuery ID",
  "BrightQuery ID"
 ],
 "USCC": [
  "USCC",
  "USCC",
  "USCC",
  "USCC",
  "USCC"
 ],
 "Id ICIJ": [
  "ICIJ ID",
  "Identification ICIJ",
  "ICIJ-ID",
  "Identificación de ICIJ",
  "الاتحاد الدولي للصحفيين الاستقصائيين"
 ],
 "OKPO": [
  "OKPO",
  "OKPO",
  "OKPO",
  "OKPO",
  "Okpo هو حي في مدينة Geoje في مقاطعة كوريا الجنوبية"
 ],
 "INN (codice fiscale russo)": [
  "INN",
  "INN",
  "INN",
  "INN",
  "النزل"
 ],
 "OGRN": [
  "OGRN",
  "OGRN",
  "OGRN",
  "OGRN",
  "يتم استخدام OGRN في السجل كرقم ملف تسجيل شركة"
 ],
 "OKVED": [
  "OKVED",
  "OKVED",
  "OKVED",
  "OKVED",
  "OKVED"
 ],
 "LEI": [
  "LEI",
  "LEI",
  "LEI",
  "LEI",
  "LEI"
 ],
 "Numero DUNS": [
  "DUNS",
  "DUNS",
  "DUNS",
  "DUNS",
  "DUNS"
 ],
 "Id entità univoco": [
  "Unique Entity ID",
  "Unique Entity ID",
  "Unique Entity ID",
  "Unique Entity ID",
  "Unique Entity ID"
 ],
 "NPI": [
  "NPI",
  "NPI",
  "NPI",
  "NPI",
  "NPI"
 ],
 "SWIFT/BIC": [
  "SWIFT/BIC",
  "SWIFT/BIC",
  "SWIFT/BLZ",
  "SWIFT/BIC",
  "SWIFT/BIC"
 ],
 "Codice CAGE": [
  "CAGE",
  "CAGE",
  "CAGE",
  "CAGE",
  "CAGE"
 ],
 "PermID": [
  "PermID",
  "PermID",
  "PermID",
  "PermID",
  "PermID"
 ],
 "Numero IMO": [
  "IMO Number",
  "Numéro OMI",
  "IMO-Nummer",
  "Número de IMO",
  "رقم المنظمة البحرية الدولية"
 ],
 "GIIN": [
  "GIIN",
  "GIIN",
  "GIIN",
  "GIIN",
  "GIIN"
 ],
 "Capitale": [
  "Capital",
  "Capital",
  "Vermögen",
  "Capital",
  "العاصمة"
 ],
 "VOEN": [
  "VOEN",
  "VOEN",
  "VOEN",
  "VOEN",
  "VOEN"
 ],
 "Codice territoriale COATO / SOATO / OKATO": [
  "COATO / SOATO / OKATO",
  "COATO / SOATO / OKATO",
  "COATO / SOATO / OKATO",
  "COATO / SOATO / OKATO",
  "أوكاتو / أوكاتو / أوكاتو"
 ],
 "Numero IRS": [
  "IRS Number",
  "Numéro IRS",
  "IRS-Nummer",
  "Número de IRS",
  "رقم IRS"
 ],
 "IPO": [
  "IPO",
  "IPO",
  "IPO",
  "IPO",
  "شركات عامه- الاكتتاب العام IPO"
 ],
 "Chiave SEC (CIK)": [
  "SEC Central Index Key",
  "Central Index Key de la SEC",
  "Zentraler SEC-Indexschlüssel",
  "Clave del índice central de la SEC",
  "الرمز المرجعي لهيئة الأوراق المالية والبورصة - مفتاح المؤشر المركزي"
 ],
 "JIB": [
  "JIB",
  "JIB",
  "JIB",
  "JIB",
  "البنك الإسلامي الأردني"
 ],
 "MBS": [
  "MBS",
  "MBS",
  "MBS",
  "MBS",
  "جدول فوائد الرعاية الطبية MBS"
 ],
 "Codice CAEM": [
  "COD CAEM",
  "COD CAEM",
  "COD CAEM",
  "COD CAEM",
  "رقم النشاط التجاري COD CAEM"
 ],
 "KPP": [
  "KPP",
  "KPP",
  "KPP",
  "KPP",
  "مشروع إنتاج المعرفة KPP"
 ],
 "OKOPF": [
  "OKOPF",
  "OKOPF",
  "OKOPF",
  "OKOPF",
  "OKOPF"
 ],
 "Codice del servizio fiscale federale": [
  "Federal tax service code",
  "Code de service fiscal fédéral",
  "Bundessteuer-Code",
  "Código de servicio de impuestos federales",
  "رمز خدمة الضرائب الفيدرالية"
 ],
 "Codice FSS": [
  "FSS",
  "FSS",
  "FSS",
  "FSS",
  "محاكي نظام حقل العمل FSS"
 ],
 "BIK (codice banca russo)": [
  "BIK",
  "BIK",
  "BIK",
  "BIK",
  "مكتب معلومات الائتمان"
 ],
 "Numero PFR": [
  "PFR Number",
  "Numéro PFR",
  "PFR Nummer",
  "Número PFR",
  "رقم تسجيل الأسطول الدائم"
 ],
 "OKSM": [
  "OKSM",
  "OKSM",
  "OKSM",
  "OKSM",
  "OKSM"
 ],
 "Ticker di borsa": [
  "Stock ticker symbol",
  "Stock ticker symbol",
  "Stock ticker symbol",
  "Stock ticker symbol",
  "Stock ticker symbol"
 ],
 "Codice strumento Reuters (RIC)": [
  "Reuters Instrument Code",
  "Reuters Instrument Code",
  "Reuters Instrument Code",
  "Reuters Instrument Code",
  "Reuters Instrument Code"
 ],
 "Società": [
  "Company",
  "Société",
  "Firma",
  "Empresa",
  "شركة"
 ],
 "Data del contratto": [
  "Contract date",
  "Date du contrat",
  "Vertragsdatum",
  "Fecha del contrato",
  "تاريخ العقد"
 ],
 "Numero della procedura": [
  "Procedure number",
  "Numéro de procédure",
  "Vorgangsnummer",
  "Número de procedimiento",
  "رقم الإجراء"
 ],
 "Procedura contrattuale": [
  "Contract procedure",
  "Procédure du contrat",
  "Vertragsprozedur",
  "Procedimiento contractual",
  "إجراءات العقد"
 ],
 "Id avviso di aggiudicazione": [
  "Contract Award Notice ID",
  "Identification de l’avis d’attribution du contrat",
  "Vergabeszuschlagsnummer",
  "Identificación de aviso de adjudicación de contrato",
  "رقم إشعار إرساء العقد"
 ],
 "Numero di aggiudicazioni": [
  "Number of awards",
  "Nombre d’attributions",
  "Anzahl der Zuschläge",
  "Número de adjudicaciones",
  "عدد الجوائز"
 ],
 "Metodo di appalto": [
  "Procurement method",
  "Méthode d’approvisionnement",
  "Vergabemethode",
  "Método de compra",
  "طريقة الشراء"
 ],
 "Criteri di aggiudicazione": [
  "Contract award criteria",
  "Critères d’attribution du contrat",
  "Vergabekriterien",
  "Criterios de adjudicación de contrato",
  "معيار منح العقد"
 ],
 "Annullato?": [
  "Cancelled?",
  "Annulé ?",
  "Abgebrochen?",
  "¿Cancelado?",
  "الغي؟"
 ],
 "Contratto": [
  "Contract",
  "Contrat",
  "Vertrag",
  "Contrato",
  "العقد"
 ],
 "Categoria": [
  "Category",
  "Catégorie",
  "Kategorie",
  "Categoría",
  "الفئة"
 ],
 "Numero del procedimento": [
  "Case number",
  "Numéro de dossier",
  "Fallnummer",
  "Número de caso",
  "رقم القضية"
 ],
 "Tribunale": [
  "Court",
  "Tribunal",
  "Gericht",
  "Tribunal",
  "المحكمة"
 ],
 "Data di deposito": [
  "File date",
  "Date de dépôt",
  "Aktendatum",
  "Fecha de archivo",
  "تاريخ الملف"
 ],
 "Procedimento giudiziario": [
  "Court case",
  "Affaire judiciaire",
  "Gerichtsfall",
  "Causa procesal",
  "قضية محكمة"
 ],
 "Indirizzo crypto": [
  "Crypto address",
  "Crypto address",
  "Crypto address",
  "Crypto address",
  "Crypto address"
 ],
 "Chiave privata": [
  "Private key",
  "Clé privée",
  "Privater Schlüssel",
  "Private key",
  "Private key"
 ],
 "Id conto": [
  "Account ID",
  "Account ID",
  "Account ID",
  "Account ID",
  "Account ID"
 ],
 "Data di creazione": [
  "Creation date",
  "Date de création",
  "Creation date",
  "Creation date",
  "Creation date"
 ],
 "Codice valuta": [
  "Currency short code",
  "Code monnaie",
  "Currency short code",
  "Currency short code",
  "Currency short code"
 ],
 "Blockchain": [
  "Blockchain",
  "Blockchain",
  "Blockchain",
  "Blockchain",
  "Blockchain"
 ],
 "Borsa di quotazione": [
  "Managing exchange",
  "Bourse de gestion",
  "Managing exchange",
  "Managing exchange",
  "Managing exchange"
 ],
 "Tipo di custodia": [
  "Custody type",
  "Custody type",
  "Custody type",
  "Custody type",
  "Custody type"
 ],
 "Wallet di criptovalute": [
  "Cryptocurrency wallet",
  "Portefeuille de cryptomonnaies",
  "Kryptowährungs-Wallet",
  "Cryptocurrency wallet",
  "Cryptocurrency wallet"
 ],
 "Checksum": [
  "Checksum",
  "Somme de contrôle",
  "Prüfsumme",
  "Comprobación",
  "المجموع الاختباري"
 ],
 "Generatore": [
  "Generator",
  "Générateur",
  "Erzeuger",
  "Generador",
  "مولد (منتج)"
 ],
 "Crawler": [
  "Crawler",
  "Collecteur",
  "Scraper",
  "Rastreador",
  "محرك بحث "
 ],
 "Estensione": [
  "File extension",
  "Extension du fichier",
  "Dateiendung",
  "Extensión del archivo",
  "إمتداد الملف"
 ],
 "Codifica del file": [
  "File encoding",
  "Encodage du fichier",
  "Dateikodierung",
  "Codificación de archivo",
  "ترميز الملف"
 ],
 "Agente di elaborazione": [
  "Processing agent",
  "Processing agent",
  "Processing agent",
  "Processing agent",
  "Processing agent"
 ],
 "File": [
  "File",
  "Fichier",
  "Datei",
  "Archivo",
  "ملف"
 ],
 "Numero dichiarazione doganale": [
  "Customs Cargo Declaration Number",
  "Numéro de déclaration de chargement des douanes (CCD)",
  "Zoll Waren-Erklärungsnummer",
  "Número de declaración de carga en aduana",
  "رقم بيان / تخليص  البضائع الجمركية"
 ],
 "Valore dichiarazione doganale": [
  "CCD Value",
  "Valeur du CCD",
  "CCD-Wert",
  "Valor CCD",
  "قيمة الشحن"
 ],
 "Direzione del trasporto": [
  "Direction of transportation",
  "Direction du transport",
  "Transportrichtung",
  "Dirección de transporte",
  "اتجاه النقل"
 ],
 "Procedura doganale": [
  "Customs Procedure",
  "Procédure douanière",
  "Zollverfahren",
  "Procedimiento aduanero",
  "الإجراءات الجمركية"
 ],
 "Codice FEAC": [
  "FEAC Code",
  "Code FEAC",
  "FEAC-Code",
  "Código FEAC",
  "كود FEAC"
 ],
 "Descrizione codice FEAC": [
  "FEAC Code description",
  "Description du code FEAC",
  "Beschreibung des FEAC-Codes",
  "Descripción del código FEAC",
  "وصف كود FEAC"
 ],
 "Descrizione delle merci": [
  "Description of goods",
  "Description des marchandises",
  "Beschreibung der Güter",
  "Descripción de los bienes",
  "وصف البضائع"
 ],
 "Valore fattura": [
  "Invoice Value Amount",
  "Montant de la valeur facturée",
  "Rechnungswert",
  "Monto de la factura",
  "مبلغ قيمة الفاتورة"
 ],
 "Valore doganale": [
  "Customs Value Amount",
  "Montant de la valeur douanière",
  "Zollwarenwert",
  "Valor aduanero",
  "مقدار القيمة الجمركية"
 ],
 "Cambio in USD": [
  "USD Exchange Rate",
  "Taux de change de l’USD",
  "US-Dollar Tauschkurs",
  "Tipo de cambio de USD",
  "سعر صرف الدولار الأمريكي"
 ],
 "Paese di scambio": [
  "Trading Country",
  "Pays de l’opération commerciale",
  "Handelsland",
  "País de la empresa",
  "بلد تجاري"
 ],
 "Paese di partenza": [
  "Country of departure",
  "Pays de départ",
  "Ursprungsland",
  "País de salida",
  "بلد المغادرة"
 ],
 "Paese di destinazione": [
  "Country of destination",
  "Pays de destination",
  "Zielland",
  "País de destino",
  "بلد الوجهة أو الوصول"
 ],
 "Dichiarazione doganale": [
  "Customs declaration",
  "Déclaration douanière",
  "Zollerklärungen",
  "Declaración de aduana",
  "بيان أو إقرار او تخليص جمركي"
 ],
 "Sintesi": [
  "Summary",
  "Résumé",
  "Zusammenfassung",
  "Resumen",
  "ملخص"
 ],
 "Luogo": [
  "Location",
  "Emplacement",
  "Ort",
  "Ubicación",
  "الموقع"
 ],
 "Importante": [
  "Important",
  "Important",
  "Wichtig",
  "Importante",
  "مهم"
 ],
 "Evento": [
  "Event",
  "Événement",
  "Ereignis",
  "Evento",
  "حدث"
 ],
 "Cartella": [
  "Folder",
  "Dossier",
  "Ordner",
  "Carpeta",
  "مجلد"
 ],
 "Numero del documento": [
  "Document number",
  "Numéro de document",
  "Dokumentennummer",
  "Número de documento",
  "رقم المستند"
 ],
 "Autorità": [
  "Authority",
  "Autorité",
  "Behörde",
  "Autoridad",
  "سلطة"
 ],
 "Identificazione": [
  "Identification",
  "Identification",
  "Identification",
  "Identification",
  "Identification"
 ],
 "Soggetto giuridico": [
  "Legal entity",
  "Entité juridique",
  "Rechtsperson",
  "Persona jurídica",
  "كيان قانوني"
 ],
 "Area": [
  "Area",
  "Surface",
  "Fläche",
  "Área",
  "المنطقة"
 ],
 "Merci": [
  "Commodities",
  "Commodités",
  "Rohstoffe",
  "Productos básicos",
  "بضاعة"
 ],
 "Data di revisione della licenza": [
  "License review date",
  "Date d’examen de la licence",
  "Lizenzprüfdatum",
  "Fecha de revisión de la licencia",
  "تاريخ مراجعة الترخيص"
 ],
 "Licenza": [
  "License",
  "Licence",
  "Lizenz",
  "Licencia",
  "رخصة"
 ],
 "Menzione": [
  "Mention",
  "Mention",
  "Erwähnung",
  "Mention",
  "أشير إلى"
 ],
 "Oggetto": [
  "Subject",
  "Objet",
  "Betreff",
  "Tema",
  "الموضوع"
 ],
 "Argomento della discussione": [
  "Thread topic",
  "Sujet de la conversation",
  "Thread-Thema",
  "Tema del hilo",
  "سلسلة الموضوع"
 ],
 "Messaggio": [
  "Message",
  "Message",
  "Nachricht",
  "Mensaje",
  "رسالة"
 ],
 "Organizzazione": [
  "Organization",
  "Organisation",
  "Organisation",
  "Organización",
  "منظمة"
 ],
 "Pacchetto": [
  "Package",
  "Pack",
  "Archiv",
  "Paquete",
  "حزمة"
 ],
 "Indice": [
  "Index",
  "Index",
  "Index",
  "Índice",
  "فهرس"
 ],
 "Pagina": [
  "Page",
  "Page",
  "Seite",
  "Página",
  "صفحة"
 ],
 "Documento": [
  "Document",
  "Document",
  "Dokument",
  "Documento",
  "المستند"
 ],
 "Data di nascita": [
  "Birth date",
  "Date de naissance",
  "Geburtsdatum",
  "Fecha de nacimiento",
  "تاريخ الميلاد"
 ],
 "Luogo di nascita": [
  "Place of birth",
  "Lieu de naissance",
  "Geburtsort",
  "Lugar de nacimiento",
  "مكان الولادة"
 ],
 "Sesso": [
  "Gender",
  "Sexe",
  "Gender",
  "Sexo",
  "الجنس"
 ],
 "Numero personale": [
  "Personal number",
  "Numéro d’identification personnel",
  "Personalnummer",
  "Número personal",
  "رقم شخصي"
 ],
 "Passaporto": [
  "Passport",
  "Passeport",
  "Reisepass",
  "Pasaporte",
  "جواز سفر"
 ],
 "File di testo": [
  "Text file",
  "Fichier texte",
  "Textdatei",
  "Archivo de texto",
  "ملف النص"
 ],
 "Area subnazionale": [
  "Subnational area",
  "Subnational area",
  "Subnational area",
  "Subnational area",
  "Subnational area"
 ],
 "Numero totale di seggi": [
  "Total number of seats",
  "Total number of seats",
  "Total number of seats",
  "Total number of seats",
  "Total number of seats"
 ],
 "Incarico / posizione": [
  "Position",
  "Profession",
  "Stellung",
  "Cargo",
  "الوضع"
 ],
 "Id progetto": [
  "Project ID",
  "Identifiant du projet",
  "Projekt-Kennung",
  "Project ID",
  "Project ID"
 ],
 "Fase": [
  "Phase",
  "Phase",
  "Phase",
  "Phase",
  "Phase"
 ],
 "Obiettivo del progetto": [
  "Project goal",
  "But du projet",
  "Projektziel",
  "Project goal",
  "Project goal"
 ],
 "Progetto": [
  "Project",
  "Projet",
  "Projekt",
  "Project",
  "Project"
 ],
 "Ente pubblico": [
  "Public body",
  "Entité publique",
  "Behörde",
  "Entidad pública",
  "هيئة عامة"
 ],
 "Latitudine": [
  "Latitude",
  "Latitude",
  "Breitengrad",
  "Latitud",
  "خط العرض"
 ],
 "Longitudine": [
  "Longitude",
  "Longitude",
  "Längengrad",
  "Longitud",
  "خط الطول"
 ],
 "Sezione di censimento": [
  "Census block",
  "Îlot de recensement",
  "Zensusblock",
  "Bloque de censo",
  "مجموعة التعداد السكاني"
 ],
 "Codice catastale": [
  "Cadastral code",
  "Référence cadastrale",
  "Katasternummer",
  "Código catastral",
  "كود المساحة"
 ],
 "Numero di titolo": [
  "Title number",
  "Numéro de titre",
  "Besitzrechtsnummer",
  "Número del título",
  "رقم العنوان"
 ],
 "Durata dell'incarico": [
  "Tenure",
  "Bail",
  "Pacht",
  "Tenencia",
  "ملكية / حيازة"
 ],
 "Gravame": [
  "Encumbrance",
  "Charge",
  "Belastung",
  "Gravamen",
  "عبء"
 ],
 "Tipo di immobile": [
  "Property type",
  "Type de bien",
  "Eigentumsart",
  "Tipo de propiedad",
  "نوع الملكية"
 ],
 "Tipo di terreno": [
  "Land type",
  "Type de terrain",
  "Landart",
  "Tipo de tierra",
  "نوع الأرض"
 ],
 "Data del record": [
  "Record date",
  "Date d’enregistrement",
  "Eintragsdatum",
  "Fecha de registro",
  "تاريخ التسجيل"
 ],
 "Immobile": [
  "Real estate",
  "Immobilier",
  "Grundstück",
  "Bienes raíces",
  "عقار"
 ],
 "Programma": [
  "Program",
  "Programme",
  "Programm",
  "Programa",
  "برنامج"
 ],
 "Id programma": [
  "Program ID",
  "Program ID",
  "Program ID",
  "Program ID",
  "Program ID"
 ],
 "URL programma": [
  "Program URL",
  "Program URL",
  "Program URL",
  "Program URL",
  "Program URL"
 ],
 "Temi": [
  "Topics",
  "Sujets",
  "Themen",
  "Temas",
  "المواضيع"
 ],
 "Motivo": [
  "Reason",
  "Raison",
  "Grund",
  "Motivo",
  "السبب"
 ],
 "Data di inserimento in lista": [
  "Listing date",
  "Date d’inscription",
  "Listing date",
  "Listing date",
  "Listing date"
 ],
 "Rischio": [
  "Risk",
  "Risk",
  "Risk",
  "Risk",
  "Risk"
 ],
 "Identificativo assegnato dall'autorità": [
  "Authority-issued identifier",
  "Identifiant émis par l’autorité",
  "Authority-issued identifier",
  "Authority-issued identifier",
  "Authority-issued identifier"
 ],
 "Identificativo ONU (Consiglio di sicurezza)": [
  "UN SC identifier",
  "Identifiant CS ONU",
  "UN SC identifier",
  "UN SC identifier",
  "UN SC identifier"
 ],
 "Ambito delle sanzioni": [
  "Scope of sanctions",
  "Portée des sanctions",
  "Scope of sanctions",
  "Scope of sanctions",
  "Scope of sanctions"
 ],
 "Sanzione": [
  "Sanction",
  "Sanction",
  "Sanktion",
  "Sanción",
  "عقوبة"
 ],
 "ISIN": [
  "ISIN",
  "ISIN",
  "ISIN",
  "ISIN",
  "ISIN"
 ],
 "Identificativo globale dello strumento (FIGI)": [
  "Financial Instrument Global Identifier",
  "Financial Instrument Global Identifier",
  "Financial Instrument Global Identifier",
  "Financial Instrument Global Identifier",
  "Financial Instrument Global Identifier"
 ],
 "Data di emissione": [
  "Date issued",
  "Date d’émission",
  "Date issued",
  "Date issued",
  "Date issued"
 ],
 "Data di scadenza": [
  "Maturity date",
  "Maturity date",
  "Maturity date",
  "Maturity date",
  "Maturity date"
 ],
 "Garanzia": [
  "Collateral",
  "Garantie",
  "Collateral",
  "Collateral",
  "Collateral"
 ],
 "Strumento finanziario": [
  "Security",
  "Valeur/Titre",
  "Security",
  "Security",
  "Security"
 ],
 "Punteggio di confidenza": [
  "Confidence score",
  "Confidence score",
  "Confidence score",
  "Confidence score",
  "Confidence score"
 ],
 "Criteri di confronto": [
  "Matching criteria",
  "Matching criteria",
  "Matching criteria",
  "Matching criteria",
  "Matching criteria"
 ],
 "Confrontatore": [
  "Matcher",
  "Matcher",
  "Matcher",
  "Matcher",
  "Matcher"
 ],
 "Simile": [
  "Similar",
  "Similar",
  "Similar",
  "Similar",
  "Similar"
 ],
 "Numero di righe": [
  "Number of rows",
  "Nombre de lignes",
  "Zeilenzahl",
  "Número de filas",
  "عدد الصفوف"
 ],
 "Tabella": [
  "Table",
  "Tableau",
  "Tabelle",
  "Tabla",
  "جدول"
 ],
 "Cognome": [
  "Surname",
  "Nom",
  "Nachname",
  "Apellido",
  "إسم العائلة"
 ],
 "Nome di battesimo": [
  "Given name",
  "Prénom",
  "Rufname",
  "Nombre",
  "الاسم "
 ],
 "Reddito dichiarato": [
  "Registered income",
  "Revenu déclaré",
  "Versteuertes Einkommen",
  "Ingreso registrado",
  "الدخل المسجل"
 ],
 "Imposte pagate": [
  "Amount of tax paid",
  "Montant de l’impôt payé",
  "Steuerzahlbetrag",
  "Monto de impuesto pagado",
  "مبلغ الضريبة المدفوعة"
 ],
 "Patrimonio dichiarato": [
  "Registered wealth",
  "Patrimoine déclaré",
  "Besteuerte Vermögenswerte",
  "Fortuna registrada",
  "الثروة المسجلة"
 ],
 "Dichiarazione fiscale": [
  "Tax roll",
  "Registre fiscal",
  "Steuererklärung",
  "Registro fiscal",
  "كشف الضرائب"
 ],
 "Livello": [
  "Level",
  "Level",
  "Level",
  "Level",
  "Level"
 ],
 "Codice territorio": [
  "Territory code",
  "Territory code",
  "Territory code",
  "Territory code",
  "Territory code"
 ],
 "Codice FIPS": [
  "FIPS code",
  "FIPS code",
  "FIPS code",
  "FIPS code",
  "FIPS code"
 ],
 "CAP": [
  "ZIP code",
  "ZIP code",
  "ZIP code",
  "ZIP code",
  "ZIP code"
 ],
 "Territorio": [
  "Territory",
  "Territory",
  "Territory",
  "Territory",
  "Territory"
 ],
 "Viaggio": [
  "Trip",
  "Trip",
  "Trip",
  "Trip",
  "Trip"
 ],
 "Numero CRS": [
  "CRS Number",
  "Numéro CRS",
  "CRS-Nummer",
  "Número de CRS",
  "رقم التقارير المجمعة CRS"
 ],
 "Bandiera": [
  "Flag",
  "Pavillon",
  "Flagge",
  "Marca",
  "علم"
 ],
 "Porto di immatricolazione": [
  "Port of Registration",
  "Port d’immatriculation",
  "Anmeldehafen",
  "Puerto de registro",
  "ميناء التسجيل"
 ],
 "Area di navigazione": [
  "Navigation Area",
  "Zone de navigation",
  "Navigationsgebiet",
  "Área de navegación",
  "منطقة الملاحة"
 ],
 "Stazza": [
  "Tonnage",
  "Tonnage",
  "Tonnage",
  "Tonelaje",
  "حمولة"
 ],
 "Stazza lorda (GRT)": [
  "Gross Registered Tonnage",
  "Jauge brute enregistrée",
  "Bruttoregistertonnen",
  "Tonelaje bruto registrado",
  "الحمولة الإجمالية المسجلة"
 ],
 "Portata lorda (DWT)": [
  "Deadweight Tonnage",
  "Deadweight Tonnage",
  "Deadweight Tonnage",
  "Deadweight Tonnage",
  "Deadweight Tonnage"
 ],
 "Data del cambio di nome": [
  "Date of Name Change",
  "Date du changement de nom",
  "Datum der Namensänderung",
  "Fecha de cambio de nombre",
  "تاريخ تغيير الاسم"
 ],
 "Nominativo radio": [
  "Call Sign",
  "Indicatif",
  "Rufzeichen",
  "Señal de identificación",
  "علامة إتصال"
 ],
 "Bandiere precedenti": [
  "Past Flags",
  "Pavillons précédents",
  "Vorherige Ausflaggung",
  "Marcas Past",
  "الأعلام السابقة"
 ],
 "Tipi precedenti": [
  "Past Types",
  "Types précédents",
  "Vorherige Typen",
  "Tipo Past",
  "الأنواع السابقة"
 ],
 "MMSI": [
  "MMSI",
  "MMSI",
  "MMSI",
  "MMSI",
  "هوية الخدمة المتنقلة البحرية MMSI"
 ],
 "Nave": [
  "Vessel",
  "Vaisseau",
  "Schiff",
  "Embarcación",
  "سفينة"
 ],
 "Video": [
  "Video",
  "Vidéo",
  "Video",
  "Video",
  "فيديو"
 ],
 "Cartella di lavoro": [
  "Workbook",
  "Classeur",
  "Arbeitsmappe",
  "Libro de trabajo",
  "كتاب عمل"
 ]
}

# schema FtM <-> tipo di OsintGraph (per importazione ed esportazione)
FTM_SCHEMA_OF = {
 "airplane": "Airplane",
 "article": "Article",
 "asset": "Asset",
 "audio": "Audio",
 "ftmbankaccount": "BankAccount",
 "call": "Call",
 "callfortenders": "CallForTenders",
 "company": "Company",
 "contract": "Contract",
 "courtcase": "CourtCase",
 "cryptowallet": "CryptoWallet",
 "ftmdocument": "Document",
 "economicactivity": "EconomicActivity",
 "ftmevent": "Event",
 "folder": "Folder",
 "identification": "Identification",
 "legalentity": "LegalEntity",
 "license": "License",
 "mention": "Mention",
 "message": "Message",
 "ftmorganization": "Organization",
 "package": "Package",
 "page": "Page",
 "pages": "Pages",
 "passport": "Passport",
 "plaintext": "PlainText",
 "position": "Position",
 "project": "Project",
 "publicbody": "PublicBody",
 "realestate": "RealEstate",
 "risk": "Risk",
 "sanction": "Sanction",
 "security": "Security",
 "similar": "Similar",
 "table": "Table",
 "taxroll": "TaxRoll",
 "territory": "Territory",
 "trip": "Trip",
 "vessel": "Vessel",
 "video": "Video",
 "workbook": "Workbook"
}
FTM_TYPE_OF = {
 "Airplane": "airplane",
 "Article": "article",
 "Asset": "asset",
 "Audio": "audio",
 "BankAccount": "ftmbankaccount",
 "Call": "call",
 "CallForTenders": "callfortenders",
 "Company": "company",
 "Contract": "contract",
 "CourtCase": "courtcase",
 "CryptoWallet": "cryptowallet",
 "Document": "ftmdocument",
 "EconomicActivity": "economicactivity",
 "Event": "ftmevent",
 "Folder": "folder",
 "Identification": "identification",
 "LegalEntity": "legalentity",
 "License": "license",
 "Mention": "mention",
 "Message": "message",
 "Organization": "ftmorganization",
 "Package": "package",
 "Page": "page",
 "Pages": "pages",
 "Passport": "passport",
 "PlainText": "plaintext",
 "Position": "position",
 "Project": "project",
 "PublicBody": "publicbody",
 "RealEstate": "realestate",
 "Risk": "risk",
 "Sanction": "sanction",
 "Security": "security",
 "Similar": "similar",
 "Table": "table",
 "TaxRoll": "taxroll",
 "Territory": "territory",
 "Trip": "trip",
 "Vessel": "vessel",
 "Video": "video",
 "Workbook": "workbook"
}
