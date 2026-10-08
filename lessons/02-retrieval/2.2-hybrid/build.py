"""Build lesson 2.2 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

The fusion bench is computed here, from the kit, at build time: acme's corpus cut by the kit's chunker, the index's
sparse leg (shared/sparse_encoder.py, scored by dot product as Vector Search scores a sparse vector) and the
ablation's leg (BM25Okapi with rank_bm25 0.2.2's constants, ported below so the build needs no extra package).
"""
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


def subst(text: str) -> str:
    reps = {**{k: str(v) for k, v in STATS.items()}, "CHUNKS": f"{N:,}", "DOCS": str(DOCS), "NP03_POS": str(NP03_POS),
            "BENCH_ROWS": "\n".join(bench_rows), "BENCH_OPTIONS": "".join(bench_options),
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

body = "".join([
    subst(fill(pb.part(LESSON, "a"))),
    setup,
    subst(fill(pb.part(LESSON, "b"))),
    subst(fill(pb.part(LESSON, "c"))),
])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"bench: {N} chunks from {DOCS} documents | golden {STATS} | ranks " + ", ".join(f"{k}: A {v['ranks']['hashed']} B {v['ranks']['bm25']}" for k, v in bench.items()))
