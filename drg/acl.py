"""Desk -> company access control. Company names must equal the manifest's `company` column."""
import csv
from pathlib import Path

_BASE = {
    "consumer": ["PepsiCo", "Best Buy", "MGM Resorts", "Ulta Beauty"],
    "health_industrials": ["Johnson & Johnson", "Pfizer", "3M", "Boeing"],
    "tech_telecom": ["AMD", "Adobe", "Corning", "Verizon"],
}
DESK_COMPANIES = {**_BASE, "lead": [c for cs in _BASE.values() for c in cs]}


class UnknownRole(ValueError):
    pass


def allowed_companies(role):
    try:
        return list(DESK_COMPANIES[role])
    except KeyError:
        raise UnknownRole(
            f"unknown role {role!r}; expected one of {sorted(DESK_COMPANIES)}") from None


def check_manifest(manifest_path):
    """Assert DESK_COMPANIES uses exactly the manifest's company names, and that
    each company sits on the desk the manifest says."""
    with open(Path(manifest_path), newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    manifest_companies = {r["company"].strip() for r in rows}
    ours = set(DESK_COMPANIES["lead"])
    assert len(DESK_COMPANIES["lead"]) == 12 and len(ours) == 12, "lead must list 12 companies"
    assert ours == manifest_companies, (
        f"ACL company names differ from manifest: only in ACL={sorted(ours - manifest_companies)}, "
        f"only in manifest={sorted(manifest_companies - ours)}")
    for r in rows:
        assert r["company"].strip() in DESK_COMPANIES.get(r["desk"].strip(), []), (
            f"{r['doc_id']}: company {r['company']!r} not on desk {r['desk']!r} in ACL")
