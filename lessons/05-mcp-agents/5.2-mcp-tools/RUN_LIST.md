# Lesson 5.2 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/05-mcp-agents/5.2-mcp-tools/data/`. Record each file once from your lane, replace
every identifier with the course's placeholders, then rebuild (with the venv that has fastmcp 3.4.7: the build runs the
kit's MCP server) and check:

    python pagekit/build.py 5.2 && python pagekit/check_lesson.py 5.2 && python pagekit/audit_pages.py 5.2

Everything else on the page is computed when it builds, from the kit: the server's declarations, and the live cells
against the kit's own server on localhost with the token check, the roster, rag-api and Firestore stood in.

The cohort plan puts these runs in **batch 2** (Mon 2 - Wed 4 Nov 2026), as "5.2's doc-types box".

## Before the first run

- **The lane:** deployed by `make up` (lesson 0.3) with `make ingest-corpus` done, and acme's text rows still
  `unknown`: no `make doc-types APPLY=1` for acme since the corpus was ingested (lesson 10.4 does one). If acme already
  has a registry, run 1's seed lines say `unchanged` instead of `pin`; record it anyway and say so.
- **Where:** the operator shell (Cloud Shell or the workstation), in the kit (`~/deploy_module_rag`), after the page's
  shared setup block (lesson 1.1's), which exports `PROJECT`, `REGION=asia-south1`, `TENANT=acme`, `API` and defines
  `tok`, and checks `adc ok`: the registry and the relabel go through Application Default Credentials.
- **Order:** run 1 at the start, before the lesson's other cells; run 2 when the lesson is done. Between them the rows
  of acme carry their classes, which is what the page's step 1 panel and step 7 describe.
- **What to record:** what the terminal shows for the cell, stdout and stderr together, with nothing trimmed but
  secrets. If `make` stops with `Error 3` (BigQuery deferred a statement for rows in its streaming buffer), record that
  too, then run the last line again later and append its output.
- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER`, including in the index's resource path
  (`projects/NUMBER/locations/asia-south1/indexes/...`); your email `you@your-company.com` (the registry's `set_by` is
  your gcloud account, though the output does not print it; check anyway). Doc keys and chunk counts may stay.
  `check_lesson.py` refuses a real project id, a project number in a URL or resource path, a personal mailbox, and
  every string in `.publish-deny`.

## The runs

| # | Data file | Page step | Time | Cost |
|---|---|---|---|---|
| 1 | `data/doc_types.txt` | the box before step 3: the registry, then the relabel applied | a few minutes | no model call: writes only |
| 2 | `data/doc_types_reset.txt` | the box's last cell, when the lesson is done: the rows back to `unknown` | a few minutes | no model call: writes only |

**What the runs write.** No model is called and nothing is embedded again (on a lane whose rows carry the declared
embedding). Each run writes acme's changed chunk rows in Firestore and re-upserts their datapoints in Vector Search
from the stored vectors: about 1,600 rows on a lane holding the manifest's acme documents (the handbook alone is 283),
counted with `shared/documind_corpus.chunk_document` over `evals/manifest.json`. For each version (about 20) it also
updates the Vertex AI Search document's `doc_type` and runs a BigQuery `UPDATE` for each label, and it expires acme's
answer cache. The prices of
those writes are not in `shared/prices.py`; the cohort plan estimates the two runs at under Rs 1. Please note the bill
if it is more.

The page's prose states what each recording should show, read from the kit's code; the expectations are listed under
each run. If a recording disagrees, the recording is right: say so, and the prose changes with it.

### 1. `data/doc_types.txt` (the box before step 3)

```bash
export VECTOR_INDEX_NAME="$(gcloud ai indexes list --region="$REGION" --project="$PROJECT" \
  --filter='displayName=documind-chunks' --format='value(name)')"; echo "index: $VECTOR_INDEX_NAME"     # the index the relabel re-upserts, read off your lane
make doc-types PROJECT="$PROJECT" TENANT=acme SEED=manifest   # the registry from the manifest, the view, the plan
make doc-types PROJECT="$PROJECT" TENANT=acme APPLY=1         # the plan applied, store by store
```

(The page's copy of the cell is the one to run; this is the same text.)

Expect `index: projects/NUMBER/locations/asia-south1/indexes/...`; then, from the first `make`: one `{"seed": ...}`
line per acme object of the manifest (`"action": "pin"`, or `not_ingested` for a media object your lane does not hold),
the view (`object  label  class  pin  chunks  state`, each registered object `unknown` with its class and
`relabel N rows`, any object an earlier lesson uploaded that the manifest does not name `unregistered`), one
`{"relabel": ...}` line per version to change, and `{"event": "relabel_plan", ...}` ending in `"note": "nothing is
written without --apply (APPLY=1)"`. From the second: the view again, the same plan lines, and
`{"event": "relabel_applied", ...}` with the rows changed, `"vertex_search": "checked"` and `"fingerprint": "unchanged:
a relabel moves no doc_key; the answer cache was expired instead"`.

### 2. `data/doc_types_reset.txt` (the box's last cell, when the lesson is done)

```bash
# when you finish the lesson: acme's rows back to what the worker wrote, as lesson 5.5 expects; the registry stays
export VECTOR_INDEX_NAME="$(gcloud ai indexes list --region="$REGION" --project="$PROJECT" \
  --filter='displayName=documind-chunks' --format='value(name)')"
make doc-types PROJECT="$PROJECT" TENANT=acme RESET=1 APPLY=1
```

Expect the view (every registered object now carrying its class, `pinned`), one `{"relabel": ..., "why": "reset"}`
line per version, and `{"event": "relabel_applied", "tenant": "acme", "reset": true, ...}`. Afterwards,
`make doc-types PROJECT="$PROJECT" TENANT=acme` (not recorded) should show every registered object's label back to
`unknown`, a figure's to `figure`; lesson 5.5's step 6 depends on it.
