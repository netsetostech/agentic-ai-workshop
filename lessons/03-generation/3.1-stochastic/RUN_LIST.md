# Lesson 3.1 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/03-generation/3.1-stochastic/data/`. Every figure the page gives for Gemini (the
distinct answers, the passes, the thought tokens, the rupees, the times, the temperature that went out) is computed
from these files when the page is built, so nothing on it changes by hand. Batch 1 of the lesson plan (section 6,
Mon 26 - Wed 28 Oct). Record each file once, then rebuild and check:

    python pagekit/build.py 3.1 && python pagekit/check_lesson.py 3.1 && python pagekit/audit_pages.py 3.1

## Before the first run

- **The lane:** up, in the one shape lesson 0.3 deploys, with `make ingest-corpus` done and `make roster` run. Nothing
  here changes the lane: the runs are reads and model calls. `SEMANTIC_CACHE` must be `off` (the default; step 6's
  first line prints it): with the answer cache on, a repeated question can be served with no model call.
- **Where:** the operator shell, in the kit (`~/deploy_module_rag`), after the page's shared setup block (lesson 1.1's),
  which exports `PROJECT`, `REGION=asia-south1`, `TENANT=acme`, `ME`, `NUMBER` and `API`, and pins acme to the kit's
  index (`make tenant-backend PROJECT=$PROJECT TENANT=acme RETRIEVAL_BACKEND=vector`). Put the pin back after run 4.
- **Python:** the shell's venv (`rag-shell-venv`) with rag-api's pins, which `make bench` needs to import
  `services/rag-api/generator.py`: Module 0 installed them. If the bench says the shell lacks one, run
  `python -m pip install -r services/rag-api/requirements.txt` and start again.
- **One shell, in order, nothing else in between:** run 4 reads the usage rows written since `T0`, so do the page's
  steps 3, 6, 7 and 8 in this order in one shell, with no other lesson's traffic on the lane meanwhile.
- **One run each:** record the first complete run of each step. Rerunning for a tidier count would make the
  measurement a choice. If a run fails part-way (a 429, an expired sign-in), rerun that whole step and record it.
- **What to record:** what the terminal shows, stdout and stderr together, through the pipe each command below carries:
  `tr` strips carriage returns, `sed` replaces your project number with `NUMBER` and your project id with
  `documind-ai-YOUR-ID`, and `tee` shows the output as it is written. The files land in `~/lesson31/`; make it once:
  `mkdir -p ~/lesson31`. Before you copy them, `grep -n "$NUMBER\|$PROJECT\|$ME" ~/lesson31/*` must print nothing.
  `check_lesson.py` refuses a real project id, a project number in a URL and every string in `.publish-deny`.
- **Then:** copy the six files from `~/lesson31/` into `lessons/03-generation/3.1-stochastic/data/` of this
  repository, rebuild and check. The build checks each file's shape, and that each `.json` and its `.txt` are one run
  (the kit's own summary lines, computed from the JSON, must be in the text); a file that does not match fails it.

## The runs, in order

| # | Data file | Page step | Time | Cost (estimated when the page was built) |
|---|---|---|---|---|
| 0 | none: the browser | 3, golden row jn-03 asked five times in the Chat page | two minutes | five streamed answers: about Rs 0.78 of input, at most Rs 7.30 |
| 1 | `data/rest_five.txt` | 6, five `/v1/query` calls, judged | about a minute | five answers: about Rs 1.01 of input, at most Rs 7.54 |
| 2 | `data/bench_levels.txt` and `data/bench_levels.json` | 7, `make bench` at LOW and HIGH | two to four minutes | ten answers: about Rs 2.02 of input, at most Rs 15.08 |
| 3 | `data/bench_temperature.txt` and `data/bench_temperature.json` | 8, the temperature of 2.0 | two to three minutes | ten answers: about Rs 2.02 of input, at most Rs 15.08 |
| 4 | `data/usage_rows.txt` | 9, the usage rows since `T0` | seconds | Rs 0: one Cloud Logging read |

In all: thirty answers, about Rs 5.82 of input and at most Rs 44.99. How the costs were computed
(`build.py`, which prints a note when this file no longer states a figure): golden row jn-03's pool on the Rs 0 lane
(`evals/decide.py`'s `LocalLane`, the six passages the gate's top_k reads, five for the Chat page), packed the way
`generator.generate()` packs it and counted by the kit's `estimate_tokens()` (four characters a token): about 1,584
prompt tokens an answer, 1,216 with five passages. Priced with `shared/prices.py` (gemini-3.6-flash, USD 1.50 in and
7.50 out per million, USD_INR 85). "Of input" is the prompt alone; "at most" adds the whole 2,048-token cap
(`max_answer_tokens`, the thinking included) to every answer, Rs 1.31 each. An answer cut off at the cap is asked
once more with 6,144 tokens of room, which adds up to Rs 3.92; HIGH thinks out of the same cap, so if a retry
happens it is likeliest there, and the bench prints a `retried` line. A typical answer thinks and writes far less than
the cap, and every run prints what it spent. The lesson plan's estimate for this lesson was about Rs 14.

The page's prose says how to read each output, from the kit's code; it states no result in advance. If a recording
shows something the prose does not expect, the recording is right: say so, and the prose changes with it.

### 0. Start the clock, then the Chat page (step 3; not recorded)

```bash
mkdir -p ~/lesson31
export T0="$(date -u +%Y-%m-%dT%H:%M:%SZ)"; echo "lesson 3.1 from $T0 (UTC): step 9 reads the usage rows written since then"
```

Then, in the browser: open `https://documind-ui-NUMBER.asia-south1.run.app`, sign in as yourself (Brain `direct` if
the sidebar offers one) and ask the question below five times, each when the last answer has finished. Check what
step 3 says you will see: five answers whose words may differ, the same passages under Sources each time, and the
sidebar's tokens and cost grown by each turn. Tell the page's editor if any of the three differs.

`I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve?`

### 1. `data/rest_five.txt` (step 6)

```bash
python - <<'PY' 2>&1 | tr -d '\r' | sed -e "s/$NUMBER/NUMBER/g" -e "s/$PROJECT/documind-ai-YOUR-ID/g" | tee ~/lesson31/rest_five.txt
import json, os, re, subprocess, sys, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = ["evals", "."]
import run_eval
from route_eval import rate
from shared.prices import USD_INR, usd
API, PROJECT = os.environ["API"], os.environ["PROJECT"]
ROW = next(r for r in run_eval.load_golden() if r["id"] == "jn-03")
TOKEN = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}",
                        f"--impersonate-service-account=documind-ui-sa@{PROJECT}.iam.gserviceaccount.com"],
                       capture_output=True, text=True, check=True).stdout.strip()
version = json.load(urllib.request.urlopen(urllib.request.Request(f"{API}/version", headers={"Authorization": f"Bearer {TOKEN}"}),
                                           timeout=30))
print(f"/version: {version['generator_model']} | prompt {version['prompt']} | semantic_cache {version['semantic_cache']}")
current = run_eval.fetch_current_shas(API, ROW["tenant"], TOKEN)          # the ledger's current versions, as the gate reads them
if current is None:
    print("[info] GET /v1/sources was unavailable: the version check is skipped")
manifest = run_eval.load_manifest_objects()
corpus = re.sub(r"\s+", " ", run_eval.haystack(run_eval.load_corpus(), ROW["tenant"]))
said, cited, passed, rupees = [], [], 0, 0.0
for run in range(1, 6):
    status, body, ms = run_eval.ask(API, ROW["question"], ROW["tenant"], "eval@documind.in", TOKEN)   # the gate's own request
    v = run_eval.row_verdict(ROW, status, body, current, manifest, corpus)                               # and its own rule
    if v["outcome"] != "ok":
        print(f"run {run}: {v['outcome']} | {v['why']}")
        continue
    passed += v["pass"]
    said.append(" ".join(body["answer"].split()))
    cited.append(frozenset(c["chunk_id"] for c in body["citations"]))
    rs = usd(body["model"], body["tokens_in"], body["tokens_out"]) * USD_INR       # tokens_out: the answer and the thinking
    rupees += rs
    print(f"run {run}: {'pass' if v['pass'] else 'FAIL'} | tokens {body['tokens_in']} in + {body['tokens_out']} out | "
          f"generate_ms {body['stages'].get('generate_ms')} | cache {body['cache_hit']} | Rs {rs:.4f}"
          + (f" | {v['why']}" if v["why"] else ""))
    for c in body["citations"]:
        print(f"       cites {c['source_uri'].rsplit('/', 1)[-1]}#{c['chunk_id'].rsplit('#', 1)[-1]}: {c['quote'][:60]!r}")
    print(f"       {said[-1][:240]}")
print(f"distinct answers {len(set(said))} of {len(said)} | cite sets {len(set(cited))} of {len(said)} | "
      f"pass {rate(passed, 5)} | Rs {rupees:.4f} for the five")
PY
```

Expect `/version: gemini-3.6-flash | prompt documind-rag@v3 | semantic_cache off`, then five `run` lines, each with
its verdict, `tokens ... in + ... out`, `generate_ms`, `cache none` and its rupees, its citations and its answer, and
last `distinct answers ... | cite sets ... | pass k/5 = ... | Rs ... for the five`. A failed answer's line ends with the
gate's own reason; record it as it is.

### 2. `data/bench_levels.txt` and `data/bench_levels.json` (step 7)

```bash
make bench PROJECT="$PROJECT" REGION="$REGION" BENCH_ARGS="--rows jn-03 --runs 5 --levels LOW,HIGH --show --report evals/reports/bench-levels.json" 2>&1 | tr -d '\r' | sed -e "s/$NUMBER/NUMBER/g" -e "s/$PROJECT/documind-ai-YOUR-ID/g" | tee ~/lesson31/bench_levels.txt
sed -e "s/$NUMBER/NUMBER/g" -e "s/$PROJECT/documind-ai-YOUR-ID/g" evals/reports/bench-levels.json > ~/lesson31/bench_levels.json
```

Expect `>> https://documind-api-NUMBER.asia-south1.run.app`, the bench's header for `1 row(s) x 1 arm(s) x 2 level(s) x
5 run(s)`, jn-03's pool line (six passages), the kit arm's prompt sha256 `543ed8060f1b...` (documind-rag@v3's), ten
answer lines, the table with a `kit LOW` and a `kit HIGH` row, the quotes lines, the `--show` section (the pool, then
each level's distinct answers), the rupees in all, `generator.py unchanged on disk; SYSTEM is the kit's again` and
`report: evals/reports/bench-levels.json`. The page's Level 0 widget shows the ten answers from the JSON once it is in.

### 3. `data/bench_temperature.txt` and `data/bench_temperature.json` (step 8)

```bash
make bench PROJECT="$PROJECT" REGION="$REGION" BENCH_ARGS="--rows jn-03 --runs 5 --temperature 2.0 --report evals/reports/bench-temperature.json" 2>&1 | tr -d '\r' | sed -e "s/$NUMBER/NUMBER/g" -e "s/$PROJECT/documind-ai-YOUR-ID/g" | tee ~/lesson31/bench_temperature.txt
sed -e "s/$NUMBER/NUMBER/g" -e "s/$PROJECT/documind-ai-YOUR-ID/g" evals/reports/bench-temperature.json > ~/lesson31/bench_temperature.json
```

Expect two arms with one prompt sha256 (`kit ... no temperature`, `edit ... temperature 2`), ten answer lines at LOW,
the table's `kit LOW` and `edit LOW` rows, and the same closing lines. The page runs step 8's report cell over the
JSON when it is built, and prints the config every call went out with.

### 4. `data/usage_rows.txt` (step 9, a minute after run 3)

```bash
python - <<'PY' 2>&1 | tr -d '\r' | sed -e "s/$NUMBER/NUMBER/g" -e "s/$PROJECT/documind-ai-YOUR-ID/g" | tee ~/lesson31/usage_rows.txt
import json, os, subprocess, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, ".")
from shared.prices import USD_INR
EVENTS = ("query", "stream", "passages")
FILTER = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND ('
          + " OR ".join(f'jsonPayload.event="{e}"' for e in EVENTS) + f') AND timestamp>="{os.environ["T0"]}"')
got = subprocess.run(["gcloud", "logging", "read", FILTER, "--project", os.environ["PROJECT"], "--limit", "200",
                      "--format=json"], capture_output=True, text=True, check=True).stdout
rows = [e["jsonPayload"] for e in json.loads(got or "[]")][::-1]          # Cloud Logging lists the newest first
for r in rows:
    print(f"{r['event']:8} {r['tenant']:5} tokens {r['tokens_in']:>5} in + {r['tokens_out']:>5} out | "
          f"Rs {(r.get('cost_usd') or 0) * USD_INR:.4f} | answerable {r['answerable']} | {r['model']} | "
          f"{r['prompt_version']} | generate_ms {r.get('generate_ms')}")
print("rows since T0: " + ", ".join(f"{e} {sum(r['event'] == e for r in rows)}" for e in EVENTS)
      + f" | tokens out {sum(r['tokens_out'] for r in rows):,} | Rs {sum(r.get('cost_usd') or 0 for r in rows) * USD_INR:.4f}")
PY
```

Expect, oldest first, five `stream` rows (run 0), five `query` rows (run 1) with the tokens run 1 printed, and two
`passages` rows (runs 2 and 3) with no tokens and Rs 0.0000, then `rows since T0: query 5, stream 5, passages 2 | tokens
out ... | Rs ...`. No row exists for the bench's twenty answers: that absence is what the step shows.

When all are in, put acme's pin back (the setup section's last window), copy the files and rebuild the page.
