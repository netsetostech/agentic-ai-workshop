# Lesson 6.8 run list: the live outputs the page still needs

The page builds without them: each output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`,
until its file exists in `lessons/06-context-memory/6.8-checkpoint-resume/data/`. Record each file once from your lane,
replace every identifier with the course's placeholders, then rebuild with the chat image's pins and check:

    venvs312/chat/Scripts/python pagekit/build.py 6.8 && python pagekit/check_lesson.py 6.8 && python pagekit/audit_pages.py 6.8

Everything else on the page is computed when it builds, from the kit: `make replay OFFLINE=1` and `AT=0` (the kit's
cut-off fixture resumed and a finished turn matched), step 5's offline cell (the next question on the cut-off thread,
as it is and after `limits.repair_thread()`), the Level 0 panel (the fixture's checkpoints and four ways on from its
cut, each run on the kit's LangGraph brain), LangGraph 1.2.12's discard line, and the Change-it's edit and restore. The
build also runs every cell below against stand-ins (the kit test's fake gcloud and connector over a thread the kit's
brain wrote, a scripted model, a fake Cloud SQL), so a cell that would fail on the lane fails the build first.

These are batch 2's runs (Mon 2 - Wed 4 Nov, plan section 6).

## Before the first run

- **The lane:** deployed by `make up` (lesson 0.3), with the chat service on its Cloud SQL checkpointer as lessons
  6.5 to 6.7 found it, and `make ingest-corpus` done. The runs write one thread (run 1's conversation) and nothing else
  in the checkpoint tables.
- **The kit in the operator shell:** `~/deploy_module_rag` must carry PR #107's files (`mk/memory.mk`,
  `commands/thread_read.py`, `commands/thread_replay.py`, `commands/graph-venv.sh`). The first `make thread` makes or
  updates `~/graph-venv` with the chat image's pins and the Cloud SQL connector: a minute or two, once.
- **Where:** the operator shell (Cloud Shell or the workstation), in the kit, after the page's shared setup block
  (lesson 1.1's), which exports `PROJECT`, `REGION=asia-south1`, `TENANT=acme`, `ME`, `NUMBER` and `API` and defines
  `tok`. Run 1 also needs the UI in a browser, signed in as you.
- **Order, in one sitting:** runs 1, 2, 3, 4, 5, 6. Run 2 is independent of the others. Runs 4 to 6 read run 3's
  `~/lesson68.json`; run 6 must come after run 5, with no new UI turn on run 1's session in between.
- **What to record:** what the terminal shows for the cell, stdout and stderr together, with nothing trimmed but
  secrets. If pip prints a notice the first time `graph-venv.sh` installs the pins, leave that line out.
- **Placeholders:** project id `documind-ai-YOUR-ID` (it is in the connection line, the instance name and
  `documind-ui-sa`'s address); project number `NUMBER`; your email `you@your-company.com` (it is in the thread id and
  the listing's header); home directory `/home/you` (in the export's path). The UI's 12-character session id, checkpoint
  ids, call ids, times and the model's words may stay. `check_lesson.py` refuses a real project id, a project number in
  a URL, a personal mailbox, and every string in `.publish-deny`; the build refuses a file with any `documind-ai-` id
  but the placeholder.

## The runs

| # | Data file | Page step | Time | Cost |
|---|---|---|---|---|
| 1 | `data/ui_thread.txt` | 3, two questions in the UI, then `make thread` | a few minutes | about Rs 2.68 for the two turns; `make thread` reads only |
| 2 | `data/next_turn.txt` | 5, the next question with Gemini on the kit's cut-off thread | under a minute | at most about Rs 1.34; nothing if Gemini refuses the history |
| 3 | `data/thread_at.txt` | 6, `make thread AT=1 EXPORT=` | seconds | none: reads only |
| 4 | `data/replay_fork.txt` | 7, `make replay FILE= FORK=` | about a minute | about Rs 2.68 (the replay prints its own) |
| 5 | `data/changeit.txt` | 7, the Change-it's replay with the edited prompt | about a minute | at most about Rs 2.68 (printed) |
| 6 | `data/table_read.txt` | 8, the direct read | seconds | none: reads only |

**Where the rupees come from.** `shared/prices.py`: gemini-3.6-flash at $1.50 in and $7.50 out per million tokens, Rs 85
to the dollar, priced at the course's typical answer of 2,000 tokens in and 300 out (lessons 4.3, 4.4 and 11.6): Rs 0.45
a call. An agent turn with one search is three such calls: the model asking for `retrieve`, rag-api's grounded answer to
the search (the agents ignore it, and it bills), and the model's answer: Rs 1.34 a turn. In all, at most about Rs 9.37,
inside the plan's Rs 7-10 for this lesson. The UI's captions and each replay's last line print the real figures from
the turn's `limits.Meter`; please note them when you hand the files back.

The page's prose states what each recording should show, read from the kit's code; the expectations are under each
run, taken from the build's stand-in run of the same commands. If a recording disagrees, the recording is right: say
so, and the prose changes with it.

### 1. `data/ui_thread.txt` (step 3)

In the UI (`https://documind-ui-$NUMBER.$REGION.run.app`), signed in as yourself, set **Brain** to `langgraph` and ask
exactly `After how many years of continuous service is gratuity payable?`, then, when its answer is in,
`Is it payable to a contract employee?`. Note the two captions' rupees (not recorded). Then record:

```bash
make thread EMAIL="$ME" | tee /tmp/lesson68-threads.txt
SID=$(awk '$1 == "acme" && $2 !~ /^desk~/ {print $2; exit}' /tmp/lesson68-threads.txt)
echo "SID=$SID"
make thread EMAIL="$ME" SESSION="$SID"
```

Expect the connection line `documind-ai-YOUR-ID:asia-south1:documind-checkpoint, database documind, as chat (read
only)`, `threads of you@your-company.com, the latest written first:`, the header, and your new session as the first chat
row, with `10` checkpoints, `2` turns and last step `8` if each turn searched once; a Desk thread of yours is listed and
marked `(a Desk thread, desk_graph.py: not decoded here)`. Then `SID=` and the session, the connection line again,
`thread acme:you@your-company.com:<SID>: 10 checkpoints, 2 turns`, the header and ten rows: `-1 input __start__`,
`0 loop agent`, `1 loop tools`, `2 loop agent`, `3 loop -`, `4 input __start__`, `5 loop agent`, `6 loop tools`,
`7 loop agent`, `8 loop -`, each with its time, `langgraph`, its message count and newest message. If Gemini searched
twice in a turn, or not at all for the follow-up, record it as it is and say so in the review: the prose describes one
search a turn. The build refuses a file without `threads of `, `the latest written first:`, `checkpoints, 2 turns` and
`the newest message`.

### 2. `data/next_turn.txt` (step 5)

Run the step's second cell as written: a heredoc in `~/graph-venv`, with `GOOGLE_CLOUD_PROJECT`, `RAG_API_URL` and
`DOCUMIND_IMPERSONATE_SA` set on its first line. It copies the kit's cut-off fixture into a local saver and asks the
kit's LangGraph brain, with Gemini on `global` and your rag-api, `Is gratuity payable to an apprentice?`, as
`/v1/chat` would.

Expect one of two results, and record whichever comes. Either `the next turn answered; tools: ...`, the messages from
6 on (`6. ai     asks retrieve(query='Is gratuity payable to a contract employee?')`,
`7. human  Is gratuity payable to an apprentice?`, then the model's own), `tool calls no tool message answers: retrieve
call_21c9aa740d14` (plus any call of its own left open) and `N model call(s), Rs X at list price with the searches`.
Or `the next turn failed: <the error's class>: <its message>`, messages 6 and 7 only, the same open-call line and
`1 model call(s), Rs 0.00 ...`. Say in the review which it was: this run settles what the 7 October review left
unverified, Gemini's answer to a history with an unanswered function call. The page's prose holds for both.

### 3. `data/thread_at.txt` (step 6)

```bash
SID=${SID:-$(make thread EMAIL="$ME" | awk '$1 == "acme" && $2 !~ /^desk~/ {print $2; exit}')}
make thread EMAIL="$ME" SESSION="$SID" AT=1 EXPORT="$HOME/lesson68.json"
```

Expect run 1's ten rows again, then `step 1: checkpoint <id>, parent <id>, written <time>`, `source loop, brain
langgraph, next tools`, the metadata line, `the messages saved at step 1 (2):` with your first question and
`ai     asks retrieve(query=...)`, then `wrote /home/you/lesson68.json: 10 checkpoints and 8 messages. Replay a turn of
it locally: make replay FILE=/home/you/lesson68.json AT=<step>`. Keep `~/lesson68.json` for runs 4 to 6.

### 4. `data/replay_fork.txt` (step 7)

```bash
make replay FILE="$HOME/lesson68.json" FORK="Is it payable to an apprentice?"
```

Expect `thread acme:you@your-company.com:<SID>`, `  from /home/you/lesson68.json: 10 checkpoints, steps -1 to 8, 2
turns`, `on your machine: Gemini (gemini-3.6-flash, location global) and your lane's rag-api as
documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com`, `1. the copy: 10 checkpoints in a local InMemorySaver,
one update_state() each; every step's number, next and messages are the file's`, `2. replay from step 5 (next
agent)`, the turn's question, the `+` lines and the comparison line (`the replay matches the recorded turn: ...` or
`the replay differs from the recorded turn: ...`), `3. fork from step 4`, `the fork's question: 'Is it payable to an
apprentice?'` and its `+` lines, `4. graph.get_state_history(thread): N checkpoints, in 3 branches` with its rows, and
`only the local copy was written; the lane never is. Model calls: the replay N, the fork N; Rs X at list price with the
searches (limits.Meter)`. A `1. the copy` line that lists differing steps is a kit finding: record it and say so.

### 5. `data/changeit.txt` (step 7, Change it)

Run the edit cell (not recorded); its `grep -c` prints `0`:

```bash
sed -i 's/document question, a follow-up too, and cite/document question, and cite/' services/chat/brains.py
grep -c "a follow-up too" services/chat/brains.py
```

Then record:

```bash
make replay FILE="$HOME/lesson68.json" FORK="Is it payable to an apprentice?"
```

Then run the restore cell (not recorded) and check it prints `1`:

```bash
git checkout -q -- services/chat/brains.py
grep -c "a follow-up too" services/chat/brains.py
```

Expect run 4's shape. The comparison line is the result: `different steps (ai)` if the model answered the follow-up
without searching, the steps of run 4 if it still searched. Record it as it comes, and say which in the review.

### 6. `data/table_read.txt` (step 8)

Run the step's cell as written (a heredoc in `~/graph-venv`), after run 5. Expect `session <SID>: 10 checkpoints on the
lane; step 6's export holds 10`, `the newest checkpoint names messages version N: a msgpack blob of N bytes, decoded:`
and eight lines, twice `HumanMessage <the question>`, `AIMessage    asks retrieve`, `ToolMessage  N citations`,
`AIMessage    <the answer's first words>`. If the two counts differ, something wrote to the thread between runs 3 and
6: record it anyway and say what.
