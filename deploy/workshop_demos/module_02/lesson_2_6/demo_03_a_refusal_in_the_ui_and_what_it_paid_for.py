"""Lesson 2.6: A refusal in the UI, and what it paid for

First the row's truth, from the file every eval reads: First the row's truth, from the file every eval reads: Then the question as documind-ui-sa, through /v1/query, which generates, and /v1/passages, which stops at the reranker:

Run order inside this file:
1. Do it: the golden row, and the same question from the shell (source window 6)
2. Do it: the golden row, and the same question from the shell (source window 8)

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


# Original CLI workflow for step_01_the_golden_row_and_the_same_question_from.
COMMANDS_01 = """python -c "import json; print(json.dumps(next(r for r in map(json.loads, open('evals/golden.jsonl', encoding='utf-8')) if r['id'] == 'rf-01'), indent=1))"

"""

def step_01_the_golden_row_and_the_same_question_from(session):
    """Run Do it: the golden row, and the same question from the shell at this checkpoint.

    First the row's truth, from the file every eval reads:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: one line of the golden set).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: {
     "id": "rf-01",
     "shape": "refusal",
     "question": "What is ACME's sabbatical policy?",
     "tenant": "acme",
     "must_contain": [],
     "must_retrieve": [],
     "answerable": false,
     "note": "Was 'parental leave' until the real Maternity Benefit Acts joined ACME's corpus, which made twenty-six weeks a defensible answer. A refusal row has to ask for something the corpus really does not hold."
    }
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_the_golden_row_and_the_same_question_from(session):
    """Run Do it: the golden row, and the same question from the shell at this checkpoint.

    First the row's truth, from the file every eval reads: Then the question as documind-ui-sa, through /v1/query, which generates, and /v1/passages, which stops at the reranker:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell: one generator call, about Rs 0.23 of input by the kit's own count and at most Rs 1.31 of output; the passages call costs nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/ui_refusal.txt]
    """
    import json, os, subprocess, sys, urllib.request, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path.insert(0, ".")
    from shared.prices import USD_INR, usd
    PROJECT, API = os.environ["PROJECT"], os.environ["API"]
    Q = "What is ACME's sabbatical policy?"                              # golden row rf-01: answerable false
    tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}",
                          f"--impersonate-service-account=documind-ui-sa@{PROJECT}.iam.gserviceaccount.com"],
                         capture_output=True, text=True, check=True).stdout.strip()
    
    
    def post(route, body):
        """POST one JSON body to the API as documind-ui-sa and return the decoded reply.
        
        Example: post('/v1/query', {'query': Q, 'tenant_id': 'acme', 'stream': False, 'top_k': 5})
        """
        req = urllib.request.Request(f"{API}{route}", data=json.dumps(body).encode(), method="POST",
                                     headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
        return json.load(urllib.request.urlopen(req, timeout=180))
    
    
    a = post("/v1/query", {"query": Q, "tenant_id": "acme", "stream": False, "top_k": 5})
    s = a["stages"]
    print(f"/v1/query     answerable {a['answerable']} | confidence {a['confidence']} | citations {len(a['citations'])} | backend {a['backend']} | model {a['model']}")
    print(f"              pool {s['pool']} | retrieve_ms {s['retrieve_ms']} | rerank_ms {s['rerank_ms']} | generate_ms {s['generate_ms']}")
    print(f"              tokens {a['tokens_in']} in + {a['tokens_out']} out | cost_usd on the answer: {a['cost_usd']} | "
          f"priced by shared/prices.py: Rs {usd(a['model'], a['tokens_in'], a['tokens_out']) * USD_INR:.4f}")
    print(f"              answer: {a['answer'][:100]}")
    p = post("/v1/passages", {"query": Q, "tenant_id": "acme", "top_k": 5})
    u = p["usage"]
    print(f"/v1/passages  passages {len(p['passages'])} | answerable {p['answerable']} | model {u['model']} | cost_usd {u['cost_usd']} | "
          f"retrieve_ms {u['stages']['retrieve_ms']} | rerank_ms {u['stages']['rerank_ms']}")
    for x in p["passages"]:
        print(f"   [{x['n']}] {x['source_uri'].split('/')[-1][:30]:30} {x['text'][:56]!r}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_6', step_01_the_golden_row_and_the_same_question_from),
        ('source_8', step_02_the_golden_row_and_the_same_question_from),
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
