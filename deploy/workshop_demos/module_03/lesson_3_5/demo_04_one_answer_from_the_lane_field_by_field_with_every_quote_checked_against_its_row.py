"""Lesson 3.5: One answer from the lane, field by field, with every quote checked against its row

Do it: one question, two halves, three rows

Run order inside this file:
1. Do it: one question, two halves, three rows (source window 16)

Prerequisites: demo_03_the_contract_offline_drafts_that_pass_drafts_that_fail_and_the_resolver_on_the_k.
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


def step_01_one_question_two_halves_three_rows(session):
    """Run Do it: one question, two halves, three rows at this checkpoint.

    Do it: one question, two halves, three rows

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; one question and three Firestore reads, a rupee).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the contract: {"answer": "A confirmed employee in grade E3 must serve a notice period of ... [1]...", "citations": "3 citations", "confidence": "high", "answerable": true}
    the envelope: {'model': 'gemini-3.6-flash', 'backend': 'vertex', 'tokens_in': 1xxx, 'tokens_out': 4xx, 'cached_tokens': 0, 'cost_usd': 0.00xxxx, 'latency_ms': 2xxx, 'cache_hit': 'none'}
    [N] marks in the answer: ['1', '2', '3'] | citations returned: 3
       [1] #  1 hr_policy_2026.md        page None score 0.9xxx kind text | row found True | quote in the row True | 1x words
       [2] #  4 hr_policy_2026.md        page None score 0.8xxx kind text | row found True | quote in the row True | 1x words
       [3] #  2 hr_policy_2026.md    
    """
    import os, re, json, subprocess, urllib.request, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    from google.cloud import firestore
    PROJECT, API = os.environ["PROJECT"], os.environ["API"]
    tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}",
                          f"--impersonate-service-account=documind-ui-sa@{PROJECT}.iam.gserviceaccount.com"], capture_output=True, text=True, check=True).stdout.strip()
    req = urllib.request.Request(f"{API}/v1/query", method="POST", headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
                                 data=json.dumps({"query": "What is the notice period for a confirmed E3?", "tenant_id": "acme", "stream": False, "top_k": 3}).encode())
    j = json.load(urllib.request.urlopen(req, timeout=180))
    print("the contract:", json.dumps({"answer": j["answer"][:90] + "...", "citations": f"{len(j['citations'])} citations", "confidence": j["confidence"], "answerable": j["answerable"]}, ensure_ascii=False))
    print("the envelope:", {k: j[k] for k in ("model", "backend", "tokens_in", "tokens_out", "cached_tokens", "cost_usd", "latency_ms", "cache_hit")})
    print("[N] marks in the answer:", sorted(set(re.findall(r"\[(\d+)\]", j["answer"])), key=int), "| citations returned:", len(j["citations"]))
    db = firestore.Client(project=PROJECT)
    norm = lambda s: " ".join(s.split()).lower()
    for i, c in enumerate(j["citations"], 1):
        row = db.collection("chunks").document(c["chunk_id"]).get().to_dict() or {}
        print(f"   [{i}] #{c['chunk_id'].rsplit('#', 1)[1]:>3} {c['source_uri'].split('/')[-1][:24]:24} page {c['page']} score {c['score']:.4f} kind {c['kind']} | row found {bool(row)} | quote in the row {norm(c['quote']) in norm(row.get('text', ''))} | {len(c['quote'].split())} words")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_16', step_01_one_question_two_halves_three_rows),
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
