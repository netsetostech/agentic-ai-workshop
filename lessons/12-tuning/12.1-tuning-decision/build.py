"""Build lesson 12.1 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Decide whether tuning is justified and prepare data. The kit has no decision tool: the decision is the page's rubric on
numbers the kit already produces - the live gate's report (which rows missed, and why), the generator's own events in
Cloud Logging (a draft repaired, invalid or unparsed: the grammar breaking), the price of the tunable base against the
served model (services/rag-api/cost.py's table; evals/tune.py: gemini-3.6-flash is not tunable, gemini-3.1-flash-lite
is) and the data the corpus can give. A tuned model learns the lane's HABIT - ModelDraft's JSON, [Source N] citations
with a quote, saying no - not facts, which are retrieval's job (make_trainset.py's own words). Then the data:
make_trainset.py writes one question and answer per real chunk in the served grammar, drops what the golden set could
recognise (the evidence rule and the question rule), drops any row DLP flags, writes the Gemini SFT and chat formats
and a manifest, and uploads them to the datasets bucket.
Offline: the kit's --selftest, then an audit of the committed v1 (the formats, the targets, SYSTEM, the quotes, the
handbook's rows, the golden set today, the prompt it trains against the prompt the generator serves). Live: make
eval-live with a report, the rubric over it and the logs and the price; make trainset as version v2; the frozen
manifest read back from the bucket and the files held to it.

Build-time proof: the gate's block is the kit's run_eval.live() over a stub API that misses two rows on purpose (lesson
4.2's), the rubric cell ran over that report and a week of stand-in usage rows, make trainset ran the kit's
make_trainset.py main() on a copy of the kit with Gemini, DLP and Cloud Storage stood in (lane171.py, beside this
file), and the audit and freeze cells ran on the kit's own files. The panel is make_trainset.exclude_golden with
run_eval.normalise, ported and compared with the kit's function on every committed v1 row and every question it offers
on every chunk it offers.
"""
import ast
import contextlib
import hashlib
import html
import io
import itertools
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "12.1"
title = "<title>Lesson 12.1 Decide whether tuning is justified and prepare data - a rubric, then a frozen file | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
API = "https://documind-api-NUMBER.asia-south1.run.app"
MT, TUNE, BUDGET, GEN, COST, RUN_EVAL = ("evals/make_trainset.py", "evals/tune.py", "services/rag-api/context_budget.py",
                                         "services/rag-api/generator.py", "services/rag-api/cost.py", "evals/run_eval.py")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select,.pc-in input[type=text]{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;box-sizing:border-box;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin:6px 0 4px;}
.tg-chunk{font-family:var(--mono);font-size:11.5px;line-height:1.5;max-height:9.5em;overflow:auto;white-space:pre-wrap;background:var(--bg,#f8fafc);border-radius:6px;padding:6px 8px;margin:4px 0 0;}
.tg-out{font-size:13px;line-height:1.6;}
.tg-out .pass{color:var(--teal-dark);font-weight:600;}
.tg-out .stop{color:#9a3412;font-weight:600;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
BUDGET_LINE = "        block = f\"{source_header(len(packed) + 1, c)}\\n{c.get('text') or c.get('content', '')}\""
EXCERPTS = {
    "rules": ("evals/make_trainset.py - the four rules that make the file defensible",
              block(MT, "Four rules make the file defensible", n=9)),
    "turn": ("evals/make_trainset.py - the user turn and the target: the served SYSTEM, one source, ModelDraft's JSON",
             block(MT, "def user_turn(text: str, question: str) -> str:", n=12)),
    "exclude": ("evals/make_trainset.py - exclude_golden(): the evidence rule, then the question rule, for each golden row in order",
                block(MT, '    gold = [(g["id"], _content(g["question"]), _phrases(g), g.get("tenant"),', n=25)),
    "manifest": ("evals/make_trainset.py - write(): the manifest, a sha256 per file, and the rule it states",
                 block(MT, "    manifest = {", n=14)),
    "recipe": ("Makefile - make trainset: build, scan, freeze, upload",
               block("Makefile", "trainset: guard-project", n=3)),
    "served": ("services/rag-api/context_budget.py - what the generator serves: a header line, then the chunk, for every packed source",
               block(BUDGET, BUDGET_LINE, n=1)),
    "tunable": ("evals/tune.py - what managed tuning accepts: not the model the lane serves",
                block(TUNE, 'TUNABLE = {"gemini-3.5-flash", "gemini-3.1-flash-lite"}', n=1)),
}
assert EXCERPTS["rules"][1].rstrip().endswith("frozen          the version is in the file name. A changed corpus is a new version, never an edit.")
assert EXCERPTS["turn"][1].rstrip().endswith("return json.dumps(draft, ensure_ascii=False)") and '[Source 1] {text.strip()}' in EXCERPTS["turn"][1]
assert EXCERPTS["exclude"][1].rstrip().endswith("return kept, dropped") and "inter >= 4" in EXCERPTS["exclude"][1]
assert EXCERPTS["manifest"][1].rstrip().endswith("}") and '"rule": "frozen: a changed corpus is a new version, never an edit of this file",' in EXCERPTS["manifest"][1]
assert EXCERPTS["recipe"][1].rstrip().endswith("--upload gs://$(PROJECT)-datasets/sft/ $(TRAINSET_ARGS)")
assert EXCERPTS["served"][1].strip().startswith("block = f\"{source_header(") and "3.6-flash is not tunable" in EXCERPTS["tunable"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
src = {p: (KIT / p).read_text(encoding="utf-8") for p in (MT, TUNE, BUDGET, GEN, COST, RUN_EVAL, "Makefile", "terraform/storage.tf")}
MK = src["Makefile"] + "".join(p.read_text(encoding="utf-8") for p in sorted((KIT / "mk").glob("*.mk")))
assert 'GEN_MODEL = "gemini-3.6-flash"' in src[MT] and "MIN_CHUNK_CHARS = 400" in src[MT] and "REFUSAL_EVERY = 10" in src[MT] and "OVERLAP_DROP = 0.5" in src[MT]
assert "TUNE_BASE       ?= gemini-3.1-flash-lite" in MK and "TUNE_EPOCHS     ?= 3" in MK and "TUNE_ADAPTER    ?= 4" in MK and "TENANT        ?= acme" in MK
assert "Needs google-genai and google-cloud-dlp in the shell" in MK and "$(if $(REPORT),--report $(REPORT),)" in MK
assert "A model tuned on this learns the HABIT the lane serves,\nnot facts (10.5: facts are retrieval's job)" in src[MT]
assert '"gemini-3.6-flash": (1.50, 7.50)' in src[COST] and '"gemini-3.1-flash-lite": (0.25, 1.50)' in src[COST]
assert "Versioned and never expiring" in src["terraform/storage.tf"]
# 1. the frozen rule is a comment: the default version is v1, write() opens its files for writing, the recipe passes no version, make tune reads v1
assert 'VERSION = os.environ.get("TRAINSET_VERSION", "v1")' in src[MT] and 'with open(paths[fmt], "w", encoding="utf-8", newline="\\n") as f:' in src[MT]
WRITE_FN = src[MT].split("def write(", 1)[1].split("\ndef upload(", 1)[0]
assert "exists" not in WRITE_FN and "--version" not in EXCERPTS["recipe"][1] and "documind_sft_$${VERSION:-v1}.vertex.jsonl" in MK
# 2. the training prompt is not the served prompt: one source with no header, and SYSTEM twice (the generator sends it once, in the prompt)
assert 'return f"{SYSTEM}\\n\\nContext:\\n[Source 1] {text.strip()}\\n\\nQuestion: {question.strip()}"' in src[MT]
assert '"systemInstruction": {"role": "system", "parts": [{"text": SYSTEM}]}' in src[MT] and "system_instruction" not in src[GEN]
assert 'prompt = f"{SYSTEM}{_dated_rule(packed)}\\n\\nContext:\\n{context}\\n\\nQuestion: {query}"' in src[GEN]
# 3. nothing checks a quote against its chunk, or its length against SYSTEM's rule
ASK = src[MT].split("def ask_pairs(", 1)[1].split("\n# ---", 1)[0]
assert "copied \"\n                      \"exactly, at most twenty-five words)" in ASK and "in c[\"text\"]" not in src[MT] and "split())" not in src[MT].split("def target(", 1)[1].split("def _pair_schema", 1)[0]
assert "google-genai==" in (KIT / "services/ingest/requirements.txt").read_text(encoding="utf-8") and "google-cloud-dlp==" in (KIT / "services/ingest/requirements.txt").read_text(encoding="utf-8")
assert "it bills per training token and nothing else on the lane triggers it" in src[TUNE] and "Tuning is REGIONAL (us-central1)" in src[TUNE]
assert "--batch writes the same requests as a Batch API file (10.3: half price, no rate limit)" in src[MT]
# 4. the guard the code names does not exist
assert "tools/check_auth_wiring.py holds the two equal" in src[MT] and not (ROOT / "tools/check_auth_wiring.py").exists() and not (KIT / "tools/check_auth_wiring.py").exists()
# 5. the targets never mark a source: SYSTEM's rule 2 asks for [N], the UI turns each [N] into a pill, the gate counts only the citations list
CITES = (KIT / "services/frontend/citations.py").read_text(encoding="utf-8")
assert "2. Cite using [N] where N is the chunk number. Multiple chunks: [1,2]." in src[MT] and "html = _CITE.sub(_pill, answer)" in CITES and "_CITE = re.compile(" in CITES
assert 'draft = {"answer": answer.strip(),' in src[MT] and '"citations": ([{"source": 1, "quote": quote.strip()[:200]}] if answerable and quote else []),' in src[MT]
assert 'else:\n                    valid = False\n                    rec["why"] = "answered without a citation"' in src[RUN_EVAL] and "\\[\\d" not in src[RUN_EVAL] and "_CITE" not in src[RUN_EVAL]
# the rubric's habit misses are run_eval's own words; the pair call thinks LOW
assert 'rec["why"] = "answered, should refuse"' in src[RUN_EVAL] and 'rec["outcome"] = "malformed"' in src[RUN_EVAL]
assert 'thinking_config=types.ThinkingConfig(thinking_level="LOW")' in src[MT]
# step 7's v3, --style helpdesk: the plain faults above fixed in functions of its own, the plain ones left as they are
HD = src[MT].split("# ----------------------------------------------------------------------------- the helpdesk style", 1)[1].split("\n# ---", 1)[0]
assert 'HELPDESK_TEACHER = "gemini-3.1-pro-preview"' in HD and "DISTRACTORS = 2" in HD and "HINGLISH_EVERY = 2" in HD and "VALIDATION_EVERY = 10" in HD
assert "from context_budget import pack_chunks" in HD and 'return f"{SYSTEM}\\n\\nContext:\\n{context}\\n\\nQuestion: {question.strip()}"' in HD
assert 'return {"contents": [{"role": "user", "parts": [{"text": r["prompt"]}]}, {"role": "model", "parts": [{"text": r["target"]}]}]}' in HD
assert "systemInstruction" not in HD and "and _flat(quote) in _flat(passage)" in HD and "len(quote.split()) <= 25" in HD
assert 'texts = list(dict.fromkeys(t for r in rows for t in (r["question"], r["answer"], *r["context_texts"])))' in HD
assert 'filler = {c["chunk_id"] for c in everything if "#GEN-" in c["chunk_id"]}' in HD and "rows, dropped_golden = drop_orphan_twins(*exclude_golden(rows, golden))" in HD
assert f' [{{n}}].\\n**Clause:** {{where}}"' in HD and '"gemini-3.1-pro-preview": (2.00, 12.00)' in src[COST]

# ------------------------------------------------------------------ the committed v1, audited with the kit's own functions
sys.path[:0] = [str(KIT), str(KIT / "evals")]
import make_trainset as mt  # noqa: E402
import run_eval as rv  # noqa: E402
from shared import documind_corpus as dc  # noqa: E402
GOLDEN = [json.loads(line) for line in (KIT / "evals/golden.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
CHUNKS = mt.load_chunks("acme")
BY_TEXT = {c["text"].strip(): c for c in CHUNKS}
V1 = [json.loads(line) for line in (KIT / "evals/sft/documind_sft_v1.vertex.jsonl").read_text(encoding="utf-8").splitlines()]
M1 = json.loads((KIT / "evals/sft/documind_sft_v1.manifest.json").read_text(encoding="utf-8"))
V1ROWS = []
for v in V1:
    user = v["contents"][0]["parts"][0]["text"]
    text = user.split("[Source 1] ", 1)[1].rsplit("\n\nQuestion: ", 1)[0]
    c = BY_TEXT[text.strip()]
    V1ROWS.append({"chunk_id": c["chunk_id"], "source_uri": c["source_uri"], "text": text, "question": user.rsplit("\n\nQuestion: ", 1)[1],
                   "draft": json.loads(v["contents"][1]["parts"][0]["text"])})
flat = lambda s: re.sub(r"\s+", " ", s).strip()  # noqa: E731
Q1 = [(r["text"], r["draft"]["citations"][0]["quote"]) for r in V1ROWS if r["draft"]["citations"]]
N_Q1, N_EXACT, N_FLAT = len(Q1), sum(q in t for t, q in Q1), sum(flat(q) in flat(t) for t, q in Q1)
N_LONG, MAX_WORDS = sum(len(q.split()) > 25 for _, q in Q1), max(len(q.split()) for _, q in Q1)
N_GEN1 = sum("#GEN-" in r["chunk_id"] for r in V1ROWS)
HB = next(d for d in dc.load_documents("acme", str(KIT / "evals"), PROJ) if d["slug"] == "hr_policy_2026")
HB_CHUNKS = dc.chunk_document(HB, "acme")
HB_SHORT = [c["chunk_id"].split("#", 1)[1] for c in HB_CHUNKS if len(c["text"].strip()) < mt.MIN_CHUNK_CHARS]
N_HB_GEN = sum("#GEN-" in c["chunk_id"] for c in HB_CHUNKS)
assert (M1["rows"], M1["refusals"], len(V1ROWS), N_Q1) == (317, 30, 317, 287) and not mt.exclude_golden(V1ROWS, GOLDEN)[1]
assert (N_EXACT, N_FLAT, N_LONG, MAX_WORDS) == (22, 282, 17, 33), (N_EXACT, N_FLAT, N_LONG, MAX_WORDS)
assert len(HB_SHORT) == 11 and "NP-03" in HB_SHORT and N_HB_GEN == 272 and len(CHUNKS) == 1542, (HB_SHORT, N_HB_GEN, len(CHUNKS))
assert len(HB_CHUNKS) == N_HB_GEN + len(HB_SHORT) and all("#GEN-" not in f"#{s}" for s in HB_SHORT)   # the handbook: its real clauses, all short, and the GEN sections
assert "preamble" in HB_SHORT                                                   # ten clauses and the preamble
GEN_TOPICS, GEN_BODIES = set(), set()                                          # the GEN sections: one paragraph, its topic and number swapped
for c in HB_CHUNKS:
    if "#GEN-" in c["chunk_id"]:
        head, rest = c["text"].strip().split("\n", 1)
        topic = head.split("—", 1)[1].strip()
        GEN_TOPICS.add(topic)
        GEN_BODIES.add(re.sub(r"GEN-\d+", "GEN-N", re.sub(r"\s+", " ", rest)).replace(topic.lower(), "TOPIC"))
assert len(GEN_TOPICS) == 18 and len(GEN_BODIES) == 1, (len(GEN_TOPICS), len(GEN_BODIES))
assert ('SYSTEM = """' + mt.SYSTEM + '"""') in src[GEN]
UI_CITE = re.search(r'_CITE = re\.compile\(r"(.+?)"\)', CITES).group(1)          # the pattern the UI turns into pills
MARKED1 = sum(bool(re.search(UI_CITE, r["draft"]["answer"])) for r in V1ROWS if r["draft"]["answerable"])
assert MARKED1 == 0, MARKED1
# 6. the PII scan reads the question and the answer, never the chunk the user turn carries: acme's invoice carries a PAN,
# which the default sample of 300 passes by and a sample of 1,000 takes
assert 'texts = [x for r in rows for x in (r["question"], r["answer"])]' in src[MT] and '{"name": "INDIA_PAN_INDIVIDUAL"}' in (KIT / "shared/pii.py").read_text(encoding="utf-8")
INV = next(c for c in CHUNKS if c["chunk_id"] == "acme:inv_2026_0412#p1-0")
assert re.search(r"\b[A-Z]{3}P[A-Z][0-9]{4}[A-Z]\b", INV["text"]) and INV not in mt.sample(CHUNKS, 300) and INV in mt.sample(CHUNKS, 1000)
assert re.search(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][0-9A-Z]Z[0-9A-Z]\b", INV["text"]) and '{"name": "INDIA_GST_INDIVIDUAL"}' in (KIT / "shared/pii.py").read_text(encoding="utf-8")
# step 7's reasons, in the kit's own words
assert "Not the logs: sink.tf keeps question and answer out of BigQuery\non purpose. Not the answer cache: on the lane it holds the golden questions every eval run asked" in src[MT]
assert "the first selftest passed 'which region's revenue declined'" in src[MT] and '"""Drop, never rewrite: a row that carries PII is not worth a redacted version' in src[MT]
assert "Weights cannot be filtered per tenant afterwards." in src[MT] and "so 10.1 and 10.5 tune on the same rows" in src[MT]
assert "--dataset gs://$(PROJECT)-datasets/sft/documind_sft_$${VERSION:-v1}.vertex.jsonl" in MK and "twenty-minute make trainset" in MK
assert 1.5e6 < sum((KIT / "evals/sft" / f"documind_sft_v1.{x}").stat().st_size for x in ("vertex.jsonl", "chat.jsonl", "manifest.json")) < 2.5e6
# what make trainset's 300 calls cost at cost.py's flash rates: each prompt's characters over four, and an answer the size of v1's
PROMPT_HEAD = re.search(r'"text": "(Read this passage.*?Passage:\\n)" \+ c\["text"\]\[:2400\]', src[MT]).group(1)
SAMPLED = mt.sample(CHUNKS, 300)
# the sample is sorted and strided: while the corpus is unchanged, v2's chunks are v1's (v1's 287 are today's 300 less its 13 dropped)
assert "Deterministic and spread over every document: sorted by id, then evenly strided." in src[MT]
V1_IDS = {r["chunk_id"] for r in V1ROWS}
assert V1_IDS <= {c["chunk_id"] for c in SAMPLED} and len(V1_IDS) == 300 - M1["dropped_golden_overlap"], len(V1_IDS)
TOK_IN = sum(len(PROMPT_HEAD) + len(c["text"][:2400]) for c in SAMPLED) / 4
ANS = [r for r in V1ROWS if r["draft"]["answerable"]]
TOK_OUT = len(SAMPLED) * (sum(len(r["question"]) + len(r["draft"]["answer"]) + len(r["draft"]["citations"][0]["quote"]) for r in ANS) / len(ANS) / 4 + 40)
TRAIN_RS = (TOK_IN * 1.50 + TOK_OUT * 7.50) / 1e6 * 85
assert 30 < TRAIN_RS < 120, TRAIN_RS

# ------------------------------------------------------------------ step 3: the kit's rules, and the v1 it ships, audited (offline)
AUDIT_PY = """import json, re, sys
sys.path[:0] = [".", "evals", "services/rag-api"]
import make_trainset as mt                                    # the kit's rules and its corpus loader
from context_budget import source_header                    # the header the generator serves above each chunk
from shared.documind_schemas import ModelDraft
V = "evals/sft/documind_sft_v1"
m = json.load(open(V + ".manifest.json", encoding="utf-8"))
vertex = [json.loads(l) for l in open(V + ".vertex.jsonl", encoding="utf-8")]
chat = [json.loads(l) for l in open(V + ".chat.jsonl", encoding="utf-8")]
print(f"the manifest: {m['version']}, built {m['built_at']}, {m['rows']} rows ({m['refusals']} refusals) from "
      f"{len(m['documents'])} documents; dropped {m['dropped_golden_overlap']} for the golden set, {m['dropped_pii']} for PII")
same = all(c["messages"][2]["content"] == v["contents"][1]["parts"][0]["text"] for v, c in zip(vertex, chat))
drafts = [ModelDraft.model_validate_json(v["contents"][1]["parts"][0]["text"]) for v in vertex]
system_same = ('SYSTEM = \"\"\"' + mt.SYSTEM + '\"\"\"') in open("services/rag-api/generator.py", encoding="utf-8").read()
print(f"the two formats agree row by row: {same}; targets that parse as ModelDraft: {len(drafts)} of {len(vertex)}; "
      f"SYSTEM is the generator's: {system_same}")
chunks = {c["text"].strip(): c for c in mt.load_chunks("acme")}
rows = []
for v, d in zip(vertex, drafts):
    user = v["contents"][0]["parts"][0]["text"]
    text = user.split("[Source 1] ", 1)[1].rsplit("\\n\\nQuestion: ", 1)[0]
    c = chunks[text.strip()]
    rows.append({"chunk_id": c["chunk_id"], "source_uri": c["source_uri"], "text": text, "draft": d,
                 "question": user.rsplit("\\n\\nQuestion: ", 1)[1]})
quotes = [(r["text"], r["draft"].citations[0].quote) for r in rows if r["draft"].citations]
flat = lambda s: re.sub(r"\\s+", " ", s).strip()
print(f"quotes: {len(quotes)}; in their chunk as written: {sum(q in t for t, q in quotes)}, once line breaks are spaces: "
      f"{sum(flat(q) in flat(t) for t, q in quotes)}; over twenty-five words: {sum(len(q.split()) > 25 for _, q in quotes)}")
said = [r["draft"].answer for r in rows if r["draft"].answerable]
marked = sum(bool(re.search(r"\\[(\\d+(?:\\s*,\\s*\\d+)*)\\]", a)) for a in said)   # the UI's own pattern: [1], [1,2]
print(f"answers that mark their source with [N], as SYSTEM's rule 2 asks: {marked} of {len(said)}")
print(f"rows from the handbook: {sum(r['chunk_id'].startswith('acme:hr_policy_2026') for r in rows)}, every one from a generated "
      f"GEN- section: its clauses are all under {mt.MIN_CHUNK_CHARS} characters")
golden = [json.loads(l) for l in open("evals/golden.jsonl", encoding="utf-8") if l.strip()]
print(f"today's golden set ({len(golden)} rows) would drop {len(mt.exclude_golden(rows, golden)[1])} of v1's rows")
r = next(x for x in rows if x["text"][:1].isupper())             # a chunk that starts at a word
print("the prompt v1 trains on shows a chunk as: " + repr(("[Source 1] " + r["text"])[:64]) + "...")
print("the prompt the generator serves shows it as: " + repr((source_header(1, {"source_uri": r["source_uri"]}) + "\\n" + r["text"])[:64]) + "...")"""
CELLS = {"audit": "python evals/make_trainset.py --selftest\n" + "python - <<'PY'\n" + AUDIT_PY + "\nPY"}
T = Path(tempfile.mkdtemp(prefix="lesson171-"))
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ, "HOME": str(T),
       "USERPROFILE": str(T), "GOOGLE_CLOUD_PROJECT": PROJ, "LANE171_GCS": str(T / "gcs.json"), "LANE171_LOGS": str(T / "logs.json"),
       "PYTHONPATH": str(T)}
for k in [k for k in ENV if k.startswith(("TRAINSET_", "DOCUMIND_"))]:
    ENV.pop(k)
# the stand-in Gemini names a passage the way a reader would: its document's title and, where it has one, its heading
DOC_TITLES = {"cgst_act_2017": "the CGST Act, 2017", "hr_policy_2026": "ACME's HR handbook", "code_on_social_security_2020": "the Code on Social Security, 2020",
              "osh_code_2020": "the OSH Code, 2020", "industrial_relations_code_2020": "the Industrial Relations Code, 2020", "it_act_2000": "the IT Act, 2000",
              "code_on_wages_2019": "the Code on Wages, 2019", "payment_of_bonus_act_1965": "the Payment of Bonus Act, 1965", "dpdp_act_2023": "the DPDP Act, 2023",
              "labour_codes_compliance_handbook": "the labour codes compliance handbook", "payment_of_gratuity_act_1972": "the Payment of Gratuity Act, 1972",
              "maternity_benefit_act_1961": "the Maternity Benefit Act, 1961", "maternity_benefit_amendment_act_2017": "the Maternity Benefit (Amendment) Act, 2017",
              "inv_2026_0412": "invoice INV-2026-0412", "townhall_2026_q1": "the FY2026 town hall transcript"}
SECTION = re.compile(r"(?:^|\s)(\d{1,3}[A-Z]?)\.\s+([A-Z][a-z][A-Za-z ,'()]{2,60}?)\.?\s*[—–]")


def heading_of(c: dict) -> str:
    first = c["text"].strip().splitlines()[0]
    m = re.match(r"GEN-\d+\s*[—–-]\s*(.+)$", first)
    if m:
        return m.group(1).strip().lower()
    m = SECTION.search(c["text"])
    if m:
        return f"{m.group(2).strip().lower()} (section {m.group(1)})"
    low = c["text"].lower()                                              # else the first subject the passage names
    hits = sorted((low.find(t), t) for t in TERMS if low.find(t) >= 0)
    if not hits:
        return "its scope"
    return ("the " + hits[0][1]) if hits[0][1] in ("employer", "establishment", "appropriate government", "inspector-cum-facilitator",
                                                   "certifying authority", "data fiduciary", "safety committee", "social security fund") else hits[0][1]


TERMS = ["input tax credit", "composition levy", "registration", "tax invoice", "returns", "refund", "gratuity", "bonus", "minimum wages",
         "overtime", "trade union", "strike", "lay-off", "retrenchment", "standing orders", "grievance redressal", "maternity benefit", "creche",
         "provident fund", "employees' state insurance", "social security fund", "gig workers", "platform workers", "safety committee",
         "working hours", "annual leave", "contract labour", "migrant workers", "inspector-cum-facilitator", "appropriate government",
         "penalty", "offences", "appeal", "personal data", "data fiduciary", "consent", "electronic record", "digital signature",
         "certifying authority", "wages", "employer", "establishment"]


(T / "titles.json").write_text(json.dumps({hashlib.sha256(c["text"][:2400].encode("utf-8")).hexdigest():
                                            {"title": DOC_TITLES[c["chunk_id"].split(":", 1)[1].split("#", 1)[0]], "heading": heading_of(c)}
                                            for c in CHUNKS}), encoding="utf-8")
ENV["LANE171_TITLES"] = str(T / "titles.json")


def run(cmd: list, cwd: Path, stdin: str | None = None, env: dict | None = None) -> str:
    r = subprocess.run(cmd, input=stdin, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), (cmd[:3], r.returncode, r.stdout[-1500:], r.stderr[-3000:])
    return r.stdout


SELFTEST = run([sys.executable, "evals/make_trainset.py", "--selftest"], KIT)
OUT = {"audit": SELFTEST + run([sys.executable, "-"], KIT, AUDIT_PY)}
AU = OUT["audit"]
assert AU.startswith("selftest: the evidence rule dropped jn-06's chunk") and "317 rows (30 refusals) from 12 documents" in AU, AU
assert "the two formats agree row by row: True; targets that parse as ModelDraft: 317 of 317; SYSTEM is the generator's: True" in AU, AU
assert f"quotes: {N_Q1}; in their chunk as written: {N_EXACT}, once line breaks are spaces: {N_FLAT}; over twenty-five words: {N_LONG}" in AU, AU
assert f"rows from the handbook: {N_GEN1}, every one from a generated GEN- section" in AU and "would drop 0 of v1's rows" in AU, AU
assert f"answers that mark their source with [N], as SYSTEM's rule 2 asks: 0 of {N_Q1}" in AU, AU
assert "the prompt v1 trains on shows a chunk as: '[Source 1] " in AU and "the prompt the generator serves shows it as: '[Source 1] " in AU and "\\n" in AU, AU

# ------------------------------------------------------------------ step 4: the evidence - the gate's report, the grammar, the price
for k in ("DOCUMIND_ID_TOKEN", "DOCUMIND_OUTSIDER_TOKEN", "DOCUMIND_USER_EMAIL", "DOCUMIND_OUTSIDER_EMAIL"):
    os.environ.pop(k, None)
OUTSIDER = "outsider@not-a-tenant.invalid"
NOFIG = {"jn-06": "EMEA revenue fell in FY2026 [1]."}


def reply(row: dict, outcome: str) -> tuple:
    """Lesson 4.2's stub: each golden row answered the way a scenario says."""
    t, mc = row["tenant"], row.get("must_contain", [])

    def cite(tenant=t, kind=None):
        return {"chunk_id": f"{tenant}:lesson#0", "source_uri": f"gs://lesson/{tenant}/doc.md", "quote": mc[0] if mc else "lesson",
                "kind": kind or row.get("must_cite_kind") or "text"}

    def body(answer, cites, answerable, conf="high"):
        return 200, {"answer": answer, "citations": cites, "answerable": answerable, "confidence": conf, "model": "gemini-3.6-flash",
                     "backend": "vertex", "cache_hit": "none", "stages": {"retrieve_ms": 400, "rerank_ms": 200, "generate_ms": 1500, "pool": 12}}
    fig = " and ".join(mc)
    if row["answerable"]:
        table = {"ok": (f"{fig} [1].", [cite()], True), "refused": ("The documents do not say.", [], False),
                 "nofig": (NOFIG.get(row["id"], "The documents cover this [1]."), [cite()], True)}
    else:
        table = {"ok": ("The documents do not say.", [], False)}
    answer, cites, answerable = table[outcome]
    return body(answer, cites, answerable, "high" if answerable else "low")


def stub_ask(scenario: dict):
    member = [0]

    def ask(api_url, question, tenant, email, token, retries=1):
        if email == OUTSIDER:
            return 403, {}, 120
        row = GOLDEN[member[0] % len(GOLDEN)]
        member[0] += 1
        assert row["question"] == question and row["tenant"] == tenant, (row["id"], question)
        status, b = reply(row, scenario.get(row["id"], "ok"))
        return status, b, 1000
    return ask


MISSES = {"lk-27": "refused", "jn-06": "nofig"}                          # lesson 4.2's two misses: both knowledge
rv.ask = stub_ask(MISSES)
rv.fetch_current_shas = lambda *a, **k: set()
REPORT = T / "gate171.json"
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    rc = rv.live(API, report=str(REPORT))
assert rc == 0, rc


def mask(text: str) -> str:
    out = []
    for line in text.splitlines():
        if line.startswith(("  latency ms", "  retrieve_ms", "  rerank_ms", "  generate_ms", "  pool")):
            line = re.sub(r"(p50|p95|avg)\s+[\d.]+", lambda m: f"{m.group(1)}   ...", line)
            line = re.sub(r"semantic cache hits \d+", "semantic cache hits ...", line)
        if "[info] quote_support_rate" in line:
            line = re.sub(r"\d+\.\d%", "  ...", line)
        out.append(line.replace(str(REPORT), "/home/YOU/gate171.json"))
    return "\n".join(out) + "\n"


CELLS["gate"] = 'make eval-live PROJECT="$PROJECT" REPORT="$HOME/gate171.json"'
OUT["gate"] = f">> {API}\n== eval gate: LIVE ==\n" + mask(buf.getvalue())
assert "rows that cost a point (2):" in OUT["gate"] and "All thresholds met." in OUT["gate"] and "report: /home/YOU/gate171.json" in OUT["gate"], OUT["gate"][-900:]

# a week of the lane's usage rows, and the generator's own events, as Cloud Logging holds them
rnd = random.Random(171)
NOW = "2026-09-24T08:30:00+00:00"
entries = []
from datetime import datetime, timedelta, timezone  # noqa: E402
t0 = datetime.fromisoformat(NOW)
for i in range(460):
    at = t0 - timedelta(minutes=rnd.randint(10, 60 * 24 * 9))
    event = "stream" if rnd.random() < 0.45 else "query"
    entries.append({"timestamp": at.isoformat().replace("+00:00", "Z"), "resource": {"type": "cloud_run_revision", "labels": {"service_name": "documind-api"}},
                    "jsonPayload": {"event": event, "tenant": rnd.choice(["acme", "acme", "acme", "zeta", "globex"]), "model": "gemini-3.6-flash",
                                    "tokens_in": max(900, int(rnd.gauss(7400, 900))), "tokens_out": max(40, int(rnd.gauss(210, 60)))}})
for days, event in ((2.1, "generation_repaired"), (8.5, "generation_repaired")):
    at = t0 - timedelta(days=days)
    entries.append({"timestamp": at.isoformat().replace("+00:00", "Z"), "resource": {"type": "cloud_run_revision", "labels": {"service_name": "documind-api"}},
                    "jsonPayload": {"event": event, "problems": ["citations.0.quote: String should have at most 200 characters"]}})
(T / "logs.json").write_text(json.dumps({"entries": entries}), encoding="utf-8")
shutil.copy(HERE / "lane171.py", T / "lane171.py")

DECIDE_PY = """import ast, datetime as dt, json, os, subprocess, sys
sys.path[:0] = [".", "evals"]
P = os.environ["PROJECT"]
rep = json.load(open(os.path.expanduser("~/gate171.json"), encoding="utf-8"))
HABIT = ("answered without a citation", "answered, should refuse")     # the citation and the refusal: what the rows teach
failed = [r for r in rep["records"] if not r["pass"]]
habit = [r for r in failed if r["why"].startswith(HABIT) or r["outcome"] == "malformed"]
print(f"1. the gate: {rep['rows']} rows, {len(failed)} missed")
for r in failed:
    kind = "habit" if r in habit else "knowledge (retrieval, the corpus, or the row)"
    print(f"   {r['id']:6} {r['shape']:8} {r['why'][:44]:44} -> {kind}")
since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")


def logged(event, limit=5000):                                # the API's own lines, from Cloud Logging
    flt = (f'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" '
           f'AND jsonPayload.event="{event}" AND timestamp>="{since}"')
    return json.loads(subprocess.run(["gcloud", "logging", "read", flt, f"--project={P}", "--format=json", f"--limit={limit}"],
                                     capture_output=True, text=True, check=True).stdout)


answers = logged("query") + logged("stream")
broke = {e: len(logged(e, 500)) for e in ("generation_repaired", "generation_invalid", "generation_unparsed")}
rate = sum(broke.values()) / max(len(answers), 1)
print(f"2. the grammar, last 7 days: {broke['generation_repaired']} repaired, {broke['generation_invalid']} invalid, "
      f"{broke['generation_unparsed']} unparsed, in {len(answers)} answers ({100 * rate:.1f}%)")
tree = ast.parse(open("services/rag-api/cost.py", encoding="utf-8").read())
PRICE = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "FALLBACK")
tin = sum(int(e["jsonPayload"].get("tokens_in") or 0) for e in answers) / max(len(answers), 1)
tout = sum(int(e["jsonPayload"].get("tokens_out") or 0) for e in answers) / max(len(answers), 1)
month = len(answers) * 30 / 7
print(f"3. the price at this lane's tokens ({tin:,.0f} in and {tout:,.0f} out an answer, {month:,.0f} answers a month):")
TUNED = 1.5                  # Google's pricing page: a tuned Gemini 3 endpoint predicts at 1.5 times its base (cost.py says 1)
cost = {}
for model, name, factor in (("gemini-3.6-flash", "gemini-3.6-flash", 1.0), ("gemini-3.1-flash-lite", "tuned flash-lite, 1.5 x", TUNED)):
    usd_in, usd_out = PRICE[model]                            # cost.py's table: USD a million tokens
    each = (tin * usd_in + tout * usd_out) * factor / 1e6 * 85
    cost[model] = each * month
    print(f"   {name:24} Rs {each:.2f} an answer, Rs {cost[model]:,.0f} a month")
import make_trainset as mt
print(f"4. the data: {len(mt.load_chunks('acme')):,} chunks of {mt.MIN_CHUNK_CHARS} characters or more in acme's corpus mirrors")
saving = cost["gemini-3.6-flash"] - cost["gemini-3.1-flash-lite"]
if habit or rate >= 0.01:
    print("verdict: tune for quality - the misses are the habit the training rows teach")
elif saving > 0:
    print(f"verdict: not for quality - the misses are knowledge, and the grammar holds.\\n"
          f"         for price, only as an experiment: gemini-3.6-flash cannot be tuned; a tuned gemini-3.1-flash-lite would save\\n"
          f"         Rs {saving:,.0f} a month at this traffic, if it passes the same gate (lesson 12.3)")
else:
    print("verdict: do not tune")"""
CELLS["decide"] = "python - <<'PY'\n" + DECIDE_PY + "\nPY"
OUT["decide"] = run([sys.executable, "-"], KIT, "import lane171\nlane171.freeze()\nlane171.fake_cli()\n" + DECIDE_PY, {"LANE171_NOW": NOW})
DE = OUT["decide"]
assert "1. the gate: 65 rows, 2 missed" in DE and DE.count("-> knowledge (retrieval, the corpus, or the row)") == 2 and "-> habit" not in DE, DE
assert "2. the grammar, last 7 days: 1 repaired, 0 invalid, 0 unparsed, in " in DE and "verdict: not for quality" in DE, DE
assert "4. the data: 1,542 chunks of 400 characters or more in acme's corpus mirrors" in DE, DE
assert "in 360 answers (0.3%)" in DE and "Rs 1.08 an answer" in DE and "tuned flash-lite, 1.5 x  Rs 0.28 an answer" in DE, DE
# a tuned endpoint's price: cost.py bills it at its base's rate; Google's pricing page (checked 24 September 2026) says 1.5 times
assert "A tuned model (10.1) is an endpoint path, billed at its BASE model's rate: RAG_MODEL_BASE names it." in src[COST]
assert 'model = os.environ.get("RAG_MODEL_BASE") or "gemini-3.6-flash"' in src[COST]
assert 'cost = cost_usd if cost_usd is not None else price(model, ans_tokens_in, ans_tokens_out, cached)["usd"]' in (KIT / "services/rag-api/main.py").read_text(encoding="utf-8")
assert "SUM(CAST(jsonPayload.cost_usd AS FLOAT64))" in (KIT / "terraform/sql/tenant_daily.sql").read_text(encoding="utf-8")
assert 'a["usd"] += float(r.get("cost_usd") or 0.0)' in (KIT / "evals/usage_rows.py").read_text(encoding="utf-8") and "evals/usage_rows.py" in MK
SAVING = re.search(r"would save\n         Rs ([\d,]+) a month", DE).group(1)
assert "jn-06  join      acme    answered without ['EMEA', '11.4']" in OUT["gate"] and "lk-27  lookup    acme    REFUSED" in OUT["gate"]
assert next(g for g in GOLDEN if g["id"] == "lk-27")["answerable"] and "CGST Act" in next(g for g in GOLDEN if g["id"] == "lk-27")["question"]

# ------------------------------------------------------------------ step 5: make trainset, as version v2 (the kit's main(), on a copy of the kit)
K2 = T / "kit"
shutil.copytree(KIT / "evals", K2 / "evals", ignore=shutil.ignore_patterns("__pycache__", "reports"))
shutil.copytree(KIT / "shared", K2 / "shared", ignore=shutil.ignore_patterns("__pycache__"))
RECIPE = MK[MK.index("\ntrainset: guard-project\n") + 1:].split("\n\n", 1)[0].split("\n", 1)[1]
ECHO = (RECIPE.replace("\t", "").replace("$(PY)", "python").replace("$(PROJECT)", PROJ).replace("$(TENANT)", "acme").replace("$$", "$")
        .replace("$(TRAINSET_ARGS)", "--version v2") + "\n")
assert ECHO == f"python evals/make_trainset.py --project {PROJ} --tenant acme --rows ${{ROWS:-300}} \\\n  --upload gs://{PROJ}-datasets/sft/ --version v2\n", ECHO
REQ = (KIT / "services/ingest/requirements.txt").read_text(encoding="utf-8")
PINS = [re.search(rf"^{p}==[\d.]+$", REQ, re.M).group(0) for p in ("google-genai", "google-cloud-dlp")]
# The 429 box (24 September 2026): the pin makes one attempt unless the client carries retry options, and ask_pairs's now do
assert "http_options=types.HttpOptions(retry_options=types.HttpRetryOptions(**RETRY))" in ASK and "automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)" in ASK
assert mt.RETRY["http_status_codes"] == [408, 429, 500, 502, 503, 504] and mt.RETRY["initial_delay"] == 2.0 and mt.RETRY["max_delay"] == 60.0
assert "if e.code not in RETRY[\"http_status_codes\"]:\n                raise" in ASK and "nothing written. Run it again later." in ASK
WAIT_S = sum(min(mt.RETRY["initial_delay"] * 2 ** k, mt.RETRY["max_delay"]) for k in range(mt.RETRY["attempts"] - 1))
assert 170 <= WAIT_S <= 190 and PINS[0] == "google-genai==2.22.0", (WAIT_S, PINS)
CELLS["trainset"] = (f"python -m pip install -q {' '.join(PINS)}   # the ingest image's pins: the model that writes the rows, the PII scan\n"
                     'make trainset PROJECT="$PROJECT" TRAINSET_ARGS="--version v2"     # v1 is the kit\'s own file: yours is v2')
TRAIN_PY = ("import lane171, runpy, sys\nlane171.freeze()\nsys.path[:0] = ['.']\nlane171.install()\n"
            f"sys.argv = ['make_trainset.py', '--project', {PROJ!r}, '--tenant', 'acme', '--rows', '300', '--upload', 'gs://{PROJ}-datasets/sft/', '--version', 'v2']\n"
            "try:\n    runpy.run_path('evals/make_trainset.py', run_name='__main__')\nexcept SystemExit as e:\n    assert not e.code, e.code\n")
trained = run([sys.executable, "-"], K2, TRAIN_PY, {"LANE171_NOW": "2026-09-24T09:10:00+00:00"})
OUT["trainset"] = ECHO + trained.replace(str(K2 / "evals" / "sft"), "/home/YOU/deploy_module_rag/evals/sft").replace("\\", "/")
TR = OUT["trainset"]
M2 = json.loads((K2 / "evals/sft/documind_sft_v2.manifest.json").read_text(encoding="utf-8"))
assert "  300 chunks sampled from acme's corpus mirrors" in TR and f"  {M2['rows']} rows ({M2['refusals']} refusals) from {len(M2['documents'])} documents" in TR, TR
assert TR.count(f"  uploaded gs://{PROJ}-datasets/sft/documind_sft_v2.") == 3 and "review the rows before you commit them" in TR, TR
assert f"dropped {M2['dropped_golden_overlap']} for golden overlap [" in TR and "] and 0 by the PII scan" in TR and M1["refusals"] == 30, TR
assert M2["version"] == "v2" and M2["built_at"] == "2026-09-24" and M2["files"]["vertex"]["path"] == "evals/sft/documind_sft_v2.vertex.jsonl", M2

FREEZE_PY = """import hashlib, json, os, re, sys
from google.cloud import storage
sys.path[:0] = [".", "evals"]
import make_trainset as mt
P = os.environ["PROJECT"]
bucket = storage.Client(project=P).bucket(f"{P}-datasets")
m = json.loads(bucket.blob("sft/documind_sft_v2.manifest.json").download_as_text())
print(f"the frozen manifest, from gs://{P}-datasets/sft/: {m['version']}, built {m['built_at']}, {m['rows']} rows "
      f"({m['refusals']} refusals) from {len(m['documents'])} documents; generator {m['generator']}")
print(f"  dropped {m['dropped_golden_overlap']} for the golden set {m['dropped_golden_by_rule']} "
      f"({', '.join(m['dropped_golden_ids']) or 'none'}), {m['dropped_pii']} for PII")
for fmt, f in m["files"].items():
    data = bucket.blob("sft/" + os.path.basename(f["path"])).download_as_bytes()
    same = hashlib.sha256(data).hexdigest() == f["sha256"]
    print(f"  {fmt:6} {os.path.basename(f['path'])}: {len(data.splitlines())} rows, sha256 {'as the manifest says' if same else 'DIFFERS FROM THE MANIFEST'}")
chunks = {c["text"].strip(): c for c in mt.load_chunks(m["tenant"])}
rows = []
for line in open("evals/sft/documind_sft_v2.vertex.jsonl", encoding="utf-8"):
    v = json.loads(line)
    user = v["contents"][0]["parts"][0]["text"]
    text = user.split("[Source 1] ", 1)[1].rsplit("\\n\\nQuestion: ", 1)[0]
    c = chunks[text.strip()]
    rows.append({"chunk_id": c["chunk_id"], "source_uri": c["source_uri"], "text": text,
                 "question": user.rsplit("\\n\\nQuestion: ", 1)[1], "draft": json.loads(v["contents"][1]["parts"][0]["text"])})
golden = [json.loads(l) for l in open("evals/golden.jsonl", encoding="utf-8") if l.strip()]
print(f"the rows, checked again: the golden set would drop {len(mt.exclude_golden(rows, golden)[1])} of {len(rows)}")
quotes = [(r["text"], r["draft"]["citations"][0]["quote"]) for r in rows if r["draft"]["citations"]]
flat = lambda s: re.sub(r"\\s+", " ", s).strip()
print(f"  quotes in their chunk, line breaks as spaces: {sum(flat(q) in flat(t) for t, q in quotes)} of {len(quotes)}; "
      f"over twenty-five words: {sum(len(q.split()) > 25 for _, q in quotes)}")
said = [r["draft"]["answer"] for r in rows if r["draft"]["answerable"]]
marked = sum(bool(re.search(r"\\[(\\d+(?:\\s*,\\s*\\d+)*)\\]", a)) for a in said)
print(f"  answers that mark their source with [N]: {marked} of {len(said)}")
print(f"  rows from the handbook's generated GEN- sections: {sum('#GEN-' in r['chunk_id'] for r in rows)}")
for r in rows[:: max(1, len(rows) // 3)][:3]:
    print(f"  {r['chunk_id']}: {r['question']}")"""
CELLS["freeze"] = "python - <<'PY'\n" + FREEZE_PY + "\nPY"
assert ('r"' + UI_CITE + '"') in AUDIT_PY and ('r"' + UI_CITE + '"') in FREEZE_PY          # the cells count the UI's own marks
OUT["freeze"] = run([sys.executable, "-"], K2, "import lane171\nlane171.freeze()\nlane171.install()\n" + FREEZE_PY, {"LANE171_NOW": "2026-09-24T09:40:00+00:00"})
FR = OUT["freeze"]
assert f"the frozen manifest, from gs://{PROJ}-datasets/sft/: v2, built 2026-09-24, {M2['rows']} rows" in FR, FR
assert FR.count("sha256 as the manifest says") == 2 and f"the golden set would drop 0 of {M2['rows']}" in FR, FR
N2, R2 = M2["rows"], M2["refusals"]
assert f"  answers that mark their source with [N]: 0 of {N2 - R2}" in FR and f"quotes in their chunk, line breaks as spaces: {N2 - R2} of {N2 - R2}" in FR, FR

# ------------------------------------------------------------------ step 7 (optional): v3, --style helpdesk (the kit's main(), the same copy)
shutil.copytree(KIT / "services" / "rag-api", K2 / "services" / "rag-api", ignore=shutil.ignore_patterns("__pycache__"))  # served_prompt's packer
ECHO3 = ECHO.replace("--version v2\n", "--version v3 --style helpdesk\n")
assert ECHO3 != ECHO
CELLS["v3"] = (f"python -m pip install -q {' '.join(PINS)}   # the same pins as step 5\n"
               'make trainset PROJECT="$PROJECT" TRAINSET_ARGS="--version v3 --style helpdesk"     # v2 stays as it is')
TRAIN3_PY = TRAIN_PY.replace("'--version', 'v2']", "'--version', 'v3', '--style', 'helpdesk']")
assert TRAIN3_PY != TRAIN_PY
trained3 = run([sys.executable, "-"], K2, TRAIN3_PY, {"LANE171_NOW": "2026-09-27T09:10:00+00:00"})
OUT["v3"] = ECHO3 + trained3.replace(str(K2 / "evals" / "sft"), "/home/YOU/deploy_module_rag/evals/sft").replace("\\", "/")
T3 = OUT["v3"]
M3 = json.loads((K2 / "evals/sft/documind_sft_v3.manifest.json").read_text(encoding="utf-8"))
N3, V3, H3, R3 = M3["rows"], M3["validation_rows"], M3["hinglish_rows"], M3["refusals"]
DQ3, DH3, DG3, DP3 = M3["dropped_quote"], M3["dropped_hinglish"], M3["dropped_golden_overlap"], M3["dropped_pii"]
V3_SHA = "fc16d910b684"                                                            # lesson 12.2's build asserts the same
assert f"(sha {V3_SHA})" in T3, T3
INDEX3 = [json.loads(line) for line in (K2 / "evals/sft/documind_sft_v3.rows.jsonl").read_text(encoding="utf-8").splitlines()]
EMAIL_CHUNK = "acme:cgst_act_2017#p1-0"                                            # the public helpdesk address lesson 12.2's DLP finds
SAMPLED3 = mt.sample([c for c in CHUNKS if "#GEN-" not in c["chunk_id"]], 300)
assert DP3 == 1 and EMAIL_CHUNK in {c["chunk_id"] for c in SAMPLED3} and all(EMAIL_CHUNK not in i["context_ids"] for i in INDEX3), DP3
assert (M3["version"], M3["style"], M3["teacher"], M3["distractors"]) == ("v3", "helpdesk", mt.HELPDESK_TEACHER, mt.DISTRACTORS), M3
assert f"  300 chunks sampled from acme's corpus mirrors, the handbook's {N_HB_GEN} generated GEN- sections left out;" in T3, T3
assert f"  {N3} training rows ({H3} in Hinglish, {R3} refusals) and {V3} validation rows from {len(M3['documents'])} documents" in T3, T3
assert f"dropped {DQ3} pairs whose quote was not in its chunk" in T3 and T3.count(f"  uploaded gs://{PROJ}-datasets/sft/documind_sft_v3.") == 5, T3
assert DQ3 > 0 and DH3 > 0 and 350 < N3 < 450 and 25 < V3 < 60 and H3 > 100 and "hr_policy_2026.md" not in M3["documents"], M3
assert (K2 / "evals/sft/documind_sft_v2.manifest.json").read_text(encoding="utf-8") == json.dumps(M2, indent=1, ensure_ascii=False) + "\n"   # v2 untouched
V3READ_PY = """import hashlib, json, os, re, sys
from google.cloud import storage
sys.path[:0] = [".", "evals"]
import make_trainset as mt
P = os.environ["PROJECT"]
bucket = storage.Client(project=P).bucket(f"{P}-datasets")
m = json.loads(bucket.blob("sft/documind_sft_v3.manifest.json").download_as_text())
print(f"the frozen manifest: {m['version']}, {m['style']} style, teacher {m['teacher']}: {m['rows']} training rows "
      f"({m['hinglish_rows']} in Hinglish, {m['refusals']} refusals) and {m['validation_rows']} validation rows")
data = {}
for key, f in m["files"].items():
    data[key] = bucket.blob("sft/" + os.path.basename(f["path"])).download_as_bytes()
    same = hashlib.sha256(data[key]).hexdigest() == f["sha256"]
    print(f"  {key:10} {os.path.basename(f['path'])}: {len(data[key].splitlines())} rows, sha256 {'as the manifest says' if same else 'DIFFERS FROM THE MANIFEST'}")
index = [json.loads(l) for l in data["rows"].decode("utf-8").splitlines()]
train = [json.loads(l) for l in data["vertex"].decode("utf-8").splitlines()]
rows = [dict(i, prompt=v["contents"][0]["parts"][0]["text"], draft=json.loads(v["contents"][1]["parts"][0]["text"]))
        for i, v in zip([i for i in index if i["split"] == "train"], train)]
k = 1 + m["distractors"]
served = sum(r["prompt"].startswith(mt.SYSTEM) and r["prompt"].count("You are DocuMind") == 1 and r["prompt"].count("\\n[Source ") == k for r in rows)
print(f"the prompts: {served} of {len(rows)} are the served shape - SYSTEM once, {k} sources under their header lines, the question")
chunks = {c["chunk_id"]: c for c in mt.load_chunks(m["tenant"])}
said = [r for r in rows if r["answerable"]]
marked = sum(r["draft"]["citations"][0]["source"] == r["position"] and f"[{r['position']}]" in r["draft"]["answer"] for r in said)
quoted = sum(mt.quote_holds(r["draft"]["citations"][0]["quote"], chunks[r["chunk_id"]]["text"]) for r in said)
print(f"the answers: {marked} of {len(said)} mark the source their citation names; {quoted} of {len(said)} quotes are in their chunk, "
      f"at most twenty-five words")
golden = [json.loads(l) for l in open("evals/golden.jsonl", encoding="utf-8") if l.strip()]
again = mt.exclude_golden([dict(i, text=chunks[i["chunk_id"]]["text"]) for i in index], golden)[1]
print(f"the test set: the golden set would drop {len(again)} of {len(index)} rows; rows from the handbook's GEN- sections: "
      f"{sum('#GEN-' in i['chunk_id'] for i in index)}")
held = {i["chunk_id"] for i in index if i["split"] == "validation"}
print(f"the split: {len(held)} chunks held out for validation, every twin beside its pair: "
      f"{all((i['chunk_id'] in held) == (i['split'] == 'validation') for i in index)}")
twins = [r for r in rows if r["lang"] == "hinglish" and r["answerable"]]
twin = next((r for r in twins if "gratuity" in r["chunk_id"]), twins[0] if twins else None)
for r in [x for x in rows if twin and x["chunk_id"] == twin["chunk_id"] and x["answerable"]]:
    print(f"\\n  {r['lang']}: {r['chunk_id']}, answered from [Source {r['position']}]")
    print("  " + "\\n  ".join(line for line in r["prompt"].splitlines() if line.startswith("[Source ")))
    print(f"  Question: {r['question']}")
    print("  " + r["draft"]["answer"].replace("\\n", "\\n  "))"""
CELLS["v3read"] = "python - <<'PY'\n" + V3READ_PY + "\nPY"
OUT["v3read"] = run([sys.executable, "-"], K2, "import lane171\nlane171.freeze()\nlane171.install()\n" + V3READ_PY, {"LANE171_NOW": "2026-09-27T09:40:00+00:00"})
R3OUT = OUT["v3read"]
A3 = N3 - R3
assert f"the frozen manifest: v3, helpdesk style, teacher {mt.HELPDESK_TEACHER}: {N3} training rows ({H3} in Hinglish, {R3} refusals) and {V3} validation rows" in R3OUT, R3OUT
assert R3OUT.count("sha256 as the manifest says") == 4 and f"the prompts: {N3} of {N3} are the served shape" in R3OUT, R3OUT
assert f"the answers: {A3} of {A3} mark the source their citation names; {A3} of {A3} quotes are in their chunk" in R3OUT, R3OUT
assert f"the golden set would drop 0 of {N3 + V3} rows; rows from the handbook's GEN- sections: 0" in R3OUT and "every twin beside its pair: True" in R3OUT, R3OUT
assert "\n  en: acme:payment_of_gratuity_act_1972#" in R3OUT and "\n  hinglish: acme:payment_of_gratuity_act_1972#" in R3OUT and R3OUT.count("**Clause:** ") == 2, R3OUT
# what the teacher's 300 calls cost at cost.py's Pro rates: the longer ask and each chunk in, the pair twice (two languages) and a verdict out
TOK_IN3 = sum(len(mt.HELPDESK_ASK) + len(c["text"][:2400]) for c in SAMPLED3) / 4
TOK_OUT3 = TOK_OUT * 2.2
PRO = next(ast.literal_eval(n.value) for n in ast.parse(src[COST]).body
           if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "FALLBACK")["gemini-3.1-pro-preview"]
TRAIN3_RS = (TOK_IN3 * PRO[0] + TOK_OUT3 * PRO[1]) / 1e6 * 85
assert 60 < TRAIN3_RS < 250, TRAIN3_RS

# ------------------------------------------------------------------ the panel: would this row enter the file? (exclude_golden, ported)
PANEL_CHUNKS = ["acme:payment_of_gratuity_act_1972#p4-0", "acme:code_on_wages_2019#p7-1", "acme:payment_of_bonus_act_1965#p1-0",
                "acme:labour_codes_compliance_handbook#p14-0", "acme:code_on_wages_2019#p2-0", "acme:hr_policy_2026#GEN-003"]
BY_ID = {c["chunk_id"]: c for c in CHUNKS}
PCH = [{"id": i, "source": BY_ID[i]["source_uri"].replace("${PROJECT_ID}", PROJ), "text": BY_ID[i]["text"]} for i in PANEL_CHUNKS]
PRESETS = ["What is the notice period for a confirmed E3 employee?", "How many days a month can I work from home?",
           "After how many years of service does gratuity become payable?", "What does this Code define as wages?",
           "Who may inspect the register this section requires?"]
GOLD = [{"id": g["id"], "tenant": g.get("tenant"), "question": g["question"], "must_contain": g.get("must_contain", []),
         "must_retrieve": g.get("must_retrieve", [])} for g in GOLDEN]
CASES = [{"chunk_id": r["chunk_id"], "source_uri": r["source_uri"], "text": r["text"], "question": r["question"]} for r in V1ROWS]
CASES += [{"chunk_id": c["id"], "source_uri": c["source"], "text": c["text"], "question": q} for c in PCH for q in PRESETS + [g["question"] for g in GOLDEN]]
PY_SIDE = []
for case in CASES:
    kept, dropped = mt.exclude_golden([case], GOLDEN)
    PY_SIDE.append(["kept"] if kept else [dropped[0]["overlaps"], dropped[0]["rule"]])
assert sum(1 for x in PY_SIDE if x[0] != "kept") > 100 and {x[1] for x in PY_SIDE if len(x) == 2} == {"evidence", "question"}
PANEL_RESULTS = {(c["chunk_id"], q): r for c, q, r in ((c, c["question"], r) for c, r in zip(CASES, PY_SIDE))}
assert PANEL_RESULTS[(PANEL_CHUNKS[0], PRESETS[3])] == ["lk-16", "evidence"] and PANEL_RESULTS[(PANEL_CHUNKS[1], PRESETS[3])] == ["kept"]
assert PANEL_RESULTS[(PANEL_CHUNKS[4], PRESETS[0])] == ["lk-06", "question"] and PANEL_RESULTS[(PANEL_CHUNKS[2], PRESETS[4])] == ["mm-02", "evidence"]
NUM = ast.literal_eval(src[RUN_EVAL].split("_SMALL = ", 1)[1].split("\n_SCALE", 1)[0])
SCALE = ast.literal_eval(src[RUN_EVAL].split("_SCALE = ", 1)[1].split("\n", 1)[0])
STOPWORDS = sorted(mt.STOPWORDS)

UI_JS = r"""var root = document.getElementById('tg'); if (!root) return;
  var SMALL = __SMALL__, SCALE = __SCALE__, STOP = {}, GOLD = __GOLD__, CHUNKS = __CHUNKS__, PRESETS = __PRESETS__;
  __STOP__.forEach(function(w){ STOP[w] = 1; });
  var has = function(o, k){ return Object.prototype.hasOwnProperty.call(o, k); };
  var WORD = Object.keys(SMALL).concat(Object.keys(SCALE)).join('|');
  function toInt(run){ var total = 0, current = 0; run.split(/[\s-]+/).forEach(function(w){ if (has(SMALL, w)) { current += SMALL[w]; } else if (w === 'hundred') { current = (current || 1) * 100; } else if (has(SCALE, w)) { total += (current || 1) * SCALE[w]; current = 0; } }); return total + current; }
  function normalise(t){ t = t.toLowerCase().split(',').join('').split('-').join(' '); [' per cent', 'per cent', ' percent', 'percent'].forEach(function(s){ t = t.split(s).join('%'); });
    return t.replace(new RegExp('\\b(?:(?:' + WORD + ')(?:[\\s-]+(?:' + WORD + '))*)\\b', 'g'), function(m){ return String(toInt(m)); }); }
  function content(q){ var out = {}; (normalise(q).match(/[a-z0-9]+/g) || []).forEach(function(w){ if (w.length > 2 && !has(STOP, w)) { out[w] = 1; } }); return Object.keys(out); }
  var G = GOLD.map(function(g){ return {id: g.id, tenant: g.tenant, q: content(g.question), musts: g.must_contain.map(normalise).filter(function(p){ return p.length >= 4; }),
    anchors: g.must_retrieve.filter(function(a){ return a; }).map(normalise), question: g.question}; });
  function judge(chunkId, source, text, question){ var t = content(question), textN = normalise(text), whereN = normalise(chunkId + ' ' + source), tenant = chunkId.split(':')[0];
    for (var i = 0; i < G.length; i++) { var g = G[i];
      var scoped = !g.anchors.length || g.anchors.some(function(a){ return whereN.indexOf(a) >= 0 || textN.indexOf(a) >= 0; });
      var phrase = g.musts.filter(function(m){ return textN.indexOf(m) >= 0; })[0];
      if (g.musts.length && scoped && (!g.tenant || g.tenant === tenant) && phrase !== undefined) { return {id: g.id, rule: 'evidence', phrase: phrase, question: g.question}; }
      if (t.length && g.q.length) { var shared = t.filter(function(w){ return g.q.indexOf(w) >= 0; }), union = t.length + g.q.length - shared.length;
        if (shared.length / union >= 0.5 || shared.length === t.length || shared.length === g.q.length || shared.length >= 4) { return {id: g.id, rule: 'question', shared: shared, score: shared.length / union, question: g.question}; } } }
    return null; }
  window.__tg = {judge: function(c){ var r = judge(c.chunk_id, c.source_uri, c.text, c.question); return r ? [r.id, r.rule] : ['kept']; }};
  var $ = function(id){ return document.getElementById(id); };
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) { e.className = cls; } if (text !== undefined) { e.textContent = text; } return e; }
  function show(){ var c = CHUNKS[Number($('tg-chunk').value)], q = $('tg-q').value, out = $('tg-out'), r = judge(c.id, c.source, c.text, q);
    $('tg-text').textContent = c.text.slice(0, 700) + (c.text.length > 700 ? '\u2026' : ''); out.textContent = '';
    if (!q.trim()) { out.appendChild(el('div', '', 'Type or pick a question.')); return; }
    if (!r) { out.appendChild(el('div', 'pass', 'Kept: this row can enter the training file.')); out.appendChild(el('div', '', 'No golden row\u2019s evidence is in this chunk, and no golden question is this one rephrased. The PII scan still runs.')); return; }
    out.appendChild(el('div', 'stop', 'Dropped by the ' + r.rule + ' rule: golden row ' + r.id + '.'));
    out.appendChild(el('div', '', '\u201c' + r.question + '\u201d'));
    if (r.rule === 'evidence') { out.appendChild(el('div', '', 'This chunk is in that row\u2019s scope and carries its phrase \u201c' + r.phrase + '\u201d: it is the evidence the gate scores against, whatever question is written from it.')); }
    else { out.appendChild(el('div', '', 'Shared content words: ' + r.shared.join(', ') + ' (overlap ' + r.score.toFixed(2) + '). A model memorises a rephrasing as well as the words.')); } }
  $('tg-pick').addEventListener('change', function(){ if ($('tg-pick').value !== '') { $('tg-q').value = PRESETS[Number($('tg-pick').value)]; } show(); });
  $('tg-q').addEventListener('input', function(){ $('tg-pick').value = ''; show(); }); $('tg-chunk').addEventListener('change', show);
  $('tg-q').value = PRESETS[0]; $('tg-pick').value = '0'; show();"""
UI_JS = (UI_JS.replace("__SMALL__", json.dumps(NUM)).replace("__SCALE__", json.dumps(SCALE)).replace("__STOP__", json.dumps(STOPWORDS))
         .replace("__GOLD__", json.dumps(GOLD, ensure_ascii=False)).replace("__CHUNKS__", json.dumps(PCH, ensure_ascii=False))
         .replace("__PRESETS__", json.dumps(PRESETS)))
squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS
PORT_JS = UI_JS.split("var $ = function(id)")[0].replace("var root = document.getElementById('tg'); if (!root) return;", "")
NODE = ("var window = {}, document = {};\n(new Function('window', 'document', " + json.dumps(PORT_JS) + "))(window, document);\n"
        "var C = " + json.dumps(CASES, ensure_ascii=False) + ";\n"
        "process.stdout.write(JSON.stringify(C.map(function(c){ return window.__tg.judge(c); })));\n")
node = subprocess.run(["node", "-"], input=NODE, capture_output=True, text=True, encoding="utf-8")
assert node.returncode == 0, node.stderr[-800:]
JS_SIDE = json.loads(node.stdout)
for i, (a_, b_) in enumerate(zip(JS_SIDE, PY_SIDE)):
    assert a_ == b_, (CASES[i]["chunk_id"], CASES[i]["question"], a_, b_)
N_CHECKED = len(CASES)
shutil.rmtree(T, ignore_errors=True)
CHUNK_OPTIONS = "".join(f'<option value="{i}">{html.escape(c["id"].split(":", 1)[1])}</option>' for i, c in enumerate(PCH))
PRESET_OPTIONS = '<option value="">your own question</option>' + "".join(f'<option value="{i}">{html.escape(q)}</option>' for i, q in enumerate(PRESETS))


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "audit": "run in the operator shell, in the kit (the rules on fixtures, then the kit's own v1; no network)",
    "gate": "run in the operator shell, in the kit (every golden row, as in 7.2: about ten minutes)",
    "decide": "run in the operator shell, in the kit (reads only: the report, a week of logs, the price table)",
    "trainset": "run in the operator shell, in the kit (about twenty minutes: one flash call a chunk)",
    "freeze": "run in the operator shell, in the kit (reads only)",
    "v3": "optional: run in the operator shell, in the kit (about twenty-five minutes: one teacher call a chunk)",
    "v3read": "optional: run in the operator shell, in the kit (reads only)",
}
OUT_LABELS = {
    "audit": "(this cell run on the kit's own make_trainset.py and its committed v1)",
    "gate": "(run_eval.py's own code over lesson 4.2's stub API, which misses two rows on purpose; your rows and times are your lane's)",
    "decide": "(this cell over that report and a week of stand-in usage rows; your traffic, tokens and verdict are your lane's)",
    "trainset": "(the kit's make_trainset.py with Gemini, DLP and Cloud Storage stood in: your questions, drops and counts are yours)",
    "freeze": "(the same stand-ins: your manifest's numbers are your v2's)",
    "v3": "(the kit's make_trainset.py --style helpdesk with the teacher, DLP and Cloud Storage stood in: your rows, drops and counts are yours)",
    "v3read": "(the same stand-ins; the stand-in teacher's wording is mechanical, and your teacher writes its own)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})
STATS = {"N_CHECKED": str(N_CHECKED), "N_Q1": str(N_Q1), "N_EXACT": str(N_EXACT), "N_FLAT": str(N_FLAT), "N_OFF": str(N_Q1 - N_FLAT),
         "N_LONG": str(N_LONG), "MAX_WORDS": str(MAX_WORDS), "N_GEN1": str(N_GEN1), "N_HB_GEN": str(N_HB_GEN), "N_CHUNKS": f"{len(CHUNKS):,}",
         "N2": str(N2), "R2": str(R2), "CHUNK_OPTIONS": CHUNK_OPTIONS, "PRESET_OPTIONS": PRESET_OPTIONS, "TRAIN_RS": f"{round(TRAIN_RS / 5) * 5:.0f}",
         "TOK_IN": f"{TOK_IN / 1000:.0f}", "N_DROP2": str(M2["dropped_golden_overlap"]), "N_GOLD": str(len(GOLDEN)), "N_TOPICS": str(len(GEN_TOPICS)), "N_V1": str(len(V1ROWS)), "SAVING": SAVING,
         "GENAI_PIN": PINS[0].split("==")[1], "ATTEMPTS": str(mt.RETRY["attempts"]), "WAIT_MIN": str(round(WAIT_S / 60)),
         "GIVE_UP": {2: "Two", 3: "Three", 4: "Four", 5: "Five"}[mt.GIVE_UP_AFTER],
         "TEACHER": mt.HELPDESK_TEACHER, "DISTRACTORS": str(mt.DISTRACTORS), "N_SOURCES": {2: "two", 3: "three", 4: "four"}[1 + mt.DISTRACTORS],
         "VAL_EVERY": str(mt.VALIDATION_EVERY), "N3": str(N3), "V3": str(V3), "H3": str(H3), "R3": str(R3), "DQ3": str(DQ3), "DH3": str(DH3),
         "DG3": str(DG3), "DP3_ROWS": f"{DP3} row" + ("" if DP3 == 1 else "s"), "TRAIN3_RS": f"{round(TRAIN3_RS / 5) * 5:.0f}", "TOK_IN3": f"{TOK_IN3 / 1000:.0f}", "A3": str(A3)}

if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    print({k: v for k, v in STATS.items() if not k.endswith("_OPTIONS")})
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: make_trainset --selftest and main(), run_eval.live() on 4.2's stub, the rubric on its report | v1: {N_Q1} quotes, "
      f"{N_Q1 - N_FLAT} off their chunk, {N_LONG} over 25 words | panel checked against exclude_golden on {N_CHECKED} cases")
