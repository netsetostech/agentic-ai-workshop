"""Answer or refuse, asked of a System One model: TypeSafe AI's Jev (workshop lesson 2.6). Stdlib only.

The kit's first model that is not Google's. A System One model returns a typed decision - a choice, a score, a value
between 0 and 1 - with a calibrated probability, where a generator returns text. Lesson 2.6 asks it one question per
golden row: given the question and the passages retrieval found (rag-api's /v1/passages), answer or refuse? Jev sits
between rerank and generate in the diagram, but not on the request path: evals/decide.py is its only caller, beside
two arms that need no vendor - the kit's rule and the generator's own refusals.

What TypeSafe says about Jev, from its page in October 2026 (the author's notes, so the vendor's claims, not the kit's
measurements): launched on 15 September 2026; typed decisions with calibrated probabilities instead of text; early
access through console.typesafe.ai; a hosted API that runs outside Google Cloud; USD 42 per billion input tokens. Its
data retention and its hosting region are not documented. Its API documentation is not available to the kit yet either,
so this file holds no endpoint, no authentication scheme and no request or response shape: PR 2.6-C fills in the
adapter seam below once TypeSafe's docs and a key arrive, and until then live mode answers error, never a guess.

    JEV_MODE=off        the default: no call, no file read; every row is skipped ("Jev not available")
    JEV_MODE=recorded   evals/system_one/recorded.jsonl, one recorded decision per golden row id; nothing is sent
    JEV_MODE=live       TypeSafe's API, through the adapter seam; until PR 2.6-C, verdict error, NOT_CONFIGURED

decide(question, passages, row_id, tenant) returns one dict with RESULT_KEYS, always, and never raises:

    verdict     answer | refuse | skipped | error. skipped is no decision (the switch is off, there is no recording,
                the tenant's policy keeps its text home); error is a decision that failed. Neither is a refusal, and
                evals/decide.py scores neither as one
    score       Jev's calibrated probability that the passages answer the question, 0 to 1, or None
    reason      one line a person reads
    model, request_id, tokens ({"input", "output"}), ms, cost_usd      as the call reported them, or None
    source      off | recorded | live | policy (the tenant's data_region stopped it) | code (an empty pool)
    error       why the decision failed, or None

Four rules hold before anything could leave the kit:

1. An empty pool is refused by code, as rag-api refuses it (main.py's empty_pool_answer): nothing to judge, no call.
2. Only a tenant whose data_region is `any` is sent (shared/tenancy.py; make roster sets acme and zeta to any and
   globex to in), as the lesson plan rules. The policy is read live and fails closed: an unreadable or unknown policy
   is `in`. `in` keeps a tenant's text in India, and Jev's region is undocumented, so an `in` tenant is never sent.
   `any` was written for Google's managed stores (RAG Engine, Vertex AI Search); reading it as leave to send text to a
   vendor outside Google Cloud is the plan's rule, and where TypeSafe processes and keeps data is one of the terms
   asked of it (the lesson plan's decision 5).
3. Identifiers are masked: Aadhaar and card numbers by their check digits, PAN and checked GSTINs by their patterns
   (shared/identifiers.py). shared/desk_rules.mask() lets PAN and GSTIN pass because the kit's own model may read
   them; a vendor whose retention is undocumented may not.
4. The payload is the question and the passages' text, masked, and nothing else: no tenant, no person, no document
   name or id, no row id.

THE RECORDED FILE. evals/system_one/recorded.jsonl does not exist: no recording ships until one is made against
TypeSafe's API, and none is ever written by hand. While it is absent every recorded row is skipped with RECORDED_ABSENT
as its reason, and evals/decide.py prints the file's absence in its header. recording_errors() is the line's schema: a
line without the vendor's request_id and the time it was recorded is not a recording. Whether recordings may be
published at all is one of the terms asked of TypeSafe (the lesson plan's decision 5).

THE PRICE is TypeSafe's, not the kit's table: shared/prices.usd() bills an unknown model at flash's rate, USD 1.50 a
million input tokens, about 36 times the USD 42 a billion on Jev's page. _price() charges the input tokens at
USD_PER_1B_INPUT; the output tokens' price is not documented, so a decision that reports any is unpriced (None), never
priced by a guess.

THE ADAPTER SEAM (PR 2.6-C): _request() sends the payload and returns (HTTP status, body); _headers() carries
JEV_API_KEY, read from the environment and nowhere else (never a flag, a make variable or a file in the repository);
_parse() turns TypeSafe's body into {verdict, score, model, request_id, tokens}; _price() is filled now. Until the
adapter lands, _request() raises AdapterNotConfigured and decide() turns that into verdict error with NOT_CONFIGURED,
before any key is read and before any socket opens.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path

from shared import identifiers, tenancy

MODES = ("off", "recorded", "live")
VERDICTS = ("answer", "refuse", "skipped", "error")
RESULT_KEYS = ("verdict", "score", "reason", "model", "source", "ms", "tokens", "cost_usd", "error", "request_id")
KIT = Path(__file__).resolve().parents[1]
RECORDED = KIT / "evals" / "system_one" / "recorded.jsonl"
RECORDED_ABSENT = ("no recordings: evals/system_one/recorded.jsonl does not exist - none ship until decisions are "
                   "recorded against TypeSafe's API (PR 2.6-C), and none are written by hand")
NOT_CONFIGURED = "TypeSafe adapter not configured (PR 2.6-C)"
OFF_REASON = "JEV_MODE=off: Jev not available, nothing sent"
EMPTY_POOL = "empty pool: refused by code, as rag-api refuses it (empty_pool_answer); Jev not asked"
USD_PER_1B_INPUT = 42.0     # TypeSafe's page, October 2026: USD 42 per billion input tokens (the vendor's claim)
USD_PER_1B_OUTPUT = None    # not documented: a decision that reports output tokens is unpriced, never guessed
MASK_TEXT = {"aadhaar": "[Aadhaar]", "card": "[card no.]", "pan": "[PAN]", "gstin": "[GSTIN]"}


class AdapterNotConfigured(RuntimeError):
    """Live mode before PR 2.6-C: TypeSafe's endpoint, authentication and shapes are not in the kit yet."""


def result(verdict: str, *, score: float | None = None, reason: str = "", model: str | None = None,
           source: str = "off", ms: int | None = None, tokens: dict | None = None, cost_usd: float | None = None,
           error: str | None = None, request_id: str | None = None) -> dict:
    """One decision in the shape every arm of evals/decide.py shares. A verdict outside VERDICTS, or a score outside
    0 to 1, is a ValueError: decide() turns it into verdict error."""
    if verdict not in VERDICTS:
        raise ValueError(f"verdict {verdict!r} is not one of {'|'.join(VERDICTS)}")
    if score is not None and (isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 1):
        raise ValueError(f"score {score!r} is not a number from 0 to 1")
    return {"verdict": verdict, "score": None if score is None else float(score), "reason": reason, "model": model,
            "source": source, "ms": ms, "tokens": tokens, "cost_usd": cost_usd, "error": error,
            "request_id": request_id}


def mode(value: str | None = None) -> str:
    """JEV_MODE as decide() reads it, at call time: off when unset or empty, else the value lower-cased. A value
    outside MODES is returned as it is, so the caller can name it; decide() sends nothing for it."""
    v = os.environ.get("JEV_MODE", "") if value is None else value
    return (v or "off").strip().lower() or "off"


# ---------------------------------------------------------------- masking
def mask_identifiers(text: str) -> tuple[str, list[str]]:
    """(text with every checked Aadhaar and card number, PAN and checked GSTIN replaced, the kinds replaced, sorted).
    The finders are shared/identifiers.py's: a number counts only when its check digit and printed grouping say it is
    one, so an invoice number or a date range passes. Overlapping finds keep the first, longest one."""
    text = text or ""
    found = sorted(identifiers.find_numbers(text) + identifiers.find_pan_gstin(text), key=lambda f: (f[0], -f[1]))
    if not found:
        return text, []
    out, last, kinds = [], 0, set()
    for start, end, kind in found:
        if start < last:
            continue
        out += [text[last:start], MASK_TEXT[kind]]
        kinds.add(kind)
        last = end
    out.append(text[last:])
    return "".join(out), sorted(kinds)


def _payload(question: str, passages: list[dict]) -> tuple[dict, list[str]]:
    """(what would be sent, the identifier kinds masked in it): the question and each passage's text, masked, and
    nothing else. Retention and region are undocumented, so the least that answers the question is what goes."""
    q, kinds = mask_identifiers(str(question or ""))
    texts = []
    for p in passages:
        t, k = mask_identifiers(str((p or {}).get("text") or ""))
        texts.append(t)
        kinds = kinds + k
    return {"question": q, "passages": texts}, sorted(set(kinds))


# ---------------------------------------------------------------- the data-region policy
def _policy(tenant: str, policy_for=None) -> str:
    """The tenant's data_region: `any` only when the reader says exactly that, else `in`. policy_for defaults to
    shared/tenancy.policy_for (Firestore, failing closed itself); a reader that raises is `in` too."""
    try:
        read = policy_for or tenancy.policy_for
        got = str(read(tenant) or "").strip().lower()
    except Exception:  # noqa: BLE001 - the policy is a guard; when it cannot be read nothing leaves
        return "in"
    return got if got == "any" else "in"


# ---------------------------------------------------------------- the recorded file
def recording_errors(rec) -> list[str]:
    """Why a line of evals/system_one/recorded.jsonl is not a recording, or []. A recording is what TypeSafe's API
    returned for one golden row: it carries the vendor's request_id and the time it was recorded."""
    if not isinstance(rec, dict):
        return ["not a JSON object"]
    why = [f"{k} missing or empty" for k in ("id", "tenant", "model", "request_id", "recorded_at")
           if not isinstance(rec.get(k), str) or not rec.get(k).strip()]
    if rec.get("verdict") not in ("answer", "refuse"):
        why.append("verdict is not answer or refuse")
    score = rec.get("score")
    if score is not None and (isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 1):
        why.append("score is not a number from 0 to 1")
    if isinstance(rec.get("recorded_at"), str):
        try:
            datetime.fromisoformat(rec["recorded_at"].replace("Z", "+00:00"))
        except ValueError:
            why.append("recorded_at is not an ISO 8601 time")
    ms = rec.get("ms")
    if ms is not None and (isinstance(ms, bool) or not isinstance(ms, int) or ms < 0):
        why.append("ms is not a whole number of milliseconds")
    tokens = rec.get("tokens")
    if tokens is not None and not (isinstance(tokens, dict) and all(
            isinstance(tokens.get(k), int) and not isinstance(tokens.get(k), bool) and tokens[k] >= 0
            for k in ("input", "output"))):
        why.append("tokens is not {input, output} counts")
    ids = rec.get("chunk_ids")
    if ids is not None and not (isinstance(ids, list) and all(isinstance(i, str) for i in ids)):
        why.append("chunk_ids is not a list of ids")
    return why


def _recordings(path: Path | None = None) -> tuple[dict[str, list[dict]], list[str]] | None:
    """({row id: [lines]}, problems with the file), or None when the file does not exist."""
    path = path or RECORDED
    if not path.is_file():
        return None
    by_id: dict[str, list[dict]] = {}
    problems: list[str] = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            problems.append(f"line {n} is not JSON")
            continue
        if not isinstance(rec, dict):
            problems.append(f"line {n} is not a JSON object")
            continue
        by_id.setdefault(str(rec.get("id")), []).append(rec)
    return by_id, problems


def _pool_ids(passages: list[dict]) -> list:
    return [(p or {}).get("chunk_id") for p in passages]


def _recorded(row_id: str, tenant: str, passages: list[dict]) -> dict:
    """The recorded decision for one golden row, read from the file; nothing is sent and no policy is read."""
    got = _recordings()
    if got is None:
        return result("skipped", source="recorded", reason=RECORDED_ABSENT)
    by_id, problems = got
    if problems:
        return result("error", source="recorded", error=f"evals/system_one/recorded.jsonl: {problems[0]}",
                      reason="the recorded file is not well formed")
    lines = by_id.get(row_id) or []
    if not lines:
        return result("skipped", source="recorded", reason=f"no recording for row {row_id}")
    if len(lines) > 1:
        return result("error", source="recorded", error=f"{len(lines)} recordings for row {row_id}",
                      reason="one recording per golden row")
    rec = lines[0]
    why = recording_errors(rec)
    if not why and rec["tenant"] != tenant:
        why = [f"recorded for tenant {rec['tenant']}, not {tenant}"]
    if why:
        return result("error", source="recorded", error=f"recording for {row_id}: {why[0]}",
                      reason="not a recording")
    note = ""
    if rec.get("chunk_ids") is not None and rec["chunk_ids"] != _pool_ids(passages):
        note = "; recorded on another pool than this run's"
    return result(rec["verdict"], score=rec.get("score"), model=rec["model"], source="recorded", ms=rec.get("ms"),
                  tokens=rec.get("tokens"), cost_usd=_price(rec.get("tokens")), request_id=rec["request_id"],
                  reason=f"recorded {rec['recorded_at']}{note}")


def recording(row_id: str, tenant: str, passages: list[dict], res: dict, now: datetime | None = None) -> dict:
    """The recorded.jsonl line for one live decision (PR 2.6-C's recorder writes these): the decision as the API
    returned it, the pool's ids it was made on, and when. Refuses anything but a live answer or refusal with the
    vendor's request_id, so a recording can only come from a call."""
    if res.get("source") != "live" or res.get("verdict") not in ("answer", "refuse") or not res.get("request_id"):
        raise ValueError("only a live answer or refusal with the vendor's request_id is a recording")
    stamp = (now or datetime.now().astimezone()).isoformat(timespec="seconds")
    line = {"id": row_id, "tenant": tenant, "verdict": res["verdict"], "score": res.get("score"),
            "model": res.get("model"), "request_id": res["request_id"], "recorded_at": stamp, "ms": res.get("ms"),
            "tokens": res.get("tokens"), "chunk_ids": _pool_ids(passages)}
    why = recording_errors(line)
    if why:
        raise ValueError(f"not a recording: {why[0]}")
    return line


# ---------------------------------------------------------------- the adapter seam (PR 2.6-C)
def _headers() -> dict[str, str]:
    """PR 2.6-C: the request's headers. The key is JEV_API_KEY from the environment and nowhere else; which header
    carries it is TypeSafe's to document, so nothing is built until the docs say."""
    if not os.environ.get("JEV_API_KEY", "").strip():
        raise AdapterNotConfigured("JEV_API_KEY is not set: early access is through console.typesafe.ai, and the "
                                   "key is read from the environment only")
    raise AdapterNotConfigured(NOT_CONFIGURED)


def _request(payload: dict) -> tuple[int, dict]:
    """PR 2.6-C: send the masked payload to TypeSafe's hosted API, with _headers(), a timeout and no retry, and
    return (HTTP status, the decoded body). The endpoint and the request shape are TypeSafe's to document; until
    then this raises before a key is read or a socket opens."""
    raise AdapterNotConfigured(NOT_CONFIGURED)


def _parse(status: int, body: dict) -> dict:
    """PR 2.6-C: {verdict: answer|refuse, score: P(answer) from 0 to 1, model, request_id, tokens: {input,
    output}} from TypeSafe's response, or an exception naming what is missing. A choice reported with its own
    probability becomes P(answer): p for answer, 1 - p for refuse."""
    raise AdapterNotConfigured(NOT_CONFIGURED)


def _price(tokens: dict | None) -> float | None:
    """USD for one decision at TypeSafe's published price (USD_PER_1B_INPUT), or None when it cannot be priced: no
    token counts, or output tokens, whose price is not documented. Never shared/prices.usd(), which bills an unknown
    model at flash's rate."""
    if not isinstance(tokens, dict) or not isinstance(tokens.get("input"), int):
        return None
    if tokens.get("output") and USD_PER_1B_OUTPUT is None:
        return None
    return (tokens["input"] * USD_PER_1B_INPUT + (tokens.get("output") or 0) * (USD_PER_1B_OUTPUT or 0)) / 1e9


def _live(question: str, passages: list[dict], tenant: str, policy_for=None) -> dict:
    """One live decision: the tenant's policy first, then the masked payload, then the transport and the parse."""
    policy = _policy(tenant, policy_for)
    if policy != "any":
        return result("skipped", source="policy", cost_usd=0.0,
                      reason=f"tenant {tenant}: data_region {policy} - its text stays in India and Jev's region is "
                             f"undocumented: not sent")
    payload, kinds = _payload(question, passages)
    masked = f"; masked {', '.join(kinds)}" if kinds else ""
    t0 = time.monotonic()
    try:
        status, body = _request(payload)
        got = _parse(status, body)
    except AdapterNotConfigured as e:
        return result("error", source="live", error=str(e), cost_usd=0.0,
                      reason=f"the question and {len(passages)} passages were ready to send{masked}")
    except Exception as e:  # noqa: BLE001 - a failed call is an error row, never a refusal and never a crash
        return result("error", source="live", error=f"{type(e).__name__}: {e}"[:300],
                      ms=int((time.monotonic() - t0) * 1000), reason=f"the call failed{masked}")
    return result(got["verdict"], score=got.get("score"), model=got.get("model"), source="live",
                  ms=int((time.monotonic() - t0) * 1000), tokens=got.get("tokens"),
                  cost_usd=_price(got.get("tokens")), request_id=got.get("request_id"), reason=f"live{masked}")


# ---------------------------------------------------------------- the one entry point
def decide(question: str, passages: list[dict], row_id: str, tenant: str, *, jev_mode: str | None = None,
           policy_for=None) -> dict:
    """Jev's answer-or-refuse decision for one question over one pool, in the mode JEV_MODE names (or jev_mode).
    policy_for(tenant) -> in|any reads the data region (default shared/tenancy.policy_for). Never raises."""
    try:
        m = mode(jev_mode)
        if m == "off":
            return result("skipped", source="off", reason=OFF_REASON, cost_usd=0.0)
        if m not in MODES:
            return result("skipped", source="off", cost_usd=0.0,
                          reason=f"JEV_MODE={m!r} is not one of {'|'.join(MODES)}: nothing sent")
        if not passages:
            return result("refuse", source="code", reason=EMPTY_POOL, ms=0, cost_usd=0.0)
        if m == "recorded":
            return _recorded(row_id, tenant, passages)
        return _live(question, passages, tenant, policy_for)
    except Exception as e:  # noqa: BLE001 - decide() never raises: an unexpected failure is an error row
        return {"verdict": "error", "score": None, "reason": "decide() failed", "model": None, "source": "off",
                "ms": None, "tokens": None, "cost_usd": None, "error": f"{type(e).__name__}: {e}"[:300],
                "request_id": None}
