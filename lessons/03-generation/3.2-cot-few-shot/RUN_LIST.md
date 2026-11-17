# Lesson 3.2 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/03-generation/3.2-cot-few-shot/data/`. Record each file once from your lane, replace
every identifier with the course's placeholders, then rebuild and check:

    python pagekit/build.py 3.2 && python pagekit/check_lesson.py 3.2 && python pagekit/audit_pages.py 3.2

The build reads more than it shows. Once `join_levels.txt`, `cot_rule.txt`, `exemplars_kit.txt` and
`exemplars_none.txt` are in, it writes the "author's lane" paragraphs under steps 6, 7 and 9, and a per-row grid of
verdicts and thought tokens under steps 6 and 7, from the lines the kit prints. Its parsers are checked at every build
against the kit's own output (prompt_bench.py on its offline test harness, route_eval.py --local), so a file it cannot
read was trimmed or recorded with another command: the build says which, and that one is re-recorded.

Batch 1 of the cohort plan (Mon 26 - Wed 28 Oct 2026).

## Before the first run

- **The lane:** deployed by lesson 0.3's `make plan` / `make up`, `make ingest-corpus` done, serving the kit this page
  was built against. Nothing in these runs deploys or changes a service. A Module 3 lane is enough: step 9 runs the
  router in your shell and needs no deployed Desk.
- **Where:** the operator shell (Cloud Shell or the workstation), in the kit (`~/deploy_module_rag`), after the page's
  shared setup block (lesson 1.1's), which activates `~/rag-shell-venv`, exports `PROJECT`, `REGION=asia-south1`,
  `TENANT=acme`, `NUMBER` and `API`, and defines `tok`. The venv must hold rag-api's pins (Module 0's install:
  `services/rag-api/requirements.txt`, google-genai 2.22.0): `make bench` imports `services/rag-api/generator.py` in
  your shell, and `--live-l1` builds google-genai clients.
- **First:** pin acme to the kit's index, as the setup section says:
  `make tenant-backend PROJECT=$PROJECT TENANT=acme RETRIEVAL_BACKEND=vector`. Put the pin back
  (`RETRIEVAL_BACKEND=rag_engine`) after run 4.
- **Order, in one sitting:** runs 1 to 8 as numbered. Run 5 reads run 4's report, and run 8 reads runs 6 and 7's.
- **What to record:** what the terminal shows for the cell, stdout and stderr together, with nothing trimmed but
  secrets. One run each: record the first complete run; re-running for a tidier result turns the measurement into a
  choice. If a run fails part-way (a 429, an expired sign-in), run the whole cell again and record that run.
- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER` (make bench prints the API's URL twice:
  `>> https://documind-api-NUMBER.asia-south1.run.app` and the bench's own header); home directory `/home/you` (the
  bench prints its report's path); email `you@your-company.com`. Times and token counts stay. `check_lesson.py`
  refuses a real project id, a project number in a URL, a personal mailbox, and every string in `.publish-deny`.

## The runs, in order

| # | Data file | Page step | Time | Cost |
|---|---|---|---|---|
| 1 | `data/ui_stream.txt` | 3, jn-03 in the Chat page, then its usage row | a minute | one answer, about Rs 0.45 |
| 2 | `data/passages_jn03.txt` | 5, jn-03's pool from /v1/passages | seconds | Rs 0.085: one Ranking API request; the route bills no tokens |
| 3 | `data/join_levels.txt` | 6, the 11 join rows at LOW, MEDIUM and HIGH | a few minutes | about Rs 15.66 to Rs 40.18 |
| 4 | `data/cot_rule.txt` | 7, the kit arm and the reasoning rule, both at LOW | a few minutes | about Rs 10.75 to Rs 23.01 |
| 5 | `data/cot_answers.txt` | 7, jn-03's two answers from run 4's report | seconds | Rs 0 |
| 6 | `data/exemplars_kit.txt` | 9, the router with the kit's 8 examples | a few minutes | about Rs 3.90, plus the arbiter's thinking |
| 7 | `data/exemplars_none.txt` | 9, the same rows with no example | a few minutes | about Rs 3.53, plus the arbiter's thinking |
| 8 | `data/exemplar_flips.txt` | 10, the two reports paired turn by turn | seconds | Rs 0 |

**Where the rupees come from.** `shared/prices.py`: gemini-3.6-flash at $1.50 in and $7.50 out per million tokens,
gemini-3.1-flash-lite at $0.25 and $1.50, Rs 85 to the dollar. A LOW answer is priced at the course's typical answer,
2,000 tokens in and 300 out (the figure lessons 4.3, 4.4 and 11.6 use): Rs 0.45. An answer asked to think or write
more (MEDIUM, HIGH, the rule's edit arm) is priced with its whole 2,048-token output cap once, thinking included:
Rs 1.56. So run 3 is about Rs 15.66 if every answer is the typical one and Rs 40.18 if the 22 MEDIUM and HIGH answers
fill their caps; run 4 is Rs 10.75 to Rs 23.01 the same way. A cut-off answer is asked again with three times the
room (`generator.generate()`), and the retry adds at most Rs 4.17; the bench's `retried` line counts them. Each pool
read is one Ranking API request at the rate lesson 2.3 states, $1 per thousand: Rs 0.085, 11 of them in runs 3 and 4
each. Runs 6 and 7 are priced from the kit's own offline run (`make exemplars LOCAL=1`), which prices the router's calls
at the scripted counts (a prompt's characters divided by four in, 30 tokens out): Rs 3.84 with the examples and
Rs 3.48 without, the difference being the eight lines on each of the 126 L1 calls. Each run also embeds the 198-row
index and the 126 questions L1 sees with text-embedding-005, about Rs 0.058 at $0.000025 per 1,000 characters (the rate
lessons 1.6 and 3.9 use), and the arbiter's thinking at LOW is billed on top: at most Rs 0.65 for each call sent to it
(48 offline; the live count is in the run's `sent to L2` line). In all, about Rs 34.38 to Rs 71.15, plus the arbiter's
thinking. The cohort plan estimated Rs 45-65. The bench's and the router's own last lines print the real figures:
please note them when you hand the files back.

The page's prose states what each recording should show, read from the kit's code; the expectations are under each
run. If a recording disagrees, the recording is right: say so, and the prose changes with it.

### 1. `data/ui_stream.txt` (step 3)

In the DocuMind UI's Chat page, signed in as yourself (the direct brain), ask exactly:
`I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve?` Then, within ten
minutes:

```bash
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="stream"' \
  --project "$PROJECT" --freshness 10m --limit 1 --format=json | python -c "
import sys, json
for e in json.load(sys.stdin):
    r = e['jsonPayload']
    print('stream | brain', r.get('brain'), '| tenant', r.get('tenant'), '| model', r.get('model'), '| pool', r.get('pool'),
          '| tokens_in', r.get('tokens_in'), '| tokens_out', r.get('tokens_out'), '| generate_ms', r.get('generate_ms'),
          '| Rs %.4f' % (85 * (r.get('cost_usd') or 0)))"
```

Expect one line: `stream | brain ui | tenant acme | model gemini-3.6-flash | pool N | tokens_in N | tokens_out N |
generate_ms N | Rs N`. Note in the review whether the answer said 45 and 60, and whether it mentioned that NP-03's 60
days are for a confirmed employee.

### 2. `data/passages_jn03.txt` (step 5)

```bash
curl -s -X POST "$API/v1/passages" -H "Authorization: Bearer $(tok "$API")" -H "Content-Type: application/json" \
  -d '{"query": "I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve?", "tenant_id": "acme", "top_k": 6}' -o /tmp/jn03_pool.json
python - <<'PY'
import json, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, "evals")
from run_eval import anchors_found, contains, load_golden
row = next(r for r in load_golden() if r["id"] == "jn-03")
body = json.load(open("/tmp/jn03_pool.json", encoding="utf-8"))
pool, usage = body["passages"], body["usage"]
print(f"{len(pool)} passages from {usage['stages'].get('retrieval_backend')}; the route's own bill: {usage['tokens_in']} tokens in, "
      f"{usage['tokens_out']} out")
for p in pool:
    text = " ".join(p["text"].split())
    found = [f for f in row["must_contain"] if contains(text, f)]
    name = p["source_uri"].rsplit("/", 1)[-1]
    print(f"  [{p['n']}] {name} {p.get('section') or 'p.' + str(p.get('page'))} | figures: {', '.join(found) or '-'} | {text[:60]}")
print("anchors in the pool:", anchors_found(row, pool))
PY
```

The page's cell is this one, verbatim. Expect `6 passages from vector; the route's own bill: 0 tokens in, 0 out`, six
passage lines, `45` beside LV-07's passage and `60` beside NP-03's, and `anchors in the pool: {'LV-07': True,
'NP-03': True}`. If an anchor is `False`, record it anyway: the page's prose covers a missing clause.

### 3. `data/join_levels.txt` (step 6)

```bash
make bench PROJECT=$PROJECT BENCH_ARGS="--shape join --levels LOW,MEDIUM,HIGH"
```

Expect `>> https://documind-api-NUMBER.asia-south1.run.app`, then the bench's header (`11 row(s) x 1 arm(s) x 3
level(s) x 1 run(s): up to 33 answers`), eleven pool lines, the kit arm with `prompt sha256 543ed8060f1b177c...` (the
text `services/rag-api/prompt_versions.json` registers as `documind-rag@v3`), 33 answer lines, the summary table with one
row each for LOW, MEDIUM and HIGH, the quote lines, any `errors`, `retried` or `fell back` lines, `Rs N in all: 33
answers, N model calls on gemini-3.6-flash`, and `generator.py unchanged on disk; SYSTEM is the kit's again`. An
unsupported level would come back as an error on its answers' rows; record that too.

### 4. `data/cot_rule.txt` (step 7)

```bash
make bench PROJECT=$PROJECT BENCH_ARGS="--shape join --levels LOW --add-rule 'Show your working in the answer: name each fact the question needs and the [N] that states it, then combine them.' --report $HOME/cot_rule.json"
```

Expect the same shape with two arms: `kit   generator.py's SYSTEM - 5 rules; no temperature` and `edit  rule added:
Show your working ... - 6 rules; no temperature`, each with its prompt sha256 (the kit's `543ed8060f1b177c...`, the edit arm's
`3f23ad647176d4fe...`, as step 4's offline cell prints them), 22 answer lines, summary rows `kit LOW` and `edit LOW`, the
total, the generator line, and `report: /home/you/cot_rule.json` (placeholder the home directory).

### 5. `data/cot_answers.txt` (step 7)

```bash
python - <<'PY'
import json, os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
report = json.load(open(os.path.expanduser("~/cot_rule.json"), encoding="utf-8"))
for a in (a for a in report["answers"] if a["id"] == "jn-03"):
    thought = sum(c.get("thought", 0) for c in a["calls"])
    visible = sum(c.get("visible", 0) for c in a["calls"])
    print(f"== {a['arm']} {a['level']}: {'pass' if a['pass'] else 'did not pass: ' + a['why']} | thought {thought} | visible {visible} "
          f"| Rs {a['cost_inr']:.4f}")
    print(a.get("answer") or a.get("error"))
    for c in a.get("cites", []):
        print(f"   quote, {c['check']}: {c['quote'][:90]}")
PY
```

Expect two blocks, `== kit LOW: ...` and `== edit LOW: ...`, each with its answer (the report keeps the first 600
characters) and its quotes with their checks. The page says the edit arm's answer carries its working; if it does
not, say so in the review.

### 6. `data/exemplars_kit.txt` (step 9)

```bash
python evals/route_eval.py --live-l1 --project "$PROJECT" --exemplars kit --report "$HOME/exemplars_kit.json"
```

This is the line `make exemplars PROJECT=$PROJECT REPORT="$HOME/exemplars_kit.json"` runs. Expect
`live: flash-lite, flash and text-embedding-005`, `187 rows scored; 20 left out (the groups of the prompt's
examples); index of 198 dev rows`, `exemplars: the kit's own, desk_routes.PROMPT_EXEMPLARS - 8 in the L1 prompt; ...`,
the route report with its intervals, the method mix, `sent to L2`, `router cost Rs N in all`, `L1 alone k/126 = ...`,
and either `the dev gates hold` or `FAIL` lines against lesson 10.4's dev gates (then the command exits 1: record it
as it is; the page reads it as a measurement).

### 7. `data/exemplars_none.txt` (step 9)

```bash
python evals/route_eval.py --live-l1 --project "$PROJECT" --exemplars none --report "$HOME/exemplars_none.json"
```

The same rows with no example: expect `exemplars: none - 0 in the L1 prompt; the rows of the kit's 8 stay out of the
score in every arm`, and the same report lines. The router cost should come in a little under run 6's.

### 8. `data/exemplar_flips.txt` (step 10)

Run the page's step 10 cell as written (a Python heredoc reading `~/exemplars_kit.json` and `~/exemplars_none.json`).
Expect two arm lines (`kit  8 examples | L1 alone ... | top-1 route ...`, `none 0 examples | ...`), two paired
blocks (`L1 alone, paired over 126 rows: ...` and `top-1 route, paired over 187 rows: ...`, each with Newcombe's
interval and the exact McNemar p), `turns where L1's route changed with the examples out: N`, and one line per such
turn. The build ran the same cell over the offline reports, where N is 0.
