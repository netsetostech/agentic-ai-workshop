# Lesson 8.3 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/08-ingestion-practical/8.3-size-ten-million/data/`. Record each file once from your
lane, replace every identifier with the course's placeholders, then rebuild and check:

    python pagekit/build.py 8.3 && python pagekit/check_lesson.py 8.3 && python pagekit/audit_pages.py 8.3

Everything else on the page (step 5's measurement, the calculator, the tables, every price) is computed from the kit
when the page builds, so these five runs are the whole list. None of them changes the lane.

## Before the first run

- **The lane:** deployed by lesson 0.3's `make plan` / `make up`, with `make ingest-corpus` done and the vector index
  deployed (lesson 0.4's smoke passes its vector-tier line). Later lessons' changes may stay: the runs read whatever
  the lane holds, and the expectations below say which numbers move with it.
- **Where:** the operator shell (Cloud Shell or the workstation), in the kit (`~/deploy_module_rag`), after the page's
  shared setup block (lesson 1.1's), which exports `PROJECT`, `REGION=asia-south1`, `NUMBER` and `API`. The page tells
  learners the pin windows are optional here; skip them.
- **What to record:** what the terminal shows for the cell, stdout and stderr together, with nothing trimmed but
  secrets.
- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER`; your email `you@your-company.com`; home
  directory `/home/you`; the corpus fingerprint shortened with `...` (the page's rule for a hash). Object generations,
  counts, times and latencies may stay. `check_lesson.py` refuses a real project id, a project number in a URL or
  resource path, a personal mailbox, and every string in `.publish-deny`.

## The runs, in order

| # | Data file | Page step | Time | Cost |
|---|---|---|---|---|
| 1 | `data/sources_acme.txt` | 3, make sources for acme | seconds | Firestore reads: one per acme source row, plus the three ledger rows |
| 2 | `data/vector_status.txt` | 3, make vector-status | seconds | none: two describes |
| 3 | `data/index_rest.txt` | 6, the index and its deployment over REST | seconds | none: two GETs |
| 4 | `data/firestore_counts.txt` | 7, nine count queries | seconds | a few Firestore reads (a count is billed by the index entries it scans, not by rows) |
| 5 | `data/ingest_latency.txt` | 7, the worker's request latencies | under a minute | none: one Cloud Logging read; writes `~/ingest-requests.json` |

The page's prose states what each recording should show, read from the kit's code; the expectations are listed under
each run. If a recording disagrees, the recording is right: say so, and the prose changes with it.

### 1. `data/sources_acme.txt` (step 3)

```bash
make sources PROJECT="$PROJECT" TENANT_ONLY=acme
```

Expect make's echo of `python services/ingest/reconcile.py --project documind-ai-YOUR-ID --report --tenant acme`, the
header (`source status gen chunks reused embed retired effective embedding indexed_at`), one row per object acme holds,
then the ledger line `{"ledger": "acme", "fingerprint": "...", "versions": ..., "last_event": ...}`. After `make
ingest-corpus` acme holds 21 objects, all `indexed`: the five Markdown documents, the twelve PDFs that have a `.md`
mirror, `posh_act_2013.pdf` (scanned, no mirror) and the three figures (`.png`, one chunk each). The town hall is
`townhall_2026_q1.mp4` instead of `.md` if you made its video in lesson 7.5. The five Markdown rows' `chunks` must equal
the page's acme table digit for digit: `hr_policy_2026` 283, `msa_acme_2026` 6, `inv_2026_0412` 1,
`annual_report_2026` 4, `townhall_2026_q1` 1. The PDF rows may differ from the table by a few chunks (Document AI's
text against pypdf's). If a Markdown row differs, stop and tell me: the page says they match.

### 2. `data/vector_status.txt` (step 3)

```bash
make vector-status PROJECT="$PROJECT" REGION="$REGION"
```

Expect two YAML blocks. The index: `displayName: documind-chunks`, `indexStats:` with `shardsCount: 1` and
`vectorsCount: '...'` (every current chunk of the three tenants, text and media), and `indexUpdateMethod:
STREAM_UPDATE`. The endpoint: `displayName: documind-endpoint` and `deployedIndexes:` with `id: documind_chunks_v1`
and its `indexSyncTime`. Run 3 must print the same vector count.

### 3. `data/index_rest.txt` (step 6)

```bash
python - <<'PY'
import json, os, subprocess, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P, R = os.environ["PROJECT"], os.environ["REGION"]
tok = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
base = f"https://{R}-aiplatform.googleapis.com/v1/projects/{P}/locations/{R}"
get = lambda path: json.load(urllib.request.urlopen(urllib.request.Request(f"{base}/{path}", headers={"Authorization": f"Bearer {tok}"}), timeout=60))
GIB, SHARD_GIB = 1 << 30, {"SHARD_SIZE_SMALL": 2, "SHARD_SIZE_MEDIUM": 20, "SHARD_SIZE_LARGE": 50}   # Google's shard sizes (step 8)
for ix in get("indexes").get("indexes", []):
    cfg, st = ix["metadata"]["config"], ix.get("indexStats", {})
    n, dims, shard = int(st.get("vectorsCount", 0)), int(cfg["dimensions"]), cfg.get("shardSize", "not stated")
    print(f"index {ix['displayName']}: {n:,} vectors of {dims}, {st.get('shardsCount', 0)} shard(s), {shard}, {ix['indexUpdateMethod']}")
    if shard in SHARD_GIB:
        used = n * dims * 4 / GIB
        print(f"  dense data {used * 1024:,.1f} MiB: {100 * used / SHARD_GIB[shard]:.3f}% of one {SHARD_GIB[shard]} GiB shard; "
              f"the shard holds {int(SHARD_GIB[shard] * GIB / (dims * 4)):,} vectors of this length")
for ep in get("indexEndpoints").get("indexEndpoints", []):
    for d in ep.get("deployedIndexes", []):
        res = d.get("dedicatedResources", {})
        print(f"deployed {d['id']}: {res.get('machineSpec', {}).get('machineType')}, replicas {res.get('minReplicaCount')} to {res.get('maxReplicaCount')}")
PY
```

Expect three lines. `index documind-chunks: N vectors of 768, 1 shard(s), SHARD_SIZE_SMALL, STREAM_UPDATE`, with N
equal to run 2's `vectorsCount`; `vector.tf` creates a new index SMALL, and an index created before the kit declared a
size keeps the one the API chose then (`SHARD_SIZE_MEDIUM`). Then `  dense data ... MiB: ...% of one 2 GiB shard; the
shard holds 699,050 vectors of this length` (on MEDIUM: `20 GiB` and `6,990,506`), with a percentage far below one.
Then `deployed documind_chunks_v1: e2-standard-2, replicas 1 to 1` (on MEDIUM: `e2-standard-16`). If `shardSize` is
missing from the response, the line says `not stated` and the dense-data line is absent: tell me, because step 6's
prose reads it.

### 4. `data/firestore_counts.txt` (step 7)

```bash
python - <<'PY'
import os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
db = firestore.Client(project=os.environ["PROJECT"])
count = lambda q: int(q.count().get()[0][0].value)          # one aggregation: billed by the index entries it reads, not by rows
eq = lambda q, field, value: q.where(filter=FieldFilter(field, "==", value))
print(f"{'tenant':7} {'chunk rows':>10} {'current':>8} {'indexed sources':>15}")
for t in ("acme", "globex", "zeta"):
    rows = eq(db.collection("chunks"), "tenant_id", t)
    print(f"{t:7} {count(rows):>10,} {count(eq(rows, 'current', True)):>8,} "
          f"{count(eq(eq(db.collection('sources'), 'tenant_id', t), 'status', 'indexed')):>15,}")
PY
```

Expect the header `tenant  chunk rows  current  indexed sources` and one line each for acme, globex and zeta. The
three `current` figures added together equal run 2's `vectorsCount` (both are every current chunk, text and media).
`chunk rows` is at least `current` on every line (a re-issue's retired rows stay until their `expire_at`). acme's
`indexed sources` equals the `indexed` rows of run 1. A `FailedPrecondition` naming an index would mean a count needs
an index the kit does not declare: tell me, and the cell changes.

### 5. `data/ingest_latency.txt` (step 7)

```bash
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-ingest" AND httpRequest.requestMethod="POST"' \
  --project="$PROJECT" --freshness=30d --limit=1000 --format=json > ~/ingest-requests.json
python - <<'PY'
import json, os, statistics, warnings
warnings.filterwarnings("ignore", category=UserWarning)
by = {}
for e in json.load(open(os.path.expanduser("~/ingest-requests.json"))):
    h = e.get("httpRequest", {})
    by.setdefault(int(h.get("status", 0)), []).append(float(str(h.get("latency", "0s")).rstrip("s") or 0))
for status, secs in sorted(by.items()):
    secs.sort()
    print(f"HTTP {status}: {len(secs):>4} deliveries, median {statistics.median(secs):.1f} s, slowest {secs[-1]:.1f} s")
taken = sorted(s for status, secs in by.items() if 200 <= status < 300 for s in secs)
if taken:
    m = statistics.median(taken)
    print(f"at 10,000,000 documents, 30 at a time, {m:.1f} s each: {10000000 * m / 30 / 86400:,.1f} days")
PY
```

Expect one line per HTTP status the worker returned in the last 30 days: `HTTP 200: N deliveries, median X s, slowest
Y s`, and possibly `HTTP 429` (Cloud Run turning a delivery away while instances start) or 5xx lines. Then `at
10,000,000 documents, 30 at a time, X s each: Y days`. The log keeps 30 days: if the lane's last ingest is older and
the cell prints nothing, ingest one document again (`make ingest-one FILE=... TENANT=acme`, in the page's table of
make targets) and record after it. Delete `~/ingest-requests.json` when the file is saved, as the page's last box says.
