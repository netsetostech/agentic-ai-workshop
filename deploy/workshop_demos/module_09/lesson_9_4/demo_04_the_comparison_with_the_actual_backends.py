"""Lesson 9.4: The comparison, with the actual backends

Do it

Run order inside this file:
1. Do it (source window 14)

Prerequisites: demo_03_the_table_s_maths_read.
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


def step_01_the_comparison_with_the_actual_backends(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (20 questions to the API, then to three routes; the GPU wakes; about five minutes).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: backend            rows  groundedness  cite-precision   p95 ms  Rs/1k queries
    ------------------------------------------------------------------------------
    documind-general     20         1.000           1.000     1500          38.69
    documind-slm         20         0.850           1.000     3100         262.77
    documind-inference   20         0.850           1.000     3400          38.50

    what answered each route - the gateway's reply, which the table does not keep:
      documind-general    gemini-3.6-flash            20 rows
      documind-slm        ollama_chat/documind-slm    20 rows
      documind-inference  ollama_chat/documind-slm    20 rows
    the rupees for these rows, the gateway's price against 
    """
    import collections, contextlib, csv, os, subprocess, sys
    P, R = os.environ["PROJECT"], os.environ["REGION"]
    N = subprocess.run(["gcloud", "projects", "describe", P, "--format=value(projectNumber)"], capture_output=True, text=True, check=True).stdout.strip()
    GW, API, UI = f"https://documind-gateway-{N}.{R}.run.app", f"https://documind-api-{N}.{R}.run.app", f"documind-ui-sa@{P}.iam.gserviceaccount.com"
    tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--impersonate-service-account={UI}", f"--audiences={GW}"],
                         capture_output=True, text=True, check=True).stdout.strip()
    os.environ.update(LITELLM_URL=GW, LITELLM_ID_TOKEN=tok, RAG_API_URL=API, DOCUMIND_IMPERSONATE_SA=UI, GOOGLE_CLOUD_PROJECT=P)   # make compare's
    sys.path.insert(0, "services/slm")
    import requests
    import compare_backends as cb
    seen, post = [], requests.post                    # what the table does not keep: the model that answered, and the gateway's price
    
    
    def recorded(url, **kw):
        """Wrap the existing HTTP request to retain the actual backend response used by the comparison.
        
        Example: recorded(url) in the owning lesson/helper context
        """
        r = post(url, **kw)
        if url.endswith("/v1/chat/completions"):
            seen.append((kw["json"]["model"], r.json().get("model"), float(r.headers.get("x-litellm-response-cost") or 0)))
        return r
    
    
    requests.post = recorded
    BACKENDS = "documind-general,documind-slm,documind-inference"
    args = type("Args", (), {"golden": "evals/golden.jsonl", "rows": 20, "backends": BACKENDS})
    with open("compare.csv", "w", newline="", encoding="utf-8") as f, contextlib.redirect_stdout(f):
        cb.live(args)                                 # make compare's own pass, row for row
    rows = list(csv.DictReader(open("compare.csv", encoding="utf-8")))
    cb.print_summary(cb.summarise(rows))
    print("\nwhat answered each route - the gateway's reply, which the table does not keep:")
    for (asked, served), n in sorted(collections.Counter((a, s) for a, s, _ in seen).items(), key=lambda x: BACKENDS.index(x[0][0])):
        print(f"  {asked:19} {served:26} {n:>3} rows")
    print("the rupees for these rows, the gateway's price against the table's:")
    for b in BACKENDS.split(","):
        gw, tb = sum(c for a, _, c in seen if a == b) * cb.USD_INR, sum(float(r["cost_inr"]) for r in rows if r["backend"] == b)
        print(f"  {b:19} Rs {gw:6.2f}   Rs {tb:6.2f}")
    slm = sorted(int(r["latency_ms"]) for r in rows if r["backend"] == "documind-slm")
    print(f"the slowest documind-slm row: {slm[-1] / 1000:.1f} s; the p95 the table prints is row {int(round(0.95 * len(slm)))} of {len(slm)}, "
          f"{slm[int(round(0.95 * len(slm))) - 1] / 1000:.1f} s")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_14', step_01_the_comparison_with_the_actual_backends),
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
