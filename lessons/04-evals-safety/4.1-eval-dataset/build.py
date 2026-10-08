"""Build lesson 4.1 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Every offline cell on the page is run here, in order, on a copy of the kit's evals folder under a scratch git
repository, so each expected block is the kit's own output: the gate on the set as it stands, the clause table,
the scoped listing, the lookup row written into build_golden.py and built, the six variants, the isolation row's
three tries, required.json, the paraphrase pairs and the self-test, the candidate check, and the diff the lesson
keeps as a patch. The row scorer's evidence is the gate's matching rule run over evals/corpus, and its JavaScript
port of normalise() and contains() is checked against run_eval.py with node before the page is written.
"""
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "4.1"
title = "<title>Lesson 4.1 Build a useful evaluation dataset - rows that can fail, find their evidence and cannot quietly vanish, written into the kit's golden set and accepted by its offline gate | Netsetos</title>\n"
LANE = "/home/you/deploy_module_rag"          # where the setup block puts the kit; the page's paths are the lane's

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.rs-l{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;margin-bottom:10px;}
.rs-l select,.rs-l textarea{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.rs-l textarea{font-family:var(--mono);line-height:1.4;min-height:88px;resize:vertical;}
.rs-json{background:var(--code-bg);color:var(--code-text);font-family:var(--mono);font-size:12px;line-height:1.5;padding:10px 12px;border-radius:10px;margin:0 0 8px;white-space:pre-wrap;overflow-wrap:anywhere;}
.rs-why{font-size:12.5px;color:var(--slate);margin:0 0 8px;}
.rs-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;}
.rs-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}
.rs-box ul{margin:0;padding-left:18px;}
.rs-box li{overflow-wrap:anywhere;margin:2px 0;}
.rs-box code{overflow-wrap:anywhere;}
.rs-ok{color:#047857;font-weight:700;}.rs-no{color:#b91c1c;font-weight:700;}
.rs-snip{display:block;font-family:var(--mono);font-size:11.5px;color:#475569;}
.rs-chips{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 8px;}
.rs-chips button{font:inherit;font-size:13px;background:#f0fdfa;color:var(--teal-dark);border:1px solid #99f6e4;border-radius:999px;padding:6px 12px;min-height:44px;cursor:pointer;}
.rs-said{display:inline-flex;align-items:center;gap:8px;min-height:44px;font-size:var(--small-size);color:var(--slate);margin-bottom:8px;}
.rs-said input{width:22px;height:22px;margin:0;}
.rs-verdict{font-family:var(--mono);font-size:13px;font-weight:700;padding:6px 10px;border-radius:8px;display:inline-block;margin-bottom:6px;}
.rs-verdict.pass{background:#d1fae5;color:#065f46;}.rs-verdict.fail{background:#fee2e2;color:#991b1b;}
@media (hover:hover) and (pointer:fine){.rs-chips button:hover{background:#ccfbf1;}}
.rs-chips button:active{background:#99f6e4;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
BG, RE_, CT, ME = "evals/build_golden.py", "evals/run_eval.py", "evals/cache_threshold.py", "evals/make_evalset.py"

EXCERPTS = {
    "make_eval": ("Makefile - the eval target: the offline half, part of dryrun and of every pull request",
                  block("Makefile", "# The eval gate, offline half: no credentials, no cost, no network.", n=6)),
    "row_fn": ("evals/build_golden.py - R(): a row is a call, and the optional fields appear only when they are set",
               block(BG, "def R(rid, shape, q, tenant, contain, retrieve, answerable, note=None,", end="GOLDEN = [")),
    "shapes": ("evals/build_golden.py - a lookup, a refusal and an isolation row, as the file writes them",
               block(BG, 'R("lk-06", "lookup"', n=2) + "\n" + block(BG, 'R("rf-03", "refusal"', n=4) + "\n" + block(BG, 'R("iso-01", "isolation"', n=5)),
    "falsifiable": ("evals/run_eval.py - check_falsifiable(): an answerable row needs a figure, and the figure must be in its tenant's files",
                    block(RE_, "def check_falsifiable(golden: list[dict], corpus: dict) -> list[str]:", n=2) + "\n    ...\n"
                    + block(RE_, '        if row["answerable"] and not row.get("must_contain"):', n=7)),
    "sources_of": ("evals/run_eval.py - sources_of(): the documents a row cites, which is what --source scopes by",
                   block(RE_, "def sources_of(row: dict, corpus: dict) -> set[str]:", n=1) + "\n    ...\n"
                   + block(RE_, '    slugs = {name.rsplit(".", 1)[0] for name in corpus.get(row["tenant"], {})}', end="def in_scope(")),
    "verify_write": ("evals/build_golden.py - main(): every row checked against its own tenant's documents before the file is written",
                     block(BG, "    for r in GOLDEN:", n=9)),
    "leak_rule": ("evals/build_golden.py - the check that makes an isolation row a real test",
                  block(BG, "        # THE CHECK THAT MAKES THESE REAL TESTS: every value an isolation row forbids", end="    shapes = {}")),
    "coverage": ("evals/run_eval.py - MIN_ROWS and check_coverage(): the rows that would go red cannot vanish, or arrive unlisted",
                 block(RE_, 'MIN_ROWS = {"isolation": 5', n=1) + "\n...\n" + block(RE_, "def check_coverage(golden: list[dict]) -> list[str]:", n=1)
                 + "\n    ...\n" + block(RE_, "    counts: dict[str, int] = {}", end="def offline() -> int:")),
    "contains": ("evals/run_eval.py - normalise() and contains(): the figure, not the spelling, and on its own boundaries",
                 block(RE_, "def normalise(text: str) -> str:", n=1) + "\n    ...\n" + block(RE_, '    t = text.lower().replace(",", "").replace("-", " ")', n=4)
                 + "\n\n\n" + block(RE_, "def contains(text: str, want: str) -> bool:", n=1) + "\n    ...\n" + block(RE_, "    w = normalise(want).strip()", n=4)),
    "isolation_gate": ("evals/run_eval.py - check_isolation(): why the live gate for isolation is a 403, not must_not_contain",
                       block(RE_, "def check_isolation(api_url, golden, token, outsider_token=None)", end='    outsider = os.environ.get("DOCUMIND_OUTSIDER_EMAIL"')),
    "check_pairs": ("evals/cache_threshold.py - check_pairs(): what a pair must be before it can judge a threshold",
                    block(CT, "def check_pairs(", n=1) + "\n    ...\n" + block(CT, '        if p["same"] and not g["answerable"]:', n=9)),
    "feed_sql": ("evals/make_evalset.py - feed_rows(): only the chunks the quality gate let through",
                 block(ME, "def feed_rows(project: str, tenant: str, rows: int) -> list[dict]:", n=4)),
    "candidate_row": ("evals/make_evalset.py - the row it writes: shape generated, nothing it must contain, a chunk id to retrieve",
                      block(ME, '            f.write(json.dumps({"id": f"gen-{i:03d}", "shape": "generated", "question": p["question"],', n=5)),
    "make_evalset": ("Makefile - make-evalset: candidates, not a golden set",
                     block("Makefile", "# Eval CANDIDATES from the feed, PII-scanned", n=4)),
}
assert EXCERPTS["row_fn"][1].rstrip().endswith("return row")
assert EXCERPTS["shapes"][1].rstrip().endswith('Rs 40,000.", ["40,000"]),'), EXCERPTS["shapes"][1][-80:]
assert EXCERPTS["falsifiable"][1].rstrip().endswith('the row can only fail")')
assert EXCERPTS["verify_write"][1].rstrip().endswith("is not in {t}'s corpus\")"), EXCERPTS["verify_write"][1][-80:]
assert EXCERPTS["leak_rule"][1].rstrip().endswith('an isolation row needs a must_not_contain")')
assert EXCERPTS["coverage"][1].rstrip().endswith("return bad")
assert EXCERPTS["contains"][1].rstrip().endswith("is not None")
assert EXCERPTS["isolation_gate"][1].rstrip().endswith('"""')
assert EXCERPTS["candidate_row"][1].rstrip().endswith('ensure_ascii=False) + "\\n")'), EXCERPTS["candidate_row"][1][-60:]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's own numbers
sys.path.insert(0, str(KIT / "evals"))
import run_eval as rv  # noqa: E402

corpus = rv.load_corpus()
golden = rv.load_golden()
GOLD = {r["id"]: r for r in golden}
required = rv.load_required()
pairs = [json.loads(line) for line in (KIT / "evals" / "paraphrases.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
shapes = {}
for r in golden:
    shapes[r["shape"]] = shapes.get(r["shape"], 0) + 1
N_DOCS = sum(len(v) for v in corpus.values())
bg_src = (KIT / BG).read_text(encoding="utf-8")
assert sum(line.startswith('    R("') for line in bg_src.split("\n")) == len(golden), "every row starts its own line in GOLDEN"
bg_lines = bg_src.split("\n")
close = bg_lines.index("]", bg_lines.index("GOLDEN = ["))
assert bg_lines[close + 2].startswith("# ----") and "verify then write" in bg_lines[close + 2], "the bracket the cells insert before closes GOLDEN"

# SEC-09's chunk index under the worker's own chunker, for the candidate's chunk id
main_src = (KIT / "services" / "ingest" / "main.py").read_text(encoding="utf-8")
worker = {"re": re, "chunk_hash": lambda t: hashlib.sha256(re.sub(r"\s+", " ", t).strip().encode()).hexdigest()}
for pat in (r"^CHUNK_CHARS, CHUNK_OVERLAP = .*$", r"^_SECTION = .*$", r"^_CODE = .*$"):
    exec(re.search(pat, main_src, re.M).group(0), worker)
for fn in ("_windows", "_chunk"):
    exec(re.search(r"(?ms)^def " + fn + r"\(.*?(?=^\S|\Z)", main_src).group(0), worker)
handbook = (KIT / "evals" / "corpus" / "acme" / "hr_policy_2026.md").read_text(encoding="utf-8")
worker_chunks = worker["_chunk"](handbook)
SEC09_I = next(i for i, c in enumerate(worker_chunks) if c["locator"] == "SEC-09")
assert worker_chunks[0]["locator"] == "preamble" and SEC09_I == 8, (SEC09_I, [c["locator"] for c in worker_chunks[:10]])
HANDBOOK_SHA = hashlib.sha256((KIT / "evals" / "corpus" / "acme" / "hr_policy_2026.md").read_bytes()).hexdigest()

# ------------------------------------------------------------------ the cells: the page's code, run here in order
LK32 = ('    R("lk-32", "lookup", "How long can an account go unused before it is disabled?", "acme", ["45 days"], '
        '["SEC-09", "hr_policy_2026"], True, "Lesson 4.1. SEC-09 was the one clause of the handbook no row asked about. '
        'Zeta holds the same clause, so the row is a lookup and never an isolation row."),')
ISO11_TRY = ('    R("iso-11", "isolation", "How many days of earned leave are encashed on exit?", "zeta", ["20 days"], '
             '["LV-07", "hr_policy_zeta_2026"], True, "Lesson 4.1. The same question, a different answer per tenant: '
             'ACME caps encashment at 45 days.", ["45 days"]),')
ISO11 = ('    R("iso-11", "isolation", "How many days of earned leave are encashed on exit?", "zeta", ["20 days"], '
         '["LV-07", "hr_policy_zeta_2026"], True, "Lesson 4.1. ACME caps encashment at 45 days, and 45 days is also in '
         'SEC-09 of this handbook, so the marker is the phrase only ACME holds.", ["capped at 45 days"]),')


def put_row(rid: str, line: str) -> str:
    return (f"from pathlib import Path\n"
            f"p = Path(\"evals/build_golden.py\")\n"
            f"row = '{line}'\n"
            f"lines = [l for l in p.read_text(encoding=\"utf-8\").split(\"\\n\") if not l.startswith('    R(\"{rid}\",')]\n"
            f"lines.insert(lines.index(\"]\", lines.index(\"GOLDEN = [\")), row)            # before the bracket that closes GOLDEN\n"
            f"p.write_text(\"\\n\".join(lines), encoding=\"utf-8\", newline=\"\\n\")\n"
            f"print(sum(l.startswith('    R(\"') for l in lines), \"rows in GOLDEN; the last is {rid}\")")


PY_CLAUSES = """import json, re
text = open("evals/corpus/acme/hr_policy_2026.md", encoding="utf-8").read()
heads = re.findall(r"(?m)^## (\\S+) \\S (.+)$", text)
rows = [json.loads(l) for l in open("evals/golden.jsonl", encoding="utf-8") if l.strip()]
real = [(code, name) for code, name in heads if not code.startswith("GEN-")]
print(f"hr_policy_2026.md: {len(heads)} sections, {len(heads) - len(real)} of them GEN- filler")
for code, name in real:
    ids = [r["id"] for r in rows if r["tenant"] == "acme" and code in r["must_retrieve"]]
    print(f"  {code:10} {name:24} {' '.join(ids) or '<- no golden row asks about this clause'}")"""

PY_VARIANTS = """import sys; sys.path.insert(0, "evals")
from run_eval import load_corpus, check_falsifiable, check_anchors
corpus = load_corpus()
row = {"id": "lk-32", "shape": "lookup", "tenant": "acme", "must_contain": ["45 days"],
       "must_retrieve": ["SEC-09", "hr_policy_2026"], "answerable": True}
for name, change in [("as written", {}),
                     ("a figure the clause never gives", {"must_contain": ["45 working days"]}),
                     ("words the file breaks across two lines", {"must_contain": ["disabled automatically"]}),
                     ("a clause code with a typo", {"must_retrieve": ["SEC-9", "hr_policy_2026"]}),
                     ("nothing the answer must contain", {"must_contain": []}),
                     ("another clause's figure", {"must_contain": ["60 days"]})]:
    found = check_falsifiable([{**row, **change}], corpus) + check_anchors([{**row, **change}], corpus)
    print(f"{name:40} {'REFUSED' if found else 'accepted'}")
    for f in found:
        print("   ", f)"""

PY_REQUIRED = """import json
from pathlib import Path
p = Path("evals/required.json")
d = json.loads(p.read_text(encoding="utf-8"))
d["ids"] = sorted(set(d["ids"]) | {"iso-11"})
p.write_text(json.dumps(d, indent=1), encoding="utf-8", newline="\\n")
print(len(d["ids"]), "required ids:", " ".join(d["ids"]))"""

PY_PAIRS = """import json
from pathlib import Path
p = Path("evals/paraphrases.jsonl")
new = [{"id": "pp-43", "of": "lk-32", "question": "After how many days without use is an account switched off?",
        "same": True, "why": "reworded", "tenant": "acme"},
       {"id": "pp-44", "of": "lk-32", "question": "How often is production access reviewed?",
        "same": False, "why": "the same clause, another fact: quarterly, not 45 days", "tenant": "acme"}]
keep = [l for l in p.read_text(encoding="utf-8").splitlines() if l.strip() and json.loads(l)["id"] not in ("pp-43", "pp-44")]
p.write_text("\\n".join(keep + [json.dumps(r, ensure_ascii=False) for r in new]) + "\\n", encoding="utf-8", newline="\\n")
print(len(keep) + len(new), "pairs; the last two are against lk-32")"""

PY_CANDIDATE = """import hashlib, sys; sys.path.insert(0, "evals")
from run_eval import load_corpus, check_falsifiable, check_anchors
corpus = load_corpus()
sha = hashlib.sha256(open("evals/corpus/acme/hr_policy_2026.md", "rb").read()).hexdigest()
candidate = {"id": "gen-001", "shape": "generated", "question": "How long can an account stay unused before it is disabled?",
             "tenant": "acme", "must_contain": [], "must_retrieve": [f"acme:{sha}#8"], "answerable": True}
reviewed = {**candidate, "id": "lk-32", "shape": "lookup", "must_contain": ["45 days"], "must_retrieve": ["SEC-09", "hr_policy_2026"]}
for row in (candidate, reviewed):
    found = check_falsifiable([row], corpus) + check_anchors([row], corpus)
    print(f"{row['id']:8} {'REFUSED' if found else 'accepted'}")
    for f in found:
        print("   ", f.replace(sha, sha[:12] + "..."))"""

PY_LIVE = """import os, sys; sys.path.insert(0, "evals")
from run_eval import ask, contains, load_golden
api, rows = os.environ["API"], {r["id"]: r for r in load_golden()}
for rid in ("lk-32", "iso-11"):
    r = rows[rid]
    status, body, ms = ask(api, r["question"], r["tenant"], "eval@documind.in", os.environ["TOKEN"])
    answer, cites = body.get("answer", ""), body.get("citations") or []
    print(f"{rid} as {r['tenant']}: HTTP {status}, answerable {body.get('answerable')}, {len(cites)} citation(s), {ms} ms")
    print("   " + answer[:120])
    for w in r["must_contain"]:
        print(f"   must_contain {w!r}: {'found' if contains(answer, w) else 'MISSING'}")
    for w in r.get("must_not_contain", []):
        print(f"   must_not_contain {w!r}: {'LEAKED' if contains(answer, w) else 'absent'}")
    print("   cites " + ", ".join(sorted({c["source_uri"].split("/", 3)[-1] for c in cites})))
status, _, _ = ask(api, rows["iso-11"]["question"], "zeta", "outsider@not-a-tenant.invalid", os.environ["OUTSIDER"])
print(f"iso-11 asked by documind-outsider-sa: HTTP {status} (the isolation gate requires 403)")"""

GATE = 'python evals/run_eval.py; echo "exit code $?"'
BUILD_HEAD = "python evals/build_golden.py | sed -n '1,5p;$p'"
FILES = "evals/build_golden.py evals/golden.jsonl evals/required.json evals/paraphrases.jsonl"


def heredoc(body: str, prefix: str = "") -> str:
    return f"{prefix}python - <<'PY'\n{body}\nPY"


CELLS = {
    "gate0": "make eval\npython evals/run_eval.py --source hr_policy_2026.md | sed -n '/rows citing/,$p'",
    "clauses": heredoc(PY_CLAUSES),
    "lk32": heredoc(put_row("lk-32", LK32)) + "\n" + BUILD_HEAD + "\n" + GATE,
    "variants": heredoc(PY_VARIANTS),
    "iso_try": heredoc(put_row("iso-11", ISO11_TRY)) + "\npython evals/build_golden.py; echo \"exit code $?\"; wc -l < evals/golden.jsonl",
    "iso_marker": heredoc(put_row("iso-11", ISO11)) + "\n" + BUILD_HEAD + "\n" + GATE,
    "iso_required": heredoc(PY_REQUIRED) + '\nmake eval; echo "exit code $?"',
    "live": heredoc(PY_LIVE, prefix='TOKEN="$(tok "$API")" OUTSIDER="$(otok)" '),
    "pairs": heredoc(PY_PAIRS) + "\npython evals/cache_threshold.py --selftest",
    "candidate": heredoc(PY_CANDIDATE),
    "feed": ("N=$(bq --project_id=\"$PROJECT\" query --nouse_legacy_sql --format=csv \\\n"
             "  \"SELECT COUNT(*) FROM \\`$PROJECT.rag_data.index_feed\\` WHERE tenant_id = 'acme'\" | tail -1)\n"
             "echo \"feed rows for acme: $N\"\n"
             "if [ \"${N:-0}\" -gt 0 ] 2>/dev/null; then make make-evalset PROJECT=\"$PROJECT\" TENANT=acme ROWS=10 && wc -l evals/golden_generated.jsonl\n"
             "else echo \"no feed rows yet: lesson 11.5 builds the feed (make features)\"; fi"),
    "patch": (f"F=\"{FILES}\"\n"
              "git diff --stat -- $F\n"
              "git diff --quiet -- $F || { git diff -- $F > \"$HOME/lesson71_rows.patch\" && git checkout -- $F; }   # a second run keeps the patch\n"
              "git diff --quiet -- $F && echo \"the four files match the kit again\"\n"
              "wc -l < evals/golden.jsonl; grep -c '^+[^+]' \"$HOME/lesson71_rows.patch\""),
}

# ------------------------------------------------------------------ run them on a scratch copy of the kit
T = Path(tempfile.mkdtemp(prefix="lesson71-"))
E = T / "evals"
E.mkdir()
for name in ("build_golden.py", "run_eval.py", "cache_threshold.py", "golden.jsonl", "required.json", "paraphrases.jsonl", "manifest.json"):
    shutil.copy2(KIT / "evals" / name, E / name)
for sub in ("corpus", "demo"):
    for p in (KIT / "evals" / sub).rglob("*"):
        if p.is_file() and p.suffix in (".md", ".txt"):
            dest = E / p.relative_to(KIT / "evals")
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
git = ["git", "-C", str(T), "-c", "core.autocrlf=false", "-c", "user.name=lesson", "-c", "user.email=lesson@example.invalid"]
subprocess.run(git + ["init", "-q"], check=True)
subprocess.run(git + ["add", "-A"], check=True)
subprocess.run(git + ["commit", "-qm", "the kit as published"], check=True)
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}


def lane(text: str) -> str:
    return text.replace(str(T) + os.sep + "evals" + os.sep, LANE + "/evals/").replace(str(T), LANE)


def py(args: list, stdin: str | None = None) -> tuple[str, int]:
    r = subprocess.run([sys.executable] + args, input=stdin, cwd=str(T), capture_output=True, text=True, encoding="utf-8", env=ENV)
    assert not r.stderr.strip(), r.stderr[-800:]
    return lane(r.stdout), r.returncode


def heredoc_body(cell: str, n: int = 0) -> str:
    return re.findall(r"python - <<'PY'\n(.*?)\nPY", cell, re.S)[n]


def run_heredoc(cell: str, n: int = 0) -> str:
    out, rc = py(["-"], heredoc_body(cell, n))
    assert rc == 0, out
    return out


def gate_line() -> str:
    out, rc = py(["evals/run_eval.py"])
    return out + f"exit code {rc}\n", rc


def build_head() -> str:
    out, rc = py(["evals/build_golden.py"])
    assert rc == 0, out
    lines = out.rstrip("\n").split("\n")
    return "\n".join(lines[:5] + [lines[-1]]) + "\n"


OUT = {}
# step 3: make eval, the scoped listing, the clause table
out, rc = py(["evals/run_eval.py"])
assert rc == 0
OUT["gate0"] = "python evals/run_eval.py\n" + out
listing, rc = py(["evals/run_eval.py", "--source", "hr_policy_2026.md"])
OUT["gate0"] += listing[listing.index("  rows citing"):]
OUT["clauses"] = run_heredoc(CELLS["clauses"])
# step 4: the lookup row, built and gated; the variants
OUT["lk32"] = run_heredoc(CELLS["lk32"]) + build_head()
g, rc = gate_line()
assert rc == 0, g
OUT["lk32"] += g
OUT["variants"] = run_heredoc(CELLS["variants"])
# step 5: the isolation row's three tries
OUT["iso_try"] = run_heredoc(CELLS["iso_try"])
out, rc = py(["evals/build_golden.py"])
assert rc == 1, out
OUT["iso_try"] += out + f"exit code {rc}\n" + f"{len((E / 'golden.jsonl').read_text(encoding='utf-8').splitlines())}\n"
OUT["iso_marker"] = run_heredoc(CELLS["iso_marker"]) + build_head()
g, rc = gate_line()
assert rc == 1 and "[FAIL] coverage" in g, g
OUT["iso_marker"] += g
req_before = (KIT / "evals" / "required.json").read_text(encoding="utf-8")
assert json.dumps(json.loads(req_before), indent=1) == req_before, "required.json round-trips through json.dumps(indent=1)"
OUT["iso_required"] = run_heredoc(CELLS["iso_required"])
out, rc = py(["evals/run_eval.py"])
assert rc == 0, out
OUT["iso_required"] += "python evals/run_eval.py\n" + out + "exit code 0\n"
# step 7: the pairs and the self-test; the candidate
OUT["pairs"] = run_heredoc(CELLS["pairs"])
out, rc = py(["evals/cache_threshold.py", "--selftest"])
assert rc == 0, out
OUT["pairs"] += out
OUT["candidate"] = run_heredoc(CELLS["candidate"])
# step 8: the diff kept as a patch, the files given back
FINAL_ROWS = {r["id"]: r for r in (json.loads(line) for line in (E / "golden.jsonl").read_text(encoding="utf-8").splitlines())
              if r["id"] in ("lk-32", "iso-11")}
assert len(FINAL_ROWS) == 2 and FINAL_ROWS["iso-11"]["must_not_contain"] == ["capped at 45 days"], FINAL_ROWS
g = lambda *a: subprocess.run(git + list(a), capture_output=True, text=True, encoding="utf-8", check=True).stdout  # noqa: E731
stat = g("diff", "--stat", "--", *FILES.split())
patch = g("diff", "--", *FILES.split())
added = sum(1 for line in patch.splitlines() if re.match(r"^\+[^+]", line))
g("checkout", "--", *FILES.split())
clean = subprocess.run(git + ["diff", "--quiet", "--", *FILES.split()]).returncode == 0
rows_after = len((E / "golden.jsonl").read_text(encoding="utf-8").splitlines())
assert clean and rows_after == len(golden) and added == 7, (clean, rows_after, added)
OUT["patch"] = stat + "the four files match the kit again\n" + f"{rows_after}\n{added}\n"
shutil.rmtree(T, ignore_errors=True)

if os.environ.get("CELLS_ONLY"):                  # CELLS_ONLY=1 python build.py: the captured outputs, nothing written
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    sys.exit(0)

# the two expected blocks no build can capture: they need the lane
LIVE_OUT = """lk-32 as acme: HTTP 200, answerable True, 1 citation(s), 2410 ms
   An account unused for 45 days is disabled automatically and must be re-approved to restore it [1].
   must_contain '45 days': found
   cites acme/hr_policy_2026.md
iso-11 as zeta: HTTP 200, answerable True, 1 citation(s), 2230 ms
   Earned leave is encashed on exit at basic pay, capped at 20 days [1].
   must_contain '20 days': found
   must_not_contain 'capped at 45 days': absent
   cites zeta/hr_policy_zeta_2026.md
iso-11 asked by documind-outsider-sa: HTTP 403 (the isolation gate requires 403)
"""
FEED_EMPTY = "feed rows for acme: 0\nno feed rows yet: lesson 11.5 builds the feed (make features)\n"
FEED_FULL = ("feed rows for acme: COUNT\n"
             "python evals/make_evalset.py --project documind-ai-YOUR-ID --tenant acme --rows ${ROWS:-200}\n"
             "  10 feed chunks -> 10 pairs -> 10 kept, 0 dropped by the PII scan\n"
             f"  wrote {LANE}/evals/golden_generated.jsonl  (candidates; run_eval.py reads golden.jsonl only)\n"
             "10 evals/golden_generated.jsonl\n")
assert "must_contain '45 days': found" in LIVE_OUT
me_src = (KIT / ME).read_text(encoding="utf-8")
assert 'print(f"  wrote {OUT}  (candidates; run_eval.py reads golden.jsonl only)")' in me_src and "dropped by the PII scan" in me_src


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "gate0": "run in the operator shell, in the kit (the offline gate, then the rows that cite the handbook)",
    "clauses": "run in the operator shell, in the kit (reads the handbook and golden.jsonl; changes nothing)",
    "lk32": "run in the operator shell, in the kit (one line into evals/build_golden.py, then the build and the gate)",
    "variants": "run in the operator shell, in the kit (six versions of the row, judged in memory; writes nothing)",
    "iso_try": "run in the operator shell, in the kit (the isolation row, with the obvious marker)",
    "iso_marker": "run in the operator shell, in the kit (the same row with ACME's phrase as the marker, then the build and the gate)",
    "iso_required": "run in the operator shell, in the kit (iso-11 listed in evals/required.json, then make eval)",
    "live": "run in the operator shell, in the kit (three requests to the API; under a rupee)",
    "pairs": "run in the operator shell, in the kit (two lines appended to evals/paraphrases.jsonl, then the offline self-test)",
    "candidate": "run in the operator shell, in the kit (a candidate for SEC-09 as make-evalset writes one, judged in memory)",
    "feed": "run in the operator shell, in the kit (one BigQuery count; ten Gemini calls only if the feed has rows)",
    "patch": "run in the operator shell, in the kit (your rows kept as a patch, the four files given back)",
}
OUT_LABELS = {
    "gate0": "(the gate's own output, captured when this page was built)",
    "clauses": "(captured when this page was built)",
    "lk32": "(captured when this page was built; your path is your home directory)",
    "variants": "(captured when this page was built)",
    "iso_try": "(captured when this page was built: the writer refuses, and golden.jsonl keeps its 66 lines)",
    "iso_marker": "(captured when this page was built: written, then refused by the coverage rule)",
    "iso_required": "(captured when this page was built)",
    "live": "(your wording, citation count and times differ; the verdict lines are what to check)",
    "pairs": "(captured when this page was built)",
    "candidate": "(captured when this page was built; the hash is the handbook's own, the same on every lane)",
    "feed_empty": "before lesson 11.5 fills the feed",
    "feed_full": "on a lane whose feed has rows (COUNT is your lane's)",
    "patch": "(captured when this page was built)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})
WIN["OUT_LIVE"] = out_window(OUT_LABELS["live"], LIVE_OUT)
WIN["OUT_FEED_EMPTY"] = out_window(OUT_LABELS["feed_empty"], FEED_EMPTY)
WIN["OUT_FEED_FULL"] = out_window(OUT_LABELS["feed_full"], FEED_FULL)
WIN["REQUIRED_JSON"] = ('<div class="cw"><div class="ch-bar"><span>evals/required.json - the ids that must exist, and must pass one by one</span>'
                        '<span class="ro">read only</span></div><pre tabindex="0">'
                        + html.escape((KIT / "evals" / "required.json").read_text(encoding="utf-8"), quote=False) + "</pre></div>\n")


# ------------------------------------------------------------------ the row scorer: rows, the gate's evidence, presets
def snip(hay: str, i: int, n: int, pad: int = 24) -> str:
    a, b = max(0, i - pad), min(len(hay), i + n + pad)
    return ("..." if a else "") + " ".join(hay[a:b].split()) + ("..." if b < len(hay) else "")


def first_hit(tenant: str, phrase: str):
    for name, text in corpus.get(tenant, {}).items():
        hay = name + "\n" + text
        i = hay.lower().find(phrase.lower())
        if i >= 0:
            return name, snip(hay, i, len(phrase))
    return None


DEMO = {p.name: p.read_text(encoding="utf-8") for p in sorted((KIT / "evals" / "demo").glob("*.md"))}


def evidence(row: dict, variant: bool) -> list:
    """[ok, text, snippet] for each assertion: what the offline gate finds, by its own matching rule."""
    t, out = row["tenant"], []
    for w in row.get("must_contain", []):
        files = [n for n, x in corpus.get(t, {}).items() if w.lower() in (n + "\n" + x).lower()]
        own = [n for n in files if n.rsplit(".", 1)[0] in row.get("must_retrieve", [])] or files   # the anchored document first
        if not own:
            out.append([0, f"must_contain '{w}' is in none of {t}'s files", ""])
            continue
        hay = own[0] + "\n" + corpus[t][own[0]]
        more = f", and in {len(files) - 1} other {t} file{'s' if len(files) > 2 else ''}" if len(files) > 1 else ""
        out.append([1, f"must_contain '{w}' is in {t}/{own[0]}{more}", snip(hay, hay.lower().find(w.lower()), len(w))])
    for w in row.get("must_not_contain", []):
        if row["shape"] == "version":
            cur = corpus.get(t, {}).get(row.get("source", ""), "")
            inside = w.lower() in cur.lower()
            out.append([0 if inside else 1, f"'{w}' is {'IN' if inside else 'not in'} the current {t}/{row.get('source')}", ""])
            hit = next(((n, snip(x, x.lower().find(w.lower()), len(w))) for n, x in DEMO.items() if w.lower() in x.lower()), None)
            out.append([1, f"'{w}' is in the retired evals/demo/{hit[0]}", hit[1]] if hit else [0, f"'{w}' is in no retired version", ""])
            continue
        own = first_hit(t, w)
        out.append([0, f"must_not_contain '{w}' is in {t}'s OWN {own[0]}", own[1]] if own else [1, f"must_not_contain '{w}' is in none of {t}'s files", ""])
        others = [(o, first_hit(o, w)) for o in corpus if o != t]
        others = [(o, h) for o, h in others if h]
        out += [[1, f"and it is in {o}/{h[0]}", h[1]] for o, h in others[:1]] or [[0, "and it is in no other tenant's files", ""]]
    for a in row.get("must_retrieve", []):
        hit = first_hit(t, a)
        out.append([1, f"anchor '{a}' is in {t}/{hit[0]}", ""] if hit else [0, f"anchor '{a}' matches nothing in {t}'s files", ""])
    if not (row.get("must_contain") or row.get("must_not_contain") or row.get("must_retrieve")):
        out.append([1, "a refusal row gives the offline gate nothing to check: no figure, no marker, no anchor", ""])
    if rv.mandatory(row) and not variant:
        late = row["id"] == "iso-11"
        out.append([1, f"{row['id']} is listed in required.json" + (", once step 5 adds it" if late else ""), ""])
    return out


KEYS = ("id", "shape", "question", "tenant", "must_contain", "must_retrieve", "answerable", "must_not_contain", "must_cite_kind", "source")
SCORER = [
    # group, label, row, variant?, why, presets (label, answer, answered)
    ("lookup", "lk-06", GOLD["lk-06"], False,
     "A bare figure. Since 12 September it has to stand on its own: 60 is not in 160 days.",
     [("the right figure", "A confirmed E3 serves a notice period of 60 days [1].", 1),
      ("a number that contains it", "The notice period is 160 days [1].", 1),
      ("a refusal", "I could not find this in the documents.", 0)]),
    ("lookup", "lk-23", GOLD["lk-23"], False,
     "The third live eval answered 300 or more against a row that says three hundred. Number words become digits on both sides.",
     [("an answer with the 7 September figure", "The chapter applies to establishments with 300 or more workers [1].", 1)]),
    ("lookup", "lk-20", GOLD["lk-20"], False,
     "Anchored on the figure since the third live eval. The next entry is the same row as it was first written.",
     [("the 7 September wording", "Overtime is paid at twice the normal rate of wages [1].", 1)]),
    ("as first written", "lk-20, first written", {**GOLD["lk-20"], "must_contain": ["twice the rate of wages"]}, True,
     "Five words the model was hoped to use. It wrote six, with the right figure, and the row scored it wrong.",
     [("the 7 September wording", "Overtime is paid at twice the normal rate of wages [1].", 1)]),
    ("join", "jn-08", GOLD["jn-08"], False,
     "Two figures from two documents. twelve weeks and 12 weeks are the same fact.",
     [("both, in digits", "The 1961 Act fixed 12 weeks; the 2017 amendment made it 26 weeks [1][2].", 1),
      ("only the new figure", "The 2017 amendment set the maximum at 26 weeks [1].", 1)]),
    ("refusal", "rf-03", GOLD["rf-03"], False,
     "Globex holds an MSA and no HR policy. The right answer says so.",
     [("a refusal", "The documents for this tenant do not state a notice period.", 0),
      ("ACME's handbook, borrowed", "The notice period is 60 days [1].", 1)]),
    ("as first written", "rf-07, first written", {**GOLD["rf-07"], "question": "What GST rate applies to DocuMind's document processing services?"}, True,
     "The invoice says GST @ 18%. The first live eval answered correctly, and the row was wrong.",
     [("the first live eval's answer", "The invoice charges GST at 18% on document processing [1].", 1)]),
    ("isolation", "iso-01", GOLD["iso-01"], False,
     "The same question, another tenant. Zeta's cap must be there and ACME's must not.",
     [("Zeta's own cap", "The per-trip cap is Rs 25,000 [1].", 1),
      ("ACME's cap, leaked", "The per-trip cap is Rs 40,000 [1].", 1)]),
    ("isolation", "iso-07", GOLD["iso-07"], False,
     "The marker is the Act's phrase: a bare fifteen days is in Globex's own IT Act, as a filing deadline.",
     [("a refusal", "Nothing in this tenant's documents covers gratuity.", 0),
      ("a leak, in digits", "Gratuity is paid at 15 days' wages for each completed year [1].", 1)]),
    ("version", "vr-01", GOLD["vr-01"], False,
     "The current handbook says 60. Its retired revision under evals/demo says 90, and 90 must never come back.",
     [("the current figure", "A confirmed E3 serves 60 days of notice [1].", 1),
      ("the retired figure", "A confirmed E3 serves 90 days of notice [1].", 1)]),
    ("this lesson's rows", "lk-32", FINAL_ROWS["lk-32"], False,
     "The row step 4 writes into build_golden.py.",
     [("the clause's figure", "An account unused for 45 days is disabled automatically [1].", 1),
      ("the clause's other fact", "Production access is reviewed quarterly [1].", 1)]),
    ("this lesson's rows", "iso-11, first try", {**FINAL_ROWS["iso-11"], "must_not_contain": ["45 days"]}, True,
     "Step 5's first try. A correct Zeta answer that also mentions SEC-09 would fail it.",
     [("a correct answer that mentions SEC-09", "Encashment is capped at 20 days [1]. Separately, an account unused for 45 days is disabled [2].", 1)]),
    ("this lesson's rows", "iso-11", FINAL_ROWS["iso-11"], False,
     "The row step 5 ends with. A marker is a phrase, so a leak in other words gets past it, and must_contain catches it.",
     [("Zeta's own cap", "Earned leave is encashed on exit at basic pay, capped at 20 days [1].", 1),
      ("ACME's cap, in ACME's words", "Earned leave is encashed on exit, capped at 45 days [1].", 1),
      ("ACME's cap, in other words", "You can encash up to 45 days of earned leave [1].", 1)]),
]
SCORE_ROWS = []
for group, label, row, variant, why, presets in SCORER:
    shown = {k: row[k] for k in KEYS if k in row}
    SCORE_ROWS.append({"g": group, "l": label, "r": shown, "w": why, "ev": evidence(row, variant),
                       "pr": rv.check_falsifiable([row], corpus) + rv.check_anchors([row], corpus), "p": [list(p) for p in presets]})
assert [e["l"] for e in SCORE_ROWS if e["pr"]] == ["iso-11, first try"], [e["l"] for e in SCORE_ROWS if e["pr"]]

# the kit's own verdict for every preset: run_eval.live() on the one row, the API replaced by the preset's reply
import contextlib  # noqa: E402
import io  # noqa: E402

rv.load_corpus = lambda: corpus
rv.fetch_current_shas = lambda *a, **k: None
REP = Path(tempfile.mkdtemp(prefix="lesson71-live-")) / "report.json"


def kit_verdict(row: dict, answer: str, answered: int) -> tuple:
    def fake_ask(api_url, question, tenant, email, token, retries=1):
        cites = [{"chunk_id": f"{tenant}:lesson#0", "source_uri": f"gs://lesson/{tenant}/doc.md", "quote": "q",
                  "kind": row.get("must_cite_kind", "text")}] if answered else []
        return 200, {"answer": answer, "citations": cites, "answerable": bool(answered), "confidence": "high"}, 1
    rv.ask = fake_ask
    with contextlib.redirect_stdout(io.StringIO()):
        rv.live("http://lesson.invalid", golden=[row], report=str(REP))
    rec = json.loads(REP.read_text(encoding="utf-8"))["records"][0]
    return rec["pass"], rec["why"]


KIT_VERDICTS = [[kit_verdict(e["r"], p[1], p[2]) for p in e["p"]] for e in SCORE_ROWS]
shutil.rmtree(REP.parent, ignore_errors=True)

PORT_JS = r"""var SMALL = {zero:0,one:1,two:2,three:3,four:4,five:5,six:6,seven:7,eight:8,nine:9,ten:10,eleven:11,twelve:12,thirteen:13,fourteen:14,fifteen:15,sixteen:16,seventeen:17,eighteen:18,nineteen:19,twenty:20,thirty:30,forty:40,fifty:50,sixty:60,seventy:70,eighty:80,ninety:90};
  var SCALE = {hundred:100,thousand:1000,lakh:100000,crore:10000000};
  var W = '[\\p{L}\\p{N}_]', WORD = Object.keys(SMALL).concat(Object.keys(SCALE)).join('|');
  var NUMWORDS = new RegExp('(?<!' + W + ')(?:(?:' + WORD + ')(?:[\\s-]+(?:' + WORD + '))*)(?!' + W + ')', 'gu');
  var has = function(o, k){ return Object.prototype.hasOwnProperty.call(o, k); };
  function toInt(run){ var total = 0, current = 0;                                   /* run_eval._to_int() */
    run.split(/[\s-]+/).forEach(function(w){ if (has(SMALL, w)) current += SMALL[w]; else if (w === 'hundred') current = (current || 1) * 100;
      else if (has(SCALE, w)) { total += (current || 1) * SCALE[w]; current = 0; } });
    return total + current; }
  function normalise(text){ var t = String(text).toLowerCase().split(',').join('').split('-').join(' ');   /* run_eval.normalise() */
    [' per cent', 'per cent', ' percent', 'percent'].forEach(function(s){ t = t.split(s).join('%'); });
    return t.replace(NUMWORDS, function(m){ return String(toInt(m)); }); }
  function contains(text, want){ var w = normalise(want).trim(); if (!w) return false;          /* run_eval.contains() */
    return new RegExp('(?<![\\p{L}\\p{N}_.])' + w.replace(/[.*+?^${}()|[\]\\\/]/g, '\\$&') + '(?!' + W + '|\\.\\d)', 'u').test(normalise(text)); }
  function pyrepr(s){ return (s.indexOf("'") >= 0 && s.indexOf('"') < 0) ? '"' + s + '"' : "'" + s.replace(/\\/g, '\\\\').replace(/'/g, "\\'") + "'"; }
  function score(row, answer, answered){                                              /* the per-row judgment in run_eval.live() */
    var checks = [], reasons = [], leaked = false, pass;
    (row.must_not_contain || []).forEach(function(n){ var hit = contains(answer, n); checks.push(['must_not_contain', n, hit]);
      if (hit) { leaked = true; reasons.push((row.shape === 'version' ? 'stale: ' : 'leak: ') + 'answer contained ' + pyrepr(n)); } });
    if (row.answerable) {
      if (answered) { var missing = (row.must_contain || []).filter(function(w){ var hit = contains(answer, w); checks.push(['must_contain', w, hit]); return !hit; });
        if (missing.length) reasons.push('answered without [' + row.must_contain.map(pyrepr).join(', ') + ']');
        pass = !missing.length && !leaked; }
      else { reasons.push('refused'); pass = false; }
    } else if (!answered) { pass = !leaked; } else { reasons.push('answered, should refuse'); pass = false; }
    return {pass: pass, checks: checks, reasons: reasons}; }"""

# node: the port against the kit, figure by figure and verdict by verdict
probes = [(p[1], w) for e in SCORE_ROWS for p in e["p"] for w in e["r"].get("must_contain", []) + e["r"].get("must_not_contain", [])]
probes += [("The notice period is 160 days", "60"), ("3600 rupees", "60"), ("8.33%", "8.33"), ("18.33%", "8.33"), ("twelve weeks", "12 weeks"),
           ("twenty-six weeks", "26 weeks"), ("Rs 1,84,500 payable", "1,84,500"), ("5.2 per cent", "5.2%"), ("set-on and set-off", "set on"),
           ("three hundred workers", "300"), ("one lakh twenty thousand", "120000"), ("twice the normal rate of wages", "twice the rate of wages"),
           ("fifteen days' wages", "15 days' wages"), ("it is 60.", "60"), ("60.5 days", "60"), ("E3", "3"), ("forty-five days", "45 days")]
test_js = ("'use strict';\n" + PORT_JS + "\nvar probes = " + json.dumps(probes) + ";\nvar rows = " + json.dumps(SCORE_ROWS) + ";\n"
           "console.log(JSON.stringify({c: probes.map(function(p){ return contains(p[0], p[1]); }),"
           " v: rows.map(function(e){ return e.p.map(function(p){ var s = score(e.r, p[1], p[2]); return [s.pass, s.reasons]; }); })}));\n")
tjs = Path(tempfile.mkdtemp(prefix="lesson71-js-")) / "port.js"
tjs.write_text(test_js, encoding="utf-8")
node = subprocess.run(["node", str(tjs)], capture_output=True, text=True, encoding="utf-8")
shutil.rmtree(tjs.parent, ignore_errors=True)
assert node.returncode == 0, node.stderr[-800:]
jsr = json.loads(node.stdout)
for (text, want), got in zip(probes, jsr["c"]):
    assert got == rv.contains(text, want), (text, want, got)
for e, kit_row, js_row in zip(SCORE_ROWS, KIT_VERDICTS, jsr["v"]):
    for p, (kpass, kwhy), (jpass, jreasons) in zip(e["p"], kit_row, js_row):
        assert kpass == jpass and (kpass or any(r.endswith(kwhy) for r in jreasons)), (e["l"], p[0], kpass, kwhy, jpass, jreasons)
N_PRESETS = sum(len(e["p"]) for e in SCORE_ROWS)

UI_JS = r"""var root = document.getElementById('scorer'); if (!root) return;
  var $ = function(id){ return document.getElementById(id); };
  var sel = $('rs-row'), js = $('rs-json'), why = $('rs-why'), off = $('rs-off'), chips = $('rs-chips'), ans = $('rs-ans'), said = $('rs-said'), out = $('rs-out');
  function esc(t){ return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  var groups = {}, order = [];
  D.forEach(function(e, i){ if (!groups[e.g]) { groups[e.g] = []; order.push(e.g); } groups[e.g].push(i); });
  sel.innerHTML = order.map(function(g){ return '<optgroup label="' + esc(g) + '">' + groups[g].map(function(i){
    return '<option value="' + i + '">' + esc(D[i].l) + ' &middot; ' + esc(D[i].r.question) + '</option>'; }).join('') + '</optgroup>'; }).join('');
  function val(v){ return Array.isArray(v) ? '[' + v.map(function(x){ return JSON.stringify(x); }).join(', ') + ']' : JSON.stringify(v); }
  function tick(ok){ return '<span class="' + (ok ? 'rs-ok">&#10003;' : 'rs-no">&#10007;') + '</span> '; }
  function run(){
    var e = D[+sel.value], v = score(e.r, ans.value, said.checked);
    out.innerHTML = '<span class="rs-verdict ' + (v.pass ? 'pass">PASS' : 'fail">FAIL') + '</span>'
      + (v.reasons.length ? '<ul>' + v.reasons.map(function(x){ return '<li>' + esc(x) + '</li>'; }).join('') + '</ul>' : '')
      + '<ul>' + v.checks.map(function(c){ var good = c[0] === 'must_contain' ? c[2] : !c[2];
          return '<li>' + tick(good) + c[0] + ' <code>' + esc(c[1]) + '</code>, normalised <code>' + esc(normalise(c[1]).trim()) + '</code>: '
            + (c[2] ? 'found' : 'not found') + (c[0] === 'must_not_contain' && c[2] ? ', a leak' : '') + '</li>'; }).join('')
      + (said.checked && e.r.answerable ? '<li>citation: assumed valid (the live half checks tenant, document and version)</li>' : '') + '</ul>'
      + '<span class="rs-snip">the answer, normalised: ' + esc(normalise(ans.value)) + '</span>';
  }
  function load(j){ var p = D[+sel.value].p[j]; if (!p) return; ans.value = p[1]; said.checked = !!p[2]; run(); }
  function show(){
    var e = D[+sel.value], r = e.r;
    js.textContent = '{\n' + Object.keys(r).map(function(k){ return '  "' + k + '": ' + val(r[k]); }).join(',\n') + '\n}';
    why.textContent = e.w;
    off.innerHTML = '<b class="h">Offline: the gate ' + (e.pr.length ? '<span class="rs-no">refuses</span>' : '<span class="rs-ok">accepts</span>') + ' this row</b><ul>'
      + e.ev.map(function(x){ return '<li>' + tick(x[0]) + esc(x[1]) + (x[2] ? '<span class="rs-snip">' + esc(x[2]) + '</span>' : '') + '</li>'; }).join('')
      + e.pr.map(function(x){ return '<li class="rs-no">' + esc(x) + '</li>'; }).join('') + '</ul>';
    chips.innerHTML = e.p.map(function(p, j){ return '<button type="button" data-j="' + j + '">' + esc(p[0]) + '</button>'; }).join('');
    load(0);
  }
  chips.addEventListener('click', function(ev){ var b = ev.target.closest('button'); if (b) load(+b.getAttribute('data-j')); });
  sel.addEventListener('change', show); ans.addEventListener('input', run); said.addEventListener('change', run);
  show();"""

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = ("<script>\n(function(){\n'use strict';\nvar D = " + json.dumps(SCORE_ROWS, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + ";\n"
      + squeeze(PORT_JS) + "\n" + squeeze(UI_JS) + "\n})();\n</script>\n")

# ------------------------------------------------------------------ numbers for the prose
cost_txt = (KIT / "services" / "rag-api" / "cost.py").read_text(encoding="utf-8")
RATE_IN, RATE_OUT = (float(x) for x in re.search(r'"gemini-3.6-flash": \(([\d.]+), ([\d.]+)\)', cost_txt).groups())
USD_INR = float(re.search(r'USD_INR = float\(os.environ.get\("USD_INR_RATE", "([\d.]+)"\)\)', cost_txt).group(1))
per_row = (420 * RATE_IN + 100 * RATE_OUT) / 1e6 * USD_INR           # a chunk of up to 1,500 characters and the instruction in; the pair out
CACHE_T = re.search(r'THRESHOLD = float\(os.environ.get\("SEMANTIC_CACHE_THRESHOLD", "([\d.]+)"\)\)',
                    (KIT / "services" / "rag-api" / "semantic_cache.py").read_text(encoding="utf-8")).group(1)
heads = re.findall(r"(?m)^## (\S+) \S (.+)$", handbook)
STATS = {
    "N_ROWS": str(len(golden)), "N_TENANTS": str(len(corpus)), "N_DOCS": str(N_DOCS), "N_REQ": str(len(required)),
    "N_LOOKUP": str(shapes["lookup"]), "N_JOIN": str(shapes["join"]), "N_REFUSAL": str(shapes["refusal"]),
    "N_ISO": str(shapes["isolation"]), "N_VERSION": str(shapes["version"]),
    "N_ANSWERABLE": str(sum(r["answerable"] for r in golden)), "N_UNANSWERABLE": str(sum(not r["answerable"] for r in golden)),
    "MIN_ISO": str(rv.MIN_ROWS["isolation"]), "MIN_REFUSAL": str(rv.MIN_ROWS["refusal"]), "MIN_LOOKUP": str(rv.MIN_ROWS["lookup"]),
    "MIN_JOIN": str(rv.MIN_ROWS["join"]), "MIN_VERSION": str(rv.MIN_ROWS["version"]), "N_THRESHOLDS": str(len(rv.THRESHOLDS)),
    "N_PAIRS": str(len(pairs)), "N_SAME": str(sum(p["same"] for p in pairs)), "N_DIFF": str(sum(not p["same"] for p in pairs)),
    "N_SECTIONS": str(len(heads)), "N_FILLER": str(sum(c.startswith("GEN-") for c, _ in heads)), "N_REAL": str(sum(not c.startswith("GEN-") for c, _ in heads)),
    "SEC09_I": str(SEC09_I), "CACHE_T": CACHE_T, "N_SCORER": str(len(SCORE_ROWS)), "N_PRESETS": str(N_PRESETS),
    "RATE_IN": f"{RATE_IN:.2f}", "RATE_OUT": f"{RATE_OUT:.2f}", "USD_INR": f"{USD_INR:g}",
    "EVALSET_10": f"{10 * per_row:.1f}", "EVALSET_200": f"{200 * per_row:.0f}",
    "N_ROWS_1": str(len(golden) + 1), "N_ROWS_2": str(len(golden) + 2), "N_REQ_1": str(len(required) + 1), "N_PAIRS_2": str(len(pairs) + 2),
    "N_EMBED": str(len({p["of"] for p in pairs} | {"lk-32"}) + len(pairs) + 2),   # cache_threshold.py embeds each golden question once, then every pair
    "N_ACME_FILES": str(len(corpus["acme"])),
    "N_60": str(sum("60" in (n + "\n" + x).lower() for n, x in corpus["acme"].items())),
    "N_45": str(sum("45 days" in (n + "\n" + x).lower() for n, x in corpus["acme"].items())),
}
assert STATS["N_45"] == "1" and int(STATS["N_60"]) > 5, (STATS["N_45"], STATS["N_60"])
assert f"{len(pairs) + 2} pairs" in OUT["pairs"] and f"wrote {len(golden) + 1} rows" in OUT["lk32"] and f"{len(required) + 1} required ids" in OUT["iso_required"]
assert STATS["N_SECTIONS"] == "282" and STATS["N_REAL"] == "10" and STATS["N_REQ"] == "15"


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([
    subst(fill(pb.part(LESSON, "a"))),
    setup,
    subst(fill(pb.part(LESSON, "b"))),
    subst(fill(pb.part(LESSON, "c"))),
])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: {len(golden)} rows ({', '.join(f'{k} {v}' for k, v in sorted(shapes.items()))}) over {len(corpus)} tenants, {N_DOCS} documents"
      f" | required {len(required)} | pairs {len(pairs)} | SEC-09 is chunk {SEC09_I} | cells {len(CELLS)} run | scorer {len(SCORE_ROWS)} rows,"
      f" {N_PRESETS} presets, verdicts equal to run_eval.live() | {len(probes)} contains() probes equal in node")

