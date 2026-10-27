# Lesson 10.10 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/10-agent-patterns/10.10-coding-agents/data/`. Record each file once, replace every
identifier with the course's placeholders, then rebuild and check:

    python pagekit/build.py 10.10 && python pagekit/check_lesson.py 10.10 && python pagekit/audit_pages.py 10.10

Everything else on the page is computed from the kit when the page builds, at Rs 0: the workspace and the hand
iteration's checks, every oracle verdict, the Change it, the scripted loop under both oracles, on a rupee cap, on the
iteration cap and on paper-to-code, the guards, the dry run with the egress proxy off and on, the refusals, the linter,
and the human step on the weak run's kit.patch.

## Before batch 4: what the batch-1 probe must settle (Mon 26 - Wed 28 Oct 2026)

The page's runs are batch 4's. They stand on facts the batch-1 probe establishes in Cloud Shell. If one of them fails,
the page's live sections change before anything below is recorded. What batch 4 needs from the probe:

1. **The pin.** `docker version` answers; `npm view @google/gemini-cli version` gives the version to pin;
   `make ralph-image GEMINI_CLI_VERSION=<pin>` builds, and the image's `documind.gemini-cli` label shows the pin.
2. **The isolation, free.** `make ralph-probe`: the oracle's container (`--network none`) is refused on example.com,
   and the agent's container holds only `GOOGLE_API_KEY`, `GOOGLE_GENAI_USE_VERTEXAI`, `HOME` and `RALPH_MODEL` of
   ours, with no gcloud configuration and no docker.sock among its mounts.
3. **The key.** The model-only key of the cohort plan's decision 12, which the author creates for a run and deletes
   after it: likely an API key restricted to `aiplatform.googleapis.com`. The probe verifies the exact `gcloud`
   commands; the page prints none. The key is read with `read -rs RALPH_API_KEY && export RALPH_API_KEY`, never put
   on a make command line.
4. **Gemini CLI headless, a few rupees.** `make ralph-probe YES=1` (two calls): the JSON stats carry the field names
   `price_stats()` reads (`stats.models.<model>.tokens.prompt`, `tool`, `cached`, `candidates`, `thoughts`, and
   `api.totalRequests`); whether the key needs `RALPH_PROJECT` (retry with `RALPH_PROJECT=<id>` if the call is
   refused); no web tool runs; `/etc/gemini-cli/settings.json` is honoured with no unknown-settings warning; `--yolo`
   works with a read-only root and `HOME=/tmp`; and whether `--output-format stream-json` would list tool calls.
5. **The egress proxy, a few rupees.** `make ralph-probe RALPH_EGRESS=proxy YES=1`: checks 5 to 7 (free) find
   example.com and 169.254.169.254 unreachable straight out of the agent's container and example.com refused by the
   proxy, which opens a tunnel to `aiplatform.googleapis.com:443`; the two calls, numbered 8 and 9 here, then run behind
   the proxy, and each one's `the egress proxy on this call:` line should show `allowed aiplatform.googleapis.com:443`
   and refuse nothing Gemini CLI needs. If a call fails and that line names a refused host, Gemini CLI needs that host
   (or ignored `HTTPS_PROXY`): the author decides whether `EGRESS_ALLOW` in `commands/ralph.py` grows. Note whether
   check 5 says example.com resolved: a lookup leaving the internal network is Docker's embedded DNS, not the proxy.
6. **The cap.** The dry run `make ralph RALPH_MAX_ITERS=1 RALPH_BUDGET_INR=30`: one iteration's rupees set batch 4's
   `CAP`. Batch 1 also runs one iteration by hand and reviews it (about Rs 1-2); that is the probe's, not the page's.
7. **The key deleted** at the end of batch 1. Batch 4 creates a fresh one.

## Batch 4 (Mon 23 - Wed 25 Nov 2026): the runs, in order

- **Where:** Cloud Shell, in the kit (`~/deploy_module_rag`), after the page's setup block (lesson 1.1's), which
  exports `PROJECT` and the rest. Docker is Cloud Shell's, and its image storage does not outlive the session.
- **The lane:** nothing on it changes. The loop runs in containers on the Cloud Shell machine. The reviewer calls
  gemini-3.6-flash on location `global` as you (Application Default Credentials), billed to the lane.
- **What to record:** what the terminal shows, stdout and stderr together, with nothing trimmed but secrets.
- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER`; your email `you@your-company.com`;
  home directory `/home/you`; each run directory's stamp and suffix as `ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX`.
  A key never appears in any output (the kit's tests hold that); if one does, stop, delete the key and record again.
  Run `grep -n "$PROJECT\|$NUMBER" data/*` before you copy.

| # | Data file | Page step | Cost (shared/prices.py; estimated when the page was built) |
|---|---|---|---|
| 0 | none | 8, the image and the key | none: a docker build in Cloud Shell |
| 1 | `data/ralph_loop.txt` | 8, the live loop | the cap, `CAP`, by the Meter's rule (below) |
| 2 | `data/review_diff.txt` | 8, the reviewer on ralph.patch | one call: about Rs 0.26 of input, plus output and thinking |
| 3 | `data/ralph_reads.txt` | 9, the run's record | none |
| 4 | `data/human_step.txt` | 9, the human step | none |
| 5 | `data/review_eval.txt` and `data/review_eval.json` | 7, and the Level 0 panel | 21 calls: Rs 5.48 of input; Rs 16.19 to Rs 36.28 in all |
| 6 | `data/isolation.txt` | 8, the egress proxy on a live docker | none: no key and no model call |

Total: `CAP`, plus Rs 16.19 to Rs 36.28 for run 5, plus run 2's one call.

How the reviews' rupees were computed (`build.py` computes them and refuses to build while this file states others):
each of the seven diffs' requests, built by `review_diff.prompt()` as `make review-eval` builds it, is 2,042 to 2,054
tokens by the kit's four-characters-a-token count. At gemini-3.6-flash's list price (USD 1.50 in and 7.50 out a
million tokens, USD_INR 85), three repeats come to Rs 5.48 of input. The kit sets no output cap on a review: at 300
output and 500 thinking tokens a call, the 21 calls come to Rs 16.19 in all; at 300 and 2,000, Rs 36.28. Run 2's call
is about Rs 0.26 of input on a diff the size of the kit's own function.

The loop's cost is its own. The cap is checked before each iteration but the first, so the first iteration always
runs, an iteration under way always finishes, and one dearer than the dearest so far can take the total past the cap.
A cut iteration (900 s) or one whose agent printed no stats stops the loop with its cost uncounted: read it in the
lane's billing.

The page's prose says what each recording should show, read from the kit's code; the expectations are under each run.
If a recording disagrees, the recording is right: say so, and the prose changes with it.

### 0. The image and the key, each Cloud Shell session (not recorded)

```bash
make ralph-image GEMINI_CLI_VERSION=<pin>
read -rs RALPH_API_KEY && export RALPH_API_KEY      # the fresh model-only key, typed, never echoed
```

### 1. `data/ralph_loop.txt` (step 8)

```bash
make ralph RALPH_MAX_ITERS=8 RALPH_BUDGET_INR=<CAP> OUT="$HOME/ralph-live"
```

Add `RALPH_PROJECT="$PROJECT"` if the probe found the key needs it. Expect the header (`ralph: task deadline
(statutory_deadline written to an engineer's spec), agent gemini-cli, strong oracle`, the caps line with `Rs <CAP>`,
`the run: /home/you/ralph-live/ralph-deadline-...`), one line for each iteration with its item, lines, verdict, tokens
and rupees (FAIL lines, flags or `the agent:` errors under it), then `stopped: ...`, what was spent, the weak oracle's
verdict on the same code after a pass, the paths of ralph.patch, kit.patch and summary.json, and `nothing was applied
to your clone and nothing was pushed`. Exit 0 when the oracle passed, 1 on a cap. Keep the run directory: runs 2 to 4
read it.

### 2. `data/review_diff.txt` (step 8)

```bash
export RUN="$(ls -dt "$HOME"/ralph-live/ralph-* | head -n 1)"
make review-diff PROJECT="$PROJECT" DIFF="$RUN/ralph.patch"
```

Expect `review-diff: ralph.patch, by gemini-3.6-flash on location global, thinking low`, one line per finding
(`line N: rule - why`) or `no findings`, then `N findings; Rs ...`.

### 3. `data/ralph_reads.txt` (step 9)

With `RUN` exported as in run 2, run step 9's first cell without its first line (the `export RUN=` that points at
`/tmp/ralph-strong`), then its summary cell as printed. Record both outputs together: the run's commit subjects, its
fix_plan.md, GEMINI.md's Learned section and ralph.patch, then the summary's lines.

### 4. `data/human_step.txt` (step 9)

With `RUN` still the live run, run step 9's human-step cell without its first line. Expect kit.patch's diff, the
selftest's last line, nothing from `git status --short`, then the verdicts of `make ralph-check PATCH=`. If kit.patch
is empty (the loop wrote the kit's own function byte for byte), `git apply` refuses it: record that as it prints.

### 5. `data/review_eval.txt` and `data/review_eval.json` (step 7 and the Level 0 panel)

```bash
make review-eval PROJECT="$PROJECT" REPEAT=3 SAVE="$HOME/review-eval.json"
```

Copy `~/review-eval.json` to `data/review_eval.json` in the authoring repository. Expect `review-eval: gemini-3.6-flash
on location global, thinking low`, the seven-row table (found and near as k/3, false alarms with their rules), the
`catch count:` line, `21 reviews, N failed; Rs ...` and `saved: /home/you/review-eval.json`. The build rescores the
JSON as `make review-eval FROM=` would, and refuses a text and a JSON whose catch counts differ, so record both from
the same run. The JSON holds the date, the reviewer, the model and every finding; check it holds no project id.

### 6. `data/isolation.txt` (step 8)

Any time after the image is built in the session (run 0); it needs no key and calls no model:

```bash
make ralph-probe RALPH_EGRESS=proxy
```

Expect the header ending `RALPH_EGRESS=proxy`; checks 1 to 3 as batch 1 recorded them; 4, the agent's container
holding `HTTPS_PROXY` beside `GOOGLE_API_KEY`, `GOOGLE_GENAI_USE_VERTEXAI`, `HOME` and `RALPH_MODEL` of ours, with no
gcloud configuration and no docker.sock among its mounts; 5, `the agent's container reaches example.com and
169.254.169.254 directly: refused, as it must be`, with whether example.com resolved and each connection's error; 6,
`the egress proxy opens a tunnel to example.com:443: refused, as it must be - HTTP/1.1 403 Forbidden`; 7, `the egress
proxy opens a tunnel to aiplatform.googleapis.com:443: observed - HTTP/1.1 200 Connection established (nothing sent
through it, Rs 0)`; the proxy's log line (`allowed aiplatform.googleapis.com:443 (1); refused example.com:443 (1)`);
then `8. one headless call: not tested - add YES=1`. A `REACHED` or `OPENED` means the proxy does not hold: record it
as it prints, and the page's step 8 and its gaps box change with it.

### Last: the key

`unset RALPH_API_KEY`, then delete the key (decision 12). No make target creates or deletes it.
