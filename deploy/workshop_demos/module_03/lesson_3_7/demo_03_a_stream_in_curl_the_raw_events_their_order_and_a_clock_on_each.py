"""Lesson 3.7: A stream in curl: the raw events, their order, and a clock on each

Do it: one stream, timed, then the query's citations beside it

Run order inside this file:
1. Do it: one stream, timed, then the query's citations beside it (source window 12)

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


def step_01_one_stream_timed_then_the_query_s_citation(session):
    """Run Do it: one stream, timed, then the query's citations beside it at this checkpoint.

    Do it: one stream, timed, then the query's citations beside it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (a Python cell; one stream and one query, two rupees).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: first citation at 1xxx ms | first token at 2xxx ms | done at 4xxx ms | the API's own latency_ms 4xxx
    5 citation events, then 3x token events, then done
       citation 1 #  1 hr_policy_2026.md      kind text effective_from None quote 'NP-03 — Notice period\\nA confirmed em'
       citation 2 #  4 hr_policy_2026.md      kind text effective_from None quote '...'
       ...
    the answer: A confirmed employee in grade E3 must serve a notice period of ... [1] ...
    done: {'tokens_in': 1xxx, 'tokens_out': 4xx, 'cached_tokens': 0, 'model': 'gemini-3.6-flash', 'backend': 'vertex', 'cache_hit': 'none', 'prompt': 'documind-rag@v3'}
    stages: {'policy_fallback': 0, 'retrieval_backend': 'vector', 'retrieve_ms': 6xx, 'pool
    """
    import os, json, time, subprocess, urllib.request
    PROJECT, API = os.environ["PROJECT"], os.environ["API"]
    Q = os.environ.get("Q", "What is the notice period for a confirmed E3?")
    tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}",
                          f"--impersonate-service-account=documind-ui-sa@{PROJECT}.iam.gserviceaccount.com"], capture_output=True, text=True, check=True).stdout.strip()
    H = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
    req = urllib.request.Request(f"{API}/v1/stream", method="POST", headers=H, data=json.dumps({"query": Q, "tenant_id": "acme", "top_k": 5}).encode())
    t0 = time.perf_counter(); ev = None; first = {}; cits, tokens, done, raw = [], [], {}, []
    with urllib.request.urlopen(req, timeout=180) as r:
        for line in r:
            line = line.decode("utf-8").rstrip("\n"); raw.append(line)
            if line.startswith("event: "):
                ev = line[7:]; first.setdefault(ev, round((time.perf_counter() - t0) * 1000))
            elif line.startswith("data: "):
                d = json.loads(line[6:])
                if ev == "citation": cits.append(d)
                elif ev == "token": tokens.append(d["t"])
                elif ev == "done": done = d
    open("/tmp/stream63.txt", "w", encoding="utf-8").write("\n".join(raw) + "\n")
    print(f"first citation at {first.get('citation')} ms | first token at {first.get('token')} ms | done at {first.get('done')} ms | the API's own latency_ms {done.get('latency_ms')}")
    print(f"{len(cits)} citation events, then {len(tokens)} token events, then done")
    for c in cits:
        print(f"   citation {c['n']} #{str(c['chunk_id']).rsplit('#', 1)[-1]:>3} {c['source'].split('/')[-1][:22]:22} kind {c['kind']} effective_from {c.get('effective_from')} quote {c['quote'][:34]!r}")
    print("the answer:", " ".join("".join(tokens).split())[:120], "...")
    print("done:", {k: done.get(k) for k in ("tokens_in", "tokens_out", "cached_tokens", "model", "backend", "cache_hit", "prompt")})
    print("stages:", done.get("stages"))
    req = urllib.request.Request(f"{API}/v1/query", method="POST", headers=H, data=json.dumps({"query": Q, "tenant_id": "acme", "stream": False, "top_k": 5}).encode())
    j = json.load(urllib.request.urlopen(req, timeout=180))
    print(f"the query's answer to the same question: {len(j['citations'])} citations, the ones the model used; the stream's {len(cits)} were the packed set")
    print("saved /tmp/stream63.txt: paste it into the reader in step 1")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_12', step_01_one_stream_timed_then_the_query_s_citation),
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
