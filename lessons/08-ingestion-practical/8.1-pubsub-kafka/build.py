"""Build lesson 8.1 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Run the ingest events through Pub/Sub, mapped to Kafka. One upload is traced from the object's generation through the
notice, the push and the acknowledgement to the records and an answer that cites it; the subscription's settings are
read off the kit (five declared in terraform/eventarc.tf, five left to Google); a burst of the kit's corpus is pushed at
a worker squeezed to five instances; and thirteen Pub/Sub settings are set beside Kafka's nearest concepts.

Computed here, offline, from the kit:
  - every name and number on the page: eventarc.tf's topic, notice, subscription and policy; gchat.tf's other push
    subscription (the retention eventarc.tf leaves out, and the never-expire both set); lesson-12.5.sh's worker limits; what main.py's push()
    reads of the envelope and the verdicts it answers; the burst's objects by evals/upload.sh's own rule;
  - the note's chunks, by the worker's own _windows() and _chunk() lifted out of main.py with ast and run here (and
    held equal to shared/documind_corpus.py's twin), so the page states the count the lane will print;
  - make ingest-corpus's own lines, from upload.sh's echo statements and the corpus on disk;
  - the trace panel in step 1: the hops are data built here from those facts; node runs the panel's script against
    the same data before the page is written;
  - the run list's rupees, from shared/prices.py, rag-api's config.py and lessons/00-setup/standing_cost.py.
Google's documented behaviour, which the kit does not hold (defaults, limits, delivery rules), is the dated GOOGLE table
below, each fact with its page. Kafka's facts are its general model and its documented defaults, stated in KAFKA.
Recorded from the author's lane with pb.recorded(): every cell that reads the lane (RUN_LIST.md says how). The seven
Python cells that read the lane are also run here against stand-in Google APIs, so their code is tested before a lane
runs them; their stand-in output is asserted, never shown.

    python pagekit/build.py 8.1
"""
import ast
import hashlib
import html
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, MANIFEST, block, filler, finish, setup_section, window  # noqa: E402

sys.path.insert(0, str(HERE.parents[1] / "00-setup"))
import standing_cost as sc  # noqa: E402  the lane's hourly bill, shared with 0.1, 0.3, 0.4 and 8.3

LESSON = "8.1"
title = ("<title>Lesson 8.1 Run the ingest events through Pub/Sub, mapped to Kafka - one upload followed from the bucket "
         "to a cited answer, one burst squeezed, every setting set beside Kafka's | Netsetos</title>\n")
PROJ = "documind-ai-YOUR-ID"
TENANT = "acme"
NOTE_NAME = "pubsub_trace_note.md"
OBJECT = f"{TENANT}/{NOTE_NAME}"
SQUEEZE = 5                                  # the cohort plan's ceiling for the burst (plan section 7, wave 4)
QUESTION = "After 9 pm, where do couriers deliver at the Bhiwandi depot, and who signs for the parcel?"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
/* the trace panel: eight hops as buttons, one card with the lane's column and Kafka's */
.tr-l{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;margin:0 0 10px;}
.tr-l select{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.tr-hops{list-style:none;margin:0 0 10px;padding:0;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px;}
.tr-hops li{margin:0;}
.tr-hop{width:100%;font:inherit;font-size:12.5px;line-height:1.3;text-align:left;color:var(--navy);background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px;min-height:max(44px,var(--touch));cursor:pointer;-webkit-tap-highlight-color:transparent;overflow-wrap:anywhere;}
.tr-hop b{font-family:var(--mono);color:var(--teal);margin-right:4px;}
.tr-hop[aria-pressed="true"]{border:2px solid var(--teal);background:var(--teal-light);}
.tr-hop.bad b{color:#b45309;}
.tr-hop.bad[aria-pressed="true"]{border-color:#d97706;background:#fffbeb;}
.tr-hop:active{transform:scale(.98);}
.tr-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:10px 12px;min-width:0;}
.tr-card h5{font-size:var(--small-size);color:var(--navy);margin:0 0 6px;}
.tr-cols{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;}
.tr-col{font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.tr-col > b{display:block;font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:.8px;text-transform:uppercase;color:var(--teal-dark);margin-bottom:4px;}
.tr-col.kafka > b{color:#0e7490;}
.tr-col p{font-size:12.5px;margin:0 0 6px;}
.tr-num{border-left:3px solid var(--teal);padding-left:8px;}
.tr-col.kafka .tr-num{border-left-color:#0891b2;}
@media (hover:hover) and (pointer:fine){.tr-hop:hover{border-color:var(--teal);}}
@media (max-width: 640px){.tr-hops{grid-template-columns:repeat(2,minmax(0,1fr));}.tr-cols{grid-template-columns:minmax(0,1fr);}}
"""

# ------------------------------------------------------------------ the shared setup section, with this lesson's reason
setup = setup_section()
for old, new in (
        ("This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end.",
         "This lesson's answers, in steps 3 and 6, must come from the kit's own rows, where the worker writes the note it "
         "traces, so point acme at them for the duration and put the pin back at the end."),):
    assert setup.count(old) == 1, old
    setup = setup.replace(old, new)
assert "step 3 makes the difference visible." in setup          # this page's step 3: the operator uploads, the person reads


# ------------------------------------------------------------------ the kit's facts
def read(rel: str) -> str:
    """One kit file's text."""
    return (KIT / rel).read_text(encoding="utf-8")


def one(pattern: str, text: str, flags: int = 0) -> str:
    """The one match of a pattern's first group: a kit fact the page states, or the build stops."""
    found = re.findall(pattern, text, flags)
    assert len(found) == 1, (pattern, found)
    return found[0]


def tf_block(text: str, head: str) -> str:
    """One Terraform resource, from its head line to the first brace alone at the start of a line."""
    i = text.index(head)
    return text[i:text.index("\n}\n", i) + 2]


EV_REL, GC_REL, L125, ING = "terraform/eventarc.tf", "terraform/gchat.tf", "commands/lesson-12.5.sh", "services/ingest/main.py"
EV, GC, SA, VARS = read(EV_REL), read(GC_REL), read("terraform/sa.tf"), read("terraform/variables.tf")
MAKE = read("Makefile") + "".join("\n" + p.read_text(encoding="utf-8") for p in sorted((KIT / "mk").glob("*.mk")))
TOPIC = one(r'resource "google_pubsub_topic" "ingest" \{ name = "([\w-]+)" \}', EV)
DLQ_TOPIC = one(r'resource "google_pubsub_topic" "ingest_dlq" \{ name = "([\w-]+)" \}', EV)
NOTIFY = tf_block(EV, 'resource "google_storage_notification" "uploads" {')
EVENT = one(r'event_types\s+= \["(\w+)"\]', NOTIFY)
PAYLOAD = one(r'payload_format = "(\w+)"', NOTIFY)
assert "topic          = google_pubsub_topic.ingest.id" in NOTIFY and "bucket         = google_storage_bucket.uploads.name" in NOTIFY
assert 'name                        = "${var.project_id}-uploads"' in read("terraform/storage.tf")
assert "versioning { enabled = true }" in tf_block(read("terraform/storage.tf"), 'resource "google_storage_bucket" "uploads" {')
SUB_TF = tf_block(EV, 'resource "google_pubsub_subscription" "ingest_push" {')
SUB = one(r'^  name  = "([\w-]+)"$', SUB_TF, re.M)
DLQ_SUB_TF = tf_block(EV, 'resource "google_pubsub_subscription" "ingest_dlq_sub" {')
DLQ_SUB = one(r'name  = "([\w-]+)"', DLQ_SUB_TF)
assert DLQ_SUB_TF.splitlines()[1:-1] == ['  name  = "ingest-dlq-sub"', "  topic = google_pubsub_topic.ingest_dlq.name",
                                         "  # Never expires (13 October 2026), as ingest_push: a quiet lane's dead letters must still have a reader to land on.",
                                         "  expiration_policy {", '    ttl = ""', "  }"]   # a pull subscription that never expires
ACK = int(one(r"ack_deadline_seconds = (\d+)", SUB_TF))
MIN_BO, MAX_BO = (int(one(rf'{w}_backoff = "(\d+)s"', SUB_TF)) for w in ("minimum", "maximum"))
ATTEMPTS = int(one(r"max_delivery_attempts = (\d+)", SUB_TF))
assert "dead_letter_topic     = google_pubsub_topic.ingest_dlq.id" in SUB_TF
assert "push_endpoint = local.ingest_url" in SUB_TF and "service_account_email = google_service_account.ingest.email" in SUB_TF
assert one(r'ingest_url = "([^"]+)"', EV) == "https://documind-ingest-${data.google_project.current.number}.${var.region}.run.app"
INGEST_SA = one(r'account_id\s+= "([\w-]+)"', tf_block(SA, 'resource "google_service_account" "ingest" {'))
PUSH_URL = "https://documind-ingest-NUMBER.asia-south1.run.app"
SA_EMAIL = f"{INGEST_SA}@{PROJ}.iam.gserviceaccount.com"
# what the subscription declares, and what it leaves to Google: the Terraform arguments, by name
TF_ARGS = ["push_config", "ack_deadline_seconds", "retry_policy", "dead_letter_policy", "message_retention_duration",
           "retain_acked_messages", "expiration_policy", "enable_message_ordering", "enable_exactly_once_delivery", "filter"]
DECLARED = {arg: bool(re.search(rf"^\s*{arg}\b", SUB_TF, re.M)) for arg in TF_ARGS}
assert [a for a in TF_ARGS if DECLARED[a]] == TF_ARGS[:4] + ["expiration_policy"], DECLARED   # never expire: 13 October 2026
N_DECLARED, N_DEFAULTED = sum(DECLARED.values()), len(TF_ARGS) - sum(DECLARED.values())
TOPIC_TF = one(r'(resource "google_pubsub_topic" "ingest" \{[^}]*\})', EV)
assert "message_retention_duration" not in TOPIC_TF and "message_storage_policy" not in TOPIC_TF
# the kit's other push subscription sets the retention this one leaves out, and the same never-expire, with its reasons
GC_SUB = tf_block(GC, 'resource "google_pubsub_subscription" "gchat_push" {')
assert 'expiration_policy {\n    ttl = ""\n  }' in GC_SUB and 'message_retention_duration = "3600s"' in GC_SUB
assert "allowed_persistence_regions = [var.india_region]" in tf_block(GC, 'resource "google_pubsub_topic" "gchat_work" {')
# the alerts on this path: one on the dead-letter subscription, and (13 October 2026) one on the push subscription's
# oldest unacknowledged message
ALERTS = read("terraform/alerts.tf")
assert "google_pubsub_subscription.ingest_dlq_sub.name" in ALERTS and ALERTS.count("google_pubsub_subscription.ingest_push.name") == 1
BACKLOG_TF = tf_block(ALERTS, 'resource "google_monitoring_alert_policy" "ingest_backlog" {')
assert "google_pubsub_subscription.ingest_push.name" in BACKLOG_TF and "subscription/oldest_unacked_message_age" in BACKLOG_TF
BACKLOG_S, BACKLOG_FOR = int(one(r"threshold_value = (\d+)", BACKLOG_TF)), int(one(r'duration        = "(\d+)s"', BACKLOG_TF))
assert BACKLOG_S % 60 == 0 and BACKLOG_FOR % 60 == 0 and BACKLOG_S < 3600, (BACKLOG_S, BACKLOG_FOR)   # it pages before the DLQ would
EVENTS_RE = one(r'jsonPayload\.event=~"\^ingest_\(([a-z_|]+)\)\$"', tf_block(ALERTS, 'resource "google_logging_metric" "ingest_events" {'))
COUNTED = EVENTS_RE.split("|")
assert COUNTED == ["ok", "superseded", "reactivated", "stale_event", "failed", "queued_batch", "poison", "withdrawn",
                   "already_current", "claim_retaken"], COUNTED                   # widened on 13 October 2026
assert "duplicate" not in COUNTED and "claim_held" not in COUNTED              # a delivery the claim turns away stays out
EMBEDDED_TF = tf_block(ALERTS, 'resource "google_logging_metric" "ingest_embedded" {')
assert 'jsonPayload.event="ingest_ok"' in EMBEDDED_TF and 'value_extractor = "EXTRACT(jsonPayload.embedded)"' in EMBEDDED_TF
assert 'key         = "event"' in tf_block(ALERTS, 'resource "google_logging_metric" "ingest_events" {')
API_MAIN = read("services/rag-api/main.py")       # the answer's usage row (step 6): event "query", logged on documind-api
assert 'ans.latency_ms, ans.answerable, ans.confidence, "query",' in API_MAIN and 'return {"event": surface, "tenant": req.tenant_id,' in API_MAIN

# the worker that receives: lesson-12.5.sh's DEPLOY block
DEPLOY = read(L125).split("gcloud run deploy documind-ingest \\", 1)[1].split("gcloud run services add-iam-policy-binding", 1)[0]
CONC = int(one(r"--concurrency=(\d+)", DEPLOY))
MAXI = int(one(r"--max-instances=(\d+)", DEPLOY))
MINI = int(one(r"--min-instances=(\d+)", DEPLOY))
TIMEOUT = int(one(r"--timeout=(\d+)", DEPLOY))
assert "--ingress=internal" in DEPLOY and "--no-allow-unauthenticated" in DEPLOY and f"--service-account={INGEST_SA}@" in DEPLOY
assert "--role=roles/run.invoker" in read(L125) and (CONC, MAXI, MINI, TIMEOUT) == (1, 30, 0, 600)
IN_FLIGHT = CONC * MAXI
assert TIMEOUT == ACK and SQUEEZE < MAXI
assert "MANAGED_MIRROR  ?= both" in MAKE and re.search(r'policies = \[\("acme", "any"\)', read("commands/lane.py"))
RETENTION_DAYS = int(one(r'variable "retention_days" \{\s*type\s+= number\s*default = (\d+)', VARS, re.S))

# the handler: what push() reads of the envelope, and what it answers
MAIN = read(ING)
PUSH = MAIN.split('@app.post("/")', 1)[1].split("\ndef index_document(", 1)[0]
INDEX = MAIN.split("\ndef index_document(", 1)[1]
assert re.findall(r'envelope\[[^\]]+\](?:\[[^\]]+\])*', MAIN) == ['envelope["message"]["data"]']
for unread in ("messageId", "message_id", "deliveryAttempt", "delivery_attempt", "publishTime", "attributes", "orderingKey"):
    assert unread not in MAIN, unread                          # the handler reads one field of the envelope, and only one
VERDICTS = sorted(set(re.findall(r'return \{"status": "(\w+)"', PUSH)) | set(re.findall(r'return \{"status": "(\w+)"', INDEX)))
assert VERDICTS == ["already_current", "batch_processing", "duplicate", "indexed", "queued_batch", "reactivated", "stale",
                    "withdrawn"], VERDICTS                                # batch_processing: the claim's lease, 13 October 2026
assert 'raise HTTPException(409, f"claim {lease[\'verdict\']}: Pub/Sub delivers it again")' in PUSH     # the lease's nack
assert re.findall(r"HTTPException\((\d+)", PUSH) == ["400", "409", "500"]      # the poison, the held claim, the failed pipeline
assert 'blob = _gcs.bucket(msg.bucket).blob(msg.name, generation=int(msg.generation))' in PUSH
assert PUSH.index("stale_generation(") < PUSH.index(".blob(msg.name, generation=") < PUSH.index("if not claim(")
assert 'if content_type.startswith("text/"):' in MAIN                       # a .md goes up as text: no Document AI
assert "logging.googleapis.com/trace" not in MAIN and 'format="%(message)s", stream=sys.stdout' in MAIN   # plain stdout lines, no trace
UI_DOCS = read("services/frontend/documents.py")
assert 'blob = BUCKET.blob(f"{tenant_id}/{name}")' in UI_DOCS and '"md": "text/plain"' in UI_DOCS

# ------------------------------------------------------------------ the note this page traces, cut by the worker's own code
NOTE_BODY = """# Night gate note

A note for lesson 8.1's trace, uploaded at __WHEN__. Every fact in it is invented.

## NG-01 - The night gate

After 9 pm, couriers deliver to gate 3 of the Bhiwandi depot. The parcel is signed for at the security desk, and
the duty officer enters it in the green register before the gate is closed.

## NG-02 - A refused parcel

A parcel refused at gate 3 goes back to the hub and comes again the next evening, at most three times. After the
third refusal it waits at the hub for the sender to collect.
"""
SAMPLE_WHEN = "2026-11-17T10:00:00Z"               # the cell writes the time it runs: the length is the same, the count too
sys.path.insert(0, str(KIT))
from shared import documind_corpus as dc  # noqa: E402  the notebooks' twin of the worker's chunker (standard library only)
NS = {"re": re, "hashlib": hashlib}


def lift(rel: str, wanted: set) -> None:
    """Run the named top-level assignments and functions of one kit file into NS, verbatim, and nothing else: the
    worker's chunker without the worker's imports (Firestore, Cloud Storage, google-genai, pydantic)."""
    for node in ast.parse(read(rel)).body:
        names = {t.id for t in getattr(node, "targets", []) if isinstance(t, ast.Name)} | \
                {e.id for t in getattr(node, "targets", []) if isinstance(t, ast.Tuple) for e in t.elts}
        if (isinstance(node, ast.Assign) and names & wanted) or (isinstance(node, ast.FunctionDef) and node.name in wanted):
            exec(compile(ast.Module([node], []), rel, "exec"), NS)


lift("services/ingest/contracts.py", {"_WS", "chunk_hash"})
lift(ING, {"CHUNK_CHARS", "CHUNK_OVERLAP", "_SECTION", "_CODE", "_windows", "_chunk"})
assert {"chunk_hash", "_windows", "_chunk", "CHUNK_CHARS", "_SECTION", "_CODE"} <= set(NS)
NOTE_CHUNKS = NS["_chunk"](NOTE_BODY.replace("__WHEN__", SAMPLE_WHEN))
LOCATORS = [c["locator"] for c in NOTE_CHUNKS]
N_CHUNKS = len(NOTE_CHUNKS)
TWIN = dc.chunk_document({"text": NOTE_BODY.replace("__WHEN__", SAMPLE_WHEN), "source_uri": f"gs://{PROJ}-uploads/{OBJECT}",
                          "doc_type": "unknown", "slug": NOTE_NAME[:-3]}, TENANT)
assert [c["text"] for c in TWIN] == [c["text"] for c in NOTE_CHUNKS] and LOCATORS == ["preamble", "NG-01", "NG-02"]
CITE_POS = LOCATORS.index("NG-01")                  # the chunk the question finds: doc.chunk_id(i) names its position
assert "gate 3" in NOTE_CHUNKS[CITE_POS]["text"] and "security desk" in NOTE_CHUNKS[CITE_POS]["text"]
assert not re.search(r"effective[ _-]?(?:from|date)?\s*[:=]", NOTE_BODY, re.I)   # the note declares no date
assert "@" not in NOTE_BODY                          # no email in the note: the DLP scan finds nothing to record

# ------------------------------------------------------------------ the burst: make ingest-corpus, by upload.sh's own rule
UPLOAD = read("evals/upload.sh")
for line in ('    if [[ "${f}" == *.md && ( -f "${f%.md}.pdf" || -f "${f%.md}.mp4" ) ]]; then',
             '    if [[ "${f}" == *.segments.json ]]; then', '  gcloud storage cp "${files[@]}" "${BUCKET}/${tenant}/"'):
    assert line in UPLOAD, line
assert "ingest-corpus: guard-project\n\tPROJECT_ID=$(PROJECT) bash evals/upload.sh" in MAKE


def clone_files(tenant_dir: Path) -> set:
    """A tenant's corpus files as a fresh clone has them: lesson 7.5's town hall video and the segments beside it are
    gitignored, so a checkout where someone made them must not change the page."""
    return {f.name for f in tenant_dir.iterdir() if f.is_file() and f.suffix != ".mp4" and not f.name.endswith(".segments.json")}


def would_upload(tenant_dir: Path) -> list:
    """upload.sh's rule for one tenant: every file, but a .md whose .pdf or .mp4 twin exists, and a .segments.json."""
    files = clone_files(tenant_dir)
    return [n for n in sorted(files) if not (n.endswith(".md") and (n[:-3] + ".pdf" in files or n[:-3] + ".mp4" in files))]


CORPUS = {d.name: would_upload(d) for d in sorted((KIT / "evals" / "corpus").iterdir()) if d.is_dir()}
N_OBJECTS = sum(len(v) for v in CORPUS.values())
assert list(CORPUS) == ["acme", "globex", "zeta"] and N_OBJECTS == 31, {k: len(v) for k, v in CORPUS.items()}
assert "townhall_2026_q1.md" in CORPUS["acme"]       # a clone without lesson 7.5's video; with it, the .mp4 goes instead
ROUNDS_SQ, ROUNDS_FULL = math.ceil(N_OBJECTS / (CONC * SQUEEZE)), math.ceil(N_OBJECTS / IN_FLIGHT)
OWNER_NOTES = [m["note"] for m in json.loads(read("evals/manifest.json")) if m.get("supplied_by") == "owner"]
assert len(OWNER_NOTES) == 2 and all('"' not in n for n in OWNER_NOTES)
ECHO = ['echo "project : ${PROJECT_ID}"', 'echo "bucket  : ${BUCKET}"',
        "echo \"Uploaded. The bucket's notification now pushes one message per object to the worker;\"",
        'echo "if nothing lands, peek at the dead letters without acknowledging them (a pull --auto-ack would delete them):"',
        'echo "  make dlq"',
        'echo "The two binary assets are NOT here - manifest.json lists what to supply:"',
        '  echo "==> ${tenant} (${#files[@]} files) -> ${BUCKET}/${tenant}/"', '    echo "    $(basename "${f}")"']
for line in ECHO:
    assert line in UPLOAD, line
BUCKET = f"gs://{PROJ}-uploads"
CORPUS_OUT = "\n".join(
    ["BURST_SINCE=YYYY-MM-DDTHH:MM:SSZ", f"PROJECT_ID={PROJ} bash evals/upload.sh", f"project : {PROJ}", f"bucket  : {BUCKET}", ""]
    + [line for t, names in CORPUS.items()
       for line in [f"==> {t} ({len(names)} files) -> {BUCKET}/{t}/"] + [f"    {n}" for n in names] + ["..."]]
    + ["", "Uploaded. Eventarc should now be enqueuing one ingest job per object;", "watch the DLQ if nothing lands:",
       "  gcloud pubsub subscriptions pull ingest-dlq-sub --auto-ack --limit=10", "",
       "The two binary assets are NOT here - manifest.json lists what to supply:"]
    + [f"  - {n}" for n in OWNER_NOTES])

# ------------------------------------------------------------------ Google's documented behaviour, read on 12 October 2026
READ_ON = "12 October 2026"
GOOGLE = {   # each: the page it is read from, and what the page says (the build states nothing else about Pub/Sub's defaults)
    "props": "https://docs.cloud.google.com/pubsub/docs/subscription-properties",
    # ack deadline: "Default value = 10 seconds", "Maximum value = 600 seconds"; message retention: "Default value = 7
    # days", "Minimum value = 10 minutes", "Maximum value = 31 days"; expiration: "Default value = 31 days", "Examples of
    # subscriber activities include open connections, active pulls, or successful pushes.", "never expire"; retry: "By
    # default, the retry policy for a subscription is set to use Retry immediately.", "The longest backoff duration that
    # you can specify is 600 seconds."; dead letter: "The default value is 5 delivery attempts.", "between 5 and 100";
    # ordering: "For the messages to be received in order, the publisher must set the ordering key."; filter: "You can
    # filter messages by their attributes, but not by the data in the message.", "Filters cannot be changed or removed
    # after you apply them."
    "push": "https://docs.cloud.google.com/pubsub/docs/push",
    # ack: 102, 200, 201, 202, 204; "To send a negative acknowledgment for the message, return any other status code.";
    # "Pub/Sub adjusts the number of concurrent push requests using a slow-start algorithm."; "The push window increases
    # on any successful delivery and decreases on any failure."; "The system starts with a small single-digit window size."
    "eod": "https://docs.cloud.google.com/pubsub/docs/exactly-once-delivery",
    # "Push and export subscriptions don't support exactly-once delivery."
    "ordering": "https://docs.cloud.google.com/pubsub/docs/ordering",
    # "You can't change the message ordering property after you create a subscription."; "For a push subscription,
    # Pub/Sub supports only one outstanding message for each ordering key at a time."
    "replay": "https://docs.cloud.google.com/pubsub/docs/replay-overview",
    # to replay acknowledged messages "you must configure message retention on the topic, or configure the subscription
    # to retain acknowledged messages."
    "topic": "https://docs.cloud.google.com/pubsub/docs/topic-properties",
    # topic message retention: "Default = Not enabled", 10 minutes to 31 days
    "retry": "https://docs.cloud.google.com/pubsub/docs/subscription-retry-policy",
    # "Exponential backoff is only applied per-message, rather than to all the messages in a subscription (global)."
    "dlq": "https://docs.cloud.google.com/pubsub/docs/handling-failures",
    # "The maximum number of delivery attempts is approximate."
    "overview": "https://docs.cloud.google.com/pubsub/docs/subscription-overview",
    # "Only messages published to the topic after the subscription is created are available to subscriber clients.";
    # "By default, Pub/Sub offers at-least-once delivery with no ordering guarantees on all subscription types."
    "gcs": "https://docs.cloud.google.com/storage/docs/pubsub-notifications",
    # "Once started, Cloud Storage guarantees at-least-once delivery to Pub/Sub."; no SLA for delivery time, "typically
    # delivered within seconds"; notifications are not guaranteed to be published in order; use the object's generation
    # and metageneration as preconditions; OBJECT_FINALIZE: "Sent when a new object (or a new generation of an existing
    # object) is successfully created in the bucket."; attributes objectGeneration, overwroteGeneration
    "run_scaling": "https://docs.cloud.google.com/run/docs/about-instance-autoscaling",
    # pending requests wait "for up to 3.5 times average startup time ... or 10 seconds, whichever is greater", then
    # "the request fails with a 429 error code"
    "run_max": "https://docs.cloud.google.com/run/docs/configuring/max-instances",
    # "this maximum setting can be exceeded for a brief period due to circumstances such as traffic spikes"; Google
    # recommends service-level maximum instances; --max-instances is revision-level and deploys a new revision
    "run_logging": "https://docs.cloud.google.com/run/docs/logging",
    # "Container logs are not automatically correlated to request logs unless you use a Cloud Logging client library."
    "metrics": "https://docs.cloud.google.com/monitoring/api/metrics_gcp_p_z",
    # subscription/num_undelivered_messages (GAUGE), oldest_unacked_message_age (GAUGE, s), push_request_count (DELTA;
    # response_class: ack, deadline_exceeded, internal, invalid, remote_server_4xx, remote_server_5xx, unreachable),
    # dead_letter_message_count (DELTA); "Sampled every 60 seconds. After sampling, data is not visible for up to 120
    # seconds."; run.googleapis.com/container/instance_count (GAUGE, label state: active or idle)
}
G = {"ack_default": 10, "ack_max": 600, "retention_days": 7, "retention_min": "10 minutes", "retention_max_days": 31,
     "expiration_days": 31, "dlq_default": 5, "dlq_min": 5, "dlq_max": 100, "backoff_max": 600,
     "ack_codes": "102, 200, 201, 202 or 204", "sample_s": 60, "visible_s": 120, "pending_s": 10, "pending_x": "3.5"}
DAY = 86_400
assert ACK == G["ack_max"] and MAX_BO == G["backoff_max"] and G["dlq_min"] <= ATTEMPTS <= G["dlq_max"]
assert ATTEMPTS > G["dlq_default"] and TIMEOUT == G["ack_max"]
DLQ_BOUND_MIN = (ATTEMPTS - 1) * MAX_BO // 60       # at most eleven waits of at most 600 s between twelve attempts
# Kafka: its general model, and two of its documented defaults
KAFKA = {"retention_hours": 168, "max_poll_ms": 300_000}
assert KAFKA["retention_hours"] == 24 * G["retention_days"]          # Kafka's default retention is Pub/Sub's, seven days

# ------------------------------------------------------------------ verbatim kit excerpts
TF_AL, RC = "terraform/alerts.tf", "services/ingest/reconcile.py"
EXCERPTS = {
    "ingest_one": ("commands/ingest-one.sh - what make ingest-one runs: one copy, then the worker's ingest_ok line",
                   block("commands/ingest-one.sh", "SINCE=$(date -u +%Y-%m-%dT%H:%M:%SZ); NAME=$(basename", n=6)),
    "ui_upload": ("services/frontend/documents.py - upload_document(): the UI's uploader writes to the same prefix",
                  block("services/frontend/documents.py", '    blob = BUCKET.blob(f"{tenant_id}/{name}")', n=3)),
    "notification": ("terraform/eventarc.tf - the notice: one event type, one format, one topic",
                     block(EV_REL, 'resource "google_storage_notification" "uploads" {', n=7)),
    "guard": ("services/ingest/main.py - push(): the generation guard, then the bytes of that generation",
              block(ING, "    # THE GENERATION GUARD (12 September 2026).", n=6) + "\n...\n"
              + block(ING, "    blob = _gcs.bucket(msg.bucket).blob(msg.name, generation=int(msg.generation))", n=1)),
    "subscription": ("terraform/eventarc.tf - the push subscription: five settings, and nothing else",
                     block(EV_REL, 'resource "google_pubsub_subscription" "ingest_push" {',
                           end='resource "google_pubsub_subscription_iam_member" "dlq_subscriber"')),
    "gchat_sub": ("terraform/gchat.tf - the kit's other push subscription: the retention this one leaves out, and the same never-expire",
                  block(GC_REL, "  # By default a subscription with no activity for 31 days expires", n=7)),
    "deploy": ("commands/lesson-12.5.sh - the worker: one request an instance, thirty instances, 600 seconds",
               block(L125, "# The ingest worker. Reached by nothing but the push subscription", n=6) + "\n...\n"
               + block(L125, "gcloud run deploy documind-ingest \\", n=8)),
    "push_parse": ("services/ingest/main.py - push(): the one field of the envelope it reads",
                   block(ING, '@app.post("/")', n=6)),
    "doc_key": ("services/ingest/contracts.py - DocumentContract: the key is the content, never the message id",
                block("services/ingest/contracts.py", "    doc_key is the IDEMPOTENCY KEY and it is derived from CONTENT, never from", n=5)),
    "duplicate": ("services/ingest/main.py - push(): a second delivery of the same bytes is a 200",
                  block(ING, "            # Already done by an earlier delivery, or by an earlier upload of the", n=4)),
    "upload_rule": ("evals/upload.sh - which files go up, and how",
                    block("evals/upload.sh", '    if [[ "${f}" == *.md && ( -f "${f%.md}.pdf" || -f "${f%.md}.mp4" ) ]]; then', n=13)),
    "events_metric": ("terraform/alerts.tf - documind/ingest_events: the worker's verdicts, and not the duplicate",
                      block(TF_AL, 'resource "google_logging_metric" "ingest_events" {', n=8)),
    "rewrite": ("services/ingest/reconcile.py - the walk's replay: the object rewritten onto itself",
                block(RC, '        elif act["action"] == "reingest":', n=5)),
}
E = {k: v[1] for k, v in EXCERPTS.items()}
assert E["ingest_one"].endswith("done") and 'jsonPayload.event=\\"ingest_ok\\"' in E["ingest_one"]
assert E["ui_upload"].endswith("rewind=True)")
assert E["notification"].endswith("}") and f'event_types    = ["{EVENT}"]' in E["notification"]
assert "THE GENERATION GUARD" in E["guard"] and E["guard"].endswith("generation=int(msg.generation))")
assert E["subscription"].rstrip().endswith("}") and f"max_delivery_attempts = {ATTEMPTS}" in E["subscription"]
assert E["gchat_sub"].endswith('"3600s" # one hour; the minimum allowed is from memory') and 'ttl = ""' in E["gchat_sub"]
assert "Thirty instances, so a corpus" in E["deploy"] and E["deploy"].endswith("--execution-environment=gen2 \\")
assert E["push_parse"].endswith("msg = IngestMessage.model_validate_json(raw)")
assert E["doc_key"].rstrip().endswith("A content hash catches both.")
assert E["duplicate"].endswith('return {"status": "duplicate", "doc_key": doc.doc_key}')
assert E["upload_rule"].endswith('gcloud storage cp "${files[@]}" "${BUCKET}/${tenant}/"')
assert E["events_metric"].endswith('jsonPayload.event=~"^ingest_(' + "|".join(COUNTED) + ')$"\n  EOT')
assert E["rewrite"].endswith('print(json.dumps({"event": "reconcile_reingest", "gcs_uri": uri}))') and "blob.rewrite(blob)" in E["rewrite"]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the cells
def heredoc(code: str, prefix: str = "") -> str:
    """A Python cell as the page prints it: a heredoc that pastes into bash."""
    return f"{prefix}python - <<'PY'\n{code}\nPY"


API_ONLY = r'''TOKEN = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()


def api(url, body=None):
    """GET one Google API URL, or POST it a JSON body, with the operator's token; returns the parsed JSON."""
    req = urllib.request.Request(url, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=60))'''
API_HELPERS = API_ONLY + r'''


def when(stamp):
    """An RFC 3339 time from a Google API as a UTC datetime (nanoseconds cut to microseconds)."""
    head, _, frac = stamp.rstrip("Z").partition(".")
    return dt.datetime.fromisoformat(f"{head}.{(frac + '000000')[:6]}+00:00")'''

PY_TRACE = r'''import datetime as dt, json, os, subprocess, urllib.parse, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P, NAME = os.environ["PROJECT"], "__OBJECT__"
__HELPERS__


obj = api(f"https://storage.googleapis.com/storage/v1/b/{P}-uploads/o/{urllib.parse.quote(NAME, safe='')}")
t0, gen = when(obj["timeCreated"]), str(obj["generation"])
print(f"gs://{P}-uploads/{NAME}: generation {gen}, {obj['size']} bytes, {obj['contentType']}, created {obj['timeCreated']}")
iso = lambda t: t.strftime("%Y-%m-%dT%H:%M:%SZ")
first, last = iso(t0 - dt.timedelta(seconds=5)), iso(t0 + dt.timedelta(minutes=10))
flt = (f'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-ingest" '
       f'AND timestamp>="{first}" AND timestamp<="{last}"')
seen = api("https://logging.googleapis.com/v2/entries:list",
           {"resourceNames": [f"projects/{P}"], "filter": flt, "orderBy": "timestamp asc", "pageSize": 500}).get("entries", [])
ok = [e for e in seen if (e.get("jsonPayload") or {}).get("event") == "ingest_ok"
      and str(e["jsonPayload"].get("generation")) == gen]
key = ok[0]["jsonPayload"]["doc_key"] if ok else None
print("seconds after the object was created:")
for e in seen:
    h, j, at = e.get("httpRequest") or {}, e.get("jsonPayload") or {}, (when(e["timestamp"]) - t0).total_seconds()
    if h.get("requestMethod") == "POST":
        print(f"{at:7.1f}  POST {h.get('status')}, latency {float(str(h.get('latency', '0s')).rstrip('s') or 0):.3f} s (Cloud Run's request log)")
    elif key and (j.get("doc_key") == key or (j.get("event") == "ledger_fingerprint" and j.get("tenant") == "acme")):
        rest = {k: j[k] for k in ("store", "op", "chunks", "reused", "embedded", "generation", "versions") if k in j}
        print(f"{at:7.1f}  {j['event']}  " + "  ".join(f"{k} {v}" for k, v in rest.items()))
if ok:
    print(f"ingest_ok's generation equals the object's: {str(ok[0]['jsonPayload']['generation']) == gen}; doc_key {key[:13]}...")
else:
    print(f"no ingest_ok for generation {gen} between {first} and {last}: Cloud Logging can lag a minute; run this again")'''.replace("__HELPERS__", API_HELPERS)

PY_SUB = r'''import json, os, re, subprocess, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P = os.environ["PROJECT"]
__HELPERS__


def short(value):
    """A field's value on one line: nested settings flattened, a field the API left out said in words."""
    if value is None:
        return "(absent)"
    if isinstance(value, dict):
        return ", ".join(f"{k} {short(v)}" for k, v in value.items()) or "{} (set, and empty: never expires)"
    return str(value)


sub = api(f"https://pubsub.googleapis.com/v1/projects/{P}/subscriptions/__SUB__")
top = api(f"https://pubsub.googleapis.com/v1/projects/{P}/topics/__TOPIC__")
tf = open("terraform/eventarc.tf", encoding="utf-8").read()
declared = tf.split('resource "google_pubsub_subscription" "ingest_push"', 1)[1].split("\n}\n", 1)[0]
FIELDS = [("pushConfig", "push_config"), ("ackDeadlineSeconds", "ack_deadline_seconds"), ("retryPolicy", "retry_policy"),
          ("deadLetterPolicy", "dead_letter_policy"), ("messageRetentionDuration", "message_retention_duration"),
          ("retainAckedMessages", "retain_acked_messages"), ("expirationPolicy", "expiration_policy"),
          ("enableMessageOrdering", "enable_message_ordering"),
          ("enableExactlyOnceDelivery", "enable_exactly_once_delivery"), ("filter", "filter")]
print(f"subscription {sub['name'].rsplit('/', 1)[1]}, topic {sub['topic'].rsplit('/', 1)[1]}, state {sub.get('state')}")
for rest, arg in FIELDS:
    who = "eventarc.tf" if re.search(rf"^\s*{arg}\b", declared, re.M) else "Google"
    print(f"  {rest:26} {who:12} {short(sub.get(rest))}")
topic_tf = re.search(r'resource "google_pubsub_topic" "ingest" \{[^}]*\}', tf).group(0)
print(f"topic {top['name'].rsplit('/', 1)[1]}")
print(f"  {'messageRetentionDuration':26} {'eventarc.tf' if 'message_retention_duration' in topic_tf else 'Google':12} "
      f"{short(top.get('messageRetentionDuration'))}")'''.replace("__HELPERS__", API_ONLY)

PY_RECORDS = r'''import json, os, subprocess, urllib.parse, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
P, NAME = os.environ["PROJECT"], "__OBJECT__"
TOKEN = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
req = urllib.request.Request(f"https://storage.googleapis.com/storage/v1/b/{P}-uploads/o/{urllib.parse.quote(NAME, safe='')}",
                             headers={"Authorization": f"Bearer {TOKEN}"})
gen = str(json.load(urllib.request.urlopen(req, timeout=60))["generation"])
db = firestore.Client(project=P)
src = db.document("sources/" + NAME.replace("/", "~")).get().to_dict() or {}
key = src.get("doc_key") or ""
claim = (db.document(f"documents/{key}").get().to_dict() or {}) if key else {}
rows = (db.collection("chunks").where(filter=FieldFilter("tenant_id", "==", "acme"))
        .where(filter=FieldFilter("source_uri", "==", f"gs://{P}-uploads/{NAME}")).stream())
mine = sorted((s for s in rows if (s.to_dict() or {}).get("doc_key") == key), key=lambda s: int(s.id.rsplit("#", 1)[1]))
led = db.document("ledger/acme").get().to_dict() or {}
same = lambda g: "yes" if str(g) == gen else "NO"
print(f"the object:  generation {gen}")
print(f"sources/{NAME.replace('/', '~')}: {src.get('status')}, generation {src.get('generation')} (the object's: "
      f"{same(src.get('generation'))}), chunks {src.get('chunks')}, reused {src.get('reused')}, embedded {src.get('embedded')}")
print(f"documents/{key[:13]}...: {claim.get('status')}, generation {claim.get('generation')} (the object's: "
      f"{same(claim.get('generation'))}), chunks {claim.get('chunks')}")
print(f"chunks of this version: {len(mine)}, {sum(1 for s in mine if s.to_dict().get('current'))} current, "
      f"locators {', '.join(s.to_dict().get('locator') or '?' for s in mine)}")
print(f"ledger/acme: fingerprint {str(led.get('fingerprint'))[:8]}..., versions {led.get('versions')}, last_event {led.get('last_event')}")'''

PY_API = r'''import json, os, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
API, TOKEN, NAME = os.environ["API"], os.environ["TOKEN"], "__OBJECT__"
QUESTION = "__QUESTION__"


def call(path, body=None):
    """GET or POST one DocuMind API path as the UI's service account; returns the parsed JSON."""
    req = urllib.request.Request(API + path, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=120))


row = next((r for r in call("/v1/sources?tenant_id=acme")["sources"] if r["name"] == NAME), {})
print(f"GET /v1/sources: {NAME} {row.get('status')}, generation {row.get('generation')}, chunks {row.get('chunks')}, "
      f"embedded {row.get('embedded')}, held in {', '.join(sorted(row.get('mirrored') or {})) or 'the kit rows only'}")
ans = call("/v1/query", {"query": QUESTION, "tenant_id": "acme", "stream": False})
print(f"POST /v1/query: {ans['answer'][:160]}")
for c in ans["citations"]:
    if c["source_uri"].endswith(NAME):
        print(f"  cites {c['chunk_id'][:17]}...#{c['chunk_id'].rsplit('#', 1)[1]}: {c['quote'][:70]}")
s = ans.get("stages") or {}
print(f"  answerable {ans['answerable']}, backend {s.get('retrieval_backend')}, pool {s.get('pool')}, from the index {s.get('vector_chunks')}")'''

PY_PRECHECK = r'''import hashlib, os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from google.cloud import firestore
db = firestore.Client(project=os.environ["PROJECT"])


def would_upload(tenant_dir):
    """evals/upload.sh's rule for one tenant: every file, but a .md whose .pdf or .mp4 twin exists, and a .segments.json."""
    out = []
    for name in sorted(os.listdir(tenant_dir)):
        path = os.path.join(tenant_dir, name)
        stem, ext = os.path.splitext(path)
        if not os.path.isfile(path) or name.endswith(".segments.json"):
            continue
        if ext == ".md" and (os.path.isfile(stem + ".pdf") or os.path.isfile(stem + ".mp4")):
            continue
        out.append(name)
    return out


total, same, other = 0, 0, []
for tenant in sorted(os.listdir("evals/corpus")):
    folder = os.path.join("evals/corpus", tenant)
    if not os.path.isdir(folder):
        continue
    names = would_upload(folder)
    total += len(names)
    print(f"{tenant}: {len(names)} objects")
    for name in names:
        sha = hashlib.sha256(open(os.path.join(folder, name), "rb").read()).hexdigest()
        row = db.document(f"sources/{tenant}~{name}").get().to_dict() or {}
        if row.get("status") == "indexed" and row.get("sha256") == sha:
            same += 1
        else:
            other.append(f"{tenant}/{name}: the ledger holds {row.get('status') or 'nothing'}"
                         + (f", sha256 {str(row.get('sha256'))[:8]}..., this file {sha[:8]}..." if row else ""))
print(f"{same} of {total} files are the version the ledger holds current" + (": every delivery will be a duplicate" if same == total else ""))
for line in other:
    print("  differs:", line)'''

PY_BURST_LOG = r'''import collections, datetime as dt, json, os, statistics, subprocess, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P, SINCE = os.environ["PROJECT"], os.environ["BURST_SINCE"]
__HELPERS__


def entries(flt):
    """Every Cloud Logging entry that matches a filter, oldest first, page by page."""
    out, page = [], None
    while True:
        body = {"resourceNames": [f"projects/{P}"], "filter": flt, "orderBy": "timestamp asc", "pageSize": 1000}
        if page:
            body["pageToken"] = page
        r = api("https://logging.googleapis.com/v2/entries:list", body)
        out += r.get("entries", [])
        page = r.get("nextPageToken")
        if not page:
            return out


t0 = when(SINCE)
seen = entries(f'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-ingest" AND timestamp>="{SINCE}"')
posts = [(when(e["timestamp"]), int(e["httpRequest"].get("status", 0)), float(str(e["httpRequest"].get("latency", "0s")).rstrip("s") or 0))
         for e in seen if (e.get("httpRequest") or {}).get("requestMethod") == "POST"]
verdicts = collections.Counter(e["jsonPayload"]["event"] for e in seen
                               if str((e.get("jsonPayload") or {}).get("event", "")).startswith("ingest_"))
print(f"deliveries to documind-ingest since {SINCE}: {len(posts)}")
for status in sorted({s for _, s, _ in posts}):
    mine = [p for p in posts if p[1] == status]
    print(f"  HTTP {status}: {len(mine):3}, the first at +{(mine[0][0] - t0).total_seconds():.0f} s, the last at "
          f"+{(mine[-1][0] - t0).total_seconds():.0f} s, median latency {statistics.median(p[2] for p in mine):.2f} s")
slices = collections.defaultdict(collections.Counter)
for t, s, _ in posts:
    slices[int((t - t0).total_seconds()) // 10 * 10][s] += 1
print("by ten-second slice after BURST_SINCE:")
for b in sorted(slices):
    print(f"  +{b:4} s  " + "  ".join(f"HTTP {s} x{n}" for s, n in sorted(slices[b].items())))
print("the worker's verdicts: " + (", ".join(f"{k} {v}" for k, v in sorted(verdicts.items())) or "none"))'''.replace("__HELPERS__", API_HELPERS)

PY_BURST_METRICS = r'''import datetime as dt, json, os, subprocess, urllib.parse, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P, SINCE = os.environ["PROJECT"], os.environ["BURST_SINCE"]
__HELPERS__


start = when(SINCE) - dt.timedelta(minutes=2)
end = dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0)
iso = lambda t: t.strftime("%Y-%m-%dT%H:%M:%SZ")
SUB = 'resource.type="pubsub_subscription" AND resource.labels.subscription_id="{}"'
RUN = 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-ingest" AND metric.labels.state="active"'


def minutes(metric, where, aligner, group=None):
    """One metric over the window in one-minute steps, summed across series: {label: {"HH:MM": value}}."""
    q = {"filter": f'metric.type="{metric}" AND {where}', "interval.startTime": iso(start), "interval.endTime": iso(end),
         "aggregation.alignmentPeriod": "60s", "aggregation.perSeriesAligner": aligner,
         "aggregation.crossSeriesReducer": "REDUCE_SUM"}
    if group:
        q["aggregation.groupByFields"] = f"metric.label.{group}"
    out = {}
    for s in api(f"https://monitoring.googleapis.com/v3/projects/{P}/timeSeries?{urllib.parse.urlencode(q)}").get("timeSeries", []):
        label = (s.get("metric", {}).get("labels") or {}).get(group, "?") if group else "all"
        for pt in s.get("points", []):
            v = pt["value"]
            out.setdefault(label, {})[pt["interval"]["endTime"][11:16]] = float(v.get("int64Value", v.get("doubleValue", 0)))
    return out


backlog = minutes("pubsub.googleapis.com/subscription/num_undelivered_messages", SUB.format("__SUB__"), "ALIGN_MAX").get("all", {})
oldest = minutes("pubsub.googleapis.com/subscription/oldest_unacked_message_age", SUB.format("__SUB__"), "ALIGN_MAX").get("all", {})
pushes = minutes("pubsub.googleapis.com/subscription/push_request_count", SUB.format("__SUB__"), "ALIGN_DELTA", "response_class")
dead = minutes("pubsub.googleapis.com/subscription/dead_letter_message_count", SUB.format("__SUB__"), "ALIGN_DELTA").get("all", {})
dlq = minutes("pubsub.googleapis.com/subscription/num_undelivered_messages", SUB.format("__DLQ_SUB__"), "ALIGN_MAX").get("all", {})
active = minutes("run.googleapis.com/container/instance_count", RUN, "ALIGN_MAX").get("all", {})
named = ("ack", "remote_server_4xx", "remote_server_5xx")
print(f"{'UTC':5}  {'backlog':>7}  {'oldest':>7}  {'ack':>4}  {'4xx':>4}  {'5xx':>4}  {'other':>5}  {'instances':>9}")
for m in sorted(set(backlog) | set(oldest) | set(active) | {k for v in pushes.values() for k in v}):
    other = sum(v.get(m, 0) for k, v in pushes.items() if k not in named)
    print(f"{m}  {backlog.get(m, 0):7.0f}  {oldest.get(m, 0):6.0f}s  " + "  ".join(f"{pushes.get(k, {}).get(m, 0):4.0f}" for k in named)
          + f"  {other:5.0f}  {active.get(m, 0):9.0f}")
print(f"forwarded to the dead-letter topic in the window: {sum(dead.values()):.0f}")
print(f"__DLQ_SUB__ undelivered, the last sample: {dlq[max(dlq)]:.0f}" if dlq else "__DLQ_SUB__: no sample in the window")'''.replace("__HELPERS__", API_HELPERS)

for name, code in list(globals().items()):
    if name.startswith("PY_"):
        code = (code.replace("__OBJECT__", OBJECT).replace("__SUB__", SUB).replace("__TOPIC__", TOPIC)
                .replace("__DLQ_SUB__", DLQ_SUB).replace("__QUESTION__", QUESTION))
        assert 'warnings.filterwarnings("ignore", category=UserWarning)' in code and "'''" not in code and "\nPY" not in code, name
        assert not re.search(r"__[A-Z_]+__", code), (name, re.findall(r"__[A-Z_]+__", code))
        for fn in re.findall(r"^def (\w+)\(", code, re.M):              # every function a cell defines has a docstring
            assert re.search(rf'^def {fn}\([^\n]*\n    """[^\n]+"""$', code, re.M), (name, fn)
        globals()[name] = code

NOTE_CELL = ("cat > /tmp/" + NOTE_NAME + " <<EOF\n"
             + NOTE_BODY.replace("__WHEN__", "$(date -u +%Y-%m-%dT%H:%M:%SZ)").rstrip("\n")
             + "\nEOF\nmake ingest-one PROJECT=$PROJECT TENANT=acme FILE=/tmp/" + NOTE_NAME)
DESCRIBE = ('gcloud run services describe documind-ingest --region "$REGION" --project "$PROJECT" \\\n'
            "  --format='yaml(status.latestReadyRevisionName,spec.template.metadata.annotations)' | grep -E 'latestReadyRevisionName|maxScale'")
CELLS = {
    "note": NOTE_CELL,
    "trace": heredoc(PY_TRACE),
    "sub": heredoc(PY_SUB),
    "records": heredoc(PY_RECORDS),
    "api": heredoc(PY_API, prefix='TOKEN="$(tok "$API")" '),
    "precheck": heredoc(PY_PRECHECK),
    "squeeze": f'gcloud run services update documind-ingest --region "$REGION" --project "$PROJECT" --max-instances={SQUEEZE}\n{DESCRIBE}',
    "corpus": 'export BURST_SINCE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"; echo "BURST_SINCE=$BURST_SINCE"\nmake ingest-corpus PROJECT=$PROJECT',
    "burst_log": heredoc(PY_BURST_LOG),
    "burst_metrics": heredoc(PY_BURST_METRICS),
    "restore": (f'gcloud run services update documind-ingest --region "$REGION" --project "$PROJECT" --max-instances={MAXI}\n'
                f"{DESCRIBE}\nmake dlq PROJECT=$PROJECT"),
    "retire": f"make retire PROJECT=$PROJECT SOURCE={OBJECT}",
}
CELL_LABELS = {
    "note": "run in the operator shell, in the kit (one small upload; paise of embedding)",
    "trace": "run in the operator shell, a minute after the upload (one Cloud Storage read, one Cloud Logging read)",
    "sub": "run in the operator shell, in the kit (two Pub/Sub reads and your clone's eventarc.tf; changes nothing)",
    "records": "run in the operator shell (Firestore reads and one Cloud Storage read; writes nothing)",
    "api": "run in the operator shell (the ledger, then one answer: paise)",
    "precheck": "run in the operator shell, in the kit (hashes your clone's corpus against the ledger; writes nothing)",
    "squeeze": "run in the operator shell (a new revision of the worker, the same image; a minute)",
    "corpus": "run in the operator shell, in the kit (31 uploads, every one already indexed)",
    "burst_log": "run in the operator shell, two minutes after the upload (Cloud Logging reads; changes nothing)",
    "burst_metrics": "run in the operator shell, at least three minutes after the upload (Cloud Monitoring reads; changes nothing)",
    "restore": "run in the operator shell, before you leave this step (the ceiling back to the kit's; a minute)",
    "retire": "run in the operator shell, in the kit, when the lesson is done (withdraws the note; reversible with make restore)",
}
assert CELL_LABELS["corpus"].count(str(N_OBJECTS)) == 1

# ------------------------------------------------------------------ the lane cells, run here against stand-in Google APIs
QUIET = {"PATH": str(Path(sys.executable).parent), "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""), "PYTHONIOENCODING": "utf-8",
         "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}       # no gcloud on PATH, no Google credentials in reach
STAND_IN = r'''import io, json, sys, types, urllib.parse, urllib.request
ROUTES, DOCS = json.loads(%r), json.loads(%r)
class R:
    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, "", 0
def run(cmd, **kw):
    if cmd[1:3] == ["auth", "print-access-token"]:
        return R("stand-in-token\n")
    raise SystemExit("unexpected command: " + " ".join(cmd))
fake = types.ModuleType("subprocess"); fake.run = run; sys.modules["subprocess"] = fake
class Resp(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): return False
def urlopen(req, timeout=None):
    url = urllib.parse.unquote_plus(req.full_url)
    for keys, value in ROUTES:
        if all(k in url for k in keys):
            return Resp(json.dumps(value).encode())
    raise SystemExit("unexpected URL: " + url)
urllib.request.urlopen = urlopen
class Snap:
    def __init__(self, path):
        self.id, self._d = path.split("/", 1)[1], DOCS.get(path)
    exists = property(lambda self: self._d is not None)
    def to_dict(self): return None if self._d is None else dict(self._d)
class Doc:
    def __init__(self, path): self.path = path
    def get(self, **kw): return Snap(self.path)
class FieldFilter:
    def __init__(self, field, op, value): self.field, self.op, self.value = field, op, value
class Query:
    def __init__(self, name, filters=()): self.name, self.filters = name, filters
    def where(self, *a, filter=None): return Query(self.name, self.filters + (filter or FieldFilter(*a),))
    def stream(self):
        for path in sorted(DOCS):
            d = DOCS[path]
            if path.startswith(self.name + "/") and all(d.get(f.field) == f.value for f in self.filters):
                yield Snap(path)
class Client:
    def __init__(self, project=None): pass
    def document(self, path): return Doc(path)
    def collection(self, name): return Query(name)
google, cloud = types.ModuleType("google"), types.ModuleType("google.cloud")
fs, v1, bq = (types.ModuleType(n) for n in ("google.cloud.firestore", "google.cloud.firestore_v1", "google.cloud.firestore_v1.base_query"))
fs.Client, bq.FieldFilter, google.cloud, cloud.firestore = Client, FieldFilter, cloud, fs
sys.modules.update({"google": google, "google.cloud": cloud, "google.cloud.firestore": fs,
                    "google.cloud.firestore_v1": v1, "google.cloud.firestore_v1.base_query": bq})
'''


def stand_in(cell: str, routes: list, docs: dict, cwd: Path, extra_env: dict | None = None) -> str:
    """One lane cell, run offline: stand-in gcloud, Google APIs and Firestore; the cell's stdout, which must be clean."""
    r = subprocess.run([sys.executable, "-"], input=STAND_IN % (json.dumps(routes), json.dumps(docs)) + cell,
                       cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
                       env={**QUIET, "PROJECT": PROJ, "REGION": "asia-south1", "API": "https://documind-api-NUMBER.asia-south1.run.app",
                            "TOKEN": "stand-in", **(extra_env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stderr[-1500:], r.stdout[-500:])
    return r.stdout


SI_GEN, SI_KEY = "1111111111111111", "acme_" + "ab" * 32       # stand-in values: never printed on the page
SI_OBJ = {"name": OBJECT, "generation": SI_GEN, "size": "512", "contentType": "text/markdown", "timeCreated": "2026-11-17T10:00:00.250Z"}
SI_LOG = {"entries": [
    {"timestamp": "2026-11-17T10:00:01.100000000Z", "httpRequest": {"requestMethod": "POST", "status": 200, "latency": "4.200s"}},
    {"timestamp": "2026-11-17T10:00:04.900Z", "jsonPayload": {"event": "mirror_ok", "store": "rag_engine", "op": "upsert", "doc_key": SI_KEY}},
    {"timestamp": "2026-11-17T10:00:05.100Z", "jsonPayload": {"event": "ledger_fingerprint", "tenant": "acme", "versions": 22}},
    {"timestamp": "2026-11-17T10:00:05.200Z", "jsonPayload": {"event": "ingest_ok", "doc_key": SI_KEY, "chunks": N_CHUNKS, "reused": 0,
                                                              "embedded": N_CHUNKS, "generation": SI_GEN}}]}
out = stand_in(PY_TRACE, [(["storage/v1/b/"], SI_OBJ), (["entries:list"], SI_LOG)], {}, KIT)
assert "POST 200, latency 4.200 s" in out and f"ingest_ok  chunks {N_CHUNKS}" in out and "equals the object's: True" in out, out
assert f"generation {SI_GEN}, 512 bytes" in out and out.count("mirror_ok") == 1, out

SI_SUB = {"name": f"projects/{PROJ}/subscriptions/{SUB}", "topic": f"projects/{PROJ}/topics/{TOPIC}", "state": "ACTIVE",
          "pushConfig": {"pushEndpoint": PUSH_URL, "oidcToken": {"serviceAccountEmail": SA_EMAIL}}, "ackDeadlineSeconds": ACK,
          "retryPolicy": {"minimumBackoff": f"{MIN_BO}s", "maximumBackoff": f"{MAX_BO}s"},
          "deadLetterPolicy": {"deadLetterTopic": f"projects/{PROJ}/topics/{DLQ_TOPIC}", "maxDeliveryAttempts": ATTEMPTS},
          "messageRetentionDuration": "stand-in", "expirationPolicy": {}}       # never expires: the API returns an empty policy
out = stand_in(PY_SUB, [([f"subscriptions/{SUB}"], SI_SUB), ([f"topics/{TOPIC}"], {"name": f"projects/{PROJ}/topics/{TOPIC}"})], {}, KIT)
rows_ = [line.split()[:2] for line in out.splitlines() if line.startswith("  ")]
assert [k for k, v in rows_ if v == "eventarc.tf"] == ["pushConfig", "ackDeadlineSeconds", "retryPolicy", "deadLetterPolicy",
                                                       "expirationPolicy"], out
assert sum(v == "Google" for _, v in rows_) == N_DEFAULTED + 1 and ["retainAckedMessages", "Google"] in rows_, out   # + the topic's

SI_DOCS = {f"sources/{OBJECT.replace('/', '~')}": {"status": "indexed", "generation": SI_GEN, "doc_key": SI_KEY, "chunks": N_CHUNKS,
                                                    "reused": 0, "embedded": N_CHUNKS},
           f"documents/{SI_KEY}": {"status": "indexed", "generation": SI_GEN, "chunks": N_CHUNKS},
           "ledger/acme": {"fingerprint": "0123456789abcdef", "versions": 22, "last_event": "ingest_ok"}}
for i, chunk in enumerate(NOTE_CHUNKS):
    SI_DOCS[f"chunks/acme:{SI_KEY[5:]}#{i}"] = {"tenant_id": "acme", "source_uri": f"gs://{PROJ}-uploads/{OBJECT}", "doc_key": SI_KEY,
                                               "current": True, "locator": chunk["locator"]}
out = stand_in(PY_RECORDS, [(["storage/v1/b/"], SI_OBJ)], SI_DOCS, KIT)
assert out.count("(the object's: yes)") == 2 and f"chunks of this version: {N_CHUNKS}, {N_CHUNKS} current, locators {', '.join(LOCATORS)}" in out, out

SI_ANS = {"answer": "Couriers deliver to gate 3; the parcel is signed for at the security desk [1].",
          "citations": [{"chunk_id": f"acme:{SI_KEY[5:]}#{CITE_POS}", "source_uri": f"gs://{PROJ}-uploads/{OBJECT}", "quote": "gate 3"}],
          "answerable": True, "stages": {"retrieval_backend": "vector", "pool": 20, "vector_chunks": 20}}
out = stand_in(PY_API, [(["/v1/sources"], {"sources": [{"name": OBJECT, "status": "indexed", "generation": SI_GEN, "chunks": N_CHUNKS,
                                                        "embedded": N_CHUNKS, "mirrored": {"rag_engine": "us-central1"}}]}),
                        (["/v1/query"], SI_ANS)], {}, KIT)
assert f"#{CITE_POS}: gate 3" in out and "backend vector" in out and "held in rag_engine" in out, out

# the pre-check against a stand-in ledger that holds the kit's corpus as published: every file must match. It runs in
# a copy of the corpus as a fresh clone has it, so a checkout holding lesson 7.5's video cannot change the result.
CLONE = Path(tempfile.mkdtemp(prefix="lesson81-"))
for t in CORPUS:
    (CLONE / "evals" / "corpus" / t).mkdir(parents=True)
    for n in clone_files(KIT / "evals" / "corpus" / t):
        (CLONE / "evals" / "corpus" / t / n).write_bytes((KIT / "evals" / "corpus" / t / n).read_bytes())
LEDGER = {f"sources/{t}~{n}": {"status": "indexed", "sha256": hashlib.sha256((KIT / "evals" / "corpus" / t / n).read_bytes()).hexdigest()}
          for t, names in CORPUS.items() for n in names}
out = stand_in(PY_PRECHECK, [], LEDGER, CLONE)
assert out.splitlines()[:3] == [f"{t}: {len(n)} objects" for t, n in CORPUS.items()], out
assert f"{N_OBJECTS} of {N_OBJECTS} files are the version the ledger holds current: every delivery will be a duplicate" in out, out
changed = dict(LEDGER)
changed["sources/acme~hr_policy_2026.md"] = {"status": "indexed", "sha256": "f" * 64}
out = stand_in(PY_PRECHECK, [], changed, CLONE)
assert f"{N_OBJECTS - 1} of {N_OBJECTS}" in out and "differs: acme/hr_policy_2026.md" in out, out
shutil.rmtree(CLONE, ignore_errors=True)

BURST = "2026-11-17T10:00:00Z"
SI_BURST = {"entries": [{"timestamp": f"2026-11-17T10:00:0{i}.5Z", "httpRequest": {"requestMethod": "POST", "status": 429, "latency": "10.0s"}}
                        for i in range(3)]
            + [{"timestamp": f"2026-11-17T10:00:{12 + i:02d}.5Z", "httpRequest": {"requestMethod": "POST", "status": 200, "latency": "0.4s"}}
               for i in range(N_OBJECTS)]
            + [{"timestamp": f"2026-11-17T10:00:{12 + i:02d}.6Z", "jsonPayload": {"event": "ingest_duplicate", "doc_key": f"k{i}"}}
               for i in range(N_OBJECTS)]}
out = stand_in(PY_BURST_LOG, [(["entries:list"], SI_BURST)], {}, KIT, {"BURST_SINCE": BURST})
assert f"deliveries to documind-ingest since {BURST}: {N_OBJECTS + 3}" in out and f"HTTP 200:  {N_OBJECTS}" in out, out
assert f"ingest_duplicate {N_OBJECTS}" in out and "+   0 s  HTTP 429 x3" in out, out


def series(value: float, label: dict | None = None) -> dict:
    """A stand-in Monitoring series with one point at 10:01."""
    return {"metric": {"labels": label or {}}, "points": [{"interval": {"endTime": "2026-11-17T10:01:00Z"}, "value": {"int64Value": str(int(value))}}]}


SI_MON = [(["num_undelivered_messages", f'subscription_id="{SUB}"'], {"timeSeries": [series(N_OBJECTS)]}),
          (["num_undelivered_messages", f'subscription_id="{DLQ_SUB}"'], {"timeSeries": [series(0)]}),
          (["oldest_unacked_message_age"], {"timeSeries": [series(24)]}),
          (["push_request_count", "groupByFields=metric.label.response_class"],
           {"timeSeries": [series(N_OBJECTS, {"response_class": "ack"}), series(3, {"response_class": "remote_server_4xx"})]}),
          (["dead_letter_message_count"], {"timeSeries": []}),
          (["container/instance_count", 'metric.labels.state="active"'], {"timeSeries": [series(SQUEEZE)]})]
out = stand_in(PY_BURST_METRICS, SI_MON, {}, KIT, {"BURST_SINCE": BURST})
assert f"10:01  {N_OBJECTS:7d}      24s  {N_OBJECTS:4d}     3     0      0  {SQUEEZE:9d}" in out, out
assert "forwarded to the dead-letter topic in the window: 0" in out and f"{DLQ_SUB} undelivered, the last sample: 0" in out, out
N_STAND_INS = 8

# ------------------------------------------------------------------ the outputs: recorded from the author's lane, or computed
RECORDED = {k: pb.recorded(LESSON, f"{k}.txt") for k in (
    "trace_upload", "trace_timeline", "subscription_rest", "trace_records", "trace_api", "burst_precheck", "burst_squeeze",
    "burst_requests", "burst_metrics", "burst_restore", "trace_retire")}
LANE = "(the author's lane: your generations, keys, times and counts are yours)"
OUTS = {
    "note": (LANE, RECORDED["trace_upload"]), "trace": (LANE, RECORDED["trace_timeline"]),
    "sub": ("(the author's lane: your project's names in place of the placeholders)", RECORDED["subscription_rest"]),
    "records": (LANE, RECORDED["trace_records"]), "api": ("(the author's lane: the answer's wording is the model's)", RECORDED["trace_api"]),
    "precheck": (LANE, RECORDED["burst_precheck"]), "squeeze": ("(the author's lane: your revision's name is yours)", RECORDED["burst_squeeze"]),
    "corpus": ("shape (upload.sh's own lines, computed from the kit's corpus when this page was built; gcloud storage cp's "
               "progress lines are the ...)", CORPUS_OUT),
    "burst_log": (LANE, RECORDED["burst_requests"]), "burst_metrics": (LANE, RECORDED["burst_metrics"]),
    "restore": ("(the author's lane: your revision's name is yours)", RECORDED["burst_restore"]),
    "retire": (LANE, RECORDED["trace_retire"]),
}
assert set(OUTS) == set(CELLS)


def bash_window(label: str, code: str) -> str:
    """A command window: the label says where to run it, the button copies it."""
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + html.escape(label) + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    """An expected-output window: read only."""
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + html.escape(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(*v) for k, v in OUTS.items()})


# ------------------------------------------------------------------ the tables
def tw(head: list, rows: list) -> str:
    """A comparison table: the first cell bare, every other cell labelled for the phone layout."""
    out = ['<div class="tw"><div class="tw-scroll" tabindex="0"><table class="comp-table">',
           "<thead><tr>" + "".join(f"<th>{h}</th>" for h in head) + "</tr></thead>", "<tbody>"]
    for cells in rows:
        out.append("<tr><td>" + cells[0] + "</td>" + "".join(f'<td data-label="{html.escape(re.sub("<[^>]+>", "", h))}">{c}</td>'
                                                            for h, c in zip(head[1:], cells[1:])) + "</tr>")
    out.append('</tbody></table></div><span class="scroll-hint">&#8596; SWIPE</span></div>')
    return "\n".join(out)


def link(key: str, text: str) -> str:
    """A link to one of Google's pages this lesson reads."""
    return f'<a href="{GOOGLE[key]}" target="_blank" rel="noopener">{text}</a>'


def c(text: str) -> str:
    """Inline code."""
    return f"<code>{html.escape(text)}</code>"


WORDS = {3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 10: "ten", 12: "twelve", 13: "thirteen", 30: "thirty",
         31: "thirty-one"}
SETTINGS_ROWS = [
    [c("push_config"), f"push to {c('local.ingest_url')}, the worker's own URL, with an OIDC token for {c(INGEST_SA)}",
     "without it, a pull subscription: the reader asks", "Pub/Sub calls the worker, and nothing else on the internet can"],
    [c("ack_deadline_seconds"), f"{ACK}", f"{G['ack_default']} s by default, {G['ack_max']} s at most",
     f"the longest Google allows, and the worker's own {c(f'--timeout={TIMEOUT}')}"],
    [c("retry_policy"), f"{MIN_BO} s, growing to {MAX_BO} s", f"retry immediately by default; {G['backoff_max']} s is the longest backoff",
     "a refused message waits before it comes back (lesson 1.5 timed it)"],
    [c("dead_letter_policy"), f"{c(DLQ_TOPIC)} after {ATTEMPTS} attempts",
     f"{G['dlq_default']} attempts by default once a dead-letter topic is set; {G['dlq_min']} to {G['dlq_max']} allowed",
     f"{WORDS[ATTEMPTS]}, for the cold-start refusals the comment records"],
    [c("message_retention_duration"), "not set", f"{G['retention_days']} days ({G['retention_min']} to {G['retention_max_days']} days)",
     f"a notice nobody acknowledges is dropped after {WORDS[G['retention_days']]} days"],
    [c("retain_acked_messages"), "not set", "off", "an acknowledged notice is gone: there is nothing to seek back to"],
    [c("expiration_policy"), c('ttl = ""') + ": never (13 October 2026)",
     f"{G['expiration_days']} days without subscriber activity, then the subscription is deleted; never expire is a setting",
     f"a lane with no upload for {G['expiration_days']} days keeps the subscription it would otherwise have lost, in silence"],
    [c("enable_message_ordering"), "not set", "off; it needs ordering keys from the publisher, and cannot be changed after creation",
     "no order; the generation guard makes order irrelevant"],
    [c("enable_exactly_once_delivery"), "not set", "off; push subscriptions cannot have it at all",
     "a second delivery is possible; the claim makes it a duplicate"],
    [c("filter"), "not set", "none; it matches attributes only, and cannot be changed after creation", "every notice reaches the worker"],
]
assert [r[1] == "not set" for r in SETTINGS_ROWS] == [not DECLARED[a] for a in TF_ARGS]
SETTINGS_ROWS.append([f"{c('message_retention_duration')} on the topic", "not set",
                      f"not enabled ({G['retention_min']} to {G['retention_max_days']} days when it is)",
                      "the topic keeps no copy of anything"])
SETTINGS_TABLE = tw(["Setting", f"In {c('eventarc.tf')}", "Google's default and limits", "On your lane"], SETTINGS_ROWS)

KAFKA_ROWS = [
    ["Topic", f"{c(TOPIC)}, written by Cloud Storage's notice; a twin, {c(DLQ_TOPIC)}, for dead letters",
     "A topic, split into partitions you choose and replicated to brokers you run",
     "Pub/Sub has no partitions or replicas to size; Kafka makes both your decision"],
    ["Subscription", f"{c(SUB)}: Pub/Sub keeps each message's state until it is acknowledged",
     "A consumer group's committed offsets: one number per partition",
     "Per-message state against one cursor per partition; an acknowledged message is gone, a read record stays"],
    ["Push and pull", f"Push to the worker's URL with an OIDC token for {c(INGEST_SA)}; Pub/Sub sets the pace",
     "Pull only: each consumer polls when it is ready; an HTTP endpoint needs a consumer, or a sink connector, in front of it",
     "A pushed reader that is full refuses, and spends attempts; a pulling reader reads later (step 7)"],
    ["Ack deadline", f"{ACK} s, the most Google allows, and the worker's {c(f'--timeout={TIMEOUT}')}",
     f"{c('max.poll.interval.ms')}, {WORDS[KAFKA['max_poll_ms'] // 60_000]} minutes by default: a consumer that does not poll "
     "again in time leaves the group",
     "Pub/Sub times out one delivery; Kafka times out the consumer and hands its partitions to another"],
    ["Retry", f"{MIN_BO} s growing to {MAX_BO} s, per message, by the subscription", "None in the broker: the consumer retries, "
     "or republishes the record to a retry topic, in code you write", "A retry is a setting on Pub/Sub and a design on Kafka"],
    ["Dead letter", f"{c(DLQ_TOPIC)} after {ATTEMPTS} attempts, held by {c(DLQ_SUB)}, and an alert while it holds any",
     f"None in the broker: a dead-letter topic is one more topic your consumer writes to (Kafka Connect's sinks have {c('errors.deadletterqueue.topic.name')})",
     "Pub/Sub counts the attempts for you, approximately; on Kafka the count is yours"],
    ["Ordering", "Not enabled; Cloud Storage does not promise its notices in order; the generation guard acknowledges a late one as stale",
     "Order within a partition; records with the same key go to the same partition",
     "Kafka orders per key by design; Pub/Sub only with ordering keys, and then one message per key at a time on push"],
    ["Exactly once", "Not available on push; a second delivery finds the content-hash claim and is a 200 duplicate",
     "Within Kafka: an idempotent producer and transactions, read with read_committed",
     "Neither makes a Firestore write exactly once: the consumer's own key does, here the content hash"],
    ["Retention", f"Not set: {G['retention_days']} days for a notice nobody acknowledged; acknowledged notices are not kept",
     f"Every record, read or not, for the topic's retention: {KAFKA['retention_hours']} hours by default",
     "Pub/Sub keeps the unread; Kafka keeps everything"],
    ["Replay", f"No seek: nothing acknowledged is kept. The kit replays by rewriting the object onto itself: a new generation, a new notice",
     "Move a consumer's offset, or reset a group's, to any retained offset or time",
     "Kafka's history is the log; the kit's history is the versioned bucket"],
    ["Consumer groups", f"One subscription, so one reader; Cloud Run's instances share it",
     "Any number of groups, each with its own offsets; a new group can start from the earliest retained record",
     "A new Pub/Sub subscription gets only what is published after it exists; a new Kafka group can read the past"],
    ["Partitions", f"None to choose: Pub/Sub scales the topic; the worker's parallelism is Cloud Run's, {CONC} request x {MAXI} instances",
     "The partition count caps a group's parallelism: one consumer per partition at a time",
     "Kafka's ceiling is set on the topic; the kit's on the consumer"],
    ["Throughput", f"No Pub/Sub quota declared; {IN_FLIGHT} in flight at most; the backlog is Pub/Sub's undelivered count and its oldest message's age",
     "Brokers and partitions set it; consumer lag, in offsets, is the backlog", f"The kit alerts on {c(SUB)}'s oldest message past {BACKLOG_S // 60} minutes, and on the dead-letter subscription"],
]
assert len(KAFKA_ROWS) == 13
KAFKA_TABLE = tw(["Idea", "On your lane", "Kafka's nearest", "What differs"], [[f"<strong>{r[0]}</strong>"] + r[1:] for r in KAFKA_ROWS])
assert "quota" in read("terraform/quota.tf") and "pubsub" not in read("terraform/quota.tf").split("documind_alerts", 1)[0]
SOURCES = ", ".join(link(k, t) for k, t in (
    ("props", "subscription properties"), ("push", "push subscriptions"), ("retry", "the retry policy"), ("dlq", "dead-letter topics"),
    ("ordering", "ordering"), ("eod", "exactly-once delivery"), ("replay", "replay and seek"), ("topic", "topic retention"),
    ("overview", "subscriptions"), ("gcs", "Cloud Storage's notices"), ("run_scaling", "Cloud Run's pending requests"),
    ("run_max", "Cloud Run's maximum instances"), ("run_logging", "Cloud Run's logs"), ("metrics", "the metrics")))
assert SOURCES.count("<a ") == len(GOOGLE)

# ------------------------------------------------------------------ the trace panel (step 1): data, script, and node's check
HOPS_COMMON = [
    {"n": 1, "name": "Upload",
     "lane": f"`make ingest-one` (or the UI's Documents page) writes `{OBJECT}` into `{PROJ}-uploads`. The bucket keeps versions, "
             "so the write is a new generation: the number every later hop is keyed on.",
     "number": "The tenant is the first segment of the name; the generation is the version.",
     "kafka": "A producer. Kafka watches no bucket: the uploader, or a source connector, writes the record itself, carrying "
              "the object's name and generation and leaving the bytes in the store."},
    {"n": 2, "name": "Notice",
     "lane": f"The bucket's one notification (`{EVENT}`, `{PAYLOAD}`) has Cloud Storage's own service agent publish the object's "
             f"metadata into `{TOPIC}`; the attributes carry `objectGeneration`.",
     "number": "At least once, usually within seconds with no SLA, and not promised in order (Google).",
     "kafka": "`send()` to the topic: the record is appended to one partition, chosen from its key, and acknowledged to the "
              "producer once the brokers have it."},
    {"n": 3, "name": "Subscription",
     "lane": f"`{TOPIC}` has one subscription, `{SUB}`. The message waits there, unacknowledged. The topic itself keeps nothing.",
     "number": f"Unacknowledged, it is kept {G['retention_days']} days: Google's default, since the kit sets none.",
     "kafka": f"The record sits in the partition's log at the next offset, kept for the topic's retention "
              f"({KAFKA['retention_hours']} hours by default) whether or not any group reads it."},
    {"n": 4, "name": "Push",
     "lane": f"Pub/Sub POSTs the message, wrapped in an envelope, to `{PUSH_URL}` with an OIDC token for `{INGEST_SA}`. Cloud Run "
             "admits that caller and no other. Pub/Sub sets the pace: a push window that starts small and grows with each success.",
     "number": f"{CONC} request an instance, {MAXI} instances at most: {IN_FLIGHT} in flight. A request no instance takes in time is refused with a 429.",
     "kafka": "Nothing is pushed. The consumer group's member that owns the partition calls `poll()` when it is ready and takes "
              "a batch; a busy consumer polls later and the records wait in the log."},
    {"n": 5, "name": "Handler",
     "lane": "`push()` decodes `message.data` into `IngestMessage`, the object's record, and reads nothing else of the envelope: "
             "not the message id, the attributes or the delivery attempt. Then the generation guard, that generation's bytes, "
             "and the claim on their content hash.",
     "number": f"{ACK} s to answer: the subscription's ack deadline and the worker's --timeout are one number.",
     "kafka": "The same handler, called from the poll loop with the record's value. The content-hash claim would still be the "
              "defence against a second delivery."},
]
HOPS = {
    "ack": HOPS_COMMON + [
        {"n": 6, "name": "Acknowledge",
         "lane": "The handler answers 200 `indexed`. On push a 2xx is the acknowledgement: Pub/Sub removes the message from the "
                 "subscription and keeps no copy. Any other status, or no answer in time, would be a refusal.",
         "number": "Once. A later duplicate delivery would find the claim and answer 200 `duplicate`.",
         "kafka": "The consumer commits the offset after the work is done. A crash before the commit means the record is "
                  "read again: at least once, as here."},
        {"n": 7, "name": "Records",
         "lane": f"Before the 200: the chunks written staged, swapped current and upserted to Vector Search; `documents/` and "
                 f"`sources/{OBJECT.replace('/', '~')}` with the object's generation; the ledger's fingerprint; the managed "
                 "mirrors acme's policy allows; and an `ingest_ok` line.",
         "number": f"{N_CHUNKS} chunks for this note, by the worker's own chunker: {', '.join(LOCATORS)}.",
         "kafka": "The same writes. They are the consumer's side effects, which is why Kafka's exactly-once would not make "
                  "them exactly once."},
        {"n": 8, "name": "Answer",
         "lane": "A question about the night gate, asked for acme with acme pinned to the kit's index, retrieves the note's "
                 f"NG-01 chunk and cites it as `acme:<sha256>#{CITE_POS}`, the version's own id.",
         "number": "Paise: one embedding of the question, a rerank, one generation.",
         "kafka": "The same answer. The bus decided only when the worker heard about the note."},
    ],
    "nack": HOPS_COMMON + [
        {"n": 6, "name": "Refuse", "bad": True,
         "lane": "The handler answers 400 (a record it can never parse) or 500 (the pipeline failed), or Cloud Run answers 429 "
                 f"before the handler runs, or nothing comes back in {ACK} s. Each is a negative acknowledgement: the message stays.",
         "number": f"Every refusal is one delivery attempt of {ATTEMPTS}.",
         "kafka": "The consumer does not commit. The broker does not retry: the consumer seeks back and tries again, or writes "
                  "the record to a retry topic, in code you write."},
        {"n": 7, "name": "Retry", "bad": True,
         "lane": f"The retry policy waits before the next delivery: from {MIN_BO} s, growing to at most {MAX_BO} s, per message. "
                 "Google's default would retry at once. Lesson 1.5 watched this clock run.",
         "number": f"At most {ATTEMPTS - 1} waits of at most {MAX_BO} s: {DLQ_BOUND_MIN} minutes from the first try to the last.",
         "kafka": "A retry topic per delay, or a pause and a seek in the consumer: the delay and the count are yours to build."},
        {"n": 8, "name": "Dead letter", "bad": True,
         "lane": f"After the last attempt Pub/Sub forwards the message, unchanged, to `{DLQ_TOPIC}`; `{DLQ_SUB}` holds it, and the "
                 "kit's alert opens an incident while it holds anything. Lesson 1.5 reads one with `make dlq`.",
         "number": "Google counts the attempts approximately.",
         "kafka": "A dead-letter topic is one more topic that your consumer, or Kafka Connect's error handling, writes to "
                  "after its own count."},
    ],
}
assert [len(v) for v in HOPS.values()] == [8, 8] and HOPS["ack"][:5] == HOPS["nack"][:5]
TR_JS = r"""var D = __DATA__;
function esc(t){ return String(t).replace(/[&]/g,'&amp;').replace(/[<]/g,'&lt;').replace(/[>]/g,'&gt;'); }
function marks(t){ return esc(t).replace(/`([^`]+)`/g, '<code>$1</code>'); }
function card(verdict, i){ var h = D[verdict][i];
  return {title: h.n + '. ' + h.name, lane: marks(h.lane), number: marks(h.number), kafka: marks(h.kafka)}; }
window.__tr = {hops: function(v){ return D[v]; }, card: card};
var root = document.getElementById('tr'); if (!root) { return; }
var sel = document.getElementById('tr-verdict'), list = document.getElementById('tr-hops'), out = document.getElementById('tr-card'), cur = 0;
function el(tag, cls, inner){ var e = document.createElement(tag); if (cls) { e.className = cls; } e.innerHTML = inner || ''; return e; }
function render(){
  var v = sel.value, c = card(v, cur), cols = el('div', 'tr-cols'), lane = el('div', 'tr-col'), kafka = el('div', 'tr-col kafka');
  list.innerHTML = D[v].map(function(h, i){
    return '<li><button type="button" class="tr-hop' + (h.bad ? ' bad' : '') + '" data-i="' + i + '" aria-pressed="' + (i === cur) + '"><b>' + h.n + '</b>' + esc(h.name) + '</button></li>';
  }).join('');
  lane.appendChild(el('b', '', 'On your lane')); lane.appendChild(el('p', '', c.lane)); lane.appendChild(el('p', 'tr-num', c.number));
  kafka.appendChild(el('b', '', 'The same hop on Kafka')); kafka.appendChild(el('p', '', c.kafka));
  cols.appendChild(lane); cols.appendChild(kafka);
  out.textContent = ''; out.appendChild(el('h5', '', esc(c.title))); out.appendChild(cols);
}
list.addEventListener('click', function(e){ var b = e.target.closest ? e.target.closest('button[data-i]') : null; if (!b) { return; }
  cur = parseInt(b.getAttribute('data-i'), 10); render(); });
sel.addEventListener('change', render);
render();"""
TR_JS = TR_JS.replace("__DATA__", json.dumps(HOPS, separators=(",", ":"))).replace("</", "<\\/")   # nothing closes the script early
JS = "<script>\n(function(){\n'use strict';\n" + TR_JS + "\n})();\n</script>\n"
assert "<div" not in JS and "</div" not in JS                 # the page's div balance is counted over the whole file
NODE = ("var window = {}, document = {getElementById: function(){ return null; }};\n"     # node runs the script as shipped
        "(new Function('window', 'document', " + json.dumps("'use strict';\n" + TR_JS) + "))(window, document);\n"
        "var out = ['ack', 'nack'].map(function(v){ return window.__tr.hops(v).map(function(h, i){ return window.__tr.card(v, i); }); });\n"
        "process.stdout.write(JSON.stringify(out));\n")
node = subprocess.run(["node", "-"], input=NODE, capture_output=True, text=True, encoding="utf-8")
assert node.returncode == 0, node.stderr[-800:]
CARDS = json.loads(node.stdout)
for verdict, cards in zip(("ack", "nack"), CARDS):
    assert len(cards) == 8 and all(c_["lane"] and c_["number"] and c_["kafka"] for c_ in cards)
    for h, c_ in zip(HOPS[verdict], cards):             # what the browser prints is the build's text, marked up and nothing else
        assert re.sub(r"</?code>", "`", c_["lane"]).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&") == h["lane"]
assert all(c_["lane"].count("<code>") == h["lane"].count("`") // 2 for c_, h in zip(CARDS[0], HOPS["ack"]))

# ------------------------------------------------------------------ the run list's rupees, from the kit's prices
PRICES = read("shared/prices.py")
USD_INR = int(one(r"^USD_INR = (\d+)\b", PRICES, re.M))
FLASH_IN, FLASH_OUT = map(float, one(r'"gemini-3\.6-flash": \(([\d.]+), ([\d.]+)\)', PRICES))
CFG = read("services/rag-api/config.py")
CTX, ANS = int(one(r"max_context_tokens: int = (\d+)", CFG)), int(one(r"max_answer_tokens: int = (\d+)", CFG))
TYPICAL = (2000 * FLASH_IN + 300 * FLASH_OUT) / 1e6 * USD_INR          # the course's typical answer (lessons 4.3, 4.4, 11.6)
CAP = (CTX * FLASH_IN + ANS * FLASH_OUT) / 1e6 * USD_INR             # one attempt at config.py's budgets (lesson 2.5)
LANE_H = 1.5
LANE_RS = {k: v * LANE_H * sc.USD_INR for k, v in sc.HOURLY.items()}
assert sc.USD_INR == USD_INR
RUN_LIST = (HERE / "RUN_LIST.md").read_text(encoding="utf-8")
for figure in (f"Rs {TYPICAL:.2f}", f"Rs {CAP:.2f}", f"Rs {LANE_RS['small']:.2f}", f"Rs {LANE_RS['medium']:.2f}",
               f"Rs {sc.HOURLY['small'] * sc.USD_INR:.2f}", f"Rs {sc.HOURLY['medium'] * sc.USD_INR:.2f}", f"{N_OBJECTS} objects",
               f"--max-instances={SQUEEZE}", f"--max-instances={MAXI}", f"`{OBJECT}`"):
    assert figure in RUN_LIST, figure
for k in RECORDED:
    assert f"`data/{k}.txt`" in RUN_LIST, k
for name, code in (("trace", PY_TRACE), ("sub", PY_SUB), ("records", PY_RECORDS), ("api", PY_API), ("precheck", PY_PRECHECK),
                   ("burst_log", PY_BURST_LOG), ("burst_metrics", PY_BURST_METRICS)):
    assert code in RUN_LIST, f"RUN_LIST.md's copy of the {name} cell is not the page's"
for k in ("note", "squeeze", "corpus", "restore", "retire"):
    assert CELLS[k] in RUN_LIST, f"RUN_LIST.md's {k} commands are not the page's"

# ------------------------------------------------------------------ the numbers the prose states
STATS = {
    "TOPIC": TOPIC, "DLQ_TOPIC": DLQ_TOPIC, "SUB": SUB, "DLQ_SUB": DLQ_SUB, "EVENT": EVENT, "PAYLOAD": PAYLOAD,
    "BACKLOG_MIN": str(BACKLOG_S // 60), "BACKLOG_FOR_MIN": WORDS.get(BACKLOG_FOR // 60, str(BACKLOG_FOR // 60)),
    "ACK": str(ACK), "MIN_BO": str(MIN_BO), "MAX_BO": str(MAX_BO), "ATTEMPTS": str(ATTEMPTS), "ATTEMPTS_W": WORDS[ATTEMPTS],
    "INGEST_SA": INGEST_SA, "PUSH_URL": PUSH_URL, "OBJECT": OBJECT, "OBJECT_ID": OBJECT.replace("/", "~"), "NOTE_NAME": NOTE_NAME,
    "CONC": str(CONC), "MAXI": str(MAXI), "MAXI_W": WORDS[MAXI], "TIMEOUT": str(TIMEOUT), "IN_FLIGHT": str(IN_FLIGHT),
    "SQUEEZE": str(SQUEEZE), "SQUEEZE_W": WORDS[SQUEEZE], "N_OBJECTS": str(N_OBJECTS), "N_OBJECTS_W": WORDS[N_OBJECTS],
    "N_OBJECTS_WC": WORDS[N_OBJECTS].capitalize(), "N_ACME": str(len(CORPUS["acme"])), "N_GLOBEX": str(len(CORPUS["globex"])),
    "N_ZETA": str(len(CORPUS["zeta"])), "ROUNDS_SQ": str(ROUNDS_SQ), "ROUNDS_FULL": str(ROUNDS_FULL),
    "N_CHUNKS": str(N_CHUNKS), "N_CHUNKS_W": WORDS[N_CHUNKS], "LOCATORS": ", ".join(f"<code>{x}</code>" for x in LOCATORS),
    "CITE_POS": str(CITE_POS), "QUESTION": html.escape(QUESTION), "N_DECLARED_W": WORDS[N_DECLARED],
    "N_DECLARED_WC": WORDS[N_DECLARED].capitalize(), "N_DEFAULTED_W": WORDS[N_DEFAULTED],
    "RET_DAYS": str(G["retention_days"]), "RET_DAYS_W": WORDS[G["retention_days"]], "RET_S": f"{G['retention_days'] * DAY:,}",
    "EXP_DAYS": str(G["expiration_days"]), "EXP_S": f"{G['expiration_days'] * DAY:,}", "RET_MIN": G["retention_min"],
    "RET_MAX": str(G["retention_max_days"]), "ACK_CODES": G["ack_codes"], "SAMPLE_S": str(G["sample_s"]),
    "VISIBLE_S": str(G["visible_s"]), "PENDING_S": str(G["pending_s"]), "PENDING_X": G["pending_x"],
    "DLQ_MIN": str(DLQ_BOUND_MIN), "KAFKA_H": str(KAFKA["retention_hours"]), "RETENTION_DAYS": str(RETENTION_DAYS),
    "COUNTED": ", ".join(f"<code>ingest_{x}</code>" for x in COUNTED), "N_COUNTED_W": WORDS[len(COUNTED)],
    "READ_ON": READ_ON, "SETTINGS_TABLE": SETTINGS_TABLE, "KAFKA_TABLE": KAFKA_TABLE, "SOURCES": SOURCES,
    "NEXT_TITLE": html.escape(MANIFEST["modules"]["08"]["lessons"]["8.2"]["name"]),
    **{f"URL_{k.upper()}": v for k, v in GOOGLE.items()},
}
assert N_DECLARED == 5 and N_DEFAULTED == 5 and ROUNDS_SQ == 7 and ROUNDS_FULL == 2 and DLQ_BOUND_MIN == 110   # five since 13 October 2026


def subst(text: str) -> str:
    """Every %%NAME%% in a part: a code window, or a number computed above."""
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: {TOPIC} -> {SUB} (ack {ACK} s, {MIN_BO}-{MAX_BO} s, {ATTEMPTS} attempts), worker {CONC} x {MAXI}; the note {N_CHUNKS} chunks "
      f"({', '.join(LOCATORS)}); the burst {N_OBJECTS} objects, {ROUNDS_SQ} rounds of {SQUEEZE} | {N_STAND_INS} lane-cell runs "
      f"passed against stand-ins | the trace panel's script agrees with the build (node)")
