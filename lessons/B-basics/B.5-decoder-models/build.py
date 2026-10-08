"""Build lesson B.5 from its three parts, the shared template, the Basics laptop setup and verbatim kit excerpts.

Generate with GPT-style models: decoding and run-to-run variance. A decoder writes one token at a time: it scores every
candidate for the next position (logits), softmax turns the scores into probabilities, one token is picked - the
likeliest (greedy) or by a draw (sampling) - and the loop runs again until the end token or the cap. Temperature, top-k
and top-p reshape the probabilities before the draw.

Offline, at build time: a toy next-token model in numpy over a vocabulary of 13 tokens. Three cells - one step's
logits, softmax, greedy and seeded draws; the three knobs on that step; the whole loop with five seeded runs per
setting, the distinct answers counted - run here in this interpreter (the Basics venv's numpy pin), and every claim the
prose makes is asserted on their own output. The explorer's script is checked against the same functions under node.

Live, from the author's runs (pb.recorded, RUN_LIST.md): the generator's own prompt for golden row lk-06 sent five times
to the kit's model with _call()'s config, the distinct answers counted; golden row jn-01's prompt at thinking levels LOW
and HIGH, the thought tokens and the rupees from shared/prices.py. Both live cells also run here against a stand-in
client (no network), so their code and the config they send are checked with the SDK's own types.

Sources (checked 7 October 2026; the kit's own values come from the kit, read below):
  - Gemini 3.6 Flash, model page: does not support custom values for temperature, Top-K and Top-P - custom values are
    ignored; custom frequency and presence penalties throw an error. The page also carries a deprecation notice for
    19 November 2026 (upgrade to Gemini 3.8 Flash), which this page does not repeat: the model id comes from the kit.
    https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-6-flash
    (the English page did not render for the fetcher; read through Google's own mirror,
    https://docs.cloud.google.cn/gemini-enterprise-agent-platform/models/gemini/3-6-flash)
  - Developer's guide to Gemini 3.6 Flash: "Custom values for temperature, top-k, or top-p parameters are no longer
    supported. Setting custom values will be ignored in the API surface"; control output determinism with
    thinking_level or a structured JSON schema instead; thinking levels MINIMAL, LOW, MEDIUM, HIGH (default MEDIUM);
    thinking_level replaces thinking_budget; the global endpoint in the REST example.
    https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-3-6-flash
  - Gemini 3 developer guide (Gemini API; page last updated 2026-09-23): "For all Gemini 3 models, we strongly recommend
    keeping the temperature parameter at its default value of 1.0"; previous models benefited from tuning it, "Gemini
    3's reasoning capabilities are optimized for the default setting"; below 1.0 "may lead to unexpected behavior, such
    as looping or degraded performance, particularly in complex mathematical or reasoning tasks"; minimal "does not
    guarantee that thinking is off"; thinking_level with the legacy thinking_budget in one request returns a 400.
    https://ai.google.dev/gemini-api/docs/gemini-3
  - Gemini API pricing (page last updated 2026-10-07): the output row reads "Output price (including thinking tokens)".
    https://ai.google.dev/gemini-api/docs/pricing
So the build plan's "Gemini 3 ignores temperature" is exact for gemini-3.6-flash, the kit's model, and a simplification
for the earlier Gemini 3 models, where Google advises against changing it rather than ignoring it. The page says both.
"""
import ast
import html
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules imported below leave no __pycache__ in deploy/
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, window  # noqa: E402

LESSON = "B.5"
title = ("<title>Lesson B.5 Generate with GPT-style models: decoding and run-to-run variance - one token at a time, "
         "five answers to one prompt | Netsetos</title>\n")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.dx-controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,150px),1fr));gap:10px 16px;margin-bottom:12px;}
.dx-l{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.dx-l select{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.dx-l input[type=range]{width:100%;min-height:44px;accent-color:var(--teal);}
.dx-bars{display:flex;flex-direction:column;gap:5px;}
.dx-row{display:grid;grid-template-columns:58px minmax(0,1fr);align-items:center;gap:8px;font-family:var(--mono);font-size:var(--kicker-size);color:var(--navy);}
.dx-track{height:20px;background:#e2e8f0;border-radius:5px;overflow:hidden;position:relative;}
.dx-fill{height:100%;background:#5eead4;}
.dx-fill.bad{background:#fca5a5;}
.dx-lbl{position:absolute;left:8px;top:0;line-height:20px;font-size:11px;color:var(--navy);}
.dx-sum{font-family:var(--mono);font-size:var(--kicker-size);color:var(--teal-dark);margin:10px 0 8px;overflow-wrap:anywhere;}
.dx-runs{font-family:var(--mono);font-size:12.5px;line-height:1.6;color:var(--slate);background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;overflow-wrap:anywhere;}
.dx-runs .bad{color:#b91c1c;font-weight:600;}
.dx-count{margin-top:4px;color:var(--navy);font-weight:600;}
"""

setup = pb.basics_setup_section()

# ------------------------------------------------------------------ the kit's own values, read from the kit
GEN_REL, CFG_REL, PRICES_REL, SCHEMA_REL = ("services/rag-api/generator.py", "services/rag-api/config.py",
                                            "shared/prices.py", "shared/documind_schemas.py")
GEN = (KIT / GEN_REL).read_text(encoding="utf-8")
CFG = (KIT / CFG_REL).read_text(encoding="utf-8")
sys.path[:0] = [str(KIT), str(KIT / "services" / "rag-api")]
from shared import documind_corpus as dc, documind_schemas, prices  # noqa: E402
from context_budget import TokenBudget, estimate_tokens, pack_chunks  # noqa: E402

MODEL = re.search(r'^    generator_model: str = "([^"]+)"$', CFG, re.M).group(1)
CAP = int(re.search(r"^    max_answer_tokens: int = (\d+)$", CFG, re.M).group(1))
MAX_CTX = int(re.search(r"^    max_context_tokens: int = (\d+)$", CFG, re.M).group(1))
# What the page says about the knobs is what Google's pages say about THIS model: a new default model is a page review.
assert MODEL == prices.DEFAULT_MODEL == "gemini-3.6-flash", MODEL
USD_IN, USD_OUT = prices.PRICES[MODEL]
USD_INR = prices.USD_INR
assert GEN.count("settings.max_answer_tokens * 3") == 2          # generate(): one retry with three times the room, both backends
CAP3 = CAP * 3

TREE = ast.parse(GEN)
FUNCS = {n.name: ast.get_source_segment(GEN, n) for n in TREE.body if isinstance(n, ast.FunctionDef)}
K = {n.targets[0].id: ast.literal_eval(n.value) for n in TREE.body
     if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ("SYSTEM", "DATED_RULE")}
LOW_LINE = 'thinking_config=types.ThinkingConfig(thinking_level="LOW")'
assert '_client = genai.Client(enterprise=True, project=settings.project_id, location="global")' in GEN
assert LOW_LINE in FUNCS["_call"] and LOW_LINE in FUNCS["_vertex_stream"]     # the answer and the stream: LOW
assert 'response_mime_type="application/json"' in FUNCS["_call"] and "response_schema=ModelDraft" in FUNCS["_call"]
assert "max_output_tokens=max_tokens" in FUNCS["_call"] and "contents=_contents(prompt, packed)" in FUNCS["_call"]
for knob in ("temperature", "top_p", "top_k", "seed", "candidate_count"):
    assert f"{knob}=" not in GEN, knob                                        # the page says the kit sends none of them
assert '"tokens_out": n("candidates_token_count") + n("thoughts_token_count")' in FUNCS["_usage"]
assert '    prompt = f"{SYSTEM}{_dated_rule(packed)}\\n\\nContext:\\n{context}\\n\\nQuestion: {query}"' in FUNCS["generate"]
assert "the thinking drawn from the same" in CFG                              # config.py: the cap is shared with the thinking
assert "NO temperature / top_p / top_k: gemini-3.6-flash ignores all" in FUNCS["_call"]       # the comment step 6 reads
assert "thinking_level, not thinking_budget=0 - Gemini 3.x" in FUNCS["_call"] and "cannot be switched off" in FUNCS["_call"]
assert "**_cache_kwargs(tenant_id, model)" in FUNCS["_call"]                  # a tenant's cache joins the config when live
assert 'if c.get("kind") in ("figure", "table") and c.get("media_url"):' in FUNCS["_contents"]   # a packed figure adds its image
assert "billed = _add(billed, " in FUNCS["generate"]                          # the cut-off attempt is billed with the retry
assert "number words to digits" in (KIT / "evals/run_eval.py").read_text(encoding="utf-8")   # run_eval.py's normalise()
prices.PROFILE = "gcp"                                                        # price at list, whatever this shell's profile


def inr(tokens_in: int, tokens_out: int) -> float:
    """The kit's own arithmetic: shared/prices.py's usd(), at its USD_INR."""
    return prices.usd(MODEL, tokens_in, tokens_out) * USD_INR


INR_PER_K_OUT, INR_PER_K_IN = inr(0, 1000), inr(1000, 0)
assert round(INR_PER_K_OUT, 4) == 0.6375 and round(INR_PER_K_IN, 4) == 0.1275 and USD_OUT / USD_IN == 5

# ------------------------------------------------------------------ the generator's prompt for two golden rows
HANDBOOK = (KIT / "evals/corpus/acme/hr_policy_2026.md").read_text(encoding="utf-8")
CHUNKS = {c["locator"]: c for c in dc.chunk_document({"slug": "hr_policy_2026", "doc_type": "policy", "text": HANDBOOK,
                                                      "source_uri": "gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md"}, "acme")}
GOLDEN = {r["id"]: r for r in map(json.loads, filter(str.strip, (KIT / "evals/golden.jsonl").read_text(encoding="utf-8").splitlines()))}
LK06, JN01 = GOLDEN["lk-06"], GOLDEN["jn-01"]
assert LK06["must_contain"] == ["60"] and "NP-03" in LK06["must_retrieve"] and LK06["answerable"]
assert JN01["must_contain"] == ["15", "cannot"] and JN01["must_retrieve"] == ["PB-02", "LV-07"] and JN01["answerable"]
assert "notice period of 60 days" in CHUNKS["NP-03"]["text"]
assert "period is 15 days" in CHUNKS["PB-02"]["text"] and "capped at 45 days" in CHUNKS["LV-07"]["text"]
assert "Leave cannot be\nencashed during probation" in CHUNKS["LV-07"]["text"]
assert "terminate for convenience on 90 days" in (KIT / "evals/corpus/acme/msa_acme_2026.md").read_text(encoding="utf-8")


def generator_prompt(locators: list, row: dict) -> str:
    """generate()'s prompt for these clauses: _budget()'s chunk budget, pack_chunks()'s context, no dated rule (no
    clause here carries a date), the question - byte for byte what the API sends when retrieval hands it these."""
    query = row["question"]
    budget = TokenBudget.fit(MAX_CTX, f"{K['SYSTEM']}{K['DATED_RULE']}\n\nContext:\n\n\nQuestion: {query}",
                             estimate_tokens, answer=CAP).chunks
    context, packed, dropped = pack_chunks([CHUNKS[loc] for loc in locators], budget, estimate_tokens)
    assert not dropped and not any(c.get("effective_from") for c in packed)
    prompt = f"{K['SYSTEM']}\n\nContext:\n{context}\n\nQuestion: {query}"
    assert "\\" not in prompt and '"""' not in prompt                        # safe inside the cell's triple quotes
    return prompt


PROMPT_LK06, PROMPT_JN01 = generator_prompt(["NP-03"], LK06), generator_prompt(["PB-02", "LV-07"], JN01)
EST_LK06, EST_JN01 = estimate_tokens(PROMPT_LK06), estimate_tokens(PROMPT_JN01)
CEIL_FIVE, CEIL_THINK = inr(0, 5 * CAP), inr(0, 2 * CAP3)            # output at the cap: the bound the labels quote

# ------------------------------------------------------------------ verbatim kit excerpts
SCHEMA_SRC = block(SCHEMA_REL, "class DraftCitation(BaseModel):", end="def resolve(")
EXCERPTS = {
    "client": ("services/rag-api/generator.py - the client: generation on the global endpoint",
               block(GEN_REL, "_client = genai.Client(enterprise=True", n=1)),
    "config_model": ("services/rag-api/config.py - the model is a setting", block(CFG_REL, "    # GENERATOR_MODEL in the environment.", n=5)),
    "call": ("services/rag-api/generator.py - _call(): one generate_content and its config", block(GEN_REL, "def _call(", end="def _exhausted_tier(")),
    "schema": ("shared/documind_schemas.py - DraftCitation and ModelDraft, the response schema", SCHEMA_SRC),
    "system": ("services/rag-api/generator.py - SYSTEM, the rules every prompt starts with", block(GEN_REL, 'SYSTEM = """You are DocuMind', n=8)),
    "prompt_line": ("services/rag-api/generator.py - generate(): the prompt, in one text part",
                    block(GEN_REL, '    prompt = f"{SYSTEM}{_dated_rule(packed)}', n=1)),
    "usage": ("services/rag-api/generator.py - _usage(): the thinking is billed as output", block(GEN_REL, "def _usage(", end="def _add(")),
    "retry": ("services/rag-api/generator.py - generate(): a cut-off answer, retried once",
              block(GEN_REL, '    if draft is None and _finish_reason(r) == "MAX_TOKENS":', end="    if draft is None:")),
    "config_cap": ("services/rag-api/config.py - the cap, shared with the thinking", block(CFG_REL, "    # 2048, not 1024:", n=4)),
    "prices": ("shared/prices.py - the price list and usd()", block(PRICES_REL, "USD_INR = 85", end="def inr(")),
    "golden_lk06": ("evals/golden.jsonl - the row step 7 asks", block("evals/golden.jsonl", '"id": "lk-06"', n=1)),
    "golden_jn01": ("evals/golden.jsonl - the row step 8 asks", block("evals/golden.jsonl", '"id": "jn-01"', n=1)),
}
assert EXCERPTS["system"][1].rstrip().endswith('"""') and "Rules:" in EXCERPTS["system"][1]
assert EXCERPTS["retry"][1].rstrip().endswith("draft = _draft(r)") and "settings.max_answer_tokens * 3" in EXCERPTS["retry"][1]
assert EXCERPTS["config_cap"][1].rstrip().endswith(f"max_answer_tokens: int = {CAP}")
assert EXCERPTS["config_model"][1].rstrip().endswith(f'generator_model: str = "{MODEL}"')
assert EXCERPTS["prices"][1].rstrip().endswith("return (billable_in * usd_in + cached_tokens * usd_in * 0.10 + tokens_out * usd_out) / 1_000_000")
fill = filler(EXCERPTS, window)


# ------------------------------------------------------------------ cells: what the page shows, and how the build runs them
def heredoc(body: str) -> str:
    return f"python - <<'PY'\n{body}\nPY"


def run_cell(body: str, env: dict | None = None) -> str:
    """Run a cell's Python as the page's heredoc does, in this interpreter, outside the repository."""
    r = subprocess.run([sys.executable, "-"], input=body, capture_output=True, text=True, encoding="utf-8",
                       cwd=tempfile.gettempdir(), env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1", **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stdout[-1500:], r.stderr[-3000:])
    return r.stdout


DRAWS = '''def draws(seed):                                          # a tiny seeded generator: the same seed gives the same draws
    x = seed
    while True:
        x = (x + 0x9E3779B9) & 0xFFFFFFFF                 # step the state, then mix its bits (MurmurHash3's finaliser)
        z = ((x ^ (x >> 16)) * 0x85EBCA6B) & 0xFFFFFFFF
        z = ((z ^ (z >> 13)) * 0xC2B2AE35) & 0xFFFFFFFF
        yield (z ^ (z >> 16)) / 2**32                     # a number from 0 up to, not including, 1'''

SHAPED = '''def shaped(logits, T=1.0, k=None, top_p=None):            # the three knobs, on one step's logits
    z = np.asarray(logits, dtype=float)
    if T == 0:                                            # temperature 0 is greedy: all the probability on the top token
        q = (z == z.max()).astype(float)
        return q / q.sum()
    q = np.exp((z - z.max()) / T)                         # temperature divides the logits, then the softmax
    q /= q.sum()
    order = np.argsort(-q, kind="stable")                 # the candidates, likeliest first
    n = len(q) if k is None else min(k, len(q))           # top-k keeps the k likeliest
    if top_p is not None:                                 # top-p keeps the fewest whose probabilities reach top_p
        n = min(n, int(np.searchsorted(np.cumsum(q[order]), top_p)) + 1)
    q[order[n:]] = 0.0                                    # the rest can no longer be picked,
    return q / q.sum()                                    # and what is left adds up to 1 again'''

TOY = '''NEXT = ["60", "sixty", "15", "90", "45", "30", "ninety"]  # the toy's candidates after "...serves a notice period of"
logits = np.array([4.0, 2.6, 0.6, 0.2, -0.2, -0.6, -1.0])  # the model's raw scores, one per candidate'''

SCORE_PY = f'''import numpy as np
{TOY}
e = np.exp(logits - logits.max())                         # softmax: exponentiate (less the largest, so nothing overflows)
p = e / e.sum()                                           # and divide by the total, so the probabilities add up to 1
for token, z, q in zip(NEXT, logits, p):
    print(f"{{token:>6}}  logit {{z:+.1f}}  probability {{q:.3f}}")
print(f"total {{p.sum():.3f}} | 60 or sixty {{p[:2].sum():.3f}}, another figure {{p[2:].sum():.3f}} | greedy picks {{NEXT[int(np.argmax(p))]!r}}")

{DRAWS}

def sample(p, u):                                         # sampling: the first candidate whose running total passes u
    return min(int(np.searchsorted(np.cumsum(p), u, side="right")), len(p) - 1)

for seed in (1, 2, 1):
    u = draws(seed)
    print(f"seed {{seed}}, ten draws:", " ".join(NEXT[sample(p, next(u))] for _ in range(10)))
u = draws(7)
counts = np.bincount([sample(p, next(u)) for _ in range(10_000)], minlength=len(NEXT))
print("seed 7, 10,000 draws:", ", ".join(f"{{t}} {{c / 10_000:.3f}}" for t, c in zip(NEXT, counts)))'''

SHAPE_PY = f'''import numpy as np
{TOY}

{SHAPED}

print(f"{{'setting':18}} {{'P(60)':>6}} {{'P(sixty)':>8}} {{'P(another figure)':>17}} {{'left':>4}}")
for name, knobs in (("T=0 (greedy)", dict(T=0)), ("T=0.5", dict(T=0.5)), ("T=1.0", dict(T=1.0)),
                    ("T=1.5", dict(T=1.5)), ("T=2.0", dict(T=2.0)), ("T=1.0, top-k 2", dict(k=2)),
                    ("T=1.0, top-p 0.90", dict(top_p=0.90)), ("T=1.0, top-p 0.95", dict(top_p=0.95))):
    q = shaped(logits, **knobs)
    print(f"{{name:18}} {{q[0]:6.3f}} {{q[1]:8.3f}} {{q[2:].sum():17.3f}} {{int((q > 0).sum()):4d}}")'''

LOOP_DEFS = f'''import numpy as np
FIGURES = ("60", "sixty", "15", "90", "45", "30", "ninety")
TABLE = {{"of": dict(zip(FIGURES, (4.0, 2.6, 0.6, 0.2, -0.2, -0.6, -1.0))),   # the toy model: for the last token written,
         **{{f: {{"days": 2.4, "calendar": 1.0}} for f in FIGURES}},             # the logits of the tokens that may follow
         "calendar": {{"days": 1.0}}, "days": {{".": 1.6, "from": 0.9}},
         "from": {{"acknowledgement": 1.0}}, "acknowledgement": {{".": 1.0}}, ".": {{"<end>": 1.0}}}}

{DRAWS}

{SHAPED}

def generate(seed, T=1.0, k=None, top_p=None, cap=8):     # the loop: score, shape, pick, append
    u, last, out = draws(seed), "of", []
    while len(out) < cap:
        tokens, logits = list(TABLE[last]), list(TABLE[last].values())
        q = shaped(logits, T, k, top_p)
        pick = tokens[min(int(np.searchsorted(np.cumsum(q), next(u), side="right")), len(q) - 1)]
        if pick == "<end>":
            return " ".join(out), "STOP"                  # the model ended it: finish reason STOP
        out.append(pick)
        last = pick
    return " ".join(out), "MAX_TOKENS"                    # the cap ended it: finish reason MAX_TOKENS'''

LOOP_RUN = '''for name, knobs in (("greedy (T=0)", dict(T=0)), ("T=0.5", dict(T=0.5)), ("T=1.0", dict(T=1.0)), ("T=1.5", dict(T=1.5)),
                    ("T=2.0", dict(T=2.0)), ("T=2.0, top-k 2", dict(T=2.0, k=2))):
    runs = [generate(seed, **knobs)[0] for seed in range(1, 6)]   # the same five seeds each time: only the knobs change
    other = sum(run.split()[0] not in ("60", "sixty") for run in runs)
    print(f"{name:15} distinct {len(set(runs))} of 5, another figure in {other} of 5")
    print(" " * 16 + " | ".join(runs))
print("greedy, capped at 2 tokens:", generate(1, T=0, cap=2))'''
LOOP_PY = LOOP_DEFS + "\n\n" + LOOP_RUN

# the live cells: the generator's prompt and _call()'s config, with the kit's own schema and prices
LIVE_HEAD = f'''import json, os, IMPORTS, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # print any character a model writes, Windows included
from typing import List, Literal
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

{SCHEMA_SRC}

'''
FIVE_PY = LIVE_HEAD.replace("os, IMPORTS, sys", "os, re, sys") + f'''PROMPT = """{PROMPT_LK06}"""
client = genai.Client(enterprise=True, project=os.environ["PROJECT"], location="global")    # generator.py's _client
config = types.GenerateContentConfig(                     # _call()'s config: no temperature, top_p, top_k or seed
    response_mime_type="application/json", response_schema=ModelDraft, max_output_tokens={CAP},
    thinking_config=types.ThinkingConfig(thinking_level="LOW"))
answers, tokens_in, tokens_out = [], 0, 0
for run in range(1, 6):
    r = client.models.generate_content(model="{MODEL}", contents=[PROMPT], config=config)
    u = r.usage_metadata
    tokens_in += u.prompt_token_count or 0
    tokens_out += (u.candidates_token_count or 0) + (u.thoughts_token_count or 0)   # _usage(): thinking is output
    try:
        answers.append(json.loads(r.text)["answer"])
    except (TypeError, ValueError, KeyError):             # cut off or blocked: no draft to read
        answers.append("(no parseable answer)")
    print(f"run {{run}}: {{answers[-1]}}")
distinct = len({{" ".join(a.split()) for a in answers}})
states_60 = sum(bool(re.search(r"(?<![\\w.])60(?![\\w]|\\.\\d)", a.lower())) for a in answers)   # run_eval.py's rule: 60, not 160
rupees = (tokens_in * {USD_IN:.2f} + tokens_out * {USD_OUT:.2f}) / 1_000_000 * {USD_INR}           # shared/prices.py
print(f"distinct answers: {{distinct}} of 5 | answers that state 60 (golden row lk-06): {{states_60}} of 5")
print(f"five calls: {{tokens_in}} tokens in, {{tokens_out}} out (thinking included) | Rs {{rupees:.4f}} at the kit's prices")'''

THINK_PY = LIVE_HEAD.replace("os, IMPORTS, sys", "os, sys") + f'''PROMPT = """{PROMPT_JN01}"""
client = genai.Client(enterprise=True, project=os.environ["PROJECT"], location="global")    # generator.py's _client
rupees = {{}}
for level in ("LOW", "HIGH"):                             # the kit's level, then the deepest
    r = client.models.generate_content(model="{MODEL}", contents=[PROMPT], config=types.GenerateContentConfig(
        response_mime_type="application/json", response_schema=ModelDraft,
        max_output_tokens={CAP3},                         # the room generate() gives its one retry
        thinking_config=types.ThinkingConfig(thinking_level=level)))
    u = r.usage_metadata
    prompt, answer, thoughts = u.prompt_token_count or 0, u.candidates_token_count or 0, u.thoughts_token_count or 0
    rupees[level] = (prompt * {USD_IN:.2f} + (answer + thoughts) * {USD_OUT:.2f}) / 1_000_000 * {USD_INR}   # shared/prices.py
    finish = getattr(r.candidates[0].finish_reason, "name", "UNKNOWN") if r.candidates else "NO_CANDIDATES"
    print(f"{{level:4}}: thoughts {{thoughts}} | answer {{answer}} | prompt {{prompt}} | finish {{finish}} | Rs {{rupees[level]:.4f}}")
    try:
        print("      " + json.loads(r.text)["answer"])
    except (TypeError, ValueError, KeyError):             # cut off or blocked: no draft to read
        print("      (no parseable answer)")
print(f"HIGH cost Rs {{rupees['HIGH'] - rupees['LOW']:+.4f}} against LOW, at the kit's prices")'''

for body in (SCORE_PY, SHAPE_PY, LOOP_PY, FIVE_PY, THINK_PY):
    ast.parse(body)

if os.environ.get("CELLS_ONLY"):                  # print the live cells, for the run list, and stop
    for name, body in (("five_runs.txt", FIVE_PY), ("thinking_levels.txt", THINK_PY)):
        print(f"===== {name}\n{body}")
    sys.exit(0)

# ------------------------------------------------------------------ step 3: one step, run and pinned
SCORE_OUT = run_cell(SCORE_PY)
ROWS = re.findall(r"^\s*(\S+)  logit ([+-]\d\.\d)  probability (\d\.\d{3})$", SCORE_OUT, re.M)
assert [t for t, _, _ in ROWS] == ["60", "sixty", "15", "90", "45", "30", "ninety"], SCORE_OUT
P = {t: float(q) for t, _, q in ROWS}
m = re.search(r"^total (\d\.\d{3}) \| 60 or sixty (\d\.\d{3}), another figure (\d\.\d{3}) \| greedy picks '60'$", SCORE_OUT, re.M)
assert m and m.group(1) == "1.000", SCORE_OUT
TOTAL, RIGHT_T1, OTHER_T1 = m.groups()
assert P["60"] == 0.750 and P["sixty"] == 0.185 and OTHER_T1 == "0.066", (P, OTHER_T1)
SEEDLINES = re.findall(r"^seed (\d), ten draws: (.+)$", SCORE_OUT, re.M)
assert [s for s, _ in SEEDLINES] == ["1", "2", "1"] and SEEDLINES[0][1] == SEEDLINES[2][1] != SEEDLINES[1][1], SEEDLINES
TEN = (SEEDLINES[0][1] + " " + SEEDLINES[1][1]).split()
assert max(set(TEN), key=TEN.count) == "60" and any(t != "60" for t in TEN), TEN
FREQ = dict(re.findall(r"(\S+) (\d\.\d{3})", SCORE_OUT.split("10,000 draws:", 1)[1]))
assert list(FREQ) == list(P), FREQ
MAXDEV = max(abs(float(FREQ[t]) - P[t]) for t in P)
assert MAXDEV <= 0.015, MAXDEV

# ------------------------------------------------------------------ step 4: the knobs, run and pinned
SHAPE_OUT = run_cell(SHAPE_PY)
KNOB = {name.strip(): (float(a), float(b), float(c), int(d)) for name, a, b, c, d in
        re.findall(r"^(T=\S+(?: \(greedy\)|, top-[kp] [\d.]+)?)\s+(\d\.\d{3})\s+(\d\.\d{3})\s+(\d\.\d{3})\s+(\d)$", SHAPE_OUT, re.M)}
assert list(KNOB) == ["T=0 (greedy)", "T=0.5", "T=1.0", "T=1.5", "T=2.0", "T=1.0, top-k 2", "T=1.0, top-p 0.90", "T=1.0, top-p 0.95"], SHAPE_OUT
assert KNOB["T=0 (greedy)"] == (1.0, 0.0, 0.0, 1) and KNOB["T=1.0"][0] == P["60"] and f"{KNOB['T=1.0'][2]:.3f}" == OTHER_T1
assert KNOB["T=0.5"][0] > KNOB["T=1.0"][0] > KNOB["T=1.5"][0] > KNOB["T=2.0"][0]           # cooler is sharper
assert KNOB["T=0.5"][2] < KNOB["T=1.0"][2] < KNOB["T=1.5"][2] < KNOB["T=2.0"][2]           # hotter grows the tail
assert all(KNOB[f"T={t}"][3] == 7 for t in ("0.5", "1.0", "1.5", "2.0"))                   # temperature removes nothing
assert KNOB["T=1.0, top-k 2"][2:] == (0.0, 2) and KNOB["T=1.0, top-p 0.90"][2:] == (0.0, 2)
assert KNOB["T=1.0, top-p 0.95"][3] == 3 and KNOB["T=1.0, top-p 0.95"][2] > 0                 # 15 comes back in
assert KNOB["T=1.0, top-p 0.90"][:2] == KNOB["T=1.0, top-k 2"][:2]

# ------------------------------------------------------------------ step 5: the loop, run and pinned
LOOP_OUT = run_cell(LOOP_PY)
LOOP = {name.strip(): (int(d), int(w)) for name, d, w in re.findall(r"^(\S.{0,14}?)\s+distinct (\d) of 5, another figure in (\d) of 5$", LOOP_OUT, re.M)}
RUNS = dict(zip(LOOP, [line.strip().split(" | ") for line in re.findall(r"^ {16}(\S.*)$", LOOP_OUT, re.M)]))
assert list(LOOP) == ["greedy (T=0)", "T=0.5", "T=1.0", "T=1.5", "T=2.0", "T=2.0, top-k 2"], LOOP_OUT
assert LOOP["greedy (T=0)"] == (1, 0) and RUNS["greedy (T=0)"] == ["60 days ."] * 5
D = {t: LOOP[f"T={t}"][0] for t in ("0.5", "1.0", "1.5", "2.0")}
W = {t: LOOP[f"T={t}"][1] for t in ("0.5", "1.0", "1.5", "2.0")}
assert 1 < D["1.0"] < D["1.5"] < D["2.0"] and D["0.5"] <= D["1.0"] and W["0.5"] == W["1.0"] == 0, (D, W)
assert {"sixty days .", "60 days from acknowledgement ."} <= set(RUNS["T=1.0"]), RUNS["T=1.0"]
assert 1 <= W["1.5"] <= W["2.0"], W
assert LOOP["T=2.0, top-k 2"][1] == 0 and LOOP["T=2.0, top-k 2"][0] > 1
assert "greedy, capped at 2 tokens: ('60 days', 'MAX_TOKENS')" in LOOP_OUT
NS = {}
exec(LOOP_DEFS, NS)                                                     # the cell's own definitions, for the explorer's check
TABLE = NS["TABLE"]
assert [(t, f"{z:+.1f}") for t, z in TABLE["of"].items()] == [(t, z) for t, z, _ in ROWS]   # one toy across the three cells
assert list(TABLE["of"].values()) == sorted(TABLE["of"].values(), reverse=True)           # so top-p 0.95's third is 15
VOCAB_N = len({t for row in TABLE.values() for t in row})
assert VOCAB_N == 13

# ------------------------------------------------------------------ the live cells, against a stand-in client (no network)
STANDIN = '''import json as _json, types as _ns
import google.genai as _genai
from google.genai import types as _types
_CLIENTS, _CALLS = [], []
class _Models:
    def generate_content(self, model, contents, config):
        _CALLS.append((model, contents, config))
        low = config.thinking_config.thinking_level.name == "LOW"
        body = {"answer": f"stand-in {len(_CALLS) % 2}: a notice period of 60 days [1]", "citations": [{"source": 1, "quote": "60 days"}],
                "confidence": "high", "answerable": True}
        usage = _ns.SimpleNamespace(prompt_token_count=321, candidates_token_count=40, thoughts_token_count=100 if low else 900)
        return _ns.SimpleNamespace(text=_json.dumps(body), usage_metadata=usage, parsed=None,
                                   candidates=[_ns.SimpleNamespace(finish_reason=_types.FinishReason.STOP)])
class _Client:
    def __init__(self, **kw):
        _CLIENTS.append(kw)
        self.models = _Models()
_genai.Client = _Client
'''


def standin_check(levels: list, cap: int) -> str:
    return f'''
assert _CLIENTS == [{{"enterprise": True, "project": "documind-ai-YOUR-ID", "location": "global"}}], _CLIENTS
assert [c[2].thinking_config.thinking_level.name for c in _CALLS] == {levels!r}
for _model, _contents, _config in _CALLS:
    assert _model == {MODEL!r} and _contents == [PROMPT] and _config.max_output_tokens == {cap}
    assert (_config.temperature, _config.top_p, _config.top_k, _config.seed, _config.candidate_count) == (None,) * 5
    assert _config.response_mime_type == "application/json" and _config.response_schema is ModelDraft
assert ModelDraft.model_json_schema() == {documind_schemas.ModelDraft.model_json_schema()!r}   # the kit's schema, field for field
print("STAND-IN CHECKED")'''


FIVE_RX = [r"^run 1: .+$", r"^run 2: .+$", r"^run 3: .+$", r"^run 4: .+$", r"^run 5: .+$",
           r"^distinct answers: [1-5] of 5 \| answers that state 60 \(golden row lk-06\): [0-5] of 5$",
           r"^five calls: \d+ tokens in, \d+ out \(thinking included\) \| Rs \d+\.\d{4} at the kit's prices$"]
THINK_RX = [r"^LOW : thoughts \d+ \| answer \d+ \| prompt \d+ \| finish \w+ \| Rs \d+\.\d{4}$",
            r"^HIGH: thoughts \d+ \| answer \d+ \| prompt \d+ \| finish \w+ \| Rs \d+\.\d{4}$",
            r"^HIGH cost Rs [+-]\d+\.\d{4} against LOW, at the kit's prices$"]
ENV = {"PROJECT": "documind-ai-YOUR-ID", "GOOGLE_CLOUD_PROJECT": "documind-ai-YOUR-ID"}
DRY_FIVE = run_cell(STANDIN + FIVE_PY + standin_check(["LOW"] * 5, CAP), ENV)
DRY_THINK = run_cell(STANDIN + THINK_PY + standin_check(["LOW", "HIGH"], CAP3), ENV)
for out, rxs in ((DRY_FIVE, FIVE_RX), (DRY_THINK, THINK_RX)):
    assert out.rstrip().endswith("STAND-IN CHECKED"), out
    assert all(re.search(rx, out, re.M) for rx in rxs), out
assert "distinct answers: 2 of 5 | answers that state 60 (golden row lk-06): 5 of 5" in DRY_FIVE, DRY_FIVE
assert f"Rs {inr(5 * 321, 5 * 140):.4f} at the kit's prices" in DRY_FIVE, DRY_FIVE          # the cell's rupees are prices.usd()'s
assert f"| Rs {inr(321, 940):.4f}" in DRY_THINK and f"HIGH cost Rs {inr(321, 940) - inr(321, 140):+.4f}" in DRY_THINK, DRY_THINK

# ------------------------------------------------------------------ the live outputs: the author's recorded runs
OUT_FIVE, OUT_THINK = pb.recorded(LESSON, "five_runs.txt"), pb.recorded(LESSON, "thinking_levels.txt")
RUN_LIST = (HERE / "RUN_LIST.md").read_text(encoding="utf-8")
for name, text, rxs, body in (("five_runs.txt", OUT_FIVE, FIVE_RX, FIVE_PY), ("thinking_levels.txt", OUT_THINK, THINK_RX, THINK_PY)):
    if text.startswith("[awaiting the author's run:"):
        assert body in RUN_LIST, (f"RUN_LIST.md must carry the cell that records data/{name}, verbatim, while it is awaited: "
                                  "CELLS_ONLY=1 python pagekit/build.py B.5 prints the cells as the page now has them")
        assert f"data/{name}" in RUN_LIST
    else:
        assert all(re.search(rx, text, re.M) for rx in rxs), (name, text[:400])
for amount in (CEIL_FIVE, CEIL_THINK):
    assert f"Rs {amount:.2f}" in RUN_LIST, amount

# ------------------------------------------------------------------ the explorer: the cells' functions, in the browser
CORE_JS = r"""function draws(seed){
  var x = seed >>> 0;
  return function(){
    x = (x + 0x9E3779B9) >>> 0;
    var z = Math.imul(x ^ (x >>> 16), 0x85EBCA6B) >>> 0;
    z = Math.imul(z ^ (z >>> 13), 0xC2B2AE35) >>> 0;
    return ((z ^ (z >>> 16)) >>> 0) / 4294967296;
  };
}
function shaped(z, T, k, p){
  var n = z.length, i, max = -Infinity, q = [], s = 0;
  for (i = 0; i < n; i++){ if (z[i] > max){ max = z[i]; } }
  if (T === 0){
    for (i = 0; i < n; i++){ q.push(z[i] === max ? 1 : 0); s += q[i]; }
    return q.map(function(v){ return v / s; });
  }
  for (i = 0; i < n; i++){ q.push(Math.exp((z[i] - max) / T)); s += q[i]; }
  q = q.map(function(v){ return v / s; });
  var order = q.map(function(v, j){ return j; }).sort(function(a, b){ return (q[b] - q[a]) || (a - b); });
  var keep = (k === null) ? n : Math.min(k, n);
  if (p !== null){ var acc = 0, m = 0; while (m < n){ acc += q[order[m]]; m++; if (acc >= p){ break; } } keep = Math.min(keep, m); }
  for (i = keep; i < n; i++){ q[order[i]] = 0; }
  s = 0; for (i = 0; i < n; i++){ s += q[i]; }
  return q.map(function(v){ return v / s; });
}
function generate(table, start, seed, T, k, p, cap){
  var u = draws(seed), last = start, out = [];
  while (out.length < cap){
    var row = table[last], q = shaped(row.map(function(r){ return r[1]; }), T, k, p), r = u(), acc = 0, i;
    for (i = 0; i < q.length; i++){ acc += q[i]; if (acc > r){ break; } }
    if (i >= q.length){ i = q.length - 1; }
    if (row[i][0] === '<end>'){ return [out.join(' '), 'STOP']; }
    out.push(row[i][0]); last = row[i][0];
  }
  return [out.join(' '), 'MAX_TOKENS'];
}"""
UI_JS = r"""var root = document.getElementById('dx'); if (!root) { return; }
var TABLE = __TABLE__, START = 'of', RIGHT = ['60', 'sixty'], OF = TABLE[START];
var $ = function(id){ return document.getElementById(id); };
var tIn = $('dx-t'), kIn = $('dx-k'), pIn = $('dx-p'), sIn = $('dx-s'), tV = $('dx-t-v'), bars = $('dx-bars'), sum = $('dx-sum'), runs = $('dx-runs');
function el(tag, cls, text){ var e = document.createElement(tag); if (cls){ e.className = cls; } if (text !== undefined){ e.textContent = text; } return e; }
function render(){
  var T = Math.round(parseFloat(tIn.value) * 10) / 10, k = kIn.value ? parseInt(kIn.value, 10) : null, p = pIn.value ? parseFloat(pIn.value) : null, s0 = parseInt(sIn.value, 10);
  tV.textContent = T === 0 ? '0 (greedy)' : T.toFixed(1);
  var q = shaped(OF.map(function(r){ return r[1]; }), T, k, p), other = 0, left = 0;
  bars.textContent = '';
  OF.forEach(function(r, i){
    var bad = RIGHT.indexOf(r[0]) < 0, row = el('div', 'dx-row'), track = el('div', 'dx-track'), fill = el('div', bad ? 'dx-fill bad' : 'dx-fill');
    if (bad){ other += q[i]; }
    if (q[i] > 0){ left++; }
    fill.style.width = (q[i] * 100).toFixed(1) + '%';
    track.appendChild(fill); track.appendChild(el('span', 'dx-lbl', q[i].toFixed(3)));
    row.appendChild(el('span', '', r[0])); row.appendChild(track); bars.appendChild(row);
  });
  sum.textContent = 'P(60) ' + q[0].toFixed(3) + ' | P(sixty) ' + q[1].toFixed(3) + ' | P(another figure) ' + other.toFixed(3) + ' | candidates left ' + left;
  var seen = {}, distinct = 0, wrong = 0;
  runs.textContent = '';
  for (var s = s0; s < s0 + 5; s++){
    var g = generate(TABLE, START, s, T, k, p, 8), bad = RIGHT.indexOf(g[0].split(' ')[0]) < 0;
    if (!seen[g[0]]){ seen[g[0]] = 1; distinct++; }
    if (bad){ wrong++; }
    runs.appendChild(el('div', bad ? 'bad' : '', 'seed ' + s + ': ' + g[0]));
  }
  runs.appendChild(el('div', 'dx-count', 'distinct ' + distinct + ' of 5, another figure in ' + wrong + ' of 5'));
}
[tIn, kIn, pIn, sIn].forEach(function(el){ el.addEventListener('input', render); el.addEventListener('change', render); });
render();"""
TABLE_JS = {last: [[t, z] for t, z in row.items()] for last, row in TABLE.items()}       # lists: JS objects reorder numeric keys
UI_JS = UI_JS.replace("__TABLE__", json.dumps(TABLE_JS))
SCRIPT = CORE_JS + "\n" + UI_JS
JS = "<script>\n(function(){\n'use strict';\n" + SCRIPT + "\n})();\n</script>\n"
assert not re.search(r"</|<!--|<(div|span|p|b|script)\b", SCRIPT), "the script writes no markup and cannot close its tag"
assert "%%" not in JS and "@@" not in JS

GRID = [[s, t, k, p, cap] for s in range(1, 21) for t in (0, 0.5, 1.0, 1.5, 2.0)
        for k, p in ((None, None), (1, None), (2, None), (None, 0.5), (None, 0.9), (3, 0.95)) for cap in (8,)] + \
       [[s, 0, None, None, 2] for s in range(1, 4)]
PY_SIDE = {"gen": [list(NS["generate"](s, t, k, p, cap)) for s, t, k, p, cap in GRID],
           "shp": [NS["shaped"](list(TABLE["of"].values()), t, k, p).tolist() for _, t, k, p, _ in GRID[:30]]}
NODE = (CORE_JS + "\nvar TABLE = " + json.dumps(TABLE_JS) + ", GRID = " + json.dumps(GRID) + ";\n"
        "var OF = TABLE['of'].map(function(r){ return r[1]; });\n"
        "process.stdout.write(JSON.stringify({gen: GRID.map(function(c){ return generate(TABLE, 'of', c[0], c[1], c[2], c[3], c[4]); }),\n"
        "  shp: GRID.slice(0, 30).map(function(c){ return shaped(OF, c[1], c[2], c[3]); })}));\n")
node = subprocess.run(["node", "-"], input=NODE, capture_output=True, text=True, encoding="utf-8")
assert node.returncode == 0, node.stderr[-800:]
JS_SIDE = json.loads(node.stdout)
assert JS_SIDE["gen"] == PY_SIDE["gen"], next((g, a, b) for g, a, b in zip(GRID, JS_SIDE["gen"], PY_SIDE["gen"]) if a != b)
for a_, b_ in zip(JS_SIDE["shp"], PY_SIDE["shp"]):
    assert all(abs(x - y) < 1e-12 for x, y in zip(a_, b_)), (a_, b_)
N_CHECKED = len(GRID)


# ------------------------------------------------------------------ windows and numbers for the parts
def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


OFFLINE = "run on your laptop, in the Basics venv (numpy only, no network)"
BUILT = "(this cell's own output, computed when the page was built: yours prints the same)"
LIVE = "(the author's run, recorded: your answers, token counts and rupees are your own)"
WIN = {
    "CELL_SCORE": bash_window(OFFLINE, heredoc(SCORE_PY)), "OUT_SCORE": out_window(BUILT, SCORE_OUT),
    "CELL_SHAPE": bash_window(OFFLINE, heredoc(SHAPE_PY)), "OUT_SHAPE": out_window(BUILT, SHAPE_OUT),
    "CELL_LOOP": bash_window(OFFLINE, heredoc(LOOP_PY)), "OUT_LOOP": out_window(BUILT, LOOP_OUT),
    "CELL_FIVE": bash_window(f"run on your laptop after lesson 0.1, in the Basics venv (five calls to {MODEL}, at most Rs {CEIL_FIVE:.2f} in output)",
                             heredoc(FIVE_PY)),
    "OUT_FIVE": out_window(LIVE, OUT_FIVE),
    "CELL_THINK": bash_window(f"run on your laptop after lesson 0.1, in the Basics venv (two calls to {MODEL}, at most Rs {CEIL_THINK:.2f} in output)",
                              heredoc(THINK_PY)),
    "OUT_THINK": out_window(LIVE, OUT_THINK),
}
STATS = {
    "MODEL": MODEL, "CAP": f"{CAP:,}", "CAP3": f"{CAP3:,}", "VOCAB_N": str(VOCAB_N),
    "USD_IN": f"{USD_IN:.2f}", "USD_OUT": f"{USD_OUT:.2f}", "USD_INR": str(USD_INR), "RATIO": f"{USD_OUT / USD_IN:g}",
    "INR_PER_K_OUT": f"{INR_PER_K_OUT:.2f}", "INR_PER_K_IN": f"{INR_PER_K_IN:.2f}",
    "INR_CAP": f"{inr(0, CAP):.2f}", "INR_CAP3": f"{inr(0, CAP3):.2f}",
    "CEIL_FIVE": f"{CEIL_FIVE:.2f}", "CEIL_THINK": f"{CEIL_THINK:.2f}", "EST_LK06": str(EST_LK06), "EST_JN01": str(EST_JN01),
    "TOTAL": TOTAL, "P60": f"{P['60']:.3f}", "PSIXTY": f"{P['sixty']:.3f}", "RIGHT_T1": RIGHT_T1, "OTHER_T1": OTHER_T1,
    "MAXDEV": f"{MAXDEV:.3f}",
    "P60_T05": f"{KNOB['T=0.5'][0]:.3f}", "P60_T15": f"{KNOB['T=1.5'][0]:.3f}",
    "PO_T05": f"{KNOB['T=0.5'][2]:.3f}", "PO_T15": f"{KNOB['T=1.5'][2]:.3f}", "PO_T20": f"{KNOB['T=2.0'][2]:.3f}",
    "D_T05": str(D["0.5"]), "D_T10": str(D["1.0"]), "D_T15": str(D["1.5"]), "D_T20": str(D["2.0"]),
    "W_T15": str(W["1.5"]), "W_T20": str(W["2.0"]), "D_K2": str(LOOP["T=2.0, top-k 2"][0]),
    "N_CHECKED": str(N_CHECKED),
}

def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: {MODEL} on global, thinking LOW, no temperature/top_p/top_k/seed, cap {CAP} (retry {CAP3}), "
      f"Rs {INR_PER_K_OUT:.4f} per 1,000 output tokens | toy: distinct {D} at five seeds | explorer checked on {N_CHECKED} runs")
