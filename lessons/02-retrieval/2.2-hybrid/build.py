"""Build lesson 2.2 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

The fusion bench is computed here, from the kit, at build time: acme's corpus cut by the kit's chunker, the index's
sparse leg (shared/sparse_encoder.py, scored by dot product as Vector Search scores a sparse vector) and the
ablation's leg (BM25Okapi with rank_bm25 0.2.2's constants, ported below so the build needs no extra package).
"""
import hashlib
import html
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "2.2"
title = "<title>Lesson 2.2 Compare dense and hybrid retrieval - two legs through one index, one fusion rule, and an ablation that measures instead of arguing | Netsetos</title>\n"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.fb-controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px 16px;margin-bottom:10px;}
.fb-l{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.fb-wide{grid-column:1/-1;}
.fb-l select,.fb-l textarea{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.fb-l textarea{font-family:var(--mono);font-size:16px;line-height:1.35;min-height:96px;resize:vertical;}
.fb-l input[type=range]{width:100%;min-height:44px;margin:0;}
.fb-legs{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;margin:8px 0;}
.fb-leg{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 10px;min-width:0;}
.fb-leg h5{margin:0 0 6px;font-size:var(--small-size);color:var(--navy);}
.fb-leg ol{margin:0;padding-left:22px;font-size:12.5px;line-height:1.5;color:var(--slate);}
.fb-leg li span,.fb-fused td span{color:var(--slate);font-family:var(--mono);font-size:var(--kicker-size);overflow-wrap:anywhere;}
.fb-leg li.hit{color:var(--navy);font-weight:600;background:var(--teal-light);border-radius:4px;padding:1px 4px;margin-left:-4px;}
.fb-rank{font-family:var(--mono);font-size:var(--kicker-size);color:var(--teal);margin:6px 0 0;}
.fb-fused{margin-top:8px;overflow-x:auto;overscroll-behavior-x:contain;-webkit-overflow-scrolling:touch;}
.fb-fused table{width:100%;border-collapse:collapse;font-size:12.5px;}
.fb-fused th,.fb-fused td{text-align:left;padding:4px 6px;border-bottom:1px solid var(--border);vertical-align:top;}
.fb-fused td.num{font-family:var(--mono);white-space:nowrap;}
.fb-fused tr.hit td{background:var(--teal-light);color:var(--navy);font-weight:600;}
.dv-controls{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px;}
.dv-btn{font:inherit;font-size:var(--small-size);min-height:44px;padding:8px 14px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--navy);cursor:pointer;}
.dv-btn[aria-pressed="true"]{background:var(--teal-light);border-color:var(--teal);color:var(--teal-dark);font-weight:600;}
@media (hover:hover) and (pointer:fine){.dv-btn:hover{border-color:var(--teal);}}
.dv-q{font-weight:600;color:var(--navy);margin:4px 0 6px;}
.dv-toks{min-height:30px;margin-bottom:8px;}
.dv-tok{display:inline-block;font-family:var(--mono);font-size:var(--kicker-size);padding:2px 7px;margin:2px 4px 2px 0;border:1px solid var(--border);border-radius:6px;background:var(--card);opacity:0;transition:opacity .35s ease,background .35s ease,border-color .35s ease;}
.dv-tok.on{opacity:1;}
.dv-tok.hit{background:var(--teal-light);border-color:var(--teal);}
.dv-panels{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;}
.dv-panel{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 10px;min-width:0;}
.dv-panel h5{margin:0 0 6px;font-size:var(--small-size);color:var(--navy);}
.dv-panel svg{display:block;width:100%;height:auto;}
.dv-key{font-size:var(--kicker-size);color:var(--slate);margin:4px 0 0;}
.dv-sw{display:inline-block;width:12px;height:4px;border-radius:2px;margin:0 4px 2px 8px;vertical-align:middle;}
.dv-sw:first-child{margin-left:0;}
.dv-sw-doc{background:#94a3b8;}
.dv-sw-q{background:#d97706;}
.dv-sw-hit{background:#0d9488;}
.dv-math{font-family:var(--mono);font-size:var(--kicker-size);color:var(--navy);min-height:1.4em;margin:6px 0 0;overflow-wrap:anywhere;}
.dv-rank{display:inline-block;font-size:var(--kicker-size);padding:3px 8px;margin:6px 6px 0 0;border:1px solid var(--border);border-radius:6px;background:var(--bg);opacity:0;transition:opacity .4s ease;}
.dv-rank.on{opacity:1;}
.dv-rank.win{background:var(--teal-light);border-color:var(--teal);color:var(--teal-dark);font-weight:600;}
.dv-cmd{font-family:var(--mono);font-size:var(--kicker-size);color:var(--slate);margin:6px 0 0;overflow-wrap:anywhere;}
.dv-verdict{min-height:1.5em;color:var(--navy);font-weight:600;margin:10px 0 0;}
@media (prefers-reduced-motion:reduce){.dv-tok,.dv-rank,#dv-sp line,#dv-dn circle,#dv-dn line,#dv-pin{transition-duration:.01ms!important;}}
.hd-controls{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px;}
.hd-btn{font:inherit;font-size:var(--small-size);min-height:44px;padding:8px 14px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--navy);cursor:pointer;}
.hd-btn[aria-pressed="true"]{background:var(--teal-light);border-color:var(--teal);color:var(--teal-dark);font-weight:600;}
@media (hover:hover) and (pointer:fine){.hd-btn:hover{border-color:var(--teal);}}
.hd-q{font-weight:600;color:var(--navy);margin:4px 0 6px;}
.hd-toks{min-height:30px;margin-bottom:8px;}
.hd-tok{display:inline-block;font-size:var(--kicker-size);padding:2px 8px;margin:2px 4px 2px 0;border:1px solid var(--border);border-radius:6px;background:var(--card);opacity:0;transition:opacity .35s ease,background .35s ease,border-color .35s ease;}
.hd-tok.on{opacity:1;}
.hd-tok.hit{background:var(--teal-light);border-color:var(--teal);}
.hd-panels{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;}
.hd-panel{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 10px;min-width:0;}
.hd-wide{grid-column:1/-1;}
.hd-panel h5{margin:0 0 6px;font-size:var(--small-size);color:var(--navy);}
.hd-panel svg{display:block;width:100%;height:auto;}
.hd-doc{display:flex;gap:8px;align-items:flex-start;padding:6px 8px;margin-bottom:4px;border:1px solid transparent;border-radius:8px;transition:background .35s ease,border-color .35s ease;}
.hd-doc.win{background:var(--teal-light);border-color:var(--teal);}
.hd-doc b{color:var(--navy);min-width:14px;}
.hd-doc p{margin:0;flex:1;min-width:0;font-size:var(--small-size);line-height:1.45;color:var(--slate);}
.hd-w{border-radius:4px;padding:0 2px;transition:background .3s ease,color .3s ease;}
.hd-w.hit{background:#99f6e4;color:var(--teal-dark);}
.hd-n{font-family:var(--mono);font-size:var(--kicker-size);color:var(--slate);white-space:nowrap;min-width:56px;text-align:right;}
.hd-list{font-size:var(--kicker-size);color:var(--navy);margin:8px 0 0;min-height:1.4em;}
.hd-rule{font-size:var(--kicker-size);color:var(--slate);margin:0 0 6px;}
.hd-alpha{display:flex;flex-wrap:wrap;align-items:center;gap:4px 10px;font-size:var(--small-size);color:var(--navy);margin-bottom:6px;}
.hd-alpha input[type=range]{flex:1;min-width:180px;min-height:44px;margin:0;}
.hd-rrf td span{display:block;font-family:var(--mono);font-size:var(--kicker-size);color:var(--slate);}
.hd-rrf tbody tr{opacity:0;transition:opacity .4s ease;}
.hd-rrf tbody tr.on{opacity:1;}
.hd-rrf tbody tr.win{background:#ccfbf1;}
.hd-rrf td.tot{font-family:var(--mono);font-weight:600;white-space:nowrap;}
.hd-verdict{min-height:3em;color:var(--navy);font-weight:600;margin:10px 0 0;}
@media (prefers-reduced-motion:reduce){.hd-tok,.hd-doc,.hd-w,.hd-rrf tbody tr,#hd-map circle,#hd-map line,#hd-pin{transition-duration:.01ms!important;}}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
RET = "services/rag-api/retriever.py"
CFG = "services/rag-api/config.py"
API = "services/rag-api/main.py"
ABL = "evals/ablate.py"
HYB = "services/rag-api/hybrid.py"


def nth_after(rel: str, start: str, after: str) -> int:
    """Which occurrence of `start` is the first one after the line containing `after`."""
    lines = (KIT / rel).read_text(encoding="utf-8").splitlines()
    h = next(i for i, line in enumerate(lines) if after in line)
    return sum(1 for line in lines[:h] if start in line) + 1


EXCERPTS = {
    "mode_setting": ("services/rag-api/config.py - retrieval_mode, and the validator that refuses an impossible pair at import",
                     block(CFG, '    retrieval_mode: str = "dense"', n=1) + "\n...\n" + block(CFG, "    @model_validator", end="settings = Settings()")),
    "version": ("services/rag-api/main.py - /version: the mode that passed the check", block(API, '@app.get("/version")', n=10)),
    "datapoint_sparse": ("services/ingest/indexer.py - _sparse(): the vector on every datapoint (lesson 1.3)",
                         block("services/ingest/indexer.py", "def _sparse(", end="def _datapoint(")),
    "ablate_corpus": ("evals/ablate.py - Lane.tenant_corpus(): the rows' text and a BM25 index, the harness's sparse leg",
                      block(ABL, "    def tenant_corpus(", end="    def _current(")),
    "hybrid_query": ("services/rag-api/hybrid.py - hybrid_find_neighbors(): the question encoded, one HybridQuery, the tenant once",
                     block(HYB, "def hybrid_find_neighbors(")),
    "retriever_hybrid": ("services/rag-api/retriever.py - _dense_retrieve(): the two branches, alpha 0.7 under hybrid mode",
                         block(RET, '        if settings.retrieval_mode == "hybrid":', end="    except Exception as e:")),
    "rrf": ("services/rag-api/hybrid.py - rrf_fuse(): the rule", block(HYB, "def rrf_fuse(", end="def hybrid_find_neighbors(")),
    "ablate_rrf": ("evals/ablate.py - rrf(): the same rule, in the harness", block(ABL, "def rrf(", end="def hay(")),
    "make_ablate": ("Makefile - the ablate target", block("Makefile", "# The ablation harness (4.8, Part 5)", n=7)),
    "ablate_arms": ("evals/ablate.py - arms(): one knob each", block(ABL, "def arms(", end="def parse_arms(")),
    "ablate_hybrid": ("evals/ablate.py - Lane.hybrid(): BM25 ids fused with the Firestore rung's dense ids",
                      block(ABL, "    def hybrid(self, question", end="    def rag(self")),
    "ablate_metrics": ("evals/ablate.py - hay(), recall_at(), mrr(), p95(): how an arm is scored",
                       block(ABL, "def hay(", end="# ------------------------------------------------------------------ the lane, from outside it")),
    "ablate_read": ("evals/ablate.py - the reading order the harness prints", block(ABL, '    print("\\nRead it in this order', n=4)),
    "modes": ("services/rag-api/config.py - check_retrieval_modes(): the two refusals",
              block(CFG, "def check_retrieval_modes(", n=1) + "\n...\n" + block(CFG, '    if backend in MANAGED_BACKENDS and mode == "hybrid":', n=7)),
    "pin_rule": ("services/rag-api/main.py - choose_for(): a managed pin is ignored under hybrid, with a line",
                 block(API, '    pin = ts.get("retrieval_backend")', n=8)),
    "chaos": ("services/rag-api/retriever.py - the chaos rung: hybrid degrades to the dense Firestore rung, logged",
              block(RET, "    except Exception as e:", n=8, nth=nth_after(RET, "    except Exception as e:", 'if settings.retrieval_mode == "hybrid":'))),
    "usage_mode": ("services/rag-api/main.py and terraform/sql/tenant_daily.sql - the mode on every usage row, and the view that groups by it",
                   block(API, '            "retrieval_mode": settings.retrieval_mode,', n=1) + "\n...\n"
                   + block("terraform/sql/tenant_daily.sql", "  jsonPayload.retrieval_mode AS retrieval_mode,", n=1)),
}
assert EXCERPTS["chaos"][1].startswith("    except Exception as e:") and "vector_search_fallback" in EXCERPTS["chaos"][1]
assert EXCERPTS["ablate_read"][1].rstrip().endswith('shows up as a miss.")'), EXCERPTS["ablate_read"][1][-80:]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the bench: two sparse rulers over acme's corpus
sys.path.insert(0, str(KIT))
from shared import documind_corpus as dc  # noqa: E402
from shared.sparse_encoder import sparse_encode  # noqa: E402

CORPUS = KIT / "evals" / "corpus" / "acme"
docs = []
for p in sorted(CORPUS.glob("*.md")):
    for i, c in enumerate(dc.chunk_document({"slug": p.stem, "doc_type": "policy", "source_uri": f"gs://x/acme/{p.name}",
                                             "text": p.read_text(encoding="utf-8")}, "acme")):
        docs.append({"source": p.name, "locator": c.get("locator") or f"#{i}", "pos": i, "text": c["text"]})
N = len(docs)
DOCS = len(list(CORPUS.glob("*.md")))
NP03_POS = next(d["pos"] for d in docs if d["source"] == "hr_policy_2026.md" and d["locator"] == "NP-03")

sparse_vecs = [dict(zip(*reversed(sparse_encode(d["text"])))) for d in docs]      # {dimension: weight}


def index_leg(q: str) -> list:
    """What Vector Search computes for a sparse query: the dot product with every datapoint's sparse vector."""
    vals, dims = sparse_encode(q)
    qv = dict(zip(dims, vals))
    return [sum(w * v.get(dim, 0.0) for dim, w in qv.items()) for v in sparse_vecs]


def tokens(text: str) -> list:
    return re.findall(r"[a-z0-9\-]+", text.lower())            # ablate.tokens() and the encoder's _tokens(): the same rule


# BM25Okapi as rank_bm25 0.2.2 computes it: k1 1.5, b 0.75, epsilon 0.25 (negative idf floored at epsilon * mean idf)
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


def bm25_leg(q: str) -> list:
    out = [0.0] * N
    for w in tokens(q):
        if w not in idf:
            continue
        for i, f in enumerate(doc_freqs):
            qf = f.get(w, 0)
            if qf:
                out[i] += idf[w] * qf * (K1 + 1) / (qf + K1 * (1 - B + B * doc_len[i] / avgdl))
    return out


CLAUSE = re.compile(r"[A-Z]{2,}(?:-[A-Z]+)?-\d+")


def is_hit(d: dict, anchors: list) -> bool:
    """A clause anchor (NP-03) must be the row's locator; a document anchor (inv_2026_0412) its source."""
    return any((d["locator"] == a) if CLAUSE.fullmatch(a) else d["source"].startswith(a) for a in anchors)


golden = [json.loads(line) for line in (KIT / "evals" / "golden.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
by_id = {r["id"]: r for r in golden}
anchored = [r for r in golden if r.get("must_retrieve")]
STATS = {
    "ROWS": len(golden), "ANCH": len(anchored), "ACME_ROWS": sum(1 for r in anchored if r["tenant"] == "acme"),
    "ANCHORS": sum(len(r["must_retrieve"]) for r in anchored),
    "CODES": sum(1 for r in anchored for a in r["must_retrieve"] if CLAUSE.fullmatch(a)),
}

BENCH_IDS = ["lk-10", "lk-06", "jn-02", "lk-05", "lk-12", "mm-03", "lk-27"]
bench, bench_rows, bench_options = {}, [], []
for rid in BENCH_IDS:
    row = by_id[rid]
    q, anchors = row["question"], row["must_retrieve"]
    entry = {"id": rid, "q": q, "anchors": anchors, "tokens": tokens(q), "dims": len(sparse_encode(q)[1]), "n": N, "ranks": {}, "legs": {}}
    for name, scores in (("hashed", index_leg(q)), ("bm25", bm25_leg(q))):
        order = [i for i in sorted(range(N), key=lambda i: -scores[i]) if scores[i] > 0]
        entry["ranks"][name] = next((r for r, i in enumerate(order, 1) if is_hit(docs[i], anchors)), None)
        entry["legs"][name] = [{"loc": docs[i]["locator"], "src": docs[i]["source"], "score": round(scores[i], 3), "hit": is_hit(docs[i], anchors)}
                               for i in order[:5]]
    bench[rid] = entry
    show = lambda r: "none" if r is None else str(r)
    bench_rows.append(f'<tr><td>{rid} &middot; {html.escape(q)}</td><td data-label="Anchor">{html.escape(", ".join(anchors))}</td>'
                      f'<td data-label="Index leg: rank">{show(entry["ranks"]["hashed"])}</td><td data-label="BM25: rank">{show(entry["ranks"]["bm25"])}</td></tr>')
    bench_options.append(f'<option value="{rid}">{rid} &middot; {html.escape(q)}</option>')
assert bench["lk-10"]["ranks"]["bm25"] == 1 and (bench["lk-10"]["ranks"]["hashed"] or 0) > 100, bench["lk-10"]["ranks"]

# ------------------------------------------------------------------ step 1's explainer: one sentence, two vectors
# Three questions, each against the one chunk that answers it: every slot, weight, shared word, score and sparse rank
# below is the kit's own arithmetic on acme's corpus. The dense side is a sketch in the page, except the invoice's rank,
# which is step 4's run on the lane; step 4 measures the other two with Q and ANCHOR exported.
from shared.sparse_encoder import SPARSE_DIMS  # noqa: E402


def slot(token: str) -> int:
    """The dimension sparse_encode() gives one token: blake2b over it, folded into SPARSE_DIMS."""
    return int(hashlib.blake2b(token.encode(), digest_size=4).hexdigest(), 16) % SPARSE_DIMS


def tf_weight(n: int) -> float:
    return 1.0 + (n - 1) * 0.5                                  # sparse_encode()'s curve: 1, then 0.5 per repeat


def ordinal(n: int) -> str:
    return f"{n:,}" + ("th" if 10 < n % 100 < 14 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))


assert "dense  first five (anchor at rank 1 of 20)" in pb.part(LESSON, "b"), "step 4's lane output moved: update DENSE_ON_LANE"
DENSE_ON_LANE = {"inv": 1}
DV_SPEC = [
    ("code", "Clause code", "What does clause NP-03 say?", "hr_policy_2026.md", "NP-03", "NP-03",
     "An exact code: the sparse leg finds it, but only when rare words weigh more, as they do in BM25."),
    ("para", "Paraphrase", "If I quit my job, how long must I keep working?", "hr_policy_2026.md", "NP-03", "NP-03",
     "Same meaning, no shared word: to a word counter, quit is not resignation. Only the dense leg can bridge that."),
    ("inv", "Invoice number", by_id["lk-10"]["question"], "inv_2026_0412.md", None, "inv_2026_0412",
     "Both legs can find it: BM25 by the exact number, the dense leg by the meaning. Fusing keeps it at the top."),
]
dv = {}
for key, label, q, src, loc, anchor, verdict in DV_SPEC:
    i = next(j for j, d in enumerate(docs) if d["source"] == src and (loc is None or d["locator"] == loc))
    dcount, qcount = Counter(tokens(docs[i]["text"])), Counter(tokens(q))
    doc_toks = [[w, slot(w), tf_weight(n)] for w, n in dcount.items()]
    assert sorted({s for _, s, _ in doc_toks}) == sparse_encode(docs[i]["text"])[1], (key, "slot() must reproduce sparse_encode()")
    shared = [[w, tf_weight(qcount[w]), tf_weight(dcount[w])] for w in qcount if w in dcount]
    score = index_leg(q)[i]
    assert abs(score - sum(a * b for _, a, b in shared)) < 1e-9, (key, score, shared)
    ranks = {}
    for name, scores in (("hashed", index_leg(q)), ("bm25", bm25_leg(q))):
        order = [j for j in sorted(range(N), key=lambda j: -scores[j]) if scores[j] > 0]
        ranks[name] = order.index(i) + 1 if i in order else None
    dv[key] = {"label": label, "q": q, "anchor": anchor, "doc": src + (f", {loc}" if loc else ""), "docToks": doc_toks,
               "qToks": [[w, slot(w)] for w in qcount], "shared": shared, "score": round(score, 2), "ranks": ranks,
               "dense": DENSE_ON_LANE.get(key), "n": N, "verdict": verdict}
assert [s[0] for s in dv["code"]["shared"]] == ["np-03"] and dv["code"]["ranks"]["bm25"] == 1 and dv["code"]["ranks"]["hashed"] > 100, dv["code"]
assert dv["para"]["shared"] == [] and dv["para"]["ranks"] == {"hashed": None, "bm25": None}, dv["para"]
assert dv["inv"]["ranks"]["bm25"] == 1 and dv["inv"]["ranks"]["hashed"] > 100, dv["inv"]["ranks"]
DV_BUTTONS = "".join(f'<button type="button" class="dv-btn" data-key="{k}" aria-pressed="{"true" if k == "code" else "false"}">{html.escape(v["label"])}</button>'
                     for k, v in dv.items())

# ------------------------------------------------------------------ step 1's intuition: a help desk with four answers
# A toy before the corpus: four answers, word matching that counts each shared word once (tokens(), the kit's rule),
# a two-number map whose positions are made up, and the kit's merge rule. Every number the three panels show, and
# every claim the page makes about them, is computed and checked here.
HD_DOCS = [("A", "Refund policy", "Refund policy: cancelled tickets are refunded within 7 days.", (0.85, 0.35)),
           ("B", "Order ORD-7781", "Order ORD-7781 was delivered on 12 April.", (0.10, 0.90)),
           ("C", "Order ORD-7782", "Order ORD-7782 is out for delivery.", (0.14, 0.85)),
           ("D", "Password help", "Change your password from the profile page.", (0.08, 0.10))]
HD_QS = [("money", "Money back", "How do I get my money back?", (0.90, 0.22)),
         ("order", "Order number", "Where is order ORD-7782?", (0.07, 0.835)),       # on the line equidistant from B and C
         ("ticket", "Refund, cancelled ticket", "Refund for a cancelled ticket", (0.78, 0.30))]
HD_K, HD_ALPHA = 60, 0.7


def hd_fuse(dense: list, sparse: list, alpha: float) -> dict:
    """rrf_fuse() with ranks from 1: alpha / (k + rank) from the dense list plus (1 - alpha) / (k + rank) from the sparse one."""
    score = {}
    for rank, d in enumerate(dense, 1):
        score[d] = score.get(d, 0.0) + alpha / (HD_K + rank)
    for rank, d in enumerate(sparse, 1):
        score[d] = score.get(d, 0.0) + (1 - alpha) / (HD_K + rank)
    return score


def hd_order(score: dict) -> list:
    return sorted(score, key=lambda d: -score[d])                # stable: an exact tie keeps the dense list's order


hd_letters = [d[0] for d in HD_DOCS]
hd = {}
for key, label, q, pin in HD_QS:
    qw = list(dict.fromkeys(tokens(q)))
    shared = {d[0]: [w for w in qw if w in set(tokens(d[2]))] for d in HD_DOCS}
    dist = {d[0]: round(math.hypot(d[3][0] - pin[0], d[3][1] - pin[1]), 2) for d in HD_DOCS}
    hd[key] = {"label": label, "q": q, "pin": pin, "words": qw, "shared": shared,
               "sparse": [x for x in sorted(hd_letters, key=lambda x: -len(shared[x])) if shared[x]],
               "dist": dist, "dense": sorted(hd_letters, key=lambda x: dist[x])}
hd_s = {k: hd_fuse(v["dense"], v["sparse"], HD_ALPHA) for k, v in hd.items()}
assert hd["money"]["sparse"] == [] and hd["money"]["dense"] == ["A", "D", "C", "B"] and hd_order(hd_s["money"])[0] == "A", hd["money"]
assert hd["order"]["sparse"] == ["C", "B"] and hd["order"]["dist"]["B"] == hd["order"]["dist"]["C"] and hd["order"]["dense"][:2] == ["B", "C"], hd["order"]
assert hd_order(hd_s["order"])[0] == "B" and hd_order(hd_fuse(hd["order"]["dense"], hd["order"]["sparse"], 0.3))[0] == "C", hd_s["order"]
assert hd["ticket"]["sparse"] == ["A", "C"] and hd["ticket"]["dense"] == ["A", "D", "C", "B"] and hd_order(hd_s["ticket"]) == ["A", "C", "D", "B"], hd_s["ticket"]
assert hd["ticket"]["shared"]["A"] == ["refund", "cancelled"], hd["ticket"]["shared"]    # ticket is not tickets
hd["money"]["verdict"] = ("Sparse finds nothing: no answer contains how, get, money or back, so its list is empty. Dense lands next to A, "
                          "because money back means refund. With one list empty, the merge follows the other, and A comes first.")
hd["order"]["verdict"] = (f"Sparse picks C: only C contains ORD-7782. Dense cannot choose: B and C are equally near, because a number carries no "
                          f"meaning, and B came first by chance. At alpha 0.7 the merge follows the dense guess, B {1000 * hd_s['order']['B']:.2f} "
                          f"against C {1000 * hd_s['order']['C']:.2f}; slide alpha below 0.5 and C wins. The merge cannot read the text; "
                          f"lesson 2.3's reranker can.")
hd["ticket"]["verdict"] = ("Both legs put A first. C was third for dense but second for sparse, so the merge lifts it above D, which only dense "
                           "had: being on both lists counts most. And sparse matched refund and cancelled but not ticket, because the answer says tickets.")
HD_BUTTONS = "".join(f'<button type="button" class="hd-btn" data-key="{k}" aria-pressed="{"true" if k == "money" else "false"}">{html.escape(v["label"])}</button>'
                     for k, v in hd.items())


def subst(text: str) -> str:
    reps = {**{k: str(v) for k, v in STATS.items()}, "CHUNKS": f"{N:,}", "DOCS": str(DOCS), "NP03_POS": str(NP03_POS),
            "BENCH_ROWS": "\n".join(bench_rows), "BENCH_OPTIONS": "".join(bench_options),
            "SPARSE_DIMS": f"{SPARSE_DIMS:,}", "DV_NP03_SLOTS": str(len(dv["code"]["docToks"])), "DV_BUTTONS": DV_BUTTONS, "HD_BUTTONS": HD_BUTTONS,
            "DV_CODE_TF": ordinal(dv["code"]["ranks"]["hashed"]), "DV_INV_TF": ordinal(dv["inv"]["ranks"]["hashed"]),
            "B1": f"{0.7 / 61:.5f}", "B2": f"{0.3 / 61:.5f}", "B3": f"{0.7 / 80:.5f}"}
    for k, v in reps.items():
        text = text.replace(f"%%{k}%%", v)
    return text


# ------------------------------------------------------------------ the bench's script: rrf_fuse() in JavaScript
JS = """<script>
(function(){
  'use strict';
  var BENCH = __BENCH__;
  var root = document.getElementById('bench'); if (!root) return;
  var qSel = document.getElementById('fb-q'), alpha = document.getElementById('fb-alpha'), kIn = document.getElementById('fb-k'),
      dense = document.getElementById('fb-dense'), legs = document.getElementById('fb-legs'), fusedEl = document.getElementById('fb-fused'),
      alphaV = document.getElementById('fb-alpha-v'), kV = document.getElementById('fb-k-v'), meta = document.getElementById('fb-meta');
  var CLAUSE = /^[A-Z]{2,}(?:-[A-Z]+)?-\\d+$/;
  function esc(t){ return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  function key(loc, src){ return (loc + ' ' + src.slice(0, 12)).toLowerCase(); }
  function isHit(loc, src, anchors){ return anchors.some(function(a){ return CLAUSE.test(a) ? loc === a : src.indexOf(a) === 0; }); }
  function legList(rows){ return rows.map(function(r){ return {k: key(r.loc, r.src), loc: r.loc, src: r.src, score: r.score, hit: r.hit}; }); }
  function pasted(anchors){
    return dense.value.split('\\n').map(function(l){ return l.trim(); }).filter(Boolean).map(function(l){
      var p = l.split(/\\s+/); return {k: key(p[0], p[1] || ''), loc: p[0], src: p[1] || '', hit: isHit(p[0], p[1] || '', anchors)}; });
  }
  function render(){
    var b = BENCH[qSel.value], a = parseFloat(alpha.value), k = parseInt(kIn.value, 10);
    alphaV.textContent = a.toFixed(2); kV.textContent = k;
    meta.textContent = b.tokens.length + ' words, ' + b.dims + ' sparse dimensions; anchor: ' + b.anchors.join(', ') + '; ' + b.n + ' chunks scored';
    var A = legList(b.legs.hashed), Bl = legList(b.legs.bm25);
    legs.innerHTML = [['Leg A: the index\\'s sparse leg (hashed TF, dot product)', A, b.ranks.hashed], ['Leg B: the ablation\\'s leg (BM25)', Bl, b.ranks.bm25]].map(function(x){
      return '<div class="fb-leg"><h5>' + esc(x[0]) + '</h5><ol>' + x[1].map(function(r){
        return '<li' + (r.hit ? ' class="hit"' : '') + '>' + esc(r.loc) + ' <span>' + esc(r.src) + '</span> ' + r.score.toFixed(2) + '</li>'; }).join('') +
        '</ol><div class="fb-rank">anchor at rank ' + (x[2] === null ? 'none' : x[2]) + ' of ' + b.n + '</div></div>';
    }).join('');
    var P = pasted(b.anchors), one = P.length ? P : Bl;
    var label1 = P.length ? 'your dense order from step 4' : 'leg B, standing in for the dense leg until you paste yours';
    var score = {}, info = {};
    /* rrf_fuse(): alpha / (k + rank + 1) for list 1, (1 - alpha) / (k + rank + 1) for list 2, summed per id, sorted */
    one.forEach(function(r, i){ score[r.k] = (score[r.k] || 0) + a / (k + i + 1); info[r.k] = info[r.k] || {loc: r.loc, src: r.src, hit: r.hit}; info[r.k].r1 = i + 1; });
    A.forEach(function(r, i){ score[r.k] = (score[r.k] || 0) + (1 - a) / (k + i + 1); info[r.k] = info[r.k] || {loc: r.loc, src: r.src, hit: r.hit}; info[r.k].r2 = i + 1; if (r.hit) info[r.k].hit = true; });
    var order = Object.keys(score).sort(function(x, y){ return score[y] - score[x]; }).slice(0, 8);
    fusedEl.innerHTML = '<p class="fb-rank">RRF: list 1 = ' + esc(label1) + ', weight ' + a.toFixed(2) + '; list 2 = leg A, weight ' + (1 - a).toFixed(2) + '; k = ' + k + '</p>' +
      '<table><thead><tr><th>#</th><th>chunk</th><th>list 1</th><th>list 2</th><th>score</th></tr></thead><tbody>' +
      order.map(function(kk, i){ var f = info[kk];
        return '<tr' + (f.hit ? ' class="hit"' : '') + '><td class="num">' + (i + 1) + '</td><td>' + esc(f.loc) + ' <span>' + esc(f.src.slice(0, 26)) + '</span></td>' +
               '<td class="num">' + (f.r1 || '-') + '</td><td class="num">' + (f.r2 || '-') + '</td><td class="num">' + score[kk].toFixed(4) + '</td></tr>'; }).join('') +
      '</tbody></table>';
  }
  [qSel, alpha, kIn].forEach(function(el){ el.addEventListener('input', render); el.addEventListener('change', render); });
  dense.addEventListener('input', render);
  render();
})();
</script>
""".replace("__BENCH__", json.dumps(bench, ensure_ascii=False, separators=(",", ":")))

# ------------------------------------------------------------------ step 1's explainer: the two legs, animated
JS += """<script>
(function(){
  'use strict';
  var DV = __DV__;
  var root = document.getElementById('dvs'); if (!root) return;
  var NS = 'http://www.w3.org/2000/svg', sp = document.getElementById('dv-sp'), dn = document.getElementById('dv-dn');
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var DOC = '#94a3b8', QC = '#d97706', HIT = '#0d9488', INK = '#334155';
  var timers = [], cur = 'code', dots = {}, pin = null, link = null;
  /* the dense panel is a sketch: fixed positions for a few of acme's chunks, and where each question lands */
  var MAP = [['np', 70, 62, 'NP-03 notice', 78], ['gr', 130, 38, 'Gratuity rule', 54], ['el', 48, 112, 'Earned leave', 128],
             ['usb', 250, 40, 'USB drives rule', 56], ['gst', 275, 118, 'GST rates', 134], ['inv', 238, 148, 'INV-2026-0412', 164],
             ['cg', 180, 176, 'CGST invoice rules', 192]];
  var PIN = {code: [165, 104, null], para: [98, 92, 'np'], inv: [214, 132, 'inv']};
  function el(tag, attrs, parent){ var e = document.createElementNS(NS, tag); for (var k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; }
  function label(x, y, s, anchor, parent){ var t = el('text', {x: x, y: y, 'text-anchor': anchor || 'start', fill: INK, 'font-size': 12}, parent); t.textContent = s; return t; }
  function later(ms, fn){ if (reduce) fn(); else timers.push(setTimeout(fn, ms)); }
  function num(n){ return n.toLocaleString('en-US'); }
  function ord(n){ var v = n % 100, s = (v > 10 && v < 14) ? 'th' : ({1: 'st', 2: 'nd', 3: 'rd'}[n % 10] || 'th'); return num(n) + s; }
  function rankText(r, n){ return r === null ? 'not found, score 0' : ord(r) + ' of ' + num(n); }
  function X(s){ return 10 + s / DV.dims * 300; }
  function chip(parent, text, win){ var c = document.createElement('span'); c.className = 'dv-rank' + (win ? ' win' : ''); c.textContent = text; parent.appendChild(c); return c; }
  function drawMap(){
    while (dn.firstChild) dn.removeChild(dn.firstChild);
    MAP.forEach(function(d){
      var c = el('circle', {cx: d[1], cy: d[2], r: 5, fill: '#fff', stroke: DOC, 'stroke-width': 1.5}, dn);
      c.style.transition = 'stroke .4s ease, stroke-width .4s ease';
      label(d[1], d[4], d[3], 'middle', dn); dots[d[0]] = c;
    });
    link = el('line', {x1: 0, y1: 0, x2: 0, y2: 0, stroke: HIT, 'stroke-width': 1.5, 'stroke-dasharray': '4 3'}, dn);
    link.style.opacity = 0; link.style.transition = 'opacity .4s ease';
    pin = el('g', {id: 'dv-pin'}, dn);
    el('circle', {r: 7, fill: QC, stroke: '#fff', 'stroke-width': 2}, pin);
    pin.style.transform = 'translate(20px,20px)';
  }
  function play(key){
    cur = key; timers.forEach(clearTimeout); timers = [];
    var q = DV.q[key], shared = {};
    q.shared.forEach(function(s){ shared[s[0]] = 1; });
    root.querySelectorAll('.dv-btn[data-key]').forEach(function(b){ b.setAttribute('aria-pressed', String(b.getAttribute('data-key') === key)); });
    document.getElementById('dv-q').textContent = q.q;
    var toks = document.getElementById('dv-toks'); toks.textContent = '';
    var chips = q.qToks.map(function(t, k){ var c = document.createElement('span'); c.className = 'dv-tok'; c.textContent = t[0]; toks.appendChild(c);
      later(60 + k * 70, function(){ c.classList.add('on'); }); return c; });
    while (sp.firstChild) sp.removeChild(sp.firstChild);
    label(10, 13, q.doc + ': ' + q.docToks.length + ' distinct words', 'start', sp);
    label(10, 127, 'slot 0', 'start', sp); label(310, 127, num(DV.dims), 'end', sp);
    el('line', {x1: 10, y1: 66, x2: 310, y2: 66, stroke: '#cbd5e1', 'stroke-width': 1}, sp);
    var docTick = {};
    q.docToks.forEach(function(d, k){
      var x = X(d[1]), ln = el('line', {x1: x, y1: 65, x2: x, y2: 65 - 9 * d[2], stroke: DOC, 'stroke-width': 1.5}, sp);
      ln.style.opacity = 0; ln.style.transition = 'opacity .3s ease, stroke .4s ease';
      docTick[d[0]] = ln; later(200 + k * 10, function(){ ln.style.opacity = 1; });
    });
    var t0 = 200 + q.docToks.length * 10 + 150, tHit = t0 + q.qToks.length * 90 + 300;
    q.qToks.forEach(function(t, k){
      var x = X(t[1]), ln = el('line', {x1: x, y1: 67, x2: x, y2: 88, stroke: QC, 'stroke-width': 1.5}, sp);
      ln.style.opacity = 0; ln.style.transition = 'opacity .3s ease, stroke .4s ease';
      later(t0 + k * 90, function(){ ln.style.opacity = 1; });
      if (shared[t[0]]) later(tHit, function(){
        ln.style.stroke = HIT; ln.style.strokeWidth = 3;
        if (docTick[t[0]]) { docTick[t[0]].style.stroke = HIT; docTick[t[0]].style.strokeWidth = 3; }
        chips[k].classList.add('hit');
      });
    });
    var math = document.getElementById('dv-math'); math.textContent = '';
    later(tHit + 200, function(){
      math.textContent = q.shared.length ? 'shared: ' + q.shared.map(function(s){ return s[0] + ' ' + s[1].toFixed(1) + ' × ' + s[2].toFixed(1); }).join(' + ') + ' = ' + q.score.toFixed(1)
                                         : 'shared: none, so the score is 0';
    });
    var sr = document.getElementById('dv-sprank'); sr.textContent = '';
    var r1 = chip(sr, 'every word counts: ' + rankText(q.ranks.hashed, q.n), q.ranks.hashed === 1),
        r2 = chip(sr, 'BM25, rare words weigh more: ' + rankText(q.ranks.bm25, q.n), q.ranks.bm25 === 1);
    later(tHit + 600, function(){ r1.classList.add('on'); r2.classList.add('on'); });
    drawMap();
    var p = PIN[key];
    pin.style.transition = reduce ? 'none' : 'transform .9s ease';
    later(400, function(){ pin.style.transform = 'translate(' + p[0] + 'px,' + p[1] + 'px)'; });
    var dr = document.getElementById('dv-dnrank'); dr.textContent = '';
    var r3 = chip(dr, q.dense ? 'dense: ' + ord(q.dense) + ' on your lane' : 'dense: not yet measured on your lane', q.dense === 1), cmd = null;
    if (!q.dense) {
      cmd = document.createElement('p'); cmd.className = 'dv-cmd'; cmd.style.opacity = 0;
      cmd.textContent = "export Q='" + q.q + "' ANCHOR=" + q.anchor + '   # then run step 4'; dr.appendChild(cmd);
    }
    later(1450, function(){
      if (p[2]) { var t = dots[p[2]]; link.setAttribute('x1', p[0]); link.setAttribute('y1', p[1]); link.setAttribute('x2', t.getAttribute('cx')); link.setAttribute('y2', t.getAttribute('cy'));
                  link.style.opacity = 1; t.style.stroke = HIT; t.style.strokeWidth = 3; }
      r3.classList.add('on'); if (cmd) cmd.style.opacity = 1;
    });
    var v = document.getElementById('dv-verdict'); v.textContent = '';
    later(Math.max(tHit + 900, 1900), function(){ v.textContent = q.verdict; });
  }
  root.querySelectorAll('.dv-btn[data-key]').forEach(function(b){ b.addEventListener('click', function(){ play(b.getAttribute('data-key')); }); });
  document.getElementById('dv-replay').addEventListener('click', function(){ play(cur); });
  play('code');
})();
</script>
""".replace("__DV__", json.dumps({"dims": SPARSE_DIMS, "q": dv}, ensure_ascii=False, separators=(",", ":")))

# ------------------------------------------------------------------ step 1's help desk: three panels, animated
JS += """<script>
(function(){
  'use strict';
  var HD = __HD__;
  var root = document.getElementById('hdesk'); if (!root) return;
  var NS = 'http://www.w3.org/2000/svg', map = document.getElementById('hd-map'), alphaIn = document.getElementById('hd-alpha');
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var DOC = '#94a3b8', QC = '#d97706', HIT = '#0d9488', INK = '#334155';
  var timers = [], cur = 'money', dots = {}, pin = null, link = null, rrfVersion = 0;
  var LABEL = {A: [0, -13, 'middle'], B: [14, -6, 'start'], C: [14, 14, 'start'], D: [12, 4, 'start']};
  function el(tag, attrs, parent){ var e = document.createElementNS(NS, tag); for (var k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; }
  function text(x, y, s, anchor){ var t = el('text', {x: x, y: y, 'text-anchor': anchor || 'start', fill: INK, 'font-size': 12}, map); t.textContent = s; return t; }
  function later(ms, fn){ if (reduce) fn(); else timers.push(setTimeout(fn, ms)); }
  function P(xy){ return [40 + xy[0] * 250, 200 - xy[1] * 170]; }
  function xyOf(letter){ return HD.docs.filter(function(d){ return d[0] === letter; })[0][3]; }
  function ord(n){ return n + ({1: 'st', 2: 'nd', 3: 'rd'}[n] || 'th'); }
  function pts(rank){ return 1000 / (HD.k + rank); }
  function fmt(v){ return v.toFixed(2); }
  function words(s){ return s.toLowerCase().match(/[a-z0-9\\-]+/g) || []; }
  function drawDocs(q){
    var box = document.getElementById('hd-docs'); box.textContent = '';
    return HD.docs.map(function(d){
      var row = document.createElement('div'), b = document.createElement('b'), p = document.createElement('p'), n = document.createElement('span'), hits = [];
      row.className = 'hd-doc'; b.textContent = d[0]; n.className = 'hd-n';
      d[2].split(/(\\s+)/).forEach(function(part){
        var s = document.createElement('span'), w = words(part)[0];
        s.textContent = part; if (part.trim()) s.className = 'hd-w';
        if (w && q.shared[d[0]].indexOf(w) >= 0) { s.setAttribute('data-w', w); hits.push(s); }
        p.appendChild(s);
      });
      row.appendChild(b); row.appendChild(p); row.appendChild(n); box.appendChild(row);
      return {letter: d[0], row: row, hits: hits, n: n, count: q.shared[d[0]].length};
    });
  }
  function drawMap(){
    while (map.firstChild) map.removeChild(map.firstChild);
    el('line', {x1: 40, y1: 200, x2: 300, y2: 200, stroke: '#cbd5e1', 'stroke-width': 1}, map);
    el('line', {x1: 40, y1: 200, x2: 40, y2: 20, stroke: '#cbd5e1', 'stroke-width': 1}, map);
    text(300, 217, 'about money', 'end'); text(46, 14, 'about orders and delivery');
    HD.docs.forEach(function(d){
      var p = P(d[3]), c = el('circle', {cx: p[0], cy: p[1], r: 6, fill: '#fff', stroke: DOC, 'stroke-width': 1.5}, map), L = LABEL[d[0]];
      c.style.transition = 'stroke .4s ease, stroke-width .4s ease';
      text(p[0] + L[0], p[1] + L[1], d[0] + ' ' + d[1], L[2]); dots[d[0]] = c;
    });
    link = el('line', {x1: 0, y1: 0, x2: 0, y2: 0, stroke: HIT, 'stroke-width': 1.5, 'stroke-dasharray': '4 3'}, map);
    link.style.opacity = 0; link.style.transition = 'opacity .4s ease';
    pin = el('g', {id: 'hd-pin'}, map);
    el('circle', {r: 7, fill: QC, stroke: '#fff', 'stroke-width': 2}, pin);
    pin.style.transform = 'translate(290px,34px)';
  }
  function renderRrf(q, instant, t0){
    var mine = ++rrfVersion, a = parseFloat(alphaIn.value), score = {}, cell = {};
    document.getElementById('hd-alpha-v').textContent = a.toFixed(1);
    HD.docs.forEach(function(d){
      var L = d[0], dr = q.dense.indexOf(L) + 1, sr = q.sparse.indexOf(L) + 1;
      cell[L] = {dr: dr, sr: sr, dp: dr ? a * pts(dr) : 0, sp: sr ? (1 - a) * pts(sr) : 0};
      score[L] = cell[L].dp + cell[L].sp;
    });
    var order = HD.docs.map(function(d){ return d[0]; }).sort(function(x, y){ return (score[y] - score[x]) || (q.dense.indexOf(x) - q.dense.indexOf(y)); });
    function leg(rank, w, v){ return rank ? ord(rank) + '<span>' + w.toFixed(1) + ' × ' + fmt(pts(rank)) + ' = ' + fmt(v) + '</span>' : 'not in the list<span>0</span>'; }
    document.getElementById('hd-rrf').innerHTML = '<table class="comp-table"><thead><tr><th>Answer</th><th>Dense</th><th>Sparse</th><th>Total</th></tr></thead><tbody>' +
      HD.docs.map(function(d){ var c = cell[d[0]];
        return '<tr' + (order[0] === d[0] ? ' class="win"' : '') + '><td><b>' + d[0] + '</b> ' + d[1] + '</td><td data-label="Dense">' + leg(c.dr, a, c.dp) +
               '</td><td data-label="Sparse">' + leg(c.sr, 1 - a, c.sp) + '</td><td class="tot" data-label="Total">' + fmt(score[d[0]]) + '</td></tr>'; }).join('') + '</tbody></table>';
    var rows = document.querySelectorAll('#hd-rrf tbody tr'), fused = document.getElementById('hd-fused');
    var line = 'Merged list: ' + order.map(function(L, i){ return (i === 0 ? '' : (Math.abs(score[L] - score[order[i - 1]]) < 1e-9 ? ' = ' : ' › ')) + L + ' ' + fmt(score[L]); }).join('');
    if (instant) { rows.forEach(function(r){ r.classList.add('on'); }); fused.textContent = line; return; }
    fused.textContent = '';
    rows.forEach(function(r, k){ later(t0 + k * 350, function(){ if (mine === rrfVersion) r.classList.add('on'); }); });
    later(t0 + rows.length * 350 + 200, function(){ if (mine === rrfVersion) fused.textContent = line; });
  }
  function play(key){
    cur = key; timers.forEach(clearTimeout); timers = []; alphaIn.value = HD.alpha;
    var q = HD.q[key], chips = {};
    root.querySelectorAll('.hd-btn[data-key]').forEach(function(b){ b.setAttribute('aria-pressed', String(b.getAttribute('data-key') === key)); });
    document.getElementById('hd-q').textContent = q.q;
    var toks = document.getElementById('hd-toks'); toks.textContent = '';
    q.words.forEach(function(w, k){ var c = document.createElement('span'); c.className = 'hd-tok'; c.textContent = w; toks.appendChild(c); chips[w] = c;
      later(60 + k * 60, function(){ c.classList.add('on'); }); });
    var rows = drawDocs(q), t = 450;
    rows.forEach(function(r, k){ later(t + k * 450, function(){
      r.hits.forEach(function(s){ s.classList.add('hit'); chips[s.getAttribute('data-w')].classList.add('hit'); });
      r.n.textContent = r.count + (r.count === 1 ? ' word' : ' words'); }); });
    var tSparse = t + rows.length * 450, spl = document.getElementById('hd-splist'); spl.textContent = '';
    later(tSparse, function(){
      rows.forEach(function(r){ if (q.sparse[0] === r.letter) r.row.classList.add('win'); });
      spl.textContent = q.sparse.length ? 'Sparse list: ' + q.sparse.map(function(l){ return l + ' (' + q.shared[l].length + ')'; }).join(', ') : 'Sparse list: empty, every answer scores 0';
    });
    drawMap();
    pin.style.transition = reduce ? 'none' : 'transform .9s ease';
    var qp = P(q.pin), tDense = tSparse + 1200, dnl = document.getElementById('hd-dnlist'); dnl.textContent = '';
    later(tSparse + 200, function(){ pin.style.transform = 'translate(' + qp[0] + 'px,' + qp[1] + 'px)'; });
    later(tDense, function(){
      var best = q.dist[q.dense[0]], near = q.dense.filter(function(l){ return q.dist[l] === best; });
      near.forEach(function(l){ dots[l].style.stroke = HIT; dots[l].style.strokeWidth = 3; });
      if (near.length === 1) { var p = P(xyOf(near[0])); link.setAttribute('x1', qp[0]); link.setAttribute('y1', qp[1]); link.setAttribute('x2', p[0]); link.setAttribute('y2', p[1]); link.style.opacity = 1; }
      dnl.textContent = 'Dense list, nearest first: ' + q.dense.map(function(l){ return l + ' ' + q.dist[l].toFixed(2); }).join(', ') +
                        (near.length > 1 ? ', a tie: ' + near.join(' and ') + ' are equally near' : '');
    });
    var tRrf = tDense + 500;
    renderRrf(q, false, tRrf);
    var v = document.getElementById('hd-verdict'); v.textContent = '';
    later(tRrf + HD.docs.length * 350 + 700, function(){ v.textContent = q.verdict; });
  }
  root.querySelectorAll('.hd-btn[data-key]').forEach(function(b){ b.addEventListener('click', function(){ play(b.getAttribute('data-key')); }); });
  document.getElementById('hd-replay').addEventListener('click', function(){ play(cur); });
  alphaIn.addEventListener('input', function(){ renderRrf(HD.q[cur], true); });
  play('money');
})();
</script>
""".replace("__HD__", json.dumps({"k": HD_K, "alpha": HD_ALPHA, "docs": [[d[0], d[1], d[2], list(d[3])] for d in HD_DOCS], "q": hd},
                                ensure_ascii=False, separators=(",", ":")))

body = "".join([
    subst(fill(pb.part(LESSON, "a"))),
    setup,
    subst(fill(pb.part(LESSON, "b"))),
    subst(fill(pb.part(LESSON, "c"))),
])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"bench: {N} chunks from {DOCS} documents | golden {STATS} | ranks " + ", ".join(f"{k}: A {v['ranks']['hashed']} B {v['ranks']['bm25']}" for k, v in bench.items()))
print("two vectors: " + ", ".join(f"{k}: shared {[s[0] for s in v['shared']]} score {v['score']} A {v['ranks']['hashed']} B {v['ranks']['bm25']} dense {v['dense']}" for k, v in dv.items()))
