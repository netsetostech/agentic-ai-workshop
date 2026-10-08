# Lesson B.5: the live runs the page still needs

The page builds now, with a marked stand-in where each output below belongs: `pb.recorded()` reads the file from
`data/` once it exists, `finish()` names every output still awaited, and `check_lesson.py` notes the count. Two runs,
both on the author's own project. No lane is needed: Basics comes before Module 0.

## Before either run

- **Where:** your laptop, in bash (Git Bash on Windows), from the root of this repository, so that the paths below
  resolve. Make the data folder once: `mkdir -p lessons/B-basics/B.5-decoder-models/data`
- **Python:** the Basics venv: the one the page's setup builds (`~/basics-venv`, numpy 2.5.3 and google-genai 2.22.0),
  or the venv the pages are built with. Both carry pydantic, which google-genai installs.
- **Google:** the setup's second block has run in this shell: Application Default Credentials, `PROJECT` exported, and
  Vertex AI enabled on the project. `echo "$PROJECT"` prints your project id.
- **What the cells print:** answers, token counts and rupees; no project id, project number or email, so nothing needs
  a placeholder before it is committed. Read each file once anyway.
- **One run each:** record the first complete run of each cell. Rerunning for a tidier count would turn the measurement
  into a choice. If a call fails part-way (a 429, an expired sign-in), rerun the whole cell and record that run.
- **The pipe:** each command is the page's cell with `| tr -d '\r' | tee FILE` added to its first line. `tr` strips the
  carriage returns Python writes on Windows, so the file is LF like the rest of the repository; `tee` shows the output
  as it is written.

## 1. `data/five_runs.txt` (step 7: the same prompt, five times)

- **What it is:** the generator's own prompt for golden row lk-06 (clause NP-03), sent five times to gemini-3.6-flash
  on `global` with `_call()`'s config: the kit's `ModelDraft` schema, 2,048 output tokens, thinking level LOW, no
  temperature, top-p, top-k or seed. The cell prints the five answers, how many are distinct, how many state 60, and
  the rupees for the five calls.
- **Cost, from the kit's prices (`shared/prices.py`):** at most Rs 6.53 in output (five calls, each capped at 2,048
  output tokens, thinking included), plus well under a rupee of input. A short answer costs a fraction of that, and
  the cell prints the real figure.
- **Command:**

```bash
python - <<'PY' | tr -d '\r' | tee lessons/B-basics/B.5-decoder-models/data/five_runs.txt
import json, os, re, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # print any character a model writes, Windows included
from typing import List, Literal
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

class DraftCitation(BaseModel):
    """What the model cites: the [Source N] number it saw, and the words it is relying on."""

    source: int = Field(ge=1, description="1-based [Source N] in the context")
    quote: str = Field(max_length=200, description="Exact words from that source")


class ModelDraft(BaseModel):
    """What the model is asked for. Use this as response_schema; resolve() turns it into a
    RAGAnswer. Asking the model for chunk ids or scores directly invites it to invent them."""

    answer: str
    citations: List[DraftCitation]
    confidence: Literal["high", "medium", "low"]
    answerable: bool

PROMPT = """You are DocuMind, a retrieval-grounded assistant.
Rules:
1. Answer ONLY from the numbered context below. Never invent sources.
2. Cite using [N] where N is the chunk number. Multiple chunks: [1,2].
3. If the context does not contain the answer, set answerable=false and say so.
4. Keep answers under 300 words unless asked for more.
5. A quote is the clause that answers - at most twenty-five words, never a whole section.


Context:
[Source 1] hr_policy_2026.md, p.1, NP-03 — Notice period
NP-03 — Notice period
A confirmed employee at grade E3 or above serves a notice period of 60 days. Notice runs
from the date the resignation is acknowledged in writing. Unused earned leave may not be
set off against the notice period.

Question: What is the notice period for a confirmed E3?"""
client = genai.Client(enterprise=True, project=os.environ["PROJECT"], location="global")    # generator.py's _client
config = types.GenerateContentConfig(                     # _call()'s config: no temperature, top_p, top_k or seed
    response_mime_type="application/json", response_schema=ModelDraft, max_output_tokens=2048,
    thinking_config=types.ThinkingConfig(thinking_level="LOW"))
answers, tokens_in, tokens_out = [], 0, 0
for run in range(1, 6):
    r = client.models.generate_content(model="gemini-3.6-flash", contents=[PROMPT], config=config)
    u = r.usage_metadata
    tokens_in += u.prompt_token_count or 0
    tokens_out += (u.candidates_token_count or 0) + (u.thoughts_token_count or 0)   # _usage(): thinking is output
    try:
        answers.append(json.loads(r.text)["answer"])
    except (TypeError, ValueError, KeyError):             # cut off or blocked: no draft to read
        answers.append("(no parseable answer)")
    print(f"run {run}: {answers[-1]}")
distinct = len({" ".join(a.split()) for a in answers})
states_60 = sum(bool(re.search(r"(?<![\w.])60(?![\w]|\.\d)", a.lower())) for a in answers)   # run_eval.py's rule: 60, not 160
rupees = (tokens_in * 1.50 + tokens_out * 7.50) / 1_000_000 * 85           # shared/prices.py
print(f"distinct answers: {distinct} of 5 | answers that state 60 (golden row lk-06): {states_60} of 5")
print(f"five calls: {tokens_in} tokens in, {tokens_out} out (thinking included) | Rs {rupees:.4f} at the kit's prices")
PY
```

## 2. `data/thinking_levels.txt` (step 8: one prompt at LOW and at HIGH)

- **What it is:** the generator's prompt for golden row jn-01 (clauses PB-02 and LV-07), sent once at thinking level
  LOW and once at HIGH, each with 6,144 output tokens of room (the room `generate()` gives its one retry). For each
  level the cell prints the thought, answer and prompt tokens, the finish reason, the rupees and the answer, then
  HIGH's difference in rupees.
- **Cost, from the kit's prices:** at most Rs 7.83 in output (two calls, each capped at 6,144 output tokens, thinking
  included), plus a few paise of input.
- **Command:**

```bash
python - <<'PY' | tr -d '\r' | tee lessons/B-basics/B.5-decoder-models/data/thinking_levels.txt
import json, os, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # print any character a model writes, Windows included
from typing import List, Literal
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

class DraftCitation(BaseModel):
    """What the model cites: the [Source N] number it saw, and the words it is relying on."""

    source: int = Field(ge=1, description="1-based [Source N] in the context")
    quote: str = Field(max_length=200, description="Exact words from that source")


class ModelDraft(BaseModel):
    """What the model is asked for. Use this as response_schema; resolve() turns it into a
    RAGAnswer. Asking the model for chunk ids or scores directly invites it to invent them."""

    answer: str
    citations: List[DraftCitation]
    confidence: Literal["high", "medium", "low"]
    answerable: bool

PROMPT = """You are DocuMind, a retrieval-grounded assistant.
Rules:
1. Answer ONLY from the numbered context below. Never invent sources.
2. Cite using [N] where N is the chunk number. Multiple chunks: [1,2].
3. If the context does not contain the answer, set answerable=false and say so.
4. Keep answers under 300 words unless asked for more.
5. A quote is the clause that answers - at most twenty-five words, never a whole section.


Context:
[Source 1] hr_policy_2026.md, p.1, PB-02 — Probation
PB-02 — Probation
New joiners serve six months on probation at grade E2. During probation the notice
period is 15 days for either side. Probation may be extended once, by up to three
months, with written reasons.

[Source 2] hr_policy_2026.md, p.1, LV-07 — Leave on exit
LV-07 — Leave on exit
Earned leave is encashed on exit at basic pay, capped at 45 days. Leave cannot be
encashed during probation and cannot be used to shorten notice.

Question: If I resign during probation, what notice applies and can I encash leave?"""
client = genai.Client(enterprise=True, project=os.environ["PROJECT"], location="global")    # generator.py's _client
rupees = {}
for level in ("LOW", "HIGH"):                             # the kit's level, then the deepest
    r = client.models.generate_content(model="gemini-3.6-flash", contents=[PROMPT], config=types.GenerateContentConfig(
        response_mime_type="application/json", response_schema=ModelDraft,
        max_output_tokens=6144,                         # the room generate() gives its one retry
        thinking_config=types.ThinkingConfig(thinking_level=level)))
    u = r.usage_metadata
    prompt, answer, thoughts = u.prompt_token_count or 0, u.candidates_token_count or 0, u.thoughts_token_count or 0
    rupees[level] = (prompt * 1.50 + (answer + thoughts) * 7.50) / 1_000_000 * 85   # shared/prices.py
    finish = getattr(r.candidates[0].finish_reason, "name", "UNKNOWN") if r.candidates else "NO_CANDIDATES"
    print(f"{level:4}: thoughts {thoughts} | answer {answer} | prompt {prompt} | finish {finish} | Rs {rupees[level]:.4f}")
    try:
        print("      " + json.loads(r.text)["answer"])
    except (TypeError, ValueError, KeyError):             # cut off or blocked: no draft to read
        print("      (no parseable answer)")
print(f"HIGH cost Rs {rupees['HIGH'] - rupees['LOW']:+.4f} against LOW, at the kit's prices")
PY
```

## After both

Rebuild with the Basics interpreter and check. Keep credentials out of the build; it never calls Google:

```bash
APPDATA=$(mktemp -d) CLOUDSDK_CONFIG=$(mktemp -d) USERPROFILE=$(mktemp -d) PYTHONIOENCODING=utf-8 python pagekit/build.py B.5
python pagekit/check_lesson.py B.5
python pagekit/audit_pages.py B.5
```

The build checks each recorded file's shape (five `run` lines and the two count lines; the LOW and HIGH lines and the
difference) and fails on a file that does not match, so a truncated paste is caught there. When both files are in, the
build prints no "awaiting" line and `check_lesson.py` no note.

While a file is still missing, the build also checks that this list carries its cell verbatim, so a kit change that
alters a cell (the generator's rules, the handbook's clauses, the golden rows, the model, the cap or the prices) fails
the build until the cell here is replaced. `CELLS_ONLY=1 python pagekit/build.py B.5` prints both cells as the page now
has them.
