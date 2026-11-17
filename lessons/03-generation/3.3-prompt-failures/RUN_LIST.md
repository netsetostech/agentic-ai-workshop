# Lesson 3.3 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/03-generation/3.3-prompt-failures/data/`. Record each file once from your lane,
replace every identifier with the course's placeholders, then rebuild and check:

    python pagekit/build.py 3.3 && python pagekit/check_lesson.py 3.3 && python pagekit/audit_pages.py 3.3

Everything else on the page is computed when it builds, from the kit: the failure desk (eight golden rows with pools of
the kit's own chunks; its JavaScript port of `row_verdict()`, `quote_check()`, `anchors_found()` and `address()` is run
in node and held equal to the kit), the rules cell, the edit cell and the SYSTEM equality cell with the kit's own test.
The four lane cells are also run at build time against a stand-in lane, so their code is tested before your lane runs
them: `run_eval.live()` against a stub API with `DOCUMIND_EVAL_PASSAGES=1`, the read cell over the stub's report with
`/v1/passages` stood in, the bench's `main()` over `generator.py` lifted with a scripted model, and the fix cell over the
bench's three reports. Batch 1 of the lesson plan (Mon 26 - Wed 28 Oct).

## Before the first run

- **The lane:** up, deployed by `make up` (lesson 0.3), with `make ingest-corpus` done and `make roster` run, serving the
  kit this page was built against. Nothing here deploys or changes the lane: the runs are model calls and reads.
- **Where:** the operator shell, in the kit (`~/deploy_module_rag`), after the page's shared setup block (lesson 1.1's),
  which exports `PROJECT`, `REGION=asia-south1`, `ME`, `NUMBER` and `API` and defines `tok`. Then pin acme to the kit's
  own index, as the setup section says: `make tenant-backend PROJECT=$PROJECT TENANT=acme RETRIEVAL_BACKEND=vector`.
  Put the pin back (`RETRIEVAL_BACKEND=rag_engine`) after run 4.
- **The venv:** `rag-shell-venv` with rag-api's packages (Module 0's install), because `make bench` imports
  `services/rag-api/generator.py` into the shell. If run 3 stops on a missing package:
  `python -m pip install -r services/rag-api/requirements.txt`. The bench's model calls use Application Default
  Credentials: the setup block's `adc ok` line must have printed.
- **Shell variables:** `DOCUMIND_EVAL_PASSAGES` unset (run 1 sets it for its own command only); `FIX1`, `FIX2` and
  `FIX3` unset until run 2 prints them.
- **Order, in one sitting:** run 1, run 2, then paste run 2's last line into the shell, run 3's three commands, run 4.
- **What to record:** what the terminal shows for the command, stdout and stderr together, with nothing trimmed but
  secrets.
- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER`, including in URLs
  (`https://documind-api-NUMBER.asia-south1.run.app`); emails `you@your-company.com`. make's echo line (`>> https://...`)
  and the bench's header carry the API's address. `grep -n "$NUMBER\|$PROJECT" data/*` before you copy, and replace what
  it finds. `check_lesson.py` refuses a real project id, a project number in a URL and every string in `.publish-deny`.

## The runs, in order

| # | Data file | Page step | Time | Cost (estimated when the page was built) |
|---|---|---|---|---|
| 1 | `data/eval_live.txt` | 5, the eval with the switch | ten minutes or more | 65 generator calls: Rs 17.57 of input, about Rs 30.00 at 300 tokens out, at most Rs 102.43 |
| 2 | `data/failing_rows.txt` | 6, the failing rows read | under a minute | Rs 0: one `/v1/passages` a failing row, no model |
| 3 | `data/fix_1.txt`, `data/fix_2.txt`, `data/fix_3.txt` | 7, one rule per row | about two minutes each | 18 generator calls each: Rs 4.73 of input, about Rs 8.18 at 300 tokens out, at most Rs 28.23 |
| 4 | `data/fix_read.txt` | 7, the three fixes side by side | seconds | Rs 0: three files read |

In all: Rs 31.77 of input, about Rs 54.53 at 300 tokens out, at most Rs 187.14. The lesson plan's estimate for this
lesson was about Rs 50.

How the costs were computed (`build.py`, which asserts that this file states its figures and commands as the page does):
every golden row's pool on the Rs 0 lane, the kit's lexical rank over its own chunks as lesson 2.6 prices its runs,
packed the way `generator.generate()` packs it (`_budget()`, `pack_chunks()`, the prompt line) and counted by the kit's
`estimate_tokens()` (four characters a token), priced with `shared/prices.py` (gemini-3.6-flash, USD 1.50 in and 7.50
out per million, USD_INR 85). "Of input" is the prompts alone; "at 300 tokens out" adds the course's typical answer;
"at most" adds the whole 2,048-token answer reserve (`max_answer_tokens`, thinking included) to every call. A fix's
failing row is priced at the largest answerable prompt. A call cut off at the reserve is asked once more with three times
the room, which no estimate here includes. `/v1/passages` calls cost nothing: no model, no tokens. Each bench run prints
its own total from the usage the model returned: please note the three totals when you hand the files back.

The page's prose says what each recording should show, read from the kit's code; the expectations are under each run.
If a recording disagrees, the recording is right: say so, and the prose changes with it.

### 1. `data/eval_live.txt` (step 5)

```bash
DOCUMIND_EVAL_PASSAGES=1 make eval-live PROJECT="$PROJECT" REPORT=evals/reports/lesson33.json 2>&1 | tee eval_live.txt
```

Expect make's `>> https://documind-api-NUMBER.asia-south1.run.app`, `== eval gate: LIVE ==`,
`65 rows (47 answerable, 18 not)`, nine threshold lines, then three [info] lines: `quote_support_rate`,
`quote_passage_rate` (the answered rows' quotes in the passage they cite, with elsewhere, absent, substituted and unread
counts) and `must_retrieve_recall` (anchors found over the answerable rows read back). Then the shape table, the latency
lines, `rows that cost a point (N):` with each failing row and its why, `report: evals/reports/lesson33.json`, and
`All thresholds met.` or `Blocked: ...`. Record it either way. The build refuses the file if either passage [info] line
or the report line is missing: that means the switch was not set, or `REPORT=` was left off.

### 2. `data/failing_rows.txt` (step 6)

Run step 6's cell exactly as the page prints it (it starts `DOCUMIND_ID_TOKEN="$(tok "$API")" python - <<'PY'`) and
record its output. Then paste its last line into the shell: it is `export FIX1=... FIX2=... FIX3=...`.

Expect `65 rows asked, N did not pass; a pool read for M`, then one block per failing row: its id, shape, tenant and why;
`asked`; `said` (answerable, confidence and the answer's start); a `cited` line per citation with its quote check; for an
answerable row, `wants` with each anchor in or NOT in the pool and a `passage` line per expected figure; and
`-> <address>: <reason>`. Then `by address: ...`, `passing rows whose quotes the passage check flags: ...` and
`to bench, one rule each: export FIX1=... FIX2=... FIX3=...`. FIX1 is the first refused row with its anchors in the
pool, FIX2 the first join answered without a figure, FIX3 the first other row answered without one. If the line names
fewer than three, or says `no row the prompt can fix`, follow "Fewer than three prompt rows" below before run 3.

### 3. `data/fix_1.txt`, `data/fix_2.txt`, `data/fix_3.txt` (step 7)

After pasting run 2's export line, the page's three commands, one at a time, each recorded:

```bash
make bench PROJECT="$PROJECT" BENCH_ARGS="--rows ${FIX1:?set FIX1 from the read cell} --shape refusal --report evals/reports/fix33_1.json --add-rule 'If a source answers the question in other words, or states a rule that covers the case asked about, answer from it and cite it.'" 2>&1 | tee fix_1.txt
make bench PROJECT="$PROJECT" BENCH_ARGS="--rows ${FIX2:?set FIX2 from the read cell} --shape refusal --report evals/reports/fix33_2.json --add-rule 'If the question asks more than one thing, answer every part, each from the source that states it, and cite each source.'" 2>&1 | tee fix_2.txt
make bench PROJECT="$PROJECT" BENCH_ARGS="--rows ${FIX3:?set FIX3 from the read cell} --shape refusal --report evals/reports/fix33_3.json --add-rule 'Begin the answer with the figure, name or term that answers the question, written as the source writes it.'" 2>&1 | tee fix_3.txt
```

Expect for each: make's `>> https://documind-api-NUMBER.asia-south1.run.app`; `== prompt bench: gemini-3.6-flash,
against ... ==`; `9 row(s) x 2 arm(s) x 1 level(s) x 1 run(s): up to 18 answers, one generate() each`; the pools line and
nine row lines in golden.jsonl's order (the fix row among rf-01 to rf-07 and mm-05); the arms, `kit   generator.py's SYSTEM - 5 rules; no
temperature` with `prompt sha256 543ed8060f1b177cc26159b1af609d16dabeeafa88097945f5a74e884aca4e1e`, and
`edit  rule added: <the rule> - 6 rules; no temperature` with its own sha256; 18 answer lines; the table of both arms;
the quote lines; `Rs ... in all: 18 answers, 18 model calls on gemini-3.6-flash, priced at list (shared/prices.py)`;
`generator.py unchanged on disk; SYSTEM is the kit's again`; and `report: evals/reports/fix33_N.json`. The build refuses
a file without the edit arm's rule line, the unchanged line or its report line. A refusal row with an empty pool is not
benched and says so: tell the editor if that happens, because the prose counts eight.

### 4. `data/fix_read.txt` (step 7)

Run step 7's fix cell exactly as the page prints it (the `python - <<'PY'` cell that defines `verdicts(answers)`) and
record its output.

Expect three blocks, one per report: `evals/reports/fix33_N.json: gemini-3.6-flash, 18 answers, Rs ..., generator.py
unchanged: True`, the rule, the fix row's kit and edit lines with their verdicts and answers, `refusal rows: kit K of 8;
edit E of 8`, and one of `-> fixed, and the guard held`, `-> fixed, and the guard broke`, `-> not fixed` or `-> the kit
arm passed too: nothing to credit the rule with`. Last line: `fixed with the guard held: N of 3`. Whatever N is, record
it: the page reads the verdicts as they come, and three of three is not required.

### Fewer than three prompt rows

If run 2's export line names fewer than three rows, find the missing kinds on the kit's cheap model, with the kit's
prompt only:

```bash
make bench PROJECT="$PROJECT" BENCH_ARGS="--shape lookup,join --model gemini-3.1-flash-lite --show" 2>&1 | tee lite_rows.txt
```

45 answers on gemini-3.1-flash-lite: Rs 2.03 of input, at most Rs 13.78. Pick FAIL rows whose why is `refused` (for
FIX1) or `answered without [...]` (a join for FIX2, any other row for FIX3), and whose pool, printed by `--show`, holds
the row's clause. Export them by hand (`export FIX2=jn-NN`), and add `--model gemini-3.1-flash-lite` to that fix's
`BENCH_ARGS`. Hand back `lite_rows.txt` too (the page does not show it), and say which fixes ran on the cheap model: the
fix cell prints each report's model, and the prose then needs a sentence.

When all four runs are in, put acme's pin back (the setup section's last window), and rebuild the page.
