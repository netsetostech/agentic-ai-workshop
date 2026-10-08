"""Lesson 12.3: Optional: one question, two models

Do it

Run order inside this file:
1. Do it (source window 32)

Prerequisites: optional_demo_07_optional_the_v3_candidate_and_the_gate_on_it.
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


def step_01_optional_one_question_two_models(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — optional: run in the operator shell, in the kit (three questions on each revision; ask again as often as you like).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: Q: Can unused leave shorten my notice period?
      live, as the UI answers (gemini-3.6-flash): 2 citation(s), 2 [N] mark(s), 2100 ms, about Rs 1.06
        No. Unused earned leave may not be set off against the notice period [1], and leave cannot be used to shorten notice [2].
      tuned candidate (endpoint 3784707595493887459): 1 citation(s), 1 [N] mark(s), 1000 ms, about Rs 0.25
        **Answer:** No.
        **Why:** Unused earned leave may not be set off against the notice period [1].
        **Clause:** NP-03, hr_policy_2026.md

    Q: Kya main apni bachi hui leave se notice period chhota kar sakta hoon?
      live, as the UI answers (gemini-3.6-flash): 2 citation(s), 2 [N] mark(s), 2100 ms, about Rs 1.06
        No. U
    """
    import ast, json, os, re, subprocess, sys
    sys.path[:0] = ["evals"]
    from run_eval import ask                         # the gate's own client: POST /v1/query, the call the UI's API receives
    P, R, API = os.environ["PROJECT"], os.environ["REGION"], os.environ["API"]
    CAND = os.environ.get("CAND") or f"https://candidate---documind-api-{os.environ['NUMBER']}.{R}.run.app"
    SA = f"documind-ui-sa@{P}.iam.gserviceaccount.com"
    token = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}", f"--impersonate-service-account={SA}"],
                           capture_output=True, text=True, check=True).stdout.strip()
    mine = os.path.expanduser("~/demo_questions.txt")                      # your own questions, one a line, asked instead
    QUESTIONS = [q.strip() for q in open(mine, encoding="utf-8") if q.strip()] if os.path.exists(mine) else [
        "Can unused leave shorten my notice period?",                             # golden jn-02: in neither training file
        "Kya main apni bachi hui leave se notice period chhota kar sakta hoon?",  # the same question, in Hinglish
        "How much is ACME's referral bonus?"]                                      # the handbook names it, and never says
    tree = ast.parse(open("services/rag-api/cost.py", encoding="utf-8").read())
    PRICE = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "FALLBACK")
    for q in QUESTIONS:
        print(f"\nQ: {q}")
        for name, url in (("live, as the UI answers", API), ("tuned candidate", CAND)):
            status, body, ms = ask(url, q, "acme", SA, token)
            if status != 200:
                print(f"  {name}: HTTP {status}")
                continue
            tuned = body["model"].startswith("projects/")
            usd_in, usd_out = PRICE["gemini-3.1-flash-lite" if tuned else "gemini-3.6-flash"]
            rs = (body["tokens_in"] * usd_in + body["tokens_out"] * usd_out) * (1.5 if tuned else 1.0) / 1e6 * 85   # a tuned endpoint: 1.5 x
            marks = len(re.findall(r"\[(\d+(?:\s*,\s*\d+)*)\]", body["answer"]))
            model = "endpoint " + body["model"].rsplit("/", 1)[1] if tuned else body["model"]
            print(f"  {name} ({model}): {len(body['citations'])} citation(s), {marks} [N] mark(s), {ms} ms, about Rs {rs:.2f}")
            print("    " + body["answer"].replace("\n", "\n    "))
    svc = json.loads(subprocess.run(["gcloud", "run", "services", "describe", "documind-api", "--region", R, "--project", P, "--format=json"],
                                    capture_output=True, text=True, check=True).stdout)
    live = max((t for t in svc["status"]["traffic"] if t.get("percent")), key=lambda t: t["percent"])
    print(f"\nthe UI's URL sends {live['percent']}% of its traffic to {live['revisionName']}; the candidate answers only at its own URL")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_32', step_01_optional_one_question_two_models),
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
