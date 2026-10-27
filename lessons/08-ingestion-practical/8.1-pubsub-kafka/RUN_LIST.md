# Lesson 8.1 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/08-ingestion-practical/8.1-pubsub-kafka/data/`. Record each file once from your
lane, replace every identifier with the course's placeholders, then rebuild and check:

    python pagekit/build.py 8.1 && python pagekit/check_lesson.py 8.1 && python pagekit/audit_pages.py 8.1

Everything else on the page is computed from the kit when the page builds: the note's 3 chunks (the worker's own
`_chunk()`, run on the note), the burst's 31 objects (`evals/upload.sh`'s rule on the corpus), `make ingest-corpus`'s
own lines, the settings and Kafka tables, the trace panel, and Google's defaults (dated in `build.py`). The seven
Python cells below were run against stand-in Google APIs when the page was built, so their code is tested; what they
print on a lane is what this list records. The build holds this file to the page: every command below is the page's
own, character for character, or the build stops.

## Before the first run

- **The batch:** batch 3 of the cohort plan (Mon 16 - Wed 18 Nov), in one lane session with lesson 8.2: about 3.5
  hours together, about 1.5 of them for this lesson.
- **The lane:** deployed by lesson 0.3's `make plan` / `make up` in the one shape (`MANAGED_MIRROR=both`, acme's
  `data_region` `any`, so the note is mirrored to acme's two managed stores), with `make ingest-corpus` done and the
  handbook at version 1, as lessons 1.6 and 6.3 leave it. Run 6 checks that before the burst moves anything.
- **Where:** the operator shell (Cloud Shell or the workstation), in the kit (`~/deploy_module_rag`), after the page's
  shared setup block (lesson 1.1's), which exports `PROJECT`, `REGION=asia-south1`, `TENANT=acme`, `ME`, `NUMBER` and
  `API` and defines `tok`. Keep one shell for the whole session: runs 8 and 9 read `BURST_SINCE`, which the corpus
  cell exports.
- **First:** pin acme to the kit's index, as the setup section says:
  `make tenant-backend PROJECT=$PROJECT TENANT=acme RETRIEVAL_BACKEND=vector`. Runs 1 and 5 need it: the answer must
  come from the kit's rows, where the worker writes the note first. Put the pin back (`RETRIEVAL_BACKEND=rag_engine`)
  after run 11, with the setup's second window (not recorded).
- **What to record:** what the terminal shows for the cell, stdout and stderr together, with nothing trimmed but
  secrets. Define a scrub once in the shell and pipe each recording through it, for example
  `{ <the cell> ; } 2>&1 | scrub > ~/lesson-8.1/trace_upload.txt`:

```bash
mkdir -p ~/lesson-8.1
scrub() { sed -e "s/$PROJECT/documind-ai-YOUR-ID/g" -e "s/$NUMBER/NUMBER/g" -e "s/$ME/you@your-company.com/g" -e "s#$HOME#/home/you#g"; }
```

- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER` (it is in the push endpoint and in the
  URLs gcloud prints); your email `you@your-company.com`; home directory `/home/you`. The cells already shorten the
  hashes they print (a `doc_key` to `acme_` and 8 characters, a fingerprint to 8); shorten any other SHA-256 the same
  way, with `...`. Object generations, revision names, times and counts may stay. `check_lesson.py` refuses a real
  project id, a project number in a URL or resource path, a personal mailbox, and every string in `.publish-deny`.

## The runs, in order

| # | Data file | Page step | Time | Cost |
|---|---|---|---|---|
| 1 | `data/trace_upload.txt` | 3, the note, then `make ingest-one` | a minute | 3 short chunks embedded: a fraction of a paisa |
| 2 | `data/trace_timeline.txt` | 5, the trace over REST | seconds | none: one Cloud Storage read, one Cloud Logging read |
| 3 | `data/subscription_rest.txt` | 5, the subscription and the topic | seconds | none: two Pub/Sub reads |
| 4 | `data/trace_records.txt` | 6, the records in Firestore | seconds | a few Firestore reads |
| 5 | `data/trace_api.txt` | 6, the ledger and one answer | under a minute | one answer: about Rs 0.45, at most Rs 2.33 |
| 6 | `data/burst_precheck.txt` | 7, the corpus against the ledger | seconds | 31 Firestore reads |
| 7 | `data/burst_squeeze.txt` | 7, the ceiling to 5 | a minute | none |
| - | (not recorded) | 7, `make ingest-corpus` | a minute | deliveries only: every object a duplicate |
| 8 | `data/burst_requests.txt` | 7, the request log, two minutes after the upload | seconds | none: Cloud Logging reads |
| 9 | `data/burst_metrics.txt` | 7, Pub/Sub's metrics, three minutes after | seconds | none: Cloud Monitoring reads |
| 10 | `data/burst_restore.txt` | 7, the ceiling back to 30, then `make dlq` | a minute | none |
| 11 | `data/trace_retire.txt` | 9, `make retire` | seconds | none |

Step 3's look at the UI (the Versions row and one question in the Chat page) is not recorded; its question is one
more answer.

**Where the rupees come from.** `shared/prices.py`: gemini-3.6-flash at $1.50 in and $7.50 out per million tokens, Rs
85 to the dollar. The course's typical answer, 2,000 tokens in and 300 out (as lessons 4.3, 4.4 and 11.6 price it), is
Rs 0.45; `services/rag-api/config.py`'s budgets cap one attempt at 8,000 tokens in and 2,048 out, Rs 2.33. Run 5
and the UI question are two answers: about Rs 0.90. The note's 3 chunks are a few hundred characters of
embedding, a fraction of a paisa at the price lesson 8.3 states. The DLP scan and the two managed mirrors' copies of
one short note are not priced here. The burst calls no model at all: 31 objects, every one a duplicate, if run 6
says so. The larger line is the lane's standing cost: about 1.5 hours at Rs 44.05 an hour on the SMALL shard
`vector.tf` declares for a new index, Rs 66.08 (Rs 111.10 an hour, Rs 166.64, on MEDIUM, which only an index
created before 8 October 2026 can have), from `lessons/00-setup/standing_cost.py`. The cohort plan budgeted "under Rs
5 and about 1.5 lane hours".

The page's prose states what each recording should show, read from the kit's code; the expectations are listed under
each run. If a recording disagrees, the recording is right: say so, and the prose changes with it.

### 1. `data/trace_upload.txt` (step 3)

```bash
cat > /tmp/pubsub_trace_note.md <<EOF
# Night gate note

A note for lesson 8.1's trace, uploaded at $(date -u +%Y-%m-%dT%H:%M:%SZ). Every fact in it is invented.

## NG-01 - The night gate

After 9 pm, couriers deliver to gate 3 of the Bhiwandi depot. The parcel is signed for at the security desk, and
the duty officer enters it in the green register before the gate is closed.

## NG-02 - A refused parcel

A parcel refused at gate 3 goes back to the hub and comes again the next evening, at most three times. After the
third refusal it waits at the hub for the sender to collect.
EOF
make ingest-one PROJECT=$PROJECT TENANT=acme FILE=/tmp/pubsub_trace_note.md
```

Expect gcloud's copy line, `>> gs://documind-ai-YOUR-ID-uploads/acme/pubsub_trace_note.md - waiting for the worker (up to 5 min)`,
then `>> indexed: acme_...` followed by `3` and `1`, tab-separated: the version's `doc_key`, 3 chunks and one page.
Shorten the `doc_key`'s hash to 8 characters and `...`. Then, in the UI, signed in as yourself: Documents, Versions
shows `acme/pubsub_trace_note.md` `indexed`, chunks 3, reused 0, embedded 3; in Chat, ask
"After 9 pm, where do couriers deliver at the Bhiwandi depot, and who signs for the parcel?" and tell me whether the answer names gate 3 and the security desk and cites the note: step 3's
prose says it does.

### 2. `data/trace_timeline.txt` (step 5)

A minute or more after run 1 (the cell's window is fixed to the ten minutes after the object's creation, so a later
run reads the same lines):

```bash
python - <<'PY'
import datetime as dt, json, os, subprocess, urllib.parse, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P, NAME = os.environ["PROJECT"], "acme/pubsub_trace_note.md"
TOKEN = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()


def api(url, body=None):
    """GET one Google API URL, or POST it a JSON body, with the operator's token; returns the parsed JSON."""
    req = urllib.request.Request(url, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=60))


def when(stamp):
    """An RFC 3339 time from a Google API as a UTC datetime (nanoseconds cut to microseconds)."""
    head, _, frac = stamp.rstrip("Z").partition(".")
    return dt.datetime.fromisoformat(f"{head}.{(frac + '000000')[:6]}+00:00")


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
    print(f"no ingest_ok for generation {gen} between {first} and {last}: Cloud Logging can lag a minute; run this again")
PY
```

Expect the object's line (its generation, a size of about 520 bytes, its content type, its creation time; tell me the
content type, which the page does not name), `seconds after the object was created:`, then in time order one
`POST 200, latency ... s (Cloud Run's request log)`, `mirror_ok  store rag_engine  op upsert` and `mirror_ok  store
vertex_search  op upsert` (acme's policy is `any` and the mirror is `both`), `ledger_fingerprint  versions ...` and
`ingest_ok  chunks 3  reused 0  embedded 3  generation ...`, and last `ingest_ok's generation equals the object's:
True; doc_key acme_...`. A `mirror_failed` or `mirror_no_store` line instead of a `mirror_ok` is a fact about the lane:
record it and tell me. So is a second POST in the window, from some other upload.

### 3. `data/subscription_rest.txt` (step 5)

```bash
python - <<'PY'
import json, os, re, subprocess, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P = os.environ["PROJECT"]
TOKEN = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()


def api(url, body=None):
    """GET one Google API URL, or POST it a JSON body, with the operator's token; returns the parsed JSON."""
    req = urllib.request.Request(url, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=60))


def short(value):
    """A field's value on one line: nested settings flattened, a field the API left out said in words."""
    if value is None:
        return "(absent)"
    if isinstance(value, dict):
        return ", ".join(f"{k} {short(v)}" for k, v in value.items()) or "{} (set, and empty: never expires)"
    return str(value)


sub = api(f"https://pubsub.googleapis.com/v1/projects/{P}/subscriptions/documind-ingest-push")
top = api(f"https://pubsub.googleapis.com/v1/projects/{P}/topics/documind-ingest")
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
      f"{short(top.get('messageRetentionDuration'))}")
PY
```

Expect `subscription documind-ingest-push, topic documind-ingest, state ACTIVE`, then ten field lines. Five say `eventarc.tf`:
`pushConfig` (the endpoint `https://documind-ingest-NUMBER.asia-south1.run.app` once scrubbed, the token's
`serviceAccountEmail` `documind-ingest-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com`, perhaps an `audience`),
`ackDeadlineSeconds 600`, `retryPolicy minimumBackoff 10s, maximumBackoff 600s`, `deadLetterPolicy` (the topic
`projects/documind-ai-YOUR-ID/topics/documind-ingest-dlq`, `maxDeliveryAttempts 12`) and `expirationPolicy {} (set, and
empty: never expires)` - the kit declares it since 13 October 2026, so run `make plan` and apply before this read; a lane
applied earlier shows Google's `ttl 2678400s` there instead. Five say `Google`: `messageRetentionDuration 604800s`,
`retainAckedMessages (absent)`, `enableMessageOrdering (absent)`, `enableExactlyOnceDelivery (absent)` and `filter (absent)`.
Last the topic, `messageRetentionDuration Google (absent)`.
If the API reports a switch as `False` instead of leaving it out, or reports a retention or a time to live that is
not Google's documented default, record it as it is: step 5's prose follows the recording.

### 4. `data/trace_records.txt` (step 6)

```bash
python - <<'PY'
import json, os, subprocess, urllib.parse, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
P, NAME = os.environ["PROJECT"], "acme/pubsub_trace_note.md"
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
print(f"ledger/acme: fingerprint {str(led.get('fingerprint'))[:8]}..., versions {led.get('versions')}, last_event {led.get('last_event')}")
PY
```

Expect `the object:  generation ...`, then `sources/acme~pubsub_trace_note.md: indexed, generation ... (the object's: yes), chunks
3, reused 0, embedded 3`, `documents/acme_...: indexed, generation ... (the object's: yes), chunks 3`, `chunks
of this version: 3, 3 current, locators preamble, NG-01, NG-02` and `ledger/acme: fingerprint ..., versions ...,
last_event ingest_ok`. A `NO` anywhere, or a `FailedPrecondition` naming an index, is a finding: tell me.

### 5. `data/trace_api.txt` (step 6)

```bash
TOKEN="$(tok "$API")" python - <<'PY'
import json, os, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
API, TOKEN, NAME = os.environ["API"], os.environ["TOKEN"], "acme/pubsub_trace_note.md"
QUESTION = "After 9 pm, where do couriers deliver at the Bhiwandi depot, and who signs for the parcel?"


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
print(f"  answerable {ans['answerable']}, backend {s.get('retrieval_backend')}, pool {s.get('pool')}, from the index {s.get('vector_chunks')}")
PY
```

Expect `GET /v1/sources: acme/pubsub_trace_note.md indexed, generation ..., chunks 3, embedded 3, held in rag_engine,
vertex_search`, then `POST /v1/query:` and the answer's first 160 characters (gate 3, the security desk), a line
`cites acme:...#1: ...` quoting the NG-01 section, and `answerable True, backend vector, pool ..., from the index ...`.
If the answer does not cite the note, or cites it at another position, record it as it is and tell me.

### 6. `data/burst_precheck.txt` (step 7)

```bash
python - <<'PY'
import hashlib, os, warnings
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
    print("  differs:", line)
PY
```

Expect `acme: 21 objects`, `globex: 3 objects`, `zeta: 7 objects` and `31 of 31 files are the version the ledger
holds current: every delivery will be a duplicate`. If any line says `differs`, stop: do not run the burst, and send
me the output. The page tells learners the same. (The town hall goes up as `.mp4` if your clone has lesson 7.5's
video; the count is the same.)

### 7. `data/burst_squeeze.txt` (step 7)

```bash
gcloud run services update documind-ingest --region "$REGION" --project "$PROJECT" --max-instances=5
gcloud run services describe documind-ingest --region "$REGION" --project "$PROJECT" \
  --format='yaml(status.latestReadyRevisionName,spec.template.metadata.annotations)' | grep -E 'latestReadyRevisionName|maxScale'
```

Expect gcloud's deploy lines, ending with the revision it deployed serving 100 percent of traffic and the service's
URL, then grep's two lines: `autoscaling.knative.dev/maxScale: '5'` and `latestReadyRevisionName: documind-ingest-...`.
This is a new revision of the worker with the same image and environment (`--max-instances` is revision-level), so
the lane runs at 5 instances until run 10.

Then, not recorded, in the same shell:

```bash
export BURST_SINCE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"; echo "BURST_SINCE=$BURST_SINCE"
make ingest-corpus PROJECT=$PROJECT
```

The page computes this output from `upload.sh` and the corpus: the `BURST_SINCE=` line, make's echo
`PROJECT_ID=documind-ai-YOUR-ID bash evals/upload.sh`, the project and bucket lines, `==> acme (21 files) -> ...`,
`==> globex (3 files) -> ...` and `==> zeta (7 files) -> ...` with their file names and gcloud's copy lines, then the
closing lines. Tell me if gcloud printed anything other than its copy progress.

### 8. `data/burst_requests.txt` (step 7)

Two minutes after the corpus cell:

```bash
python - <<'PY'
import collections, datetime as dt, json, os, statistics, subprocess, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P, SINCE = os.environ["PROJECT"], os.environ["BURST_SINCE"]
TOKEN = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()


def api(url, body=None):
    """GET one Google API URL, or POST it a JSON body, with the operator's token; returns the parsed JSON."""
    req = urllib.request.Request(url, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=60))


def when(stamp):
    """An RFC 3339 time from a Google API as a UTC datetime (nanoseconds cut to microseconds)."""
    head, _, frac = stamp.rstrip("Z").partition(".")
    return dt.datetime.fromisoformat(f"{head}.{(frac + '000000')[:6]}+00:00")


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
print("the worker's verdicts: " + (", ".join(f"{k} {v}" for k, v in sorted(verdicts.items())) or "none"))
PY
```

Expect `deliveries to documind-ingest since ...:` with a count of 31 plus one for each refusal, an `HTTP 200:` line
counting 31 (one or two more would be redeliveries, which at-least-once allows), possibly an `HTTP 429:` line, the
ten-second slices, and `the worker's verdicts: ingest_duplicate 31`. A 5xx, or any verdict but `ingest_duplicate`,
is a finding: record it and tell me, because the page says neither should appear.

### 9. `data/burst_metrics.txt` (step 7)

At least three minutes after the corpus cell (Pub/Sub's metrics are sampled each minute and can take two more to
appear):

```bash
python - <<'PY'
import datetime as dt, json, os, subprocess, urllib.parse, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P, SINCE = os.environ["PROJECT"], os.environ["BURST_SINCE"]
TOKEN = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()


def api(url, body=None):
    """GET one Google API URL, or POST it a JSON body, with the operator's token; returns the parsed JSON."""
    req = urllib.request.Request(url, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=60))


def when(stamp):
    """An RFC 3339 time from a Google API as a UTC datetime (nanoseconds cut to microseconds)."""
    head, _, frac = stamp.rstrip("Z").partition(".")
    return dt.datetime.fromisoformat(f"{head}.{(frac + '000000')[:6]}+00:00")


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


backlog = minutes("pubsub.googleapis.com/subscription/num_undelivered_messages", SUB.format("documind-ingest-push"), "ALIGN_MAX").get("all", {})
oldest = minutes("pubsub.googleapis.com/subscription/oldest_unacked_message_age", SUB.format("documind-ingest-push"), "ALIGN_MAX").get("all", {})
pushes = minutes("pubsub.googleapis.com/subscription/push_request_count", SUB.format("documind-ingest-push"), "ALIGN_DELTA", "response_class")
dead = minutes("pubsub.googleapis.com/subscription/dead_letter_message_count", SUB.format("documind-ingest-push"), "ALIGN_DELTA").get("all", {})
dlq = minutes("pubsub.googleapis.com/subscription/num_undelivered_messages", SUB.format("ingest-dlq-sub"), "ALIGN_MAX").get("all", {})
active = minutes("run.googleapis.com/container/instance_count", RUN, "ALIGN_MAX").get("all", {})
named = ("ack", "remote_server_4xx", "remote_server_5xx")
print(f"{'UTC':5}  {'backlog':>7}  {'oldest':>7}  {'ack':>4}  {'4xx':>4}  {'5xx':>4}  {'other':>5}  {'instances':>9}")
for m in sorted(set(backlog) | set(oldest) | set(active) | {k for v in pushes.values() for k in v}):
    other = sum(v.get(m, 0) for k, v in pushes.items() if k not in named)
    print(f"{m}  {backlog.get(m, 0):7.0f}  {oldest.get(m, 0):6.0f}s  " + "  ".join(f"{pushes.get(k, {}).get(m, 0):4.0f}" for k in named)
          + f"  {other:5.0f}  {active.get(m, 0):9.0f}")
print(f"forwarded to the dead-letter topic in the window: {sum(dead.values()):.0f}")
print(f"ingest-dlq-sub undelivered, the last sample: {dlq[max(dlq)]:.0f}" if dlq else "ingest-dlq-sub: no sample in the window")
PY
```

Expect the header and one line a minute from two minutes before `BURST_SINCE`: the backlog rising and falling to 0,
the oldest message's age in seconds, `ack` adding up to about 31, `4xx` matching run 8's 429s, `5xx` and `other` at 0,
and `instances` at 5 or under (a minute just over is allowed: Google notes the ceiling can be exceeded briefly). Then
`forwarded to the dead-letter topic in the window: 0` and `ingest-dlq-sub undelivered, the last sample: 0` (or `no sample in
the window`: tell me which). If the burst's last minute is missing, wait a minute and record again.

### 10. `data/burst_restore.txt` (step 7)

```bash
gcloud run services update documind-ingest --region "$REGION" --project "$PROJECT" --max-instances=30
gcloud run services describe documind-ingest --region "$REGION" --project "$PROJECT" \
  --format='yaml(status.latestReadyRevisionName,spec.template.metadata.annotations)' | grep -E 'latestReadyRevisionName|maxScale'
make dlq PROJECT=$PROJECT
```

Expect the deploy lines, `autoscaling.knative.dev/maxScale: '30'` and the newer revision's name, then make's echo of the
`gcloud pubsub subscriptions pull ingest-dlq-sub ...` line and an empty listing (gcloud may say `Listed 0 items.`; record
what it prints).

### 11. `data/trace_retire.txt` (step 9)

```bash
make retire PROJECT=$PROJECT SOURCE=acme/pubsub_trace_note.md
```

Expect one JSON line, `{"event": "reconcile_withdrawn", "gcs_uri": "gs://documind-ai-YOUR-ID-uploads/acme/pubsub_trace_note.md",
"fingerprint": "...", "retired_doc_keys": ["acme_..."], "retired_ids": [...], "retired_chunks": 3, "datapoints_removed": 3,
"note": "..."}`, with its 3 retired ids, which left the index too (a lane on a kit from before 13 October 2026 prints no
`datapoints_removed`: tell me if yours does not). Shorten every hash in it to 8 characters and `...`. Then put acme's pin back with the setup's second
window, and delete `/tmp/pubsub_trace_note.md`.
