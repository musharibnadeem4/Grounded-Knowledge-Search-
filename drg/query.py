"""Query parsing for the optional company / year filter (config.YEAR_COMPANY_FILTER)."""
import csv
import re
from pathlib import Path

# canonical name (== manifest `company`) -> aliases
ALIASES = {
    "PepsiCo": ["PepsiCo", "Pepsi"],
    "Best Buy": ["Best Buy"],
    "MGM Resorts": ["MGM Resorts", "MGM"],
    "Ulta Beauty": ["Ulta Beauty", "Ulta"],
    "Johnson & Johnson": ["Johnson & Johnson", "J&J", "JnJ"],
    "Pfizer": ["Pfizer"],
    "3M": ["3M", "MMM"],
    "Boeing": ["Boeing"],
    "AMD": ["AMD"],
    "Adobe": ["Adobe"],
    "Corning": ["Corning"],
    "Verizon": ["Verizon"],
}

_COMPANY_RES = []
for _name, _aliases in ALIASES.items():
    # longest alias first; spaces may be any whitespace; word boundaries on both sides
    _alts = "|".join(re.escape(a).replace(r"\ ", r"\s+")
                     for a in sorted(_aliases, key=len, reverse=True))
    _COMPANY_RES.append((_name, re.compile(rf"(?<!\w)(?:{_alts})(?!\w)", re.I)))

_YEAR_LO, _YEAR_HI = 2010, 2030
# FY2022 / FY 2022 / FY22 / fiscal 2022 / fiscal year 2022 / fiscal 22
_FY = re.compile(r"(?<!\w)(?:FY|fiscal(?:\s+year)?)\s*'?(\d{4}|\d{2})(?!\d)", re.I)
# bare 4-digit year; not part of a longer number like 12,2022 or 2022.5
_BARE = re.compile(r"(?<![\d,.])(20[123]\d)(?![\d]|,\d|\.\d)")


def parse_query(q):
    """-> (companies: set[str] canonical names, year: int | None). Several years -> max."""
    companies = {name for name, rx in _COMPANY_RES if rx.search(q)}
    years = []
    for m in _FY.finditer(q):
        y = int(m.group(1))
        years.append(y if y >= 100 else 2000 + y)
    years += [int(m.group(1)) for m in _BARE.finditer(q)]
    years = [y for y in years if _YEAR_LO <= y <= _YEAR_HI]
    return companies, (max(years) if years else None)


def load_periods(manifest_path):
    """{company: {period strings}} from the manifest."""
    out = {}
    with open(Path(manifest_path), newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            out.setdefault(r["company"].strip(), set()).add(r["period"].strip())
    return out


def company_periods(periods, year):
    """Periods to filter one company on, or None for no year filter.
    period == year if the company has it; else period in {year+1, year+2}; else None."""
    if str(year) in periods:
        return [str(year)]
    later = [str(y) for y in (year + 1, year + 2) if str(y) in periods]
    return later or None


def build_where(allowed, companies, year, periods_by_company):
    """Single Chroma `where`. Never wider than `allowed`: the role filter is
    AND-ed on top, and the company set is parsed ∩ allowed (or allowed if empty).
    Returns (where, chosen_companies)."""
    chosen = [c for c in allowed if c in companies] or list(allowed)
    role = {"company": {"$in": list(allowed)}}
    if year is None:
        if len(chosen) == len(allowed):
            return role, chosen
        return {"$and": [role, {"company": {"$in": chosen}}]}, chosen
    clauses = []
    for c in chosen:
        ps = company_periods(periods_by_company.get(c, set()), year)
        clauses.append({"$and": [{"company": c}, {"period": {"$in": ps}}]} if ps
                       else {"company": c})
    inner = clauses[0] if len(clauses) == 1 else {"$or": clauses}
    return {"$and": [role, inner]}, chosen
