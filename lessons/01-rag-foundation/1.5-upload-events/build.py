"""Build lesson 1.5 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts."""
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, PLAN, block, filler, finish, hl, hl_plain, setup_section, window  # noqa: E402,F401

LESSON = "1.5"


title = "<title>Lesson 1.5 Follow upload events, retries, dead-letter handling and the batch lane - one object, one message, one verdict | Netsetos</title>\n"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.dp-controls{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;margin-bottom:10px;}
.dp-l{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;flex:1 1 280px;min-width:0;}
.dp-l select{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.dp-path{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:6px;}
.dp-path li{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 10px;font-size:12.5px;line-height:1.45;color:var(--slate);display:grid;grid-template-columns:28px 1fr;gap:8px;align-items:start;min-width:0;}
.dp-path li b{font-family:var(--mono);font-size:var(--kicker-size);color:var(--teal);}
.dp-path li.end{border:2px solid var(--teal);background:var(--teal-light);color:var(--navy);}
.dp-path li.bad{border:2px solid #d97706;background:#fffbeb;color:var(--navy);}
.dp-clock{margin-top:10px;}
.dp-clock table{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:var(--kicker-size);color:var(--navy);}
.dp-clock th,.dp-clock td{text-align:left;padding:4px 6px;border-bottom:1px solid var(--border);}
.dp-clock th{color:var(--slate);font-weight:500;}
.dp-clock tr.dlq td{color:#92400e;font-weight:700;}
.dp-clock .dp-note{font-size:var(--small-size);color:var(--slate);margin:6px 0 0;}
@media (prefers-reduced-motion: reduce){.dp-path li{transition:none;}}
"""

setup = setup_section()



ING = "services/ingest/main.py"
IDM = "services/ingest/idempotency.py"
TF = "terraform/eventarc.tf"
EXCERPTS = {
    "tf_notification": ("terraform/eventarc.tf - the topics, the grant, and the bucket notification",
                        block(TF, 'resource "google_pubsub_topic" "ingest" ', end="locals {")),
    "tf_subscription": ("terraform/eventarc.tf - the push subscription: the token, the policy, the ceiling",
                        block(TF, 'resource "google_pubsub_subscription" "ingest_push" ', end='resource "google_pubsub_subscription_iam_member" "dlq_subscriber"')),
    "tf_dlq_sub": ("terraform/eventarc.tf - where the dead letters are read from", block(TF, "# Somewhere to read the poison from.", n=5)),
    "push_head": ("services/ingest/main.py - push(): the envelope, the contract, and the 400", block(ING, '@app.post("/")', n=12)),
    "push_branches": ("services/ingest/main.py - push(): the acknowledged verdicts after a lost claim", block(ING, "        elif status_of(_db, doc.doc_key) == \"queued\":", n=9)),
    "push_tail": ("services/ingest/main.py - push(): the only 500", "    try:\n" + block(ING, "        return index_document(doc, msg, content)", n=3)),
    "contract_size": ("services/ingest/contracts.py - IngestMessage: the fields, and what makes a message poison",
                      block("services/ingest/contracts.py", "    model_config = ConfigDict(populate_by_name=True)", end="    @property")),
    "make_poison": ("commands/poison.sh - what make poison runs", block("commands/poison.sh", "#!/usr/bin/env bash", n=200)),
    "make_dlq": ("mk/ingestion.mk - dlq: a peek, not a pull", block("mk/ingestion.mk", "dlq: guard-project", n=2)),
    "lane_decision": ("services/ingest/main.py - index_document(): the decision, before Document AI", block(ING, "            # The batch decision BEFORE Doc AI (12 September 2026)", n=9)),
    "enqueue": ("services/ingest/main.py - _enqueue_batch(): the two records and the hand-off", block(ING, '    _db.collection("ingest_batch").document(doc.doc_key).set({', end="    log.warning(json.dumps({\"event\": \"ingest_queued_batch\"")),
    "take_batch": ("services/ingest/idempotency.py - take_batch(): the job takes a queued claim in a transaction", block(IDM, "def take_batch(", end="def stale_generation(")),
    "batch_tf": ("terraform/batch.tf - the job: the ingest image, a different command, no platform retries", block("terraform/batch.tf", 'resource "google_cloud_run_v2_job" "ingest_batch"', n=14)),
    "claim_doc": ("services/ingest/idempotency.py - claim(): why a transaction", block(IDM, "def claim(", n=9)),
    "deploy_flags": ("commands/lesson-12.5.sh - the worker's own limits: one request per instance, 600 seconds, thirty instances", block("commands/lesson-12.5.sh", "gcloud run deploy documind-ingest \\", n=9)),
    "batch_timeout": ("terraform/batch.tf - two hours, and the claim carries the retry", block("terraform/batch.tf", "      max_retries     = 0", n=2)),
}


fill = filler(EXCERPTS, window)


# ---- the delivery player: one message, one verdict, the subscription's own policy ----
COMMON = [
    ["1", "OBJECT_FINALIZE: Cloud Storage writes the object's record (name, bucket, generation, size, contentType) and publishes it into documind-ingest."],
    ["2", "documind-ingest-push delivers it: one POST to the worker's URL, with an OIDC token minted as documind-ingest-sa. The ack deadline starts: 600 s."],
    ["3", "push() decodes the envelope and parses the record into IngestMessage."],
]
VERDICTS = {
    "indexed": {"steps": [["4", "The claim is taken, the pages counted, the document parsed, chunked, embedded, written staged, swapped, upserted, mirrored, recorded: lesson 1.4's seven records."], ["5", "200 {\"status\": \"indexed\"}: the message is acknowledged and destroyed. Log: ingest_ok."]], "end": "ok"},
    "duplicate": {"steps": [["4", "The bytes hash to a doc_key whose claim is already processing or indexed: nothing is downloaded, nothing written."], ["5", "200 {\"status\": \"duplicate\"}: acknowledged. Log: ingest_duplicate. A 200 is a 200 whatever the body says."]], "end": "ok"},
    "stale": {"steps": [["4", "The ledger row for this object already names a newer generation: an older event, delivered late."], ["5", "200 {\"status\": \"stale\"}: acknowledged, nothing downloaded, nothing changed. Log: ingest_stale_event (lesson 1.7)."]], "end": "ok"},
    "queued": {"steps": [["4", "The PDF's page tree says more than 250 pages: no page goes to Document AI. Two records instead: ingest_batch/{doc_key} and the claim with status queued; the job is started if declared."], ["5", "200 {\"status\": \"queued_batch\"}: acknowledged. Log: ingest_queued_batch. The job indexes it with lane=\"batch\" and no deadline."]], "end": "ok"},
    "poison": {"steps": [["4", "Validation fails: a size of 0, or an object with no tenant prefix, or a name that escapes it. Log: ingest_poison, with the field named."], ["5", "400: not acknowledged. The subscription waits and delivers the same message again. The worker will refuse it the same way every time."]], "end": "bad", "clock": True},
    "failed": {"steps": [["4", "index_document() raises after Document AI, the embedding call or a store failed; the claim is released with the error. Log: ingest_failed."], ["5", "500: not acknowledged. The subscription retries; the next attempt finds the claim failed, takes it back and tries again. A transient cause clears; a permanent one reaches the ceiling."]], "end": "bad", "clock": True},
    "refused": {"steps": [["4", "Cloud Run has no warm instance and answers 429 before the worker sees the request: a corpus upload lands thirty objects against one request per instance."], ["5", "Not acknowledged, no worker log line at all. The subscription retries; by the second or third attempt an instance is up. This is why the ceiling is twelve."]], "end": "bad", "clock": True},
    "timeout": {"steps": [["4", "The worker is still parsing when 600 s pass: the platform kills the request, and the code that releases the claim never runs. The claim stays processing."], ["5", "504: not acknowledged. The retry finds the claim taken and is acknowledged as a duplicate: every delivery reports success and the document is never indexed. The 250-page ceiling exists so that a push request never begins such a document."]], "end": "bad"},
}
CLOCK = [(1, 0), (2, 10), (3, 30), (4, 70), (5, 150), (6, 310), (7, 630), (8, 1230), (9, 1830), (10, 2430), (11, 3030), (12, 3630)]

JS = """<script>
(function(){
  'use strict';
  var COMMON = %s, VERDICTS = %s, CLOCK = %s;
  var root = document.getElementById('delivery'); if (!root) return;
  var sel = document.getElementById('dp-verdict'), path = document.getElementById('dp-path'), clock = document.getElementById('dp-clock');
  function esc(t){ return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  function mmss(s){ return Math.floor(s / 60) + 'm' + ('0' + (s %% 60)).slice(-2) + 's'; }
  function render(){
    var v = VERDICTS[sel.value], steps = COMMON.concat(v.steps);
    path.innerHTML = steps.map(function(s, i){
      var last = i === steps.length - 1, cls = last ? (v.end === 'ok' ? 'end' : 'bad') : '';
      return '<li class="' + cls + '"><b>' + esc(s[0]) + '</b><span>' + esc(s[1]) + '</span></li>';
    }).join('');
    if (v.clock){
      var rows = CLOCK.map(function(c, i){
        var wait = i === 0 ? '-' : mmss(CLOCK[i][1] - CLOCK[i - 1][1]);
        return '<tr' + (i === CLOCK.length - 1 ? ' class="dlq"' : '') + '><td>' + c[0] + '</td><td>' + wait + '</td><td>' + mmss(c[1]) + '</td><td>' + (sel.value === 'refused' ? (i < 2 ? 'refused at the door' : 'an instance is up: the worker answers') : 'the same verdict') + '</td></tr>';
      }).join('');
      clock.innerHTML = '<table><thead><tr><th>attempt</th><th>wait before it</th><th>elapsed</th><th>outcome</th></tr></thead><tbody>' + rows + '</tbody></table>' +
        '<p class="dp-note">After the twelfth failed attempt the message is forwarded to documind-ingest-dlq and ingest-dlq-sub holds it: about an hour after the first. The waits double from the 10 s minimum to the 600 s maximum; Pub/Sub adds jitter, so your gaps are close to these, not equal to them.</p>';
    } else {
      clock.innerHTML = v.end === 'ok' ? '<p class="dp-note">Acknowledged on the first delivery: no clock runs. The message is gone; the records (or the log line) are what remain.</p>'
                                       : '<p class="dp-note">No clock can help here: each retry is acknowledged as a duplicate. The defence is not to start such a request, which is what the page ceiling in step 6 does.</p>';
    }
  }
  sel.addEventListener('change', render);
  render();
})();
</script>
""" % (json.dumps(COMMON), json.dumps(VERDICTS), json.dumps(CLOCK))

body = "".join([
    fill(pb.part(LESSON, "a")),
    setup,
    fill(pb.part(LESSON, "b")),
    fill(pb.part(LESSON, "c")),
])
finish(LESSON, title, EXTRA_CSS, body, JS)
