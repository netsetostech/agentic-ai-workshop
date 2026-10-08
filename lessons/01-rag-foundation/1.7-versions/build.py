"""Build lesson 1.7 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts."""
import hashlib
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, PLAN, block, filler, finish, hl, hl_plain, setup_section, window  # noqa: E402,F401

LESSON = "1.7"


title = "<title>Lesson 1.7 Publish versions, retire documents and reject stale events - one current version, three ways to stop being it, and the event that must not count | Netsetos</title>\n"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.vp-buttons{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px;}
.vp-btn{font:inherit;font-size:var(--small-size);font-weight:500;min-height:44px;padding:8px 12px;border:1px solid var(--teal);border-radius:8px;background:var(--card);color:var(--teal);cursor:pointer;flex:1 1 170px;}
.vp-btn:disabled{opacity:.4;cursor:default;}
.vp-status{display:flex;flex-wrap:wrap;gap:8px 16px;font-family:var(--mono);font-size:var(--kicker-size);color:var(--navy);margin:6px 0 10px;}
.vp-status span b{color:var(--teal);}
.vp-versions{display:flex;flex-wrap:wrap;gap:8px;}
.vp-card{flex:1 1 170px;border-radius:10px;padding:8px 10px;font-size:12.5px;line-height:1.45;min-width:0;border:1px solid var(--border);background:var(--card);color:var(--slate);}
.vp-card.cur{border:2px solid var(--teal);background:var(--teal-light);color:var(--navy);}
.vp-card b{display:block;font-family:var(--mono);font-size:var(--kicker-size);color:var(--navy);margin-bottom:3px;}
.vp-log{margin-top:10px;padding:8px 12px;border-left:4px solid #d97706;background:#fffbeb;border-radius:0 8px 8px 0;font-size:var(--small-size);color:var(--navy);}
@media (hover:hover) and (pointer:fine){.vp-btn:hover:not(:disabled){background:var(--teal-light);}}
"""

setup = setup_section()



IDM = "services/ingest/idempotency.py"
RET = "services/rag-api/retriever.py"
REC = "services/ingest/reconcile.py"
ING = "services/ingest/main.py"
EXCERPTS = {
    "swap": ("services/ingest/idempotency.py - swap_versions(): the docstring, and the new version first", block(IDM, "def swap_versions(", end="    for snap in rows:                                       # then the old")),
    "retire_fn": ("services/ingest/idempotency.py - _retire(): the four fields, nothing else", block(IDM, "def _retire(", end="def retire_previous(")),
    "newest": ("services/rag-api/retriever.py - newest_per_source() and prefer_current(): the reader's guard", block(RET, "def newest_per_source(", end="@lru_cache(maxsize=1)")),
    "retire_prev": ("services/ingest/idempotency.py - retire_previous(): a flag, never a delete", block(IDM, "def retire_previous(", n=9)),
    "ttl": ("terraform/firestore_indexes.tf - the TTL policy: the only deleter", block("terraform/firestore_indexes.tf", "# TTL for superseded/staged chunk rows.", n=9)),
    "purge_mk": ("mk/lifecycle.mk - purge: the policy's manual twin", block("mk/lifecycle.mk", "# the manual twin of the TTL policy", n=4)),
    "guard": ("services/ingest/main.py - push(): the generation guard, and the download by generation", block(ING, "    # THE GENERATION GUARD (12 September 2026)", end="    doc = DocumentContract(tenant_id=msg.tenant_id, sha256=sha256_of(content),")),
    "stale_fn": ("services/ingest/idempotency.py - stale_generation(): the ledger's number against the event's", block(IDM, "def stale_generation(", end="def _retire(")),
    "is_stale": ("services/ingest/contracts.py - is_stale(): the rule, on its own", block("services/ingest/contracts.py", "def is_stale(", n=9)),
    "withdrawn_fn": ("services/ingest/idempotency.py - withdrawn(): the tombstone, asked twice", block(IDM, "def withdrawn(", end="def reactivate(")),
    "retire_cli": ("services/ingest/reconcile.py - --retire: what make retire writes", "        if not a.apply:\n" + block(REC, 'print(f"would withdraw {uri}', n=12)),
    "restore_cli": ("services/ingest/reconcile.py - --restore: the way back", block(REC, "    if a.restore:", end="    if a.backfill:")),
    "retire_mk": ("mk/lifecycle.mk - retire and restore, as make runs them", block("mk/lifecycle.mk", "retire: guard-project", n=4) + "\n\n" + block("mk/lifecycle.mk", "restore: guard-project", n=3)),
    "walk_states": ("services/ingest/reconcile.py - the walk's plan: withdrawn is kept, retired is re-ingested", block(REC, '        elif row.get("status") == "withdrawn":', n=12)),
    "fingerprint_fn": ("services/ingest/idempotency.py - refresh_fingerprint(): the cache follows the ledger", block(IDM, "def refresh_fingerprint(", n=200)),
}


fill = filler(EXCERPTS, window)


V1 = (KIT / "evals/corpus/acme/hr_policy_2026.md").read_bytes()
V2 = (KIT / "evals/demo/hr_policy_2026_v2.md").read_bytes()
r3 = V1.decode("utf-8").replace("# ACME Employee Handbook 2026\n", "# ACME Employee Handbook 2026 (revision 3)\n\nEffective from: 2026-11-01. Revision 3 changes NP-03: the notice period for a confirmed E3 becomes 90 days.\n", 1).replace("serves a notice period of 60 days", "serves a notice period of 90 days", 1)
SHA1, SHA2, SHA3 = hashlib.sha256(V1).hexdigest(), hashlib.sha256(V2).hexdigest(), hashlib.sha256(r3.encode("utf-8")).hexdigest()
empty = re.search(r'^EMPTY_POOL_ANSWER\s*=\s*\(?\s*"([^"]+)"', (KIT / "services/rag-api/main.py").read_text(encoding="utf-8"), re.M)
EMPTY_POOL = empty.group(1) if empty else "(the API's empty-pool refusal)"


def subst(text: str) -> str:
    return (text.replace("%%SHA1_8%%", SHA1[:8]).replace("%%SHA2_8%%", SHA2[:8]).replace("%%SHA3_8%%", SHA3[:8])
            .replace("%%EMPTY_POOL%%", html.escape(EMPTY_POOL[:90])))


# ---- the version player: the kit's rules as a state machine ----
JS = """<script>
(function(){
  'use strict';
  var root = document.getElementById('lifecycle'); if (!root) return;
  var status = document.getElementById('vp-status'), vers = document.getElementById('vp-versions'), log = document.getElementById('vp-log'), btns = root.querySelectorAll('.vp-btn');
  var S;
  function fresh(){ S = {ledger: 'indexed', next: 2, versions: [{id: 'v1', claim: 'indexed', rows: 'current', expires: null, seen: 'the corpus load'}],
                          log: 'the corpus load: ingest_ok, 283 chunks embedded; the ledger row says indexed', day: 0}; }
  function current(){ return S.versions.find(function(v){ return v.rows === 'current'; }); }
  function retirable(){ return S.versions.filter(function(v){ return v.rows === 'retired'; }); }
  function retireCurrent(by, log){ var c = current(); if (!c) return 0; c.rows = 'retired'; c.claim = 'superseded'; c.expires = S.day + 30; c.by = by; return 1; }
  function activate(v){ v.rows = 'current'; v.claim = 'indexed'; v.expires = null; v.by = null; v.reactivated = true; }   /* reactivate() and the swap delete superseded_by, superseded_at, expire_at */
  var ACTS = {
    reissue: {ok: function(){ return S.versions.length < 5; }, run: function(){
      var id = 'v' + (S.next++); retireCurrent(id);
      S.versions.push({id: id, claim: 'indexed', rows: 'current', expires: null});
      S.ledger = 'indexed'; S.log = 'the worker: ingest_ok for ' + id + ' (changed chunks embedded, the rest lent by hash); ingest_superseded for the version it retired' + (S.ledger === 'withdrawn' ? '' : '') + '. The ledger row says indexed and names ' + id + '.'; }},
    same: {ok: function(){ return !!current(); }, run: function(){ S.log = 'the worker: ingest_duplicate - the claim is already indexed; acknowledged, nothing written.'; }},
    undo: {ok: function(){ return retirable().length > 0 && S.ledger !== 'retired'; }, run: function(){
      var v = retirable()[retirable().length - 1];
      if (S.ledger === 'withdrawn'){ S.log = 'the worker: ingest_withdrawn - the tombstone holds; acknowledged, nothing flipped. make restore SOURCE= clears it.'; return; }
      retireCurrent(v.id); activate(v);
      S.ledger = 'indexed'; S.log = 'the worker: ingest_reactivated for ' + v.id + ' - its retired rows flipped back, embedded 0; the newer version retired in turn.'; }},
    retire: {ok: function(){ return !!current() && S.ledger === 'indexed'; }, run: function(){
      retireCurrent(null); S.ledger = 'withdrawn'; S.log = 'make retire: reconcile_withdrawn - every current row retired with a 30-day expiry, the ledger row says withdrawn, the fingerprint moved. The object stays in the bucket.'; }},
    restore: {ok: function(){ return S.ledger === 'withdrawn'; }, run: function(){
      var v = retirable()[retirable().length - 1]; S.ledger = 'retired';
      if (v){ retireCurrent(v.id); activate(v); S.ledger = 'indexed';
        S.log = 'make restore: reconcile_restored - the ledger row to retired, the object rewritten onto itself; the worker: ingest_reactivated for ' + v.id + ', embedded 0. The ledger row says indexed.'; }
      else { var id = 'v' + (S.next++); S.versions.push({id: id, claim: 'indexed', rows: 'current', expires: null}); S.ledger = 'indexed';
        S.log = 'make restore: the retired rows had expired, so the rewrite was a fresh version: ingest_ok for ' + id + ', every chunk embedded.'; } }},
    gone: {ok: function(){ return !!current() && S.ledger === 'indexed'; }, run: function(){
      retireCurrent(null); S.ledger = 'retired'; S.log = 'the nightly walk: the object left the bucket - retire: the rows retired with a 30-day expiry, the ledger row says retired.'; }},
    back: {ok: function(){ return S.ledger === 'retired'; }, run: function(){
      var v = retirable()[retirable().length - 1];
      if (v){ activate(v); S.ledger = 'indexed';
        S.log = 'the object is back (the same bytes): the worker finds a superseded claim inside the window - ingest_reactivated, embedded 0; the ledger row says indexed.'; }
      else { var id = 'v' + (S.next++); S.versions.push({id: id, claim: 'indexed', rows: 'current', expires: null}); S.ledger = 'indexed';
        S.log = 'the object is back after the rows expired: reactivate_incomplete, the claim retaken, ingest_ok as a fresh version.'; } }},
    old: {ok: function(){ return true; }, run: function(){ S.log = 'the worker: ingest_stale_event - older than the ledger; acknowledged, nothing downloaded, nothing changed.'; }},
    ttl: {ok: function(){ return retirable().length > 0; }, run: function(){
      S.day += 30; var gone = 0; S.versions.forEach(function(v){ if (v.rows === 'retired' && v.expires !== null && v.expires <= S.day){ v.rows = 'rows expired (deleted by the TTL policy)'; gone++; } });
      S.log = '30 days pass: the TTL policy deleted the retired rows of ' + gone + ' version(s). Their claims stay superseded; their bytes would now be a fresh version.'; }},
    reset: {ok: function(){ return true; }, run: function(){ fresh(); }}
  };
  function render(){
    var c = current();
    status.innerHTML = '<span>ledger row: <b>' + S.ledger + '</b></span><span>day <b>' + S.day + '</b></span><span>a reader sees: <b>' + (c ? c.id : 'no current version: a refusal') + '</b></span>';
    vers.innerHTML = S.versions.map(function(v){
      return '<div class="vp-card' + (v.rows === 'current' ? ' cur' : '') + '"><b>' + v.id + ' &middot; claim ' + v.claim + '</b>rows: ' + v.rows + (v.expires !== null && v.rows === 'retired' ? ' (expire on day ' + v.expires + ')' : '') + (v.by ? '<br>superseded_by ' + v.by : '') + (v.reactivated ? '<br>reactivated' : '') + '</div>';
    }).join('');
    log.textContent = S.log;
    btns.forEach(function(b){ b.disabled = !ACTS[b.getAttribute('data-act')].ok(); });
  }
  btns.forEach(function(b){ b.addEventListener('click', function(){ var act = ACTS[b.getAttribute('data-act')]; if (act.ok()){ act.run(); render(); } }); });
  fresh(); render();
})();
</script>
"""

body = "".join([
    subst(fill(pb.part(LESSON, "a"))),
    setup,
    subst(fill(pb.part(LESSON, "b"))),
    subst(fill(pb.part(LESSON, "c"))),
])
finish(LESSON, title, EXTRA_CSS, body, JS)
