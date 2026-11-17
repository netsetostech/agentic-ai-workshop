#!/usr/bin/env python3
"""The prompt bench (workshop lessons 3.1, 3.2 and 3.3): the kit's own generate() asked the same question again and again
on one fixed pool - at each thinking level, with or without a temperature, with a rule added to SYSTEM or one taken out -
and every answer judged by the eval gate's own rule.

    python deploy/evals/prompt_bench.py --api-url URL --rows lk-06 --runs 5 --levels LOW,HIGH            # 3.1
    python deploy/evals/prompt_bench.py --api-url URL --rows lk-06 --runs 5 --temperature 2.0             # 3.1
    python deploy/evals/prompt_bench.py --api-url URL --shape join --levels LOW,MEDIUM,HIGH               # 3.2
    python deploy/evals/prompt_bench.py --api-url URL --from-report evals/reports/live.json --failing \\
        --shape refusal --add-rule "..."                                                                  # 3.3
    make bench BENCH_ARGS="--rows lk-06 --runs 5 --levels LOW,HIGH"

LIVE, and only live: retrieval comes from your lane and every answer is a Gemini call billed to it. make bench mints the
ID token the API wants (DOCUMIND_ID_TOKEN, as documind-ui-sa, as make eval-live does) and sets GOOGLE_CLOUD_PROJECT;
without make, set both yourself. CI tests it offline, with the generator's library calls replaced
(evals/tests/test_prompt_bench.py).

RETRIEVAL, ONCE A ROW. Each row's pool is read once, before any answer is asked, from POST /v1/passages
(run_eval.passages(): ask()'s body, top_k 6, the same door, roster, retrieval and rerank as /v1/query, and no generator
call), and every arm, level and run answers from that pool - so a difference between two answers is the prompt's or the
model's, never retrieval's. A row whose pool cannot be read is not benched, nor is an empty pool: /v1/query refuses one
with no model call (main.py's empty_pool_answer). What the route does not return, the bench cannot send: a figure's
media_url, so a figure or table is answered from its caption with no image part, and a dated document's effective_from,
so no source header carries a date and generator.DATED_RULE is never added.

GENERATION, THE KIT'S OWN. services/rag-api/generator.py is imported from your shell as the service imports it (rag-api's
pins: pip install -r services/rag-api/requirements.txt once; GOOGLE_CLOUD_PROJECT names your lane), and every answer is
its generate(question, pool, model=..., backend="vertex"): the same packing, prompt, response schema, max_output_tokens,
truncation retry and resolve() the API runs. No tenant goes with it, so no tenant's explicit cache (make cache) is
attached: the bench measures the prompt, not a cached pack. A tuned endpoint is not benched: it is served on a regional
client (generator._client_for), and make candidate with make eval-live judges one.

THE RECORDER. generator._client, wrapped for the run (Recorder): generate() reaches the model only through it for a model
name, and each call goes out with thinking_config at the level being benched and, in an arm that has one, a temperature;
the schema, max_output_tokens and contents go as generator._call built them. It keeps the config as sent and the usage,
with the thought tokens apart from the visible ones (generator._usage() adds them into one tokens_out), so what a thinking
level buys is a column of its own. generator.py itself sends no temperature, which gemini-3.6-flash ignores (its
comment), and thinking_level LOW: the kit arm at LOW is the API's own request. A level or a temperature the model does not
take comes back as the API's error, on that answer's row.

SYSTEM, IN MEMORY. --add-rule TEXT appends a rule and --drop-rule N takes the kit's rule N out, the rules renumbered from 1
(edit_system()). The edited text is set on the module for its arm's answers and the kit's put back after, so generator.py
is never written: lessons quote it, and its SYSTEM must stay byte-identical to evals/make_trainset.py's copy, behind
which the tuned model was trained (12.1). The run ends by checking the file's bytes against those it started with.

ARMS. The kit arm - generator.py's SYSTEM, no temperature - runs unless --no-baseline; any rule edit or a temperature makes
a second arm, "edit", carrying all of them, so give one change at a time to read one change's effect. Each arm prints the
sha256 of its SYSTEM followed by DATED_RULE, the text every prompt starts with, hashed as a prompt version's text is
(lesson 3.6): the kit arm's is the text config.py's prompt_version names, and an edited one names no version yet. ROWS:
--rows, --shape and --from-report FILE (with --failing, only the rows that did not pass) together, in golden.jsonl's order.

SCORING. Every answer is judged by run_eval.row_verdict(), exactly as the gate judges /v1/query's: the citations the
tenant's own, current documents (GET /v1/sources, once a tenant), each must_contain figure on its own boundary, no
must_not_contain, a refusal where the corpus cannot answer. Each quote is checked by run_eval.quote_check() against the
row's own pool. Per arm and level it prints pass k/N with its Wilson interval, distinct answers and distinct citation
sets (within each row, across its runs, summed), the quote checks, thought and visible tokens per answer and rupees at
list price from shared/prices.py (rag-api's cost.py prices from BigQuery, which the bench needs no role on). --show
prints each row's pool and its distinct answers; --report writes every answer, config, usage and verdict as JSON.

IDENTIFIERS, AS THE PAGES PRINT THEM. Everything the bench prints, and its --report, carries your lane's project id and
project number as the lesson pages print them: documind-ai-YOUR-ID and NUMBER (redactor()). The id is
GOOGLE_CLOUD_PROJECT, as a whole name or the start of one (gs://documind-ai-YOUR-ID-uploads/...); the number is the one
in the API's address, and any in a Cloud Run address or a projects/NUMBER/ path. Only the printing changes: every
request still goes to the address given, and make bench's own ">> URL" line, printed before the bench starts, names it.
On by default, because the output is made to be pasted (the pages record it) and nothing on the lane differs;
BENCH_REDACT=0 prints the identifiers as they are. A whole identifier is replaced: one an error text cut short is not.

Cost: one generate() a row, arm, level and run - one call, two when an answer is cut off at max_output_tokens and asked
again - plus one /v1/passages a row. Nothing is written but --report.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
RAG_API = os.path.join(KIT, "services", "rag-api")
sys.path.insert(0, HERE)
if KIT not in sys.path:
    sys.path.append(KIT)                                # shared/: the list prices
import run_eval  # noqa: E402  - the golden rows, the pool reader and the gate's judgment of one reply
from route_eval import rate  # noqa: E402  - "k/n = p% [lo%, hi%]", the Wilson form every rate is printed in
from shared import prices  # noqa: E402  - list prices, as the chat service prices its own calls

LEVELS = ("MINIMAL", "LOW", "MEDIUM", "HIGH")       # google-genai's ThinkingLevel, less THINKING_LEVEL_UNSPECIFIED
KIT_LEVEL = "LOW"                                   # generator._call's thinking_config
SHAPES = ("lookup", "join", "refusal", "isolation", "version")
TOP_K = 6                                           # ask()'s and passages()' top_k: the pool the gate's answer drew on
ANSWER_CHARS = 600                                  # what a record keeps of an answer, as run_eval.py's --report
RULE = re.compile(r"^(\d+)\. (\S.*)$")


# --------------------------------------------------------------------- SYSTEM, edited in memory
def rules_of(system: str) -> tuple[list[str], list[str]]:
    """(the lines before the rules, each rule's text) of a SYSTEM shaped as generator.SYSTEM is: a head, then rules
    numbered 1., 2., ... to the end. Any other shape is refused: an edit is only safe on a prompt it can read back."""
    head: list[str] = []
    rules: list[str] = []
    for line in system.rstrip("\n").split("\n"):
        m = RULE.match(line)
        if m and int(m.group(1)) == len(rules) + 1:
            rules.append(m.group(2))
        elif rules:
            raise ValueError(f"SYSTEM has a line after its numbered rules: {line[:60]!r}")
        else:
            head.append(line)
    if not rules:
        raise ValueError("SYSTEM has no numbered rules")
    return head, rules


def edit_system(system: str, add=(), drop=()) -> str:
    """SYSTEM with the rules numbered in `drop` (the kit's numbers) taken out and the lines in `add` appended,
    renumbered from 1. With neither, SYSTEM itself, byte for byte."""
    head, rules = rules_of(system)
    bad = sorted({n for n in drop if not 1 <= n <= len(rules)})
    if bad:
        raise ValueError(f"--drop-rule {bad[0]}: SYSTEM's rules are 1 to {len(rules)}")
    for text in add:
        if not text.strip() or "\n" in text:
            raise ValueError("--add-rule takes one line of text")
    kept = [r for i, r in enumerate(rules, 1) if i not in set(drop)] + [t.strip() for t in add]
    return "\n".join(head + [f"{i}. {r}" for i, r in enumerate(kept, 1)]) + "\n"


def prompt_sha(system: str, dated_rule: str) -> str:
    """The sha256 of SYSTEM followed by DATED_RULE, in UTF-8: the text generate() starts every prompt with (the rule
    only when a packed chunk is dated), hashed as a prompt version's text is hashed (lesson 3.6). The kit arm's is the
    text config.py's prompt_version names; an edit arm's is a text no version names yet."""
    return hashlib.sha256((system + dated_rule).encode("utf-8")).hexdigest()


def rule_count(system: str) -> str:
    try:
        return f"{len(rules_of(system)[1])} rules"
    except ValueError:
        return "rules unread"


def arms(kit_system: str, add=(), drop=(), temperature: float | None = None, baseline: bool = True) -> list[dict]:
    """The prompts benched: the kit's (unless baseline is False) and, when anything is changed, one "edit" arm carrying
    every change - the rules edited (`changes`) and the temperature."""
    out = [{"name": "kit", "system": kit_system, "temperature": None, "changes": []}] if baseline else []
    changes = [f"rule {n} dropped" for n in sorted(set(drop))] + [f"rule added: {t.strip()}" for t in add]
    if changes or temperature is not None:
        out.append({"name": "edit", "system": edit_system(kit_system, add, drop), "temperature": temperature,
                    "changes": changes})
    return out


# --------------------------------------------------------------------- the recorder around generator._client
def _get(obj, name: str):
    return obj.get(name) if isinstance(obj, dict) else getattr(obj, name, None)


def sent(config) -> dict:
    """The knobs one request carried: its thinking level, its temperature (None when none was sent) and its
    max_output_tokens - from google-genai's GenerateContentConfig, or a dict of the same fields."""
    thinking = _get(config, "thinking_config")
    level = _get(thinking, "thinking_level") if thinking is not None else None
    return {"thinking_level": getattr(level, "value", level), "temperature": _get(config, "temperature"),
            "max_output_tokens": _get(config, "max_output_tokens")}


def usage_of(r) -> dict:
    """What one reply billed, the thought tokens apart: the prompt (tokens_in, the cached ones among them), the visible
    output (candidates_token_count) and the thinking (thoughts_token_count, billed as output too), and why it stopped."""
    u = getattr(r, "usage_metadata", None)

    def n(key: str) -> int:
        return int(getattr(u, key, None) or 0)           # None from the SDK means "not this call", not 0 tokens

    cands = getattr(r, "candidates", None) or []
    fr = getattr(cands[0], "finish_reason", None) if cands else None
    finish = (getattr(fr, "name", None) or str(fr)) if fr is not None else ("UNKNOWN" if cands else "NO_CANDIDATES")
    return {"tokens_in": n("prompt_token_count"), "cached": n("cached_content_token_count"),
            "visible": n("candidates_token_count"), "thought": n("thoughts_token_count"), "finish": finish}


class Recorder:
    """generator._client for the bench's run. generate() reaches the model through _client_for(), which returns _client
    for a model name, so every call comes through generate_content() here: sent on with thinking_config at `level` and,
    when `temperature` is set, a temperature - everything else as generator._call built it - and kept in `calls` with
    the config as sent, the usage and the time it took."""

    def __init__(self, client, types_module):
        self.client, self.types = client, types_module
        self.level, self.temperature, self.calls = KIT_LEVEL, None, []

    @property
    def models(self):
        return self

    def configure(self, config):
        fields = {"thinking_config": self.types.ThinkingConfig(thinking_level=self.level)}
        if self.temperature is not None:
            fields["temperature"] = self.temperature
        if isinstance(config, dict):
            return {**config, **fields}
        return config.model_copy(update=fields)

    def generate_content(self, *, model, contents, config=None):
        config = self.configure(config)
        call = {"model": model, **sent(config)}
        self.calls.append(call)
        t0 = time.monotonic()
        try:
            r = self.client.models.generate_content(model=model, contents=contents, config=config)
        except Exception as e:
            call.update(ms=int((time.monotonic() - t0) * 1000), error=f"{type(e).__name__}: {str(e)[:160]}")
            raise
        call.update(ms=int((time.monotonic() - t0) * 1000), **usage_of(r))
        return r


def call_inr(call: dict) -> float:
    """One call at list price (shared/prices.py): the prompt, its cached part at a tenth of the input rate, and the
    output - the visible and the thought tokens alike, both billed as output on the 3.x family."""
    return prices.inr(prices.usd(call.get("model"), call.get("tokens_in", 0),
                                 call.get("visible", 0) + call.get("thought", 0), call.get("cached", 0)))


# --------------------------------------------------------------------- rows and pools
def report_rows(path: str, failing: bool) -> dict[str, dict]:
    """{row id: its record} from a run_eval.py --report file (make eval-live REPORT=); with failing, only the records
    that did not pass."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise SystemExit(f"--from-report {path}: not readable as JSON ({e})")
    records = data.get("records") if isinstance(data, dict) else None
    if not isinstance(records, list):
        raise SystemExit(f"--from-report {path}: not a run_eval.py --report file (it has no records)")
    return {r["id"]: r for r in records if isinstance(r, dict) and r.get("id") and not (failing and r.get("pass"))}


def select_rows(golden: list[dict], ids=(), shapes=(), reported: dict | None = None) -> list[dict]:
    """The golden rows named by --rows, --shape and --from-report, together, in golden.jsonl's order."""
    known = {r["id"] for r in golden}
    missing = sorted({i for i in list(ids) + list(reported or {}) if i not in known})
    if missing:
        raise SystemExit(f"not golden rows: {', '.join(missing)} (evals/golden.jsonl)")
    bad = [s for s in shapes if s not in SHAPES]
    if bad:
        raise SystemExit(f"--shape {bad[0]}: one of {', '.join(SHAPES)}")
    want = set(ids) | set(reported or {})
    return [r for r in golden if r["id"] in want or r["shape"] in shapes]


def chunks_of(pool: list[dict]) -> list[dict]:
    """A /v1/passages pool as generate() reads retrieved chunks: the id, text, source and page under the names
    pack_chunks() and resolve() read, the section and kind as retrieval keeps them."""
    return [{"id": p.get("chunk_id"), "chunk_id": p.get("chunk_id"), "text": p.get("text") or "",
             "source_uri": p.get("source_uri") or "", "page_start": p.get("page"), "section": p.get("section"),
             "kind": p.get("kind") or "text", "doc_type": p.get("doc_type")} for p in pool]


def basename(uri) -> str:
    return str(uri or "").rsplit("/", 1)[-1] or "?"


def pool_line(pool: list[dict]) -> str:
    files = Counter(basename(p.get("source_uri")) for p in pool)
    return f"{len(pool)} passages: " + ", ".join(f"{name} x{n}" for name, n in files.most_common())


def read_pools(rows: list[dict], api_url: str, email: str, token: str | None, passages) -> dict:
    """{row id: its pool, or None when none was read}, one /v1/passages a row, before anything is generated."""
    return {r["id"]: passages(api_url, r["question"], r["tenant"], email, token, top_k=TOP_K) for r in rows}


# --------------------------------------------------------------------- one answer, and every answer
def answer_one(gen, question: str, chunks: list[dict], model: str) -> tuple[int, dict]:
    """generate() once, as /v1/query would answer: (200, the answer's JSON) or, when it raises, (its HTTP status - the
    generator's 502 for an answer it could not parse, an API error's code - or 0, and {"error": ...})."""
    try:
        ans = gen.generate(question, chunks, tenant_id=None, model=model, backend="vertex")
    except Exception as e:  # noqa: BLE001 - an error is the row's outcome, never the bench's end
        status = getattr(e, "status_code", None) or getattr(e, "code", None)
        detail = getattr(e, "detail", None) or str(e)
        return (status if isinstance(status, int) else 0), {"error": f"{type(e).__name__}: {str(detail)[:160]}"}
    return 200, (ans.model_dump(mode="json") if hasattr(ans, "model_dump") else dict(ans))


def answer_line(rec: dict) -> str:
    thought = sum(c.get("thought", 0) for c in rec["calls"])
    visible = sum(c.get("visible", 0) for c in rec["calls"])
    verdict = "pass" if rec["pass"] else ("FAIL" if rec["outcome"] == "ok" else "ERROR")
    extra = f"  {len(rec['calls'])} calls" if len(rec["calls"]) > 1 else ""
    why = f"  {rec['why'][:70]}" if rec["why"] else ""
    return (f"    {rec['id']:7} {rec['arm']:5} {rec['level']:7} run {rec['run']:<2} {verdict:5} thought {thought:6,}  "
            f"visible {visible:5,}  Rs {rec['cost_inr']:.4f}{extra}{why}")


def bench(gen, rows: list[dict], pools: dict, arm_list: list[dict], levels: list[str], runs: int, model: str, judge,
          out=print) -> list[dict]:
    """Every row, arm, level and run, interleaved run by run so a drift on the lane falls on every arm alike. One record
    an answer: its verdict, the calls as the recorder saw them, the rupees, and - when it came back - the answer, its
    citations and each quote's check against the row's pool. generator.SYSTEM and generator._client are the kit's again
    when this returns, whatever happened."""
    kit_system, kit_client = gen.SYSTEM, gen._client
    recorder = Recorder(kit_client, gen.types)
    answers: list[dict] = []
    gen._client = recorder
    try:
        for run in range(1, runs + 1):
            for row in rows:
                pool = pools[row["id"]]
                chunks = chunks_of(pool)
                for arm in arm_list:
                    gen.SYSTEM, recorder.temperature = arm["system"], arm["temperature"]
                    for level in levels:
                        recorder.level, recorder.calls = level, []
                        status, body = answer_one(gen, row["question"], chunks, model)
                        v = judge(row, status, body)
                        rec = {"id": row["id"], "arm": arm["name"], "level": level, "run": run, "status": status,
                               "outcome": v["outcome"], "pass": bool(v["pass"]), "why": v["why"], "calls": recorder.calls}
                        rec["cost_inr"] = sum(call_inr(c) for c in rec["calls"])
                        if v["outcome"] == "ok":
                            rec.update(answerable=body["answerable"], confidence=body["confidence"],
                                       answer=body["answer"][:ANSWER_CHARS], model=body.get("model"),
                                       cites=[{"chunk_id": c.get("chunk_id"), "source_uri": c.get("source_uri"),
                                               "quote": c.get("quote"), "check": run_eval.quote_check(c, pool)}
                                              for c in body["citations"]])
                        else:
                            rec["error"] = body.get("error") if isinstance(body, dict) else None
                        answers.append(rec)
                        out(answer_line(rec))
    finally:
        gen.SYSTEM, gen._client = kit_system, kit_client
    return answers


# --------------------------------------------------------------------- the summary
def flat(text) -> str:
    return " ".join(str(text or "").split())


def summarise(answers: list[dict], arm_names: list[str], levels: list[str]) -> list[dict]:
    """Per arm and level: answers asked, passed and come back (outcome ok); distinct answers and distinct citation sets,
    counted within each row across its runs and summed over the rows; the quote checks; the tokens and the rupees."""
    out = []
    for arm in arm_names:
        for level in levels:
            got = [a for a in answers if a["arm"] == arm and a["level"] == level]
            if not got:
                continue
            ok = [a for a in got if a["outcome"] == "ok"]
            by_row: dict[str, list[dict]] = {}
            for a in ok:
                by_row.setdefault(a["id"], []).append(a)
            quotes = Counter(c["check"] for a in ok for c in a["cites"])
            calls = [c for a in got for c in a["calls"]]
            out.append({"arm": arm, "level": level, "answers": len(got), "passed": sum(a["pass"] for a in got),
                        "ok": len(ok), "errors": len(got) - len(ok),
                        "distinct_answers": sum(len({flat(a["answer"]) for a in rs}) for rs in by_row.values()),
                        "distinct_citations": sum(len({frozenset(c["chunk_id"] for c in a["cites"]) for a in rs})
                                                  for rs in by_row.values()),
                        "quotes": {k: quotes.get(k, 0) for k in run_eval.QUOTE_VERDICTS},
                        "tokens_in": sum(c.get("tokens_in", 0) for c in calls),
                        "thought": sum(c.get("thought", 0) for c in calls),
                        "visible": sum(c.get("visible", 0) for c in calls),
                        "calls": len(calls),
                        "retried": sum(1 for a in got if len(a["calls"]) > 1 and a["calls"][0].get("finish") == "MAX_TOKENS"),
                        "fell_back": sum(1 for a in ok if a.get("model") != a["calls"][0]["model"]),
                        "cost_inr": sum(a["cost_inr"] for a in got)})
    return out


def summary_lines(summary: list[dict]) -> list[str]:
    """The table, then what its columns count, the quote checks, and any error or retry."""
    lines = [f"  {'arm':5} {'level':7} {'pass':<32} {'distinct':>9} {'cite sets':>10} {'thought':>8} {'visible':>8} "
             f"{'Rs/answer':>10}"]
    for s in summary:
        n = s["answers"]
        distinct, cited = f"{s['distinct_answers']} of {s['ok']}", f"{s['distinct_citations']} of {s['ok']}"
        lines.append(f"  {s['arm']:5} {s['level']:7} {rate(s['passed'], n):<32} {distinct:>9} {cited:>10} "
                     f"{s['thought'] / n:8.0f} {s['visible'] / n:8.0f} {s['cost_inr'] / n:10.4f}")
    lines.append("  distinct: answer texts that differ within a row across its runs, summed over the rows; cite sets: the "
                 "same for the passages cited; thought and visible: output tokens an answer, every call of it counted")
    for s in summary:
        q = s["quotes"]
        quoted = sum(q.values())
        if quoted:
            rest = ", ".join(f"{k} {q[k]}" for k in run_eval.QUOTE_VERDICTS if k != "own" and q[k])
            lines.append(f"  quotes {s['arm']} {s['level']}: {q['own']} of {quoted} in the passage they cite"
                         + (f" ({rest})" if rest else ""))
        if s["errors"]:
            lines.append(f"  errors {s['arm']} {s['level']}: {s['errors']} of {s['answers']} came back as an error, not "
                         f"an answer")
        if s["retried"]:
            lines.append(f"  retried {s['arm']} {s['level']}: {s['retried']} of {s['answers']} were cut off at "
                         f"max_output_tokens and asked again with three times the room (generator.generate)")
        if s["fell_back"]:
            lines.append(f"  fell back {s['arm']} {s['level']}: {s['fell_back']} of {s['answers']} were answered by the "
                         f"default model after a 429 on the one asked (generator._call_or_fallback)")
    return lines


def show_lines(rows: list[dict], pools: dict, answers: list[dict], arm_names: list[str], levels: list[str]) -> list[str]:
    """--show: each row's pool, then its distinct answers per arm and level, most frequent first."""
    lines = []
    for row in rows:
        lines.append(f"\n  {row['id']} ({row['shape']}, {row['tenant']}): {row['question']}")
        for p in pools[row["id"]]:
            page = f" p.{p['page']}" if p.get("page") else ""
            lines.append(f"    [{p.get('n', '?')}] {basename(p.get('source_uri'))}{page}: {flat(p.get('text'))[:110]!r}")
        for arm in arm_names:
            for level in levels:
                got = [a for a in answers if a["id"] == row["id"] and a["arm"] == arm and a["level"] == level]
                if not got:
                    continue
                texts = Counter(flat(a.get("answer")) if a["outcome"] == "ok" else f"<{a['why']}>" for a in got)
                lines.append(f"    {arm} {level}: {len(texts)} distinct of {len(got)}")
                for text, n in texts.most_common():
                    lines.append(f"      {n}x  {text[:150]!r}")
    return lines


# --------------------------------------------------------------------- the lane's identifiers, as the pages print them
PLACEHOLDER_PROJECT, PLACEHOLDER_NUMBER = "documind-ai-YOUR-ID", "NUMBER"     # the lesson pages' placeholders
PROJECT_ID = re.compile(r"[a-z][a-z0-9-]{4,28}[a-z0-9]")                       # a project id's shape
RUN_APP_NUMBER = re.compile(r"(?<=-)\d{6,}(?=\.[a-z0-9-]+\.run\.app)")         # Cloud Run's <service>-NUMBER.REGION.run.app
PATH_NUMBER = re.compile(r"(?<=projects/)\d{6,}(?=/)")                         # a resource path's projects/NUMBER/


def redactor(project: str | None, api_url: str | None, on: bool = True):
    """A function of one text: the text with the lane's project id and project number as the pages print them. The id
    (GOOGLE_CLOUD_PROJECT) is replaced as a whole name, or where it starts one; the number read from the API's address
    wherever it stands as a whole number, and any number in a Cloud Run address or a resource path. Off: the text as
    it is."""
    if not on:
        return lambda text: text
    pid = project if project and PROJECT_ID.fullmatch(project) else None
    found = RUN_APP_NUMBER.search(api_url or "")
    patterns = ([(re.compile(rf"(?<![a-z0-9]){re.escape(pid)}(?![a-z0-9])"), PLACEHOLDER_PROJECT)] if pid else []) + \
        ([(re.compile(rf"(?<!\d){found.group(0)}(?!\d)"), PLACEHOLDER_NUMBER)] if found else []) + \
        [(RUN_APP_NUMBER, PLACEHOLDER_NUMBER), (PATH_NUMBER, PLACEHOLDER_NUMBER)]

    def hide(text: str) -> str:
        for pattern, placeholder in patterns:
            text = pattern.sub(placeholder, text)
        return text
    return hide


def redacted(value, hide):
    """A report's value with hide() applied to every string in it: its numbers stay numbers."""
    if isinstance(value, str):
        return hide(value)
    if isinstance(value, dict):
        return {k: redacted(v, hide) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redacted(v, hide) for v in value]
    return value


def report_to(record: dict, f, hide) -> None:
    """--report's file: the run's record as JSON, every string in it through hide()."""
    json.dump(redacted(record, hide), f, indent=1)


class Redacted:
    """A text stream written through hide(): what the bench prints, as the pages print it. Each print() writes its text
    in one piece, so an identifier is never split between two writes."""

    def __init__(self, stream, hide):
        self.stream, self.hide = stream, hide

    def write(self, text: str) -> int:
        return self.stream.write(self.hide(text))

    def flush(self) -> None:
        self.stream.flush()

    def __getattr__(self, name):
        return getattr(self.stream, name)


# --------------------------------------------------------------------- the generator, from your shell
def load_generator():
    """services/rag-api/generator.py, imported as the service imports it: rag-api's own directory before site-packages
    (its config, schemas, context_budget and cache_manager), and shared/ for the contract. Importing it builds the global
    genai.Client and calls nothing; the model is called only when generate() runs."""
    if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
        raise SystemExit("GOOGLE_CLOUD_PROJECT is not set: generator.py's settings (services/rag-api/config.py) need your "
                         "lane's project id, and its client calls Gemini there (make bench sets it)")
    if RAG_API not in sys.path:
        sys.path.insert(1, RAG_API)                     # after evals/, before site-packages: the service's own order
    try:
        import generator
    except ImportError as e:
        raise SystemExit(f"generator.py needs rag-api's pins, and this shell lacks {e.name}: "
                         f"pip install -r services/rag-api/requirements.txt (once)")
    return generator


def file_sha(path) -> str | None:
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except (OSError, TypeError):
        return None


def parse_levels(text: str) -> list[str]:
    levels = []
    for part in (text or "").split(","):
        level = part.strip().upper()
        if level not in LEVELS:
            raise SystemExit(f"--levels {part.strip() or '(empty)'}: one of {', '.join(LEVELS)}")
        if level not in levels:
            levels.append(level)
    return levels


def names(text: str | None) -> list[str]:
    return [x.strip() for x in (text or "").split(",") if x.strip()]


def main(argv: list[str] | None = None, generator=None, passages=None, sources=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--api-url", help="your lane's API, for /v1/passages and /v1/sources (make bench sets it)")
    ap.add_argument("--rows", help="golden row ids, comma-separated (lk-06,jn-03)")
    ap.add_argument("--shape", help=f"golden shapes, comma-separated: {', '.join(SHAPES)}")
    ap.add_argument("--from-report", metavar="FILE", help="the rows of a run_eval.py --report file (make eval-live REPORT=)")
    ap.add_argument("--failing", action="store_true", help="with --from-report: only its rows that did not pass")
    ap.add_argument("--runs", type=int, default=1, help="answers per row, arm and level (default 1)")
    ap.add_argument("--levels", default=KIT_LEVEL, help=f"thinking levels, comma-separated, of {', '.join(LEVELS)} "
                                                        f"(default {KIT_LEVEL}, generator.py's)")
    ap.add_argument("--temperature", type=float, help="the edit arm sends this temperature (generator.py sends none)")
    ap.add_argument("--add-rule", action="append", default=[], metavar="TEXT", help="the edit arm's SYSTEM gains this "
                                                                                    "rule, in memory (repeatable)")
    ap.add_argument("--drop-rule", action="append", type=int, default=[], metavar="N",
                    help="the edit arm's SYSTEM loses the kit's rule N, in memory (repeatable)")
    ap.add_argument("--no-baseline", action="store_true", help="run the edit arm alone, without the kit arm")
    ap.add_argument("--model", help="the model generate() asks (default generator.py's settings.generator_model)")
    ap.add_argument("--show", action="store_true", help="print each row's pool and its distinct answers")
    ap.add_argument("--report", metavar="FILE", help="write every answer, its config, usage and verdict here as JSON")
    a = ap.parse_args(argv)
    # The lane's identifiers as the pages print them (IDENTIFIERS, above): stdout and stderr are written through the
    # redactor while the bench runs, and run_bench() writes the report through it (13 October 2026).
    hide = redactor(os.environ.get("GOOGLE_CLOUD_PROJECT"), a.api_url, os.environ.get("BENCH_REDACT", "1") != "0")
    with contextlib.redirect_stdout(Redacted(sys.stdout, hide)), contextlib.redirect_stderr(Redacted(sys.stderr, hide)):
        return run_bench(ap, a, hide, generator, passages, sources)


def run_bench(ap, a, hide, generator=None, passages=None, sources=None) -> int:
    """The bench, its arguments read by main(): the rows and their pools, every answer, the summary and the report."""
    levels = parse_levels(a.levels)
    if a.runs < 1:
        ap.error("--runs is 1 or more")
    if a.failing and not a.from_report:
        ap.error("--failing picks the failing rows of --from-report FILE")
    if not (a.rows or a.shape or a.from_report):
        ap.error("name the rows: --rows, --shape or --from-report FILE [--failing]")
    if not a.api_url:
        ap.error("--api-url: your lane's API, where each row's pool is read (make bench sets it)")
    if a.no_baseline and not (a.add_rule or a.drop_rule or a.temperature is not None):
        ap.error("--no-baseline leaves nothing to run without --add-rule, --drop-rule or --temperature")
    golden = run_eval.load_golden()
    reported = report_rows(a.from_report, a.failing) if a.from_report else None
    rows = select_rows(golden, names(a.rows), names(a.shape), reported)
    if not rows:
        print(f"  no row to bench: {a.from_report} has no {'failing ' if a.failing else ''}rows")
        return 0

    gen = generator or load_generator()
    model = a.model or gen.settings.generator_model
    if model.startswith("projects/"):
        raise SystemExit(f"--model {model}: a tuned endpoint is served on a regional client, not the global one the bench "
                         "records (generator._client_for); judge it with make candidate and make eval-live")
    try:
        arm_list = arms(gen.SYSTEM, a.add_rule, a.drop_rule, a.temperature, baseline=not a.no_baseline)
    except ValueError as e:
        raise SystemExit(str(e))
    path = getattr(gen, "__file__", None)
    before = file_sha(path)

    token = os.environ.get("DOCUMIND_ID_TOKEN") or None
    email = os.environ.get("DOCUMIND_USER_EMAIL", "eval@documind.in")
    answers_due = len(rows) * len(arm_list) * len(levels) * a.runs
    print(f"== prompt bench: {model}, against {a.api_url} ==")
    print(f"  {len(rows)} row(s) x {len(arm_list)} arm(s) x {len(levels)} level(s) x {a.runs} run(s): up to "
          f"{answers_due} answers, one generate() each")
    print(f"  pools: POST /v1/passages once a row (top_k {TOP_K}), held fixed for every arm, level and run")
    pools = read_pools(rows, a.api_url, email, token, passages or run_eval.passages)
    benched = []
    for r in rows:
        pool = pools[r["id"]]
        if pool is None:
            state = "no pool read back (an error, a 4xx or the Desk's door): not benched"
        elif not pool:
            state = "an empty pool, which /v1/query refuses with no model call: not benched"
        else:
            state = pool_line(pool)
        print(f"    {r['id']:7} {r['shape']:9} {r['tenant']:7} {state}")
        if reported and r["id"] in reported:
            rec = reported[r["id"]]
            print(f"            eval-live: {'pass' if rec.get('pass') else 'did not pass'}"
                  f"{' - ' + str(rec.get('why')) if rec.get('why') else ''}")
        if pool:
            benched.append(r)
    if not benched:
        print("  no pool to answer from: nothing benched")
        return 1
    kit_system, dated = gen.SYSTEM, getattr(gen, "DATED_RULE", "")
    print("  arms (prompt sha256: SYSTEM followed by DATED_RULE, the text every prompt starts with)")
    for arm in arm_list:
        what = "; ".join(arm["changes"]) or "generator.py's SYSTEM"
        temp = "no temperature" if arm["temperature"] is None else f"temperature {arm['temperature']:g}"
        print(f"    {arm['name']:5} {what} - {rule_count(arm['system'])}; {temp}")
        print(f"          prompt sha256 {prompt_sha(arm['system'], dated)}")
    if arm_list[0]["name"] == "kit" and KIT_LEVEL in levels:
        print(f"    (the kit arm at {KIT_LEVEL} is the API's own request: generator.py's SYSTEM, thinking_level "
              f"{KIT_LEVEL}, no temperature)")

    fetch = sources or run_eval.fetch_current_shas
    current = {t: fetch(a.api_url, t, token) for t in sorted({r["tenant"] for r in benched})}
    manifest = run_eval.load_manifest_objects()
    corpus = run_eval.load_corpus()
    text_of = {t: re.sub(r"\s+", " ", run_eval.haystack(corpus, t)) for t in current}

    def judge(row, status, body):
        return run_eval.row_verdict(row, status, body, current[row["tenant"]], manifest, text_of[row["tenant"]])

    print("\n  answers")
    answers = bench(gen, benched, pools, arm_list, levels, a.runs, model, judge)
    arm_names = [arm["name"] for arm in arm_list]
    summary = summarise(answers, arm_names, levels)
    print()
    for line in summary_lines(summary):
        print(line)
    skipped = sorted(t for t, v in current.items() if v is None)
    if skipped:
        print(f"  [info] version check skipped for {', '.join(skipped)}: GET /v1/sources was unavailable")
    if a.show:
        for line in show_lines(benched, pools, answers, arm_names, levels):
            print(line)
    after = file_sha(path)
    calls = sum(len(x["calls"]) for x in answers)
    models = sorted({c.get("model") for x in answers for c in x["calls"] if c.get("model")})
    print(f"\n  Rs {sum(x['cost_inr'] for x in answers):.4f} in all: {len(answers)} answers, {calls} model calls on "
          f"{', '.join(models) or model}, priced at list (shared/prices.py)")
    if before and after:
        disk = "unchanged on disk" if before == after else "CHANGED ON DISK during the run"
        back = "SYSTEM is the kit's again" if gen.SYSTEM == kit_system else "SYSTEM WAS NOT PUT BACK"
        print(f"  generator.py {disk}; {back}")
    if a.report:
        os.makedirs(os.path.dirname(os.path.abspath(a.report)), exist_ok=True)
        with open(a.report, "w", encoding="utf-8") as f:
            report_to({"api_url": a.api_url, "model": model, "levels": levels, "runs": a.runs,
                       "arms": [{"name": arm["name"], "changes": arm["changes"], "temperature": arm["temperature"],
                                 "prompt_sha256": prompt_sha(arm["system"], dated), "system": arm["system"]}
                                for arm in arm_list],
                       "rows": [{"id": r["id"], "shape": r["shape"], "tenant": r["tenant"], "question": r["question"],
                                 "benched": r in benched,
                                 "pool": None if pools[r["id"]] is None else
                                 [{**{k: p.get(k) for k in ("n", "chunk_id", "source_uri", "page", "kind")},
                                   "text": (p.get("text") or "")[:ANSWER_CHARS]} for p in pools[r["id"]]],
                                 **({"report": {k: reported[r["id"]].get(k) for k in ("pass", "why", "answer")}}
                                    if reported and r["id"] in reported else {})} for r in rows],
                       "answers": answers, "summary": summary,
                       "version_check_skipped": skipped, "cost_inr": sum(x["cost_inr"] for x in answers),
                       "generator_unchanged": (before == after) if before and after else None}, f, hide)
        print(f"  report: {a.report}")
    if before and after and before != after:
        return 1
    return 0 if any(x["outcome"] == "ok" for x in answers) else 1


if __name__ == "__main__":
    sys.exit(main())
