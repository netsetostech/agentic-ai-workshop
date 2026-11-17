#!/usr/bin/env python3
"""The eval gate. Exit code 0 merges; anything else blocks.

    python deploy/evals/run_eval.py                    # OFFLINE - no credentials, no cost
    python deploy/evals/run_eval.py --api-url URL      # LIVE    - needs a deployment
    python deploy/evals/run_eval.py --api-url URL --source hr_policy_2026.md   # LIVE, scoped to the rows citing one document

Two modes, because the gate has two halves that fail for different reasons and one of
them must run on every pull request.

OFFLINE is the half that runs in CI here (documind-dryrun.yml). It never calls Google.
It checks the golden set itself:

    falsifiable   every must_contain value really is in that tenant's corpus, and every
                  must_not_contain value really is in ANOTHER tenant's and not in its
                  own. build_golden.py asserts this when it WRITES the file; this
                  asserts it over the file that is actually committed, which is the one
                  CI runs. Those differ the moment somebody edits golden.jsonl by hand
                  to make a red build go green - which is the single most common way an
                  eval suite rots.
                  A `version` row (12 September 2026) is the ledger's: its must_contain is
                  the CURRENT version's figure, its must_not_contain a figure only a retired
                  version under evals/demo holds. It is what forces the rows to move with
                  the document, in the same commit: re-issue the handbook without moving
                  lk-06 and vr-01 and this check turns red before anything is deployed.
    anchors       every must_retrieve anchor is findable. evals/README.md left one
                  decision to this lesson: 12.5 mints chunk ids as {tenant}:{sha256}#{i}, which
                  contains neither the document slug nor the clause id, so the runner
                  matches each anchor against filename + text joined together.
                  NOTE the scope: this runs OFFLINE, over the corpus. /v1/query returns
                  citations, not the raw retrieved set, so the live half does not score
                  must_retrieve by default. DOCUMIND_EVAL_PASSAGES=1 reads each answerable
                  row's pool again from /v1/passages (workshop lesson 10.4: the same
                  retrieval and rerank, no model call) and prints must_retrieve_recall
                  beside quote_passage_rate - both [info], neither a threshold.
    coverage      the isolation and refusal rows still exist. Deleting a failing test
                  is the other common way a suite rots, and it looks like a green build.

LIVE is the half that needs a running service, and it is why this pipeline had to be
keyless. Be precise about that claim, because the loose version is wrong: this is not
the first STEP needing a credential - the build and the release authenticate before it,
in the same job. What is true is that nothing before the MERGE needs one. The offline
half above runs on every pull request with no Google credential at all, and the first
thing that does need one is this. A service-account JSON in a repository secret would
have been the easy way to provide it, and 12.7 is the lesson about not doing that.

LIVE sends EVERY row, not only the answerable ones - see live(). Scoring only the
answerable subset silently skipped all five refusal rows and four of the five isolation
rows, which is how a gate reports green over tests it never ran.

--source scopes the live half to the rows that cite one document (a slug in must_retrieve,
or the row's own `source`): a reindex is a release (deploy/INDEXING.md), and this is its
gate on a candidate - minutes, not the ten of the full set. A threshold with no rows in
scope is reported and not judged; a `version` row that cites a retired figure is a stale
answer and blocks on its own.

The threshold that matters live is NOT must_not_contain. Read WHY in check_isolation().

12 September 2026 - the gate learned to fail (course-bibles/review-rag-prod-plan-2026-09-12.md, R01). Before:

    a 200 whose body was {} counted as a refusal; a 500 on the version row cost one point of
    answerable_rate and never blocked; "60" was satisfied by "160 days"; a citation was any
    non-empty list; citation_rate and must_contain_rate divided by the ANSWERED rows, so 33
    correct of 47 read as 87%; a media row's figure was "[info]"; a missing outsider token
    printed a note and ran anyway.

Now every 200 is validated against the response schema (a malformed body is a failed request),
every non-200 is a failed request with one retry, request_success_rate must be 1.00, figures are
matched on their own boundaries, correct_rate is answered-and-right over ALL answerable rows,
every citation must name the row's tenant, its own document and a CURRENT version (GET /v1/sources),
media_kind_rate is a threshold, required.json names the rows that must exist and individually
pass, and the run refuses to start under IAP without the outsider's token. --report writes every
row's verdict, latency, stages and cache_hit to a JSON file: what the demo shows is that file.

8 October 2026 - the rows keep what was said. --report's records carry each answer (its first 600
characters) and its citations, as `cites`, so a failing row can be read without asking again.
row_verdict() is live()'s judgment of one row as a function of the reply alone, for the instruments
that judge answers outside the gate (the prompt bench); live() keeps its own inline copy, because
lessons quote it line by line, and tests/test_eval_rows.py holds the two equal. DOCUMIND_EVAL_PASSAGES=1
reads each answerable row's pool again (passage_checks()): every quote looked for in the passage it
cites, every must_retrieve anchor in the pool. An environment switch, not a flag, because lessons
quote main() and the eval-live recipe whole; with it off, every line printed is what it was.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "corpus")
DEMO = os.path.join(HERE, "demo")          # the rehearsal's retired versions: what a version row's must_not_contain lives in
GOLDEN = os.path.join(HERE, "golden.jsonl")
MANIFEST = os.path.join(HERE, "manifest.json")   # the documents each tenant owns: what a citation may name
REQUIRED = os.path.join(HERE, "required.json")   # the rows that must exist and must individually pass

# What a green run has to clear. Numbers, in one place, so raising a threshold is a
# reviewable line and not a conversation.
THRESHOLDS = {
    "request_success_rate": 1.00,  # every row sent came back 200 with a well-formed body: an error is not a refusal
    "answerable_rate": 0.80,       # of rows the corpus CAN answer, how many did
    "citation_rate": 0.95,         # of answered rows, how many carried a citation
    "citation_valid_rate": 1.00,   # of cited rows, how many cited ONLY the tenant's own, current documents
    "must_contain_rate": 0.85,     # of answered rows, how many held the expected figure (on its own boundary)
    "correct_rate": 0.68,          # answered AND right AND validly cited, over ALL answerable rows: 0.80 x 0.85, end to end
    "refusal_rate": 0.90,          # of rows the corpus CANNOT answer, how many were refused
    "media_kind_rate": 0.80,       # of rows asking for a figure or segment citation, how many got one (judged when any is in scope)
    "isolation_403_rate": 1.00,    # not 0.99. One leak is the whole product.
}
MIN_ROWS = {"isolation": 5, "refusal": 5, "lookup": 10, "join": 5, "version": 1}
STAGES = ("retrieve_ms", "rerank_ms", "generate_ms")


TEXT_FILES = (".md", ".txt")


def _text(path: str) -> str:
    """A text file's contents, the file closed again: open().read() left each one to the garbage collector, a
    ResourceWarning per corpus file wherever warnings show (13 October 2026)."""
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_corpus() -> dict[str, dict[str, str]]:
    """{tenant: {path_relative_to_corpus: text}}. Text is lower-cased once.

    Text files only. Since the real documents arrived (evals/real_sources.json) a tenant
    directory also holds PDFs - the objects upload.sh pushes - and, for each one with a
    text layer, the .md mirror fetch_real.py extracted beside it. The mirror is what a golden
    row is verified against; the PDF is bytes, and a scanned Act (posh_act_2013) has no
    mirror at all, so nothing here can assert on it."""
    out: dict[str, dict[str, str]] = {}
    for tenant in sorted(os.listdir(CORPUS)):
        d = os.path.join(CORPUS, tenant)
        if not os.path.isdir(d):
            continue
        out[tenant] = {}
        for fn in sorted(os.listdir(d)):
            p = os.path.join(d, fn)
            if os.path.isfile(p) and fn.endswith(TEXT_FILES):
                out[tenant][fn] = _text(p)
    return out


def load_demo() -> str:
    """Every retired version the rehearsal keeps under evals/demo, lower-cased: the text a version row's
    must_not_contain must live in, or the row asserts a staleness nothing could produce."""
    if not os.path.isdir(DEMO):
        return ""
    return "\n".join(_text(os.path.join(DEMO, fn)) for fn in sorted(os.listdir(DEMO)) if fn.endswith(TEXT_FILES)).lower()


def load_golden() -> list[dict]:
    with open(GOLDEN, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def haystack(corpus: dict, tenant: str) -> str:
    """THE MATCHING RULE, offline. Filenames joined with contents, because an anchor may
    be a document slug (hr_policy_2026 - only in the path) or a clause id (EXP-12 - only
    in the text).

    The same rule runs over chunk_id + source_uri + text on a real retrieval, which is the
    decision evals/README.md asked 12.7 to make: anchors_found(), over the pool /v1/passages
    returns, when DOCUMIND_EVAL_PASSAGES=1. /v1/query returns citations, not the retrieved
    set, so without the switch recall is not observed from outside the service."""
    docs = corpus.get(tenant, {})
    return "\n".join(f"{name}\n{text}" for name, text in docs.items()).lower()


def sources_of(row: dict, corpus: dict) -> set[str]:
    """The documents a row cites: the must_retrieve anchors that are document slugs in the row's tenant's corpus
    (a clause code is not a document), plus the row's own `source` when it names one."""
    slugs = {name.rsplit(".", 1)[0] for name in corpus.get(row["tenant"], {})}
    out = {a for a in row.get("must_retrieve", []) if a in slugs}
    if row.get("source"):
        out.add(row["source"].rsplit("/", 1)[-1].rsplit(".", 1)[0])
    return out


def in_scope(row: dict, source: str | None, corpus: dict) -> bool:
    if not source:
        return True
    return source.rsplit("/", 1)[-1].rsplit(".", 1)[0] in sources_of(row, corpus)


# ------------------------------------------------------------------ offline checks
def check_falsifiable(golden: list[dict], corpus: dict) -> list[str]:
    """A test that cannot fail is not a test. Prove each assertion could."""
    bad = []
    demo = load_demo()
    for row in golden:
        own = haystack(corpus, row["tenant"])
        # build_golden.py enforces these when it WRITES the file. Re-assert them over the
        # file that is actually committed: deleting an assertion is the cheapest way to
        # make a red row green, and it leaves the row in place looking like a test.
        if row["shape"] == "isolation" and not row.get("must_not_contain"):
            bad.append(f"{row['id']}: an isolation row with no must_not_contain asserts "
                       f"nothing about isolation")
        if row["answerable"] and not row.get("must_contain"):
            bad.append(f"{row['id']}: an answerable row with no must_contain accepts "
                       f"any answer at all")
        for want in row.get("must_contain", []):
            if want.lower() not in own:
                bad.append(f"{row['id']}: must_contain {want!r} is not in "
                           f"{row['tenant']}'s corpus - the row can only fail")
        if row["shape"] == "version":
            # The ledger's row. The figure it forbids must be ABSENT from the current version of its source
            # (or a correct answer fails) and PRESENT in a retired version under evals/demo (or nothing
            # stale could ever produce it). Re-issue the document without moving the row, and this is red.
            src = (row.get("source") or "").rsplit("/", 1)[-1]
            current = corpus.get(row["tenant"], {}).get(src, "").lower()
            if not src or not current:
                bad.append(f"{row['id']}: a version row must name a text document of its tenant as `source`")
            if not row.get("must_not_contain"):
                bad.append(f"{row['id']}: a version row with no must_not_contain asserts nothing about staleness")
            for never in row.get("must_not_contain", []):
                if never.lower() in current:
                    bad.append(f"{row['id']}: must_not_contain {never!r} IS in the current version of "
                               f"{src} - the row fails on a correct answer; move the row with the document")
                if never.lower() not in demo:
                    bad.append(f"{row['id']}: must_not_contain {never!r} is in no retired version under "
                               f"evals/demo - nothing stale holds it, so the row is decoration")
            continue
        for never in row.get("must_not_contain", []):
            if never.lower() in own:
                bad.append(f"{row['id']}: must_not_contain {never!r} IS in "
                           f"{row['tenant']}'s own corpus - the row fails on a "
                           f"correct answer")
            elsewhere = [t for t in corpus
                         if t != row["tenant"] and never.lower() in haystack(corpus, t)]
            if not elsewhere:
                bad.append(f"{row['id']}: must_not_contain {never!r} is in no OTHER "
                           f"tenant's corpus - there is nothing to leak, so the row "
                           f"is decoration")
    return bad


def check_anchors(golden: list[dict], corpus: dict) -> list[str]:
    """Every must_retrieve anchor must be findable under the matching rule above."""
    bad = []
    for row in golden:
        own = haystack(corpus, row["tenant"])
        for anchor in row.get("must_retrieve", []):
            if anchor.lower() not in own:
                bad.append(f"{row['id']}: anchor {anchor!r} matches nothing in "
                           f"{row['tenant']}'s corpus (slug? clause id? typo?)")
    return bad


def load_required() -> list[str]:
    """The ids that must exist and must individually pass live: every version row, every isolation row, every
    row that asks for a media citation. A manifest, not a rule in code, so that removing one is a reviewed diff."""
    with open(REQUIRED, encoding="utf-8") as f:
        return list(json.load(f)["ids"])


def mandatory(row: dict) -> bool:
    return row["shape"] in ("version", "isolation") or bool(row.get("must_cite_kind"))


def check_coverage(golden: list[dict]) -> list[str]:
    """Deleting the failing rows is not a fix, and it looks exactly like a green run.

    Two rules. Per shape, MIN_ROWS: a whole slice cannot shrink below what proves anything. Per row,
    required.json: a version, isolation or media row cannot vanish (MIN_ROWS would not notice one of eleven
    isolation rows going), and one cannot be added without being listed, so the manifest and the file agree."""
    counts: dict[str, int] = {}
    for row in golden:
        counts[row["shape"]] = counts.get(row["shape"], 0) + 1
    bad = [f"shape {shape!r}: {counts.get(shape, 0)} rows, expected at least {n}"
           for shape, n in MIN_ROWS.items() if counts.get(shape, 0) < n]
    ids = {r["id"] for r in golden}
    required = load_required()
    bad += [f"required.json names {rid!r} and golden.jsonl no longer has it" for rid in required if rid not in ids]
    bad += [f"{r['id']}: a {r['shape']}{' media' if r.get('must_cite_kind') else ''} row that required.json does not list"
            for r in golden if mandatory(r) and r["id"] not in required]
    return bad


def offline() -> int:
    corpus, golden = load_corpus(), load_golden()
    print(f"  {len(golden)} golden rows over {len(corpus)} tenants, "
          f"{sum(len(v) for v in corpus.values())} documents\n")
    failures = []
    for name, found in (("falsifiable", check_falsifiable(golden, corpus)),
                        ("anchors", check_anchors(golden, corpus)),
                        ("coverage", check_coverage(golden))):
        print(f"  [{'FAIL' if found else 'PASS'}] {name}")
        for line in found:
            print(f"         {line}")
        failures += found
    print()
    if failures:
        print(f"  {len(failures)} problem(s). The golden set cannot judge the model "
              f"until it judges itself.")
        return 1
    print("  The golden set is sound. It can go red, and it still contains the rows "
          "that would.")
    return 0


# ------------------------------------------------------------- the figure, not the spelling
_SMALL = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
          "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
          "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
          "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
          "seventy": 70, "eighty": 80, "ninety": 90}
_SCALE = {"hundred": 100, "thousand": 1000, "lakh": 100000, "crore": 10000000}
_WORD = "|".join(list(_SMALL) + list(_SCALE))
_NUMWORDS = re.compile(r"\b(?:(?:%s)(?:[\s-]+(?:%s))*)\b" % (_WORD, _WORD))


def _to_int(run: str) -> int:
    total = current = 0
    for w in re.split(r"[\s-]+", run):
        if w in _SMALL:
            current += _SMALL[w]
        elif w == "hundred":
            current = (current or 1) * 100
        elif w in _SCALE:
            total += (current or 1) * _SCALE[w]
            current = 0
    return total + current


def normalise(text: str) -> str:
    """Lower-case, thousands separators out, number words to digits - on BOTH sides of every
    live containment check, so "twelve weeks" and "12 weeks" are the same fact.

    The third live eval (7 Sept 2026) answered lk-23 with "300 or more" against a row that
    says "three hundred", and jn-08 with "12 weeks" against "twelve weeks": the right figure
    in the statute's own spelling, scored as wrong. must_contain measures the figure; this
    makes the check say so. Nothing else is relaxed - the words around the number must still
    match - and must_not_contain gets the same treatment, so a leak spelt "26 weeks" is
    caught where "twenty-six weeks" alone would have let it through.

    The second media eval (9 Sept 2026) added two more spellings of a right answer: "set-on and
    set-off" against a row that says "set on" (mm-02), and "5.2%" against "5.2 per cent" (mm-03,
    the figure the segment prompt had just learned to keep). A hyphen is a space and per cent is
    %, on both sides - the figure, not the typography."""
    t = text.lower().replace(",", "").replace("-", " ")
    for spelled in (" per cent", "per cent", " percent", "percent"):
        t = t.replace(spelled, "%")
    return _NUMWORDS.sub(lambda m: str(_to_int(m.group(0))), t)


def contains(text: str, want: str) -> bool:
    """normalise() on both sides, then the figure has to stand on its own: "60" is not in "160 days" or
    "3600", "8.33" is in "8.33%" and not in "18.33". The third live eval scored "300 or more" against
    "three hundred" as wrong; the review of 12 September found the opposite blind spot - eight rows carry a
    bare numeral that any larger number containing it satisfied."""
    w = normalise(want).strip()
    if not w:
        return False
    return re.search(r"(?<![\w.])" + re.escape(w) + r"(?![\w]|\.\d)", normalise(text)) is not None


# --------------------------------------------------------------------- live checks
def validate_body(body) -> str | None:
    """The response schema, or why this is not one. A 200 whose body is {} used to count as a refusal
    (nothing there said answerable=True); it is a failed request, and it says so."""
    if not isinstance(body, dict):
        return "body is not an object"
    for key, kind in (("answer", str), ("citations", list), ("answerable", bool)):
        if not isinstance(body.get(key), kind):
            return f"{key} missing or not a {kind.__name__}"
    if body.get("confidence") not in ("high", "medium", "low"):
        return "confidence not one of high / medium / low"
    for i, c in enumerate(body["citations"]):
        if not isinstance(c, dict) or not all(isinstance(c.get(k), str) and c.get(k) for k in ("chunk_id", "source_uri", "quote")):
            return f"citation {i} lacks chunk_id / source_uri / quote"
    return None


def _ask_once(api_url: str, question: str, tenant: str, email: str, token: str | None):
    body = json.dumps({"query": question, "tenant_id": tenant, "top_k": 6}).encode()
    req = urllib.request.Request(f"{api_url.rstrip('/')}/v1/query", data=body,
                                 method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("x-user-email", email)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, json.loads(r.read()), int((time.time() - t0) * 1000)
    except urllib.error.HTTPError as e:
        return e.code, {}, int((time.time() - t0) * 1000)
    except Exception as e:
        return 0, {"error": type(e).__name__}, int((time.time() - t0) * 1000)


RETRY_AFTER_429_S = 30   # the Retry-After rag-api's main.py sends with a model 429


def ask(api_url: str, question: str, tenant: str, email: str, token: str | None, retries: int = 1):
    """POST /v1/query. Returns (status, body, latency_ms). AUTH_MODE=dev accepts x-user-email; under IAP the
    identity comes from the assertion and the header is ignored. A 5xx, a timeout or a transport error is retried
    ONCE after two seconds and then counted: one retry separates a blip from an outage, more would hide one. A 429 is
    the one 4xx retried, once, after the Retry-After the API sends with it: the model's shared capacity said "not
    now", not "never". Before the API answered a model 429 as a 429 it arrived here as a 500 and got this same retry
    (21 October 2026)."""
    status, body, ms = _ask_once(api_url, question, tenant, email, token)
    for _ in range(retries):
        if status == 200 or (400 <= status < 500 and status != 429):
            break
        time.sleep(RETRY_AFTER_429_S if status == 429 else 2)
        status, body, ms = _ask_once(api_url, question, tenant, email, token)
    return status, body, ms


def fetch_current_shas(api_url: str, tenant: str, token: str | None) -> set[str] | None:
    """The shas of the tenant's CURRENT versions from GET /v1/sources (the ledger, 12.5): a citation whose chunk
    id carries another sha names a retired or unknown version. None when the endpoint is unavailable - then the
    version check is reported as skipped, never as passed."""
    req = urllib.request.Request(f"{api_url.rstrip('/')}/v1/sources?tenant_id={tenant}")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            rows = json.loads(r.read()).get("sources") or []
    except Exception:  # noqa: BLE001
        return None
    return {str(s.get("doc_key") or "").split("_", 1)[-1] for s in rows if s.get("status") == "indexed"}


MEDIA_KINDS = {".png": "figure", ".jpg": "figure", ".jpeg": "figure", ".mp4": "segment", ".mp3": "segment"}   # the worker's MEDIA_TYPES


def fetch_media_names(api_url: str, tenant: str, token: str | None) -> dict[str, set[str]] | None:
    """{kind: {file names}} of the tenant's CURRENT media versions, from GET /v1/sources: a picture is a figure, a video
    or an audio file is segments. None when the endpoint is unavailable - then every media row is asked for its kind."""
    req = urllib.request.Request(f"{api_url.rstrip('/')}/v1/sources?tenant_id={tenant}")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            rows = json.loads(r.read()).get("sources") or []
    except Exception:  # noqa: BLE001
        return None
    out: dict[str, set[str]] = {}
    for s in rows:
        name = str(s.get("name") or "").rsplit("/", 1)[-1]
        kind = MEDIA_KINDS.get(os.path.splitext(name)[1].lower())
        if kind and s.get("status") == "indexed":
            out.setdefault(kind, set()).add(name)
    return out


def as_media_stands(row: dict, media: dict[str, set[str]] | None) -> dict:
    """The row as the live gate asks it today. A row that wants a figure or a segment keeps must_cite_kind only while
    the tenant holds a current file of that kind named after one of its must_retrieve documents (annual_report_2026_
    fig3.png for annual_report_2026, townhall_2026_q1.mp4 for townhall_2026_q1). Until then it is judged as the text
    lookup it is - the words and the citations - and marked media_absent. Before lesson 7.5 builds the town hall's
    video, mm-03 asked for a segment that could not exist yet and kept every full gate red (22 October 2026)."""
    want = row.get("must_cite_kind")
    if not want or media is None:
        return row
    if any(n.startswith(doc) for doc in row.get("must_retrieve", []) for n in media.get(want, ())):
        return row
    return {**{k: v for k, v in row.items() if k != "must_cite_kind"}, "media_absent": want}


def load_manifest_objects() -> dict[str, set[str]]:
    """{tenant: {object names}} from manifest.json - the documents make ingest-corpus uploads for each tenant."""
    try:
        with open(MANIFEST, encoding="utf-8") as f:
            docs = json.load(f)
    except FileNotFoundError:
        return {}
    out: dict[str, set[str]] = {}
    for d in docs:
        out.setdefault(d["tenant_id"], set()).add(d["gcs_uri"].split("/", 3)[-1])
    return out


_SHA = re.compile(r"^[0-9a-f]{64}$")


def judge_citations(row: dict, citations: list[dict], current: set[str] | None, manifest: dict[str, set[str]],
                    corpus_text: str) -> tuple[bool, bool, list[str]]:
    """(valid, quotes_supported, reasons). Valid means every citation names the row's tenant (the chunk id's
    prefix and the object's folder) and, when the id carries a worker sha and the ledger is readable, a CURRENT
    version. Quote support - the quoted words found in the tenant's corpus text - is reported, not a threshold: a
    Doc AI extraction and a pypdf mirror hyphenate differently, and that is not a wrong citation."""
    valid, supported, why = True, True, []
    for c in citations:
        cid, uri = c.get("chunk_id", ""), c.get("source_uri", "")
        if not cid.startswith(row["tenant"] + ":"):
            valid = False
            why.append(f"chunk {cid[:40]} is not {row['tenant']}'s")
        obj = uri.split("/", 3)[-1] if uri.startswith("gs://") else uri
        if obj.split("/", 1)[0] != row["tenant"]:
            valid = False
            why.append(f"source {uri[:60]} is not under {row['tenant']}/")
        elif manifest.get(row["tenant"]) and obj not in manifest[row["tenant"]]:
            why.append(f"source {obj} is not in manifest.json (uploaded outside make ingest-corpus?)")
        sha = cid.split(":", 1)[-1].split("#", 1)[0]
        if current is not None and _SHA.match(sha) and sha not in current:
            valid = False
            why.append(f"chunk {cid[:40]} is a version the ledger does not list as current")
        quote = re.sub(r"\s+", " ", c.get("quote", "")).strip().lower()
        if quote and quote not in corpus_text:
            supported = False
    return valid, supported, why


def pct(values: list[int], q: float) -> int:
    if not values:
        return 0
    s = sorted(values)
    return s[max(0, int(round(q * len(s))) - 1)]


def check_isolation(api_url, golden, token, outsider_token=None) -> tuple[float, list[str]]:
    """The isolation gate, and it is NOT must_not_contain.

    retriever.py filters by tenant BEFORE anything reaches the generator - Vector
    Search restricts on tenant_id, and the Firestore fallback carries the same
    equality predicate. So no chunk from another tenant is ever in the context, and
    must_not_contain can only fail if the model invents another tenant's exact figure
    out of nothing. That is a hallucination lottery, and a gate that fires by chance
    is not a gate.

    The leg that can actually leak is the other one: identity -> tenant. That is
    enforce_membership() in auth.py, a Firestore lookup, and lookups can be loosened.
    So the gate asks as somebody who is NOT on the roster and requires a 403.
    """
    outsider = os.environ.get("DOCUMIND_OUTSIDER_EMAIL", "outsider@not-a-tenant.invalid")
    # Under IAP (AUTH_MODE=iap) the API ignores x-user-email: the caller IS the bearer token's
    # account (shared/iap.py's other leg). So the outsider has to be a second token, minted
    # for an account that may invoke the service and sits on no roster - `make eval-live`
    # mints it for documind-outsider-sa (sa.tf). With one token every row would carry the same, rostered identity
    # and this gate could not turn red.
    rows = [r for r in golden if r["shape"] == "isolation"]
    got, bad = 0, []
    for row in rows:
        status, _, _ = ask(api_url, row["question"], row["tenant"], outsider, outsider_token or token)
        if status == 403:
            got += 1
        else:
            bad.append(f"{row['id']}: a non-member asking {row['tenant']} got "
                       f"{status}, expected 403")
    return (got / len(rows) if rows else 0.0), bad


def live(api_url: str, source: str | None = None, report: str | None = None, golden: list[dict] | None = None) -> int:
    corpus = load_corpus()
    if golden is None:
        golden = [r for r in load_golden() if in_scope(r, source, corpus)]
    if source:
        print(f"  scoped to {source}: {len(golden)} row(s) cite it")
        if not golden:
            print("  no golden row cites this document - the gate has nothing to judge; add a row before the reindex")
            return 1
    token = os.environ.get("DOCUMIND_ID_TOKEN") or None
    outsider_token = os.environ.get("DOCUMIND_OUTSIDER_TOKEN") or None
    member = os.environ.get("DOCUMIND_USER_EMAIL", "eval@documind.in")
    if token and not outsider_token and any(r["shape"] == "isolation" for r in golden):
        # Under IAP the API ignores x-user-email: with one token every isolation row would ask as the same
        # rostered account and could only fail. Refuse to start rather than spend ten minutes proving that.
        print("  DOCUMIND_ID_TOKEN is set and DOCUMIND_OUTSIDER_TOKEN is empty: under IAP the isolation rows cannot "
              "be judged. Mint one for documind-outsider-sa (make eval-live does) and run again.")
        return 2
    required = set(load_required())
    manifest = load_manifest_objects()
    text_of = {t: re.sub(r"\s+", " ", haystack(corpus, t)) for t in corpus}   # for quote support
    current: dict[str, set[str] | None] = {}
    media = {t: fetch_media_names(api_url, t, token) for t in sorted({r["tenant"] for r in golden if r.get("must_cite_kind")})}
    golden = [as_media_stands(r, media.get(r["tenant"])) for r in golden]
    for r in golden:
        if r.get("media_absent"):
            print(f"  [info] {r['id']}: no {r['media_absent']} file of {', '.join(r['must_retrieve'])} indexed for {r['tenant']}"
                  f" yet: judged as a text lookup, the {r['media_absent']} citation not asked (make media builds it)")

    # EVERY row is sent, not just the answerable ones.
    #
    # The first version of this loop iterated `[r for r in golden if r["answerable"]]`, which
    # silently dropped all five refusal rows AND four of the five isolation rows (iso-02..05
    # are answerable:false). So the leak tests carrying ACME's invoice total, Form 16 date,
    # revenue and PAN were never asked, and a model that fabricated an answer to every
    # unanswerable question would have scored a clean 100%.
    answerable_rows = [r for r in golden if r["answerable"]]
    unanswerable_rows = [r for r in golden if not r["answerable"]]
    isolation_rows = [r for r in golden if r["shape"] == "isolation"]
    ok_rows = answered = cited = cit_rows = cit_valid = contained = correct = refused = 0
    kind_rows = kind_hits = quote_rows = quote_ok = 0
    leaks: list[str] = []
    stale: list[str] = []      # a version row that cited a retired figure: the ledger's promise broken, or a row that did not move
    misses: list[str] = []     # every row that cost a point, with what the API said
    required_failed: list[str] = []
    records: list[dict] = []
    for row in golden:
        status, body, ms = ask(api_url, row["question"], row["tenant"], member, token)
        rec = {"id": row["id"], "shape": row["shape"], "tenant": row["tenant"], "status": status, "latency_ms": ms,
               "outcome": "ok", "pass": False, "why": ""}
        tag = f"{row['id']:6} {row['shape']:9} {row['tenant']:7}"
        if status != 200:
            rec["outcome"] = "denied" if status in (401, 403) else "error"
            rec["why"] = f"HTTP {status}" + (f" {body.get('error')}" if body.get("error") else "")
            misses.append(f"{tag} {rec['why']:14} | {row['question'][:70]}")
        else:
            problem = validate_body(body)
            if problem:
                rec["outcome"] = "malformed"
                rec["why"] = problem
                misses.append(f"{tag} MALFORMED {problem} | {row['question'][:60]}")
        if rec["outcome"] != "ok":
            if row["id"] in required:
                required_failed.append(f"{row['id']}: {rec['why']}")
            records.append(rec)
            continue
        ok_rows += 1
        rec.update({"answerable": body["answerable"], "confidence": body["confidence"], "citations": len(body["citations"]),
                    "api_latency_ms": body.get("latency_ms"), "stages": body.get("stages") or {},
                    "cache_hit": body.get("cache_hit", "none"), "model": body.get("model"), "backend": body.get("backend")})
        # What was said, so a failing row can be read from the report without asking again (W2-A). `citations` stays
        # the count it always was; `cites` is the list, without media_url, a signed link that expires.
        rec["answer"] = body["answer"][:600]
        rec["cites"] = [{k: c.get(k) for k in ("chunk_id", "source_uri", "page", "kind", "quote", "score")} for c in body["citations"]]
        text = normalise(body["answer"])

        # must_not_contain is checked on EVERY 200, whatever the row's shape. A leak in a
        # refusal row is the same leak; a retired figure in a version row is a stale answer.
        for never in row.get("must_not_contain", []):
            if contains(text, never):
                (stale if row["shape"] == "version" else leaks).append(f"{row['id']}: answer contained {never!r}")
                rec["why"] = f"answer contained {never!r}"

        if row["answerable"]:
            if body["answerable"]:
                answered += 1
                if body["citations"]:
                    cited += 1
                    cit_rows += 1
                    if row["tenant"] not in current:
                        current[row["tenant"]] = fetch_current_shas(api_url, row["tenant"], token)
                    valid, supported, why = judge_citations(row, body["citations"], current[row["tenant"]], manifest,
                                                            text_of.get(row["tenant"], ""))
                    quote_rows += 1
                    quote_ok += supported
                    cit_valid += valid
                    if not valid:
                        misses.append(f"{tag} INVALID CITATION {'; '.join(why)[:160]}")
                        rec["why"] = "; ".join(why)
                else:
                    valid = False
                    rec["why"] = "answered without a citation"
                    misses.append(f"{tag} answered with no citation | {text[:60]!r}")
                want_kind = row.get("must_cite_kind")
                kind_ok = True
                if want_kind:
                    # A figure or a segment citation, not only the right words: the media is
                    # in the corpus (make media, make ingest-corpus) or this row says it is not.
                    kind_rows += 1
                    kinds = sorted({c.get("kind", "text") for c in body["citations"]})
                    kind_ok = want_kind in kinds
                    kind_hits += kind_ok
                    if not kind_ok:
                        misses.append(f"{tag} cited no {want_kind} (kinds {kinds}) | {row['question'][:60]}")
                        rec["why"] = f"cited no {want_kind}"
                has = all(contains(text, w) for w in row.get("must_contain", []))
                if has:
                    contained += 1
                else:
                    misses.append(f"{tag} answered without {row.get('must_contain')} | {text[:80]!r}")
                    rec["why"] = f"answered without {row.get('must_contain')}"
                rec["pass"] = has and valid and kind_ok and not rec["why"].startswith("answer contained")
                correct += rec["pass"]
            else:
                misses.append(f"{tag} REFUSED conf={body['confidence']} cites={len(body['citations'])} | {row['question'][:70]}")
                rec["why"] = "refused"
        else:
            # The corpus cannot answer this. Saying so IS the right answer.
            if not body["answerable"]:
                refused += 1
                rec["pass"] = not rec["why"]
            else:
                misses.append(f"{tag} ANSWERED (should refuse) | {text[:80]!r}")
                rec["why"] = "answered, should refuse"
        if row["id"] in required and not rec["pass"]:
            required_failed.append(f"{row['id']}: {rec['why'] or 'failed'}")
        records.append(rec)

    # DOCUMIND_EVAL_PASSAGES=1: each answerable row's pool read again, its quotes and anchors looked for in it. Off by
    # default, and an environment switch rather than a flag: main() and the eval-live recipe stay as lessons quote them.
    pq = passage_checks(api_url, golden, records, member, token) if os.environ.get("DOCUMIND_EVAL_PASSAGES") == "1" else None

    n = len(answerable_rows)
    u = len(unanswerable_rows)
    iso_rate, iso_bad = check_isolation(api_url, golden, token, outsider_token)
    scores = {
        "request_success_rate": ok_rows / len(golden) if golden else 0.0,
        "answerable_rate": answered / n if n else 0.0,
        "citation_rate": cited / max(answered, 1),
        "citation_valid_rate": cit_valid / max(cit_rows, 1),
        "must_contain_rate": contained / max(answered, 1),
        "correct_rate": correct / n if n else 0.0,
        "refusal_rate": refused / u if u else 0.0,
        "media_kind_rate": kind_hits / max(kind_rows, 1),
        "isolation_403_rate": iso_rate,
    }
    # A threshold with no rows behind it is not judged: a scoped run (--source) may hold no refusal or isolation
    # row, and 0 of 0 refused is not a failing rate - it is an absence, and it is printed as one.
    rows_behind = {"request_success_rate": len(golden), "answerable_rate": n, "citation_rate": answered,
                   "citation_valid_rate": cit_rows, "must_contain_rate": answered, "correct_rate": n,
                   "refusal_rate": u, "media_kind_rate": kind_rows, "isolation_403_rate": len(isolation_rows)}
    judged = {k for k in THRESHOLDS if rows_behind[k] > 0}
    missed = {k for k in judged if scores[k] < THRESHOLDS[k]}
    failures = [f"{k}: {scores[k]:.0%} < {THRESHOLDS[k]:.0%}" for k in sorted(missed)]

    print(f"  {len(golden)} rows ({len(answerable_rows)} answerable, {len(unanswerable_rows)} not) against {api_url}\n")
    for k, v in scores.items():
        tag = "[FAIL]" if k in missed else ("[PASS]" if k in judged else "[ -- ]")
        print(f"  {tag} {k:21} {v:6.1%}  (threshold {THRESHOLDS[k]:.0%}{'' if k in judged else '; no rows in scope'}; {rows_behind[k]} rows)")
    if quote_rows:
        print(f"  [info] {'quote_support_rate':21} {quote_ok / quote_rows:6.1%}  (quoted words found in the tenant's corpus text; "
              f"not a threshold - a Doc AI extraction and a pypdf mirror hyphenate differently)")
    for line in passage_info(pq) if pq else ():
        print(line)
    skipped = [t for t, v in current.items() if v is None]
    if skipped:
        print(f"  [info] version check skipped for {', '.join(sorted(skipped))}: GET /v1/sources was unavailable")
    for line in iso_bad + leaks + stale:
        print(f"         {line}")

    # Where the rows landed, per shape - the demo's table - and where the time went, from the API's own clocks.
    print("\n  shape        rows   ok   pass")
    for shape in ("lookup", "join", "refusal", "isolation", "version"):
        rs = [r for r in records if r["shape"] == shape]
        if rs:
            print(f"  {shape:10} {len(rs):6} {sum(r['outcome'] == 'ok' for r in rs):4} {sum(r['pass'] for r in rs):6}")
    okr = [r for r in records if r["outcome"] == "ok"]
    lat = [r["latency_ms"] for r in okr]
    if lat:
        line = f"  latency ms  p50 {pct(lat, 0.5):5}  p95 {pct(lat, 0.95):5}   (round trip, {len(lat)} rows)"
        for st in STAGES:
            vals = [int(r["stages"].get(st, 0)) for r in okr if r.get("stages")]
            if vals:
                line += f"\n  {st:11} p50 {pct(vals, 0.5):5}  p95 {pct(vals, 0.95):5}"
        hits = sum(r.get("cache_hit") == "semantic" for r in okr)
        pools = [int(r["stages"].get("pool", 0)) for r in okr if r.get("stages")]
        if pools:
            line += f"\n  pool        avg {sum(pools) / len(pools):5.1f}   semantic cache hits {hits}"
        print(line)
    if misses:
        print(f"\n  rows that cost a point ({len(misses)}):")
        for line in misses:
            print(f"    {line}")
    if required_failed:
        print(f"\n  required rows that did not pass ({len(required_failed)}) - each one blocks on its own:")
        for line in required_failed:
            print(f"    {line}")
    print()
    if report:
        os.makedirs(os.path.dirname(os.path.abspath(report)), exist_ok=True)
        with open(report, "w", encoding="utf-8") as f:
            json.dump({"api_url": api_url, "source": source, "rows": len(golden), "scores": scores, "thresholds": THRESHOLDS,
                       "judged": sorted(judged), "failed": sorted(missed), "leaks": leaks, "stale": stale,
                       "isolation": iso_bad, "required_failed": required_failed,
                       "quote_support_rate": (quote_ok / quote_rows) if quote_rows else None,
                       "version_check_skipped": sorted(skipped), "records": records,
                       **({"passage_checks": pq} if pq else {})}, f, indent=1)
        print(f"  report: {report}")
    # A must_not_contain hit is not in the thresholds, on purpose - see
    # check_isolation. It is still printed, and it is still a stop-everything.
    if leaks:
        print("  A must_not_contain row fired. That should be near-impossible given "
              "the retrieval filter, which makes it MORE serious, not less.")
        return 2
    if stale:
        print("  A version row cited a RETIRED figure. Either the ledger served a version it should have retired, or "
              "the document was re-issued and the golden rows did not move with it. Blocked.")
        failures.append("stale: a retired version was cited")
    if required_failed:
        failures.append(f"required: {len(required_failed)} mandatory row(s) did not pass")
    if failures:
        print(f"  Blocked: {'; '.join(failures)}")
        return 1
    print("  All thresholds met.")
    return 0


def row_verdict(row: dict, status: int, body, current: set[str] | None = None,
                manifest: dict[str, set[str]] | None = None, corpus_text: str = "") -> dict:
    """live()'s judgment of one row, as a function of the reply alone (W2-A): the rule for every instrument that judges
    answers outside the gate - the prompt bench asks generate() itself, and must score a row exactly as the gate would.

    live() keeps its own copy of the rule, inline, because lessons quote its lines verbatim and a quoted line cannot
    move; tests/test_eval_rows.py holds the two equal over every golden row and every kind of reply. The inputs are what
    live() holds at that point: `current` the tenant's current shas (fetch_current_shas(); None skips the version
    check), `manifest` load_manifest_objects(), `corpus_text` the tenant's haystack() with its whitespace collapsed.

    Returns the record's outcome, pass and why, and the facts the rates count: answered (an answerable row the API
    answered), refused (an unanswerable row it refused), cited, valid (every citation the tenant's own and current;
    False when it answered without one), supported (quote support, when cited), kind_ok (when the row asks for a media
    kind), contained (every must_contain figure, when answered), and the leaks and stale lines live() lists. A fact
    that does not apply to the row is None."""
    v = {"outcome": "ok", "pass": False, "why": "", "answered": False, "refused": False, "cited": False, "valid": None,
         "supported": None, "kind_ok": None, "contained": None, "leaks": [], "stale": []}
    if status != 200:
        error = body.get("error") if isinstance(body, dict) else None
        v["outcome"] = "denied" if status in (401, 403) else "error"
        v["why"] = f"HTTP {status}" + (f" {error}" if error else "")
        return v
    problem = validate_body(body)
    if problem:
        v["outcome"], v["why"] = "malformed", problem
        return v
    text = normalise(body["answer"])
    for never in row.get("must_not_contain", []):
        if contains(text, never):
            v["stale" if row["shape"] == "version" else "leaks"].append(f"{row['id']}: answer contained {never!r}")
            v["why"] = f"answer contained {never!r}"
    if not row["answerable"]:
        if body["answerable"]:
            v["why"] = "answered, should refuse"
        else:
            v["refused"], v["pass"] = True, not v["why"]
        return v
    if not body["answerable"]:
        v["why"] = "refused"
        return v
    v["answered"], v["cited"], v["valid"] = True, bool(body["citations"]), False
    if v["cited"]:
        v["valid"], v["supported"], why = judge_citations(row, body["citations"], current, manifest or {}, corpus_text)
        if not v["valid"]:
            v["why"] = "; ".join(why)
    else:
        v["why"] = "answered without a citation"
    want = row.get("must_cite_kind")
    if want:
        v["kind_ok"] = want in {c.get("kind", "text") for c in body["citations"]}
        if not v["kind_ok"]:
            v["why"] = f"cited no {want}"
    v["contained"] = all(contains(text, w) for w in row.get("must_contain", []))
    if not v["contained"]:
        v["why"] = f"answered without {row.get('must_contain')}"
    v["pass"] = v["contained"] and v["valid"] and v["kind_ok"] is not False and not v["why"].startswith("answer contained")
    return v


QUOTE_VERDICTS = ("own", "elsewhere", "absent", "substituted", "unread")   # quote_check()'s five, one per citation


def passages(api_url: str, question: str, tenant: str, email: str, token: str | None, top_k: int = 6,
             retries: int = 1) -> list[dict] | None:
    """POST /v1/passages (W2-A), the route shared/documind_tools.retrieve(passages=True) calls (workshop lesson 10.4):
    the same door, identity, roster, retrieval and rerank as /v1/query, then the pool itself - each chunk's id, source,
    page, kind and full text - and no model call. The body is ask()'s, top_k 6 included (the one knob retrieve() and
    rerank() read), so this is the pool the row's answer was drawn from; the headers are ask()'s too. A 5xx, a timeout
    or a transport error is asked once more after two seconds, as ask() does; a 4xx is an answer.

    Returns the passages, or None when there is no pool to read: an error, a body that is not the route's, or the
    Desk's door answering in the route's place (passages [] beside an answer). None leaves the row's quotes unread and
    its anchors out of the recall: a pool that could not be read is not a pool that missed."""
    data = json.dumps({"query": question, "tenant_id": tenant, "top_k": top_k}).encode()
    for attempt in range(1 + retries):
        if attempt:
            time.sleep(2)
        req = urllib.request.Request(f"{api_url.rstrip('/')}/v1/passages", data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("x-user-email", email)
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                got = json.loads(r.read())
        except urllib.error.HTTPError as e:
            if 400 <= e.code < 500:
                return None
            continue
        except Exception:  # noqa: BLE001 - a timeout, a reset, a body that is not JSON: asked once more
            continue
        pool = got.get("passages") if isinstance(got, dict) else None
        if not isinstance(pool, list) or (not pool and got.get("answer")):
            return None
        return [p for p in pool if isinstance(p, dict)]
    return None


def quote_check(citation: dict, pool: list[dict] | None) -> str:
    """One verdict per citation, from QUOTE_VERDICTS, against the pool its row's question retrieves (passages()):

        own          the quoted words are in the passage the citation names (its chunk_id)
        elsewhere    not there, but in another passage of the pool: real words under the wrong [Source N]
        absent       in no passage of the pool: words the model wrote, not words it read
        substituted  the model gave no quote, or cited the source only as an [N] in its prose, so resolve()
                     (shared/documind_schemas.py, which rag-api's generator calls) put the chunk's first 500 characters
                     in its place: nothing was quoted, nothing is supported
        unread       the passage the citation names is not in the pool read back, or no pool was read: not judged

    The match is judge_citations()'s - whitespace collapsed, case folded, a substring - against one passage instead of
    the tenant's whole corpus. The "..." that _draft() (services/rag-api/generator.py) appends when it cuts an
    over-long quote to the contract's 200 characters is not the document's, so a trailing "..." is dropped first. A
    model that quotes the whole of a chunk shorter than 200 characters reads as substituted: from outside, the two are
    the same string."""
    def flat(s):
        return re.sub(r"\s+", " ", s or "").strip().lower()

    pool = [p for p in pool or [] if isinstance(p, dict)]
    own = next((p for p in pool if p.get("chunk_id") and p.get("chunk_id") == citation.get("chunk_id")), None)
    if own is None:
        return "unread"
    quote, text = citation.get("quote") or "", own.get("text") or ""
    if flat(quote) == flat(text[:500]):
        return "substituted"
    words = flat(quote)
    if words.endswith("..."):
        words = words[:-3].rstrip()
    if not words:
        return "absent"
    if words in flat(text):
        return "own"
    if any(words in flat(p.get("text")) for p in pool if p is not own):
        return "elsewhere"
    return "absent"


def anchors_found(row: dict, pool: list[dict] | None) -> dict[str, bool] | None:
    """{anchor: in the pool?} for each of the row's must_retrieve anchors: check_anchors()'s matching rule on a real
    retrieval, as haystack() describes it - chunk_id, source_uri and text joined and lower-cased, so a document slug
    (hr_policy_2026) is found in the source and a clause id (EXP-12) in the text. None when no pool was read."""
    if pool is None:
        return None
    hay = "\n".join(f"{p.get('chunk_id') or ''}\n{p.get('source_uri') or ''}\n{p.get('text') or ''}"
                    for p in pool if isinstance(p, dict)).lower()
    return {a: a.lower() in hay for a in row.get("must_retrieve", [])}


def passage_checks(api_url: str, golden: list[dict], records: list[dict], email: str, token: str | None) -> dict:
    """DOCUMIND_EVAL_PASSAGES=1, once live() has asked every row: each answerable row that came back well-formed -
    answered or refused, so recall is not measured only where the model answered - has its pool read again
    (passages()), each of its citations checked against that pool (quote_check(), as `check` on the record's cites)
    and each must_retrieve anchor looked for in it (anchors_found(), the record's `anchors`; `pool` is the pool's size,
    None when it could not be read). quote_passage_rate counts the answered rows' citations - the rows
    quote_support_rate reads - whose passage was read; must_retrieve_recall counts every read row's anchors. One
    embedding and one rerank a row and no model call: the route bills no tokens."""
    by_id = {r["id"]: r for r in golden}
    quotes = dict.fromkeys(QUOTE_VERDICTS, 0)
    rows = unread = found = asked = 0
    for rec in records:
        row = by_id.get(rec["id"])
        if row is None or not row["answerable"] or rec["outcome"] != "ok":
            continue
        pool = passages(api_url, row["question"], row["tenant"], email, token)
        rows += 1
        unread += pool is None
        rec["pool"] = None if pool is None else len(pool)
        for c in rec.get("cites", []):
            c["check"] = quote_check(c, pool)
            if rec.get("answerable"):
                quotes[c["check"]] += 1
        rec["anchors"] = anchors_found(row, pool)
        if rec["anchors"] is not None:
            found += sum(rec["anchors"].values())
            asked += len(rec["anchors"])
    read = sum(quotes.values()) - quotes["unread"]
    return {"rows": rows, "unread_rows": unread, "quotes": quotes,
            "quote_passage_rate": quotes["own"] / read if read else None,
            "anchors_found": found, "anchors": asked, "must_retrieve_recall": found / asked if asked else None}


def passage_info(pq: dict) -> list[str]:
    """passage_checks()'s two [info] lines, printed under quote_support_rate: what was read, never a threshold."""
    def rate(v):
        return "   n/a" if v is None else f"{v:6.1%}"

    q = pq["quotes"]
    lost = f"; {pq['unread_rows']} pool(s) could not be read" if pq["unread_rows"] else ""
    return [f"  [info] {'quote_passage_rate':21} {rate(pq['quote_passage_rate'])}  ({q['own']} of {sum(q.values()) - q['unread']} "
            f"answered rows' quotes in the passage they cite; elsewhere {q['elsewhere']}, absent {q['absent']}, "
            f"substituted {q['substituted']}, unread {q['unread']}; not a threshold)",
            f"  [info] {'must_retrieve_recall':21} {rate(pq['must_retrieve_recall'])}  ({pq['anchors_found']} of {pq['anchors']} "
            f"anchors in the pool /v1/passages returned, over {pq['rows'] - pq['unread_rows']} answerable rows{lost}; "
            f"not a threshold)"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--api-url", help="run the LIVE half against this deployment")
    ap.add_argument("--source", help="scope the live half to the rows citing this document (a name or slug); "
                                     "offline, list them")
    ap.add_argument("--report", help="live: write every row's verdict, latency, stages and cache_hit to this JSON file")
    args = ap.parse_args()
    if args.api_url:
        print("== eval gate: LIVE ==")
        return live(args.api_url, args.source, args.report)
    print("== eval gate: OFFLINE (no credentials, no cost) ==")
    rc = offline()
    if args.source:
        corpus = load_corpus()
        rows = [r for r in load_golden() if in_scope(r, args.source, corpus)]
        print(f"\n  rows citing {args.source}: {len(rows)} - the scoped live gate judges these")
        for r in rows:
            print(f"    {r['id']:6} {r['shape']:9} {r['question'][:72]}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
