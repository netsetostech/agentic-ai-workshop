"""India's four identifiers a question may carry, checked by their own arithmetic (workshop lesson 5.6). Stdlib only.

    Aadhaar   12 digits, the first 2 to 9, the last a Verhoeff check digit (UIDAI's scheme)
    card      13 to 19 digits, a payment network's first digit, the last a Luhn check digit (ISO/IEC 7812)
    PAN       AAAPA9999A: five letters, four digits, a letter; the fourth letter is the holder's type
    GSTIN     a 2-digit state code, the holder's PAN, an entity number, Z, and a mod-36 check character

A pattern alone is not a number: "2234 5678 9012" has an Aadhaar's shape, and lesson 4.8 types it as a synthetic
example, but its Verhoeff check fails, so it is not one. The check digit and the printed grouping are what separate
an identifier from an invoice number, a phone number with a country code, a date range or an amount, which is why the
masking in shared/desk_rules.py masks only what passes both. One figure in ten printed 4-4-4 passes Verhoeff by
chance; the masking takes it for an Aadhaar, the safer mistake.

The gateway's classifier (services/litellm/documind_classifier.py) keeps its own regexes: the litellm image builds
from services/litellm/ and cannot import shared/. The test vectors in commands/tests/test_desk_rules.py are the ones
to run through both.
"""
from __future__ import annotations

import re
import unicodedata

# ---------------------------------------------------------------- Verhoeff (the dihedral group D5)
_D = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 2, 3, 4, 0, 6, 7, 8, 9, 5),
    (2, 3, 4, 0, 1, 7, 8, 9, 5, 6),
    (3, 4, 0, 1, 2, 8, 9, 5, 6, 7),
    (4, 0, 1, 2, 3, 9, 5, 6, 7, 8),
    (5, 9, 8, 7, 6, 0, 4, 3, 2, 1),
    (6, 5, 9, 8, 7, 1, 0, 4, 3, 2),
    (7, 6, 5, 9, 8, 2, 1, 0, 4, 3),
    (8, 7, 6, 5, 9, 3, 2, 1, 0, 4),
    (9, 8, 7, 6, 5, 4, 3, 2, 1, 0),
)
_P = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 5, 7, 6, 2, 8, 3, 0, 9, 4),
    (5, 8, 0, 3, 7, 9, 6, 1, 4, 2),
    (8, 9, 1, 6, 0, 4, 3, 5, 2, 7),
    (9, 4, 5, 3, 1, 2, 6, 8, 7, 0),
    (4, 2, 8, 6, 5, 7, 3, 9, 0, 1),
    (2, 7, 9, 3, 8, 0, 6, 4, 1, 5),
    (7, 0, 4, 6, 9, 1, 3, 2, 5, 8),
)
_INV = (0, 4, 3, 2, 1, 5, 6, 7, 8, 9)


def verhoeff_valid(digits: str) -> bool:
    """True when the last digit is the Verhoeff check digit of the rest."""
    if not digits.isdigit():
        return False
    c = 0
    for i, ch in enumerate(reversed(digits)):
        c = _D[c][_P[i % 8][int(ch)]]
    return c == 0


def verhoeff_digit(digits: str) -> str:
    """The check digit to append to `digits` (for building test numbers, never for guessing real ones)."""
    c = 0
    for i, ch in enumerate(reversed(digits)):
        c = _D[c][_P[(i + 1) % 8][int(ch)]]
    return str(_INV[c])


# ---------------------------------------------------------------- Luhn
def luhn_valid(digits: str) -> bool:
    """True when the last digit is the Luhn check digit of the rest."""
    if not digits.isdigit() or len(digits) < 2:
        return False
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


# ---------------------------------------------------------------- the numbers, in running text
# A run is digits (any script's: Devanagari ०-९ and full-width ０-９ are digits too) joined by at most three separators
# each - spaces of any kind (a no-break space pasted from a PDF), ".", "/", "-" or a dash - on one line. A run that
# touches a letter, or follows "+" (a phone number's country code), is not a number. Inside a run, a number is either
# one unbroken digit string of the right length, or digit groups in the identifier's printed grouping (Aadhaar
# 4-4-4; a card 4-4-4-4, 4-4-4-4-3, 4-6-5 or 4-6-4) with one separator throughout. So a date range ("31.08.2024 -
# 01.07.2025", two separators), a phone number ("91 93487 17536") or a list of figures ("68846 / 74258 / 61887", no
# identifier's grouping) is never joined into one, whatever its digits add up to. Invisible format characters (a soft hyphen, a zero-width space) are not
# separators: the digits on either side of one are one group. The longest number from a group wins, so
# "4111 1111 1111 1111" is one card and never an Aadhaar-shaped piece of it, and an Aadhaar that ends a sentence
# before another figure ("... 0124. 5 people") is still found.
_CF = "\u00ad\u200b-\u200f\u2060\ufeff"
_SEP = r"(?:[^\S\r\n]|[./\-\u2010-\u2015\u2212" + _CF + r"]){1,3}"
_RUN = re.compile(r"\d(?:(?:" + _SEP + r")?\d)*")
_GROUP = re.compile(r"\d+")
_CF_RE = re.compile("[" + _CF + "]")
GROUPINGS = {"aadhaar": {(4, 4, 4)}, "card": {(4, 4, 4, 4), (4, 4, 4, 4, 3), (4, 6, 5), (4, 6, 4)}}
CARD_FIRST = "234568"      # the payment networks' first digits: Mastercard 2 and 5, Amex, Diners and JCB 3, Visa 4,
                           # RuPay, Discover and Maestro 6, RuPay 8; a 0, 1, 7 or 9 is an id (a storage generation)


def _digits(s: str) -> str:
    """The ASCII digits of s, whatever script they were typed in; every other character dropped."""
    return "".join(str(unicodedata.digit(ch)) for ch in s if unicodedata.digit(ch, None) is not None)


def _aadhaar_digits(d: str) -> bool:
    return len(d) == 12 and d[0] in "23456789" and verhoeff_valid(d)


def _card_digits(d: str) -> bool:
    return 13 <= len(d) <= 19 and d[0] in CARD_FIRST and luhn_valid(d)


def is_aadhaar(s: str) -> bool:
    """12 digits (separators allowed), the first 2 to 9, Verhoeff-valid."""
    return _aadhaar_digits(_digits(s))


def is_card(s: str) -> bool:
    """13 to 19 digits (separators allowed), a payment network's first digit, Luhn-valid."""
    return _card_digits(_digits(s))


def _sep(between: str) -> str | None:
    """One separator, normalised: "" when only format characters stand between two groups (they are one group),
    " " for spaces of any kind, else the one punctuation mark, spaced or not ("-" and " - " alike). None for two
    marks ("./"), which no printed identifier puts between its groups."""
    t = _CF_RE.sub("", between)
    if not t:
        return ""
    core = t.strip()
    if not core:
        return " "
    return core if len(core) == 1 else None


def _groups(text: str, a: int, run: str) -> list[tuple[int, int, str, str | None]]:
    """(start, end, ASCII digits, the separator before it) for each digit group of a run, with groups that only format
    characters divide merged into one."""
    out = []
    for g in _GROUP.finditer(run):
        start, end, digits = a + g.start(), a + g.end(), _digits(g.group(0))
        sep = _sep(text[out[-1][1]:start]) if out else None
        if out and sep == "":
            out[-1] = (out[-1][0], end, out[-1][2] + digits, out[-1][3])
        else:
            out.append((start, end, digits, sep))
    return out


def _kind(digits: str, lengths: tuple[int, ...]) -> str | None:
    """The identifier these groups print, or None: one unbroken string, or the identifier's own grouping."""
    if _aadhaar_digits(digits) and (len(lengths) == 1 or lengths in GROUPINGS["aadhaar"]):
        return "aadhaar"
    if _card_digits(digits) and (len(lengths) == 1 or lengths in GROUPINGS["card"]):
        return "card"
    return None


def find_numbers(text: str) -> list[tuple[int, int, str]]:
    """(start, end, kind) for every Aadhaar and card number in text, kind "aadhaar" or "card", in order."""
    out = []
    for m in _RUN.finditer(text):
        a, b = m.start(), m.end()
        if (a and (text[a - 1].isalpha() or text[a - 1] in "+_")) or (b < len(text) and (text[b].isalpha() or text[b] == "_")):
            continue
        groups = _groups(text, a, m.group(0))
        i = 0
        while i < len(groups):
            hit, digits, lengths = None, "", ()
            for j in range(i, min(len(groups), i + 5)):   # at most five groups from group i on: a bounded look-ahead
                if j > i and (groups[j][3] is None or groups[j][3] != groups[i + 1][3]):
                    break                                  # one separator throughout, or no number
                digits += groups[j][2]
                lengths += (len(groups[j][2]),)
                if len(digits) > 19:
                    break
                kind = _kind(digits, lengths)
                if kind:
                    hit = (groups[i][0], groups[j][1], kind, j)   # keep looking: the longest number wins
            if hit:
                out.append(hit[:3])
                i = hit[3] + 1
            else:
                i += 1
    return out


# ---------------------------------------------------------------- PAN and GSTIN
# The fourth letter of a PAN is the holder's type: P person, C company, H HUF, F firm, A AOP, T trust, B BOI,
# L local authority, J artificial juridical person, G government.
PAN = re.compile(r"(?<![A-Za-z0-9])[A-Z]{3}[ABCFGHJLPT][A-Z][0-9]{4}[A-Z](?![A-Za-z0-9])")
GSTIN = re.compile(r"(?<![A-Za-z0-9])[0-9]{2}[A-Z]{3}[ABCFGHJLPT][A-Z][0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z](?![A-Za-z0-9])")
_B36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def gstin_check_char(first14: str) -> str:
    """The 15th character of a GSTIN: each of the first 14 characters' base-36 value times 1 or 2 (alternately,
    from the left), each product's quotient and remainder by 36 summed, and (36 - sum mod 36) mod 36."""
    total = 0
    for i, ch in enumerate(first14.upper()):
        prod = _B36.index(ch) * (2 if i % 2 else 1)
        total += prod // 36 + prod % 36
    return _B36[(36 - total % 36) % 36]


def is_pan(s: str) -> bool:
    return bool(PAN.fullmatch(s))


def is_gstin(s: str) -> bool:
    """The GSTIN pattern, a state code from 01 to 38 (or 97 and 99, the other territory and the centre's
    jurisdiction codes), and the mod-36 check character."""
    if not GSTIN.fullmatch(s):
        return False
    state = int(s[:2])
    return (1 <= state <= 38 or state in (97, 99)) and gstin_check_char(s[:14]) == s[14]


def find_pan_gstin(text: str) -> list[tuple[int, int, str]]:
    """(start, end, kind) for every PAN ("pan") and checked GSTIN ("gstin") in text. rag-api lets both pass, as it
    always has; the finder is here so every surface names them the same way."""
    out = [(m.start(), m.end(), "gstin") for m in GSTIN.finditer(text) if is_gstin(m.group(0))]
    taken = [(a, b) for a, b, _ in out]
    out += [(m.start(), m.end(), "pan") for m in PAN.finditer(text)
            if not any(a <= m.start() < b for a, b in taken)]
    return sorted(out)
