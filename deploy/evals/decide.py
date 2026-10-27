#!/usr/bin/env python3
"""Answer or refuse: the decision eval (workshop lesson 2.6). Three arms decide every golden row from the same pool.

    python deploy/evals/decide.py --local                     # Rs 0: the rule arm on the kit's corpus, no lane
    python deploy/evals/decide.py --project documind-ai-YOUR-ID --save run.json      # LIVE: the pool from your lane
    python deploy/evals/decide.py --from run.json             # a saved run again: no lane, Rs 0
    make decide PROJECT=documind-ai-YOUR-ID JEV_MODE=recorded DECIDE_ARGS="--limit 5"

THE QUESTION. Retrieval has handed over a pool of passages; before an answer is written, should the system answer
from it or refuse? The truth is golden.jsonl's own `answerable`: 47 rows the corpus answers and 18 it does not (the 8
refusal rows, and 10 isolation rows asked of a tenant that holds no such document). This scores the decision only:
whether an answer is right stays run_eval.py's job.

THE ARMS, on one pool per row:

    rule        the kit's code. An empty pool is refused (rag-api's empty_pool_answer), and so is a pool that carries
                less than --floor (default EVIDENCE_FLOOR, 0.5) of the question's information: shared/documind_tools.py's
                evidence rule, the question's content words weighted by their idf over the tenant's corpus, in "set"
                mode (the pool's passages together). Its score is that share, from 0 to 1: a number, not a probability.
                Rs 0, no model
    generator   the deployed /v1/query, asked through run_eval.ask() as the live eval gate asks it (top_k 6, its
                contract), for the generator's own answerable and confidence; or recorded, from a run saved with --save
    jev         TypeSafe's Jev through shared/system_one.decide(), as JEV_MODE says: off (the default, "Jev not
                available"), recorded (evals/system_one/recorded.jsonl, which does not exist yet) or live (only the
                tenants whose data_region is any, masked; until PR 2.6-C the adapter answers error)

THE POOL. Live: shared/documind_tools.retrieve(passages=True), rag-api's /v1/passages - the same door, roster, filters,
guard, backend and rerank as /v1/query, and no model call - as documind-ui-sa. --from: a run saved with --save.
--local: the kit's own corpus on the Rs 0 lane, the way tools/check_local_lane.py runs it - documind_tools.retrieve()
on the local profile over the chunks shared/local_corpus.py would seed - where the lane's own gate is the evidence rule
at --floor, so an empty pool is that rule's refusal. An empty pool is refused by code for every arm that runs: neither
the generator nor Jev is asked.

THE SCORE, per arm: the confusion matrix against the truth; answer rate (of the answerable rows, the share answered),
refusal recall (of the unanswerable rows, the share refused) and accuracy, each with its Wilson 95% interval
(route_eval.wilson); the false answers by id, isolation rows flagged; a table per shape; Cohen's kappa against the
generator, and the rows where the arms disagree; the Brier score and reliability bins of an arm with a score, and the
generator's accuracy by its confidence; latency p50 and p95; rupees per decision. An error or a skipped row is not a
refusal: each is counted on its own line and left out of every rate, whose denominator is printed.

Exit code 0 is a measurement, not a verdict. It is 1 when an arm that was asked to run errored on every row it was
given, and 2 when the run cannot start (a flag, no lane, an unknown JEV_MODE).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import types
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = HERE.parent
for _p in (str(KIT), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from route_eval import TOKEN_MAX_AGE_S, mint, rate, wilson  # noqa: E402 - one Wilson interval, the route eval's
from run_eval import ask, load_golden, pct, validate_body  # noqa: E402 - one /v1/query client, the eval gate's
from agreement import cohen_kappa  # noqa: E402 - one Cohen's kappa, lesson 4.5's (13 October 2026)

from shared import prices, system_one  # noqa: E402
from shared.prices import USD_INR  # noqa: E402

ARMS = ("rule", "generator", "jev")
SHAPES = ("lookup", "join", "refusal", "isolation", "version")
LEVELS = ("high", "medium", "low")
TOKEN = re.compile(r"[a-z0-9]+")       # shared/documind_tools.py's tokeniser (_lexical_rank, _snippet)
UI_SA = "documind-ui-sa@{project}.iam.gserviceaccount.com"   # make eval-live's identity, on the three golden rosters
# What --save keeps of a passage: enough to decide on it again. Not source_uri, which names the project's bucket.
SAVED_KEYS = ("n", "chunk_id", "page", "doc_type", "kind", "section", "text")


def _tools():
    """shared/documind_tools.py, imported when a pool or the evidence rule is needed (it imports requests)."""
    from shared import documind_tools
    return documind_tools


def top_k_of(top_k: int) -> int:
    return max(1, min(int(top_k), 20))          # documind_tools.retrieve's and rag-api's bounds


# --------------------------------------------------------------------- the rule arm
def evidence_share(passages: list[dict], idf: dict[str, float], match) -> float:
    """The share of the question's information the pool carries: the idf of the question's words over the tenant's
    corpus (documind_tools._lexical_rank), counting a word when any passage holds a token it matches
    (documind_tools._match) - the evidence rule of _retrieve_local in "set" mode. 0.0 for a question with no word
    left to weigh."""
    total = sum(idf.values())
    if not total:
        return 0.0
    toks = {t for p in passages for t in TOKEN.findall(str((p or {}).get("text") or "").lower())}
    return sum(v for w, v in idf.items() if any(match(w, t) for t in toks)) / total


def rule_arm(passages: list[dict], share: float | None, floor: float, gated: bool = False) -> dict:
    """The kit's rule on one pool: an empty pool is refused by code, else the evidence share against the floor. A
    pool the local lane served is already gated at this floor (gated=True): it is answered as the lane answered it."""
    t0 = time.perf_counter()
    if not passages:
        return system_one.result("refuse", score=share, source="code", model="rule", ms=0, cost_usd=0.0,
                                 reason="empty pool: refused by code" + (f" (evidence {share:.2f})" if share is not None else ""))
    share = share or 0.0
    verdict = "answer" if gated or share >= floor else "refuse"
    why = (f"the local lane's gate passed it at {floor:.2f} (evidence {share:.2f})" if gated else
           f"evidence {share:.2f} {'>=' if verdict == 'answer' else '<'} floor {floor:.2f}")
    return system_one.result(verdict, score=share, source="rule", model="rule", cost_usd=0.0,
                             ms=round((time.perf_counter() - t0) * 1000, 3), reason=why)


class CorpusStore:
    """Chroma's get() over the chunks shared/local_corpus.py would seed, metadata as seed() writes it: the stand-in
    tools/check_local_lane.py uses, so the Rs 0 lane runs with no Chroma directory."""

    def __init__(self, tenants):
        from shared import local_corpus
        self.rows = [c for t in tenants for c in local_corpus.chunks_for(t)]
        self._collection = types.SimpleNamespace(count=lambda: len(self.rows))

    def get(self, where=None, include=None):
        conds = [where] if "$and" not in (where or {}) else where["$and"]
        keep = [c for c in self.rows if all(c.get(k) == v for cond in conds for k, v in (cond or {}).items())]
        return {"ids": [c["chunk_id"] for c in keep], "documents": [c["text"] for c in keep],
                "metadatas": [{"tenant_id": c["tenant_id"], "doc_type": c["doc_type"], "page": c["page_start"],
                               "source_uri": c["source_uri"], "chunk_id": c["chunk_id"],
                               **({"section": c["section"]} if c.get("section") else {})} for c in keep]}


class LocalLane:
    """The Rs 0 lane over the kit's corpus: documind_tools.retrieve(passages=True) on the local profile, the store
    stood in for, the lane's gate at the floor. The evidence share is read from the same _lexical_rank call the lane
    made, so the rule arm's score is the lane's own number."""
    name = "local"

    def __init__(self, tenants, floor: float):
        self.store, self.floor = CorpusStore(tenants), floor

    def pool(self, question: str, tenant: str, top_k: int) -> tuple[dict, float]:
        import shared.profile as profile
        dt = _tools()
        seen: dict = {}
        real = dt._lexical_rank

        def capture(q, rows):
            seen["ranked"], seen["idf"] = got = real(q, rows)
            return got

        saved = dt.PROFILE, profile.build_store, dt._lexical_rank, dt.EVIDENCE_FLOOR
        dt.PROFILE, profile.build_store, dt._lexical_rank, dt.EVIDENCE_FLOOR = (
            "local", lambda embeddings=None: self.store, capture, self.floor)
        try:
            got = dt.retrieve(question, tenant_id=tenant, top_k=top_k, passages=True)
        finally:
            dt.PROFILE, profile.build_store, dt._lexical_rank, dt.EVIDENCE_FLOOR = saved
        ranked = (seen.get("ranked") or [])[:top_k_of(top_k)]
        return got, evidence_share([{"text": r[2]} for r in ranked], seen.get("idf") or {}, dt._match)


class CorpusIdf:
    """The idf of a question's words over the tenant's corpus, for a pool that came from a lane or a saved run: the
    kit's own chunks (what make ingest-corpus uploads), weighed by documind_tools._lexical_rank."""

    def __init__(self):
        self.rows: dict[str, list] = {}

    def __call__(self, question: str, tenant: str) -> dict[str, float]:
        if tenant not in self.rows:
            from shared import local_corpus
            self.rows[tenant] = [(c["text"], {}) for c in local_corpus.chunks_for(tenant)]
        return _tools()._lexical_rank(question, self.rows[tenant])[1]


# --------------------------------------------------------------------- the lane
class Lane:
    """The deployed API: /v1/passages through documind_tools.retrieve(passages=True), minted as documind-ui-sa
    (DOCUMIND_IMPERSONATE_SA), and /v1/query through run_eval.ask() with an ID token (DOCUMIND_ID_TOKEN, else minted
    as the same account with gcloud, as make eval-live mints it)."""
    name = "lane"

    def __init__(self, api_url: str, audience: str, account: str | None, minter=mint):
        self.api_url, self.audience, self.account, self.minter = api_url.rstrip("/"), audience, account, minter
        self._token: tuple[float, str] | None = None

    @classmethod
    def from_args(cls, a) -> "Lane":
        audience = ""
        if a.project:
            try:
                number = subprocess.run(["gcloud", "projects", "describe", a.project, "--format=value(projectNumber)"],
                                        capture_output=True, text=True).stdout.strip()
            except OSError:
                number = ""
            if not number.isdigit():
                raise SystemExit(f"gcloud did not return {a.project}'s project number: pass --api-url, or sign in")
            audience = f"https://documind-api-{number}.{a.region}.run.app"
        url = a.api_url or audience
        if not url.startswith("https://"):
            raise SystemExit("a live pool needs the API: --project (make decide passes it) or --api-url https://...")
        return cls(url, audience or url, UI_SA.format(project=a.project) if a.project else None)

    def token(self) -> str | None:
        if os.environ.get("DOCUMIND_ID_TOKEN"):
            return os.environ["DOCUMIND_ID_TOKEN"]
        if self.account and (not self._token or time.monotonic() - self._token[0] > TOKEN_MAX_AGE_S):
            t = self.minter(self.account, self.audience)
            if not t:
                raise SystemExit(f"could not mint an ID token as {self.account}: make operators lets you")
            self._token = (time.monotonic(), t)
        return self._token[1] if self._token else None

    def pool(self, question: str, tenant: str, top_k: int) -> dict:
        """The passages, or {"error"} when the call failed: an error row, never a refusal. Minting the ID token is
        tried once first, because without google-auth or the right to mint every row would fail: the run stops."""
        dt = _tools()
        dt.PROFILE, dt.RAG_API_URL = "gcp", self.api_url
        if self.account:
            os.environ.setdefault("DOCUMIND_IMPERSONATE_SA", self.account)
        if not getattr(self, "_minted", False):
            try:
                dt._id_token(self.api_url)
            except Exception as e:  # noqa: BLE001 - google-auth, ADC, or the right to mint as the account
                raise SystemExit(f"no ID token for /v1/passages as {os.environ.get('DOCUMIND_IMPERSONATE_SA') or 'ADC'}"
                                 f": {type(e).__name__}: {str(e)[:200]} (pip install google-auth; make operators "
                                 f"lets you mint as documind-ui-sa)") from e
            self._minted = True
        try:
            return dt.retrieve(question, tenant_id=tenant, top_k=top_k, passages=True)
        except Exception as e:  # noqa: BLE001 - a reply that is not JSON, say: this row has no pool
            return {"error": f"/v1/passages: {type(e).__name__}: {str(e)[:200]}"}

    def ask(self, question: str, tenant: str) -> tuple[int, dict, int]:
        return ask(self.api_url, question, tenant, os.environ.get("DOCUMIND_USER_EMAIL", "eval@documind.in"),
                   self.token())


def policy_reader(base=None):
    """A tenant's data_region, read once a run (JEV_MODE=live only) and kept for the header: shared/tenancy.policy_for
    (Firestore, failing closed to `in`) unless another reader is given. A reader that raises is `in`."""
    seen: dict[str, str] = {}

    def read(tenant: str) -> str:
        if tenant not in seen:
            try:
                if base is None:
                    from shared import tenancy
                    seen[tenant] = tenancy.policy_for(tenant)
                else:
                    seen[tenant] = base(tenant)
            except Exception:  # noqa: BLE001 - fail closed, as policy_for does
                seen[tenant] = "in"
        return seen[tenant]

    read.seen = seen
    return read


# --------------------------------------------------------------------- the generator arm
def list_usd(model: str, tokens_in: int, tokens_out: int) -> float:
    """A lane answer's tokens at shared/prices.py's list price, whatever DOCUMIND_PROFILE this shell carries: the
    answer came from the deployed lane, which Lane calls on the gcp profile the same way."""
    saved, prices.PROFILE = prices.PROFILE, "gcp"
    try:
        return round(prices.usd(model, tokens_in, tokens_out), 6)
    finally:
        prices.PROFILE = saved


def generator_live(question: str, tenant: str, lane) -> dict:
    """The generator's own decision: /v1/query's answerable, through run_eval.ask(). A non-200 or a body that is
    not the answer contract is an error, never a refusal."""
    status, body, ms = lane.ask(question, tenant)
    if status != 200:
        return system_one.result("error", source="live", ms=ms, reason="the generator's answer did not arrive",
                                 error=f"HTTP {status}" + (f" {body.get('error')}" if isinstance(body, dict) and body.get("error") else ""))
    problem = validate_body(body)
    if problem:
        return system_one.result("error", source="live", ms=ms, error=f"malformed answer: {problem}",
                                 reason="the generator's answer did not arrive")
    empty = body.get("backend") == "none" and not body["citations"] and (body.get("stages") or {}).get("pool") == 0
    tin, tout = body.get("tokens_in"), body.get("tokens_out")
    counted = isinstance(tin, int) and isinstance(tout, int)
    cost = body.get("cost_usd")
    if cost is None and counted and body.get("model"):   # /v1/query fills cost_usd only when the gateway priced the
        cost = list_usd(body["model"], tin, tout)        # answer; a Gemini answer's tokens, as cost.py prices its row
    res = system_one.result("answer" if body["answerable"] else "refuse", source="code" if empty else "live",
                            model=body.get("model"), ms=ms, cost_usd=cost,
                            tokens={"input": tin, "output": tout} if counted else None,
                            reason=f"answerable {str(body['answerable']).lower()}, confidence {body['confidence']}"
                                   + (f", cache {body['cache_hit']}" if body.get("cache_hit") not in (None, "none") else ""))
    res["confidence"] = body["confidence"]
    return res


def generator_recorded(saved: dict | None) -> dict:
    """The generator's decision as a saved run holds it."""
    res = dict(saved or {})
    if res.get("verdict") not in ("answer", "refuse", "error"):
        return system_one.result("skipped", source="recorded", reason="the saved run holds no generator decision for this row")
    if res.get("source") != "code":
        res["source"] = "recorded"
    return res


# --------------------------------------------------------------------- one row
def decide_row(row: dict, pool: dict, share: float | None, a, lane, policy_for, saved_arms: dict | None) -> dict:
    """Every arm's decision on one row's pool. A pool that failed or that rag-api's door answered is no decision for
    any arm: an error, or a skip, never a refusal."""
    jev_runs = system_one.mode() in ("recorded", "live")
    if pool.get("skip") or pool.get("error"):
        why = pool.get("skip") or pool.get("error")
        kind = "skipped" if pool.get("skip") else "error"
        fail = (lambda: system_one.result(kind, source="pool", reason=why, error=None if kind == "skipped" else why))
        return {"rule": fail(), "generator": fail() if a.generator else _not_run(a),
                "jev": fail() if jev_runs else system_one.decide(row["question"], [], row["id"], row["tenant"])}
    passages = pool.get("passages") or []
    arms = {"rule": rule_arm(passages, share, a.floor, gated=bool(getattr(a, "gated", False)))}
    if not a.generator:
        arms["generator"] = _not_run(a)
    elif not passages:
        arms["generator"] = system_one.result("refuse", source="code", ms=0, cost_usd=0.0,
                                              reason="empty pool: refused by code; the generator not asked")
    elif a.generator == "live":
        arms["generator"] = generator_live(row["question"], row["tenant"], lane)
    else:
        arms["generator"] = generator_recorded((saved_arms or {}).get("generator"))
    arms["jev"] = system_one.decide(row["question"], passages, row["id"], row["tenant"], policy_for=policy_for)
    return arms


def _not_run(a) -> dict:
    why = ("--local has no lane: the generator needs one (replay a saved run: --from FILE)" if a.local
           else "the saved run is a --local run: no lane, so no generator decisions" if getattr(a, "saved_local", False)
           else "not asked for")
    return system_one.result("skipped", source="none", reason=why)


# --------------------------------------------------------------------- the score
def decided(res: dict | None) -> bool:
    return bool(res) and res.get("verdict") in ("answer", "refuse")


def summarise(records: list[dict], arm: str) -> dict:
    """The arm's confusion matrix against golden answerable, its rates, its false answers, its errors and skips."""
    s = {"arm": arm, "rows": 0, "tp": 0, "fn": 0, "fp": 0, "tn": 0, "error": 0, "skipped": 0, "code": 0,
         "false_answers": [], "why_error": "", "why_skipped": ""}
    for r in records:
        res = r["arms"].get(arm) or {}
        s["rows"] += 1
        v = res.get("verdict")
        if v not in ("answer", "refuse"):
            kind = "error" if v == "error" else "skipped"
            s[kind] += 1
            s[f"why_{kind}"] = s[f"why_{kind}"] or res.get("error") or res.get("reason") or ""
            continue
        s["code"] += res.get("source") == "code"
        if r["answerable"]:
            s["tp" if v == "answer" else "fn"] += 1
        elif v == "answer":
            s["fp"] += 1
            s["false_answers"].append(r["id"] + ("*" if r["shape"] == "isolation" else ""))
        else:
            s["tn"] += 1
    s["decided"] = s["tp"] + s["fn"] + s["fp"] + s["tn"]
    s["answer_rate"] = (s["tp"], s["tp"] + s["fn"])
    s["refusal_recall"] = (s["tn"], s["tn"] + s["fp"])
    s["accuracy"] = (s["tp"] + s["tn"], s["decided"])
    s["wilson"] = {k: wilson(*s[k]) for k in ("answer_rate", "refusal_recall", "accuracy")}   # None for 0 of 0
    s["available"] = s["decided"] > s["code"]           # at least one decision the arm made itself
    s["failed"] = s["error"] > 0 and not s["available"]
    s["why"] = s["why_error"] or s["why_skipped"]       # what to say of an arm that is not available
    return s


def kappa(pairs: list[tuple[str, str]]) -> float | None:
    """Cohen's kappa of two arms' verdicts (answer / refuse) on the rows both decided: evals/agreement.py's
    cohen_kappa(), the kit's one kappa (lesson 4.5), counted in whole rows. None with no rows, or when the agreement
    expected by chance is 1 (both arms gave one and the same verdict throughout): undefined there, not perfect."""
    return cohen_kappa([x for x, _ in pairs], [y for _, y in pairs])


def pairs_of(records: list[dict], a: str, b: str) -> list[tuple[str, str]]:
    return [(r["arms"][a]["verdict"], r["arms"][b]["verdict"]) for r in records
            if decided(r["arms"].get(a)) and decided(r["arms"].get(b))]


def calibration(records: list[dict], arm: str, bins: int = 5) -> dict | None:
    """Brier score and reliability bins over the rows the arm decided with a score: (score - truth)^2, truth 1 for
    an answerable row. None when the arm gave no score."""
    pts = [(float(r["arms"][arm]["score"]), 1 if r["answerable"] else 0) for r in records
           if decided(r["arms"].get(arm)) and r["arms"][arm].get("score") is not None]
    if not pts:
        return None
    table = []
    for i in range(bins):
        lo, hi = i / bins, (i + 1) / bins
        inside = [(p, y) for p, y in pts if lo <= p < hi or (i == bins - 1 and p == hi)]
        table.append({"lo": lo, "hi": hi, "n": len(inside), "answerable": sum(y for _, y in inside),
                      "mean": sum(p for p, _ in inside) / len(inside) if inside else None})
    return {"n": len(pts), "brier": sum((p - y) ** 2 for p, y in pts) / len(pts), "bins": table}


def by_confidence(records: list[dict]) -> dict[str, tuple[int, int]]:
    """The generator's right decisions per confidence level: {level: (right, decided)}."""
    out = {}
    for level in LEVELS:
        rs = [r for r in records if decided(r["arms"].get("generator")) and r["arms"]["generator"].get("confidence") == level]
        out[level] = (sum(right(r, "generator") for r in rs), len(rs))
    return out


def right(r: dict, arm: str) -> bool:
    return (r["arms"][arm]["verdict"] == "answer") == bool(r["answerable"])


def latency(records: list[dict], arm: str) -> list[float]:
    """The ms of the decisions the arm made itself (an empty pool's code refusal took no call)."""
    return [float(r["arms"][arm]["ms"]) for r in records if decided(r["arms"].get(arm))
            and r["arms"][arm].get("source") != "code" and r["arms"][arm].get("ms") is not None]


def rupees(records: list[dict], arm: str) -> tuple[float | None, int, int]:
    """(rupees per decision over the priced ones, priced, unpriced), for the decisions the arm made itself."""
    costs = [r["arms"][arm].get("cost_usd") for r in records if decided(r["arms"].get(arm))
             and r["arms"][arm].get("source") != "code"]
    priced = [float(c) for c in costs if isinstance(c, (int, float))]
    return (sum(priced) / len(priced) * USD_INR if priced else None), len(priced), len(costs) - len(priced)


# --------------------------------------------------------------------- the report
def _ms(v: float) -> str:
    return "<0.01" if v < 0.01 else f"{v:.2f}" if v < 10 else f"{v:.0f}"


def report(records: list[dict], header: list[str], out=None) -> dict[str, dict]:
    out = out or sys.stdout
    say = lambda s="": print(s.rstrip(), file=out)  # noqa: E731
    n, ans = len(records), sum(1 for r in records if r["answerable"])
    say("== answer or refuse: the decision eval (lesson 2.6) ==")
    say(f"  rows       {n} golden rows: {ans} answerable, {n - ans} not")
    for line in header:
        say(f"  {line}")
    summ = {arm: summarise(records, arm) for arm in ARMS}
    say()
    for arm in ARMS:
        s = summ[arm]
        if not s["available"]:
            say(f"  {arm:<10} not available: {s['why'] or 'no decision'}"
                + (f" ({s['code']} empty pools refused by code)" if s["code"] else ""))
            continue
        say(f"  {arm:<10} {s['decided']} decided ({s['code']} by code: an empty pool), {s['error']} errors, "
            f"{s['skipped']} skipped")
        say(f"  {'':<10} answer rate     {rate(*s['answer_rate']):<32}  of the answerable rows, answered")
        say(f"  {'':<10} refusal recall  {rate(*s['refusal_recall']):<32}  of the unanswerable rows, refused")
        say(f"  {'':<10} accuracy        {rate(*s['accuracy']):<32}  of the rows decided")
        say(f"  {'':<10} confusion       answerable: {s['tp']} answered, {s['fn']} refused | "
            f"unanswerable: {s['fp']} answered, {s['tn']} refused")
        fa = s["false_answers"]
        say(f"  {'':<10} false answers   {len(fa)}" + (", * an isolation row" if any("*" in x for x in fa) else "")
            + (":" if fa else ""))
        for i in range(0, len(fa), 10):
            say(f"  {'':<10} {'':<15} {' '.join(fa[i:i + 10])}")
        if s["error"]:
            say(f"  {'':<10} errors are not refusals: {s['error']} left out ({s['why_error'][:90]})")
        if s["skipped"]:
            say(f"  {'':<10} skipped, not scored: {s['skipped']} ({s['why_skipped'][:90]})")
    live = [arm for arm in ARMS if summ[arm]["available"]]
    say()
    say("  per shape    rows  " + "".join(f"{arm:<12}" for arm in ARMS) + "(right decisions / decided)")
    for shape in SHAPES:
        rs = [r for r in records if r["shape"] == shape]
        if rs:
            cells = []
            for arm in ARMS:
                d = [r for r in rs if decided(r["arms"].get(arm))]
                cells.append(f"{sum(right(r, arm) for r in d)}/{len(d)}" if arm in live and d else "-")
            say(f"  {shape:<12}{len(rs):5}  " + "".join(f"{c:<12}" for c in cells))
    say()
    if "generator" in live:
        say("  kappa against the generator (Cohen's, on the rows both decided)")
        for arm in ("rule", "jev"):
            if arm in live:
                p = pairs_of(records, arm, "generator")
                k = kappa(p)
                say(f"    {arm:<10} {'undefined (one verdict throughout)' if k is None else f'{k:.2f}'} over {len(p)} rows")
    else:
        say("  kappa against the generator: - (the generator did not run)")
    if len(live) >= 2:
        diff = [r for r in records if len({r["arms"][arm]["verdict"] for arm in live if decided(r["arms"].get(arm))}) > 1]
        say(f"  rows where the arms disagree: {len(diff)}")
        for r in diff:
            say(f"    {r['id']:<7} {r['shape']:<10} truth {'answer' if r['answerable'] else 'refuse':<7}"
                + "  ".join(f"{arm} {r['arms'][arm]['verdict'] if decided(r['arms'].get(arm)) else '-'}" for arm in live))
    else:
        say("  rows where the arms disagree: - (one arm decided)")
    say()
    say("  calibration (Brier: 0 is perfect; always 0.5 scores 0.25)")
    for arm in ARMS:
        if arm == "generator":
            if "generator" in live:
                conf = by_confidence(records)
                say("    generator  right decisions by its confidence: "
                    + "; ".join(f"{lv} {rate(*conf[lv])}" for lv in LEVELS if conf[lv][1]))
            continue
        cal = calibration(records, arm) if arm in live else None
        if not cal:
            say(f"    {arm:<10} no scores")
            continue
        what = " (the evidence share, not a probability)" if arm == "rule" else " (its calibrated probability)"
        say(f"    {arm}{what}: Brier {cal['brier']:.3f} over {cal['n']} rows")
        say("      score      rows  mean score  answerable")
        for b in cal["bins"]:
            mean = "-" if b["mean"] is None else f"{b['mean']:.2f}"
            say(f"      {b['lo']:.1f}-{b['hi']:.1f}  {b['n']:6}  {mean:>10}  {b['answerable']:>4}/{b['n']}")
    say()
    say("  latency per decision, ms      p50       p95   decisions (an empty pool's refusal took none)")
    for arm, what in (("rule", "rule (in process)"), ("generator", "generator (/v1/query)"), ("jev", "jev")):
        ms = latency(records, arm) if arm in live else []
        if ms:
            say(f"    {what:<26}{_ms(pct(ms, 0.5)):>7}  {_ms(pct(ms, 0.95)):>8}  {len(ms):10}")
        else:
            say(f"    {what:<26}{'-':>7}  {'-':>8}  {0:10}")
    say(f"  rupees per decision (USD x {USD_INR})")
    for arm in ARMS:
        per, priced, unpriced = rupees(records, arm) if arm in live else (None, 0, 0)
        if per is None:
            say(f"    {arm:<10} -" + (f" ({unpriced} decisions unpriced)" if unpriced else ""))
        else:
            say(f"    {arm:<10} Rs {'0' if per == 0 else f'{per:.4f}'} a decision, over {priced}"
                + (f" ({unpriced} more unpriced)" if unpriced else "") + (" (code, no model)" if arm == "rule" else ""))
    return summ


# --------------------------------------------------------------------- the run
def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--project", default=os.environ.get("PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT") or None,
                    help="your lane (make decide passes it)")
    ap.add_argument("--region", default=os.environ.get("REGION") or "us-central1", help="where the API runs")
    ap.add_argument("--api-url", help="the API, when it is not documind-api on --project")
    ap.add_argument("--limit", type=int, default=0, help="only the first N rows (after --tenant): a wiring check")
    ap.add_argument("--tenant", choices=("acme", "zeta", "globex"), help="only this tenant's rows")
    ap.add_argument("--top-k", type=int, default=5, help="the pool: how many passages (1-20; default 5)")
    ap.add_argument("--generator", choices=("live", "recorded"),
                    help="live: /v1/query on the lane; recorded: the saved run's (the default with --from)")
    ap.add_argument("--floor", type=float, help="the rule arm's evidence floor (default documind_tools.EVIDENCE_FLOOR)")
    ap.add_argument("--save", help="write the run - every row's pool and every arm's decision - to this JSON file")
    ap.add_argument("--from", dest="from_file", help="read the pools (and the generator's decisions) from a saved run")
    ap.add_argument("--local", action="store_true", help="Rs 0: the pool from the kit's corpus on the local lane")
    return ap.parse_args(argv)


def load_saved(path: str) -> tuple[dict[str, dict], dict]:
    """({row id: the saved row}, the run's own fields: pool, top_k, floor, jev_mode, saved)."""
    with open(path, encoding="utf-8") as f:
        run = json.load(f)
    if not isinstance(run, dict) or run.get("kind") != "decide-run":
        raise SystemExit(f"{path} is not a run saved by decide.py --save")
    return {r["id"]: r for r in run.get("rows") or []}, {k: v for k, v in run.items() if k != "rows"}


def run(a, out=None, lane=None, policy_for=None, idf=None) -> int:
    """The eval: the rows, a pool for each, every arm's decision, the report, the saved run. lane, policy_for and idf
    stand in for the deployed API, the data-region reader and the corpus statistics (the tests pass their own)."""
    out = out or sys.stdout
    jev = system_one.mode()
    if jev not in system_one.MODES:
        print(f"JEV_MODE={jev!r} is not one of {'|'.join(system_one.MODES)}", file=sys.stderr)
        return 2
    if a.local and a.from_file:
        print("--local and --from are two pools: choose one", file=sys.stderr)
        return 2
    if a.local and a.generator:
        print("--local has no lane, so no generator: replay a saved run with --from FILE", file=sys.stderr)
        return 2
    if a.generator == "recorded" and not a.from_file:
        print("--generator recorded reads a saved run: --from FILE", file=sys.stderr)
        return 2
    saved, meta = load_saved(a.from_file) if a.from_file else ({}, {})
    a.saved_local = meta.get("pool") == "local"           # a --local run's pool: no lane, so no generator in it
    if a.saved_local and a.generator == "live":
        print(f"{a.from_file} holds the local lane's pools: /v1/query would answer from your lane's", file=sys.stderr)
        return 2
    if a.from_file and not a.generator and not a.saved_local:
        a.generator = "recorded"
    elif not a.local and not a.from_file and not a.generator:
        a.generator = "live"
    if a.floor is None:
        a.floor = _tools().EVIDENCE_FLOOR
    # A local pool is already gated by the evidence rule at its floor: at that floor the rule answers what it holds.
    a.gated = a.local or (a.saved_local and meta.get("floor") == a.floor)
    golden = [r for r in load_golden() if not a.tenant or r["tenant"] == a.tenant]
    if a.from_file:                       # a saved run is its own population: the rows it holds, the rest counted
        a.not_saved = sum(1 for r in golden if r["id"] not in saved)
        golden = [r for r in golden if r["id"] in saved]
    golden = golden[:a.limit] if a.limit > 0 else golden
    needs_lane = not a.local and (not a.from_file or a.generator == "live")
    if needs_lane and lane is None:
        try:
            lane = Lane.from_args(a)
        except SystemExit as e:
            print(str(e), file=sys.stderr)
            return 2
    if jev == "live":
        if a.project and policy_for is None:
            os.environ.setdefault("GOOGLE_CLOUD_PROJECT", a.project)     # Firestore's project, for the data-region reads
        policy_for = policy_reader(policy_for)
    local = LocalLane(sorted({r["tenant"] for r in golden}), a.floor) if a.local else None
    idf = idf or CorpusIdf()
    records = []
    for i, row in enumerate(golden, 1):
        share = None
        if local:
            pool, share = local.pool(row["question"], row["tenant"], a.top_k)
        elif a.from_file:
            got = saved[row["id"]]
            if got.get("question") != row["question"]:
                pool = {"skip": "the golden row changed after the run was saved"}
            else:
                pool, share = dict(got.get("pool") or {}), (got.get("pool") or {}).get("share")
        else:
            pool = lane.pool(row["question"], row["tenant"], a.top_k)
        if not pool.get("skip") and not pool.get("error") and pool.get("answer") and not pool.get("passages"):
            pool = {"skip": "rag-api's door answered in the route's place (the Desk's gate): no pool to decide on"}
        if not pool.get("skip") and not pool.get("error") and share is None and pool.get("passages"):
            share = evidence_share(pool["passages"], idf(row["question"], row["tenant"]), _tools()._match)
        arms = decide_row(row, pool, share, a, lane, policy_for, (saved.get(row["id"]) or {}).get("arms"))
        records.append({"id": row["id"], "tenant": row["tenant"], "shape": row["shape"],
                        "answerable": bool(row["answerable"]), "question": row["question"],
                        "pool": {"passages": [{k: p.get(k) for k in SAVED_KEYS} for p in pool.get("passages") or []],
                                 "share": share, "error": pool.get("error"), "skip": pool.get("skip")},
                        "arms": arms})
        if i % 10 == 0 and i < len(golden):
            print(f"  ... {i}/{len(golden)} rows", file=sys.stderr, flush=True)
    summ = report(records, header_lines(a, jev, local, lane, policy_for, records), out)
    if a.save:
        os.makedirs(os.path.dirname(os.path.abspath(a.save)), exist_ok=True)
        with open(a.save, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"kind": "decide-run", "saved": datetime.now().astimezone().isoformat(timespec="seconds"),
                       "pool": "local" if a.local else "file" if a.from_file else "lane", "top_k": a.top_k,
                       "floor": a.floor, "jev_mode": jev, "rows": records}, f, indent=1, ensure_ascii=False)
            f.write("\n")
        print(f"\n  saved: {a.save}", file=out)
    asked = ["rule"] + (["generator"] if a.generator else []) + (["jev"] if jev in ("recorded", "live") else [])
    return 1 if any(summ[arm]["failed"] for arm in asked) else 0


def header_lines(a, jev, local, lane, policy_for, records) -> list[str]:
    k = top_k_of(a.top_k)
    if local:
        pool = (f"the Rs 0 lane, top {k}: documind_tools.retrieve(passages=True) on the local profile over the kit's\n"
                f"  {'':<10} corpus ({len(local.store.rows)} chunks), its gate the evidence rule at {a.floor:.2f}")
    elif a.from_file:
        pool = (f"saved in {a.from_file}, the rule re-applied at floor {a.floor:.2f}"
                + (f"; {a.not_saved} golden rows are not in it" if getattr(a, "not_saved", 0) else ""))
    else:
        pool = f"your lane's /v1/passages (documind_tools.retrieve(passages=True)), top {k}"
    gen = {"live": "the lane's /v1/query through run_eval.ask() (top_k 6), the generator's own answerable",
           "recorded": f"as saved in {a.from_file}"}.get(a.generator or "", _not_run(a)["reason"])
    if jev == "off":
        jv = system_one.OFF_REASON
    elif jev == "recorded":
        got = system_one._recordings()
        jv = ("JEV_MODE=recorded: " + (system_one.RECORDED_ABSENT if got is None else
              f"{sum(len(v) for v in got[0].values())} recordings in evals/system_one/recorded.jsonl"))
    else:
        seen = getattr(policy_for, "seen", {})
        regions = ", ".join(f"{t} {p}" for t, p in sorted(seen.items())) or "not read"
        jv = (f"JEV_MODE=live: data_region {regions} - only `any` is sent, masked; the adapter: "
              + ("ready" if any(r["arms"]["jev"].get("source") == "live" and decided(r["arms"]["jev"]) for r in records)
                 else system_one.NOT_CONFIGURED))
    return [f"pool       {pool}",
            f"rule       an empty pool, or evidence under {a.floor:.2f} of the question's information, is refused (Rs 0)",
            f"generator  {gen}",
            f"jev        {jv}"]


def main(argv=None) -> int:
    return run(parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
