"""Lesson 12.4: The answer that went wrong, and the row you write from it

Your words, never a user's. The question goes into build_golden.py and your fork's history, so write it yourself. A usage row never carries the question. It names the tenant, the user, the tokens, the model and the prompt version, and the cell below shows that. If a user reports a failure, the row is your own question about the same fact. Then ask the same question once more from the shell. The cell keeps the answer and /version in your home folder for the next cell, and reads the usage row the answer left in Cloud Logging. Then ask the same question once more from the shell. The cell keeps the answer and /version in your home folder for the next cell, and reads the usage row the answer left in Cloud Logging. What a right answer holds. This is lesson 4.1's golden row. A lookup or join row has a must_contain figure and a must_retrieve anchor, both in the tenant's documents. A refusal row has both lists empty, because the documents cannot answer it. Version, isolation and media rows belong to required.json, which lesson 4.1 writes by hand, and improve.py refuses those shapes. Set your values in the first two lines and run the cell. It writes ~/row124.json, the file make improve reads.

Run order inside this file:
1. The answer that went wrong, and the row you write from it (source window 7)
2. The answer that went wrong, and the row you write from it (source window 9)

Prerequisites: setup_prepare.
Use the existing rag-shell-venv interpreter; Run or Debug this file.
The functions below contain the lesson examples in source order. Helpers
supply configuration, authentication, state and CLI execution. See README.md
for expected observations, effects and the next file; GUIDE.md retains prose.
Example: open this file at the matching HTML heading, Run once, then inspect
the observations below before continuing to the next numbered section.
A successful process is not proof that a live result matched the sample.

"""
from workshop_helpers.session import DemoSession
from workshop_helpers.steps import manual_checkpoint, run_steps

# REPEAT replays the whole file; use only after reviewing its effects.
REPEAT = False
# A failed function may have partial effects. Inspect its saved attempt first.
RETRY_FAILED_STEP = False


# Original CLI workflow for step_01_the_answer_that_went_wrong_and_the_row_you.
COMMANDS_01 = """export Q="I am still on probation. If I resign now, how long is my notice?"   # the page's example: write your own question here
curl -s "$API/version" -H "Authorization: Bearer $(tok "$API")" > ~/version124.json
python -c 'import json, os; v = json.load(open(os.path.expanduser("~/version124.json"))); print("serving:", v["prompt"], "|", v["generator_model"], "| git_sha", v["git_sha"])'
curl -s -X POST "$API/v1/query" -H "Authorization: Bearer $(tok "$API")" -H "Content-Type: application/json" \\
  -d "$(python -c 'import json, os; print(json.dumps({"query": os.environ["Q"], "tenant_id": os.environ["TENANT"], "stream": False}))')" > ~/answer124.json
python -c 'import json, os; a = json.load(open(os.path.expanduser("~/answer124.json"))); print("answerable:", a["answerable"], "| citations:", len(a["citations"])); print("answer:", a["answer"])'
sleep 20   # the usage row reaches Cloud Logging
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="query"' \\
  --project "$PROJECT" --limit 1 --format=json | python -c 'import json, sys; r = json.load(sys.stdin)[0]["jsonPayload"]; print("usage row:", {k: r.get(k) for k in ("event", "tenant", "model", "prompt_version", "tokens_in", "tokens_out", "answerable")}); print("the question in the row:", any(k in r for k in ("question", "query")))'

"""

def step_01_the_answer_that_went_wrong_and_the_row_you(session):
    """Run The answer that went wrong, and the row you write from it at this checkpoint.

    Your words, never a user's. The question goes into build_golden.py and your fork's history, so write it yourself. A usage row never carries the question. It names the tenant, the user, the tokens, the model and the prompt version, and the cell below shows that. If a user reports a failure, the row is your own question about the same fact. Then ask the same question once more from the shell. The cell keeps the answer and /version in your home folder for the next cell, and reads the usage row the answer left in Cloud Logging.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one answer from the live revision, then its usage row; about Rs 0.45).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/production_row.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_answer_that_went_wrong_and_the_row_you.
COMMANDS_02 = """export WRONG="It gave the notice of a confirmed employee; the question is about probation."   # yours, in your own words
export SHAPE=lookup CONTAIN='["15"]' RETRIEVE='["PB-02", "hr_policy_2026"]'   # what a right answer holds (lesson 4.1)
python - <<'PY'
import json, os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
home = os.path.expanduser("~")
answer = json.load(open(os.path.join(home, "answer124.json"), encoding="utf-8"))
version = json.load(open(os.path.join(home, "version124.json"), encoding="utf-8"))
row = {"tenant": os.environ["TENANT"], "question": os.environ["Q"], "answer": answer["answer"],
       "citations": answer.get("citations", []), "prompt_version": version["prompt"].split("@")[1],
       "wrong": os.environ.get("WRONG", ""),
       "expected": {"shape": os.environ["SHAPE"], "must_contain": json.loads(os.environ.get("CONTAIN") or "[]"),
                    "must_retrieve": json.loads(os.environ.get("RETRIEVE") or "[]")}}
path = os.path.join(home, "row124.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(row, f, indent=2, ensure_ascii=False)
print(path)
print(json.dumps(row, indent=2, ensure_ascii=False))
PY

"""

def step_02_the_answer_that_went_wrong_and_the_row_you(session):
    """Run The answer that went wrong, and the row you write from it at this checkpoint.

    Then ask the same question once more from the shell. The cell keeps the answer and /version in your home folder for the next cell, and reads the usage row the answer left in Cloud Logging. What a right answer holds. This is lesson 4.1's golden row. A lookup or join row has a must_contain figure and a must_retrieve anchor, both in the tenant's documents. A refusal row has both lists empty, because the documents cannot answer it. Version, isolation and media rows belong to required.json, which lesson 4.1 writes by hand, and improve.py refuses those shapes. Set your values in the first two lines and run the cell. It writes ~/row124.json, the file make improve reads.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (writes ~/row124.json; no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: /home/you/row124.json
    {
      "tenant": "acme",
      "question": "I am still on probation. If I resign now, how long is my notice?",
      "answer": "A confirmed employee at grade E3 or above serves a notice period of 60 days.",
      "citations": [],
      "prompt_version": "v3",
      "wrong": "It gave the notice of a confirmed employee; the question is about probation.",
      "expected": {
        "shape": "lookup",
        "must_contain": [
          "15"
        ],
        "must_retrieve": [
          "PB-02",
          "hr_policy_2026"
        ]
      }
    }
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_7', step_01_the_answer_that_went_wrong_and_the_row_you),
        ('source_9', step_02_the_answer_that_went_wrong_and_the_row_you),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=True, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
