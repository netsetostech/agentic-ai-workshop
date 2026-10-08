"""Build lesson 1.8 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts."""
import html
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, PLAN, block, filler, finish, hl, hl_plain, setup_section, window  # noqa: E402,F401

LESSON = "1.8"


title = "<title>Lesson 1.8 Restore documents and reconcile index differences - one document, a visible gap, and a verified return | Netsetos</title>\n"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.ws-rows{display:flex;flex-direction:column;gap:8px;}
.ws-row{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 10px;display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:6px 10px;align-items:end;min-width:0;}
.ws-row b{font-family:var(--mono);font-size:var(--kicker-size);color:var(--navy);grid-column:1 / -1;overflow-wrap:anywhere;}
.ws-l{font-size:var(--small-size);color:var(--slate);display:flex;flex-direction:column;gap:3px;min-width:0;}
.ws-l select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:#fff;min-height:44px;max-width:100%;}
.ws-l.off{opacity:.45;}
.ws-act{grid-column:1 / -1;font-size:12.5px;line-height:1.4;color:var(--navy);padding-top:4px;border-top:1px dashed var(--border);}
.ws-act em{font-family:var(--mono);font-style:normal;font-weight:700;color:var(--teal);}
.ws-act em.drift{color:#b45309;}
.ws-sum{margin-top:10px;padding:8px 12px;border-left:4px solid #d97706;background:#fffbeb;border-radius:0 8px 8px 0;font-family:var(--mono);font-size:var(--kicker-size);color:var(--navy);overflow-wrap:anywhere;}
"""

EXTRA_CSS += """
/* Chapter 1.8's static flows need no network renderer and remain readable by panning on a phone. */
.life-flow{display:flex;gap:8px;align-items:center;}
.life-flow>div{flex:1;min-width:0;border:1px solid #99d8d0;border-radius:10px;padding:12px;background:#f0fdfa;}
.life-flow b,.life-flow span:not(.life-arrow){display:block;}
.life-flow b{color:#0f1729;margin-bottom:6px;}
.life-flow>div>span{font-size:13px;line-height:1.6;}
.life-arrow{color:#0d9488;font-size:22px;}
.rf-pan{--pan-floor:760px;overflow-x:auto;overscroll-behavior-x:contain;-webkit-overflow-scrolling:touch;min-width:0;}
.rf-pan svg{display:block;width:var(--pan-floor);min-width:var(--pan-floor);max-width:none;height:auto;}
.rf-pan text{font-family:Arial,sans-serif;font-size:17px;fill:#0f1729;}
.rf-pan rect,.rf-pan polygon{fill:#fff;stroke:#64748b;stroke-width:1.5;}
.rf-pan .rf-question polygon{fill:#f0f9ff;stroke:#0891b2;}
.rf-pan .rf-repair rect{fill:#fff7ed;stroke:#c2410c;}
.rf-pan .rf-keep rect{fill:#f0fdfa;stroke:#0d9488;}
.rf-pan .rf-hash rect{fill:#eff6ff;stroke:#2563eb;}
.rf-pan .rf-edge{fill:none;stroke:#475569;stroke-width:1.5;}
.rf-pan .rf-label{font-size:15px;paint-order:stroke;stroke:#fff;stroke-width:5px;stroke-linejoin:round;}
.chapter-extra{border:1px solid var(--border);border-radius:10px;padding:14px;margin:20px 0;}
.chapter-extra>summary{cursor:pointer;min-height:44px;font-weight:700;display:list-item;}
@media(max-width:679.98px){.life-flow{flex-direction:column;align-items:stretch;}.life-arrow{align-self:center;transform:rotate(90deg);}}
"""

setup = setup_section()
# Keep the shared setup, but separate this lesson's save/set/restore operations.
pin_start = setup.index("<h4>Which store answers acme?")
pin_end = setup.index('<div class="box box-amber"><div class="box-title">Two identities', pin_start)
setup = (setup[:pin_start] + '<h4>Keep the backend change with the demo</h4><p>Step 3 saves the existing tenant pin before selecting vector. Step 12 restores that saved value. Run them at their own checkpoints; copying a setup and restoration command together immediately undoes the lesson setting.</p>\n' + setup[pin_end:])
setup = setup.replace("step 3 makes the difference visible.", "the exact-source checks below use the operator token's tenant access.")
old_scope = "means this machine has no Application Default Credentials: Python fell back to the workstation's own service-account token, which covers the bucket but not Firestore, so the <code>gcloud storage</code> lines keep working while every Firestore read is refused."
setup = setup.replace(old_scope, "means the token Python selected lacks the Firestore scope. Workstation credentials or a differently scoped ADC file can cause it; a successful gcloud storage call does not establish which credentials Python uses.")



REC = "services/ingest/reconcile.py"
IDM = "services/ingest/idempotency.py"
MK = "mk/lifecycle.mk"
EXCERPTS = {
    "queue_claim": ("services/ingest/main.py - the worker records the queued claim", block("services/ingest/main.py", '    _db.collection("ingest_batch").document(doc.doc_key).set({', n=7)),
    "queue_match": ("services/ingest/reconcile.py - matching the queued object and generation", block(REC, "    queued = {", n=12)),
    "plan_objects": ("services/ingest/reconcile.py - plan(): one decision per live object", block(REC, "    for o in objects:", end="    for sid, row in ledger.items():")),
    "plan_ledger": ("services/ingest/reconcile.py - plan(): the ledger rows whose object was not seen", block(REC, "    for sid, row in ledger.items():", end="def decide_bytes(")),
    "decide": ("services/ingest/reconcile.py - decide_bytes(): touch, backfill, queued or reingest", block(REC, "def decide_bytes(", end="def drift_of(")),
    "drift": ("services/ingest/reconcile.py - drift_of(): the night's number", block(REC, "def drift_of(", end="def expired(")),
    "apply_retire": ("services/ingest/reconcile.py - the apply: retire, touch, backfill, reingest", block(REC, '        if act["action"] == "retire":', end="    for tenant in sorted(touched):")),
    "done_line": ("services/ingest/reconcile.py - the last line", block(REC, "    # THE DRIFT LINE", n=3)),
    "reactivate_doc": ("services/ingest/idempotency.py - reactivate(): why it counts", block(IDM, "def reactivate(", n=14)),
    "reactivate_check": ("services/ingest/idempotency.py - reactivate(): the count and the clock, before anything flips", block(IDM, '    claim_snap = db.collection("documents").document(doc_key).get()', end="    n, batch, pending = 0, db.batch(), 0")),
    "job_tf": ("terraform/reconcile.tf - the job: the ingest image, --apply, no platform retries", block("terraform/reconcile.tf", 'resource "google_cloud_run_v2_job" "reconcile"', n=15)),
    "sched_tf": ("terraform/reconcile.tf - 23:30 IST, after the night switch", block("terraform/reconcile.tf", "# 23:30 IST, after documind-off", n=9)),
    "metric_tf": ("terraform/alerts.tf - the drift, read off the last line", block("terraform/alerts.tf", "# The night's number.", end="# Two nights, not one")),
    "policy_tf": ("terraform/alerts.tf - the pager: two nights, not one", block("terraform/alerts.tf", "# Two nights, not one", n=14)),
    "mk_job": ("mk/lifecycle.mk - reconcile, reconcile-job and backfill-current", block(MK, "# the full reconciliation", n=4) + "\n\n" + block(MK, "# once, after the ledger ships", n=4) + "\n\n" + block(MK, "# the nightly job, from the ingest image", end="# the versions view")),
    "smoke_doc": ("smoke/smoke_reindex.py - the six checks", block("smoke/smoke_reindex.py", "Checks:", n=9)),
    "mk_smoke": ("mk/lifecycle.mk - smoke-reindex", block(MK, "# the document lifecycle, smoked", n=6)),
}


fill = filler(EXCERPTS, window)


selftest = subprocess.run([sys.executable, "services/ingest/reconcile.py", "--selftest"], cwd=str(KIT), capture_output=True, text=True)
SELFTEST = selftest.stdout.strip()
assert SELFTEST.startswith("selftest OK"), SELFTEST[:200] + selftest.stderr[-300:]

plan_text = (PLAN / "course-plan-v5-story-2026-09-22.md").read_text(encoding="utf-8")
m5 = re.search(r"^\| 5\.1 \| ([^|]+) \|", plan_text, re.M)   # the course plan keeps the old numbers: its 5.1 is lesson 2.1
NEXT_TITLE = m5.group(1).strip() if m5 else "the first lesson of Module 2"
NEXT_TITLE = re.sub(r"\s*\*\*\(re-scoped[^)]*\)\*\*", "", NEXT_TITLE)
NEXT = f"Module 2, Retrieval, starts with lesson 2.1: {html.escape(NEXT_TITLE)}."
NEXT_FOOTER = f"Next: Module 2 Retrieval, Lesson 2.1 {html.escape(NEXT_TITLE)}."


def subst(text: str) -> str:
    return text.replace("%%DECISION_FLOW%%", pb.part(LESSON, "flow")).replace("%%SELFTEST%%", html.escape(SELFTEST)).replace("%%NEXT_FOOTER%%", NEXT_FOOTER).replace("%%NEXT%%", NEXT)


# ---- the walk simulator: plan() and decide_bytes() as a decision table ----
ROWS = [
    {"name": "acme/hr_policy_2026.md", "bucket": "same", "ledger": "indexed", "bytes": "same", "queued": False},
    {"name": "acme/smoke_note_v1.md", "bucket": "absent", "ledger": "indexed", "bytes": "same", "queued": False},
    {"name": "acme/dpdp_act_2023.pdf", "bucket": "newer", "ledger": "indexed", "bytes": "same", "queued": False},
    {"name": "acme/new_circular.md", "bucket": "same", "ledger": "none", "bytes": "new", "queued": False},
    {"name": "acme/old_policy.md", "bucket": "same", "ledger": "withdrawn", "bytes": "same", "queued": False},
]
JS = """<script>
(function(){
  'use strict';
  var ROWS = %s;
  var root = document.getElementById('walk'); if (!root) return;
  var box = document.getElementById('ws-rows'), sum = document.getElementById('ws-sum');
  var BUCKET = [['same', 'present, the ledger\\'s generation'], ['newer', 'present, a newer generation'], ['absent', 'absent (deleted)']];
  var LEDGER = [['indexed', 'indexed'], ['retired', 'retired'], ['withdrawn', 'withdrawn'], ['none', 'no row']];
  var BYTES = [['same', 'the same hash as the ledger row'], ['known', 'a hash an indexed claim already has'], ['new', 'a hash nobody has seen']];
  function esc(t){ return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  /* plan(): one decision per live object, then the ledger rows whose object was not seen; decide_bytes() after a hash */
  function decide(r){
    if (r.bucket !== 'absent'){
      if (r.queued) return {a: 'queued', why: 'handed to the batch lane; the batch job indexes it, the claim says queued', drift: false, hashed: false};
      if (r.ledger === 'none') return bytes(r, 'not in the ledger');
      if (r.ledger === 'withdrawn') return {a: 'withdrawn', why: 'withdrawn, object kept' + (r.bucket === 'newer' ? ' (a newer generation: make restore re-ingests what the object holds now)' : ''), drift: false, hashed: false};
      if (r.ledger === 'retired') return {a: 'reingest', why: 'retired in the ledger but back in the bucket', drift: true, hashed: false};
      if (r.bucket === 'newer') return bytes(r, 'the generation moved');
      return {a: 'ok', why: 'the object is at the generation the ledger recorded: counted, not printed', drift: false, hashed: false};
    }
    if (r.ledger === 'retired') return {a: '(nothing)', why: 'retired already: the walk skips it', drift: false, hashed: false};
    if (r.ledger === 'withdrawn') return {a: 'withdrawn', why: 'withdrawn, object gone: make restore needs the bytes uploaded again', drift: false, hashed: false};
    if (r.ledger === 'indexed') return {a: 'retire', why: 'gone from the bucket', drift: true, hashed: false};
    return {a: '(nothing)', why: 'no object and no row: nothing to compare', drift: false, hashed: false};
  }
  function bytes(r, why){
    if (r.ledger !== 'none' && r.bytes === 'same') return {a: 'touch', why: why + '; the bytes did not change: record the new generation, nothing to index', drift: false, hashed: true};
    if (r.bytes === 'known') return {a: 'backfill', why: why + '; the version exists under a claim: the ledger just never heard of it', drift: true, hashed: true};
    if (r.ledger === 'none' && r.bytes === 'same') return {a: 'reingest', why: why + '; no row to compare the hash with, and no claim holds it', drift: true, hashed: true};
    return {a: 'reingest', why: why + '; rewritten onto itself: a new generation, the same event, the worker indexes it', drift: true, hashed: true};
  }
  function sel(id, i, opts, val, off){
    return '<label class="ws-l' + (off ? ' off' : '') + '">' + id + '<select data-i="' + i + '" data-k="' + id + '">' + opts.map(function(o){ return '<option value="' + o[0] + '"' + (o[0] === val ? ' selected' : '') + '>' + esc(o[1]) + '</option>'; }).join('') + '</select></label>';
  }
  function render(){
    var summary = {retire: 0, reingest: 0, backfill: 0, touch: 0, ok: 0, withdrawn: 0, queued: 0};
    box.innerHTML = ROWS.map(function(r, i){
      var d = decide(r); if (summary[d.a] !== undefined) summary[d.a]++;
      var needsBytes = d.hashed;
      return '<div class="ws-row"><b>' + esc(r.name) + '</b>' + sel('bucket', i, BUCKET, r.bucket, false) + sel('ledger', i, LEDGER, r.ledger, false) + sel('bytes', i, BYTES, r.bytes, !needsBytes) +
        '<label class="ws-l">queued claim<select data-i="' + i + '" data-k="queued"><option value="no"' + (r.queued ? '' : ' selected') + '>no</option><option value="yes"' + (r.queued ? ' selected' : '') + '>yes, this generation</option></select></label>' +
        '<div class="ws-act">action <em' + (d.drift ? ' class="drift"' : '') + '>' + esc(d.a) + '</em>' + (d.drift ? ' (drift)' : '') + ' &middot; ' + esc(d.why) + '</div></div>';
    }).join('');
    var drift = summary.retire + summary.reingest + summary.backfill;
    sum.textContent = JSON.stringify(Object.assign({event: 'reconcile_done', applied: false}, summary, {drift: drift}));
    box.querySelectorAll('select').forEach(function(s){ s.addEventListener('change', function(){ var r = ROWS[+s.getAttribute('data-i')], k = s.getAttribute('data-k'); r[k] = k === 'queued' ? s.value === 'yes' : s.value; render(); }); });
  }
  render();
})();
</script>
""" % json.dumps(ROWS)

body = "".join([
    subst(fill(pb.part(LESSON, "a"))),
    setup,
    subst(fill(pb.part(LESSON, "b"))),
    subst(fill(pb.part(LESSON, "c"))),
])
finish(LESSON, title, EXTRA_CSS, body, JS)
