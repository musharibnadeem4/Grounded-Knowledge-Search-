"""Detect exhibit-index / signature boilerplate (for config.DROP_BOILERPLATE)."""
import re

MIN_CHARS = 80  # chunks with fewer stripped characters are dropped
EXHIBIT_LINE_FRACTION = 0.4  # rule 2 threshold

# page header starts with ...
_HEADER_START = re.compile(r"^\s*(?:exhibit|item\s+15|signatures)\b", re.I)
# a line that starts with an exhibit number: 10.19, *10.25, ***10.58, 31.1, 32.2
_EXHIBIT_NO = re.compile(r"^\s*[*†‡]*\d{1,3}\.\d{1,3}(?:\.\d{1,3})?[*†‡]*(?=\s)")


def _lines(text):
    return [ln for ln in (text or "").splitlines() if ln.strip()]


def exhibit_lines(text):
    """(matching exhibit-number lines, non-empty lines)."""
    ls = _lines(text)
    return sum(bool(_EXHIBIT_NO.match(ln)) for ln in ls), len(ls)


def exhibit_page(header, text):
    """True for exhibit-index / signature pages. `header` is the page header (first two
    non-empty lines after cleaning), `text` the page text or a chunk of it.
      1. header starts with Exhibit / Item 15 / SIGNATURES, or
      2. >= 40% of the lines start with an exhibit number, or
      3. the header itself starts with an exhibit number and >= 2 lines do: exhibit entries
         wrap over 2-3 lines, so real index pages often stay below 40% of lines."""
    if _HEADER_START.match(header or ""):
        return True
    hits, total = exhibit_lines(text)
    if total and hits / total >= EXHIBIT_LINE_FRACTION:
        return True
    return bool(_EXHIBIT_NO.match(header or "")) and hits >= 2


def is_boilerplate(header, text):
    """(reason | None). 'short' = under 80 stripped chars; 'exhibit' = exhibit/signature page."""
    if len((text or "").strip()) < MIN_CHARS:
        return "short"
    if exhibit_page(header, text):
        return "exhibit"
    return None
