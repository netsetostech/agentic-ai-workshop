"""Build lesson B.3 from its three parts, the shared template, the Basics laptop setup and verbatim kit excerpts.

Read a transformer block, with layer normalization. One block of the 2017 paper's design, built in numpy on a
six-word sentence: the words' vectors (four hand-set meaning numbers, plus a position signal of two sine waves),
one attention head (one word back, read from the waves), a second head (the word each word fits with, read from
the meaning numbers), the two joined and projected by W_O, the residual path, layer normalization, the
feed-forward step and the block assembled, in the paper's order and in the norm-first order of GPT-2 and later.
The kit level quotes where DocuMind meets the design: the token ceilings it plans its embedding requests around
and the prompt budget the API packs into.

Build-time proof: every cell on the page is run here, by this interpreter, exactly as a learner pastes it, and
its stdout is the expected window under it. The cells are deterministic: no random numbers, only formulas and
small hand-set integers. During the build a guard wraps numpy.round and refuses any printed number that sits
within 1e-5 of a rounding edge in its last digit, so a different processor, BLAS or numpy build cannot flip a
printed digit. The asserts below pin every number the prose states; the explorer's JSON comes from the same code.
No cell calls a network or an account, so nothing waits on the author's run (RUN_LIST.md).
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

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, window  # noqa: E402

LESSON = "B.3"
title = "<title>Lesson B.3 Read a transformer block, with layer normalization - six words, two heads, one block in numpy | Netsetos</title>\n"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.ax-controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,240px),1fr));gap:10px 16px;margin-bottom:12px;}
.ax-l{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.ax-l select{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.ax-scroll{overflow-x:auto;overscroll-behavior-x:contain;-webkit-overflow-scrolling:touch;}
.ax-grid{--ax-cell:34px;--ax-gap:3px;--ax-font:12px;--ax-pad:6px;display:grid;grid-template-columns:max-content repeat(6,minmax(var(--ax-cell),1fr));gap:var(--ax-gap);font-family:var(--mono);font-size:var(--ax-font);}
.ax-col{display:flex;align-items:flex-end;justify-content:center;font-size:var(--kicker-size);font-weight:700;color:var(--navy);padding:2px 0 4px;}
.ax-r{font:inherit;font-weight:700;color:var(--navy);background:var(--card);border:1px solid var(--border);border-radius:7px;padding:4px var(--ax-pad);text-align:right;cursor:pointer;min-height:max(34px,var(--touch));}
.ax-r.on{border-color:var(--teal);background:var(--teal-light);box-shadow:inset 3px 0 0 var(--teal);}
.ax-r:active{transform:scale(.97);}
.ax-c{display:flex;align-items:center;justify-content:center;border-radius:6px;color:var(--navy);min-height:34px;}
.ax-c.dark{color:#fff;}
.ax-c.sel{box-shadow:inset 0 0 0 2px var(--cyan);}
.ax-c.ax-m{background:repeating-linear-gradient(45deg,#f1f5f9,#f1f5f9 4px,#e2e8f0 4px,#e2e8f0 8px);color:var(--slate-light);}
.ax-sum{font-family:var(--mono);font-size:var(--kicker-size);color:var(--teal-dark);margin:10px 0 0;overflow-wrap:anywhere;line-height:1.6;}
@media (max-width: 640px){.ax-col{display:block;writing-mode:vertical-rl;justify-self:center;align-self:end;padding:4px 0;}}
@media (max-width: 380px){.ax-grid{--ax-cell:29px;--ax-gap:2px;--ax-font:11px;--ax-pad:4px;}}
@media (hover:hover) and (pointer:fine){.ax-r:hover{border-color:var(--teal);}}
"""

setup = pb.basics_setup_section()

# ------------------------------------------------------------------ verbatim kit excerpts
INDEXER, CORPUS, WORKER, CONFIG, BUDGET = ("services/ingest/indexer.py", "shared/documind_corpus.py", "services/ingest/main.py",
                                           "services/rag-api/config.py", "services/rag-api/context_budget.py")
EXCERPTS = {
    "main_chunk": ("services/ingest/main.py - the longest chunk the worker cuts", block(WORKER, "CHUNK_CHARS, CHUNK_OVERLAP = 2000, 200", n=1)),
    "indexer_consts": ("services/ingest/indexer.py - the request ceilings, and the token estimate", block(INDEXER, "EMBED_BATCH = 250", n=3)),
    "indexer_batches": ("services/ingest/indexer.py - batches(): no request over 250 texts or about 15,000 tokens", block(INDEXER, "def batches(", end="def embed_all(")),
    "corpus_doc": ("shared/documind_corpus.py - embed_batches(): the model's own ceilings, and the day the kit found them", block(CORPUS, "def embed_batches(", n=6)),
    "config_budget": ("services/rag-api/config.py - the prompt budget, and the answer's", block(CONFIG, "max_context_tokens: int = 8000", n=5)),
    "estimate": ("services/rag-api/context_budget.py - estimate_tokens(): four characters a token", block(BUDGET, "def estimate_tokens(", n=2)),
}
EX = {k: v[1] for k, v in EXCERPTS.items()}
assert EX["main_chunk"] == "CHUNK_CHARS, CHUNK_OVERLAP = 2000, 200"
assert EX["indexer_consts"] == "EMBED_BATCH = 250\nEMBED_TOKENS = 15_000\nCHARS_PER_TOKEN = 3"
assert EX["indexer_batches"].startswith("def batches(texts: list[str]) -> list[list[str]]:") and EX["indexer_batches"].rstrip().endswith("return out")
assert "tokens = max(1, len(text) // CHARS_PER_TOKEN)" in EX["indexer_batches"]
assert "if cur and (len(cur) >= EMBED_BATCH or cur_tokens + tokens > EMBED_TOKENS):" in EX["indexer_batches"]
assert "text-embedding-005 takes\n    250 texts per request and 20,000 tokens across them, and a request over either limit fails\n    whole" in EX["corpus_doc"]
assert "a two-thousand-character chunk is ~500 tokens" in EX["corpus_doc"] and "(6 Sept 2026)" in EX["corpus_doc"]
assert EX["config_budget"].startswith("    max_context_tokens: int = 8000") and EX["config_budget"].endswith("    max_answer_tokens: int = 2048")
assert EX["estimate"] == "def estimate_tokens(text: str) -> int:\n    return max(1, len(text) // 4)"
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
src = {p: (KIT / p).read_text(encoding="utf-8") for p in (INDEXER, CORPUS, WORKER, CONFIG, BUDGET, "services/rag-api/generator.py")}
assert "# 4.1's chunker, the shape every lesson's corpus has: ~500 tokens per chunk, an\n" in src[WORKER]       # the comment above CHUNK_CHARS
assert 'EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-005")' in src[INDEXER] and "EMBEDDING_DIMENSIONS = 768" in src[INDEXER]
assert "real counter such as client.models.count_tokens is injected" in src[BUDGET]
assert "return TokenBudget.fit(settings.max_context_tokens, fixed, count_fn, answer=settings.max_answer_tokens)" in src["services/rag-api/generator.py"]
assert "context, packed, dropped = pack_chunks(chunks, _budget(query).chunks, estimate_tokens)" in src["services/rag-api/generator.py"]
assert "r, model = _call_or_fallback(prompt, packed, tenant_id, settings.max_answer_tokens, model)" in src["services/rag-api/generator.py"]
# indexer.py's batches(), lifted out with its three constants and run on 2,000-character chunks (indexer.py builds its clients at import)
NS = {}
exec(EX["indexer_consts"], NS)
for node in ast.parse(src[INDEXER]).body:
    if isinstance(node, ast.FunctionDef) and node.name == "batches":
        exec(compile(ast.Module([node], []), INDEXER, "exec"), NS)
KIT_TEXTS_PER_REQUEST = len(NS["batches"](["x" * 2000] * 60)[0])
assert KIT_TEXTS_PER_REQUEST == 22, KIT_TEXTS_PER_REQUEST

# ------------------------------------------------------------------ the cells: run here exactly as a learner pastes them
PRE_X = '''import warnings
warnings.filterwarnings("ignore", category=UserWarning)
import numpy as np

words = ["the", "employee", "serves", "ninety", "days", "notice"]
meaning = np.array([[0, 0, 0, 0], [1, 0, 0, 1], [0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, -1], [1, 0, 0, 0]])
p = np.arange(6)[:, None] * np.pi / 4                                          # step 3's positions, as angles
X = np.hstack([meaning, np.sin(p), np.cos(p), np.sin(2 * p), np.cos(2 * p)])   # step 3's X: 6 words x 8 numbers
columns = ["thing", "action", "amount", "who/when", "slow sin", "slow cos", "fast sin", "fast cos"]

def show(title, M, d=2, rows=words, cols=words):
    print(title)
    print(" " * 10 + "".join(f"{c:>9}" for c in cols))
    for name, row in zip(rows, np.round(M, d) + 0.0):
        print(f"{name:>10}" + "".join(f"{v:9.{d}f}" for v in row))
'''

PRE_HEADS = '''
def softmax(S):
    e = np.exp(S - S.max(axis=1, keepdims=True))
    return e / e.sum(axis=1, keepdims=True)

c, s = np.cos(np.pi / 4), np.sin(np.pi / 4)                    # head 1: one word back (step 4)
W_Q1 = np.zeros((8, 4)); W_Q1[4:] = 4 * np.array([[c, s, 0, 0], [-s, c, 0, 0], [0, 0, 0, 1], [0, 0, -1, 0]])
W_K1 = np.zeros((8, 4)); W_K1[4:] = np.eye(4)
W_V1 = np.zeros((8, 4)); W_V1[:4] = np.eye(4)
W_Q2, W_K2, W_V2 = np.zeros((8, 4)), np.zeros((8, 4)), W_V1.copy()   # head 2: the word it fits with
W_Q2[0, 0], W_K2[1, 0] = 6, 1                                  # a thing asks for an action
W_Q2[1, 1], W_K2[3, 1] = 6, 1                                  # an action asks for a person
W_Q2[2, 2], W_K2[3, 2] = 6, -1                                 # an amount asks for a time
W_O = np.zeros((8, 8)); W_O[:4, :4] = W_O[4:, :4] = 0.5 * np.eye(4)   # half of each head, into the meaning columns

def head(Z, W_Q, W_K, W_V, causal=False):
    scores = (Z @ W_Q) @ (Z @ W_K).T / np.sqrt(W_Q.shape[1])
    if causal:                                                  # a word may not look at the words after it
        scores = np.where(np.triu(np.ones(scores.shape), 1) == 1, -np.inf, scores)
    weights = softmax(scores)
    return weights, weights @ (Z @ W_V)

def attention(Z):                                               # both heads, side by side, then W_O
    return np.hstack([head(Z, W_Q1, W_K1, W_V1)[1], head(Z, W_Q2, W_K2, W_V2)[1]]) @ W_O
'''

VECTORS_PY = '''import warnings
warnings.filterwarnings("ignore", category=UserWarning)
import numpy as np

words = ["the", "employee", "serves", "ninety", "days", "notice"]
# each word's own four numbers, set by hand: thing, action, amount, who/when (+1 a person, -1 a time)
meaning = np.array([[0, 0, 0, 0],      # the
                    [1, 0, 0, 1],      # employee: a thing, and a person
                    [0, 1, 0, 0],      # serves: an action
                    [0, 0, 1, 0],      # ninety: an amount
                    [1, 0, 0, -1],     # days: a thing, and a time
                    [1, 0, 0, 0]])     # notice: a thing
# each position's four numbers: a slow wave that turns 45 degrees a word, and a fast one that turns 90
p = np.arange(6)[:, None] * np.pi / 4
waves = np.hstack([np.sin(p), np.cos(p), np.sin(2 * p), np.cos(2 * p)])
word_vec = np.hstack([meaning, np.zeros((6, 4))])     # the word, in columns 0 to 3
pos_vec = np.hstack([np.zeros((6, 4)), waves])        # its position, in columns 4 to 7
X = word_vec + pos_vec                                # what the block reads: 6 words x 8 numbers
columns = ["thing", "action", "amount", "who/when", "slow sin", "slow cos", "fast sin", "fast cos"]

def show(title, M, d=2, rows=words, cols=words):
    print(title)
    print(" " * 10 + "".join(f"{c:>9}" for c in cols))
    for name, row in zip(rows, np.round(M, d) + 0.0):
        print(f"{name:>10}" + "".join(f"{v:9.{d}f}" for v in row))

print("tokens:", X.shape[0], "| numbers per token:", X.shape[1])
show("X = word vector + position vector", X, cols=columns)
D = waves @ waves.T
positions = [f"pos {t}" for t in range(6)]
show("position . position: one position's waves against another's", D, rows=positions, cols=positions)
print("the same along every diagonal, so it measures distance only:",
      all(np.allclose(np.diag(D, k), np.diag(D, k)[0]) for k in range(6)))
print("every position's signal has the same length:", " ".join(f"{v:.2f}" for v in np.round(np.linalg.norm(waves, axis=1), 2)))
print("adding the two is the same as setting them side by side:", np.array_equal(X, np.hstack([meaning, waves])))'''

HEAD_PY = PRE_X + '''
def softmax(S):                                      # row by row: e to each score, over the row's total
    e = np.exp(S - S.max(axis=1, keepdims=True))     # taking the row's largest off first changes nothing but overflow
    return e / e.sum(axis=1, keepdims=True)

# head 1's three weight matrices, 8 x 4 each
c, s = np.cos(np.pi / 4), np.sin(np.pi / 4)
W_Q = np.zeros((8, 4)); W_Q[4:] = 4 * np.array([[c, s, 0, 0], [-s, c, 0, 0], [0, 0, 0, 1], [0, 0, -1, 0]])
W_K = np.zeros((8, 4)); W_K[4:] = np.eye(4)          # a key: the word's own position, as it is
W_V = np.zeros((8, 4)); W_V[:4] = np.eye(4)          # a value: the word's own meaning, as it is

Q, K, V = X @ W_Q, X @ W_K, X @ W_V                  # 6 x 4 each
scores = Q @ K.T / np.sqrt(4)                        # 6 x 6: every query against every key
weights = softmax(scores)                            # 6 x 6: each row, one word's attention in shares
out = weights @ V                                    # 6 x 4: each word's weighted sum of the values

show("W_Q: both waves turned back one word, times 4 (rows: X's columns)", W_Q, rows=columns, cols=["q1", "q2", "q3", "q4"])
show("Q | K", np.hstack([Q, K]), cols=["q1", "q2", "q3", "q4", "k1", "k2", "k3", "k4"])
show("scores = Q @ K.T / 2 (rows: the word asking; columns: the word it looks at)", scores)
show("weights = softmax(scores)", weights)
print("each row sums to:", " ".join(f"{v:.2f}" for v in np.round(weights.sum(axis=1), 2)))
show("out = weights @ V: what head 1 hands each word", out, cols=columns[:4])
for word, row in zip(words, weights):
    print(f"{word:>10} looks at {words[row.argmax()]:<9}{np.round(row.max(), 2):.2f}")'''

HEADS_PY = PRE_X + PRE_HEADS + '''
weights1, out1 = head(X, W_Q1, W_K1, W_V1)
weights2, out2 = head(X, W_Q2, W_K2, W_V2)
show("W_Q2 | W_K2 (rows: X's columns)", np.hstack([W_Q2, W_K2]), rows=columns, cols=["q1", "q2", "q3", "q4", "k1", "k2", "k3", "k4"])
show("head 2's weights", weights2)
for word, row in zip(words, weights2):
    if np.round(row.max() - row.min(), 2) == 0:
        print(f"{word:>10} asks nothing, so its attention spreads evenly")
    else:
        print(f"{word:>10} looks at {words[row.argmax()]:<9}{np.round(row.max(), 2):.2f}")
both = np.hstack([out1, out2])                       # 6 x 8: head 1's four numbers, then head 2's
attn = both @ W_O                                    # 6 x 8: back in X's own eight columns
heads8 = ["1 thing", "1 action", "1 amount", "1 who", "2 thing", "2 action", "2 amount", "2 who"]
show("concat = [head 1 | head 2]", both, cols=heads8)
show("W_O (rows: the concat's columns)", W_O, rows=heads8, cols=columns)
show("attention output = concat @ W_O", attn, cols=columns)'''

SEE_PY = PRE_X + PRE_HEADS + '''
masked1, _ = head(X, W_Q1, W_K1, W_V1, causal=True)
masked2, _ = head(X, W_Q2, W_K2, W_V2, causal=True)
show("head 1's weights under the causal mask: each word sees itself and the words before it", masked1)
show("head 2's weights under the causal mask", masked2)
_, out1 = head(X, W_Q1, W_K1, W_V1)
_, out2 = head(X, W_Q2, W_K2, W_V2)
order = [5, 4, 3, 2, 1, 0]                                 # the same six words, back to front
Xr = np.hstack([meaning[order], X[:, 4:]])                 # the words move; the positions stay where they were
weights1r, out1r = head(Xr, W_Q1, W_K1, W_V1)
_, out2r = head(Xr, W_Q2, W_K2, W_V2)
print("reversed:", " ".join(words[i] for i in order))
print("head 2 hands every word the same numbers as before:", np.allclose(out2r, out2[order]))
print("head 1 hands every word the same numbers as before:", np.allclose(out1r, out1[order]))
print("one word back from serves is now:", words[order[weights1r[order.index(2)].argmax()]])'''

RESIDUAL_PY = PRE_X + PRE_HEADS + '''
attn = attention(X)
H = X + attn                                               # the residual path: the input, added back
show("H = X + attention output", H, cols=columns)

def cos(A, B):                                             # per word: 1 is the same direction, 0 unrelated
    return (A * B).sum(axis=1) / (np.linalg.norm(A, axis=1) * np.linalg.norm(B, axis=1))
print(f"{'':>10}{'cos(X, attention output)':>26}{'cos(X, H)':>11}")
for word, a, b in zip(words, np.round(cos(X, attn), 2) + 0.0, np.round(cos(X, H), 2)):
    print(f"{word:>10}{a:26.2f}{b:11.2f}")

def gaps(Z):                                               # the closest two words, and the farthest two
    d = np.sqrt(((Z[:, None] - Z[None, :]) ** 2).sum(axis=2))[np.triu_indices(6, 1)]
    return np.round(d.min(), 2), np.round(d.max(), 2)
plain, kept = X, X
for layer in range(1, 5):                                  # the attention sub-layer, four times over
    plain, kept = attention(plain), kept + attention(kept)
    print(f"layer {layer}: without the residual path the farthest two words are {gaps(plain)[1]:.2f} apart;"
          f" with it the closest two are {gaps(kept)[0]:.2f}")'''

NORM_PY = PRE_X + PRE_HEADS + '''
H = X + attention(X)                                       # step 6's H
mean = H.mean(axis=1, keepdims=True)                       # one mean per word, over its own 8 numbers
var = H.var(axis=1, keepdims=True)                         # one variance per word: the mean squared distance from it
eps = 1e-5                                                 # keeps a word of eight equal numbers from dividing by zero
H_hat = (H - mean) / np.sqrt(var + eps)
print("each word's mean and variance, before and after")
print(f"{'':>10}{'mean':>9}{'variance':>10}  ->{'mean':>11}{'variance':>11}")
for word, m0, v0, m1, v1 in zip(words, np.round(mean[:, 0], 4), np.round(var[:, 0], 4),
                                np.round(H_hat.mean(axis=1), 6) + 0.0, np.round(H_hat.var(axis=1), 6)):
    print(f"{word:>10}{m0:9.4f}{v0:10.4f}  ->{m1:11.6f}{v1:11.6f}")
show("H_hat = (H - mean) / sqrt(variance + eps)", H_hat, cols=columns)
print("every word's length is now the square root of 8:", " ".join(f"{v:.2f}" for v in np.round(np.linalg.norm(H_hat, axis=1), 2)))

gamma = np.array([1.5, 1.5, 1.5, 1.5, 0.5, 0.5, 0.5, 0.5])    # the learned scale, set by hand here
beta = np.array([0.2, 0.2, 0.2, 0.2, 0.0, 0.0, 0.0, 0.0])     # the learned shift, set by hand here
show("gamma * H_hat + beta: the meaning columns turned up, the position columns down", gamma * H_hat + beta, cols=columns)

def layer_norm(Z):
    return (Z - Z.mean(axis=1, keepdims=True)) / np.sqrt(Z.var(axis=1, keepdims=True) + eps)
print("a word ten times as loud comes out the same:", np.allclose(layer_norm(10 * H), H_hat, atol=1e-3))
changed = H.copy()
changed[2] = -3 * H[2]                                     # change serves, and only serves
print("changing one word moves no other word:", np.allclose(np.delete(layer_norm(changed), 2, axis=0), np.delete(H_hat, 2, axis=0)))
R = H / np.sqrt((H ** 2).mean(axis=1, keepdims=True) + eps)   # RMSNorm: no mean taken off, and no shift
print("RMSNorm per word, mean:           ", " ".join(f"{v:6.3f}" for v in np.round(R.mean(axis=1), 3)))
print("RMSNorm per word, mean of squares:", " ".join(f"{v:6.3f}" for v in np.round((R ** 2).mean(axis=1), 3)))'''

BLOCK_PY = PRE_X + PRE_HEADS + '''
def layer_norm(Z, gamma, beta, eps=1e-5):
    return gamma * (Z - Z.mean(axis=1, keepdims=True)) / np.sqrt(Z.var(axis=1, keepdims=True) + eps) + beta
gamma1, beta1, gamma2, beta2 = np.ones(8), np.zeros(8), np.ones(8), np.zeros(8)   # where training starts them
r8, r32 = np.arange(8), np.arange(32)
W_1, b_1 = np.cos(r8[:, None] + 2 * r32) / 2, np.zeros(32)    # 8 x 32: a formula standing in for trained weights
W_2, b_2 = np.sin(r32[:, None] + 3 * r8) / 4, np.zeros(8)     # 32 x 8

def feed_forward(Z):                                       # each word alone: 8 -> 32 -> 8, with ReLU between
    return np.maximum(0, Z @ W_1 + b_1) @ W_2 + b_2

def block(Z):                                              # the 2017 paper's order: add, then norm
    H1 = layer_norm(Z + attention(Z), gamma1, beta1)
    return layer_norm(H1 + feed_forward(H1), gamma2, beta2)

def block_norm_first(Z):                                   # GPT-2's order, and most models' since: norm, then add
    H1 = Z + attention(layer_norm(Z, gamma1, beta1))
    return H1 + feed_forward(layer_norm(H1, gamma2, beta2))

Y = block(X)
show("Y = block(X)", Y, cols=columns)
print("in", X.shape, "-> out", Y.shape, "-> a second block reads Y and returns", block(Y).shape)
print("per word, mean:    ", " ".join(f"{v:6.3f}" for v in np.round(Y.mean(axis=1), 3) + 0.0))
print("per word, variance:", " ".join(f"{v:6.3f}" for v in np.round(Y.var(axis=1), 3)))
Yn = block_norm_first(X)
print("norm first, mean:    ", " ".join(f"{v:6.3f}" for v in np.round(Yn.mean(axis=1), 3) + 0.0))
print("norm first, variance:", " ".join(f"{v:6.3f}" for v in np.round(Yn.var(axis=1), 3)))
learned = {"attention": [W_Q1, W_K1, W_V1, W_Q2, W_K2, W_V2, W_O], "feed-forward": [W_1, b_1, W_2, b_2],
           "layer norms": [gamma1, beta1, gamma2, beta2]}
sizes = {part: sum(w.size for w in ws) for part, ws in learned.items()}
print("numbers a trained block learns:", sum(sizes.values()), sizes)'''

KIT_PY = '''import warnings
warnings.filterwarnings("ignore", category=UserWarning)

CHUNK_CHARS = 2000                       # services/ingest/main.py: the longest chunk, in characters
CHARS_PER_TOKEN = 3                      # services/ingest/indexer.py: the worker's token estimate
EMBED_BATCH, EMBED_TOKENS = 250, 15_000  # indexer.py: the most texts, and estimated tokens, in one request
MAX_CONTEXT_TOKENS = 8000                # services/rag-api/config.py: the prompt budget for one answer

def pairs(n):                            # one head in one layer scores every token against every token
    return n * n

chunk = CHUNK_CHARS // CHARS_PER_TOKEN
print("one sequence: its tokens, and the scores one head computes in one layer of a block like this page's")
for name, n in (("the toy sentence", 6), ("one chunk of 2,000 characters", chunk), ("the API's prompt budget", MAX_CONTEXT_TOKENS)):
    print(f"  {name:31}{n:>6,} tokens{pairs(n):>13,} scores")
texts, tokens = 0, 0                     # batches() in indexer.py: stop at 250 texts or 15,000 estimated tokens
while texts < EMBED_BATCH and tokens + chunk <= EMBED_TOKENS:
    texts, tokens = texts + 1, tokens + chunk
print(f"one embedding request of full chunks: {texts} texts, {tokens:,} estimated tokens")
print(f"  each text its own sequence: {texts} x {pairs(chunk):,} = {texts * pairs(chunk):,} scores")
print(f"  the same tokens as one sequence: {pairs(tokens):,} scores, {pairs(tokens) // (texts * pairs(chunk))} times as many")'''

DATA_PY = PRE_X + PRE_HEADS + '''
import json
out = {"words": words, "weights": {}}
for name, (W_Q, W_K, W_V) in (("1", (W_Q1, W_K1, W_V1)), ("2", (W_Q2, W_K2, W_V2))):
    for mask in ("none", "causal"):
        weights, _ = head(X, W_Q, W_K, W_V, causal=(mask == "causal"))
        out["weights"][name + "-" + mask] = [[f"{v:.2f}" for v in row] for row in np.round(weights, 2) + 0.0]
print(json.dumps(out))'''

CELLS = {"vectors": VECTORS_PY, "head": HEAD_PY, "heads": HEADS_PY, "see": SEE_PY, "residual": RESIDUAL_PY,
         "norm": NORM_PY, "block": BLOCK_PY, "kit": KIT_PY}
for name, body in {**CELLS, "data": DATA_PY}.items():
    assert body.isascii() and "\nPY\n" not in body + "\n" and "'''" not in body, name
    assert 'warnings.filterwarnings("ignore", category=UserWarning)' in body, name

# a printed number within 1e-5 of a rounding edge in its last digit could print differently on another machine
GUARD = '''import numpy as _np
_round = _np.round
def _guarded_round(a, decimals=0, out=None):
    scaled = _np.asarray(a, dtype=float) * 10.0 ** decimals
    scaled = scaled[_np.isfinite(scaled)]
    edge = _np.abs(scaled - _np.floor(scaled) - 0.5)
    if edge.size and edge.min() < 1e-5:
        raise SystemExit("rounding edge: %r at %d decimals" % (float(scaled.ravel()[edge.argmin()]) / 10.0 ** decimals, decimals))
    return _round(a, decimals)
_np.round = _guarded_round
'''
TMP = Path(tempfile.mkdtemp(prefix="lessonB3-"))
ENV = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
ENV.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"})


def run_cell(body: str, guard: bool = True) -> str:
    r = subprocess.run([sys.executable, "-"], input=(GUARD if guard else "") + body, cwd=str(TMP), capture_output=True,
                       text=True, encoding="utf-8", env=ENV)
    assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stdout[-1500:], r.stderr[-3000:])
    return r.stdout


OUT = {name: run_cell(body) for name, body in CELLS.items()}
for name, body in CELLS.items():                     # the guard changes nothing a learner sees
    assert run_cell(body, guard=False) == OUT[name], name
DATA = json.loads(run_cell(DATA_PY))

TMP.rmdir()                                          # the cells write nothing: the folder is still empty

if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    print(json.dumps(DATA)[:400])
    sys.exit(0)


# ------------------------------------------------------------------ every number the prose states, read back from the outputs
def table(out: str, title: str) -> dict:
    """A table a cell printed with show(): its row names (the first 10 characters) and the numbers after them, as printed."""
    lines = out.splitlines()
    rows = {}
    for line in lines[lines.index(title) + 2:]:
        vals = line[10:].split()
        if not vals or not all(re.fullmatch(r"-?\d+\.\d+", v) for v in vals):
            break
        rows[line[:10].strip()] = vals
    return rows


def numbers(line: str) -> list:
    return re.findall(r"-?\d+\.\d+", line)


def line_of(out: str, start: str) -> str:
    return next(line for line in out.splitlines() if line.startswith(start))


WORDS = DATA["words"]
assert WORDS == ["the", "employee", "serves", "ninety", "days", "notice"]
W = DATA["weights"]
f2 = lambda v: float(v)  # noqa: E731

# step 3: the vectors
VE = OUT["vectors"]
assert VE.startswith("tokens: 6 | numbers per token: 8\n"), VE
X_TABLE = table(VE, "X = word vector + position vector")
assert X_TABLE["employee"] == ["1.00", "0.00", "0.00", "1.00", "0.71", "0.71", "1.00", "0.00"], X_TABLE
POS = table(VE, "position . position: one position's waves against another's")
assert POS["pos 0"] == ["2.00", "0.71", "-1.00", "-0.71", "0.00", "-0.71"], POS          # the step 3 note quotes these
assert "the same along every diagonal, so it measures distance only: True\n" in VE
assert "every position's signal has the same length: 1.41 1.41 1.41 1.41 1.41 1.41\n" in VE
assert "adding the two is the same as setting them side by side: True\n" in VE

# step 4: one head
HE = OUT["head"]
QK = table(HE, "Q | K")
assert QK["employee"][:4] == ["0.00", "4.00", "0.00", "4.00"] and QK["the"][4:] == ["0.00", "1.00", "0.00", "1.00"], QK
assert table(HE, "scores = Q @ K.T / 2 (rows: the word asking; columns: the word it looks at)")["employee"][0] == "4.00"
H1 = table(HE, "weights = softmax(scores)")
assert H1 == dict(zip(WORDS, W["1-none"])), (H1, W["1-none"])                          # the explorer shows the printed table
assert "each row sums to: 1.00 1.00 1.00 1.00 1.00 1.00\n" in HE
PREV = [f2(H1[w][i - 1]) for i, w in enumerate(WORDS) if i]                              # each word's share for the word before it
assert all(f2(H1[w][i - 1]) == max(map(f2, H1[w])) for i, w in enumerate(WORDS) if i)
assert H1["the"] == ["0.70", "0.02", "0.04", "0.17", "0.04", "0.02"], H1["the"]
assert table(HE, "out = weights @ V: what head 1 hands each word")["serves"] == ["0.87", "0.06", "0.00", "0.85"]
for w in WORDS:                                                                          # every argmax the cells print is clear
    top = sorted(map(f2, H1[w]), reverse=True)
    assert top[0] - top[1] > 0.05, (w, top)
assert "  employee looks at the      0.90\n" in HE and "    notice looks at days     0.85\n" in HE

# step 5: two heads, the mask, the order
HS = OUT["heads"]
H2 = table(HS, "head 2's weights")
assert H2 == dict(zip(WORDS, W["2-none"])), H2
assert all(H2[w][2] == "0.80" for w in ("employee", "days", "notice")) and H2["serves"][1] == "0.83" and H2["ninety"][4] == "0.83", H2
assert H2["the"] == ["0.17"] * 6 and "       the asks nothing, so its attention spreads evenly\n" in HS
for w in WORDS[1:]:
    top = sorted(map(f2, H2[w]), reverse=True)
    assert top[0] - top[1] > 0.05, (w, top)
ATTN = table(HS, "attention output = concat @ W_O")
assert ATTN["employee"][1] == "0.40" and all(v == "0.00" for row in ATTN.values() for v in row[4:]), ATTN
SE = OUT["see"]
M1 = table(SE, "head 1's weights under the causal mask: each word sees itself and the words before it")
M2 = table(SE, "head 2's weights under the causal mask")
assert M1 == dict(zip(WORDS, W["1-causal"])) and M2 == dict(zip(WORDS, W["2-causal"])), (M1, M2)
for i, w in enumerate(WORDS):                                                            # masked means exactly nothing
    assert all(v == "0.00" for v in M1[w][i + 1:] + M2[w][i + 1:]), w
assert M1["the"][0] == "1.00" and max(abs(f2(a) - f2(b)) for w in WORDS[1:] for a, b in zip(M1[w], H1[w])) <= 0.05
assert M2["employee"] == ["0.50", "0.50", "0.00", "0.00", "0.00", "0.00"] and M2["ninety"][:4] == ["0.33", "0.02", "0.33", "0.33"], M2
assert "head 2 hands every word the same numbers as before: True\n" in SE and "head 1 hands every word the same numbers as before: False\n" in SE
assert "reversed: notice days ninety serves employee the\n" in SE and SE.rstrip().endswith("one word back from serves is now: ninety")

# step 6: the residual path
RE_ = OUT["residual"]
COS = {line[:10].strip(): numbers(line) for line in RE_.splitlines()[RE_.splitlines().index(f"{'':>10}{'cos(X, attention output)':>26}{'cos(X, H)':>11}") + 1:][:6]}
assert list(COS) == WORDS, COS
COS_XA, COS_XH = [c[0] for c in COS.values()], [c[1] for c in COS.values()]
GAPS = [numbers(line) for line in RE_.splitlines() if line.startswith("layer ")]
assert [g[0] for g in GAPS] == ["1.36", "0.18", "0.00", "0.00"], GAPS                   # without: one vector by layer 3
KEPT = [g[1] for g in GAPS]
assert min(KEPT, key=f2) == KEPT[0] and all(f2(k) > 1 for k in KEPT), KEPT

# step 7: layer normalization
NO = OUT["norm"]
assert NO.startswith("each word's mean and variance, before and after\n"), NO[:200]
LN = {line[:10].strip(): numbers(line) for line in NO.splitlines()[2:8]}
assert list(LN) == WORDS and all(r[2] == "0.000000" for r in LN.values()), LN
MEAN0, VAR0, VAR1 = [r[0] for r in LN.values()], [r[1] for r in LN.values()], [r[3] for r in LN.values()]
assert all(v.startswith("0.9999") for v in VAR1), VAR1
assert [VAR1[i] for i in sorted(range(6), key=lambda i: f2(VAR0[i]))] == sorted(VAR1, key=f2)   # less of 1 where the variance was small
assert "every word's length is now the square root of 8: 2.83 2.83 2.83 2.83 2.83 2.83\n" in NO
assert "a word ten times as loud comes out the same: True\n" in NO and "changing one word moves no other word: True\n" in NO
RMS_MEAN = numbers(line_of(NO, "RMSNorm per word, mean:"))
assert numbers(line_of(NO, "RMSNorm per word, mean of squares:")) == ["1.000"] * 6 and all(f2(v) > 0.05 for v in RMS_MEAN), RMS_MEAN

# step 8: the block
BL = OUT["block"]
assert "in (6, 8) -> out (6, 8) -> a second block reads Y and returns (6, 8)\n" in BL
assert numbers(line_of(BL, "per word, mean:")) == ["0.000"] * 6 and numbers(line_of(BL, "per word, variance:")) == ["1.000"] * 6
PRE_MEAN, PRE_VAR = numbers(line_of(BL, "norm first, mean:")), numbers(line_of(BL, "norm first, variance:"))
assert all(f2(v) > 0.01 for v in PRE_MEAN) and all(f2(v) < 0.9 for v in PRE_VAR), (PRE_MEAN, PRE_VAR)
SIZES = re.search(r"numbers a trained block learns: (\d+) \{'attention': (\d+), 'feed-forward': (\d+), 'layer norms': (\d+)\}", BL).groups()
assert SIZES == ("840", "256", "552", "32") and 0.6 < int(SIZES[2]) / int(SIZES[0]) < 0.7, SIZES

# step 9: the kit's numbers, squared
KO = OUT["kit"]
assert "  one chunk of 2,000 characters     666 tokens      443,556 scores\n" in KO
assert "  the API's prompt budget         8,000 tokens   64,000,000 scores\n" in KO
assert f"one embedding request of full chunks: {KIT_TEXTS_PER_REQUEST} texts, 14,652 estimated tokens\n" in KO   # the kit's own batches()
assert KO.rstrip().endswith("the same tokens as one sequence: 214,681,104 scores, 22 times as many")
for literal in ("CHUNK_CHARS = 2000", "CHARS_PER_TOKEN = 3", "EMBED_BATCH, EMBED_TOKENS = 250, 15_000", "MAX_CONTEXT_TOKENS = 8000"):
    assert literal in KIT_PY, literal                                                    # the cell's copies of the kit's constants
assert "max_context_tokens: int = 8000" in src[CONFIG] and "CHUNK_CHARS, CHUNK_OVERLAP = 2000, 200" in src[WORKER]

STATS = {
    "N_TOKENS": "6", "D_MODEL": "8", "N_LEARNED": SIZES[0], "N_ATTN": SIZES[1], "N_FFN": SIZES[2], "N_NORMS": SIZES[3],
    "H1_EMPLOYEE_THE": H1["employee"][0], "H1_PREV_MIN": f"{min(PREV):.2f}", "H1_PREV_MAX": f"{max(PREV):.2f}",
    "H1_THE_THE": H1["the"][0], "H1_THE_NINETY": H1["the"][3],
    "H2_NOUN_SERVES": H2["employee"][2], "H2_SERVES_EMPLOYEE": H2["serves"][1], "H2_NINETY_DAYS": H2["ninety"][4], "H2_THE_EVEN": H2["the"][0],
    "ATTN_EMPLOYEE_ACTION": ATTN["employee"][1], "M2_EMPLOYEE": M2["employee"][0], "M2_NINETY_EMPLOYEE": M2["ninety"][1],
    "COS_XH_MIN": min(COS_XH, key=f2), "COS_XH_MAX": max(COS_XH, key=f2), "COS_XA_MIN": min(COS_XA, key=f2), "COS_XA_MAX": max(COS_XA, key=f2),
    "GAP_KEPT_MIN": min(KEPT, key=f2),
    "LN_MEAN0_MIN": min(MEAN0, key=f2), "LN_MEAN0_MAX": max(MEAN0, key=f2), "LN_VAR0_MIN": min(VAR0, key=f2), "LN_VAR0_MAX": max(VAR0, key=f2),
    "LN_VAR_MIN": min(VAR1, key=f2), "LN_VAR_MAX": max(VAR1, key=f2),
    "PRE_MEAN_MIN": min(PRE_MEAN, key=f2), "PRE_MEAN_MAX": max(PRE_MEAN, key=f2), "PRE_VAR_MIN": min(PRE_VAR, key=f2), "PRE_VAR_MAX": max(PRE_VAR, key=f2),
    "KIT_CHUNK_TOKENS": "666", "KIT_CHUNK_SCORES": "443,556", "KIT_PROMPT_SCORES": "64 million", "KIT_TEXTS": str(KIT_TEXTS_PER_REQUEST),
    "KIT_TOKENS": "14,652", "KIT_RATIO": "22",
}
assert 2000 // 3 == 666 and 666 * 666 == 443_556 and 8000 * 8000 == 64_000_000 and 22 * 666 == 14_652 and (14_652 ** 2) // (22 * 443_556) == 22


# ------------------------------------------------------------------ the windows
def heredoc(body: str) -> str:
    return f"python - <<'PY'\n{body}\nPY"


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + html.escape(label, quote=False) + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + html.escape(label, quote=False) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABEL = "run in the same shell, in the basics venv (numpy only, no network)"
CELL_LABELS = {name: CELL_LABEL for name in CELLS}
CELL_LABELS["kit"] = "run in the same shell (plain Python, no network)"
OUT_LABEL = "(printed by this cell when the page was built; your laptop prints the same)"
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], heredoc(v)) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABEL, v) for k, v in OUT.items()})


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


# ------------------------------------------------------------------ the explorer: the weights the cells print, as JSON
JS = """<script>
(function(){
  'use strict';
  var D = __DATA__;
  var grid = document.getElementById('ax-grid'), sum = document.getElementById('ax-sum'),
      selH = document.getElementById('ax-head'), selM = document.getElementById('ax-mask');
  if (!grid || !sum || !selH || !selM) return;
  var row = 2, rows = [], cells = [];
  function el(tag, cls, text){ var e = document.createElement(tag); e.className = cls; if (text !== undefined) { e.textContent = text; } return e; }
  function now(){ return D.weights[selH.value + '-' + selM.value]; }
  function mark(){
    var W = now(), causal = selM.value === 'causal';
    rows.forEach(function(b, i){ b.classList.toggle('on', i === row); b.setAttribute('aria-pressed', i === row ? 'true' : 'false'); });
    cells.forEach(function(r, i){ r.forEach(function(c){ c.classList.toggle('sel', i === row && !c.classList.contains('ax-m')); }); });
    var seen = W[row].map(function(v, j){ return {w: D.words[j], v: v, j: j}; }).filter(function(p){ return !(causal && p.j > row); });
    seen.sort(function(a, b){ return parseFloat(b.v) - parseFloat(a.v); });
    sum.textContent = D.words[row] + ' (head ' + selH.value + ', ' + (causal ? 'causal mask' : 'no mask') + ') gives: ' +
      seen.map(function(p){ return p.w + ' ' + p.v; }).join(', ') + (causal && row < W.length - 1 ? '; every later word is masked' : '');
  }
  function build(){
    var W = now(), causal = selM.value === 'causal';
    grid.textContent = ''; rows = []; cells = [];
    var corner = el('div', 'ax-col', ''); corner.setAttribute('aria-hidden', 'true'); grid.appendChild(corner);
    D.words.forEach(function(w){ grid.appendChild(el('div', 'ax-col', w)); });
    W.forEach(function(r, i){
      var b = el('button', 'ax-r', D.words[i]); b.type = 'button';
      b.addEventListener('click', function(){ row = i; mark(); });
      grid.appendChild(b); rows.push(b); cells.push([]);
      r.forEach(function(v, j){
        var c, x = parseFloat(v);
        if (causal && j > i) { c = el('div', 'ax-c ax-m', '-'); c.title = 'masked'; }
        else { c = el('div', 'ax-c' + (x >= 0.5 ? ' dark' : ''), v); c.style.background = 'rgba(13,148,136,' + Math.max(0.05, x).toFixed(2) + ')'; }
        grid.appendChild(c); cells[i].push(c);
      });
    });
    mark();
  }
  selH.addEventListener('change', build);
  selM.addEventListener('change', build);
  build();
})();
</script>
""".replace("__DATA__", json.dumps(DATA, separators=(",", ":")))
assert "</" not in JS.split("<script>", 1)[1].rsplit("</script>", 1)[0]

body = "".join([fill(subst(pb.part(LESSON, "a"))), setup, fill(subst(pb.part(LESSON, "b"))), fill(subst(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"cells: {len(CELLS)} run and pinned (rounding guard on, identical without it) | explorer: {len(W)} tables of 6 x 6 from the same code"
      f" | kit: {len(EXCERPTS)} excerpts, batches() run on 2,000-character chunks ({KIT_TEXTS_PER_REQUEST} per request)")
