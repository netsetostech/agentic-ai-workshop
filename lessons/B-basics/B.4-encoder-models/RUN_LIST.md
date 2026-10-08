# Lesson B.4 - the live runs this page still needs

Three outputs on the page wait for the author's run. `pagebuild.recorded()` reads each one from this folder's `data/`
and shows a marked stand-in until the file exists; `finish()` names the ones still awaited and `check_lesson.py` notes
the count. All three come from step 7 ("One question, four clauses, scored both ways on your project"): three cells, run
once, in order, in one shell. Total cost: about Rs 0.087.

## Where and how

- Where: a bash shell on a laptop (Terminal, WSL or Git Bash) or Cloud Shell, as the page's setup section describes. No
  kit checkout is needed: every cell carries its own text.
- First, once per shell: the page's setup section. Its venv block makes or activates `~/basics-venv` (Python 3.12,
  numpy 2.5.3, google-genai 2.22.0); its second block signs in Application Default Credentials, exports `PROJECT` and
  enables `aiplatform.googleapis.com`. Then step 7's enable line, for the Ranking API:

```bash
gcloud services enable discoveryengine.googleapis.com --project "$PROJECT" \
  && echo "discoveryengine.googleapis.com is on for $PROJECT"   # the Ranking API: free to enable, billed per request
```

  It prints `discoveryengine.googleapis.com is on for <your project>`.
- Paste each cell from the built page (its copy button) or from below: they are the same text, and `build.py` fails if
  the two drift apart.
- Record what each cell prints, exactly, into the named file (UTF-8, LF line endings, no extra lines). The cells print
  no project id, number or account; if a line ever does, replace it with `documind-ai-YOUR-ID` (or `NUMBER`).
- The first two cells leave `b4_bi.json` and `b4_cross.json` in the home folder; the third reads them. Delete them
  afterwards if you like.

## 1. `data/bi_encoder.txt` - step 7, "The bi-encoder side"

- API: `aiplatform.googleapis.com` (Vertex AI), enabled by the setup block. Model `text-embedding-005` on
  `us-central1`, the kit's model, region, task types and 768 numbers.
- Cost: two embedding requests (the four clauses under `RETRIEVAL_DOCUMENT`, then the question under
  `RETRIEVAL_QUERY`), 773 characters between them, at USD 0.000025 per 1,000 characters online: about Rs 0.0016 (0.16
  paise). Price as lesson 1.3 reads it, checked 7 October 2026 at
  https://cloud.google.com/vertex-ai/generative-ai/pricing ("Embeddings for Text (Excluding Gemini Embedding)").

```bash
python - <<'PY'
import os, json, warnings
warnings.filterwarnings("ignore", category=UserWarning)
import numpy as np
from google import genai
PROJECT = os.environ["PROJECT"]
QUESTION = "Can I use my unused leave to shorten my notice period?"
CLAUSES = {   # four clauses of the kit's handbook, evals/corpus/acme/hr_policy_2026.md
    "NP-03": ("A confirmed employee at grade E3 or above serves a notice period of 60 days. Notice "
              "runs from the date the resignation is acknowledged in writing. Unused earned leave may "
              "not be set off against the notice period."),
    "PB-02": ("New joiners serve six months on probation at grade E2. During probation the notice "
              "period is 15 days for either side. Probation may be extended once, by up to three "
              "months, with written reasons."),
    "LV-01": ("Earned leave accrues at 1.75 days per completed month. A maximum of 30 days may be "
              "carried forward into the next calendar year; anything above 30 lapses on 31 December."),
    "LV-07": ("Earned leave is encashed on exit at basic pay, capped at 45 days. Leave cannot be "
              "encashed during probation and cannot be used to shorten notice."),
}
client = genai.Client(enterprise=True, project=PROJECT, location="us-central1")   # embeddings are regional, as in the kit
def embed(texts, task):
    r = client.models.embed_content(model="text-embedding-005", contents=texts,
                                    config={"output_dimensionality": 768, "task_type": task})
    return np.array([e.values for e in r.embeddings])
D = embed(list(CLAUSES.values()), "RETRIEVAL_DOCUMENT")      # the worker's side: every chunk, once, at ingest
q = embed([QUESTION], "RETRIEVAL_QUERY")[0]                  # the API's side: once per question
D = D / np.linalg.norm(D, axis=1, keepdims=True)             # length 1, so the dot product below is the cosine
q = q / np.linalg.norm(q)
scores = D @ q
print(f"text-embedding-005 on us-central1: {len(D)} clause vectors (RETRIEVAL_DOCUMENT) and 1 question vector (RETRIEVAL_QUERY), {D.shape[1]} numbers each")
print("the cosine of the question with each clause, highest first:")
for name, s in sorted(zip(CLAUSES, scores), key=lambda p: -p[1]):
    print(f"  {name}  cosine {s:.4f}")
json.dump({name: float(s) for name, s in zip(CLAUSES, scores)}, open(os.path.expanduser("~/b4_bi.json"), "w"))
print("saved ~/b4_bi.json for the comparison")
PY
```

## 2. `data/cross_encoder.txt` - step 7, "The cross-encoder side"

- API: `discoveryengine.googleapis.com` (the Ranking API), enabled by the line above. The project's owner can call it;
  the kit's API service account calls it with `roles/discoveryengine.viewer` (terraform/sa.tf). Model
  `semantic-ranker-fast-004`, ranking config `default_ranking_config` on `global`, as `retriever.rerank()` calls it,
  here over REST with an access token from ADC and the `X-Goog-User-Project` header from Google's own example.
- Cost: one rank request of 4 records is one query, at USD 1.00 per 1,000 queries (a query is up to 100 records): Rs
  0.085. Checked 7 October 2026 at https://cloud.google.com/generative-ai-app-builder/pricing ("Ranking API pricing").
- If the call fails, the cell stops with the HTTP status and the first 500 characters of Google's answer, which names
  the cause (for example the API not yet enabled on the project). Fix it and run the cell again; a failed call writes
  no file.

```bash
python - <<'PY'
import os, json, warnings
warnings.filterwarnings("ignore", category=UserWarning)
import google.auth, httpx
from google.auth.transport.requests import Request
PROJECT = os.environ["PROJECT"]
QUESTION = "Can I use my unused leave to shorten my notice period?"
CLAUSES = {   # four clauses of the kit's handbook, evals/corpus/acme/hr_policy_2026.md
    "NP-03": ("A confirmed employee at grade E3 or above serves a notice period of 60 days. Notice "
              "runs from the date the resignation is acknowledged in writing. Unused earned leave may "
              "not be set off against the notice period."),
    "PB-02": ("New joiners serve six months on probation at grade E2. During probation the notice "
              "period is 15 days for either side. Probation may be extended once, by up to three "
              "months, with written reasons."),
    "LV-01": ("Earned leave accrues at 1.75 days per completed month. A maximum of 30 days may be "
              "carried forward into the next calendar year; anything above 30 lapses on 31 December."),
    "LV-07": ("Earned leave is encashed on exit at basic pay, capped at 45 days. Leave cannot be "
              "encashed during probation and cannot be used to shorten notice."),
}
creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
creds.refresh(Request())                                   # an access token from your Application Default Credentials
url = (f"https://discoveryengine.googleapis.com/v1/projects/{PROJECT}/locations/global/"
       "rankingConfigs/default_ranking_config:rank")       # the kit's ranking_config_path(), as a REST path
body = {"model": "semantic-ranker-fast-004", "query": QUESTION,
        "records": [{"id": name, "content": text} for name, text in CLAUSES.items()],
        "topN": len(CLAUSES), "ignoreRecordDetailsInResponse": True}
r = httpx.post(url, json=body, timeout=30,
               headers={"Authorization": f"Bearer {creds.token}", "X-Goog-User-Project": PROJECT})
if r.status_code != 200:
    raise SystemExit(f"HTTP {r.status_code}: {r.text[:500]}")
records = r.json()["records"]                              # highest score first
print(f"semantic-ranker-fast-004 on global: {len(records)} records scored, highest first")
for rec in records:
    print(f"  {rec['id']}  score {rec.get('score', 0.0):.4f}")
json.dump({rec["id"]: rec.get("score", 0.0) for rec in records}, open(os.path.expanduser("~/b4_cross.json"), "w"))
print("saved ~/b4_cross.json for the comparison")
PY
```

## 3. `data/compare.txt` - step 7, "Side by side"

- API: none; it reads the two files the cells above left in the home folder. Cost: Rs 0.
- Run it after 1 and 2, in the same shell. `build.py` checks that the numbers in `compare.txt` equal those in the other
  two files, so record all three from one run.

```bash
python - <<'PY'
import json, os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from itertools import combinations
bi = json.load(open(os.path.expanduser("~/b4_bi.json")))           # the first cell: the cosines
cross = json.load(open(os.path.expanduser("~/b4_cross.json")))     # the second: the ranker's scores
by_bi = sorted(bi, key=lambda n: -bi[n])
by_cross = sorted(cross, key=lambda n: -cross[n])
print(f"{'clause':8}{'bi-encoder cosine':>19}{'rank':>6}{'cross-encoder score':>21}{'rank':>6}")
for n in by_bi:
    print(f"{n:8}{bi[n]:19.4f}{by_bi.index(n) + 1:6}{cross[n]:21.4f}{by_cross.index(n) + 1:6}")
pairs = list(combinations(by_bi, 2))
same = sum((bi[a] - bi[b]) * (cross[a] - cross[b]) > 0 for a, b in pairs)
print(f"first choice: bi-encoder {by_bi[0]}, cross-encoder {by_cross[0]}")
print(f"pairs of clauses the two put in the same order: {same} of {len(pairs)}")
print(f"spread, highest minus lowest: bi-encoder {bi[by_bi[0]] - bi[by_bi[-1]]:.4f}, "
      f"cross-encoder {cross[by_cross[0]] - cross[by_cross[-1]]:.4f}")
PY
```

## After recording

Rebuild with the Basics interpreter (its offline cells run at build time; node checks the widget), then check:

```bash
python pagekit/build.py B.4
python pagekit/check_lesson.py B.4
python pagekit/audit_pages.py B.4
```

The build's "awaiting the author's run" line and check_lesson's note disappear once all three files are in `data/`. The
step 7 prose is written to read the same whatever the scores turn out to be; read the recorded comparison against it
once (the first choices, the pairs in the same order, the spread) before the page goes out.
