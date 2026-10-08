"""Build lesson 2.1 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts."""
import hashlib
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, PLAN, block, filler, finish, hl, hl_plain, setup_section, window  # noqa: E402,F401

LESSON = "2.1"


title = "<title>Lesson 2.1 Apply query embeddings and authorized filters - the question's vector, the tenant from identity, and the two filters a caller may send | Netsetos</title>\n"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.rq-controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px 16px;margin-bottom:10px;}
.rq-l{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.rq-l select{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.rq-path{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:6px;}
.rq-path li{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 10px;font-size:12.5px;line-height:1.45;color:var(--slate);display:grid;grid-template-columns:120px 1fr;gap:8px;align-items:start;min-width:0;}
.rq-path li b{font-family:var(--mono);font-size:var(--kicker-size);color:var(--navy);overflow-wrap:anywhere;}
.rq-path li.ok{border-color:var(--teal);}
.rq-path li.stop{border:2px solid #d97706;background:#fffbeb;color:var(--navy);}
.rq-path li.end{border:2px solid var(--teal);background:var(--teal-light);color:var(--navy);}
.lesson-repair{border:1px solid var(--border);border-radius:10px;padding:14px;margin:20px 0;}
.lesson-repair>summary{cursor:pointer;min-height:44px;font-weight:700;display:list-item;}
@media (max-width:480px){.rq-path li{grid-template-columns:1fr;}}
"""

setup = setup_section()
# Keep this lesson's pin and restoration at their own checkpoints.
pin_start = setup.index("<h4>Which store answers acme?")
pin_end = setup.index('<div class="box box-amber"><div class="box-title">Two identities', pin_start)
setup = (setup[:pin_start] + '<h4>Select the backend after checking the index</h4><p>The <a href="#preflight">preflight below</a> saves the original Acme pin and selects vector only after its endpoint check passes. Restore the saved pin at <a href="#restore-pin">the end of the lesson</a>; running a restore command here would immediately undo the demo setting.</p>\n' + setup[pin_end:])



API = "services/rag-api/main.py"
RET = "services/rag-api/retriever.py"
EXCERPTS = {
    "embed_query": ("services/rag-api/retriever.py - embed_query(): the question's side of the declared pair", block(RET, "def embed_query(", end="def _firestore_fallback(")),
    "handler_head": ("services/rag-api/main.py - the handler's first lines: the roster, the filters, one vector, the pool", block(API, '@app.post("/v1/query", response_model=RAGResponse)', end='    if hit:')),
    "auth": ("services/rag-api/auth.py - verify_iap() and enforce_membership()", block("services/rag-api/auth.py", "def verify_iap(", n=27)),
    "is_member": ("shared/tenancy.py - is_member(): one document read", block("shared/tenancy.py", "def is_member(", end="def tenant_for(")),
    "schema": ("services/rag-api/schemas.py - the request: the two filter keys, the unread user_id", block("services/rag-api/schemas.py", "FILTER_KEYS = ", n=13)),
    "check_filters": ("services/rag-api/main.py - check_filters(): a 400 before any work", block(API, "def check_filters(", end="EMPTY_POOL_ANSWER = (")),
    "restricts": ("services/rag-api/retriever.py - _dense_retrieve(): the restricts, in order, then the ids hydrated and marked", block(RET, '    restricts = [Namespace(name="tenant_id", allow_tokens=[tenant_id])]', n=6) + "\n" + block(RET, "            resp = _index_endpoint().find_neighbors(", n=5) + "\n" + block(RET, "    pool = _hydrate(ids[:settings.top_k_retrieve], scores)", n=4)),
    "hybrid_filters": ("services/rag-api/hybrid.py - the same restricts under hybrid, the tenant exactly once", block("services/rag-api/hybrid.py", "    filters = [Namespace(name=\"tenant_id\", allow_tokens=[tenant_id])]", n=5)),
    "backend_for": ("services/rag-api/main.py - choose_for() and retrieval_backend_for(): the store, per request", block(API, "def choose_for(", end="def _fingerprint(")),
    "prefer_current": ("services/rag-api/retriever.py - prefer_current(): a retired row is never a source", block(RET, "def prefer_current(", end="@lru_cache(maxsize=1)")),
    "current_setting": ("services/rag-api/config.py - the setting, and the two sizes", block("services/rag-api/config.py", "    retrieval_current_only: str = Field(", n=1) + "\n" + block("services/rag-api/config.py", "    top_k_retrieve: int = Field(", n=2)),
    "cache_lookup": ("services/rag-api/main.py - _semantic_hit(): the vector, the fingerprint and the scope", block(API, "def _semantic_hit(", end="def _semantic_store(")),
    "sizes": ("services/rag-api/schemas.py - top_k on the request", block("services/rag-api/schemas.py", "    top_k: int = Field(default=5, ge=1, le=20)", n=1)),
}


fill = filler(EXCERPTS, window)


SHA1 = hashlib.sha256((KIT / "evals/corpus/acme/hr_policy_2026.md").read_bytes()).hexdigest()


class _Refused(Exception):
    def __init__(self, status_code, detail=""):
        super().__init__(detail)
        self.status_code, self.detail = status_code, detail


def refusal(filters: dict) -> str:
    """What the kit's own check_filters() answers for `filters`: run, not retyped, so the page's 400s are the API's."""
    ns = {"HTTPException": _Refused, "FILTER_KEYS": ("doc_type", "kind")}
    exec(EXCERPTS["check_filters"][1], ns)
    try:
        ns["check_filters"](filters)
    except _Refused as e:
        assert e.status_code == 400
        return e.detail
    raise AssertionError(f"check_filters accepted {filters}")


assert 'FILTER_KEYS = ("doc_type", "kind")' in (KIT / "services/rag-api/schemas.py").read_text(encoding="utf-8")
DOC_TYPE_400 = refusal({"doc_type": 3})                  # the step-5 call and the widget's "a number" choice
KIND_LIST_400 = refusal({"kind": ["text"]})
assert refusal({"doc_type": ["a", "b", "c", "d", "e", "f"]}) == refusal({"doc_type": []}) == DOC_TYPE_400
assert not set("'\\<>&") & set(DOC_TYPE_400 + KIND_LIST_400), (DOC_TYPE_400, KIND_LIST_400)   # spliced raw into a JS '...' string and HTML


def subst(text: str) -> str:
    return (text.replace("%%SHA1_12%%", SHA1[:12]).replace("%%SHA1_8%%", SHA1[:8])
            .replace("%%DOC_TYPE_400%%", DOC_TYPE_400).replace("%%KIND_LIST_400%%", KIND_LIST_400))


# ---- the request gate: the handler's order, with the lane's real data ----
JS = """<script>
(function(){
  'use strict';
  var root = document.getElementById('gates'); if (!root) return;
  var who = document.getElementById('rq-who'), tenant = document.getElementById('rq-tenant'), filt = document.getElementById('rq-filters'), path = document.getElementById('rq-path');
  var ROSTER = {ui: ['acme', 'zeta', 'globex'], outsider: [], none: [], bad: []};
  var CAP = {acme: 'Rs 40,000 per trip, cited to hr_policy_2026.md (EXP-12)', zeta: 'Rs 25,000 per trip, cited to hr_policy_zeta_2026.md (EXP-12)'};
  function esc(t){ return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  function li(cls, gate, text){ return '<li class="' + cls + '"><b>' + esc(gate) + '</b><span>' + esc(text) + '</span></li>'; }
  function render(){
    var w = who.value, t = tenant.value, f = filt.value, out = [];
    if (w === 'none'){ out.push(li('stop', 'Cloud Run', '403: the service allows no unauthenticated caller. Nothing reached the API.')); path.innerHTML = out.join(''); return; }
    out.push(li('ok', 'Cloud Run', 'a token is present: the request reaches the API'));
    if (w === 'bad'){ out.push(li('stop', 'verify_iap', '401: the bearer token was minted for another audience; the API does not know who this is.')); path.innerHTML = out.join(''); return; }
    var email = w === 'ui' ? 'documind-ui-sa@<project>.iam.gserviceaccount.com' : 'documind-outsider-sa@<project>.iam.gserviceaccount.com';
    out.push(li('ok', 'verify_iap', 'identity ' + email + ' (via iam: the bearer token, verified for this service\\'s URL)'));
    if (ROSTER[w].indexOf(t) === -1){ out.push(li('stop', 'enforce_membership', '403 not a member of this tenant: tenants/' + t + '/members/' + email + ' does not exist. No embedding, no index call.')); path.innerHTML = out.join(''); return; }
    out.push(li('ok', 'enforce_membership', 'tenants/' + t + '/members/' + email + ' exists: the roster allows ' + t));
    var restricts = ['tenant_id = ' + t];
    if (f === 'tenant'){ out.push(li('stop', 'check_filters', '400 unknown filter key(s) tenant_id; allowed: doc_type, kind. The tenant is the roster\\'s, never the caller\\'s.')); path.innerHTML = out.join(''); return; }
    if (f === 'current'){ out.push(li('stop', 'check_filters', '400 unknown filter key(s) current; allowed: doc_type, kind. Current is the ledger\\'s, never the caller\\'s.')); path.innerHTML = out.join(''); return; }
    if (f === 'number'){ out.push(li('stop', 'check_filters', '400 %%DOC_TYPE_400%%.')); path.innerHTML = out.join(''); return; }
    out.push(li('ok', 'check_filters', f === 'none' ? 'no filters: nothing to check' : 'an allowed key with a string value: passes'));
    if (f === 'kind') restricts.push('kind = text');
    if (f === 'policy') restricts.push('doc_type = policy');
    out.push(li('ok', 'embed_query', 'the question, once, under RETRIEVAL_QUERY with the declared model: 768 numbers, shared with the answer cache'));
    out.push(li('ok', 'find_neighbors', 'restricts: ' + restricts.join(', ') + ' (plus current = true when RETRIEVAL_CURRENT_ONLY is on)'));
    if (f === 'policy'){ out.push(li('stop', 'the pool', 'empty: the worker stamped every plain upload doc_type = unknown, so no datapoint carries policy. answerable: false, no citations, no model call.')); path.innerHTML = out.join(''); return; }
    if (t === 'globex'){ out.push(li('stop', 'the pool', '20 candidates from globex\\'s corpus, none about travel: the model refuses (answerable: false) rather than borrow acme\\'s clause, which the restrict kept out of the pool.')); path.innerHTML = out.join(''); return; }
    out.push(li('end', 'the answer', CAP[t] + ' - the other tenant\\'s figure never entered the pool.'));
    path.innerHTML = out.join('');
  }
  [who, tenant, filt].forEach(function(el){ el.addEventListener('change', render); });
  render();
})();
</script>
"""

body = "".join([
    subst(fill(pb.part(LESSON, "a"))),
    setup,
    pb.part(LESSON, "preflight"),
    subst(fill(pb.part(LESSON, "b"))),
    subst(fill(pb.part(LESSON, "c"))),
])
finish(LESSON, title, EXTRA_CSS, body, subst(JS))
