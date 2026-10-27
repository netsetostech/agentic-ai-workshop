# Lesson 5.1 run list: the live output the page still needs

The page builds without it: the output below shows a marked stand-in, `[awaiting the author's run: data/NAME]`, until
its file exists in `lessons/05-mcp-agents/5.1-agent-loop/data/`. Record it once from your lane, replace every
identifier with the course's placeholders, then rebuild (with the chat venv: the build runs the kit's brains) and check:

    python pagekit/build.py 5.1 && python pagekit/check_lesson.py 5.1 && python pagekit/audit_pages.py 5.1

Everything else on the page is computed when it builds, from the kit: the contract, the chat and rows cells against
stand-ins, and step 7's offline cell, which runs the kit's own LangChain brain (and, build-only, the LangGraph and ADK
brains) on a scripted model against a stand-in rag-api.

The cohort plan puts this run in **batch 2** (Mon 2 - Wed 4 Nov 2026), as "5.1's optional call".

## Before the run

- **The lane:** any lane with Vertex AI enabled; the run calls nothing deployed. It is one model call, with no tool
  executed and no rag-api request.
- **Where:** the operator shell (Cloud Shell or the workstation), in the kit (`~/deploy_module_rag`), after the page's
  shared setup block (lesson 1.1's), which exports `PROJECT`, `REGION=asia-south1` and the rest, and checks `adc ok`:
  the call goes through Application Default Credentials.
- **First:** step 7's venv cell, which makes `~/graph-venv` if it is missing and installs the chat image's pins,
  `langchain-google-genai` and `google-genai` among them (not recorded).
- **What to record:** what the terminal shows for the cell, stdout and stderr together, with nothing trimmed but
  secrets.
- **Placeholders:** project id `documind-ai-YOUR-ID`; project number `NUMBER`. The cell prints neither; check anyway.
  `check_lesson.py` refuses a real project id, a project number in a URL or resource path, a personal mailbox, and
  every string in `.publish-deny`.

## The run

| # | Data file | Page step | Time | Cost |
|---|---|---|---|---|
| 1 | `data/parallel_live.txt` | 7, "Optional: does Gemini ask for two at once?" | seconds | one gemini-3.6-flash call, about Rs 0.2 to Rs 0.7 |

**Where the rupees come from.** `shared/prices.py`: gemini-3.6-flash at $1.50 in and $7.50 out per million tokens, Rs
85 to the dollar. The request is about 1,540 characters (the system prompt 426, the two tool declarations as LangChain
binds them 1,034, the question 81), about 385 tokens at four characters a token. With 200 to 1,000 output tokens,
thinking included (the brains' model thinks at `low`), that is Rs 0.18 to Rs 0.69. The cell prints the real figure.

### 1. `data/parallel_live.txt` (step 7)

The venv cell first (not recorded), then the optional cell (record this one):

```bash
GOOGLE_CLOUD_PROJECT="$PROJECT" ~/graph-venv/bin/python - <<'PY'
import sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = [".", "services/chat"]
from langchain_core.messages import HumanMessage, SystemMessage
import brains, limits, tools
from shared import prices
from shared.profile import build_llm
llm = build_llm().bind_tools(tools.TOOLS)         # the brains' model, gemini-3.6-flash on global, with the kit's two tools
msg = llm.invoke([SystemMessage(content=brains.SYSTEM),
                  HumanMessage(content="How long is my notice period, and how much earned leave is encashed when I leave?")])
print(f"  {brains.MODEL}'s first message: {len(msg.tool_calls)} tool call(s)")
for c in msg.tool_calls:
    print(f"    {c['name']}(" + ", ".join(f"{k}={v!r}" for k, v in c["args"].items()) + ")")
tin, tout, _ = limits.usage_of(msg)               # output counts the thinking tokens
print(f"  {tin} tokens in, {tout} out: Rs {prices.inr(prices.usd(brains.MODEL, tin, tout)):.2f}")
PY
```

(The page's copy of the cell is the one to run; this is the same text.)

Expect `gemini-3.6-flash's first message: N tool call(s)`, one line per call, then the tokens and the rupees. The page
reads right with any of these, and says so: two `retrieve` calls in the one message (a parallel call, the case the
offline cell runs); one `retrieve` whose query names both topics; or one `retrieve` alone (the model would search
again in its next message). If the model asks for `calculate_processing_cost`, or for no tool at all, say so when you
hand the file back: the paragraph under the output would change. The review of 7 October 2026 marked "two calls back
in one message" as model behaviour no lane has shown; this run is that check.
