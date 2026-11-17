#!/usr/bin/env python3
"""Eval-gated self-improvement (workshop lesson 12.4): what make improve runs. A production answer that went wrong
becomes a proposed rule for the generator's prompt; a person accepts it as the next prompt version; the gate judges
that version on a candidate revision before any traffic moves.

    python evals/improve.py propose --row ROW.json --project <id>     # gemini-3.1-pro-preview proposes one rule
    python evals/improve.py propose --row ROW.json --rule "..."       # your own rule: no model call, Rs 0
    python evals/improve.py propose --row ROW.json --prompt-only      # what the proposer would be sent: Rs 0
    python evals/improve.py accept --reviewer you@example.com         # the next version, and the golden row to paste
    python evals/improve.py version v4                                # make prompt-candidate's check: is v4 listed?

THE ROW. ROW.json is one answer from your lane, as you captured it, and what a right answer holds:

    {"tenant": "acme",
     "question": "...",          the question as you asked it on the UI, in your own words: it goes into
                                 evals/build_golden.py and your fork's history, so never a user's words
     "answer": "...",            what the lane answered (the UI, or /v1/query's answer)
     "citations": [...],         optional: the answer's citations, as /v1/query returned them
     "prompt_version": "v3",     optional: the version that answered (GET /version, or the usage row's)
     "wrong": "...",             optional: what is wrong with the answer, in your words
     "expected": {"shape": "lookup", "must_contain": ["..."], "must_retrieve": ["..."]}}

"expected" is the golden row lesson 4.1 writes: shape lookup or join, which the documents answer, with each
must_contain figure and each must_retrieve anchor (a clause id or a document slug) in the tenant's documents; or shape
refusal, which they cannot answer, with both lists empty. A version, isolation or media row is required.json's, and
lesson 4.1 writes those by hand. The figures and anchors are checked against evals/corpus before any model call, as
build_golden.py checks a row, so a row whose golden row could never pass costs nothing.

PROPOSE. The proposer is sent the rules the next version builds on (SYSTEM and the latest version's rules, numbered as
they are served), the row, and what a rule may not say, and returns {rule, why} under a JSON schema: one call to
gemini-3.1-pro-preview, the course's model for high reasoning, on the global endpoint (Gemini 3.x generation is served
only there), at its default thinking. The rule is then checked by services/rag-api/prompt_rules.py: one line, at most
40 words, none of the phrases that undo SYSTEM's rules, not already a rule. A rule that fails is printed and refused,
and nothing is written. One that passes goes to evals/reports/proposal.json (gitignored), with the row, the version it
builds on and the call's tokens and rupees at list price (shared/prices.py; about Rs 2, most of it the thinking). --rule
TEXT is your own proposal, checked the same way, with no call: how a "never refuse" rule meets the check at Rs 0.

ACCEPT. --reviewer is the person who read the proposal (REVIEWER= in make). The next version goes into
prompt_rules.json - the latest version's rules and this one, the reviewer, the date and the golden row's id - and
nothing else is written. A proposal made on a version that is no longer the latest is refused: propose again on the
rules as they are. It prints the R(...) row to paste into evals/build_golden.py, before the bracket that closes GOLDEN
(lesson 4.1's method), and the way on: python evals/build_golden.py and make eval (Rs 0); commit and make build, so the
image carries the version; make prompt-candidate PROMPT_VERSION=vN; make gate, every golden row asked of the candidate
(a rule that slips past the phrases and refuses less meets refusal_rate there); then make promote-gated. A red gate is
no promote, and git revert of the commit that holds the version: no traffic reached it, so dropping it leaves every
served version as it was, and the next rule is accepted on the version before.

WHAT IT NEVER WRITES. The evaluator: run_eval.py, required.json, golden.jsonl, build_golden.py, manifest.json and the
documents under corpus/ and demo/ (EVALUATOR). Every write goes through write(), which refuses them whatever path is
asked for, and anything under services/ but prompt_rules.json: a step that could edit the rows that judge its own rule
would be judged by nothing. The golden row is printed, for a person to paste. evals/tests/test_improve.py runs a
proposal end to end on a copy of the kit and compares every file before and after.

Exit 0 done; 1 refused (a rule the checks refuse, a row whose facts are not in the documents, a stale proposal, a
version prompt_rules.json does not list); 2 an input missing or unreadable, no project for a model call, or a write
improve.py never makes.
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]                  # deploy/: the root of the learner's clone
GENERATOR, CONFIG = "services/rag-api/generator.py", "services/rag-api/config.py"
RULES_PY, RULES = "services/rag-api/prompt_rules.py", "services/rag-api/prompt_rules.json"
REGISTRY = "services/rag-api/prompt_versions.json"
BUILD_GOLDEN, GOLDEN = "evals/build_golden.py", "evals/golden.jsonl"
PROPOSAL = "evals/reports/proposal.json"                   # gitignored, as make eval-live's REPORT= files are
# The evaluator: what run_eval.py judges a candidate with, and what builds golden.jsonl. write() refuses every one.
EVALUATOR = ("evals/run_eval.py", "evals/required.json", "evals/golden.jsonl", "evals/build_golden.py",
             "evals/manifest.json", "evals/corpus", "evals/demo")
MODEL = "gemini-3.1-pro-preview"
LOCATION = "global"
SHAPES = {"lookup": "lk", "join": "jn", "refusal": "rf"}   # the golden shapes a prompt rule can put right: their ids
SCHEMA = {"type": "object", "properties": {
    "rule": {"type": "string", "description": "the one rule to add: one line, at most 40 words, without a number"},
    "why": {"type": "string", "description": "the failure it puts right, in general terms, in one or two sentences"}},
    "required": ["rule", "why"]}
RETRY = {"attempts": 4, "initial_delay": 2.0, "max_delay": 30.0, "http_status_codes": [408, 429, 500, 502, 503, 504]}


class Refused(Exception):
    """Exit 1: the checks refuse it, and nothing is written."""


class Unusable(Exception):
    """Exit 2: an input missing or unreadable, no project for a model call, or a write improve.py never makes."""


# --------------------------------------------------------------------- the kit, read
def module(kit: Path, rel: str, name: str):
    """A kit module loaded by path from this kit, so a copy under test is whole: prompt_rules.py, run_eval.py and
    shared/prices.py, all standard library."""
    path = kit / rel
    if not path.is_file():
        raise Unusable(f"{rel}: not found under {kit}")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_json(path: Path, what: str):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as e:
        raise Unusable(f"{what}: cannot read {path} ({e.strerror or e})") from None
    except ValueError as e:
        raise Unusable(f"{what}: {path} is not JSON ({e})") from None


def literal(kit: Path, name: str) -> str:
    """One of generator.py's string constants, read by AST as make prompt-version reads them: the rag-api is never
    imported (it builds a Gemini client at import, and needs fastapi and pydantic-settings)."""
    tree = ast.parse((kit / GENERATOR).read_text(encoding="utf-8"))
    values = [n.value for n in tree.body if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    try:
        value = ast.literal_eval(values[0]) if len(values) == 1 else None
    except ValueError:
        value = None
    if not isinstance(value, str):
        raise Unusable(f"{GENERATOR}: {name} must be set once, at module level, to a string literal")
    return value


def system_of(kit: Path) -> str:
    return literal(kit, "SYSTEM")


def config_defaults(kit: Path) -> dict:
    """config.py's prompt_id and prompt_version defaults, read by AST: the label /version reports with no
    PROMPT_VERSION set."""
    found = {}
    for node in ast.walk(ast.parse((kit / CONFIG).read_text(encoding="utf-8"))):
        if isinstance(node, ast.ClassDef):
            for st in node.body:
                if (isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name)
                        and st.target.id in ("prompt_id", "prompt_version") and isinstance(st.value, ast.Constant)
                        and isinstance(st.value.value, str)):
                    found[st.target.id] = st.value.value
    if len(found) != 2:
        raise Unusable(f"{CONFIG}: prompt_id and prompt_version must be declared with string defaults")
    return found


def rules_doc(kit: Path):
    """(prompt_rules, the file checked whole, its latest version)."""
    pr = module(kit, RULES_PY, "prompt_rules_improve")
    try:
        doc = pr.load(kit / RULES)
    except pr.RulesError as e:
        raise Unusable(str(e)) from None
    return pr, doc, max(doc["versions"], key=lambda v: int(v[1:]))


def golden_ids(kit: Path) -> set[str]:
    """The ids in the golden set: GOLDEN's rows in build_golden.py (each starts its own line, as lesson 4.1's build
    asserts) and golden.jsonl's."""
    ids = set(re.findall(r'(?m)^    R\("([^"]+)"', (kit / BUILD_GOLDEN).read_text(encoding="utf-8")))
    if (kit / GOLDEN).is_file():
        ids |= {json.loads(line)["id"] for line in (kit / GOLDEN).read_text(encoding="utf-8").splitlines() if line.strip()}
    return ids


def next_id(ids: set[str], shape: str) -> str:
    prefix = SHAPES[shape]
    numbers = [int(m.group(1)) for i in ids for m in [re.fullmatch(prefix + r"-([0-9]+)", i)] if m]
    return f"{prefix}-{max(numbers, default=0) + 1:02d}"


def next_version(versions: dict, labels: set[str], prompt_id: str, default: str) -> str:
    """The version after the highest vN in use: listed in prompt_rules.json, registered for this prompt_id in lesson
    3.6's registry, or config.py's default. A version 3.6 made by editing SYSTEM is never given a second meaning."""
    seen = [int(v[1:]) for v in versions]
    seen += [int(m.group(1)) for label in labels for m in [re.fullmatch(re.escape(prompt_id) + r"@v([1-9][0-9]*)", label)]
             if m]
    seen += [int(m.group(1)) for m in [re.fullmatch(r"v([1-9][0-9]*)", default)] if m]
    return f"v{max(seen) + 1}"


# --------------------------------------------------------------------- the row
def check_row(row) -> dict:
    """The production row's fields, checked (the module docstring); returns its golden facts, answerable filled in."""
    if not isinstance(row, dict):
        raise Unusable("the row is a JSON object: tenant, question, answer and expected")
    missing = [k for k in ("tenant", "question", "answer") if not (isinstance(row.get(k), str) and row[k].strip())]
    if missing:
        raise Unusable(f"the row needs {', '.join(missing)}, as text")
    if any(ord(c) < 32 for c in row["question"]):
        raise Unusable("the question goes on one line, as it was asked")
    exp = row.get("expected")
    if not isinstance(exp, dict):
        raise Unusable('the row needs "expected": {"shape": ..., "must_contain": [...], "must_retrieve": [...]}')
    shape = exp.get("shape")
    if shape not in SHAPES:
        raise Unusable(f"expected.shape is lookup, join or refusal, not {shape!r}: a version, isolation or media row is "
                       "required.json's, and lesson 4.1 writes those by hand")
    contain, retrieve = exp.get("must_contain", []), exp.get("must_retrieve", [])
    for name, values in (("must_contain", contain), ("must_retrieve", retrieve)):
        if not (isinstance(values, list) and all(isinstance(v, str) and v.strip() for v in values)):
            raise Unusable(f"expected.{name} is a list of non-empty strings")
    answerable = shape != "refusal"
    if answerable and not (contain and retrieve):
        raise Unusable(f"a {shape} row needs a must_contain figure and a must_retrieve anchor")
    if not answerable and (contain or retrieve):
        raise Unusable("a refusal row asserts nothing the documents hold: must_contain and must_retrieve stay empty")
    if "answerable" in exp and exp["answerable"] is not answerable:
        raise Unusable(f"a {shape} row is answerable={answerable}")
    return {"shape": shape, "must_contain": contain, "must_retrieve": retrieve, "answerable": answerable}


def corpus_problems(kit: Path, tenant: str, expected: dict) -> list[str]:
    """What build_golden.py would refuse in this row: a figure or an anchor the tenant's documents do not hold. Matched
    as run_eval.py matches an anchor offline (haystack(): the file names and the text, lower-cased)."""
    run_eval = module(kit, "evals/run_eval.py", "run_eval_improve")
    corpus = run_eval.load_corpus()
    if tenant not in corpus:
        return [f"{tenant}: no documents under evals/corpus/{tenant}"]
    hay = run_eval.haystack(corpus, tenant)
    return ([f"must_contain {p!r} is not in {tenant}'s documents" for p in expected["must_contain"]
             if p.lower() not in hay]
            + [f"must_retrieve {a!r} is not in {tenant}'s documents (a clause id or a document slug)"
               for a in expected["must_retrieve"] if a.lower() not in hay])


def describe(expected: dict) -> str:
    if not expected["answerable"]:
        return "refusal: the documents do not hold the answer, so a right answer says so (answerable=false)"
    return (f"{expected['shape']}: contains {', '.join(json.dumps(p, ensure_ascii=False) for p in expected['must_contain'])}"
            f" and cites {', '.join(expected['must_retrieve'])}")


# --------------------------------------------------------------------- the proposer
def proposer_prompt(pr, served: str, dated: str, base: str, row: dict, expected: dict) -> str:
    """What the proposer is sent: the rules as served (DATED_RULE too, which follows them when a packed source carries
    a date), the answer, what a right one holds, and what a rule may not say (prompt_rules.FORBIDDEN's phrases)."""
    cites = json.dumps(row["citations"], ensure_ascii=False) if row.get("citations") else "none recorded"
    phrases = "; ".join(p for _, _, group in pr.FORBIDDEN for p in group)
    return (f"You review one answer from DocuMind, a retrieval-grounded assistant, and propose one rule for its prompt.\n\n"
            f"The prompt's rules today ({base}), which every answer starts with:\n<<<\n{served.rstrip()}\n>>>\n"
            f"When a source in the context carries an effective date, this line follows them too:\n<<<\n{dated.strip()}\n"
            f">>>\n\nThe answer that went wrong:\n- tenant: {row['tenant']}\n- question: {row['question'].strip()}\n"
            f"- answer: {row['answer'].strip()}\n- citations: {cites}\n"
            f"- what a right answer is, as the person who checked it says: {describe(expected)}\n"
            f"- what is wrong with it, in their words: {(row.get('wrong') or '').strip() or 'not stated'}\n\n"
            f"Propose ONE rule to add after the rules above, so that this answer and others like it come out right.\n"
            f"- One line of at most {pr.MAX_WORDS} words, without a number: its place gives it one.\n"
            f"- General: no figure, clause id, document or tenant from this case.\n"
            f"- It keeps every rule above. It never lets the assistant answer from outside the numbered context, refuse "
            f"less when the context does not hold the answer, drop the citations, or quote more than the clause that "
            f"answers.\n- A rule with any of these phrases is refused before it is tested: {phrases}.\n"
            f'Return JSON: "rule", the rule\'s text, and "why", the failure it puts right in general terms, in one or two '
            f"sentences.")


def config() -> dict:
    """The request, as a dict google-genai validates into GenerateContentConfig (services/chat/desk_router.py builds its
    own the same way): JSON under SCHEMA, the model's default thinking, a 429 or a 5xx retried with backoff."""
    return {"response_mime_type": "application/json", "response_json_schema": SCHEMA,
            "http_options": {"retry_options": RETRY}}


def client_for(project: str):
    """google-genai on the global endpoint, billed to the lane (pip install -r services/rag-api/requirements.txt once, as
    make bench needs)."""
    from google import genai
    return genai.Client(enterprise=True, project=project, location=LOCATION)


def ask(client, model: str, prompt: str) -> tuple[dict, dict]:
    """One call: ({rule, why}, its usage, the thinking billed as output as generator._usage() bills it)."""
    r = client.models.generate_content(model=model, contents=prompt, config=config())
    u = getattr(r, "usage_metadata", None)
    n = lambda k: getattr(u, k, None) or 0  # noqa: E731 - None from the SDK means "not this call", not 0 tokens
    usage = {"tokens_in": n("prompt_token_count"), "tokens_out": n("candidates_token_count") + n("thoughts_token_count"),
             "thinking": n("thoughts_token_count")}
    reply = r.parsed if isinstance(getattr(r, "parsed", None), dict) else None
    if reply is None:
        try:
            reply = json.loads(getattr(r, "text", None) or "")
        except ValueError:
            reply = None
    if not (isinstance(reply, dict) and isinstance(reply.get("rule"), str) and isinstance(reply.get("why"), str)):
        return {"rule": "", "why": f"no rule in the schema's shape: {str(getattr(r, 'text', ''))[:200]!r}"}, usage
    return {"rule": reply["rule"].strip(), "why": reply["why"].strip()}, usage


def priced(kit: Path, model: str, usage: dict) -> dict:
    prices = module(kit, "shared/prices.py", "prices_improve")
    usd = prices.usd(model, usage["tokens_in"], usage["tokens_out"])
    return {**usage, "usd": round(usd, 6), "inr": round(prices.inr(usd), 2)}


# --------------------------------------------------------------------- the one place improve.py writes
def write(kit: Path, target: Path, text: str) -> Path:
    """Every file improve.py writes goes through here: services/rag-api/prompt_rules.json, and a proposal - JSON,
    outside services/. Never the evaluator's files, whatever path is asked for."""
    target = Path(target).resolve()
    for rel in EVALUATOR:
        guarded = (kit / rel).resolve()
        if target == guarded or guarded in target.parents:
            raise Unusable(f"{rel} is the evaluator's, and improve.py never writes it: the golden row is printed for a "
                           "person to paste")
    if target != (kit / RULES).resolve() and (target.suffix != ".json" or (kit / "services").resolve() in target.parents):
        raise Unusable(f"{target.name}: improve.py writes {RULES} and its proposals (JSON, outside services/), nothing else")
    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_name(target.name + ".part")
    part.write_text(text, encoding="utf-8", newline="\n")
    os.replace(part, target)
    return target


def r_row(rid: str, row: dict, expected: dict, note: str) -> str:
    """The golden row on one line, as lesson 4.1 writes one into GOLDEN: R(id, shape, question, tenant, must_contain,
    must_retrieve, answerable, note)."""
    lit = lambda v: json.dumps(v, ensure_ascii=False)  # noqa: E731 - a JSON string or list is a Python literal too
    return (f"    R({lit(rid)}, {lit(expected['shape'])}, {lit(row['question'].strip())}, {lit(row['tenant'])}, "
            f"{lit(expected['must_contain'])}, {lit(expected['must_retrieve'])}, {expected['answerable']}, {lit(note)}),")


# --------------------------------------------------------------------- the three steps
def propose(kit: Path, row_path: str, project: str = "", rule: str | None = None, model: str = MODEL,
            out: str | None = None, prompt_only: bool = False, client=None) -> int:
    if not row_path:
        raise Unusable("ROW= names the production row, a JSON file: python evals/improve.py --help has its shape")
    row = read_json(Path(row_path), "the production row")
    expected = check_row(row)
    bad = corpus_problems(kit, row["tenant"], expected)
    if bad:
        raise Refused("the row's golden row could never pass build_golden.py: " + "; ".join(bad))
    pr, doc, base = rules_doc(kit)
    base_rules = doc["versions"][base]["rules"]
    system = system_of(kit)
    served = pr.numbered(system, base_rules) if base_rules else system
    first = pr.own_rules(system) + len(base_rules) + 1             # the number the new rule is served under
    prompt = proposer_prompt(pr, served, literal(kit, "DATED_RULE"), base, row, expected)
    if prompt_only:
        print(prompt)
        return 0
    if rule is None and not project:
        raise Unusable("a model's proposal needs PROJECT= (the call is billed to your lane); "
                       "IMPROVE_ARGS=\"--rule '...'\" proposes your own rule with none")
    print(f"row:       {row['tenant']}, {row['question'].strip()!r}, answered under "
          f"{row.get('prompt_version') or 'the version /version names'}")
    print(f"expected:  {describe(expected)}")
    print(f"builds on: {base}, SYSTEM's {pr.own_rules(system)} rules and {len(base_rules)} added")
    usage = None
    if rule is not None:
        proposal, proposer = {"rule": rule.strip(), "why": "a person's own rule"}, "person"
        print("proposer:  a person (--rule): no model call, Rs 0")
    else:
        proposal, usage = ask(client or client_for(project), model, prompt)
        usage = priced(kit, model, usage)
        proposer = model
        print(f"proposer:  {model} on {LOCATION}: {usage['tokens_in']:,} in, {usage['tokens_out']:,} out "
              f"({usage['thinking']:,} of them thinking), Rs {usage['inr']:.2f} at list price (shared/prices.py)")
    print(f"rule:      {first}. {proposal['rule']}")
    print(f"why:       {proposal['why']}")
    problems = pr.problems(proposal["rule"], base_rules)
    if problems:
        for p in problems:
            print(f"REFUSED:   {p}")
        print('Nothing was written. Propose again, or write your own rule: IMPROVE_ARGS="--rule \'...\'"')
        return 1
    print(f"checks:    one line, {len(proposal['rule'].split())} words of at most {pr.MAX_WORDS}, no phrase that undoes "
          f"SYSTEM's rules, not a rule of {base} already: passed")
    record = {"rule": proposal["rule"], "why": proposal["why"], "proposer": proposer, "base": base,
              "base_rules": base_rules, "row": row, "usage": usage,
              "proposed": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    path = write(kit, Path(out) if out else kit / PROPOSAL, json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {path}")
    print("Read it, then accept it as the next version: make improve REVIEWER=you@example.com")
    return 0


def accept(kit: Path, reviewer: str, proposal_path: str | None = None, today: dt.date | None = None) -> int:
    reviewer = (reviewer or "").strip()
    if not reviewer or any(ord(c) < 32 for c in reviewer) or len(reviewer) > 120:
        raise Unusable("REVIEWER= names the person who read the proposal: a name or an email, on one line")
    proposal = read_json(Path(proposal_path) if proposal_path else kit / PROPOSAL,
                         "the proposal (make improve ROW=... writes it)")
    if not (isinstance(proposal, dict) and isinstance(proposal.get("rule"), str) and isinstance(proposal.get("base"), str)
            and isinstance(proposal.get("base_rules"), list) and isinstance(proposal.get("proposer"), str)):
        raise Unusable("the proposal is not one make improve wrote: rule, base, base_rules, row and proposer")
    if proposal["proposer"] != "person" and reviewer.casefold() == proposal["proposer"].casefold():
        raise Refused(f"{reviewer} proposed this rule; a person reads it and accepts it")
    pr, doc, base = rules_doc(kit)
    if base != proposal["base"] or doc["versions"][base]["rules"] != proposal["base_rules"]:
        raise Refused(f"the rules moved on since this proposal: it was made on {proposal['base']}, and the latest version "
                      f"is {base}. Propose again on the rules as they are")
    row, rule = proposal.get("row"), proposal["rule"]
    expected = check_row(row)
    bad = corpus_problems(kit, row["tenant"], expected) + pr.problems(rule, proposal["base_rules"])
    if bad:
        raise Refused("; ".join(bad))
    defaults = config_defaults(kit)
    try:
        labels = pr.registered(kit / REGISTRY)
        if (kit / "commands/prompt_pin.py").is_file():         # lesson 3.6's registry tool: every label the registry
            labels |= module(kit, "commands/prompt_pin.py", "prompt_pin_improve").spent(kit, defaults["prompt_id"])
                                                            # held in any commit git keeps (a spent v4; 14 October 2026)
    except pr.RulesError:
        labels = set()
    new = next_version(doc["versions"], labels, defaults["prompt_id"], defaults["prompt_version"])
    taken = {e["golden_row"] for e in doc["versions"].values() if isinstance(e.get("golden_row"), str)}
    rid = next_id(golden_ids(kit) | taken, expected["shape"])        # an id printed before, and not pasted yet
    date = (today or dt.date.today()).isoformat()
    after = json.loads(json.dumps(doc))
    after["versions"][new] = {"rules": proposal["base_rules"] + [rule], "reviewer": reviewer, "accepted": date,
                              "proposer": proposal["proposer"], "golden_row": rid}
    bad = pr.problems_in(after) + pr.extends(doc, after)
    if bad:
        raise Refused("; ".join(bad))
    write(kit, kit / RULES, pr.dumps(after))
    label = f"{defaults['prompt_id']}@{new}"
    number = pr.own_rules(system_of(kit)) + len(proposal["base_rules"]) + 1
    print(f"accepted:  {label}, {base}'s {len(proposal['base_rules'])} added rules and this one, by {reviewer} on {date}")
    print(f"           {number}. {rule}")
    print(f"wrote {RULES}")
    note = (f"Lesson 12.4. A production answer under {row.get('prompt_version') or base} went wrong here; {new}'s rule "
            f"{number}, accepted by {reviewer} on {date}, is the change the gate judges.")
    print("\nThe golden row, for a person to paste into evals/build_golden.py before the ] that closes GOLDEN (lesson 4.1):")
    print(r_row(rid, row, expected, note))
    run_eval = module(kit, "evals/run_eval.py", "run_eval_improve")
    # refusal_rate's denominator is live()'s: every row with answerable false, the isolation rows among them, not the
    # refusal shape alone (13 October 2026: this line counted 8 rows where the gate divides by 18).
    unanswerable = sum(1 for r in run_eval.load_golden() if not r["answerable"])
    print(f"\nThen:\n  python evals/build_golden.py; make eval     the golden set checks itself, offline (Rs 0)\n"
          f"  git commit; make build                      the image carries {RULES}'s {new}\n"
          f"  make prompt-candidate PROMPT_VERSION={new}    a no-traffic revision tagged candidate, answering as {label}\n"
          f"  make gate                                   every golden row asked of it: refusal_rate at least "
          f"{run_eval.THRESHOLDS['refusal_rate']:.0%} over the {unanswerable} rows the documents cannot answer, and "
          f"required.json's {len(run_eval.load_required())} rows each\n"
          f"  make promote-gated                          traffic to it; make rollback returns to the one before\n"
          f"  or, the gate red: no promote. git revert the commit that holds {new} (no traffic reached it); "
          f"PROMPT_VERSION={new} stays in documind-api's template until make deploy-services, or make prompt-candidate "
          f"PROMPT_VERSION={defaults['prompt_version']} after make build")
    return 0


def version(kit: Path, name: str) -> int:
    """make prompt-candidate's check, before gcloud: the version is one prompt_rules.json lists."""
    name = (name or "").strip()
    if not name:
        raise Unusable("PROMPT_VERSION= names the version the candidate answers under: make prompt-candidate "
                       "PROMPT_VERSION=v4, a version services/rag-api/prompt_rules.json lists")
    pr, doc, _ = rules_doc(kit)
    versions, prompt_id = doc["versions"], config_defaults(kit)["prompt_id"]
    if name not in versions:
        print(f"PROMPT_VERSION={name} is not in {RULES}, which lists {', '.join(sorted(versions, key=lambda v: int(v[1:])))}."
              f" A version is listed once a person accepts its rule (make improve REVIEWER=); commit it and make build "
              f"before its candidate. A version made by editing SYSTEM (lesson 3.6) goes out with make release-candidate.")
        return 1
    entry, own = versions[name], pr.own_rules(system_of(kit))
    who = f", accepted by {entry['reviewer']} on {entry['accepted']}" if entry.get("reviewer") else ""
    print(f"{prompt_id}@{name}: SYSTEM's {own} rules and {len(entry['rules'])} added{who}")
    for number, rule in enumerate(entry["rules"], own + 1):
        print(f"  {number}. {rule}")
    return 0


def main(argv: list[str] | None = None, client=None) -> int:
    ap = argparse.ArgumentParser(description="Eval-gated self-improvement (lesson 12.4): propose a rule from a "
                                 "production row, accept it as the next prompt version, check a version.")
    ap.add_argument("--kit", type=Path, default=KIT, help="the kit's root, deploy/ (default: the one this file is in)")
    sub = ap.add_subparsers(dest="step", required=True)
    p = sub.add_parser("propose", help="one rule from a production row: the model's, or --rule's")
    p.add_argument("--row", default="", help="the production row, a JSON file (this file's docstring has its shape)")
    p.add_argument("--project", default=os.environ.get("GOOGLE_CLOUD_PROJECT", ""), help="the lane billed for the call")
    p.add_argument("--rule", default=None, help="your own rule: checked the same way, with no model call")
    p.add_argument("--model", default=MODEL, help=f"the proposer (default {MODEL}, on the {LOCATION} endpoint)")
    p.add_argument("--out", default=None, help=f"where the proposal goes (default {PROPOSAL})")
    p.add_argument("--prompt-only", action="store_true", help="print what the proposer would be sent, and stop")
    a = sub.add_parser("accept", help="the proposal as the next version in prompt_rules.json, and the golden row")
    a.add_argument("--reviewer", required=True, help="the person who read the proposal")
    a.add_argument("--proposal", default=None, help=f"the proposal to accept (default {PROPOSAL})")
    v = sub.add_parser("version", help="is this version one prompt_rules.json lists? (make prompt-candidate)")
    v.add_argument("name", nargs="?", default="", help="the version, v4")
    args = ap.parse_args(argv)
    kit = args.kit.resolve()
    try:
        if args.step == "propose":
            return propose(kit, args.row, args.project, args.rule, args.model, args.out, args.prompt_only, client)
        if args.step == "accept":
            return accept(kit, args.reviewer, args.proposal)
        return version(kit, args.name)
    except Refused as e:
        print(f"improve: refused: {e}", file=sys.stderr)
        return 1
    except Unusable as e:
        print(f"improve: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
