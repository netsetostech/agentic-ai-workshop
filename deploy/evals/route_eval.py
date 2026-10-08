#!/usr/bin/env python3
"""The DocuMind Desk route eval (workshop lessons 5.6 and 10.4): the route set's own checks, and the score of a run.

    python deploy/evals/route_eval.py --selftest                                  # OFFLINE - the set is sound
    python deploy/evals/route_eval.py --predictions run.jsonl --split dev [--arm B|C|Astar]
                                      [--registry doc_types.json] [--report verdicts.json]
    python deploy/evals/route_eval.py --local                                     # OFFLINE - the router, scripted
    python deploy/evals/route_eval.py --split dev --live-l1 --project documind-ai-YOUR-ID [--runs 3]   # LIVE
    python deploy/evals/route_eval.py --split dev --live --project documind-ai-YOUR-ID [--arm B|C|Astar]   # LIVE
                                      [--save run.jsonl]     # make route-eval: the deployed Desk

Stdlib only: it runs in CI's shared interpreter and in `make desk-check`, with no credential and no cost. --local and
--live-l1 import the router itself (services/chat/desk_router.py, which needs only the standard library and shared/),
so what they score is the code the service runs.

THE SET. evals/routes.jsonl holds one row per question the Desk is asked, with the route it must take:

    {id, of, group, tenant, identity, question, prev_question, prev_route, expected_route, acceptable_routes,
     expected_doc_types, expected_outcome, case_type, must_escalate, language, expect_model_calls_max,
     must_contain, must_not_contain, source, split, author, note}

    routes      handbook | statute | case | clarify | out_of_scope - the five labels the classifier has
    outcomes    answer | grounded_refusal | not_covered | denied | clarify | case | oos
    identity    a symbolic caller (acme_employee, acme_leaver), resolved to an eval service account from PROJECT
                at run time by identity_account(), so no row carries an email

build_routes.py writes the 207 rows that come from questions which already existed (golden, paraphrases, the SFT
user turns, all dev) and keeps every hand-written row; this file holds the schema both of them check against.

--selftest checks the set, not a model: every row against the schema, the split by GROUP (a golden id, its
paraphrases, a follow-up pair, an SFT source passage and every row with the same normalised question text sit on one
side), no identical normalised question - a follow-up's first turn included - on both sides of the split, and the
Wilson helper against the figures lesson 10.4 states. It prints the rows per route and split, then "no cross-split
pair". The embedding half of the contamination rule (a cosine of 0.95 or more across the split) needs a lane and is
not checked here.

SCORING reads a run: one JSON line per row, {id, route, ...}, with any of outcome, case_type, citations (each with
the Citation's source_uri, or a bare source), answer, model_calls, retrieve_calls, arm. A row the run does not carry
counts as a miss, never as out of scope: a gate that skips rows reports green over tests it never ran (run_eval.py's
lesson). The same holds for every metric the run measures: once one row carries an outcome, citations or model_calls,
a row without them fails that metric. Every rate is printed with its denominator and a Wilson 95% interval, because
at 30 rows a desk one row is 3.3 points and a bare percentage hides that.

    route accuracy   the predicted route is in acceptable_routes; per desk, per language, and the 5x5 confusion
                     matrix (a sixth column, "other", holds a missing row or a route outside the five)
    escalation       per case_type: route case with the row's case_type; reported per class and pooled
    authority_rate   every answer row cites, and every citation is the row's own tenant's object with a class in the
                     row's expected_doc_types; a grounded refusal counts only when it cites. The class comes from
                     the operator registry (--registry, a {tenant: {object: class}} export of tenants/{t}/doc_types,
                     which commands/desk_ops.py doc-types --export writes, one tenant a run)
                     or, offline, from evals/manifest.json, where a media object takes its parent document's class.
                     Citation keeps its schema: the lookup is by the object name in source_uri, not a new field. A
                     citation of another tenant's object is a cross_tenant failure, counted on its own line too; a
                     citation whose reference names no tenant is unresolved and fails
    no_citation      a row that retrieves nothing (out_of_scope, case, clarify, denied, not_covered) cites nothing
    no_leak          no must_not_contain in the answer text - a row the run lacks fails it, as it fails no_citation
    correct_rate     outcome answer, every must_contain on its own boundary, no must_not_contain (run_eval's
                     contains()), over every answer row - measured only when the run carries answer text
    denial           outcome denied with zero retrieve calls

--arm labels and scores a run by arm (workshop lesson 10.4): B is the routed Desk; C is code only (the gate,
coverage, then a direct answer over the person's doc types, no classifier); Astar is one agent with the real doc_type
vocabulary and the calculators (services/chat/desk_agent.py). One run is one arm: a run that mixes arms is refused. B
ships only if it is non-inferior to C and to Astar on the same rows. --live writes a run of any of the three (--save).

THE DEPLOYED DESK (workshop lesson 10.4). --live sends every scored row, as the row's eval account (IDENTITIES: an ID
token minted as it, so make desk-operators first), to the chat service's POST /v1/route for the decision, and each
handbook, statute and denial row also to POST /v1/desk, in a session of its own, for the answer, its citations and
retrieve calls; a follow-up row's first turn goes before it. A row the desk is not asked for takes its outcome from the
route (case, oos, clarify, denied, not_covered) with no citation. It prints the usual report - the matrix with
intervals, escalation recall, authority_rate - then the router's cost and the p50 and p95 of router_ms and of
/v1/desk's latency. Only the eval accounts call, each on one roster: chat-sa, ui-sa and mcp-sa sit on every golden
roster, so a run as one of them would score whichever tenant the roster gave it, and a reply from either route naming
another tenant than the row's stops the run. Arms C and Astar run with their arm on both routes (a desk_eval caller
only). Rows in the groups of the prompt's examples are left out, as in --live-l1.

THE ROUTER IN PROCESS (workshop lesson 10.4). --local runs decide() on every row of the split with a scripted
classifier and offline embeddings (a hashed bag of words), so CI measures the cascade - the gate, the anchors, the
acceptance rules, the arbiter, the checks - and not a model: the scripted L1 gives each row its own label except on
about one row in eight, where it is deliberately wrong (never away from a case), and the scripted arbiter picks the
label when it is one of its candidates. It prints the usual report, then the method mix, the arbiter's share,
the accuracy on turns accepted without the arbiter and the router's cost at the scripted token counts, and exits 1
below the dev gates: 95% route accuracy, 90% per desk, and every escalation row escalated. --live-l1 is the same run
with the real flash-lite, flash and text-embedding-005 on your lane, --runs times (pass^k), from your own shell.

The exemplar index is the dev rows of every routed tenant (a single-mode tenant's rows are labelled for its one desk,
so they are left out), filtered to the routes the tenant is covered for. On the dev split a row's vote runs
leave-one-group-out: its own group - its id, its golden row, its paraphrases, its follow-up pair, and every row with the
same normalised text - is out of its neighbours (knn_vote), and --selftest checks that no dev row can retrieve itself.
Rows in the groups of the classifier's prompt examples (services/chat/desk_routes.py) are left out of both runs'
scores, since the prompt has seen them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import unicodedata
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from run_eval import contains  # noqa: E402  - one matcher for a figure on its own boundary, the live gate's

ROUTES_FILE = os.path.join(HERE, "routes.jsonl")
MANIFEST = os.path.join(HERE, "manifest.json")

FIELDS = ("id", "of", "group", "tenant", "identity", "question", "prev_question", "prev_route", "expected_route",
          "acceptable_routes", "expected_doc_types", "expected_outcome", "case_type", "must_escalate", "language",
          "expect_model_calls_max", "must_contain", "must_not_contain", "source", "split", "author", "note")
ROUTES = ("handbook", "statute", "case", "clarify", "out_of_scope")
OUTCOMES = ("answer", "grounded_refusal", "not_covered", "denied", "clarify", "case", "oos")
CASE_TYPES = ("posh", "grievance", "privacy_request", "exit_dues", "people_query", "human_requested")
# The doc_type classes of the operator registry. Repeated here so the eval needs no lane and no import from the
# services.
CLASSES = ("policy", "statute", "guidance", "report", "transcript", "contract", "invoice")
LANGUAGES = ("en", "hi", "hinglish")
SPLITS = ("dev", "test")
TENANTS = ("acme", "zeta", "globex")
# What each route may end in. A handbook or statute row can also be denied (a leaver) or not_covered (a tenant
# with no documents for the desk); a row on any other route has exactly one outcome.
ROUTE_OUTCOMES = {"handbook": ("answer", "grounded_refusal", "not_covered", "denied"),
                  "statute": ("answer", "grounded_refusal", "not_covered", "denied"),
                  "case": ("case",), "clarify": ("clarify",), "out_of_scope": ("oos",)}
# The eval callers: one service account each, no project roles. The row names the symbol; the address is built from
# PROJECT when a live run starts. Role identities join as their rows arrive.
IDENTITIES = {"acme_employee": ("acme", "documind-evalacme-sa"),
              "zeta_employee": ("zeta", "documind-evalzeta-sa"),
              "globex_employee": ("globex", "documind-evalglobex-sa"),
              "acme_leaver": ("acme", "documind-evalleaver-sa")}
ARMS = {"B": "the routed Desk",
        "C": "code only: the gate, coverage, then a direct answer over the person's doc types, no classifier",
        "Astar": "one agent with the real doc_type vocabulary and the calculators"}
SOURCE = re.compile(r"^(golden\.jsonl:[a-z]+-\d+|paraphrases\.jsonl:pp-\d+|sft/documind_sft_v1\.chat\.jsonl:\d+|new)$")
ROW_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
Z95 = 1.96          # Wilson 95%: with every row passing, the lower bound is n / (n + 1.96^2) = n / (n + 3.84)


# --------------------------------------------------------------------- the set
def normalise(text: str) -> str:
    """The contamination key: NFKC, case-folded, zero-width joiners removed, punctuation and symbols dropped,
    whitespace collapsed. Marks are kept, so a Devanagari vowel sign is not stripped out of a Hindi word."""
    t = unicodedata.normalize("NFKC", text or "").casefold()
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Cf")      # a zero-width joiner is no word break
    t = "".join(" " if unicodedata.category(ch)[0] in "PSZC" else ch for ch in t)
    return " ".join(t.split())


def identity_account(identity: str, project: str) -> str:
    """The service account a live run calls as. Built here, at run time, so the set never holds an address."""
    return f"{IDENTITIES[identity][1]}@{project}.iam.gserviceaccount.com"


def _strs(value) -> bool:
    return isinstance(value, list) and all(isinstance(v, str) and v for v in value)


def row_errors(row: dict) -> list[str]:
    """Why this row is not a route row; empty when it is."""
    if not isinstance(row, dict):
        return ["not an object"]
    rid = row.get("id", "?")
    why = []
    missing, extra = [f for f in FIELDS if f not in row], sorted(set(row) - set(FIELDS))
    if missing or extra:
        return [f"{rid}: fields missing {missing}, unknown {extra}"]
    if not isinstance(rid, str) or not ROW_ID.match(rid):
        why.append(f"{rid}: id must be lower-case letters, digits and hyphens")
    for f in ("group", "question", "source", "author"):
        if not isinstance(row[f], str) or not row[f].strip():
            why.append(f"{rid}: {f} must be a non-empty string")
    for f in ("of", "prev_question", "case_type"):
        if row[f] is not None and not (isinstance(row[f], str) and row[f]):
            why.append(f"{rid}: {f} must be null or a non-empty string")
    if not isinstance(row["note"], str):
        why.append(f"{rid}: note must be a string")
    if why:
        return why
    if len(row["question"]) > 1000:
        why.append(f"{rid}: question over 1,000 characters (the classifier's fence)")
    if row["tenant"] not in TENANTS:
        why.append(f"{rid}: tenant {row['tenant']!r} not one of {TENANTS}")
    if row["identity"] not in IDENTITIES:
        why.append(f"{rid}: identity {row['identity']!r} is not a symbolic eval identity {sorted(IDENTITIES)}")
    elif IDENTITIES[row["identity"]][0] != row["tenant"]:
        why.append(f"{rid}: identity {row['identity']} is not on tenant {row['tenant']} (a person has one tenant)")
    if (row["prev_question"] is None) != (row["prev_route"] is None):
        why.append(f"{rid}: prev_question and prev_route come together")
    if row["prev_route"] is not None and row["prev_route"] not in ROUTES:
        why.append(f"{rid}: prev_route {row['prev_route']!r} not a route")
    route, outcome = row["expected_route"], row["expected_outcome"]
    if route not in ROUTES:
        why.append(f"{rid}: expected_route {route!r} not one of {ROUTES}")
    acc = row["acceptable_routes"]
    if not _strs(acc) or not acc or len(set(acc)) != len(acc) or set(acc) - set(ROUTES) or route not in acc:
        why.append(f"{rid}: acceptable_routes must be distinct routes that include expected_route")
    if outcome not in OUTCOMES:
        why.append(f"{rid}: expected_outcome {outcome!r} not one of {OUTCOMES}")
    elif route in ROUTE_OUTCOMES and outcome not in ROUTE_OUTCOMES[route]:
        why.append(f"{rid}: route {route} cannot end in {outcome}")
    types = row["expected_doc_types"]
    if not isinstance(types, list) or set(types) - set(CLASSES) or len(set(types)) != len(types):
        why.append(f"{rid}: expected_doc_types must be distinct classes from {CLASSES}")
    elif outcome in ("answer", "grounded_refusal") and not types:
        why.append(f"{rid}: an {outcome} row names the doc types its citations may come from")
    elif outcome not in ("answer", "grounded_refusal") and types:
        why.append(f"{rid}: a {outcome} row retrieves nothing, so expected_doc_types is []")
    if route == "case" and row["case_type"] not in CASE_TYPES:
        why.append(f"{rid}: a case row names its case_type, one of {CASE_TYPES}")
    if route != "case" and row["case_type"] is not None:
        why.append(f"{rid}: case_type is only for a case row")
    if not isinstance(row["must_escalate"], bool):
        why.append(f"{rid}: must_escalate must be true or false")
    elif row["must_escalate"] and route != "case":
        why.append(f"{rid}: a must_escalate row routes to case")
    if row["language"] not in LANGUAGES:
        why.append(f"{rid}: language {row['language']!r} not one of {LANGUAGES}")
    cap = row["expect_model_calls_max"]
    if cap is not None and (isinstance(cap, bool) or not isinstance(cap, int) or cap < 0):
        why.append(f"{rid}: expect_model_calls_max must be null or a whole number")
    for f in ("must_contain", "must_not_contain"):
        if not isinstance(row[f], list) or (row[f] and not _strs(row[f])):
            why.append(f"{rid}: {f} must be a list of non-empty strings")
    if not SOURCE.match(row["source"]):
        why.append(f"{rid}: source {row['source']!r} is not golden.jsonl:<id>, paraphrases.jsonl:<id>, "
                   f"sft/documind_sft_v1.chat.jsonl:<line> or new")
    if row["split"] not in SPLITS:
        why.append(f"{rid}: split {row['split']!r} not one of {SPLITS}")
    elif row["split"] == "test" and row["source"] != "new":
        why.append(f"{rid}: every pre-existing question is dev only (it was seen while the rules were written)")
    if "@" in json.dumps(row, ensure_ascii=False):
        why.append(f"{rid}: an @ - rows carry symbolic identities, never an address")
    return why


def set_errors(rows: list[dict]) -> list[str]:
    """The rules across rows: unique ids, one split per group, one group per normalised question, a paraphrase in
    its golden row's group, and no identical normalised question on both sides of the split."""
    why, seen = [], {}
    for r in rows:
        if r["id"] in seen:
            why.append(f"{r['id']}: duplicate id")
        seen[r["id"]] = r
    splits: dict[str, set] = {}
    for r in rows:
        splits.setdefault(r["group"], set()).add(r["split"])
    why += [f"group {g}: rows on both sides of the split ({', '.join(sorted(s))})"
            for g, s in sorted(splits.items()) if len(s) > 1]
    by_text: dict[str, list[dict]] = {}
    for r in rows:
        by_text.setdefault(normalise(r["question"]), []).append(r)
    first_turns: dict[str, list[dict]] = {}          # a follow-up's first turn is text the model sees too
    for r in rows:
        if r["prev_question"]:
            first_turns.setdefault(normalise(r["prev_question"]), []).append(r)
    for text, same in sorted(by_text.items()):
        if len({r["split"] for r in same}) > 1:
            why.append(f"cross-split pair: {', '.join(r['id'] for r in same)} ask {text[:60]!r}")
        if len({r["group"] for r in same}) > 1:
            why.append(f"{', '.join(r['id'] for r in same)}: the same question in groups "
                       f"{sorted({r['group'] for r in same})} (the split is by group, so one question is one group)")
    for text, follow in sorted(first_turns.items()):
        both = follow + by_text.get(text, [])
        if len({r["split"] for r in both}) > 1:
            why.append(f"cross-split pair: {', '.join(r['id'] for r in both)} ask {text[:60]!r} "
                       f"(as a question or a follow-up's first turn)")
    for r in rows:
        if r["of"] and r["of"] not in seen:
            why.append(f"{r['id']}: of {r['of']}, which is not a row of the set")
        elif r["of"] and seen[r["of"]]["group"] != r["group"]:
            why.append(f"{r['id']}: of {r['of']} but in group {r['group']}, not {seen[r['of']]['group']}")
    return why


def load_rows(path: str = ROUTES_FILE) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as e:
                    raise SystemExit(f"{path}:{n}: not JSON ({e})")
    return rows


def check_rows(rows: list[dict]) -> list[str]:
    why = [w for r in rows for w in row_errors(r)]
    return why or set_errors(rows)


# --------------------------------------------------------------------- Wilson
def wilson(k: int, n: int, z: float = Z95) -> tuple[float, float] | None:
    """The Wilson score interval for k of n. None for n = 0: no rows is no evidence, not 0% or 100%."""
    if n <= 0:
        return None
    p, z2 = k / n, z * z
    centre, margin = p + z2 / (2 * n), z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))
    return max(0.0, (centre - margin) / (1 + z2 / n)), min(1.0, (centre + margin) / (1 + z2 / n))


def rate(k: int, n: int) -> str:
    """k/n = p% [lo%, hi%], the form every rate is printed in."""
    if n == 0:
        return "0/0 (no rows)"
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {100 * k / n:.1f}% [{100 * lo:.1f}%, {100 * hi:.1f}%]"


# Lesson 10.4's figures for a split where every row passes: n / (n + 3.84), to one decimal.
WILSON_FIGURES = {20: 83.9, 73: 95.0, 75: 95.1, 100: 96.3}


def wilson_errors() -> list[str]:
    why = [f"Wilson lower bound for {n} of {n} is {100 * wilson(n, n)[0]:.1f}%, lesson 10.4 says {want}%"
           for n, want in WILSON_FIGURES.items() if round(100 * wilson(n, n)[0], 1) != want]
    if round(100 * wilson(72, 72)[0], 1) >= 95.0:
        why.append("72 rows reach a 95% lower bound, but lesson 10.4 says 73 is the minimum")
    return why


# --------------------------------------------------------------------- the selftest
def selftest(path: str = ROUTES_FILE) -> int:
    rows = load_rows(path)
    why = check_rows(rows) + wilson_errors()
    print(f"{os.path.relpath(path)}: {len(rows)} rows")
    print(f"  {'route':<14}" + "".join(f"{s:>6}" for s in SPLITS))
    for route in ROUTES:
        print(f"  {route:<14}" + "".join(f"{sum(1 for r in rows if r.get('expected_route') == route and r.get('split') == s):>6}"
                                         for s in SPLITS))
    print(f"  {'total':<14}" + "".join(f"{sum(1 for r in rows if r.get('split') == s):>6}" for s in SPLITS))
    if why:
        for w in why:
            print(f"FAIL  {w}")
        return 1
    print("  Wilson: " + ", ".join(f"{n} of {n} -> {100 * wilson(n, n)[0]:.1f}%" for n in WILSON_FIGURES))
    why = self_retrieval_errors(rows)
    if why:
        for w in why:
            print(f"FAIL  {w}")
        return 1
    print(f"  kNN: no dev row retrieves its own id, group or text (leave-one-group-out over "
          f"{sum(1 for r in rows if r['split'] == 'dev')} dev rows)")
    print("no cross-split pair")
    return 0


# --------------------------------------------------------------------- the doc_type of a citation
def _media_parent(slug: str, parents: dict[str, str]) -> str | None:
    """The media parent rule: a media object takes the class of the longest same-tenant slug that is its prefix."""
    best = max((p for p in parents if slug == p or slug.startswith(p + "_")), key=len, default=None)
    return parents[best] if best else None


def classes_from_manifest(path: str = MANIFEST) -> dict[tuple[str, str], str]:
    """{(tenant, object name): class} from evals/manifest.json. A text or real document takes its manifest class;
    a media object (figure, video, image are not classes) takes its parent's; whiteboard_arch.png has no parent
    and stays unregistered, so a citation of it is in no desk's scope."""
    with open(path, encoding="utf-8") as f:
        docs = json.load(f)
    out, parents = {}, {}
    for d in docs:
        if d["doc_type"] in CLASSES:
            parents.setdefault(d["tenant_id"], {})[d["slug"]] = d["doc_type"]
    for d in docs:
        name = d["file"].rsplit("/", 1)[-1]
        cls = d["doc_type"] if d["doc_type"] in CLASSES else _media_parent(d["slug"], parents.get(d["tenant_id"], {}))
        if cls:
            out[(d["tenant_id"], name)] = cls
    return out


def classes_from_registry(path: str) -> dict[tuple[str, str], str]:
    """An export of the operator registry, {tenant: {object name: class}} or {tenant: [{name, doc_type}]}. The
    registry names an object as the bucket does, "<tenant>/<basename>" (acme/hr_policy_2026.md), so the key is
    (tenant, basename), the shape citation_object() and the manifest map use; a name under another tenant's prefix is
    refused. "unknown" is kept as itself: it is in no row's expected_doc_types, so it fails authority."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    out = {}
    for tenant, entries in data.items():
        items = entries.items() if isinstance(entries, dict) else ((e["name"], e["doc_type"]) for e in entries)
        for name, cls in items:
            if "/" in name:
                prefix, name = name.split("/", 1)
                if prefix != tenant:
                    raise SystemExit(f"{path}: {prefix}/{name} is listed under tenant {tenant}")
            out[(tenant, name)] = cls
    return out


def citation_object(citation: dict) -> tuple[str | None, str]:
    """(tenant, object name) from a Citation's source_uri (gs://<bucket>/<tenant>/<name>) or a "<tenant>/<name>"
    source. A reference with no tenant segment (a bare "hr_policy_2026.md") gives tenant None: nothing in it says
    whose object it is, so it is never credited to the row's tenant."""
    ref = str(citation.get("source_uri") or citation.get("source") or "")
    if ref.startswith("gs://"):
        ref = ref.split("/", 3)[-1] if ref.count("/") >= 3 else ""
    parts = ref.split("/")
    return (parts[-2], parts[-1]) if len(parts) >= 2 and parts[-2] else (None, parts[-1])


# --------------------------------------------------------------------- scoring
def load_predictions(path: str, known: set[str]) -> dict[str, dict]:
    preds = {}
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            p = json.loads(line)
            if not isinstance(p, dict) or not isinstance(p.get("id"), str) or not isinstance(p.get("route"), str):
                raise SystemExit(f"{path}:{n}: a prediction is an object with a string id and route")
            if p["id"] not in known:
                raise SystemExit(f"{path}:{n}: {p['id']} is not a row of the route set")
            if p["id"] in preds:
                raise SystemExit(f"{path}:{n}: {p['id']} predicted twice")
            for f in ("model_calls", "retrieve_calls"):
                if f in p and (isinstance(p[f], bool) or not isinstance(p[f], int) or p[f] < 0):
                    raise SystemExit(f"{path}:{n}: {p['id']}: {f} is a whole number when present, not {p[f]!r}")
            if "citations" in p and not (isinstance(p["citations"], list)
                                         and all(isinstance(c, dict) for c in p["citations"])):
                raise SystemExit(f"{path}:{n}: {p['id']}: citations is a list of objects")
            preds[p["id"]] = p
    return preds


def run_arm(preds: dict[str, dict], arm: str | None) -> str | None:
    """The one arm this run is. --arm labels it; a prediction that names a different arm is refused, and so is a run
    whose rows name two arms - a comparison of B, C and A* is two runs on the same rows, never one mixed file."""
    named = {p["arm"] for p in preds.values() if p.get("arm") is not None}
    if arm and named - {arm}:
        raise SystemExit(f"--arm {arm}, but the run's rows name {sorted(named)}: score one arm at a time")
    if not arm and len(named) > 1:
        raise SystemExit(f"the run's rows name arms {sorted(named)}: score one arm at a time (--arm)")
    if not arm and named:
        arm = named.pop()
    if arm and arm not in ARMS:
        raise SystemExit(f"arm {arm!r} is not one of {sorted(ARMS)}")
    return arm


def score(rows: list[dict], preds: dict[str, dict], classes: dict[tuple[str, str], str]) -> dict:
    """Every metric over the rows in scope, as (k, n) pairs, plus each row's verdict. A metric the run measures at
    all (one row carries the field) is measured on every row it applies to, so a missing row fails it."""
    tally: dict[str, list[int]] = {}

    def count(key: str, ok: bool) -> None:
        t = tally.setdefault(key, [0, 0])
        t[0] += int(ok)
        t[1] += 1

    def carries(field: str) -> bool:
        return any(field in p for p in preds.values())

    cols = ROUTES + ("other",)
    confusion = {r: {c: 0 for c in cols} for r in ROUTES}
    has_answers, has_outcomes = carries("answer"), carries("outcome")
    has_citations, has_model_calls = carries("citations") or has_answers, carries("model_calls")
    verdicts = []
    for row in rows:
        p = preds.get(row["id"], {})
        got = p.get("route", "missing")
        v = {"id": row["id"], "expected_route": row["expected_route"], "route": got,
             "route_ok": got in row["acceptable_routes"]}
        confusion[row["expected_route"]][got if got in ROUTES else "other"] += 1
        count("route", v["route_ok"])
        count(f"route:{row['expected_route']}", v["route_ok"])
        count(f"language:{row['language']}", v["route_ok"])
        if row["must_escalate"]:
            v["escalated"] = got == "case" and p.get("case_type") == row["case_type"]
            count("escalation", v["escalated"])
            count(f"escalation:{row['case_type']}", v["escalated"])
            count(f"escalation:{row['language']}", v["escalated"])
        if has_outcomes:
            v["outcome_ok"] = p.get("outcome") == row["expected_outcome"]
            count("outcome", v["outcome_ok"])
        cites = p.get("citations") or []
        if has_citations and row["expected_doc_types"] and (cites or row["expected_outcome"] == "answer"):
            # Each citation is resolved on the ROW's tenant: another tenant's object is a breach, never authority,
            # and a citation that names no tenant is unresolved, never assumed to be the row's own.
            got_classes = []
            for c in cites:
                tenant, name = citation_object(c)
                got_classes.append("unresolved" if tenant is None else
                                   classes.get((tenant, name)) if tenant == row["tenant"] else "cross_tenant")
            v["citation_classes"] = got_classes
            v["authority_ok"] = bool(got_classes) and all(c in row["expected_doc_types"] for c in got_classes)
            count("authority", v["authority_ok"])
            count(f"authority:{row['expected_route']}", v["authority_ok"])
            count("no_cross_tenant", row["id"] in preds and "cross_tenant" not in got_classes)   # a lacked row misses
        elif has_citations and not row["expected_doc_types"]:
            v["no_citation_ok"] = row["id"] in preds and not cites       # a row the run lacks is a miss
            count("no_citation", v["no_citation_ok"])
        if has_answers and row["expected_outcome"] == "answer":
            text = str(p.get("answer") or "")
            v["correct"] = (p.get("outcome") == "answer" and all(contains(text, w) for w in row["must_contain"])
                            and not any(contains(text, w) for w in row["must_not_contain"]))
            count("correct", v["correct"])
        if has_answers and row["must_not_contain"]:
            v["leak"] = row["id"] not in preds or any(contains(str(p.get("answer") or ""), w)
                                                       for w in row["must_not_contain"])
            count("no_leak", not v["leak"])
        if row["expected_outcome"] == "denied":
            v["denied_ok"] = p.get("outcome") == "denied" and p.get("retrieve_calls") == 0
            count("denial", v["denied_ok"])
        if row["expect_model_calls_max"] is not None and has_model_calls:
            v["model_calls_ok"] = "model_calls" in p and p["model_calls"] <= row["expect_model_calls_max"]
            count("model_calls", v["model_calls_ok"])
        verdicts.append(v)
    return {"tally": tally, "confusion": confusion, "verdicts": verdicts, "has_answers": has_answers,
            "has_citations": has_citations}


def report(result: dict, arm: str | None, split: str, out=None) -> None:
    t, out = result["tally"], out or sys.stdout

    def line(label: str, key: str) -> None:
        k, n = t.get(key, (0, 0))
        print(f"  {label:<30}{rate(k, n)}", file=out)

    print(f"arm {arm} ({ARMS[arm]})" if arm else "arm: unlabelled", file=out)
    if arm in ("C", "Astar"):
        print(f"  arm {arm} has no route classifier: its route column shows the gate and coverage only; compare the "
              f"arms on authority_rate and correct_rate first", file=out)
    print(f"split {split}", file=out)
    line("top-1 route accuracy", "route")
    for route in ROUTES:
        line(f"  recall {route}", f"route:{route}")
    print("  confusion (rows: expected; columns: predicted)", file=out)
    cols = ROUTES + ("other",)
    print("    " + f"{'':<14}" + "".join(f"{c[:12]:>13}" for c in cols), file=out)
    for r in ROUTES:
        print("    " + f"{r:<14}" + "".join(f"{result['confusion'][r][c]:>13}" for c in cols), file=out)
    for r in ROUTES:                                 # every off-diagonal cell with rows, 0 of n included
        n = sum(result["confusion"][r].values())
        for c in cols:
            if c != r and n:
                print(f"    {r} -> {c}: {rate(result['confusion'][r][c], n)}", file=out)
    for lang in LANGUAGES:
        if f"language:{lang}" in t:
            line(f"route accuracy, {lang}", f"language:{lang}")
    line("escalation recall, pooled", "escalation")
    for ct in CASE_TYPES:
        if f"escalation:{ct}" in t:
            line(f"  {ct}", f"escalation:{ct}")
    for lang in LANGUAGES:
        if f"escalation:{lang}" in t:
            line(f"  in {lang}", f"escalation:{lang}")
    if "outcome" in t:
        line("outcome accuracy", "outcome")
    if result["has_citations"]:
        line("authority_rate", "authority")
        for route in ("handbook", "statute"):
            if f"authority:{route}" in t:
                line(f"  {route}", f"authority:{route}")
        line("  no cross-tenant citation", "no_cross_tenant")
        if "no_citation" in t:
            line("no citation where none is due", "no_citation")
    else:
        print(f"  {'authority_rate':<30}not measured: the run carries no citations (a /v1/route run)", file=out)
    if result["has_answers"]:
        line("correct_rate (answer rows)", "correct")
        if "no_leak" in t:
            line("no must_not_contain", "no_leak")
    else:
        print(f"  {'correct_rate':<30}not measured: the run carries no answer text (a /v1/route run)", file=out)
    if "denial" in t:
        line("denial, zero retrieve calls", "denial")
    if "model_calls" in t:
        line("within expect_model_calls_max", "model_calls")


# --------------------------------------------------------------------- the router, in process (lesson 10.4)
KIT = os.path.dirname(HERE)
SINGLE = {"globex": "statute"}          # build_routes.SINGLE: the tenants that run one desk with no classifier
QUEUES_DIR = os.path.join(HERE, "desk")
DEV_GATES = {"route": 0.95, "per_desk": 0.90, "escalation": 1.0}
WRONG = {"handbook": "statute", "statute": "handbook", "out_of_scope": "handbook", "clarify": "handbook",
         "case": "case"}                # the scripted classifier's mistakes: never away from a case
EMBED_DIM_OFFLINE = 256
_WORD = re.compile(r"[^\W_]+")
_STOP = frozenset("a an and are at be by can do does for from how i in is it many much my of on or the to under what "
                  "when which who whose why with".split())


def router():
    """services/chat/desk_router.py and desk_routes.py: the code the service runs, imported from the kit."""
    for p in (os.path.join(KIT, "services", "chat"), KIT):
        if p not in sys.path:
            sys.path.insert(0, p)
    import desk_router
    import desk_routes
    return desk_router, desk_routes


def offline_embed(text: str, dim: int = EMBED_DIM_OFFLINE) -> list[float]:
    """A hashed bag of content words and word pairs, unit length: a stand-in for text-embedding-005 that needs no
    lane."""
    words = [w for w in _WORD.findall(normalise(text)) if w not in _STOP]
    vec = [0.0] * dim
    for w, weight in [(w, 1.0) for w in words] + [(a + " " + b, 0.5) for a, b in zip(words, words[1:])]:
        vec[int(hashlib.sha256(w.encode("utf-8")).hexdigest(), 16) % dim] += weight
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def index_rows(rows: list[dict], enabled=None) -> list[dict]:
    """The rows an exemplar index holds: dev rows of routed tenants (a single-mode tenant's rows are labelled for its
    one desk), and only the routes given (a tenant's enabled routes)."""
    return [r for r in rows if r["split"] == "dev" and r["tenant"] not in SINGLE
            and (enabled is None or r["expected_route"] in enabled)]


def build_index(rows: list[dict], vectors: dict[str, list[float]]) -> list[dict]:
    return [{"row_id": r["id"], "group": r["group"], "route": r["expected_route"], "case_type": r["case_type"],
             "text": normalise(r["question"]), "vector": vectors[r["id"]]} for r in rows]


def held_out(row: dict, index: list[dict]) -> list[dict]:
    """The index without the row's own group: its id, its group, and any exemplar with its normalised text."""
    text = normalise(row["question"])
    return [e for e in index if e["row_id"] != row["id"] and e["group"] != row["group"] and e.get("text") != text]


def knn_vote(row: dict, index: list[dict], exclude_group: bool = True, vector=None) -> dict:
    """The k=7 vote for a dev row - the router's own knn_vote - leave-one-group-out unless told otherwise. One
    function for route_eval.py and route_threshold.py."""
    desk_router, _ = router()
    vec = vector if vector is not None else next((e["vector"] for e in index if e["row_id"] == row["id"]), None)
    if vec is None:
        vec = offline_embed(row["question"])
    return desk_router.knn_vote(vec, held_out(row, index) if exclude_group else index)


def self_retrieval_errors(rows: list[dict]) -> list[str]:
    """No dev row may retrieve itself: with the offline embeddings, every dev row's neighbours under knn_vote() hold
    no row of its group and nothing with its text - and the same vote without the exclusion does find the row, so
    the check is not passing by accident."""
    dev = [r for r in rows if r["split"] == "dev"]
    if not dev:
        return []
    by_id = {r["id"]: r for r in dev}
    index = build_index(dev, {r["id"]: offline_embed(r["question"]) for r in dev})
    why = []
    for r in dev:
        got = knn_vote(r, index)["neighbours"]
        bad = [i for i in got if by_id[i]["group"] == r["group"] or normalise(by_id[i]["question"]) == normalise(r["question"])]
        if bad:
            why.append(f"{r['id']}: retrieves {bad}, of its own group or text")
    probe = dev[0]
    if probe["id"] not in knn_vote(probe, index, exclude_group=False)["neighbours"]:
        why.append(f"{probe['id']}: not its own neighbour even without the exclusion: the check above proves nothing")
    return why


def prompt_groups(rows: list[dict]) -> set[str]:
    """The groups of the classifier's prompt examples: a live score leaves them out, since the prompt has seen them."""
    _, desk_routes = router()
    ids = {i for i, _, _ in desk_routes.PROMPT_EXEMPLARS}
    return {r["group"] for r in rows if r["id"] in ids}


def _tenant_classes() -> dict[str, set]:
    with open(MANIFEST, encoding="utf-8") as f:
        docs = json.load(f)
    out: dict[str, set] = {}
    for d in docs:
        if d["doc_type"] in CLASSES:
            out.setdefault(d["tenant_id"], set()).add(d["doc_type"])
    return out


def _clause_prefixes(tenant: str) -> list[str]:
    path = os.path.join(QUEUES_DIR, f"queues.{tenant}.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return sorted((json.load(f).get("clause_prefixes") or {}))


def _wrong(row_id: str) -> bool:
    return int(hashlib.sha256(row_id.encode("utf-8")).hexdigest(), 16) % 8 == 0


class ScriptedModels:
    """--local's models: the row's own label from L1, wrong on about one row in eight; an arbiter that picks the label
    when it is a candidate, else clarify; embeddings from the index's own vectors, or offline_embed. Token counts are
    the prompt's characters / 4 in and 30 out - the probe measures the real ones."""

    def __init__(self, rows: list[dict], vectors: dict[str, list[float]]):
        self.vectors = {normalise(r["question"]): vectors[r["id"]] for r in rows if r["id"] in vectors}
        self.row: dict | None = None

    def begin(self, row: dict) -> None:
        """The row being decided: two tenants may ask the same words with different labels (a single-mode tenant)."""
        self.row = row

    def _row(self, question: str) -> dict:
        if self.row is None or normalise(self.row["question"]) != normalise(question):
            raise KeyError("the scripted classifier was asked about a question that is not the row's")
        return self.row

    def l1(self, text: str):
        desk_router, _ = router()
        row = self._row(desk_router.prompt_parts(text)["question"])
        route = WRONG[row["expected_route"]] if _wrong(row["id"]) else row["expected_route"]
        return ({"route": route, "second_route": "none",
                 "case_type": (row["case_type"] or "people_query") if route == "case" else "none",
                 "needs_calculation": False, "followup": row["prev_question"] is not None},
                {"tokens_in": len(text) // 4, "tokens_out": 30, "cached": 0})

    def l2(self, text: str, candidates):
        question = text.rsplit("Question: <<<", 1)[1].rsplit(">>>", 1)[0]
        label = self._row(question)["expected_route"]
        return (label if label in candidates else "clarify"), {"tokens_in": len(text) // 4, "tokens_out": 30, "cached": 0}

    def embed(self, text: str) -> list[float]:
        return self.vectors.get(normalise(text)) or offline_embed(text)


def route_run(rows: list[dict], index_by_tenant: dict[str, list[dict]], models, now: float | None = None) -> list[dict]:
    """decide() on every row, each with its tenant's index held out by the row's group. One dict per row: the row's
    id, the decision and the Meter's cost."""
    desk_router, desk_routes = router()
    import limits
    classes = _tenant_classes()
    now = now or 1_790_000_000.0
    out = []
    for r in rows:
        meter = limits.Meter(model=desk_router.L1_MODEL)
        ctx = {"tenant": r["tenant"], "roles": ["leaver"] if r["identity"].endswith("_leaver") else ["employee"],
               "meter": meter, "single": SINGLE.get(r["tenant"]),
               "coverage": desk_routes.coverage(classes.get(r["tenant"], ())),
               "clause_prefixes": _clause_prefixes(r["tenant"]),
               "index": held_out(r, index_by_tenant.get(r["tenant"], [])),
               "prev_route": r["prev_route"], "prev_question": r["prev_question"],
               "prev_at": now - 60 if r["prev_question"] else None,
               "prev_clarified": r["prev_route"] == "clarify" if r["prev_question"] else False, "max_parts": 1, "now": now}
        if hasattr(models, "begin"):
            models.begin(r)
        d = desk_router.decide(r["question"], ctx, models)
        out.append({"id": r["id"], "decision": d, "cost_inr": meter.spent_inr()})
    return out


def predictions(run: list[dict]) -> dict[str, dict]:
    """A run as score() reads it. A denied or not_covered turn scores the desk it was routed to; no outcome is
    claimed, because a route-only run cannot tell an answer from a grounded refusal."""
    preds = {}
    for x in run:
        d = x["decision"]
        route = d["desk"] if d["route"] in ("denied", "not_covered") else d["route"]
        preds[x["id"]] = {"id": x["id"], "route": route, "case_type": d["case_type"], "model_calls": d["model_calls"],
                          "arm": "B"}
    return preds


def router_report(rows: list[dict], run: list[dict], out=None) -> dict:
    """The router's own figures: how turns were decided, the arbiter's share, the accuracy of turns accepted
    without it, the cost."""
    out = out or sys.stdout
    by_id = {r["id"]: r for r in rows}
    n = len(run)
    methods = Counter(x["decision"]["method"] for x in run)
    rules_ = Counter(x["decision"]["accepted_by"] for x in run if x["decision"]["accepted_by"])
    accepted = [x for x in run if x["decision"]["accepted_by"] in ("A", "B", "C", "D")
                or x["decision"]["method"] in ("anchor", "single", "rule")]
    ok = sum(1 for x in accepted if predictions([x])[x["id"]]["route"] in by_id[x["id"]]["acceptable_routes"])
    arbiter = sum(1 for x in run if x["decision"]["accepted_by"] == "F")
    cost = sum(x["cost_inr"] for x in run)
    print(f"  methods: {', '.join(f'{m} {c}' for m, c in sorted(methods.items()))}", file=out)
    print(f"  acceptance rules: {', '.join(f'{k} {c}' for k, c in sorted(rules_.items())) or 'none'}", file=out)
    print(f"  {'accepted without L2':<30}{rate(ok, len(accepted))}", file=out)
    print(f"  {'sent to L2':<30}{rate(arbiter, n)}", file=out)
    print(f"  {'router cost':<30}Rs {cost:.4f} in all, Rs {cost / max(n, 1):.5f} a turn", file=out)
    return {"accepted": (ok, len(accepted)), "arbiter": (arbiter, n), "cost_inr": cost}


def gate_failures(result: dict) -> list[str]:
    """The dev gates the run misses."""
    t, why = result["tally"], []
    k, n = t.get("route", (0, 0))
    if n == 0 or k / n < DEV_GATES["route"]:
        why.append(f"route accuracy {rate(k, n)} is under {DEV_GATES['route']:.0%}")
    for route in ROUTES:
        k, n = t.get(f"route:{route}", (0, 0))
        if n and k / n < DEV_GATES["per_desk"]:
            why.append(f"{route} recall {rate(k, n)} is under {DEV_GATES['per_desk']:.0%}")
    k, n = t.get("escalation", (0, 0))
    if n and k < n:
        why.append(f"escalation {rate(k, n)}: every escalation row must escalate")
    return why


def run_router(a) -> int:
    """--local and --live-l1."""
    desk_router, desk_routes = router()
    rows = load_rows(a.routes)
    why = check_rows(rows)
    if why:
        print("\n".join(f"FAIL  {w}" for w in why))
        return 1
    held = prompt_groups(rows)
    scored = [r for r in rows if (a.split == "all" or r["split"] == a.split) and r["group"] not in held]
    pool = index_rows(rows)
    if a.live_l1:
        if not a.project:
            raise SystemExit("--live-l1 needs --project (or PROJECT): it calls flash-lite, flash and text-embedding-005")
        models = desk_router.GeminiModels.for_project(a.project)
        vectors = dict(zip([r["id"] for r in pool], models.embed_many([r["question"] for r in pool])))
    else:
        vectors = {r["id"]: offline_embed(r["question"]) for r in pool}
        models = ScriptedModels(rows, vectors)
    classes = _tenant_classes()
    base = build_index(pool, vectors)
    indexes = {t: [e for e in base if e["route"] in desk_routes.enabled_routes(classes.get(t, ()))]
               for t in TENANTS if t not in SINGLE}
    runs = [route_run(scored, indexes, models) for _ in range(max(1, a.runs))]
    print(f"{'live: flash-lite, flash and text-embedding-005' if a.live_l1 else 'local: the classifier is scripted, so this measures the cascade, not a model'}")
    print(f"  {len(scored)} rows scored; {sum(1 for r in rows if r['group'] in held and (a.split == 'all' or r['split'] == a.split))} "
          f"left out (the groups of the prompt's examples); index of {len(base)} dev rows")
    result = score(scored, predictions(runs[0]), classes_from_manifest())
    report(result, "B", a.split)
    router_report(scored, runs[0])
    if len(runs) > 1:
        by_id = {r["id"]: r for r in scored}
        stable = [i for i in by_id if all(predictions([x for x in run if x["id"] == i])[i]["route"]
                                          in by_id[i]["acceptable_routes"] for run in runs)]
        flips = sorted({x["id"] for run in runs for x in run} - set(stable))
        print(f"  {f'pass^{len(runs)}':<30}{rate(len(stable), len(by_id))}; failing in some run: {', '.join(flips[:20]) or 'none'}")
    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            json.dump({"arm": "B", "split": a.split, "tally": result["tally"], "confusion": result["confusion"],
                       "rows": result["verdicts"], "decisions": [{"id": x["id"], **desk_router.record(x["decision"])}
                                                                 for x in runs[0]]}, f, indent=1)
    failures = gate_failures(result)
    for w in failures:
        print(f"FAIL  {w}")
    if not failures:
        print("the dev gates hold")
    return 1 if failures else 0


# --------------------------------------------------------------------- the deployed Desk (lesson 10.4)
LIVE_ARMS = ("B", "C", "Astar")         # every arm the deployed Desk serves a desk_eval caller
DESK_ROWS = ("handbook", "statute")     # the expected routes whose rows also go to POST /v1/desk
CODE_OUTCOMES = {"case": "case", "out_of_scope": "oos", "clarify": "clarify", "denied": "denied",
                 "not_covered": "not_covered"}
TOKEN_MAX_AGE_S = 45 * 60               # a Google ID token lasts an hour


def mint(account: str, audience: str) -> str | None:
    """A Google ID token minted as `account` for the chat service (make desk-operators lets you)."""
    import subprocess
    try:
        out = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email",
                              f"--impersonate-service-account={account}", f"--audiences={audience}"],
                             capture_output=True, text=True, check=True)
        return out.stdout.strip() or None
    except Exception as e:  # noqa: BLE001 - said once, and the run stops
        print(f"  could not mint a token as {account}: {str(getattr(e, 'stderr', '') or e).strip()[:200]}")
        return None


def post(base: str, path: str, token: str, body: dict, timeout: int = 150, sleep=None) -> tuple[int, object]:
    """(status, JSON or text); a 429 is waited out (Retry-After) up to three times."""
    import time
    import urllib.error
    import urllib.request
    sleep = sleep or time.sleep
    for attempt in range(4):
        req = urllib.request.Request(f"{base}{path}", data=json.dumps(body).encode(), method="POST",
                                     headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                status, raw = r.status, r.read().decode()
        except urllib.error.HTTPError as e:
            status, raw = e.code, e.read().decode()
            if status == 429 and attempt < 3:
                sleep(int(e.headers.get("Retry-After") or 60))
                continue
        except Exception as e:  # noqa: BLE001 - a call that did not arrive is a row the run lacks
            return 0, f"{type(e).__name__}: {e}"
        try:
            return status, json.loads(raw)
        except ValueError:
            return status, raw
    return 429, "still over the rate limit"


def percentile(values: list[float], p: float) -> float | None:
    """Nearest rank."""
    v = sorted(values)
    return v[max(0, math.ceil(p / 100 * len(v)) - 1)] if v else None


def live_prediction(row: dict, route: dict, desk: dict | None, arm: str) -> dict:
    """One row's prediction from the /v1/route answer and, for an answer or denial row, the /v1/desk answer."""
    d = route.get("decision") or {}
    got = route.get("route")
    pred = {"id": row["id"], "route": d.get("desk") if got in ("denied", "not_covered") else got,
            "case_type": route.get("case_type"), "model_calls": int(route.get("model_calls") or 0), "arm": arm}
    if desk is None:
        pred.update(outcome=CODE_OUTCOMES.get(got), citations=[], answer="", retrieve_calls=0)
    else:
        pred.update(outcome=desk.get("outcome"), citations=[c for c in desk.get("citations") or [] if isinstance(c, dict)],
                    answer=str(desk.get("answer") or ""), retrieve_calls=int(desk.get("retrieve_calls") or 0))
    return pred


def own_tenant(row: dict, path: str, reply) -> None:
    """Stops the run when a reply names another tenant than the row's (or none)."""
    got = reply.get("tenant") if isinstance(reply, dict) else None
    if got != row["tenant"]:
        raise SystemExit(f"{row['id']}: {path} answered {row['identity']} for tenant {got!r}, not {row['tenant']!r}: "
                         f"an eval account must be on its own tenant's roster alone")


def run_live(a, minter=mint, poster=post) -> int:
    """--live: every scored row as its eval account, to the deployed chat service's /v1/route, and each answer or
    denial row to /v1/desk too. Only the route set's eval accounts call (IDENTITIES), each on one roster; a reply that
    names another tenant than the row's, from either route, stops the run."""
    import time
    import uuid
    arm = a.arm or "B"
    if arm not in LIVE_ARMS:
        raise SystemExit(f"--live runs arm {', '.join(LIVE_ARMS)}, not {arm!r}")
    chat = (a.chat_url or os.environ.get("DOCUMIND_CHAT_URL") or "").rstrip("/")
    if not chat.startswith("https://") or not a.project:
        raise SystemExit("--live needs the chat service's URL (DOCUMIND_CHAT_URL or --chat-url, https) and --project: "
                         "make route-eval")
    rows = load_rows(a.routes)
    why = check_rows(rows)
    if why:
        print("\n".join(f"FAIL  {w}" for w in why))
        return 1
    held = prompt_groups(rows)
    scored = [r for r in rows if (a.split == "all" or r["split"] == a.split) and r["group"] not in held]
    strangers = sorted({r["identity"] for r in scored} - set(IDENTITIES))
    if strangers:
        raise SystemExit(f"identities with no eval account: {strangers} (IDENTITIES)")
    tokens: dict[str, tuple[float, str]] = {}

    def token(identity: str) -> str:
        hit = tokens.get(identity)
        if not hit or time.monotonic() - hit[0] > TOKEN_MAX_AGE_S:
            t = minter(identity_account(identity, a.project), chat)
            if not t:
                raise SystemExit("could not mint as the eval accounts: make desk-operators ADMIN_EMAILS=you@example.com")
            tokens[identity] = hit = (time.monotonic(), t)
        return hit[1]

    run_id, preds, cost, router_ms, latency, refused = uuid.uuid4().hex[:8], {}, 0.0, [], [], []
    print(f"live: {chat}, arm {arm} ({ARMS[arm]}), split {a.split}: {len(scored)} rows scored, "
          f"{sum(1 for r in rows if r['group'] in held and (a.split == 'all' or r['split'] == a.split))} left out "
          f"(the groups of the prompt's examples)")
    for r in scored:
        body = {"question": r["question"], **({"arm": arm} if arm != "B" else {})}
        if r["prev_question"]:
            body.update(prev_question=r["prev_question"], prev_route=r["prev_route"])
        status, route = poster(chat, "/v1/route", token(r["identity"]), body)
        if status != 200 or not isinstance(route, dict):
            refused.append(f"{r['id']}: /v1/route {status} {str(route)[:120]}")
            continue
        own_tenant(r, "/v1/route", route)
        cost += float(route.get("cost_inr") or 0)
        router_ms.append(float(route.get("router_ms") or 0))
        desk = None
        if r["expected_route"] in DESK_ROWS or r["expected_outcome"] == "denied":
            session = f"eval-{run_id}-{r['id']}"[:64]
            extra = {"arm": arm} if arm != "B" else {}
            if r["prev_question"]:
                status, first = poster(chat, "/v1/desk", token(r["identity"]),
                                       {"question": r["prev_question"], "session_id": session, **extra})
                if status == 200:
                    own_tenant(r, "/v1/desk", first)
            t0 = time.monotonic()
            status, desk = poster(chat, "/v1/desk", token(r["identity"]),
                                  {"question": r["question"], "session_id": session, **extra})
            if status != 200 or not isinstance(desk, dict):
                refused.append(f"{r['id']}: /v1/desk {status} {str(desk)[:120]}")
                desk = {"outcome": None, "citations": [], "answer": "", "retrieve_calls": 0}
            else:
                own_tenant(r, "/v1/desk", desk)
                latency.append((time.monotonic() - t0) * 1000)
        preds[r["id"]] = live_prediction(r, route, desk, arm)
    classes = classes_from_registry(a.registry) if a.registry else classes_from_manifest()
    result = score(scored, preds, classes)
    report(result, arm, a.split)
    n = max(len(router_ms), 1)
    print(f"  {'router cost':<30}Rs {cost:.4f} in all, Rs {cost / n:.5f} a turn")
    for label, vals in (("router_ms", router_ms), ("desk latency_ms", latency)):
        if vals:
            print(f"  {label:<30}p50 {percentile(vals, 50):.0f}  p95 {percentile(vals, 95):.0f}  over {len(vals)} turns")
    for w in refused:
        print(f"  not scored: {w}")
    if a.save:
        with open(a.save, "w", encoding="utf-8") as f:
            for p in preds.values():
                f.write(json.dumps(p, ensure_ascii=False) + "\n")
    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            json.dump({"arm": arm, "split": a.split, "tally": result["tally"], "confusion": result["confusion"],
                       "rows": result["verdicts"]}, f, indent=1)
    failures = gate_failures(result) if arm == "B" else []
    for w in failures:
        print(f"FAIL  {w}")
    return 1 if failures or refused else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--selftest", action="store_true", help="check the route set itself (offline, no cost)")
    ap.add_argument("--routes", default=ROUTES_FILE, help="the route set (default evals/routes.jsonl)")
    ap.add_argument("--predictions", help="a run to score: JSON lines {id, route, ...}")
    ap.add_argument("--split", choices=SPLITS + ("all",), default="dev")
    ap.add_argument("--arm", choices=sorted(ARMS), help="the arm this run is: B, C or Astar")
    ap.add_argument("--registry", help="an export of the doc_type registry; default: evals/manifest.json offline")
    ap.add_argument("--report", help="write every row's verdict here as JSON")
    ap.add_argument("--local", action="store_true", help="the router in process, scripted classifier (offline, CI)")
    ap.add_argument("--live-l1", action="store_true", help="the router in process with the real models (LIVE)")
    ap.add_argument("--project", default=os.environ.get("PROJECT"), help="your lane, for --live-l1")
    ap.add_argument("--runs", type=int, default=1, help="--live-l1: run every row this many times (pass^k)")
    ap.add_argument("--live", action="store_true", help="the deployed Desk, as each row's eval account (LIVE)")
    ap.add_argument("--chat-url", help="--live: the chat service's URL (default DOCUMIND_CHAT_URL)")
    ap.add_argument("--save", help="--live: write the run's predictions here, for --predictions later")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest(a.routes)
    if a.live:
        return run_live(a)
    if a.local or a.live_l1:
        return run_router(a)
    if not a.predictions:
        ap.error("--selftest, --predictions, --local, --live-l1 or --live")
    rows = load_rows(a.routes)
    why = check_rows(rows)
    if why:
        print("\n".join(f"FAIL  {w}" for w in why))
        return 1
    rows = [r for r in rows if a.split == "all" or r["split"] == a.split]
    preds = load_predictions(a.predictions, {r["id"] for r in load_rows(a.routes)})
    arm = run_arm(preds, a.arm)
    classes = classes_from_registry(a.registry) if a.registry else classes_from_manifest()
    result = score(rows, preds, classes)
    report(result, arm, a.split)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            json.dump({"arm": arm, "split": a.split, "tally": result["tally"], "confusion": result["confusion"],
                       "rows": result["verdicts"]}, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
