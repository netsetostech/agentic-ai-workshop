"""Build lesson 2.5 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Computed from the kit when the page is built:
  - the stage's switch and constants (config.py, shared/query_rewrite.py), the golden set's and the paraphrases' counts,
    the rows whose question carries a literal, and the 8 September baseline from evals/ablate.py's docstring;
  - the bench's guard: shared/query_rewrite.py's normalise(), literals(), dropped() and rewrite()'s outcome rule in
    JavaScript, run in node over every golden and paraphrase question and the cases below and held equal to the kit;
  - the bench's ranks: lesson 2.2's BM25 port over acme's corpus as the kit's chunker cuts it, for each row's question
    and for the text the stage would search;
  - the outputs of the offline cells, run here on the kit (on a copy, for the cell that edits a kit file);
  - the rupee lines, from shared/prices.py and the row counts.
Live: every output a lane prints is pb.recorded() from the author's run; RUN_LIST.md says which command records which
file. Until data/rewrites.txt is recorded, the bench's rewrites are illustrations written for this page, and say so.
"""
import ast
import html
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, MANIFEST, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "2.5"
title = ("<title>Lesson 2.5 Rewrite the query before retrieval, and measure it - the question in the documents' words for the "
         "search, the person's own words for the ranker and the model, and a guard that keeps every code and figure | Netsetos</title>\n")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.wr-list{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:6px;}
.wr-row{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;font-size:12.5px;line-height:1.5;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.wr-row.wr-stage{border-color:var(--cyan);background:#ecfeff;}
.rb-tag{display:inline-block;font-family:var(--mono);font-size:var(--kicker-size);font-weight:700;letter-spacing:.6px;border-radius:5px;padding:1px 6px;margin:0 4px 2px 0;background:var(--teal-light);color:var(--teal-dark);}
.rb-tag.s{background:#cffafe;color:#0e7490;}
.rb-tag.no{background:#fef2f2;color:#991b1b;}
.rb-tag.warn{background:#fffbeb;color:#92400e;}
.rb-l{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;margin:10px 0 6px;}
.rb-l select,.rb-l textarea{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.rb-l textarea{font-family:var(--mono);line-height:1.35;resize:vertical;}
.rb-out{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:10px 12px;font-size:var(--small-size);line-height:1.55;min-width:0;overflow-wrap:anywhere;}
.rb-out p{margin:0 0 6px;font-size:var(--small-size);}
.rb-ranks{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px;margin-top:6px;}
.rb-ranks div{border:1px solid var(--border);border-radius:8px;padding:6px 8px;min-width:0;}
.rb-ranks ol{margin:4px 0 0;padding-left:20px;font-size:12.5px;}
.rb-ranks li span{color:var(--slate-light);font-family:var(--mono);font-size:var(--kicker-size);}
.rb-ranks li.hit{color:var(--navy);font-weight:600;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
QR = "shared/query_rewrite.py"
RW = "services/rag-api/rewrite.py"
API = "services/rag-api/main.py"
CFG = "services/rag-api/config.py"
ABL = "evals/ablate.py"
DEP = "commands/lesson-12.2.sh"
UI = "services/frontend/chat.py"
RULE_START = '        "- Copy every code, grade, section, number, amount, date and unit exactly as written'

EXCERPTS = {
    "qr_call": ("shared/query_rewrite.py - the call's settings, the four outcomes, and the request google-genai receives",
                block(QR, 'MODEL = "gemini-3.1-flash-lite"', end="_FENCE = re.compile") + "\n...\n"
                + block(QR, "def config(", end="# ---------------------------------------------------------------- the literal guard")),
    "qr_prompt": ("shared/query_rewrite.py - prompt(): what the index holds, six rules, and the question fenced as data",
                  block(QR, "def prompt(question: str) -> str:", end="def config(")),
    "qr_rule": ("shared/query_rewrite.py - the rule step 8 deletes", block(QR, RULE_START, n=2)),
    "qr_guard": ("shared/query_rewrite.py - the guard: normalise(), literals(), _present(), dropped(), keeps_literals()",
                 block(QR, "_DASHES = dict.fromkeys", end="def _fenced(") + "\n...\n"
                 + block(QR, "def normalise(", end="# ---------------------------------------------------------------- one call")),
    "qr_rewrite": ("shared/query_rewrite.py - rewrite(): one call, one outcome, never an exception",
                   block(QR, "def parse(obj)", end="def row(")),
    "qr_row": ("shared/query_rewrite.py - row(): the query_rewrite line, with no question text", block(QR, "def row(")),
    "rw_search": ("services/rag-api/rewrite.py - search_query(): off is no stage at all; on, what retrieve() searches",
                  block(RW, "def search_query(")),
    "api_import": ("services/rag-api/main.py - the import, between _guard() and screen_prompt()", block(API, "from rewrite import search_query", n=1)),
    "api_retrieve": ("services/rag-api/main.py - /v1/query's retrieve stage: one vector for the question, the cache lookup, then the one call line",
                     block(API, '    with stage(stages, "retrieve"):', n=5)),
    "api_unchanged": ("services/rag-api/main.py - /v1/query's rerank and generate stages: req.query, as before the stage existed",
                      block(API, '        with stage(stages, "rerank"):', n=6)),
    "api_store": ("services/rag-api/main.py - the answer cache keeps the question's own vector", block(API, "    if not (hit or reason):", n=2)),
    "cfg_switch": ("services/rag-api/config.py - QUERY_REWRITE and QUERY_REWRITE_MODEL, and the validator that refuses a third value",
                   block(CFG, "    # Workshop lesson 2.5's rewrite stage", n=6) + "\n...\n"
                   + block(CFG, '    @field_validator("query_rewrite")', end="    @model_validator")),
    "ui_stream": ("services/frontend/chat.py - stream_answer(): the Chat page asks /v1/stream", block(UI, "def stream_answer(", end="def chat_page(")),
    "api_stream": ("services/rag-api/main.py - /v1/stream's retrieval: the question as asked, always",
                   block(API, "        chunks = [] if hit else retrieve(req.query, req.tenant_id, req.top_k, req.filters, vec=qvec, backend=rbackend)", n=1)),
    "make_candidate": ("Makefile - make candidate: --update-env-vars with its own list, QUERY_REWRITE not in it", block("Makefile", "candidate: guard-project", n=3)),
    "deploy_set": ("commands/lesson-12.2.sh - make deploy-services sets the API's whole environment, QUERY_REWRITE not in it",
                   block(DEP, '  --set-env-vars="^|^GOOGLE_CLOUD_PROJECT=', n=1)),
    "make_ablate": ("Makefile - the ablate target", block("Makefile", "ablate: guard-project", n=2)),
    "abl_flags": ("evals/ablate.py - the two flags", block(ABL, '    ap.add_argument("--rewrite"', n=5)),
    "abl_rows": ("evals/ablate.py - main(): the golden rows, the paraphrases added after them, --limit last",
                 block(ABL, '    rows = [r for r in golden if r.get("must_retrieve")', n=5)),
    "abl_arm": ("evals/ablate.py - rewrite_arm(): the rewrite searched, one kept call per question", block(ABL, "def rewrite_arm(", end="def rewrite_summary(")),
    "abl_paraphrases": ("evals/ablate.py - paraphrase_rows(): same:true rows only, on their originals' anchors",
                        block(ABL, "def paraphrase_rows(", end="def _share(")),
    "abl_split": ("evals/ablate.py - main(): the golden rows and the paraphrases apart, then the tally",
                  block(ABL, "        if any(para):", end="        for e in errors[:3]:")),
    "abl_summary": ("evals/ablate.py - rewrite_summary(): the tally line", block(ABL, "def rewrite_summary(", end="def paraphrase_rows(")),
    "abl_read": ("evals/ablate.py - how the harness tells you to read the rewrite row", block(ABL, "    if rw_arm:", n=3)),
    "abl_baseline": ("evals/ablate.py - the docstring's measurement of 8 September", block(ABL, "Measured on 8 Sept 2026 from Cloud Shell", n=3)),
}
fill = filler(EXCERPTS, window)

api_src = (KIT / API).read_text(encoding="utf-8")


def handler(name: str) -> str:
    """One handler's source, from its def to the next top-level def or decorator."""
    i = api_src.index(f"\ndef {name}(")
    j = min([k for k in (api_src.find("\ndef ", i + 1), api_src.find("\n@app.", i + 1)) if k > 0] + [len(api_src)])
    return api_src[i:j]


Q_SRC, S_SRC, P_SRC, V_SRC = handler("query"), handler("stream"), handler("passages"), handler("version")
# the rule the page teaches, held to the code: one call, after the cache lookup, the question everywhere else
assert Q_SRC.count("search_query(") == 1 and Q_SRC.index("_semantic_hit(") < Q_SRC.index("search_query(") < Q_SRC.index("retrieve(search_q")
assert "rerank(req.query, chunks" in Q_SRC and "generate(req.query, chunks" in Q_SRC and "_semantic_store(req, qvec, ans" in Q_SRC
assert all("search_query" not in src for src in (S_SRC, P_SRC, V_SRC)), "/v1/stream, /v1/passages and /version never rewrite"
assert EXCERPTS["api_retrieve"][1] in Q_SRC and "search_query(req.query, qvec, stages, req.tenant_id)" in EXCERPTS["api_retrieve"][1]
assert EXCERPTS["api_unchanged"][1] in Q_SRC and EXCERPTS["api_store"][1] in Q_SRC
assert EXCERPTS["api_stream"][1] in S_SRC and "retrieve(req.query" in EXCERPTS["api_stream"][1]
assert EXCERPTS["qr_rewrite"][1].rstrip().endswith("return out") and EXCERPTS["rw_search"][1].rstrip().endswith("return q, vec")
assert "/v1/stream" in EXCERPTS["ui_stream"][1] and "/v1/query" not in EXCERPTS["ui_stream"][1]
assert EXCERPTS["abl_split"][1].rstrip().endswith('line["rewrite"] = dict(rw_tally)'), EXCERPTS["abl_split"][1][-80:]
assert EXCERPTS["abl_read"][1].rstrip().endswith('what the calls cost.")')
DEPLOY_LINE, CAND_LINES = EXCERPTS["deploy_set"][1], EXCERPTS["make_candidate"][1]
assert "--set-env-vars" in DEPLOY_LINE and "QUERY_REWRITE" not in DEPLOY_LINE
assert "--update-env-vars" in CAND_LINES and "QUERY_REWRITE" not in CAND_LINES

# ------------------------------------------------------------------ the kit's facts the prose states
sys.path[:0] = [str(KIT), str(KIT / "evals"), str(KIT / "services" / "rag-api")]
from shared import documind_corpus as dc  # noqa: E402
from shared import prices  # noqa: E402
from shared import query_rewrite as qr  # noqa: E402
from context_budget import estimate_tokens  # noqa: E402
import ablate  # noqa: E402  - imports nothing from Google at the top

assert prices.PROFILE == "gcp", "the build prices at list price: unset DOCUMIND_PROFILE"
cfg = (KIT / CFG).read_text(encoding="utf-8")
grab = lambda pat, text: re.search(pat, text).group(1)  # noqa: E731
QR_DEFAULT = grab(r'query_rewrite: str = Field\("(\w+)", alias="QUERY_REWRITE"\)', cfg)
QR_MODEL_DEFAULT = grab(r'query_rewrite_model: str = Field\("([^"]+)", alias="QUERY_REWRITE_MODEL"\)', cfg)
MAX_CONTEXT = int(grab(r"max_context_tokens: int = (\d+)", cfg))
MAX_ANSWER = int(grab(r"max_answer_tokens: int = (\d+)", cfg))
GEN_MODEL = grab(r'generator_model: str = "([^"]+)"', cfg)
assert QR_DEFAULT == "off" and QR_MODEL_DEFAULT == qr.MODEL and qr.OUTCOMES == ("rewritten", "same", "rejected", "fallback")
RULES = [line for line in qr.prompt("QUESTION").splitlines() if line.startswith("- ")]
RULE_SRC = EXCERPTS["qr_rule"][1]
assert len(RULES) == 6 and RULE_SRC.count("\n") == 1 and "21 days stay QX-12" in RULE_SRC and RULES[1].startswith("- Copy every code")
P_IN, P_OUT = prices.PRICES[qr.MODEL]
G_IN, G_OUT = prices.PRICES[GEN_MODEL]
USD_INR = prices.USD_INR

golden = [json.loads(line) for line in (KIT / "evals" / "golden.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
by_id = {r["id"]: r for r in golden}
anchored = [r for r in golden if r.get("must_retrieve")]
PARA_FILE = KIT / "evals" / "paraphrases.jsonl"
paraphrases = [json.loads(line) for line in PARA_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
para_by_id = {p["id"]: p for p in paraphrases}
scored = ablate.paraphrase_rows(str(PARA_FILE), golden)
GOLD_Q = sorted({r["question"] for r in anchored})
ALL_Q = sorted(set(GOLD_Q) | {p["question"] for p in scored})
LIT_ROWS = [r for r in anchored if qr.literals(r["question"])]
LIT_Q = sorted({r["question"] for r in LIT_ROWS})
FIRST5 = anchored[:5]
FIRST5_LIT = [r for r in FIRST5 if qr.literals(r["question"])]
TENANTS = Counter(r["tenant"] for r in anchored)
# one kept call per distinct question: lk-06 and vr-01, lk-24 and lk-29 ask in the same words (the kit's own test says 69 in all)
assert len(scored) == sum(1 for p in paraphrases if p.get("same") is True) and len(ALL_Q) == 69 and len(GOLD_Q) < len(anchored)
assert {r["tenant"] for r in LIT_ROWS} == {"acme"} and len(FIRST5_LIT) == 1

base = re.search(r"Measured on (\d+ Sept \d{4}) from Cloud Shell, (\d+) rows: dense 5 alone ([\d.]+) recall@5 / ([\d.]+) MRR; the\s+"
                 r"lane's dense 20 -> rerank 5 ([\d.]+) / ([\d.]+)", ablate.__doc__)
BASE_DATE, BASE_ROWS, BASE_R5, BASE_MRR = base.group(1), int(base.group(2)), base.group(5), base.group(6)
assert (BASE_ROWS, BASE_R5, BASE_MRR) == (43, "0.96", "0.91") and len(anchored) > BASE_ROWS

ARM_LANE = next(n for n, _, _ in ablate.arms(SimpleNamespace(), ("dense20",)))
ARM_REWRITE = ablate.rewrite_arm(SimpleNamespace(project="p"), rewrite=lambda q: None)[0][0]

# the handbook's own words for the travel clause, quoted in the hero
HANDBOOK = (KIT / "evals" / "corpus" / "acme" / "hr_policy_2026.md").read_text(encoding="utf-8")
EXP12 = re.search(r"## EXP-12 \S+ Travel reimbursement\n\n(.*?)\.", HANDBOOK, re.S).group(1).replace("\n", " ") + "."
assert "per trip" in EXP12, EXP12

# ------------------------------------------------------------------ the bench's guard: the kit's rules in JavaScript
ZEROS = [cp for cp in range(0x110000) if chr(cp).isdecimal() and unicodedata.decimal(chr(cp)) == 0]
assert all(all(chr(z + k).isdecimal() and unicodedata.decimal(chr(z + k)) == k for k in range(10)) for z in ZEROS)
assert sum(1 for cp in range(0x110000) if chr(cp).isdecimal()) == 10 * len(ZEROS), "every decimal digit sits in a run of ten from its zero"
SPACES = [cp for cp in range(0x110000) if chr(cp).isspace()]
assert all(bool(re.match(r"\s", chr(cp))) == (cp in SPACES) for cp in range(0x3001)), "re's \\s is str.isspace() for str patterns"
FOLD = {chr(cp): chr(cp).casefold() for cp in range(0x110000) if chr(cp).casefold() != chr(cp).lower()}
WS_CLASS = "".join("\\u%04x" % cp for cp in SPACES)

GUARD_JS = r"""var ZEROS = __ZEROS__, FOLD = __FOLD__, WS = '__WS__';
var WSP = new RegExp('[' + WS + ']+'), WORD = '[\\p{L}\\p{N}_]';
var DASHES = String.fromCharCode(0x2010, 0x2011, 0x2012, 0x2013, 0x2014, 0x2015, 0x2212), RUPEE_SIGN = String.fromCharCode(0x20b9);
var RUPEE_WORD = new RegExp('(^|[^a-z0-9])(?:rs\\.?|inr)(?=[' + WS + ']*[0-9])[' + WS + ']*', 'g');
var PER_CENT = new RegExp('([0-9])[' + WS + ']?(?:%|per ?cent(?!' + WORD + '))', 'gu');
var PLURAL = new RegExp('(^|(?!' + WORD + ')[\\s\\S])(lakh|crore)s(?!' + WORD + ')', 'gu');
var END = '(?!' + WORD + ')';
var UNIT = new RegExp(' ?(?:%|(?:(?:working|calendar|business) )?(?:days?|weeks?|months?|years?|hours?|minutes?)' + END +
                      '|lakh' + END + '|crore' + END + '|employees' + END + '|workers' + END + '|times' + END + ')', 'uy');
var TOKEN = /[a-z0-9]+(?:[-\/.,][a-z0-9]+)*/g, NUMBER = /^[0-9]+(?:[.,][0-9]+)*$/, AN = /^[a-z0-9]$/;
function digit(ch){                                  /* unicodedata.decimal(): any script's digit as ASCII */
  var c = ch.codePointAt(0), lo = 0, hi = ZEROS.length - 1, z = -1;
  while (lo <= hi){ var mid = (lo + hi) >> 1; if (ZEROS[mid] <= c){ z = ZEROS[mid]; lo = mid + 1; } else hi = mid - 1; }
  return (z >= 0 && c - z <= 9) ? String(c - z) : ch; }
function collapse(s){ return String(s || '').split(WSP).filter(Boolean).join(' '); }       /* " ".join(s.split()) */
function normalise(text){                            /* normalise() */
  var t = Array.from(String(text || '')).map(function(ch){
    ch = digit(ch); if (DASHES.indexOf(ch) >= 0) ch = '-';
    return Object.prototype.hasOwnProperty.call(FOLD, ch) ? FOLD[ch] : ch.toLowerCase(); }).join('').split(RUPEE_SIGN).join(' rs ');
  t = t.replace(RUPEE_WORD, '$1rs ').replace(PER_CENT, '$1%').replace(PLURAL, '$1$2');
  return collapse(t); }
function literals(text){                             /* literals() */
  var t = normalise(text), out = [], m;
  TOKEN.lastIndex = 0;
  while ((m = TOKEN.exec(t)) !== null){
    var tok = m[0], s = m.index;
    if (!/[0-9]/.test(tok)) continue;
    if (NUMBER.test(tok)){
      if (s >= 3 && t.slice(s - 3, s) === 'rs ' && (s === 3 || !AN.test(t.charAt(s - 4)))) tok = 'rs ' + tok;
      UNIT.lastIndex = s + m[0].length; var u = UNIT.exec(t); if (u) tok += u[0]; }
    if (out.indexOf(tok) < 0) out.push(tok); }
  return out; }
function present(lit, text){                         /* _present(): whole, never inside a longer code or figure */
  for (var i = text.indexOf(lit); i >= 0; i = text.indexOf(lit, i + 1)){
    var b1 = i >= 1 ? text.charAt(i - 1) : '', b2 = i >= 2 ? text.charAt(i - 2) : '', j = i + lit.length, a1 = text.charAt(j), a2 = text.charAt(j + 1);
    if ((b1 && AN.test(b1)) || (b2 && AN.test(b2) && b1 && '-/.,'.indexOf(b1) >= 0)) continue;
    if ((a1 && AN.test(a1)) || (a1 && '-/.,'.indexOf(a1) >= 0 && a2 && AN.test(a2))) continue;
    return true; }
  return false; }
function dropped(question, rewrite){ var t = normalise(rewrite); return literals(question).filter(function(l){ return !present(l, t); }); }
function keeps(question, rewrite){ return dropped(question, rewrite).length === 0; }
function strip(s){ return s.replace(/^[ ?.!]+|[ ?.!]+$/g, ''); }
function same(a, b){ return strip(normalise(a)) === strip(normalise(b)); }          /* _same() */
function outcome(question, answer){                  /* rewrite(), from the model's answer on: parse, same, the guard */
  var got = collapse(answer);
  if (!got) return {outcome: 'fallback', error: 'parse', query: question, dropped: []};
  if (same(got, question)) return {outcome: 'same', error: null, query: question, dropped: []};
  var lost = dropped(question, got);
  if (lost.length) return {outcome: 'rejected', error: null, query: question, dropped: lost};
  return {outcome: 'rewritten', error: null, query: got, dropped: []}; }
window.__rq = {normalise: normalise, literals: literals, dropped: dropped, keeps: keeps, outcome: outcome};
"""
GUARD_JS = (GUARD_JS.replace("__ZEROS__", json.dumps(ZEROS)).replace("__FOLD__", json.dumps(FOLD, ensure_ascii=True, separators=(",", ":")))
            .replace("__WS__", WS_CLASS.replace("\\", "\\\\")))


class _Model:
    """google-genai's client as rewrite() calls it, answering with one given query: the kit's own outcome rule, unmodelled."""

    def __init__(self, answer):
        self.answer, self.models = answer, self

    def generate_content(self, model, contents, config):
        return SimpleNamespace(parsed={"query": self.answer}, text=None, usage_metadata=None)


def kit_outcome(question: str, answer: str) -> dict:
    got = qr.rewrite(_Model(answer), question)
    return {"outcome": got["outcome"], "error": got["error"], "query": got["query"], "dropped": got["dropped"]}


# ------------------------------------------------------------------ the bench: rows, rewrites, and BM25 over acme's corpus
# Each row: (id, the rewrite this page wrote for it, following the prompt's six rules). They are illustrations, not model
# output, until data/rewrites.txt records rewrite() on the author's lane; then the recorded outcomes replace them.
BENCH_ROWS = [
    ("pp-01", "per-trip cap on domestic travel reimbursement"),               # the module's own docstring example
    ("pp-10", "number of remote work days allowed per month"),
    ("jn-07", "contractor copying data to a USB drive when their statement of work (SOW) allows it"),
    ("lk-06", "notice period for confirmed employees"),                       # loses the grade
    ("pp-07", "Notice period for confirmed E3 employees"),                    # the question given back
    ("pp-09", "purchase approval authority for Rs 3,00,000"),                 # the same sum, written another way
    ("jn-03", "earned leave encashment on exit for 50 days and notice period for an E3 employee"),
    ("pp-16", "minimum bonus payable under the Payment of Bonus Act"),
    ("lk-03", "earned leave carry forward limit"),
]
CLAUSE = re.compile(r"[A-Z]{2,}(?:-[A-Z]+)?-\d+")


def row_of(rid: str) -> tuple:
    """(the row, the golden row whose anchors score it, golden or paraphrase)."""
    if rid in para_by_id:
        p = para_by_id[rid]
        return p, by_id[p["of"]], "paraphrase"
    return by_id[rid], by_id[rid], "golden"


CORPUS = KIT / "evals" / "corpus" / "acme"
docs = []
for p in sorted(CORPUS.glob("*.md")):
    for i, c in enumerate(dc.chunk_document({"slug": p.stem, "doc_type": "policy", "source_uri": f"gs://x/acme/{p.name}",
                                             "text": p.read_text(encoding="utf-8")}, "acme")):
        docs.append({"source": p.name, "locator": c.get("locator") or f"#{i}", "text": c["text"]})
N = len(docs)
DOCS = len(list(CORPUS.glob("*.md")))


def tokens(text: str) -> list:
    return re.findall(r"[a-z0-9\-]+", text.lower())            # ablate.tokens(): the ablation's sparse leg's words


# BM25Okapi as rank_bm25 0.2.2 computes it, lesson 2.2's port: k1 1.5, b 0.75, epsilon 0.25 (negative idf floored)
tok_docs = [tokens(d["text"]) for d in docs]
doc_len = [len(t) for t in tok_docs]
avgdl = sum(doc_len) / N
doc_freqs = [Counter(t) for t in tok_docs]
nd = Counter()
for f in doc_freqs:
    nd.update(f.keys())
K1, B, EPS = 1.5, 0.75, 0.25
idf = {w: math.log(N - n + 0.5) - math.log(n + 0.5) for w, n in nd.items()}
avg_idf = sum(idf.values()) / len(idf)
idf = {w: (v if v >= 0 else EPS * avg_idf) for w, v in idf.items()}


def bm25(q: str) -> list:
    out = [0.0] * N
    for w in tokens(q):
        if w not in idf:
            continue
        for i, f in enumerate(doc_freqs):
            qf = f.get(w, 0)
            if qf:
                out[i] += idf[w] * qf * (K1 + 1) / (qf + K1 * (1 - B + B * doc_len[i] / avgdl))
    return out


def target(anchors: list) -> list:
    """The row's clause codes when it has any (NP-03), else its documents (payment_of_bonus_act_1965)."""
    return [a for a in anchors if CLAUSE.fullmatch(a)] or list(anchors)


def is_hit(d: dict, anchors: list) -> bool:
    return any((d["locator"] == a) if CLAUSE.fullmatch(a) else d["source"].startswith(a) for a in anchors)


def ranked(text: str, anchors: list) -> tuple:
    scores = bm25(text)
    order = [i for i in sorted(range(N), key=lambda i: -scores[i]) if scores[i] > 0]
    rank = next((r for r, i in enumerate(order, 1) if is_hit(docs[i], anchors)), None)
    return rank, [[docs[i]["locator"], docs[i]["source"], is_hit(docs[i], anchors)] for i in order[:3]]


# the recorded rewrites, when the author's run is in: one line per bench row, as step 5's cell prints them
REWRITES_TXT = pb.recorded(LESSON, "rewrites.txt")
RECORDED = {}
if not REWRITES_TXT.startswith("[awaiting"):
    for line in REWRITES_TXT.splitlines():
        m = re.match(r"^(\S+)\s+(rewritten|same|rejected|fallback)\s+(\d+) ms  (.*)$", line)
        if m:
            RECORDED[m.group(1)] = {"outcome": m.group(2), "ms": int(m.group(3)), "detail": m.group(4)}
    assert set(RECORDED) == {rid for rid, _ in BENCH_ROWS}, f"data/rewrites.txt names {sorted(RECORDED)}: re-record it with step 5's cell"

bench, bench_rows_html, bench_options = {}, [], []
for rid, illustration in BENCH_ROWS:
    row, src, kind = row_of(rid)
    q, anchors = row["question"], target(src["must_retrieve"])
    if rid in RECORDED:
        rec = RECORDED[rid]
        got = {"outcome": rec["outcome"], "error": None, "query": q, "dropped": []}
        shown = None
        if rec["outcome"] == "rewritten":
            got["query"] = shown = rec["detail"]
            assert kit_outcome(q, shown)["outcome"] == "rewritten", (rid, shown)       # the recorded rewrite passes the kit's guard
        elif rec["outcome"] == "rejected":
            got["dropped"] = re.match(r"dropped (.*) - the question is searched$", rec["detail"]).group(1).split(", ")
            assert set(got["dropped"]) <= set(qr.literals(q)), (rid, got["dropped"])
        elif rec["outcome"] == "fallback":
            got["error"] = rec["detail"].split(" - ")[0]
        source = "recorded"
    else:
        got, shown, source = kit_outcome(q, illustration), illustration, "illustration"
    rank_q, top_q = ranked(q, anchors)
    rank_s, top_s = ranked(got["query"], anchors)
    bench[rid] = {"id": rid, "kind": kind, "of": src["id"], "q": q, "anchors": anchors, "lits": qr.literals(q), "rw": shown,
                  "source": source, "outcome": got["outcome"], "dropped": got["dropped"], "error": got["error"], "searched": got["query"],
                  "rank_q": rank_q, "rank_s": rank_s, "top_q": top_q, "top_s": top_s}
    kind_txt = "golden" if kind == "golden" else f"paraphrase of {src['id']}"
    rw_cell = (html.escape(shown) if shown else {"same": "(the question, given back)", "rejected": "(refused: the kit keeps no refused rewrite)",
                                                 "fallback": f"(no rewrite: {html.escape(got['error'] or 'the call failed')})"}.get(got["outcome"], ""))
    show = lambda r: "none" if r is None else str(r)  # noqa: E731
    bench_rows_html.append(f'<tr><td>{rid} &middot; {kind_txt}</td><td data-label="Question">{html.escape(q)}</td>'
                           f'<td data-label="Rewrite">{rw_cell}</td><td data-label="Outcome">{got["outcome"]}'
                           + (f' ({html.escape(", ".join(got["dropped"]))} dropped)' if got["dropped"] else "") + "</td>"
                           f'<td data-label="Anchor">{html.escape(", ".join(anchors))}</td>'
                           f'<td data-label="BM25 rank: question, searched">{show(rank_q)}, {show(rank_s)}</td></tr>')
    bench_options.append(f'<option value="{rid}">{rid} &middot; {html.escape(q)}</option>')
BENCH_SOURCE = "recorded" if RECORDED else "illustration"
up = sum(1 for b in bench.values() if (b["rank_s"] or 10 ** 6) < (b["rank_q"] or 10 ** 6))
down = sum(1 for b in bench.values() if (b["rank_s"] or 10 ** 6) > (b["rank_q"] or 10 ** 6))
first_q = sum(1 for b in bench.values() if b["rank_q"] == 1)
OUTCOME_COUNTS = Counter(b["outcome"] for b in bench.values())
assert bench["lk-06"]["lits"] == ["e3"] and bench["pp-09"]["lits"] == ["rs 3 lakh"] and bench["jn-03"]["lits"] == ["e3", "50 days"]
if not RECORDED:   # the illustrations show the four outcomes' first three, and the guard refusing twice
    assert (bench["lk-06"]["outcome"], bench["pp-07"]["outcome"], bench["pp-09"]["outcome"]) == ("rejected", "same", "rejected")


def word(n: int) -> str:
    return ["none", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"][n] if n <= 12 else str(n)


def ordinal(n) -> str:
    if n is None:
        return "nowhere: no chunk shares a word with it"
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


# the bench's prose about jn-07: its question's rank is the corpus's, the searched text's is the rewrite's, illustrated or recorded
J7 = bench["jn-07"]
assert all(nd[w] > N / 2 and idf[w] == EPS * avg_idf for w in ("a", "to", "and")), "the filler words count, at the floor"
JN07_Q = ordinal(J7["rank_q"])
if J7["outcome"] != "rewritten":
    JN07_S = f"the stage would search the question itself here ({J7['outcome']}), so the rank stays {JN07_Q}."
elif (J7["rank_s"] or 10 ** 6) < (J7["rank_q"] or 10 ** 6):
    JN07_S = f"the rewrite, a search query rather than a sentence, ranks it {ordinal(J7['rank_s'])}."
else:
    JN07_S = f"the rewrite ranks it {ordinal(J7['rank_s'])}, no higher."
AS_ASKED = OUTCOME_COUNTS["rejected"] + OUTCOME_COUNTS["same"] + OUTCOME_COUNTS["fallback"]
WHY = [f"{word(OUTCOME_COUNTS[k])} {what}" for k, what in (("rejected", "refused by the guard"), ("same", "given back by the model"),
                                                          ("fallback", "after a failed call")) if OUTCOME_COUNTS[k]]
BENCH_SUMMARY = (f"Of the {word(len(bench))} rows, BM25 already puts the anchor first for the question as asked on {word(first_q)}. "
                 f"The text the stage would search ranks the anchor higher on {word(up)}, in the same place on "
                 f"{word(len(bench) - up - down)}, and lower on {word(down)}"
                 + (f". {word(AS_ASKED).capitalize()} of the {word(len(bench))} search the question itself: "
                    + (", ".join(WHY[:-1]) + " and " + WHY[-1] if len(WHY) > 1 else WHY[0]) + "." if AS_ASKED else "."))

# ------------------------------------------------------------------ node runs the guard and must agree with the kit
TEXTS = sorted({r["question"] for r in golden} | {p["question"] for p in paraphrases})
TEXTS += [illus for _, illus in BENCH_ROWS]
RUPEE = "\N{INDIAN RUPEE SIGN}"


def deva(text: str) -> str:
    """The text's ASCII digits as Devanagari ones."""
    return "".join(chr(0x0966 + int(ch)) if ch.isdigit() else ch for ch in text)


TEXTS += [
    "Can I encash LV-07 leave under s.53 on Rs 52,000 a month after 45 days?",
    "A confirmed E3 with a GSTR-3B for FY2026 and invoice INV-2026-0412", "Bonus at 8.33 per cent of Rs 3 lakhs?",
    "lv\N{EN DASH}07 encashment, s.53, " + RUPEE + "52,000 a month, 45 days", "LV-07 encashment s.53 Rs. 52,000 per month after 45 days of service",
    "LV-07 encashment s.53 INR 52,000 45 days", RUPEE + deva("52,000") + " " + deva("45") + " days",
    "Who approves it after 4 years 240 days?", "12.5 % of Rs\N{NO-BREAK SPACE}3,00,000 over 30 working days", "rs5 inr7 rs.9 a crores 3 lakhsx 2 lakhs",
    "STRASSE \N{LATIN SMALL LETTER SHARP S} \N{LATIN SMALL LIGATURE FI}le \N{LATIN CAPITAL LETTER I WITH DOT ABOVE} "
    "\N{LATIN CAPITAL LETTER SHARP S} 20\N{THIN SPACE}employees, 7 times, 12 calendar months",
    "notice\N{EM SPACE}period\N{IDEOGRAPHIC SPACE}E3\N{LINE SEPARATOR}E30 \N{EM DASH} 5\N{MINUS SIGN}6", "",
]
for z in ZEROS:   # every script's digits, inside an amount and a unit
    TEXTS.append("Rs " + chr(z + 5) + chr(z + 2) + "," + chr(z) * 3 + " in " + chr(z + 4) + chr(z + 5) + " days")
TEXTS.append("".join(FOLD) + " " + "".join(chr(cp) for cp in SPACES).join(["a1", "b2", "c3"]))
PAIRS = [(row_of(rid)[0]["question"], illus) for rid, illus in BENCH_ROWS]
PAIRS += [(q, q) for q in TEXTS] + [(q, "") for q in TEXTS[:5]] + [(q, "   ") for q in TEXTS[5:8]]
for q in ALL_Q + [t for t in TEXTS if qr.literals(t)]:
    lits = qr.literals(q)
    if lits:   # the question with its first literal removed as written, and with every literal reordered to the end
        PAIRS.append((q, re.sub(re.escape(lits[0]), " ", qr.normalise(q), count=1)))
        PAIRS.append((q, "search query " + " ".join(reversed(lits))))
PAIRS += [("What is the notice period for a confirmed E3 after 45 days on Rs 52,000 under LV-07?", rw) for rw in (
    "notice period confirmed E2 45 days Rs 52,000 LV-07", "notice period confirmed E30 45 days Rs 52,000 LV-07",
    "notice period confirmed E3 60 days Rs 52,000 LV-07", "notice period confirmed E3 45 working days Rs 52,000 LV-07",
    "notice period confirmed E3 45 days Rs 52000 LV-07", "notice period confirmed E3 45 days Rs 52,000,000 LV-07",
    "notice period confirmed E3 45 days Rs 52,000 LV-7", "notice period for a confirmed employee")]
PAIRS += [("Under s.53, is gratuity due?", "Code on Social Security section 53 gratuity"),
          ("Whose approval is needed for a Rs 3 lakh purchase?", "purchase approval authority for Rs 3 lakh (Rs 3,00,000)")]

NODE = ("var window = {}, document = {getElementById: function(){ return null; }};\n"
        "(new Function('window', 'document', " + json.dumps(GUARD_JS) + "))(window, document);\n"
        "var T = " + json.dumps(TEXTS) + ", P = " + json.dumps(PAIRS) + ", R = window.__rq;\n"
        "process.stdout.write(JSON.stringify({norm: T.map(R.normalise), lits: T.map(R.literals), "
        "pairs: P.map(function(p){ var o = R.outcome(p[0], p[1]); return [o.outcome, o.error, o.query, o.dropped, R.dropped(p[0], p[1]), R.keeps(p[0], p[1])]; })}));\n")
node = subprocess.run(["node", "-"], input=NODE, capture_output=True, text=True, encoding="utf-8")
assert node.returncode == 0, node.stderr[-800:]
js = json.loads(node.stdout)
for t, n_js, l_js in zip(TEXTS, js["norm"], js["lits"]):
    assert n_js == qr.normalise(t), (t, n_js, qr.normalise(t))
    assert l_js == qr.literals(t), (t, l_js, qr.literals(t))
for (q, a), got in zip(PAIRS, js["pairs"]):
    k = kit_outcome(q, a)
    assert got == [k["outcome"], k["error"], k["query"], k["dropped"], qr.dropped(q, a), qr.keeps_literals(q, a)], (q, a, got, k)
N_NODE_TEXTS, N_NODE_PAIRS = len(TEXTS), len(PAIRS)
assert {k["outcome"] for k in (kit_outcome(q, a) for q, a in PAIRS)} == set(qr.OUTCOMES), "the cases reach every outcome"

# ------------------------------------------------------------------ cells: the commands the page asks you to paste
CELLS = {}
CELLS["names"] = r"""svc_env() { gcloud run services describe "$1" --region "$REGION" --project "$PROJECT" \
  --format='value(spec.template.spec.containers[0].env)' | tr ';' '\n' | grep "'name': '$2'" | sed -nE "s/.*'value': '([^']*)'.*/\1/p"; }
setenv() { v="$(svc_env documind-api "$1")"; if [ -n "$v" ]; then export "$1=$v"; else unset "$1"; fi; }
for N in QUERY_REWRITE QUERY_REWRITE_MODEL RETRIEVAL_BACKEND; do setenv "$N"; done
python -m pip install -q google-cloud-discoveryengine==0.13.11   # the API's own pin, services/rag-api/requirements.txt: the ablation's reranker
echo "rewrite: ${QUERY_REWRITE:-off (default)}  model: ${QUERY_REWRITE_MODEL:-gemini-3.1-flash-lite (default)}  backend: ${RETRIEVAL_BACKEND:-vector (default)}"
"""
CELLS["ui"] = r"""gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND (jsonPayload.event="stream" OR jsonPayload.event="query_rewrite")' \
  --project "$PROJECT" --freshness 10m --limit 5 --format=json | python -c "
import sys, json
rows = [e['jsonPayload'] for e in json.load(sys.stdin)]
for r in rows:
    if r['event'] == 'stream':
        print('stream | brain', r.get('brain'), '| tenant', r.get('tenant'), '| pool', r.get('pool'), '| retrieve_ms', r.get('retrieve_ms'),
              '| answerable', r.get('answerable'), '| Rs %.2f' % (85 * (r.get('cost_usd') or 0)))
print('query_rewrite lines in the last 10 minutes:', sum(1 for r in rows if r['event'] == 'query_rewrite'))"
"""
CELLS["guard"] = r"""python - <<'PY'
import sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, ".")
from shared import query_rewrite as qr
Q = "Can I encash LV-07 leave under s.53 on Rs 52,000 a month after 45 days?"
print("the question's literals:", qr.literals(Q))
for rewrite in ("leave encashment LV-07 s.53 Rs 52,000 monthly wages 45 days",
                __ESCAPED__
                "leave encashment LV-07 s.53 Rs 52000 45 days",
                "leave encashment LV-07 s.53 Rs 52,000 45 working days",
                "LV-07 encashment under section 53, Rs 52,000, 45 days"):
    lost = qr.dropped(Q, rewrite)
    print(f"{'refused' if lost else 'kept':8}{rewrite}" + (f"   (dropped {', '.join(lost)})" if lost else ""))
PY"""
U = "\\" + "u"      # a backslash and a u, kept apart in this file: the page shows the escapes, Python reads the characters
CELLS["guard"] = CELLS["guard"].replace("__ESCAPED__", f'"lv{U}201307 encashment, s.53, {U}20b9{U}096b{U}0968,{U}0966{U}0966{U}0966 a month, 45 days",')
ROWS_LIST = "\n".join(f'    ("{rid}", {json.dumps(row_of(rid)[0]["question"])}),' for rid, _ in BENCH_ROWS)
CELLS["direct"] = r"""python - <<'PY'
import os, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, ".")
from google import genai
from shared import prices, query_rewrite
client = genai.Client(enterprise=True, project=os.environ["PROJECT"], location="global")   # Gemini 3.x is served from global only
ROWS = [
__ROWS__
]
tokens_in = tokens_out = 0
usd = 0.0
for rid, question in ROWS:
    got = query_rewrite.rewrite(client, question)
    tokens_in, tokens_out, usd = tokens_in + got["tokens_in"], tokens_out + got["tokens_out"], usd + got["cost_usd"]
    detail = {"rewritten": got["query"], "same": "given back as asked - the question is searched",
              "rejected": "dropped " + ", ".join(got["dropped"]) + " - the question is searched",
              "fallback": f"{got['error']} - the question is searched"}[got["outcome"]]
    print(f"{rid:6} {got['outcome']:9} {got['ms']:5} ms  {detail}")
print(f"{len(ROWS)} calls to {query_rewrite.MODEL}, prompt {query_rewrite.PROMPT_VERSION}: {tokens_in:,} tokens in, {tokens_out:,} out, "
      f"Rs {prices.inr(usd):.2f} at list price")
PY""".replace("__ROWS__", ROWS_LIST)
ASK = r"""ask() { curl -s -X POST "$1/v1/query" -H "Authorization: Bearer $(tok "$API")" -H "Content-Type: application/json" \
  -d "{\"query\":\"$2\",\"tenant_id\":\"acme\",\"stream\":false,\"top_k\":3}" | python -c "
import sys, json
sys.path.insert(0, '.'); from shared import prices
j = json.load(sys.stdin); s = j['stages']
usd = j.get('cost_usd') or prices.usd(j.get('model'), j.get('tokens_in') or 0, j.get('tokens_out') or 0, j.get('cached_tokens') or 0)   # cost_usd is empty on the vertex backend
print('rewrite', s.get('rewrite', '-'), '| rewrite_ms', s.get('rewrite_ms', '-'), '| retrieve_ms', s['retrieve_ms'], '| pool', s['pool'],
      '| answerable', j['answerable'], '| Rs %.2f' % prices.inr(usd))
print('   searched:', s.get('search_query', '(no stage: the question)'))
for c in j['citations']:
    print('   cited:', c['source_uri'].split('/')[-1], '#' + c['chunk_id'].rsplit('#', 1)[1], c['quote'][:60])"; }"""
PP01 = para_by_id["pp-01"]["question"]
CELLS["on"] = (r"""gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate \
  --update-env-vars QUERY_REWRITE=on --quiet
export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"
""" + ASK + f'\nask "$CAND" "{PP01}"')
CELLS["fail"] = (r"""gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate \
  --update-env-vars QUERY_REWRITE_MODEL=no-such-model --quiet
""" + f'ask "$CAND" "{PP01}"')
CELLS["rows"] = r"""gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="query_rewrite"' \
  --project "$PROJECT" --freshness 15m --limit 2 --format=json | python -c "import sys, json; [print(json.dumps(e['jsonPayload'])) for e in json.load(sys.stdin)]"
"""
CELLS["undo"] = r"""gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate \
  --remove-env-vars QUERY_REWRITE,QUERY_REWRITE_MODEL --quiet
gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate --quiet
echo "template now: QUERY_REWRITE=$(svc_env documind-api QUERY_REWRITE) QUERY_REWRITE_MODEL=$(svc_env documind-api QUERY_REWRITE_MODEL)"
gcloud run services describe documind-api --region "$REGION" --project "$PROJECT" --format='value(status.traffic[].percent,status.traffic[].revisionName)'"""
ABLATE_GOLDEN = 'make ablate PROJECT=$PROJECT ABLATE_ARGS="--arms dense20 --rewrite"'
ABLATE_PARA = 'make ablate PROJECT=$PROJECT ABLATE_ARGS="--arms dense20 --rewrite --paraphrases evals/paraphrases.jsonl"'
CELLS["wiring"] = ('make ablate PROJECT=$PROJECT ABLATE_ARGS="--arms dense20 --rewrite --limit 5"\n'
                   '# the same without make: python evals/ablate.py --project $PROJECT --region $REGION --arms dense20 --rewrite --limit 5')
CELLS["golden"] = ABLATE_GOLDEN
CELLS["para"] = ABLATE_PARA
LIT_FILE = "/tmp/literal_rows.jsonl"
CELLS["litrows"] = r"""python - <<'PY'
import json, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, ".")
from shared.query_rewrite import literals
rows = [r for r in (json.loads(line) for line in open("evals/golden.jsonl", encoding="utf-8") if line.strip())
        if r.get("must_retrieve") and literals(r["question"])]
with open("__LIT__", "w", encoding="utf-8") as f:
    f.writelines(json.dumps(r) + "\n" for r in rows)
print(len(rows), "anchored golden rows carry a literal; the guard can refuse a rewrite of no other:")
for r in rows:
    print(f"   {r['id']:6} {', '.join(literals(r['question']))}")
PY""".replace("__LIT__", LIT_FILE)
CELLS["edit"] = r"""python - <<'PY'
import sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
path = "shared/query_rewrite.py"
src = open(path, encoding="utf-8").read()
rule = (__RULE__)
assert src.count(rule) == 1, "the rule is not where this page expects it: git checkout -- shared/query_rewrite.py, then pull the kit"
open(path, "w", encoding="utf-8").write(src.replace(rule, ""))
sys.path.insert(0, ".")
from shared import query_rewrite as qr
rules = [line for line in qr.prompt("QUESTION").splitlines() if line.startswith("- ")]
print(len(rules), "rules left; the prompt version still says", qr.PROMPT_VERSION)
print("\n".join(rules))
PY""".replace("__RULE__", "\n        ".join(repr(line + "\n") for line in RULE_SRC.split("\n")))
CELLS["change"] = (f'make ablate PROJECT=$PROJECT ABLATE_ARGS="--arms dense20 --rewrite --golden {LIT_FILE}"')
CELLS["restore"] = r"""git checkout -q -- shared/query_rewrite.py
git status --short -- shared/
python -c "import sys; sys.path.insert(0, '.'); from shared import query_rewrite as qr; print('the rule is back:', any(l.startswith('- Copy every code') for l in qr.prompt('q').splitlines()))"
"""
TEST_FILE = "test_query_rewrite.py"
CELLS["tests"] = (f'python -m unittest discover -s evals/tests -p {TEST_FILE} 2>&1 | grep -E "^(Ran|OK|FAILED)" | sed -E "s/ in [0-9.]+s$//"')
CELLS = {k: v.rstrip("\n") for k, v in CELLS.items()}
assert all(not v.endswith("\\") for v in CELLS.values())

LABELS = {
    "names": "run in the operator shell, in $DEMO_ROOT, once per shell",
    "ui": "run in the operator shell, after the question in the Chat page (reads the API's log; changes nothing)",
    "guard": "run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: no call leaves the machine)",
    "direct": f"run in the operator shell, in $DEMO_ROOT (a Python cell; {len(BENCH_ROWS)} {qr.MODEL} calls, a few paise)",
    "on": "run in the operator shell (one new revision, no traffic; one question to it)",
    "fail": "run in the operator shell (one more revision, no traffic, a model that does not exist; the same question)",
    "rows": "run in the operator shell (reads the API's log; the two lines the two questions wrote)",
    "undo": "run in the operator shell (the undo: the two variables removed, the tag dropped, the template read back)",
    "wiring": "run in the operator shell, in $DEMO_ROOT (five rows: a wiring check, about a minute)",
    "golden": f"run in the operator shell, in $DEMO_ROOT (the {len(anchored)} anchored golden rows, two arms)",
    "para": f"run in the operator shell, in $DEMO_ROOT (the same rows and the {len(scored)} paraphrases: {len(anchored) + len(scored)} rows, two arms)",
    "litrows": "run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0)",
    "edit": "run in the operator shell, in $DEMO_ROOT (a Python cell; edits one kit file in your clone, never the lane)",
    "change": f"run in the operator shell, in $DEMO_ROOT (the {len(LIT_ROWS)} rows above, two arms, the edited prompt)",
    "restore": "run in the operator shell, in $DEMO_ROOT (the kit file put back)",
    "tests": "run in the operator shell, in $DEMO_ROOT (the kit's own tests: fakes for the model and the lane; Rs 0)",
}


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + html.escape(label) + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + html.escape(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


# ------------------------------------------------------------------ the offline cells, run here on the kit
def run_cell(code: str, cwd: Path, swap: tuple = ()) -> str:
    """A page cell's Python, between its PY markers, run as the page runs it from the kit's root; swap moves a path."""
    body = code.split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
    for old, new in swap:
        body = body.replace(old, new)
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}
    env.pop("DOCUMIND_PROFILE", None)
    r = subprocess.run([sys.executable, "-"], input=body, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", env=env)
    assert r.returncode == 0, r.stderr[-800:]
    return r.stdout.rstrip("\n")


t = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "evals/tests", "-p", TEST_FILE], cwd=str(KIT), capture_output=True,
                   text=True, encoding="utf-8", env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"})
OUT_TESTS = "\n".join(re.sub(r" in [0-9.]+s$", "", line) for line in (t.stdout + t.stderr).splitlines() if re.match(r"^(Ran|OK|FAILED)", line))
N_TESTS = int(re.search(r"Ran (\d+) tests", OUT_TESTS).group(1))
assert t.returncode == 0 and OUT_TESTS == f"Ran {N_TESTS} tests\nOK", OUT_TESTS   # every test ran: google-genai's own check included
OUT_GUARD = run_cell(CELLS["guard"], KIT)
assert [line.split()[0] for line in OUT_GUARD.splitlines()[1:]] == ["kept", "kept", "refused", "refused", "refused"], OUT_GUARD
scratch = Path(tempfile.mkdtemp(prefix="lesson25-"))
try:
    OUT_LITROWS = run_cell(CELLS["litrows"], KIT, swap=((LIT_FILE, (scratch / "literal_rows.jsonl").as_posix()),))
    assert OUT_LITROWS.startswith(f"{len(LIT_ROWS)} anchored golden rows") and len((scratch / "literal_rows.jsonl").read_text(encoding="utf-8").splitlines()) == len(LIT_ROWS)
    (scratch / "shared").mkdir()
    for name in ("query_rewrite.py", "prices.py"):
        shutil.copy(KIT / "shared" / name, scratch / "shared" / name)
    OUT_EDIT = run_cell(CELLS["edit"], scratch)            # the edit, on a copy of the kit's two files
    edited = (scratch / "shared" / "query_rewrite.py").read_text(encoding="utf-8")
    assert RULE_SRC not in edited and edited.count("\n") == (KIT / QR).read_text(encoding="utf-8").count("\n") - 2
finally:
    shutil.rmtree(scratch, ignore_errors=True)
assert OUT_EDIT.startswith("5 rules left") and "Copy every code" not in OUT_EDIT, OUT_EDIT
r = subprocess.run([sys.executable, "-c", CELLS["restore"].splitlines()[-1].split('python -c "', 1)[1][:-1]], cwd=str(KIT),
                   capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
assert r.returncode == 0, r.stderr[-400:]
OUT_RESTORE = r.stdout.rstrip("\n")
assert OUT_RESTORE == "the rule is back: True", OUT_RESTORE

# ------------------------------------------------------------------ the author's run, recorded
REC = {k: pb.recorded(LESSON, f"{k}.txt") for k in ("ui", "candidate", "rewrite_rows", "ablate_wiring", "ablate_golden", "ablate_paraphrases", "changeit")}
awaiting = lambda text: text.startswith("[awaiting")  # noqa: E731
CAND = {}
if awaiting(REC["candidate"]):
    CAND = {k: REC["candidate"] for k in ("on", "fallback", "undo")}
else:
    parts = re.split(r"(?m)^### (on|fallback|undo)\s*$", REC["candidate"])
    CAND = {parts[i]: parts[i + 1].strip("\n") for i in range(1, len(parts) - 1, 2)}
    assert set(CAND) == {"on", "fallback", "undo"}, "data/candidate.txt needs its three sections: ### on, ### fallback, ### undo"
    assert "rewrite fallback" in CAND["fallback"], "the forced failure is a fallback on a 200 answer"

ARM_KEYS = {"lane": ARM_LANE, "rewrite": ARM_REWRITE}
SPLIT = re.compile(r"^\s+golden (\d+) rows, recall@5 ([\d.]+), mrr ([\d.]+), (\d+) at 1\.0 \| paraphrases (\d+) rows, recall@5 ([\d.]+), mrr ([\d.]+), (\d+) at 1\.0$")
TALLY = re.compile(r"rewrite: (\d+) questions? - (\d+) rewritten, (\d+) given back as asked, (\d+) refused by the literal guard, (\d+) fell back"
                   r"(?: \(([^)]*)\))?; ([\d,]+) tokens in, ([\d,]+) out, Rs ([\d.]+) at list price")


def parse_ablate(text: str) -> dict:
    """evals/ablate.py's lines read back: each arm's numbers and its golden and paraphrase shares, and the tally."""
    out, cur = {"arms": {}}, None
    if awaiting(text):
        return out
    m = re.match(r"(\d+) rows with anchors", text)
    out["rows"] = int(m.group(1)) if m else None
    for line in text.splitlines():
        key = next((k for k, name in ARM_KEYS.items() if line.startswith(name)), None)
        if key:
            nums = line[len(ARM_KEYS[key]):].split()
            cur = out["arms"][key] = ({"depth": float(nums[0]), "r5": float(nums[1]), "mrr": float(nums[2]), "rows1": int(nums[3]), "p95": int(nums[4])}
                                      if nums and nums[0] != "every" else {"failed": True})
            continue
        s, t = SPLIT.match(line), TALLY.search(line)
        if s and cur is not None:
            cur["golden"] = {"rows": int(s.group(1)), "r5": float(s.group(2)), "mrr": float(s.group(3)), "rows1": int(s.group(4))}
            cur["para"] = {"rows": int(s.group(5)), "r5": float(s.group(6)), "mrr": float(s.group(7)), "rows1": int(s.group(8))}
        if t:
            out["tally"] = {"calls": int(t.group(1)), "rewritten": int(t.group(2)), "same": int(t.group(3)), "rejected": int(t.group(4)),
                            "fallback": int(t.group(5)), "errors": t.group(6), "rs": float(t.group(9))}
    assert set(out["arms"]) == {"lane", "rewrite"} and "tally" in out, f"the recorded run lacks an arm line or the tally: {sorted(out['arms'])}"
    return out


AB = {k: parse_ablate(REC[k]) for k in ("ablate_wiring", "ablate_golden", "ablate_paraphrases", "changeit")}
ONE_G, ONE_P = 1 / len(anchored), 1 / len(scored)


def compare(a: dict, b: dict, one: float, what: str) -> str:
    """One sentence on the rewrite row against the lane's, with recall@5's difference counted in rows."""
    d5, dm = b["r5"] - a["r5"], b["mrr"] - a["mrr"]
    if abs(d5) < one / 2:
        moved = "recall@5 moved by less than half a row, so on recall the rewrite is not the knob here"
    else:
        k = round(abs(d5) / one)
        moved = f"recall@5 {'rose' if d5 > 0 else 'fell'} by {abs(d5):.2f}, about {word(k)} row{'s' if k != 1 else ''}' worth"
    return (f"on the {what}, the lane's row reads recall@5 {a['r5']:.2f} and MRR {a['mrr']:.2f}, the rewrite row {b['r5']:.2f} and "
            f"{b['mrr']:.2f}: {moved}, and MRR moved by {dm:+.2f}")


g, p_, c_ = AB["ablate_golden"], AB["ablate_paraphrases"], AB["changeit"]
first_up = lambda s: s[:1].upper() + s[1:]  # noqa: E731  - str.capitalize() would lower "MRR"
if g["arms"]:
    t = g["tally"]
    RESULT_GOLDEN = ("<p><strong>The author's lane, the golden run.</strong> "
                     + first_up(compare(g["arms"]["lane"], g["arms"]["rewrite"], ONE_G, f"{g['rows']} golden rows"))
                     + f". The tally: {t['calls']} questions, {t['rewritten']} rewritten, {t['same']} given back, {t['rejected']} refused, "
                     f"{t['fallback']} fell back, Rs {t['rs']:.2f} for the calls.</p>")
else:
    RESULT_GOLDEN = ""
if p_["arms"] and "golden" in p_["arms"]["lane"]:
    RESULT_PARA = ("<p><strong>The author's lane, the paraphrase run, split.</strong> "
                   + first_up(compare(p_["arms"]["lane"]["golden"], p_["arms"]["rewrite"]["golden"], ONE_G, "golden rows"))
                   + "; " + compare(p_["arms"]["lane"]["para"], p_["arms"]["rewrite"]["para"], ONE_P, "paraphrases") + ".</p>")
else:
    RESULT_PARA = ""
if c_["arms"] and g["arms"]:
    RESULT_CHANGE = (f"<p><strong>The author's lane.</strong> With the rule in place, the golden run refused {g['tally']['rejected']} of its "
                     f"{g['tally']['calls']} questions' rewrites, every one of them among these {len(LIT_Q)}; with the rule deleted, the guard refused "
                     f"{c_['tally']['rejected']} of {c_['tally']['calls']}. On these rows the rewrite row reads recall@5 "
                     f"{c_['arms']['rewrite']['r5']:.2f} against the lane's {c_['arms']['lane']['r5']:.2f}.</p>")
else:
    RESULT_CHANGE = ""

# ------------------------------------------------------------------ what the runs cost: shared/prices.py and the counts
RANK_USD = 1.0 / 1000      # the Ranking API's listed rate as lesson 2.3's page states it: one US dollar per thousand requests


def rewrite_usd(q: str) -> float:
    """One rewrite call at list price, estimated: the prompt in, a query as long as the question out (estimate_tokens)."""
    return prices.usd(qr.MODEL, estimate_tokens(qr.prompt(q)), estimate_tokens(json.dumps({"query": q})))


ANSWER_MAX_USD = prices.usd(GEN_MODEL, MAX_CONTEXT, MAX_ANSWER)      # one answer at config.py's budgets, one attempt
WIRE_Q = {r["question"] for r in FIRST5}
BENCH_Q = [row_of(rid)[0]["question"] for rid, _ in BENCH_ROWS]
COST = [  # (step, what is billed, Ranking API requests, the questions rewritten, answers)
    ("3", "the Chat page's answer", 0, [], 1),
    ("5", "the bench's questions, one call each", 0, BENCH_Q, 0),
    ("6", "two answers and one rewrite (the failed call bills nothing)", 0, [PP01], 2),
    ("7", "the wiring check: 5 rows, two arms", 2 * 5, sorted(WIRE_Q), 0),
    ("7", f"the golden run: {len(anchored)} rows, two arms", 2 * len(anchored), GOLD_Q, 0),
    ("7", f"the paraphrase run: {len(anchored) + len(scored)} rows, two arms", 2 * (len(anchored) + len(scored)), ALL_Q, 0),
    ("8", f"the changed prompt: {len(LIT_ROWS)} rows, two arms", 2 * len(LIT_ROWS), LIT_Q, 0),
]
cost_rows, CALLS_RS, RANK_RS, N_ANSWERS, N_RANK = [], 0.0, 0.0, 0, 0
for step, what, ranks, qs, answers in COST:
    rs_rank, rs_calls = ranks * RANK_USD * USD_INR, sum(rewrite_usd(q) for q in qs) * USD_INR
    CALLS_RS, RANK_RS, N_ANSWERS, N_RANK = CALLS_RS + rs_calls, RANK_RS + rs_rank, N_ANSWERS + answers, N_RANK + ranks
    billed = ", ".join(x for x in (f"{ranks} Ranking API requests, Rs {rs_rank:.2f}" if ranks else "",
                                   f"{len(qs)} rewrite call{'s' if len(qs) != 1 else ''}, Rs {rs_calls:.2f}" if qs else "",
                                   f"{answers} answer{'s' if answers != 1 else ''}, at most Rs {answers * ANSWER_MAX_USD * USD_INR:.2f}" if answers else "") if x)
    cost_rows.append(f'<tr><td>{step}</td><td data-label="What is billed">{html.escape(what)}</td><td data-label="Rupees">{billed}</td></tr>')
MEASURE_RS = CALLS_RS + RANK_RS
PER_1000_RS = sum(rewrite_usd(q) for q in ALL_Q) / len(ALL_Q) * 1000 * USD_INR
if g["arms"]:
    PER_1000_RS = g["tally"]["rs"] / g["tally"]["calls"] * 1000          # the author's measured calls replace the estimate
    PER_1000_SRC = f"measured: the golden run's {g['tally']['calls']} calls cost Rs {g['tally']['rs']:.2f}"
else:
    PER_1000_SRC = "estimated from the prompt's length; your tally line prints the real figure"
assert 15 < MEASURE_RS < 40, MEASURE_RS

# ------------------------------------------------------------------ the page's numbers
WIN = {f"CELL_{k.upper()}": bash_window(LABELS[k], v) for k, v in CELLS.items()}
LANE = "(the author's lane: your ids, times and numbers are yours)"
OUTS = {
    "names": ("(a lane deployed by make up: neither make target sets QUERY_REWRITE, so the defaults show)",
              f"rewrite: {QR_DEFAULT} (default)  model: {QR_MODEL_DEFAULT} (default)  backend: vector"),
    "ui": (LANE, REC["ui"]),
    "guard": ("(the kit's own output, produced when this page was built; yours should match it)", OUT_GUARD),
    "direct": ("(the author's lane: the model's words are its own, run to run; the outcomes and the guard's verdicts are the point)", REWRITES_TXT),
    "on": (LANE, CAND["on"]),
    "fail": (LANE, CAND["fallback"]),
    "rows": ("(the author's lane, newest first: no line carries a question, a rewrite or a literal)", REC["rewrite_rows"]),
    "undo": (LANE, CAND["undo"]),
    "wiring": (LANE, REC["ablate_wiring"]),
    "golden": (LANE, REC["ablate_golden"]),
    "para": (LANE, REC["ablate_paraphrases"]),
    "litrows": ("(the kit's own output, produced when this page was built)", OUT_LITROWS),
    "edit": ("(the cell's own output, produced when this page was built on a copy of the two files)", OUT_EDIT),
    "change": (LANE, REC["changeit"]),
    "restore": ("(the kit's own output after the checkout, produced when this page was built)", OUT_RESTORE),
    "tests": ("(the kit's own output, produced when this page was built; a venv without google-genai skips one test and says so)", OUT_TESTS),
}
WIN.update({f"OUT_{k.upper()}": out_window(*v) for k, v in OUTS.items()})

NEXT = MANIFEST["modules"]["02"]["lessons"]["2.6"]["name"]
STATS = {
    "MODEL": qr.MODEL, "TIMEOUT": f"{qr.TIMEOUT_S:g}", "MAXOUT": str(qr.MAX_OUTPUT_TOKENS), "QCHARS": f"{qr.QUESTION_CHARS:,}",
    "PROMPT_VERSION": qr.PROMPT_VERSION, "QR_DEFAULT": QR_DEFAULT, "N_RULES": word(len(RULES)), "RULE_TEXT": html.escape(RULES[1][2:]),
    "P_IN": f"{P_IN:.2f}", "P_OUT": f"{P_OUT:.2f}", "USD_INR": str(USD_INR), "GEN_MODEL": GEN_MODEL,
    "ROWS": str(len(golden)), "ANCH": str(len(anchored)), "ACME": str(TENANTS["acme"]), "ZETA": str(TENANTS["zeta"]), "GLOBEX": str(TENANTS["globex"]),
    "PARA_ALL": str(len(paraphrases)), "PARA": str(len(scored)), "PARA_RUN": str(len(anchored) + len(scored)), "ALL_Q": str(len(ALL_Q)),
    "PARA_SAME_FALSE": str(sum(1 for p in paraphrases if p.get("same") is not True)), "LIT_FILE": LIT_FILE, "N_TESTS": str(N_TESTS),
    "TEST_FILE": TEST_FILE,
    "GOLD_Q": str(len(GOLD_Q)), "LIT_ROWS": str(len(LIT_ROWS)), "LIT_Q": str(len(LIT_Q)), "FIRST5_LIT": FIRST5_LIT[0]["id"],
    "FIRST5_LITS": html.escape(", ".join(qr.literals(FIRST5_LIT[0]["question"]))),
    "BASE_DATE": BASE_DATE, "BASE_ROWS": str(BASE_ROWS), "BASE_R5": BASE_R5, "BASE_MRR": BASE_MRR, "NEW_ROWS": word(len(anchored) - BASE_ROWS),
    "ONE_G": f"{ONE_G:.3f}", "ONE_P": f"{ONE_P:.3f}", "EXP12": html.escape(EXP12), "PP01": html.escape(PP01),
    "PP01_MUST": html.escape(by_id[para_by_id["pp-01"]["of"]]["must_contain"][0]), "PP01_OF": para_by_id["pp-01"]["of"],
    "CHUNKS": f"{N:,}", "DOCS": str(DOCS), "BENCH_ROWS": "\n".join(bench_rows_html), "BENCH_OPTIONS": "".join(bench_options),
    "BENCH_N": word(len(bench)), "BENCH_SUMMARY": BENCH_SUMMARY, "JN07_Q": JN07_Q, "JN07_S": JN07_S,
    "N_NODE_TEXTS": str(N_NODE_TEXTS), "N_NODE_PAIRS": str(N_NODE_PAIRS),
    "BENCH_STATE": ("the rewrites are the model's own, recorded by step 5's cell on the author's lane" if RECORDED else
                    "the rewrites are illustrations written for this page, following the prompt's six rules, not model output; step 5's cell "
                    "records the model's own, and they replace these when the author's run is in"),
    "RESULT_GOLDEN": RESULT_GOLDEN, "RESULT_PARA": RESULT_PARA, "RESULT_CHANGE": RESULT_CHANGE,
    "COST_ROWS": "\n".join(cost_rows), "MEASURE_RS": f"{MEASURE_RS:.0f}", "RANK_RS": f"{RANK_RS:.2f}", "CALLS_RS": f"{CALLS_RS:.2f}",
    "N_RANK": str(N_RANK), "RS_REQ": f"{RANK_USD * USD_INR:.3f}", "ANSWER_MAX": f"{ANSWER_MAX_USD * USD_INR:.2f}", "N_ANSWERS": word(N_ANSWERS),
    "MAX_CONTEXT": f"{MAX_CONTEXT:,}", "MAX_ANSWER": f"{MAX_ANSWER:,}", "PER_1000": f"{PER_1000_RS:.0f}", "PER_1000_SRC": PER_1000_SRC,
    "NEXT": html.escape(NEXT),
}


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


# ------------------------------------------------------------------ the bench's script: the guard above, and the page around it
UI_JS = r"""var B = __BENCH__, N = __N__;
var root = document.getElementById('bench'); if (!root) return;
var sel = document.getElementById('rb-row'), rowOut = document.getElementById('rb-row-out'),
    mine = document.getElementById('rb-mine'), mineOut = document.getElementById('rb-mine-out');
var SAY = {rewritten: 'the index is searched with the rewrite', same: 'the model gave the question back: the question is searched',
           rejected: 'the guard refused it: the question is searched as asked', fallback: 'the call failed: the question is searched as asked'};
function noRewrite(r){ return r.outcome === 'fallback' ? '(no rewrite: ' + (r.error || 'the call failed') + ')' :
  r.outcome === 'same' ? '(the question, given back)' : '(refused: the kit keeps no refused rewrite)'; }
function esc(t){ return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
function tags(list, cls){ return list.length ? list.map(function(l){ return '<span class="rb-tag' + (cls ? ' ' + cls : '') + '">' + esc(l) + '</span>'; }).join('') : 'none'; }
function rankList(title, rank, top){
  return '<div><b>' + esc(title) + '</b>: the anchor at rank ' + (rank === null ? 'none' : rank) + ' of ' + N + '<ol>' + top.map(function(t){
    return '<li' + (t[2] ? ' class="hit"' : '') + '>' + esc(t[0]) + ' <span>' + esc(t[1]) + '</span></li>'; }).join('') + '</ol></div>'; }
function renderRow(){
  var r = B[sel.value];
  var who = r.source === 'recorded' ? 'recorded on the author\'s lane: rewrite() on the model' : 'an illustration written for this page, not model output';
  rowOut.innerHTML = '<p><b>' + esc(r.id) + '</b> &middot; ' + (r.kind === 'golden' ? 'golden row' : 'paraphrase of ' + esc(r.of)) + ' &middot; anchor ' + esc(r.anchors.join(', ')) + '</p>' +
    '<p><span class="rb-tag">question</span>' + esc(r.q) + '</p>' +
    '<p>Literals the guard holds: ' + tags(r.lits) + '</p>' +
    '<p><span class="rb-tag s">rewrite</span>' + esc(r.rw || noRewrite(r)) + ' <em>(' + who + ')</em></p>' +
    '<p>Outcome: <span class="rb-tag' + (r.outcome === 'rewritten' ? '' : ' warn') + '">' + r.outcome + '</span>' +
    (r.dropped.length ? 'dropped ' + tags(r.dropped, 'no') : '') + ' ' + SAY[r.outcome] + '</p>' +
    '<div class="rb-ranks">' + rankList('BM25 over the question', r.rank_q, r.top_q) + rankList('BM25 over the searched text', r.rank_s, r.top_s) + '</div>';
}
function renderMine(){
  var r = B[sel.value];
  if (!mine.value.trim()) { mineOut.innerHTML = '<p>Type a search query for the question above: drop a code, change a figure, or keep them all, and the guard answers as the kit would.</p>'; return; }
  var got = window.__rq.outcome(r.q, mine.value), kept = r.lits.filter(function(l){ return got.dropped.indexOf(l) < 0; }),
      added = window.__rq.dropped(mine.value, r.q);
  mineOut.innerHTML = '<p>Outcome: <span class="rb-tag' + (got.outcome === 'rewritten' ? '' : ' warn') + '">' + got.outcome + '</span>' + SAY[got.outcome] + (got.error ? ' (' + got.error + ')' : '') + '</p>' +
    (r.lits.length ? '<p>Kept: ' + tags(got.outcome === 'same' ? r.lits : kept) + (got.dropped.length ? ' Dropped: ' + tags(got.dropped, 'no') : '') + '</p>' : '<p>The question carries no literal, so the guard has nothing to refuse.</p>') +
    (added.length ? '<p>Your rewrite adds ' + tags(added, 'warn') + 'which the question does not carry. The guard does not look: only the prompt\'s rule against adding a fact stands in the way.</p>' : '') +
    '<p><span class="rb-tag s">searched</span>' + esc(got.query) + '</p><p><span class="rb-tag">reranked and answered</span>' + esc(r.q) + '</p>';
}
sel.addEventListener('change', function(){ mine.value = ''; renderRow(); renderMine(); });
mine.addEventListener('input', renderMine);
renderRow(); renderMine();
"""
UI_JS = UI_JS.replace("__BENCH__", json.dumps(bench, ensure_ascii=False, separators=(",", ":"))).replace("__N__", f"'{N:,}'")
JS = "<script>\n(function(){\n'use strict';\n" + GUARD_JS + UI_JS + "})();\n</script>\n"
assert "</script" not in GUARD_JS + UI_JS and (GUARD_JS + UI_JS).count("<div") == (GUARD_JS + UI_JS).count("</div>")

body = "".join([
    subst(fill(pb.part(LESSON, "a"))),
    setup,
    subst(fill(pb.part(LESSON, "b"))),
    subst(fill(pb.part(LESSON, "c"))),
])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: {qr.MODEL}, {qr.TIMEOUT_S:g} s, {qr.MAX_OUTPUT_TOKENS} tokens, prompt {qr.PROMPT_VERSION}, {len(RULES)} rules | golden {len(golden)} rows, "
      f"{len(anchored)} anchored ({dict(TENANTS)}), {len(LIT_ROWS)} with a literal | paraphrases {len(scored)} of {len(paraphrases)} scored, "
      f"{len(ALL_Q)} questions | baseline {BASE_DATE}: {BASE_ROWS} rows {BASE_R5}/{BASE_MRR} | node agrees on {N_NODE_TEXTS} texts and "
      f"{N_NODE_PAIRS} pairs | bench ({BENCH_SOURCE}): " + ", ".join(f"{k} {v['outcome']} {v['rank_q']}->{v['rank_s']}" for k, v in bench.items())
      + f" | runs: Rs {MEASURE_RS:.2f} ({N_RANK} rank requests Rs {RANK_RS:.2f}, calls Rs {CALLS_RS:.2f}) + {N_ANSWERS} answers <= Rs "
      f"{N_ANSWERS * ANSWER_MAX_USD * USD_INR:.2f}")
