# Lesson 3.9 run list: the live output the page still needs

The page builds without it: the output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`, until
its file exists in `lessons/03-generation/3.9-design-fact-checking/data/`. Every other output on the page is the kit's
own, produced at build time by the page's offline cells. Record the file once from your lane, then rebuild and check:

    python pagekit/build.py 3.9 && python pagekit/check_lesson.py 3.9 && python pagekit/audit_pages.py 3.9

## Before the run

- **The lane:** deployed by lesson 0.3 and used: the table needs at least one answer from `gemini-3.6-flash` through
  the `vertex` backend in the last 24 hours. A day of lesson cells is enough; right after a `make eval-live` the
  average is over the golden set's questions, which is a fair stand-in for claims.
- **Where:** the operator shell, in the kit (`~/deploy_module_rag`), after the page's shared setup block (lesson 1.1's),
  which exports `PROJECT` and `REGION`.
- **What to record:** what the terminal shows for the cell, stdout and stderr together, with nothing trimmed.
- **Placeholders:** the output carries model names, backends and counts only: nothing to replace. `check_lesson.py`
  still refuses a real project id, a project number and every string in `.publish-deny`.

## The run

| # | Data file | Page step | Time | Cost |
|---|---|---|---|---|
| 1 | `data/usage_tokens.txt` | 6, your lane's tokens a claim | seconds | none: one read of the usage rows |

### 1. `data/usage_tokens.txt` (step 6)

```bash
make usage PROJECT=$PROJECT HOURS=24 | sed -n '/^by model and backend/,/^$/p' | tee /tmp/usage39.txt
awk '$2 == "vertex" && $3 > 0 {printf "%s: %d answers, %.0f tokens in and %.0f out each, p95 %s ms\n", $1, $3, $4 / $3, $5 / $3, $8}' /tmp/usage39.txt
```

Expect the by-model table from `evals/usage_rows.py` (header, a rule, one row per model and backend) and one line per
`vertex` row from `awk`. The build reads the `gemini-3.6-flash  vertex` row: answers, tokens in, tokens out and p95.
From that it adds a measured option to step 6's calculator and writes the measured line under it; the static table
stays at the ceiling, which is what a cost model may not exceed. If the build stops on "no gemini-3.6-flash / vertex
row", the window held no answers from that model: ask some questions and record again.

The page's prose says the average sits under the ceiling of 8,000 tokens in and 2,048 out, which `TokenBudget.fit()`
and `max_answer_tokens` guarantee for one attempt. If the recording shows otherwise (a truncation retry bills both
attempts), the recording is right: say so, and the prose changes with it.
