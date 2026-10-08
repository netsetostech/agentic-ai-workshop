"""Build lesson B.2 from its three parts, the shared template, the Basics laptop setup and verbatim kit excerpts.

Turn text into tokens and embeddings. A token is a piece of text from a learned vocabulary: the unit a model reads,
counts and bills. An embedding is one fixed-length list of numbers for a whole text, and cosine similarity compares
two of them. The page builds both from the bottom, on the learner's laptop, before the kit is cloned (lesson 0.2):

- offline, run here when the page is built, by the interpreter that builds it (the Basics venv: Python 3.12,
  numpy 2.5.3, google-genai 2.22.0): a toy byte-pair tokenizer learned from two clauses of the kit's handbook;
  the kit's two estimates (context_budget.estimate_tokens, len // 4, and indexer.batches, len // CHARS_PER_TOKEN)
  against character, byte and word counts; the rupee line, priced with shared/prices.py's constants as lesson 3.4
  prices an answer; cosine similarity in numpy on small vectors and on word-count vectors of three clauses. Each
  cell's expected window is its own output, and the asserts below pin every number the prose states;
- live, run by the author (RUN_LIST.md): count_tokens on gemini-3.6-flash (location global), priced the same way,
  and text-embedding-005 embeddings (location us-central1) under the kit's two task types, compared by cosine in
  numpy. Their outputs come from pb.recorded() until the author's run is recorded in data/.

The token meter (step 1) is the toy tokenizer's merges, the kit's estimates and the kit's prices in JavaScript; node
runs it on every sample here and its pieces, counts and rupees must equal the Python's.

Facts that can change, checked on the web on 7 October 2026:
- count_tokens is free: "There is no charge or quota restriction for using the CountTokens API", and gemini-3.6-flash
  is among the models it counts for.
  https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/get-token-count (last updated 2026-10-06)
- Gemini bills by tokens, "4 characters result in approximately 1 text token including white space"; text embeddings
  (other than Gemini Embedding) cost USD 0.000025 per 1,000 characters online, 0.00002 batch; and gemini-3.6-flash has
  an introductory price of USD 0.75 / 3.75 per 1M tokens through 31 December 2026, the standard 1.50 / 7.50 (the kit's
  prices) from 1 January 2027.
  https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing (no date on the page; read 7 October 2026)
- text-embedding-005: up to 768 dimensions, 2,048 input tokens per text (longer text is cut unless autoTruncate is
  false), English and code; the task types, of which RETRIEVAL_QUERY is the default when none is given;
  statistics.token_count and statistics.truncated per text.
  https://docs.cloud.google.com/gemini-enterprise-agent-platform/reference/models/text-embeddings-api (last updated 2026-10-06)
- "The vectors are normalized, so you can use cosine similarity, dot product, or Euclidean distance to provide the same
  similarity rankings"; 250 input texts and 20,000 input tokens per request (a 400 error above), 2,048 tokens per text
  (the rest silently truncated); the response's metadata carries billable_character_count.
  https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/embeddings/get-text-embeddings (last updated 2026-10-06)
"""
import ast
import contextlib
import html
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
try:                                               # the cosine cell runs in this interpreter too
    import numpy  # noqa: F401
except ImportError as e:
    raise SystemExit(f"lesson B.2 builds with the Basics interpreter (Python 3.12, numpy 2.5.3, google-genai 2.22.0): {e}")
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, window  # noqa: E402

LESSON = "B.2"
title = "<title>Lesson B.2 Turn text into tokens and embeddings - what a model counts, what it costs in rupees, and how two meanings are compared | Netsetos</title>\n"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.tm-controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:10px 16px;margin-bottom:10px;}
.tm-l{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.tm-l select,.tm-l input{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;box-sizing:border-box;}
.tm-text{font-size:var(--small-size);color:var(--slate);margin:4px 0;overflow-wrap:anywhere;}
.tm-chips{display:flex;flex-wrap:wrap;gap:4px;margin:6px 0 8px;}
.tm-chips span{font-family:var(--mono);font-size:13px;line-height:1.5;padding:1px 6px;border-radius:5px;background:#ccfbf1;color:var(--navy);overflow-wrap:anywhere;}
.tm-chips span:nth-child(even){background:#e0f2fe;}
.tm-sum{font-family:var(--mono);font-size:var(--kicker-size);color:var(--teal-dark);margin:4px 0;overflow-wrap:anywhere;}
"""

setup = pb.basics_setup_section()

# ------------------------------------------------------------------ the kit files this page reads and quotes
PRICES_PY = "shared/prices.py"
COST = "services/rag-api/cost.py"
CB = "services/rag-api/context_budget.py"
GEN = "services/rag-api/generator.py"
CONFIG = "services/rag-api/config.py"
RETRIEVER = "services/rag-api/retriever.py"
SEMCACHE = "services/rag-api/semantic_cache.py"
INDEXER = "services/ingest/indexer.py"
VECTOR_TF = "terraform/vector.tf"
HANDBOOK = "evals/corpus/acme/hr_policy_2026.md"
GOLDEN = "evals/golden.jsonl"


def load(name: str, rel: str):
    """A kit module that imports nothing outside the standard library, loaded from its file (registered first:
    a dataclass with string annotations looks its module up in sys.modules)."""
    spec = importlib.util.spec_from_file_location(name, KIT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


saved_profile = os.environ.pop("DOCUMIND_PROFILE", None)      # the gcp profile: prices.usd() at list price, never the local 0
prices = load("kit_prices", PRICES_PY)
if saved_profile is not None:
    os.environ["DOCUMIND_PROFILE"] = saved_profile
context_budget = load("kit_context_budget", CB)

grab = lambda pat, rel: re.search(pat, (KIT / rel).read_text(encoding="utf-8")).group(1)  # noqa: E731
MODEL = prices.DEFAULT_MODEL
USD_IN, USD_OUT = prices.PRICES[MODEL]
USD_INR = prices.USD_INR
assert MODEL == grab(r'generator_model: str = "([^"]+)"', CONFIG) == "gemini-3.6-flash", MODEL
# cost.py, where lesson 3.4 prices an answer, carries the same fallback and the same rate (test_chat_limits holds them equal)
cost_src = (KIT / COST).read_text(encoding="utf-8")
assert tuple(float(x) for x in re.search(r'"' + re.escape(MODEL) + r'": \(([\d.]+), ([\d.]+)\)', cost_src).groups()) == (USD_IN, USD_OUT)
assert float(re.search(r'USD_INR = float\(os.environ.get\("USD_INR_RATE", "([\d.]+)"\)\)', cost_src).group(1)) == USD_INR
assert "cached_tokens * usd_in * 0.10" in cost_src and "billable_in = max(tokens_in - cached_tokens, 0)" in cost_src
GEN_LOCATION = grab(r'_client = genai\.Client\(enterprise=True, project=settings\.project_id, location="([^"]+)"\)', GEN)
assert GEN_LOCATION == "global"


def module_consts(rel: str) -> dict:
    """Module-level NAME = literal, and NAME = os.environ.get("X", literal) as its default, read without importing."""
    out = {}
    for node in ast.parse((KIT / rel).read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            v = node.value
            if isinstance(v, ast.Constant):
                out[node.targets[0].id] = v.value
            elif isinstance(v, ast.Call) and ast.unparse(v.func) == "os.environ.get" and len(v.args) == 2:
                out[node.targets[0].id] = ast.literal_eval(v.args[1])
            elif isinstance(v, ast.Call) and ast.unparse(v.func) == "genai.Client":
                out[node.targets[0].id] = {k.arg: ast.unparse(k.value) for k in v.keywords}
    return out


IX = module_consts(INDEXER)
EMBED_MODEL, EMBED_DIMS, DOC_TASK = IX["EMBEDDING_MODEL"], IX["EMBEDDING_DIMENSIONS"], IX["EMBEDDING_TASK_TYPE"]
EMBED_LOCATION = ast.literal_eval(IX["_embed"]["location"])
CHARS_PER_TOKEN, EMBED_BATCH, EMBED_TOKENS = IX["CHARS_PER_TOKEN"], IX["EMBED_BATCH"], IX["EMBED_TOKENS"]
assert (EMBED_MODEL, EMBED_DIMS, DOC_TASK, EMBED_LOCATION) == ("text-embedding-005", 768, "RETRIEVAL_DOCUMENT", "us-central1"), IX
assert (CHARS_PER_TOKEN, EMBED_BATCH, EMBED_TOKENS) == (3, 250, 15_000), IX
assert context_budget.estimate_tokens("x" * 45) == 11 and context_budget.estimate_tokens("") == 1   # len // 4, never below 1
ret_src = (KIT / RETRIEVER).read_text(encoding="utf-8")
embed_query_src = ret_src.split("def embed_query(", 1)[1].split("\ndef ", 1)[0]
QUERY_TASK = re.search(r'task_type="([A-Z_]+)"', embed_query_src).group(1)
assert QUERY_TASK == "RETRIEVAL_QUERY" and "output_dimensionality=768" in embed_query_src
assert grab(r'embed_model: str = Field\("([^"]+)"', CONFIG) == EMBED_MODEL and grab(r'region: str = "([^"]+)"', CONFIG) == EMBED_LOCATION
assert "distance_measure=DistanceMeasure.COSINE" in ret_src and 'd["score"] = 1.0 - d.pop("d", 1.0)' in ret_src
VECTOR_DISTANCE = grab(r'distance_measure_type\s*=\s*"([A-Z_]+)"', VECTOR_TF)
assert VECTOR_DISTANCE == "DOT_PRODUCT_DISTANCE" and grab(r"dimensions\s*=\s*(\d+)", VECTOR_TF) == "768"
CACHE_THRESHOLD = grab(r'THRESHOLD = float\(os.environ.get\("SEMANTIC_CACHE_THRESHOLD", "([\d.]+)"\)\)', SEMCACHE)
assert CACHE_THRESHOLD == "0.95"

# ------------------------------------------------------------------ the kit's own words: the handbook clauses and two golden questions
handbook = (KIT / HANDBOOK).read_text(encoding="utf-8")
CLAUSE = {}
for chunk in re.split(r"^## ", handbook, flags=re.M)[1:]:
    head, _, body = chunk.partition("\n")
    CLAUSE[head.split(" ")[0]] = " ".join(body.split())
GOLD = {r["id"]: r for r in (json.loads(line) for line in (KIT / GOLDEN).read_text(encoding="utf-8").splitlines() if line.strip())}
Q = GOLD["lk-06"]["question"]                       # the question lesson 3.4 packs evidence for
Q_USB = GOLD["lk-05"]["question"]
assert Q == "What is the notice period for a confirmed E3?" and GOLD["lk-06"]["must_retrieve"][0] == "NP-03"
assert Q_USB == "Are USB drives allowed on a company laptop?" and GOLD["lk-05"]["must_retrieve"][0] == "IT-SEC-04"
REWORDED = "Can I copy files to a pen drive at work?"   # lk-05 in other words: not one word shared with IT-SEC-04
HINDI = "पुष्टि किए गए E3 कर्मचारी की सूचना अवधि क्या है?"   # the question in Hindi, in lesson 3.4's words for "confirmed" and "notice period"
AMOUNT = CLAUSE["FIN-02"].split(". ")[0] + "."      # FIN-02's first sentence: an amount in lakh notation
assert AMOUNT == "Purchases up to Rs 2,00,000 are approved by the function head."


def py_lines(text: str, indent: int, width: int = 104) -> str:
    """A long string as adjacent Python literals, cut at spaces, each line under `width`: how the cells carry a clause."""
    parts, cur = [], ""
    for word in text.split(" "):
        if cur and len(cur) + 1 + len(word) > width - indent - 4:
            parts.append(cur + " ")
            cur = word
        else:
            cur = f"{cur} {word}" if cur else word
    parts.append(cur)
    assert "".join(parts) == text
    lits = [json.dumps(p, ensure_ascii=False) for p in parts]
    if len(lits) == 1:
        return lits[0]
    return "(" + ("\n" + " " * (indent + 1)).join(lits) + ")"


# ------------------------------------------------------------------ the cells: each runs as pasted, in a bash shell, in ~/basics-venv
def heredoc(body: str) -> str:
    return f"python - <<'PY'\n{body}\nPY"


TRAIN = CLAUSE["NP-03"] + " " + CLAUSE["PB-02"]
BPE_PY = r'''import re
from collections import Counter
# the whole training text: two clauses of the kit's handbook, NP-03 and PB-02
TRAIN = __TRAIN__
def words(text):
    """Cut a text into words: a word keeps the space before it, and a digit or a mark stands alone."""
    return re.findall(r" ?[A-Za-z]+| ?[0-9]| ?[^\sA-Za-z0-9]", text)
def merge(word, a, b):
    """Join every a followed by b inside one word into the single piece a+b."""
    out, i = [], 0
    while i < len(word):
        if i + 1 < len(word) and (word[i], word[i + 1]) == (a, b):
            out.append(a + b)
            i += 2
        else:
            out.append(word[i])
            i += 1
    return tuple(out)
counts = Counter(tuple(w) for w in words(TRAIN))   # each word as single characters, and how often it occurs
merges = []
while True:                         # learn: merge the commonest neighbouring pair, until no pair occurs twice
    pairs = Counter()
    for w, n in counts.items():
        for pair in zip(w, w[1:]):
            pairs[pair] += n
    (a, b), seen = pairs.most_common(1)[0]
    if seen < 2:
        break
    merges.append((a, b))
    counts = Counter({merge(w, a, b): n for w, n in counts.items()})
def encode(text):
    """Tokenize: cut the text into words, then apply every merge in the order it was learned."""
    out = []
    for w in words(text):
        w = tuple(w)
        for a, b in merges:
            w = merge(w, a, b)
        out += w
    return out
print(f"training text: {len(TRAIN)} characters, {len(set(TRAIN))} distinct; {len(merges)} merges learned")
print("the first ten:", [a + b for a, b in merges[:10]])
print("the last five:", [a + b for a, b in merges[-5:]])
for text in ("What is the notice period for a confirmed E3?", " notice", "notice", "Notice", "Bengaluru"):
    pieces = encode(text)
    print(f"{text!r:49} {len(text):2} characters -> {len(pieces):2} piece{'s' if len(pieces) > 1 else ' '} {pieces}")'''.replace("__TRAIN__", py_lines(TRAIN, 8))

EST_PY = r'''TEXTS = {
    "the question (golden row lk-06)": "What is the notice period for a confirmed E3?",
    "the same question in Hindi": "__HINDI__",
    "an Indian amount (FIN-02)": "Purchases up to Rs 2,00,000 are approved by the function head.",
    "a whole clause (NP-03)": __NP03__,
}
def api_estimate(text):
    """services/rag-api/context_budget.py, estimate_tokens(): four characters a token."""
    return max(1, len(text) // 4)
def worker_estimate(text):
    """services/ingest/indexer.py, batches(): CHARS_PER_TOKEN = 3."""
    return max(1, len(text) // 3)
print(f"{'':32} {'characters':>10} {'bytes':>6} {'words':>6} {'len // 4':>9} {'len // 3':>9}")
for name, text in TEXTS.items():
    print(f"{name:32} {len(text):10} {len(text.encode('utf-8')):6} {len(text.split()):6} {api_estimate(text):9} {worker_estimate(text):9}")'''.replace(
    "__HINDI__", HINDI).replace("__NP03__", py_lines(CLAUSE["NP-03"], 30))

PRICE_PY = r'''MODEL = "gemini-3.6-flash"
PRICES = {MODEL: (1.50, 7.50)}     # USD per 1M tokens, input and output: shared/prices.py, the standard price
USD_INR = 85                       # shared/prices.py: the course-wide rate
def price(tokens_in, tokens_out=0):
    """Dollars, then rupees: the arithmetic of the kit's usd() and cost.price(), without the cache."""
    usd_in, usd_out = PRICES[MODEL]
    usd = (tokens_in * usd_in + tokens_out * usd_out) / 1_000_000
    return usd, usd * USD_INR
Q = "What is the notice period for a confirmed E3?"
n = max(1, len(Q) // 4)            # the API's estimate: no call made yet
usd, inr = price(n)
print(f"{Q!r}: {len(Q)} characters, about {n} tokens by the estimate")
print(f"as input to {MODEL}: {n} x ${PRICES[MODEL][0]:.2f} per 1M = ${usd:.6f} = Rs {inr:.4f} at {USD_INR}, {inr * 100:.2f} paise")
usd_o, inr_o = price(0, n)
print(f"the same {n} tokens as output: ${usd_o:.6f} = Rs {inr_o:.4f}, at {PRICES[MODEL][1] / PRICES[MODEL][0]:.0f} times the input rate")
print(f"a lakh such questions as input: Rs {inr * 100_000:.2f}")'''

COUNT_PY = r'''import os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from google import genai
client = genai.Client(enterprise=True, project=os.environ["PROJECT"], location="global")   # Gemini 3 is served from global, as in the kit
MODEL = "gemini-3.6-flash"
PRICES = {MODEL: (1.50, 7.50)}     # shared/prices.py, as in step 5
USD_INR = 85
def price(tokens_in, tokens_out=0):
    """Dollars, then rupees, as in step 5."""
    usd_in, usd_out = PRICES[MODEL]
    usd = (tokens_in * usd_in + tokens_out * usd_out) / 1_000_000
    return usd, usd * USD_INR
TEXTS = {
    "the question": "What is the notice period for a confirmed E3?",
    "the same in Hindi": "__HINDI__",
    "an Indian amount": "Purchases up to Rs 2,00,000 are approved by the function head.",
}
for name, text in TEXTS.items():
    n = client.models.count_tokens(model=MODEL, contents=text).total_tokens   # the model's own count: no charge
    usd, inr = price(n)
    print(f"{name:17} {len(text):2} characters  estimate {max(1, len(text) // 4):2}  counted {n:2}  "
          f"as input ${usd:.6f} = Rs {inr:.4f} at {USD_INR}")'''.replace("__HINDI__", HINDI)

CLAUSES_SRC = ("CLAUSES = {\n"
               + "".join(f'    "{k}": {py_lines(CLAUSE[k], 4 + len(k) + 4)},\n' for k in ("IT-SEC-04", "EXP-12", "PR-05"))
               + "}\n"
               + f'QUESTIONS = {{"lk-05": "{Q_USB}",\n             "reworded": "{REWORDED}"}}')

COS_PY = r'''import re
import numpy as np
def cosine(a, b):
    """The cosine of the angle between a and b: 1 the same direction, 0 at right angles, -1 opposite."""
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))
a, b = np.array([3.0, 4.0]), np.array([4.0, 3.0])
print("a", a, " b", b)
print(f"cosine(a, b)       {cosine(a, b):7.4f}")
print(f"cosine(a, 10 * a)  {cosine(a, 10 * a):7.4f}   the length does not count, only the direction")
print(f"cosine(a, [-4, 3]) {cosine(a, np.array([-4.0, 3.0])):7.4f}   at right angles")
print(f"cosine(a, -a)      {cosine(a, -a):7.4f}   opposite")
u, v = a / np.linalg.norm(a), b / np.linalg.norm(b)
print(f"at length 1 the dot product is the cosine: {float(u @ v):.4f}")
__CLAUSES__
def words(text):
    """The text's words: lower-case runs of letters and digits."""
    return re.findall(r"[a-z0-9]+", text.lower())
vocab = sorted({w for text in [*CLAUSES.values(), *QUESTIONS.values()] for w in words(text)})
def counts(text):
    """A vector you can read: one dimension per word of the vocabulary, its value the word's count in the text."""
    return np.array([words(text).count(w) for w in vocab], dtype=float)
print(f"\nword-count vectors: {len(vocab)} dimensions, one per distinct word")
for q, question in QUESTIONS.items():
    print(f"{q:9}", "  ".join(f"{name} {cosine(counts(question), counts(clause)):.4f}" for name, clause in CLAUSES.items()),
          "  shared with IT-SEC-04:", sorted(set(words(question)) & set(words(CLAUSES["IT-SEC-04"]))))'''.replace("__CLAUSES__", CLAUSES_SRC)

EMBED_PY = r'''import os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
import numpy as np
from google import genai
client = genai.Client(enterprise=True, project=os.environ["PROJECT"], location="us-central1")   # embeddings are regional, as in the kit
MODEL, DIMS = "text-embedding-005", 768
__CLAUSES__
def embed(texts, task_type):
    """One request: DIMS numbers per text, under the task type given. Returns the response and the vectors."""
    r = client.models.embed_content(model=MODEL, contents=list(texts),
                                    config={"output_dimensionality": DIMS, "task_type": task_type})
    return r, np.array([e.values for e in r.embeddings])
def cosine(a, b):
    """Step 7's cosine: the dot product over the product of the lengths."""
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))
rd, D = embed(CLAUSES.values(), "RETRIEVAL_DOCUMENT")    # the worker's task type for passages (indexer.py)
rq, Q = embed(QUESTIONS.values(), "RETRIEVAL_QUERY")     # the API's task type for questions (retriever.py)
print("clauses", D.shape, " questions", Q.shape, " lengths", np.linalg.norm(D, axis=1).round(4), np.linalg.norm(Q, axis=1).round(4))
print("IT-SEC-04 begins", D[0, :4].round(4))
print("tokens per text, as the model read them:", [getattr(e.statistics, "token_count", None) for e in [*rd.embeddings, *rq.embeddings]])
for q, qv in zip(QUESTIONS, Q):
    print(f"{q:9}", "  ".join(f"{name} {cosine(qv, dv):.4f}" for name, dv in zip(CLAUSES, D)))
sent = sum(len(t) for t in [*CLAUSES.values(), *QUESTIONS.values()])
billed = [getattr(r.metadata, "billable_character_count", None) for r in (rd, rq)]
print(f"characters sent {sent}, billable as reported {billed}: at most Rs {sent / 1000 * 0.000025 * 85:.4f}")'''.replace("__CLAUSES__", CLAUSES_SRC)

OFFLINE = {"bpe": BPE_PY, "est": EST_PY, "price": PRICE_PY, "cos": COS_PY}
LIVE = {"count": COUNT_PY, "embed": EMBED_PY}
for name, body in OFFLINE.items():
    assert "google" not in body and "PROJECT" not in body, name          # offline: nothing in it can reach a cloud
for name, body in LIVE.items():
    assert 'warnings.filterwarnings("ignore", category=UserWarning)' in body and "genai.Client(enterprise=True" in body, name
assert 'location="global"' in COUNT_PY and f'location="{EMBED_LOCATION}"' in EMBED_PY
assert f'"{DOC_TASK}"' in EMBED_PY and f'"{QUERY_TASK}"' in EMBED_PY and f'"{EMBED_MODEL}", {EMBED_DIMS}' in EMBED_PY
# every cell that prices carries the kit's own constants, and every cell that estimates, the kit's own rules
for body in (PRICE_PY, COUNT_PY):
    assert f'PRICES = {{MODEL: ({USD_IN:.2f}, {USD_OUT:.2f})}}' in body and f'MODEL = "{MODEL}"' in body
    assert re.search(rf"^USD_INR = {USD_INR}\b", body, re.M)
assert "max(1, len(text) // 4)" in EST_PY and f"max(1, len(text) // {CHARS_PER_TOKEN})" in EST_PY
for body in (BPE_PY, EST_PY, PRICE_PY, COUNT_PY):
    assert Q in body
# the cosine cell and the embedding cell carry the same three clauses and two questions, the kit's words exactly
assert CLAUSES_SRC in COS_PY and CLAUSES_SRC in EMBED_PY
_ns = {}
exec(CLAUSES_SRC, _ns)
assert _ns["CLAUSES"] == {k: CLAUSE[k] for k in ("IT-SEC-04", "EXP-12", "PR-05")} and _ns["QUESTIONS"] == {"lk-05": Q_USB, "reworded": REWORDED}


def run_cell(body: str) -> str:
    """The cell as a learner runs it: a fresh interpreter (this one, the Basics venv) reading the body from stdin,
    with nothing from Google's credentials in its environment."""
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GOOGLE_", "CLOUDSDK_"))}
    env.update(PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run([sys.executable, "-"], input=body, capture_output=True, text=True, encoding="utf-8", env=env,
                       cwd=str(HERE))
    assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stdout[-1500:], r.stderr[-3000:])
    return r.stdout.rstrip("\n")


OUT = {name: run_cell(body) for name, body in OFFLINE.items()}


def namespace(body: str) -> tuple:
    """The same cell run in this process, for the values the page and the meter reuse: (its names, its output).
    The output must be the subprocess's, line for line."""
    ns, buf = {"__name__": "__main__"}, io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(body, "<cell>", "exec"), ns)
    return ns, buf.getvalue().rstrip("\n")


# ------------------------------------------------------------------ step 3: the toy tokenizer, its numbers pinned
BPE, bpe_out = namespace(BPE_PY)
assert bpe_out == OUT["bpe"], (bpe_out, OUT["bpe"])
MERGES = [list(m) for m in BPE["merges"]]
enc = BPE["encode"]
N_MERGES, TRAIN_CHARS, TRAIN_DISTINCT = len(MERGES), len(TRAIN), len(set(TRAIN))
Q_PIECES = enc(Q)
assert BPE["TRAIN"] == TRAIN
assert enc(" notice") == [" notice"] and enc("notice") == ["no", "tice"] and enc("Notice") == ["N", "o", "tice"], (enc("notice"), enc("Notice"))
assert enc("Bengaluru") == list("Bengaluru")                     # never seen: one piece per letter
assert {" notice", " period", " the"} <= set(Q_PIECES) and enc(" confirmed")[0] == " "   # seen twice or more: whole; once: in parts
assert "".join(Q_PIECES) == Q and "".join(enc(HINDI)) == HINDI      # the pieces always join back to the text
assert f"{N_MERGES} merges learned" in OUT["bpe"] and f"-> {len(Q_PIECES):2} pieces" in OUT["bpe"]
FIRST_TEN = [a + b for a, b in MERGES[:10]]
assert FIRST_TEN[0] == "on" and " notice" in [a + b for a, b in MERGES] and " probation" in [a + b for a, b in MERGES]
NOTICE_RANK = [a + b for a, b in MERGES].index(" notice") + 1

# ------------------------------------------------------------------ step 4: the estimates against characters, bytes and words
EST, est_out = namespace(EST_PY)
assert est_out == OUT["est"]
TEXTS4 = EST["TEXTS"]
assert list(TEXTS4.values()) == [Q, HINDI, AMOUNT, CLAUSE["NP-03"]]
for text in TEXTS4.values():
    assert EST["api_estimate"](text) == context_budget.estimate_tokens(text)                       # the kit's own function
    assert EST["worker_estimate"](text) == max(1, len(text) // CHARS_PER_TOKEN)
Q_CHARS, Q_EST4, Q_EST3 = len(Q), context_budget.estimate_tokens(Q), max(1, len(Q) // CHARS_PER_TOKEN)
H_CHARS, H_BYTES, H_EST4 = len(HINDI), len(HINDI.encode("utf-8")), context_budget.estimate_tokens(HINDI)
NP_CHARS, NP_EST4, NP_EST3 = len(CLAUSE["NP-03"]), context_budget.estimate_tokens(CLAUSE["NP-03"]), max(1, len(CLAUSE["NP-03"]) // CHARS_PER_TOKEN)
assert len(Q.encode("utf-8")) == Q_CHARS and len(CLAUSE["NP-03"].encode("utf-8")) == NP_CHARS     # English: a byte a character
assert abs(H_CHARS - Q_CHARS) <= 5 and abs(H_EST4 - Q_EST4) <= 1 and H_BYTES > 2 * H_CHARS       # Hindi: the estimate barely moves; the bytes do
assert all(ord(ch) < 128 or 0x0900 <= ord(ch) <= 0x097F for ch in HINDI)                           # ASCII and Devanagari only, and
assert all(len(ch.encode("utf-8")) == 3 for ch in HINDI if ord(ch) >= 128)                         # every Devanagari letter and sign is three bytes
for name, text in TEXTS4.items():
    assert f"{name:32} {len(text):10} {len(text.encode('utf-8')):6} {len(text.split()):6} {context_budget.estimate_tokens(text):9}" in OUT["est"]

# ------------------------------------------------------------------ step 5: the rupee line, the kit's prices
PR, price_out = namespace(PRICE_PY)
assert price_out == OUT["price"]
assert PR["PRICES"] == {MODEL: (USD_IN, USD_OUT)} and PR["USD_INR"] == USD_INR and PR["n"] == Q_EST4
usd_kit = prices.usd(MODEL, Q_EST4, 0)                                  # the kit's own function, list price
assert abs(PR["usd"] - usd_kit) < 1e-15 and abs(PR["inr"] - prices.inr(usd_kit)) < 1e-15
Q_USD, Q_INR, Q_PAISE, Q_LAKH = f"{usd_kit:.6f}", f"{prices.inr(usd_kit):.4f}", f"{prices.inr(usd_kit) * 100:.2f}", f"{prices.inr(usd_kit) * 100_000:.2f}"
usd_out_kit = prices.usd(MODEL, 0, Q_EST4)
OUT_RATIO = USD_OUT / USD_IN
assert OUT_RATIO == 5
assert f"= ${Q_USD} = Rs {Q_INR} at {USD_INR}, {Q_PAISE} paise" in OUT["price"] and f"Rs {Q_LAKH}" in OUT["price"]
assert f"${usd_out_kit:.6f} = Rs {prices.inr(usd_out_kit):.4f}, at 5 times the input rate" in OUT["price"]
INTRO_IN, INTRO_OUT = 0.75, 3.75                                       # Google's introductory price to 31 December 2026 (docstring)
assert (INTRO_IN * 2, INTRO_OUT * 2) == (USD_IN, USD_OUT)

# ------------------------------------------------------------------ step 7: cosine, in numpy
COSN, cos_out = namespace(COS_PY)
assert cos_out == OUT["cos"]
cos_fn = COSN["cosine"]
np = COSN["np"]
A, B = COSN["a"], COSN["b"]
assert round(cos_fn(A, B), 4) == 0.96 and round(cos_fn(A, 10 * A), 4) == 1.0
assert round(cos_fn(A, np.array([-4.0, 3.0])), 4) == 0.0 and round(cos_fn(A, -A), 4) == -1.0
assert "cosine(a, b)        0.9600" in OUT["cos"] and "cosine(a, -a)      -1.0000" in OUT["cos"] and "the dot product is the cosine: 0.9600" in OUT["cos"]
words4 = COSN["words"]
cnt = COSN["counts"]
CL = COSN["CLAUSES"]
assert CL == {k: CLAUSE[k] for k in ("IT-SEC-04", "EXP-12", "PR-05")} and COSN["QUESTIONS"] == {"lk-05": Q_USB, "reworded": REWORDED}
WC = {q: {k: cos_fn(cnt(qt), cnt(CL[k])) for k in CL} for q, qt in COSN["QUESTIONS"].items()}
SHARED_USB = sorted(set(words4(Q_USB)) & set(words4(CL["IT-SEC-04"])))
SHARED_EXP = sorted(set(words4(REWORDED)) & set(words4(CL["EXP-12"])))
SHARED_PR = sorted(set(words4(Q_USB)) & set(words4(CL["PR-05"])))
assert WC["reworded"]["IT-SEC-04"] == 0.0 and WC["reworded"]["EXP-12"] > 0 and SHARED_EXP == ["at"]
assert WC["lk-05"]["IT-SEC-04"] > WC["lk-05"]["PR-05"] > 0 and SHARED_USB == ["are", "company", "on", "usb"] and SHARED_PR == ["on"]
assert WC["lk-05"]["EXP-12"] == 0.0 and WC["reworded"]["PR-05"] == 0.0
assert max(WC["reworded"], key=WC["reworded"].get) == "EXP-12" and max(WC["lk-05"], key=WC["lk-05"].get) == "IT-SEC-04"
assert f"{len(COSN['vocab'])} dimensions, one per distinct word" in OUT["cos"]
fmt4 = lambda x: f"{x:.4f}"  # noqa: E731
assert all(f"{name} {fmt4(WC[q][name])}" in OUT["cos"] for q in WC for name in CL)

# ------------------------------------------------------------------ the live runs: recorded from the author's run (RUN_LIST.md)
REC = {"count": pb.recorded(LESSON, "count_tokens.txt"), "embed": pb.recorded(LESSON, "embeddings.txt")}
COUNT_TEXTS = {"the question": Q, "the same in Hindi": HINDI, "an Indian amount": AMOUNT}
if not REC["count"].startswith("[awaiting"):
    # the author's run: every line's estimate and rupees must be the kit's arithmetic on the count it printed
    lines = REC["count"].splitlines()
    assert len(lines) == 3, lines
    for (name, text), line in zip(COUNT_TEXTS.items(), lines):
        m = re.fullmatch(r"(.{17}) +(\d+) characters  estimate +(\d+)  counted +(\d+)  as input \$([\d.]+) = Rs ([\d.]+) at (\d+)", line)
        assert m and m.group(1).strip() == name and int(m.group(2)) == len(text) and int(m.group(3)) == context_budget.estimate_tokens(text), line
        n = int(m.group(4))
        assert m.group(5) == f"{prices.usd(MODEL, n, 0):.6f}" and m.group(6) == f"{prices.inr(prices.usd(MODEL, n, 0)):.4f}", line
if not REC["embed"].startswith("[awaiting"):
    rec = REC["embed"]
    assert "clauses (3, 768)  questions (2, 768)" in rec, rec
    for v in re.findall(r"(?:IT-SEC-04|EXP-12|PR-05) (-?[\d.]+)", rec):
        assert -1.0 <= float(v) <= 1.0, v

EMBED_SENT = sum(len(t) for t in [*CL.values(), Q_USB, REWORDED])
EMBED_USD_PER_1K_CHARS = 0.000025                                     # Google's list price for text embeddings, online (docstring)
EMBED_MAX_TOKENS = 2048                                               # text-embedding-005 reads this much of one text (docstring)
EMBED_REQ_TEXTS, EMBED_REQ_TOKENS = 250, 20_000                       # the embedding API's ceiling per request (docstring)
assert EMBED_BATCH <= EMBED_REQ_TEXTS and EMBED_TOKENS < EMBED_REQ_TOKENS   # the worker's batches sit under it
EMBED_RS = f"{EMBED_SENT / 1000 * EMBED_USD_PER_1K_CHARS * USD_INR:.4f}"
assert EMBED_PY.endswith('at most Rs {sent / 1000 * 0.000025 * 85:.4f}")') and USD_INR == 85
EMBED_PAISE = f"{EMBED_SENT / 1000 * EMBED_USD_PER_1K_CHARS * USD_INR * 100:.2f}"

if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    print("merges", N_MERGES, "train", TRAIN_CHARS, TRAIN_DISTINCT, "q pieces", len(Q_PIECES), "embed chars", EMBED_SENT, EMBED_RS)
    for k, v in LIVE.items():
        print(f"===== live {k}\n{heredoc(v)}")
    sys.exit(0)

# the run list carries every live cell exactly as the page shows it, and the costs the page states
run_list = (HERE / "RUN_LIST.md").read_text(encoding="utf-8")
for name, body in LIVE.items():
    assert heredoc(body) in run_list, f"RUN_LIST.md does not carry the {name} cell as the page shows it"
assert f"Rs {EMBED_RS} ({EMBED_PAISE} paise)" in run_list and f"{EMBED_SENT} characters" in run_list
assert "USD 0.000025 per 1,000 characters online" in run_list and f"Rs {USD_INR} to the dollar" in run_list

# ------------------------------------------------------------------ verbatim kit excerpts
EXCERPTS = {
    "estimate": ("services/rag-api/context_budget.py - estimate_tokens(): the API's estimate, four characters a token",
                 block(CB, "def estimate_tokens(", n=2)),
    "batches": ("services/ingest/indexer.py - the worker's estimate: three characters a token, for the embedding batches",
                block(INDEXER, "EMBED_BATCH = 250", n=3) + "\n...\n" + block(INDEXER, "def batches(", end="def embed_all(")),
    "prices": ("shared/prices.py - the kit's prices, USD per 1M tokens, and the rupee rate",
               block(PRICES_PY, "USD_INR = 85", end="def usd(") + "\n\n" + block(PRICES_PY, "def usd(") + "\n\n" + block(PRICES_PY, "def inr(", n=2)),
    "cost_price": ("services/rag-api/cost.py - price(): how lesson 3.4 prices an answer, in both currencies",
                   block(COST, "def price(")),
    "gen_client": ("services/rag-api/generator.py - the generation client, on the global location",
                   block(GEN, "_client = genai.Client(enterprise=True", n=1)),
    "count_fn": ("services/rag-api/context_budget.py - the module's promise: a real counter can replace the estimate",
                 block(CB, "Pure Python: no cloud calls.", n=2)),
    "embed_consts": ("services/ingest/indexer.py - the worker's embedding: model, task type, dimension, and a regional client",
                     block(INDEXER, 'EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL"', n=10)),
    "embed_all": ("services/ingest/indexer.py - embed_all(): every passage under RETRIEVAL_DOCUMENT, 768 numbers each",
                  block(INDEXER, "def embed_all(", end="def valid_vector(")),
    "embed_query": ("services/rag-api/retriever.py - embed_query(): every question under RETRIEVAL_QUERY",
                    block(RETRIEVER, "def embed_query(", end="def _firestore_fallback(")),
    "fallback": ("services/rag-api/retriever.py - the Firestore rung: nearest by cosine distance, turned back into a similarity",
                 block(RETRIEVER, "    hits = (query", end='        d.pop("embedding", None)')),
    "vector_tf": ("terraform/vector.tf - the Vector Search index: 768 dimensions, compared by dot product",
                  block(VECTOR_TF, "    config {", n=4)),
    "semcache": ("services/rag-api/semantic_cache.py - the answer cache: a threshold on cosine similarity, and why it is 0.95",
                 block(SEMCACHE, "# 0.95, not 0.92", n=3) + "\n...\n" + block(SEMCACHE, "        # COSINE distance: smaller is closer. 1 - d", n=3)),
}
assert EXCERPTS["estimate"][1].rstrip().endswith("return max(1, len(text) // 4)")
assert EXCERPTS["batches"][1].rstrip().endswith("return out") and "CHARS_PER_TOKEN = 3" in EXCERPTS["batches"][1]
assert EXCERPTS["prices"][1].rstrip().endswith("return usd_amount * USD_INR") and '"gemini-3.6-flash": (1.50, 7.50)' in EXCERPTS["prices"][1]
assert EXCERPTS["cost_price"][1].rstrip().endswith('"cached_tokens": cached_tokens}')
assert EXCERPTS["embed_consts"][1].rstrip().endswith(")") and 'location="us-central1",' in EXCERPTS["embed_consts"][1]
assert EXCERPTS["embed_all"][1].rstrip().endswith("return out")
assert EXCERPTS["embed_query"][1].rstrip().endswith("return resp.embeddings[0].values")
assert EXCERPTS["fallback"][1].rstrip().endswith('d["score"] = 1.0 - d.pop("d", 1.0)')
assert EXCERPTS["vector_tf"][1].rstrip().endswith('distance_measure_type       = "DOT_PRODUCT_DISTANCE"')
assert EXCERPTS["semcache"][1].rstrip().endswith("break")
fill = filler(EXCERPTS, window)


# ------------------------------------------------------------------ the cell windows
def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


HERE_RUN = "run on your laptop, in ~/basics-venv"
CELL_LABELS = {
    "bpe": f"{HERE_RUN} (a Python cell; Rs 0, nothing leaves the machine)",
    "est": f"{HERE_RUN} (a Python cell; Rs 0, nothing leaves the machine)",
    "price": f"{HERE_RUN} (a Python cell; Rs 0, arithmetic only)",
    "count": f"{HERE_RUN}, after the setup's Gemini block (a Python cell; three count_tokens calls, no charge)",
    "cos": f"{HERE_RUN} (a Python cell; Rs 0, nothing leaves the machine)",
    "embed": f"{HERE_RUN}, after the setup's Gemini block (a Python cell; two embedding requests, at most Rs {EMBED_RS})",
}
OUT_LABELS = {
    "bpe": "(this cell's own output, produced when this page was built; yours matches it piece for piece)",
    "est": "(this cell's own output, produced when this page was built; yours matches it digit for digit)",
    "price": "(this cell's own output, produced when this page was built, with the kit's prices)",
    "count": "(recorded from the author's run of this cell; the characters and the estimates are fixed by the texts)",
    "cos": "(this cell's own output, produced when this page was built)",
    "embed": "(recorded from the author's run of this cell)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], heredoc(v)) for k, v in {**OFFLINE, **LIVE}.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})
WIN["OUT_COUNT"] = out_window(OUT_LABELS["count"], REC["count"])
WIN["OUT_EMBED"] = out_window(OUT_LABELS["embed"], REC["embed"])

# ------------------------------------------------------------------ the token meter: the samples, the merges, the kit's rules
SAMPLES = [("q", "The question (golden row lk-06)", Q), ("hi", "The same question in Hindi", HINDI),
           ("amt", "An Indian amount (FIN-02)", AMOUNT), ("np", "A whole clause (NP-03)", CLAUSE["NP-03"]),
           ("blr", "A word the training text never had", "Bengaluru")]
TM_OPTIONS = "".join(f'<option value="{k}">{html.escape(label)}</option>' for k, label, _ in SAMPLES)
METER = {"merges": MERGES, "samples": {k: text for k, _, text in SAMPLES}, "usdIn": USD_IN, "usdOut": USD_OUT, "usdInr": USD_INR,
         "api": 4, "worker": CHARS_PER_TOKEN, "model": MODEL}


def meter_line(text: str) -> dict:
    """What the meter prints for a text, computed here: node must print the same."""
    n = context_budget.estimate_tokens(text)
    usd_i, usd_o = prices.usd(MODEL, n, 0), prices.usd(MODEL, 0, n)
    return {"pieces": enc(text), "chars": len(text), "bytes": len(text.encode("utf-8")), "words": len(text.split()),
            "api": n, "worker": max(1, len(text) // CHARS_PER_TOKEN),
            "usdIn": f"{usd_i:.6f}", "inrIn": f"{prices.inr(usd_i):.4f}", "paise": f"{prices.inr(usd_i) * 100:.2f}",
            "usdOut": f"{usd_o:.6f}", "inrOut": f"{prices.inr(usd_o):.4f}", "lakh": f"{prices.inr(usd_i) * 100_000:.2f}"}


METER_JS = r"""var D = __METER__;
var RX = / ?[A-Za-z]+| ?[0-9]| ?[^\sA-Za-z0-9]/gu;
function words(text){ return text.match(RX) || []; }
function merge(w, a, b){ var out = [], i = 0;
  while (i < w.length){ if (i + 1 < w.length && w[i] === a && w[i + 1] === b){ out.push(a + b); i += 2; } else { out.push(w[i]); i += 1; } }
  return out; }
function encode(text){ var out = [];
  words(text).forEach(function(word){ var w = Array.from(word); D.merges.forEach(function(m){ w = merge(w, m[0], m[1]); }); out = out.concat(w); });
  return out; }
function chars(text){ return Array.from(text).length; }
function line(text){
  var n = Math.max(1, Math.floor(chars(text) / D.api)), usdI = (n * D.usdIn + 0 * D.usdOut) / 1000000, usdO = (0 * D.usdIn + n * D.usdOut) / 1000000;
  var inrI = usdI * D.usdInr, inrO = usdO * D.usdInr;
  return {pieces: encode(text), chars: chars(text), bytes: new TextEncoder().encode(text).length, words: text.split(/\s+/).filter(Boolean).length,
    api: n, worker: Math.max(1, Math.floor(chars(text) / D.worker)), usdIn: usdI.toFixed(6), inrIn: inrI.toFixed(4), paise: (inrI * 100).toFixed(2),
    usdOut: usdO.toFixed(6), inrOut: inrO.toFixed(4), lakh: (inrI * 100000).toFixed(2)}; }
window.__tm = {line: line};
var root = document.getElementById('meter'); if (!root) { return; }
var sel = document.getElementById('tm-sample'), own = document.getElementById('tm-own'), shown = document.getElementById('tm-text'),
    chips = document.getElementById('tm-chips'), sum = document.getElementById('tm-sum'), rupee = document.getElementById('tm-rupee');
function render(){
  var text = own.value.length ? own.value : D.samples[sel.value], r = line(text);
  shown.textContent = 'Text: ' + (text.length ? text : '(empty)');
  chips.textContent = '';
  r.pieces.forEach(function(p){ var s = document.createElement('span'); s.textContent = p.replace(/ /g, '·'); chips.appendChild(s); });
  sum.textContent = r.chars + ' characters, ' + r.bytes + ' bytes, ' + r.words + (r.words === 1 ? ' word' : ' words') + ' | toy pieces ' + r.pieces.length +
    ' | the kit estimates ' + r.api + ' tokens (len // ' + D.api + ', the API) or ' + r.worker + ' (len // ' + D.worker + ', the worker)';
  rupee.textContent = 'Priced by the API estimate at ' + D.model + "'s standard rates: " + r.api + ' tokens in = $' + r.usdIn + ' = Rs ' + r.inrIn +
    ' at ' + D.usdInr + ' (' + r.paise + ' paise); as output $' + r.usdOut + ' = Rs ' + r.inrOut + '; a lakh of these as input: Rs ' + r.lakh;
}
sel.addEventListener('change', function(){ own.value = ''; render(); });
own.addEventListener('input', render);
render();"""
METER_JS = METER_JS.replace("__METER__", json.dumps(METER, ensure_ascii=False, separators=(",", ":")))
JS = "<script>\n(function(){\n'use strict';\n" + METER_JS.replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

# node runs the meter's functions on every sample and on texts that test the edges; every field must be the Python's
TESTS = [text for _, _, text in SAMPLES] + [" notice", "notice", "Notice", "Can I encash leave during probation?", "a  b\tc", "x", ""]
NODE = ("var window = {}, document = {getElementById: function(){ return null; }};\n"
        "(new Function('window', 'document', " + json.dumps(METER_JS) + "))(window, document);\n"
        "var T = " + json.dumps(TESTS, ensure_ascii=False) + ";\n"
        "process.stdout.write(JSON.stringify(T.map(function(t){ return window.__tm.line(t); })));\n")
node = subprocess.run(["node", "-"], input=NODE, capture_output=True, text=True, encoding="utf-8")
assert node.returncode == 0, node.stderr[-800:]
for text, got in zip(TESTS, json.loads(node.stdout)):
    want = meter_line(text)
    assert got == want, (text, got, want)
N_METER = len(TESTS)

# ------------------------------------------------------------------ the numbers the prose states
STATS = {
    "MODEL": MODEL, "GEN_LOCATION": GEN_LOCATION, "USD_IN": f"{USD_IN:.2f}", "USD_OUT": f"{USD_OUT:.2f}", "USD_INR": str(USD_INR),
    "OUT_RATIO": f"{OUT_RATIO:.0f}", "INTRO_IN": f"{INTRO_IN:.2f}", "INTRO_OUT": f"{INTRO_OUT:.2f}",
    "EMBED_MODEL": EMBED_MODEL, "EMBED_LOCATION": EMBED_LOCATION, "DIMS": str(EMBED_DIMS), "DOC_TASK": DOC_TASK, "QUERY_TASK": QUERY_TASK,
    "CPT_WORKER": str(CHARS_PER_TOKEN), "CPT_WORKER_WORD": {2: "two", 3: "three", 4: "four", 5: "five"}[CHARS_PER_TOKEN],
    "EMBED_BATCH": str(EMBED_BATCH), "EMBED_TOKENS": f"{EMBED_TOKENS:,}", "VECTOR_DISTANCE": VECTOR_DISTANCE, "CACHE_THRESHOLD": CACHE_THRESHOLD,
    "Q": html.escape(Q), "Q_CHARS": str(Q_CHARS), "Q_EST4": str(Q_EST4), "Q_EST3": str(Q_EST3), "Q_PIECES": str(len(Q_PIECES)),
    "H_CHARS": str(H_CHARS), "H_BYTES": str(H_BYTES), "H_EST4": str(H_EST4),
    "NP_CHARS": str(NP_CHARS), "NP_EST4": str(NP_EST4), "NP_EST3": str(NP_EST3),
    "N_MERGES": str(N_MERGES), "TRAIN_CHARS": str(TRAIN_CHARS), "TRAIN_DISTINCT": str(TRAIN_DISTINCT), "VOCAB": str(TRAIN_DISTINCT + N_MERGES),
    "NOTICE_RANK": str(NOTICE_RANK), "BLR": str(len("Bengaluru")),
    "Q_USD": Q_USD, "Q_INR": Q_INR, "Q_PAISE": Q_PAISE, "Q_LAKH": Q_LAKH,
    "WC_USB_SEC": fmt4(WC["lk-05"]["IT-SEC-04"]), "WC_USB_PR": fmt4(WC["lk-05"]["PR-05"]), "WC_RW_EXP": fmt4(WC["reworded"]["EXP-12"]),
    "W_USB": str(len(Q_USB.split())), "W_LONG": str(max(len(CL[k].split()) for k in CL)),
    "EMBED_SENT": str(EMBED_SENT), "EMBED_RS": EMBED_RS, "EMBED_PAISE": EMBED_PAISE, "EMBED_LIST": f"{EMBED_USD_PER_1K_CHARS:.6f}",
    "EMBED_MAX_TOKENS": f"{EMBED_MAX_TOKENS:,}", "EMBED_REQ_TEXTS": str(EMBED_REQ_TEXTS), "EMBED_REQ_TOKENS": f"{EMBED_REQ_TOKENS:,}",
    "N_METER": str(N_METER), "TM_OPTIONS": TM_OPTIONS,
}
assert not re.findall(r"%%(\w+)%%", "".join(STATS.values())), "a value carries a token"


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: {MODEL} on {GEN_LOCATION} at ${USD_IN}/{USD_OUT} per 1M, Rs {USD_INR} | estimates len // 4 and len // {CHARS_PER_TOKEN} | "
      f"{EMBED_MODEL} on {EMBED_LOCATION}, {EMBED_DIMS} dims, {DOC_TASK}/{QUERY_TASK} | toy tokenizer {N_MERGES} merges | "
      f"the question: {Q_CHARS} chars, {Q_EST4} tokens by the estimate, ${Q_USD} = Rs {Q_INR} | meter checked on {N_METER} texts")
