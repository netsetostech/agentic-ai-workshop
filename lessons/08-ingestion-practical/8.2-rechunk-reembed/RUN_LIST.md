# Lesson 8.2 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/08-ingestion-practical/8.2-rechunk-reembed/data/`. Record each file once from your
lane, replace every identifier with the course's placeholders, then rebuild and check:

    python pagekit/build.py 8.2 && python pagekit/check_lesson.py 8.2 && python pagekit/audit_pages.py 8.2

Everything else on the page is computed from the kit when the page builds: the handbook's chunks at every pair (both
twins, held equal), step 1's explorer (node runs it against the kit), the twin test's output on the kit and on copies
of the two files edited by the page's own `sed` lines, the measuring cell (step 4), the planner cell over a stand-in
lane (step 8), and every rupee. The build holds this file to the page: every command below is the page's own,
character for character, or the build stops.

## Before the first run

- **The batch:** batch 3 of the cohort plan (Mon 16 - Wed 18 Nov), in the same lane session as lesson 8.1, after its
  runs: about 3.5 hours together, about 2 of them for this lesson.
- **The lane:** deployed by lesson 0.3's `make plan` / `make up` in the one shape, with `make ingest-corpus` done and
  the handbook at version 1, as lessons 1.6, 6.3 and 8.1 leave it. The worker must be the image `make up` (or a later
  lesson's `deploy-services`) built under a commit tag, not one ending in `-c400`.
- **Where:** the operator shell (Cloud Shell or the workstation), in the kit (`~/deploy_module_rag`), after the page's
  shared setup block (lesson 1.1's), which exports `PROJECT`, `REGION=asia-south1`, `TENANT=acme`, `ME`, `NUMBER` and
  `API`. The checkout must be clean before step 5 (`git status --short` prints nothing): step 9 checks it out again.
- **First:** pin acme to the kit's index, as the setup section says:
  `make tenant-backend PROJECT=$PROJECT TENANT=acme RETRIEVAL_BACKEND=vector`. Run 7 needs it: on RAG Engine the
  answers would come from text the store cut by its own rule, and the run would not measure this lesson's change. Put
  the pin back (`RETRIEVAL_BACKEND=rag_engine`) after run 8, with the setup's second window (not recorded).
- **Not recorded, but run in order:** step 3's twin test, step 4's measuring cell, and step 5's two edits. Their
  outputs are computed by the build; if what your shell prints differs from the page beyond the test's time, stop and
  tell me.
- **What to record:** what the terminal shows for the cell, stdout and stderr together, with nothing trimmed but
  secrets. Define a scrub once in the shell and pipe each recording through it, for example
  `{ <the cell> ; } 2>&1 | scrub > ~/lesson-8.2/reindex.txt`:

```bash
mkdir -p ~/lesson-8.2
scrub() { sed -e "s/$PROJECT/documind-ai-YOUR-ID/g" -e "s/$NUMBER/NUMBER/g" -e "s/$ME/you@your-company.com/g" -e "s#$HOME#/home/you#g"; }
```

- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER`; your email `you@your-company.com`; home
  directory `/home/you`; the image's commit tag `COMMIT` (so `ingest:COMMIT` and `ingest:COMMIT-c400`). Shorten any
  SHA-256 to 12 characters and `...`, as the cells do. Revision names, generations, times and counts may stay.
  `check_lesson.py` refuses a real project id, a project number in a URL or resource path, a personal mailbox, and
  every string in `.publish-deny`.

## The runs, in order

| # | Data file | Page step | Time | Cost |
|---|---|---|---|---|
| 1 | `data/build_deploy.txt` | 5, the tagged build and its deploy | about ten minutes | Cloud Build minutes, not priced on the page |
| 2 | `data/reindex.txt` | 6, the re-issue | one to five minutes | 544 chunks embedded: Rs 0.36 |
| 3 | `data/rest_revisions.txt` | 7, the worker over REST | seconds | none: two GETs |
| 4 | `data/token_check.txt` | 7, the largest new chunk's tokens | seconds | one embedding of 368 characters: under a paisa |
| 5 | `data/reconcile.txt` | 8, the walk (plan only) and the versions view | a minute | Firestore reads and one bucket listing |
| 6 | `data/index_vs_ledger.txt` | 8, the rows and the index | seconds | the handbook's rows, a thousand or so Firestore reads; one count; one GET |
| 7 | `data/eval_live.txt` | 8, the gate on the handbook | a few minutes | 10 answers: about Rs 4.46, at most Rs 23.26 |
| 8 | `data/revert.txt` | 9, the original tag and version 1 | about five minutes | the undo embeds nothing |

Step 9's last window (the checkout put back, and the test) is computed by the build; run it, it is not recorded.

**Where the rupees come from.** The re-issue embeds 544 chunks, 1,70,348 characters, at `text-embedding-005`'s online
price of USD 0.000025 per 1,000 characters (lesson 8.3's dated module, `rag_scale.py`) and Rs 85 to the dollar: Rs
0.36. The token check is 368 characters at the same price. The gate is 10 answers at the course's typical answer, 2,000
tokens in and 300 out on gemini-3.6-flash at USD 1.50 / 7.50 per million (`shared/prices.py`): Rs 0.45 an answer,
about Rs 4.46; `services/rag-api/config.py`'s budgets cap one attempt at 8,000 tokens in and 2,048 out, Rs 2.33, so at
most Rs 23.26. Model and embedding calls together: about Rs 4.82, under the cohort plan's Rs 20. Not priced: the
build's Cloud Build minutes, the DLP scan of 555 chunks, the managed mirror's two copies of the handbook (acme's RAG
Engine corpus and data store re-import its text on the re-issue and again on the undo), and about 1,400 Firestore
writes (the page's step 8 table puts those at Rs 0.12). The larger line is the lane's standing cost: about 2 hours at
Rs 44.05 an hour on the SMALL shard `vector.tf` declares for a new index, Rs 88.10 (Rs 111.10 an hour, Rs 222.19, on
MEDIUM), from `lessons/00-setup/standing_cost.py`. The cohort plan budgeted "under Rs 20 and about 2 lane hours".

The page's prose states what each recording should show, read from the kit's code; the expectations are listed under
each run. If a recording disagrees, the recording is right: say so, and the prose changes with it.

### Step 5, not recorded: the two edits, one at a time

```bash
sed -i 's/^CHUNK_CHARS, CHUNK_OVERLAP = 2000, 200/CHUNK_CHARS, CHUNK_OVERLAP = 400, 50/' services/ingest/main.py
grep -n "^CHUNK_CHARS" services/ingest/main.py shared/documind_corpus.py
python -m unittest commands/tests/test_twin_chunker.py 2>&1 | grep -E "^(FAIL:|AssertionError|Ran |OK|FAILED)"
```

Expect three failures, the first naming both files and both pairs. Then:

```bash
sed -i 's/^CHUNK_CHARS, CHUNK_OVERLAP = 2000, 200/CHUNK_CHARS, CHUNK_OVERLAP = 400, 50/' shared/documind_corpus.py
grep -n "^CHUNK_CHARS" services/ingest/main.py shared/documind_corpus.py
python -m unittest commands/tests/test_twin_chunker.py 2>&1 | grep -E "^(FAIL:|AssertionError|Ran |OK|FAILED)"
git status --short
```

Expect `OK` and the two files listed as modified. Do not run the build until both edits are in.

### 1. `data/build_deploy.txt` (step 5)

```bash
[ -s ~/lesson82-orig-sha ] || gcloud run services describe documind-ingest --region "$REGION" --project "$PROJECT" \
  --format='value(spec.template.spec.containers[0].image)' | sed 's/.*://' > ~/lesson82-orig-sha
export ORIG_SHA="$(cat ~/lesson82-orig-sha)"; echo "the worker runs ingest:$ORIG_SHA; building ingest:$ORIG_SHA-c400"
make build deploy-services PROJECT=$PROJECT SERVICES=ingest SCRIPTS=commands/lesson-12.5.sh GIT_SHA=$ORIG_SHA-c400 \
  > ~/lesson82-build.log 2>&1
grep -E '^>> |has been deployed|^ERROR' ~/lesson82-build.log
gcloud run services describe documind-ingest --region "$REGION" --project "$PROJECT" --format='value(spec.template.spec.containers[0].image,status.latestReadyRevisionName)'
```

Expect `the worker runs ingest:COMMIT; building ingest:COMMIT-c400`; make's `>> building
asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/ingest:COMMIT-c400 from services/ingest` and `>>
commands/lesson-12.5.sh (DEPLOY block)` lines; gcloud's `Service [documind-ingest] revision [...] has been deployed
and is serving 100 percent of traffic.`; the operators' `>> ... may mint tokens as ...` lines; and the describe line,
`asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/ingest:COMMIT-c400` and the new revision's name. If
`ORIG_SHA` already ends in `-c400`, stop: `~/lesson82-orig-sha` was written after an earlier edited deploy; set it to
the commit tag `make up` used before you go on. Keep `~/lesson82-build.log` until the run is accepted.

### 2. `data/reindex.txt` (step 6)

```bash
python - <<'PY'
import hashlib, os
v1 = open("evals/corpus/acme/hr_policy_2026.md", "rb").read()
r4 = b"<!-- r4 -->\n" + v1                     # version 1's text behind a comment both chunkers drop: new bytes
path = os.path.expanduser("~/hr_policy_2026_r4.md")
open(path, "wb").write(r4)
print(path, "| version key acme_" + hashlib.sha256(r4).hexdigest()[:12] + "... | version 1's acme_" + hashlib.sha256(v1).hexdigest()[:12] + "...")
PY
make reindex PROJECT=$PROJECT TENANT=acme FILE=$HOME/hr_policy_2026_r4.md NAME=hr_policy_2026.md
```

Expect `/home/you/hr_policy_2026_r4.md | version key acme_48f9a1d2929b... | version 1's acme_497809ffbaa6...`;
gcloud's copy lines and `>> gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md - waiting for the worker (up to 5
min)`; then `>> event doc_key chunks reused embedded retired effective_from` and the worker's line: `ingest_ok`,
`acme_48f9a1d2929b...`, 555 chunks, 11 reused, 544 embedded, 283 retired, no effective date; then `>> retired (doc_keys,
chunks, expire days):` with version 1's key, 283 and 30; and the gate's hint. Shorten the full keys gcloud prints to 12
characters and `...`. If the line says anything but 555 11 544 283, stop and tell me: the page states those four, and
step 4 computes them. If no line comes in five minutes, the worker may still be on the old image: check run 1's
describe line. Then, in the UI, signed in as yourself: Documents, Versions shows the handbook at chunks 555, reused 11,
embedded 544, retired 283; tell me if any other row moved.

### 3. `data/rest_revisions.txt` (step 7)

```bash
python - <<'PY'
import json, os, subprocess, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P, R = os.environ["PROJECT"], os.environ["REGION"]
tok = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
base = f"https://run.googleapis.com/v2/projects/{P}/locations/{R}/services/documind-ingest"
def get(url):
    """One GET on the Cloud Run Admin API, as JSON."""
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"}), timeout=60))
svc = get(base)
print("the template's image:", svc["template"]["containers"][0]["image"].rsplit("/", 1)[-1])
print("latest ready revision:", svc["latestReadyRevision"].rsplit("/", 1)[-1])
for t in svc.get("trafficStatuses", []):
    print(f"traffic: {t.get('percent', 0)}% to {t.get('revision') or 'the latest ready revision'} ({t.get('type', '').rsplit('_', 1)[-1].lower()})")
revisions = sorted(get(base + "/revisions").get("revisions", []), key=lambda r: r["createTime"], reverse=True)
for r in revisions[:3]:
    print(f"  {r['name'].rsplit('/', 1)[-1]:30} {r['createTime'][:19]}  {r['containers'][0]['image'].rsplit('/', 1)[-1]}")
PY
```

Expect `the template's image: ingest:COMMIT-c400`, the latest ready revision (run 1's), one traffic line with 100%
(and `latest`), then three revisions, newest first: run 1's with `ingest:COMMIT-c400`, then the original with
`ingest:COMMIT`. If a revision's image prints as a digest (`ingest@sha256:...`) rather than a tag, record it as it is
and tell me: the page's prose says tags.

### 4. `data/token_check.txt` (step 7; the cohort plan's cut line drops it first)

```bash
python - <<'PY'
import json, os, subprocess, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from shared import documind_corpus as dc
dc.CHUNK_CHARS, dc.CHUNK_OVERLAP = 400, 50              # the pair the worker runs now, set in memory
hb = open("evals/corpus/acme/hr_policy_2026.md", encoding="utf-8").read()
chunks = dc.chunk_document({"slug": "hr_policy_2026", "doc_type": "policy", "source_uri": "gs://x", "text": hb}, "acme")
big = max(chunks, key=lambda c: len(c["text"]))
P = os.environ["PROJECT"]
tok = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
url = (f"https://us-central1-aiplatform.googleapis.com/v1/projects/{P}/locations/us-central1"
       "/publishers/google/models/text-embedding-005:predict")
body = {"instances": [{"content": big["text"], "task_type": "RETRIEVAL_DOCUMENT"}], "parameters": {"outputDimensionality": 768}}
req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                             headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
r = json.load(urllib.request.urlopen(req, timeout=60))
e = r["predictions"][0]["embeddings"]
print(f"{big['locator']}: {len(big['text'])} characters; the kit's estimate {len(big['text']) // dc.CHARS_PER_TOKEN} tokens (characters // {dc.CHARS_PER_TOKEN})")
print(f"the model read {e['statistics']['token_count']} tokens, truncated {e['statistics']['truncated']}, "
      f"{len(e['values'])} numbers back; billable characters {r.get('metadata', {}).get('billableCharacterCount')}")
PY
```

Expect `GEN-003: 368 characters; the kit's estimate 122 tokens (characters // 3)`, then the model's token count (a
number under 122), `truncated False`, `768 numbers back`, and the billable characters. If the response's shape differs
(a `KeyError`), record the error and tell me: the cell follows Google's REST reference for the predict call.

### 5. `data/reconcile.txt` (step 8)

```bash
make reconcile PROJECT=$PROJECT TENANT_ONLY=acme
make sources PROJECT=$PROJECT TENANT_ONLY=acme
```

Expect make's echo of the `reconcile.py` command, one `{"reconcile": ...}` line for each object that is not `ok`
(lesson 8.1's `acme/pubsub_trace_note.md` as `withdrawn`, "withdrawn, object kept", if its last step was run), then
`{"event": "reconcile_done", "applied": false, ...}` with `"drift": 0`. Then the versions view: the header, one row per
acme source, the handbook at 555, 11, 544, 283, and the other Markdown rows at their 2000/200 counts
(`msa_acme_2026.md` 6, `inv_2026_0412.md` 1, `annual_report_2026.md` 4, `townhall_2026_q1.md` 1), then the ledger
line. A drift above 0 means the ledger and the bucket disagree for a reason this lesson did not cause: record it and
tell me before going on.

### 6. `data/index_vs_ledger.txt` (step 8)

A few minutes after run 2, so the index's stream has caught up:

```bash
python - <<'PY'
import collections, hashlib, json, os, subprocess, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
P, R = os.environ["PROJECT"], os.environ["REGION"]
db = firestore.Client(project=P)
eq = lambda q, field, value: q.where(filter=FieldFilter(field, "==", value))
uri = f"gs://{P}-uploads/acme/hr_policy_2026.md"
v1 = "acme_" + hashlib.sha256(open("evals/corpus/acme/hr_policy_2026.md", "rb").read()).hexdigest()
rows = [s.to_dict() for s in eq(eq(db.collection("chunks"), "tenant_id", "acme"), "source_uri", uri).stream()]
for (key, current), n in sorted(collections.Counter((r.get("doc_key", "?"), bool(r.get("current"))) for r in rows).items()):
    print(f"  {key[:13]}...  {'current' if current else 'retired':8} {n:>4} rows{'  (version 1)' if key == v1 else ''}")
now = {r["locator"]: r for r in rows if r.get("current")}
old = {r["locator"]: r for r in rows if r.get("doc_key") == v1}
print(f"current: {len(now)} rows, the longest {max(len(r['text']) for r in now.values())} characters")
for loc in ("NP-03", "GEN-003"):
    print(f"  {loc:8} current hash {now[loc]['chunk_hash'][:12]}  version 1's {old[loc]['chunk_hash'][:12]}  "
          f"same vector: {list(now[loc]['embedding']) == list(old[loc]['embedding'])}")
current = int(eq(db.collection("chunks"), "current", True).count().get()[0][0].value)
tok = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
url = f"https://{R}-aiplatform.googleapis.com/v1/projects/{P}/locations/{R}/indexes"
for ix in json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"}), timeout=60)).get("indexes", []):
    print(f"index {ix['displayName']}: {int(ix.get('indexStats', {}).get('vectorsCount', 0)):,} vectors; Firestore: {current:,} current rows, all tenants")
PY
```

Expect a line per version and state: `acme_48f9a1d2...  current   555 rows`, `acme_497809ff...  retired   283 rows
(version 1)`, and any older version still inside its 30 days as retired; then `current: 555 rows, the longest 368
characters`; `NP-03` with equal hashes and `same vector: True`; `GEN-003` with different hashes and `same vector:
False`; and the index line. The index's count should equal the current rows: since 13 October 2026 a source withdrawn by
hand (lesson 8.1's note: 3) or retired by the walk leaves the index too. It exceeds them only by the chunks of a source
withdrawn on an older kit. Tell me the difference you see either way: the prose reads it. A `FailedPrecondition` naming an index means the count needs an
index the kit does not declare: record it and tell me.

### 7. `data/eval_live.txt` (step 8; the cohort plan's cut line drops it)

```bash
make eval-live PROJECT=$PROJECT SOURCE=hr_policy_2026.md
```

Expect `>> https://documind-api-NUMBER.asia-south1.run.app`, `== eval gate: LIVE ==`, `scoped to hr_policy_2026.md: 10
row(s) cite it`, the thresholds, the shape table, the latency line, and either `All thresholds met.` or the rows that
cost a point. Record it either way: the page's prose describes both outcomes, and the next rebuild says which one
happened. Note the date and time beside the file: the shape of the neighbourhood depends on what the index held then.

### 8. `data/revert.txt` (step 9)

```bash
export ORIG_SHA="$(cat ~/lesson82-orig-sha)"; echo "back to ingest:$ORIG_SHA"
make deploy-services PROJECT=$PROJECT SCRIPTS=commands/lesson-12.5.sh GIT_SHA=$ORIG_SHA > ~/lesson82-revert.log 2>&1
grep -E '^>> |has been deployed|^ERROR' ~/lesson82-revert.log
gcloud run services describe documind-ingest --region "$REGION" --project "$PROJECT" --format='value(spec.template.spec.containers[0].image,status.latestReadyRevisionName)'
make reindex PROJECT=$PROJECT TENANT=acme FILE=evals/corpus/acme/hr_policy_2026.md
```

Expect `back to ingest:COMMIT`; the deploy's `>>` lines and `has been deployed ... 100 percent of traffic`; the describe
line with `ingest:COMMIT` and a revision newer than run 1's; then `make reindex`'s copy lines and the worker's line:
`ingest_reactivated`, `acme_497809ffbaa6...`, 283 chunks, 283 reused, 0 embedded, 555 retired. An `ingest_ok` line
instead would mean version 1's rows had expired (the 30 days ran out) and the worker re-indexed it: record it and tell
me.

### Step 9, not recorded: the checkout put back

```bash
git checkout -- services/ingest/main.py shared/documind_corpus.py
grep -n "^CHUNK_CHARS" services/ingest/main.py shared/documind_corpus.py
python -m unittest commands/tests/test_twin_chunker.py 2>&1 | grep -E "^(FAIL:|AssertionError|Ran |OK|FAILED)"
git diff --quiet && echo "the checkout matches the kit again"
```

Then delete `~/hr_policy_2026_r4.md`, `~/lesson82-orig-sha` and the two logs, put acme's pin back, and, if you are
done with it, delete the `ingest:COMMIT-c400` image from Artifact Registry.
