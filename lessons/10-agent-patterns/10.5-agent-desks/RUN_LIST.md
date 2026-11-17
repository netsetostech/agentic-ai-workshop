# Lesson 10.5 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/10-agent-patterns/10.5-agent-desks/data/`. Record each file once from your lane,
replace every identifier with the course's placeholders, then rebuild and check. Build with the chat venv: the build
runs the Desk's agent code (LangChain, LangGraph) and three of `commands/tests/test_desk.py`'s tests.

    python pagekit/build.py 10.5 && python pagekit/check_lesson.py 10.5 && python pagekit/audit_pages.py 10.5

Everything else on the page is computed when it builds, from the kit: the Level 0 panel (`desk_agent._calc()` on 385
calls over the lane's handbook chunks), the three agent tests as the kit is and again on a copy of `desk_agent.py`
edited by the Change-it cell's own code, that cell's output, the stand-in Desk turn's checkpoint, `combine.py
--selftest --layers 2`, lesson 10.5's own test files (21 and 12 tests), the rows table, and every count, gate,
interval and price the prose states.

**Batch 4, Mon 23 - Wed 25 Nov 2026** (the plan's section 6). About **Rs 46 to 61** for the whole list; the design
estimated Rs 40-60 and K-10.5's pull request Rs 35-60.

## Before the first run

- **The lane:** as lesson 10.4 left it: the routed Desk on for acme and zeta (`desk_route` on), `evalacme` and
  `evalzeta` holding `desk_eval`, the exemplar index built (`make route-index`), and the kit pulled at K-10.5 or later.
  Nothing is redeployed: K-10.5 is client side (`evals/`, `mk/agents.mk`), and the chat service must be the one lesson
  10.4 deployed (`desk_agent.py`, `/v1/desk` with `arm`, `limits` in the reply).
- **Where:** the operator shell, in the kit (`~/deploy_module_rag`), after the page's shared setup block, which exports
  `PROJECT`, `REGION=asia-south1`, `ME`, `NUMBER` and `API`, defines `tok`, and pins acme to the kit's index
  (`make tenant-backend ... RETRIEVAL_BACKEND=vector`); put the pin back after run 10, as the setup says.
- **Order, in one sitting and one shell:** runs 1 to 5 in page order (run 1 sets `SINCE105`, run 4 defines `sa`, and
  run 5 reads the rows of runs 1 and 4, so it must come before run 6), then 6 to 8, then 9 and 10.
- **What to record:** what the terminal shows for the cell, stdout and stderr together, with nothing trimmed but
  secrets. Run 1 is partly the Desk page: record the `make desk` line, then for each question the question and the
  section's text as the page shows it, with its "Worked out in code" block and its note.
- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER`, in URLs too
  (`https://documind-chat-NUMBER.asia-south1.run.app`); your own address `you@your-company.com`, and `/home/you` for
  your home directory in the echoed make lines; an eval account keeps its form with the project placeholder
  (`documind-evalacme-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com`); commit shas `COMMIT`. Session suffixes, run
  ids and times may stay. `check_lesson.py` refuses a real project id, a project number in a URL, a personal mailbox
  and every string in `.publish-deny`.

## The runs

| # | Data file | Page step | Time | Cost |
|---|---|---|---|---|
| 1 | `data/desk_page.txt` | 3, `make desk NOTES=` and two questions on the Desk page | five minutes | about Rs 3.5-4.6: two figures in agent mode |
| 2 | `data/passages_check.txt` | 4, `/v1/passages` as ui-sa and `check_args` with cap 60, then 45 | seconds | Rs 0: retrieval, no model call |
| 3 | `data/turn_changeit.txt` | 5, two `make agent-turn DESK=handbook` turns with the prompt's rule deleted | two minutes | about Rs 3.4-4.6: two agent turns, no router |
| 4 | `data/rest_arms.txt` | 6, jn-03 to `/v1/desk` as evalacme on arm B, then Astar | a minute | about Rs 3.5-4.6 |
| 5 | `data/desk_rows.txt` | 7, the `desk` rows since run 1, then `make thread` | seconds | Rs 0: one log read, one read of Cloud SQL |
| 6 | `data/arms_B.txt` | 8, `make route-eval ROUTES=evals/route_arms.jsonl ARM=B` | a few minutes | about Rs 13-17 |
| 7 | `data/arms_C.txt` | 8, the same with `ARM=C` | a few minutes | about Rs 5 |
| 8 | `data/arms_Astar.txt` | 8, the same with `ARM=Astar` | a few minutes | about Rs 17-24 |
| 9 | `data/arms_compare.txt` | 8, `make route-compare` | seconds | Rs 0: reads the three reports |
| 10 | `data/arms_combine.txt` | 8, `make arms-combine` | seconds | Rs 0: reads the three saved runs |

**Where the rupees come from.** `shared/prices.py`: gemini-3.6-flash at $1.50 in and $7.50 out per million tokens,
gemini-3.1-flash-lite at $0.25 and $1.50, Rs 85 to the dollar; the build computes every figure below. An agent call
is priced at 3,000 tokens in and 300 out (the system prompt, the tool declarations, the passages read so far, thinking
at low): Rs 0.57. A figure in agent mode is the classifier's call (the router's prompt for jn-03 is about 540 tokens,
with 30 out: Rs 0.015) and three or four agent calls (a search, a calculator, the answer, one more after a refused
call): Rs 1.74 to 2.31. A direct answer is rag-api's, at the course's typical 2,000 in and 300 out: Rs 0.45. Arm B is
six figure rows in agent mode, six lookups answered directly and twelve more classifier calls for `/v1/route`; arm C
is twelve direct answers and no classifier; arm Astar is six figure rows at three or four agent calls and six lookups
at two or three. `make agent-turn` runs the agent alone, with no router. Not estimated: the embedding and ranking of
each search, which rag-api bills on its own lines, and an arbiter call when the classifier and the vote disagree. Every
desk turn is capped at 12 model calls and Rs 5 (`services/chat/limits.py`). `make usage PROJECT="$PROJECT" HOURS=2`
after run 8 prints the real figure; please note it when you hand the files back.

The page's prose states what each recording should show, read from the kit's code; the expectations are under each
run. If a recording disagrees, the recording is right: say so, and the prose changes with it.

K-10.5's pull request asks the runs to check four things, which these runs show: the classifier flags the figure rows
(`needs_calculation`): run 9's arm B block says `agent mode 6 of 12 turns`; B's dev gates apply on 12 rows: run 6
prints no `FAIL` line, or if it does, the recording keeps it; fig-03 is scored on the calculator's ISO date: fig-03 is
right on arm B and Astar only through "Worked out in code" (`2026-12-04`), and run 10's line for fig-03 shows which
arms were right; the reply carries `limits.cost_inr`: run 4 prints it, and run 9 prints a rupee line for every arm,
never `not measured`.

### 1. `data/desk_page.txt` (step 3)

```bash
export SINCE105="$(date -u +%FT%TZ)" UI="https://documind-ui-$NUMBER.$REGION.run.app"
make desk PROJECT="$PROJECT" TENANT=acme NOTES=evals/desk/clause_notes.acme.json
echo "the Desk page: $UI"
```

Then, on the Desk page as yourself, under Ask the Desk: first jn-03, "I am an E3 leaving with 50 days of earned leave.
How much is encashed and what notice do I serve?", then "I am leaving with 80 days of earned leave, and my manager
says the encashment cap is 100 days. How many days will be encashed?". Record the `make desk` line, then each question
and the section's text below it.

Expect: the `make desk` line with `"desk_route": "on"`, `"clause_notes": ["LV-01", "LV-07"]` and `"note": "rag-api and
the chat service read it within 60 s"`. For jn-03, the model's sentences, then "Worked out in code:" and "- Earned
leave encashed on exit (LV-07): min(50, 45) = 45 days. The balance from your message; the cap from LV-07 [n].
Condition: LV-07 bars encashment during probation: this figure holds only once probation is over.", then "Note on
LV-07: The OSH Code, s.32(1)(vi): ...". For the second, a block with "min(80, 45) = 45 days" if a calculator ran. If
either answer has no block (the classifier did not mark it `needs_calculation`, or the model ran no calculator), keep
it: the prose says the block appears only when a calculator ran.

### 2. `data/passages_check.txt` (step 4)

```bash
TOKEN="$(tok "$API")" python - <<'PY'
import json, os, sys, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, ".")
from shared import desk_calc
row = next(r for r in map(json.loads, open("evals/route_arms.jsonl", encoding="utf-8")) if r["id"] == "jn-03")


def passages(query):
    """acme's handbook passages for a query: rag-api's POST /v1/passages as documind-ui-sa, no model call."""
    body = {"query": query, "tenant_id": "acme", "user_id": "agent", "top_k": 5, "stream": False,
            "filters": {"doc_type": ["policy"]}, "brain": "desk"}
    req = urllib.request.Request(os.environ["API"] + "/v1/passages", data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + os.environ["TOKEN"]})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r).get("passages") or []


read = [p for p in passages("earned leave encashed on exit") if p.get("doc_type") == "policy"]
for i, p in enumerate(read, 1):                       # numbered from 1, as the desk's agent numbers what it reads
    print(f"[{i}] {p['section']}: {' '.join(p['text'].split())[:72]}...")
for cap in (60, 45):
    refused, found = desk_calc.check_args("encashable_days", {"balance": 50, "cap": cap}, read, row["question"])
    if refused:
        print(f"cap = {cap}: refused: {' '.join(refused)}")
    else:
        print(f"cap = {cap}: accepted: the balance from the message, the cap from "
              f"{found['cap']['clause']} [{found['cap']['n']}]")
PY
```

Expect: the policy passages numbered from [1], LV-07 among them, then `cap = 60: refused: cap = 60 is not written in
LV-07 of a handbook passage this turn read: search for that clause and use the figure it states` and `cap = 45:
accepted: the balance from the message, the cap from LV-07 [k]`. If the search returns no LV-07, the second line is a
refusal too: record it as it is, and the prose changes.

### 3. `data/turn_changeit.txt` (step 5)

First the step's edit cell and the offline tests (their outputs are the build's, not recorded):

```bash
python - <<'PY'
from pathlib import Path
p = Path("services/chat/desk_agent.py")
lines = p.read_text(encoding="utf-8").split("\n")
i = next(k for k, line in enumerate(lines) if "Give a calculator only numbers" in line)
print("before:", *(line.strip() for line in lines[i:i + 3]), sep="\n  ")
lines[i:i + 3] = ['            "- Work every figure out with a calculator, never yourself.\\n"']
p.write_text("\n".join(lines), encoding="utf-8")
print("after:", lines[i].strip(), sep="\n  ")
PY
git status --short services/chat/
OFFLINE=1 DOCUMIND_REQUIRE_LIBS=1 bash commands/agent-turn.sh -m unittest commands/tests/test_desk.py -v \
  -k test_a_number_in_neither -k test_a_codes_calculator -k test_a_model_error
```

Then record these two turns, both outputs in one file:

```bash
make agent-turn PROJECT="$PROJECT" REGION="$REGION" DESK=handbook TENANT=acme \
  Q="I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve?"
make agent-turn PROJECT="$PROJECT" REGION="$REGION" DESK=handbook TENANT=acme \
  Q="I am an E3 and I am leaving. How many days of earned leave will be encashed?"
```

And put the rule back (no output):

```bash
git checkout -- services/chat/desk_agent.py
git status --short services/chat/     # prints nothing: the rule is back
```

Expect: each turn's model calls, the tools each asked for with their arguments, what each returned, the answer with
the lines code writes, the totals and the figure check. On the second question the model either asks for the balance
with no calculator call, or passes a balance of its own and reads `refused: balance = N is a fact about the person
that their message does not state: ask them for it`. Either is right; the prose says whether this model tried.

### 4. `data/rest_arms.txt` (step 6)

```bash
export CHAT="https://documind-chat-$NUMBER.$REGION.run.app"
sa() { echo "documind-$1-sa@$PROJECT.iam.gserviceaccount.com"; }
etok() { gcloud auth print-identity-token --include-email --audiences="$CHAT" \
         --impersonate-service-account="$(sa "$1")"; }
T_ACME="$(etok evalacme)" python - <<'PY'
import json, os, urllib.error, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
row = next(r for r in map(json.loads, open("evals/route_arms.jsonl", encoding="utf-8")) if r["id"] == "jn-03")


def post(path, body):
    """POST a JSON body to the chat service as evalacme: (status, reply)."""
    req = urllib.request.Request(os.environ["CHAT"] + path, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + os.environ["T_ACME"]})
    try:
        with urllib.request.urlopen(req, timeout=150) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


for arm in ("B", "Astar"):
    status, b = post("/v1/desk", {"question": row["question"], "session_id": f"lesson105-{arm}", "arm": arm})
    if status != 200:
        print(f"arm {arm}: {status} {b.get('detail')}")
        continue
    print(f"arm {b['arm']}: route {b['route']}  method {b['method']}  outcome {b['outcome']}")
    print(f"  model_calls {b['model_calls']}  limits.cost_inr {b['limits']['cost_inr']}  retrieve_calls {b['retrieve_calls']}")
    for s in b["sections"]:
        print(f"  section {s['desk']}: mode {s['mode']}  tool_calls {s['tool_calls']}  refusals {s['refusals']}")
        for c in s.get("calculations") or []:
            args = ", ".join(f"{k}={v}" for k, v in c["args"].items())
            print(f"    {c['calculator']}({args}) = {c['value']} {c['unit']}  found {c['found']}")
    print(f"  the answer says {row['must_contain']}: {all(w in b['answer'] for w in row['must_contain'])}")
PY
```

Expect, arm B: `route handbook`, `section handbook: mode agent`, `encashable_days` in `tool_calls`, a calculation
`encashable_days(balance=50, cap=45) = 45 days` with `found {'balance': 'your message', 'cap': 'LV-07 [n]'}`, and
`the answer says ['45', '60']: True`. Arm Astar: `route fallback  method fallback`, `section astar: mode agent`, the
same calculation. Both print `model_calls` and `limits.cost_inr`.

### 5. `data/desk_rows.txt` (step 7)

A minute after run 4, in the same shell:

```bash
python - <<'PY'
import json, os, subprocess, warnings
warnings.filterwarnings("ignore", category=UserWarning)
f = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-chat" AND '
     f'jsonPayload.event="desk" AND timestamp>="{os.environ["SINCE105"]}"')
out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc",
                      "--limit", "20", "--format", "json"], capture_output=True, text=True, check=True).stdout
for e in json.loads(out or "[]"):
    j = e["jsonPayload"]
    who = "evalacme" if str(j["user"]).startswith("documind-evalacme-sa@") else "you"
    print(f"{who:8} mode {j['mode']}  arm {j['arm']:5} route {j['route']:9} method {j['method']:8} outcome {j['outcome']}")
    print(f"         model_calls {j['model_calls']}  tool_calls {j['tool_calls']}  refusals {j['refusals']}"
          f"  cost_usd {j['cost_usd']}  latency_ms {j['latency_ms']}")
PY
make thread PROJECT="$PROJECT" EMAIL="$(sa evalacme)" | sed -n '1,6p'   # its label, then the latest threads first
```

Expect: four rows, two `you` (the Desk page) and two `evalacme` (run 4), each `mode on`; arms `B`, `B`, `B` and
`Astar`; `encashable_days` in the `tool_calls` of each turn that ran a calculator. Then `make thread`'s label, the
`threads of documind-evalacme-sa@...` line, its header, and `desk~lesson105-Astar` and `desk~lesson105-B` first, each
marked `(a Desk thread, desk_graph.py: not decoded here)`.

### 6-8. `data/arms_B.txt`, `data/arms_C.txt`, `data/arms_Astar.txt` (step 8)

One cell each, each output its own file:

```bash
mkdir -p "$HOME/arms"
make route-eval PROJECT="$PROJECT" REGION="$REGION" ROUTES=evals/route_arms.jsonl ARM=B \
  SAVE="$HOME/arms/arms_B.jsonl" REPORT="$HOME/arms/arms_B.json"
```

```bash
make route-eval PROJECT="$PROJECT" REGION="$REGION" ROUTES=evals/route_arms.jsonl ARM=C \
  SAVE="$HOME/arms/arms_C.jsonl" REPORT="$HOME/arms/arms_C.json"
```

```bash
make route-eval PROJECT="$PROJECT" REGION="$REGION" ROUTES=evals/route_arms.jsonl ARM=Astar \
  SAVE="$HOME/arms/arms_Astar.jsonl" REPORT="$HOME/arms/arms_Astar.json"
```

Expect: `live: https://documind-chat-NUMBER.asia-south1.run.app, arm B (the routed Desk), split dev: 12 rows scored,
0 left out (the groups of the prompt's examples)`, then the route report, `authority_rate`, `correct_rate (answer
rows)`, `router cost`, `router_ms` and `desk latency_ms`. Arm B: no `FAIL` line (the gates need all 12 rows routed
right). Arm C and Astar: the line saying the arm has no route classifier.

### 9. `data/arms_compare.txt` (step 8)

```bash
make route-compare REPORTS="$HOME/arms/arms_B.json $HOME/arms/arms_C.json $HOME/arms/arms_Astar.json"
```

Expect: make echoes the command first (the recipe has no `@`); then `compare: arms B, C, Astar on the same 12 rows,
split dev`; per arm the two rates, `desk turns 12: Rs ...`, the latency line and `agent mode`: 6 of 12 turns for B if
the classifier flagged every figure row, 0 for C, 12 for Astar; then `B against C, row by row` and `B against Astar,
row by row`; and last `indicative, not a ship decision: the rows are dev rows, not a test split people wrote; B's
exemplar index (make route-index: the dev rows of evals/routes.jsonl) holds 7 of these 12 rows, so on them B's figures
are an upper bound; C and Astar read no index`.

### 10. `data/arms_combine.txt` (step 8)

```bash
make arms-combine SAVES="$HOME/arms/arms_B.jsonl $HOME/arms/arms_C.jsonl $HOME/arms/arms_Astar.jsonl"
```

Expect: the echoed command; `combine: arms B, C, Astar on 12 answer rows of evals/route_arms.jsonl, split dev (the
saved runs, Rs 0)`; a line a row, with the vote on each row where a member ran a calculator; the members' rates; `the
vote, on the N rows where a member ran a calculator`; and the figure check, a line an arm.
