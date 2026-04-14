# ---------------------------------------------------------------------------
# Multilingual aliases — canonical key → recognized header names
# After normalization (lowercase, accent-stripped), these are matched.
# ---------------------------------------------------------------------------

HEADER_ALIASES: dict[str, list[str]] = {
    "date": ["fecha", "date", "data", "datum"],
    "value_date": ["valor", "value date", "data valor", "valuta", "wertstellung"],
    "description": ["observaciones", "description", "descricao", "beschreibung", "observations"],
    "amount": ["importe", "amount", "montante", "betrag", "montant"],
    "currency": ["divisa", "currency", "moeda", "wahrung", "devise"],
    "balance": ["saldo", "balance", "solde"],
    "movement_no": ["no mov", "n mov", "n. mov", "movement", "movimento", "mouvement", "bewegung", "movement no"],
    "branch": ["oficina", "branch", "agencia", "filiale", "succursale"],
    "category": ["categoria", "category", "categorie", "kategorie"],
    "subcategory": ["subcategoria", "subcategory", "sous categorie", "unterkategorie"],
    "detail": ["detalle", "detail", "detalhe", "details"],
    "invoice_no": ["no factura", "n factura", "n. factura", "invoice", "fatura", "facture", "rechnung"],
    "file_ref": ["referencia archivo factura", "file reference", "referencia arquivo"],
    "extra_data": ["datos", "dados", "donnees", "daten"],
    "ref": ["ref"],
}

REQUIRED_HEADERS = {"date", "amount"}

# Optional columns that determine import mode
CATEGORY_HEADERS = {"category", "subcategory"}

CATEGORY_SHEET_NAMES = {"categorias", "categories", "kategorien"}

INCOME_ALIASES = {"entrada", "income", "receita", "recette", "einnahme", "entrata"}
EXPENSE_ALIASES = {"gasto", "expense", "despesa", "depense", "ausgabe", "spesa"}

# Reverse lookup: normalized alias text → canonical key
_ALIAS_LOOKUP: dict[str, str] = {}
for _key, _aliases in HEADER_ALIASES.items():
    for _alias in _aliases:
        _ALIAS_LOOKUP[_alias] = _key
