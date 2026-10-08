"""Lesson 7.3: Ask the stores, and find who found the cited chunk

Do it The answer's citation carries no found_by, because the kit's Citation has no such field. The stamp is on the chunk in the pool. This cell asks the API again, then runs the kit's own retrieve() in your shell with backend rag_engine, the call the API made, and looks for the cited chunk in that pool.

Run order inside this file:
1. Do it (source window 17)
2. Do it (source window 19)

Prerequisites: demo_04_the_policies_the_pins_and_the_stores.
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


# Original CLI workflow for step_01_ask_the_stores_and_find_who_found_the_cite.
COMMANDS_01 = """make tenant-backend PROJECT="$PROJECT" TENANT=acme RETRIEVAL_BACKEND=rag_engine     # make up's pin, back
sleep 60      # the API reads a tenant's settings once a minute per instance
ask153() {   # ask153 TENANT...: each tenant's question as documind-ui-sa - the store that served, the answer, the cited chunk
python - "$@" <<'PY'
import json, os, re, subprocess, sys, urllib.request
P, API = os.environ["PROJECT"], os.environ["API"]
Q = {"acme": "How long is the notice period for a confirmed employee?", "zeta": "How long is the notice period for a confirmed employee?",
     "globex": "How much notice does either party give to end the Globex agreement for convenience?"}
tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}",
                      f"--impersonate-service-account=documind-ui-sa@{P}.iam.gserviceaccount.com"],
                     capture_output=True, text=True, check=True).stdout.strip()
short = lambda cid: re.sub(r"([0-9a-f]{8})[0-9a-f]{56}", r"\\1...", cid)      # the version's sha256, cut to 8
for t in sys.argv[1:]:
    req = urllib.request.Request(API + "/v1/query", data=json.dumps({"query": Q[t], "tenant_id": t}).encode(),
                                 headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
    a = json.load(urllib.request.urlopen(req, timeout=180))
    s = a["stages"]
    print(f"{t}: retrieval_backend {s['retrieval_backend']}, policy_fallback {s['policy_fallback']}; pool {s['pool']}, {s['managed_chunks']} from a managed store")
    print(f"  A: {a['answer']}")
    for c in a["citations"]:
        print(f"  cites {short(c['chunk_id'])} ({c['source_uri'].rsplit('/', 1)[-1]})")
PY
}
ask153 acme zeta globex

"""

def step_01_ask_the_stores_and_find_who_found_the_cite(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (acme's pin back to RAG Engine, then one question for each tenant).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: acme: retrieval_backend=rag_engine
    acme: retrieval_backend rag_engine, policy_fallback 0; pool 17, 14 from a managed store
      A: A confirmed employee at grade E3 or above serves a notice period of 60 days [2].
      cites acme:acme_497809ff...#rag-c31c1f459b60 (hr_policy_2026.md)
    zeta: retrieval_backend vertex_search, policy_fallback 0; pool 12, 12 from a managed store
      A: A confirmed employee at grade L4 or above serves a notice period of 30 days [1].
      cites zeta:zeta_e920a147...#vs-9b9cb379153b (hr_policy_zeta_2026.md)
    globex: retrieval_backend vector, policy_fallback 0; pool 20, 0 from a managed store
      A: Either party may terminate the agreement for convenience on 120 days' written notice [
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_ask_the_stores_and_find_who_found_the_cite(session):
    """Run Do it at this checkpoint.

    The answer's citation carries no found_by, because the kit's Citation has no such field. The stamp is on the chunk in the pool. This cell asks the API again, then runs the kit's own retrieve() in your shell with backend rag_engine, the call the API made, and looks for the cited chunk in that pool.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the same question to the API, then through the kit's own retrieve()).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the API: retrieval_backend rag_engine, 14 of the pool's 17 chunks from the store
    the same question through the kit's retrieve(), backend rag_engine: 17 chunks
      found_by rag_engine    14   for example acme:acme_497809ff...#rag-c31c1f459b60
      found_by (none)         3   for example acme:0994e77d...#0
    the chunk the answer cites: acme:acme_497809ff...#rag-c31c1f459b60
      found_by rag_engine, score 0.706 (1 minus its distance), from hr_policy_2026.md
    """
    import json, os, re, subprocess, sys, urllib.request
    P, API = os.environ["PROJECT"], os.environ["API"]
    os.environ["GOOGLE_CLOUD_PROJECT"] = P                  # the kit's settings, read as the API reads them
    sys.path[:0] = [".", "services/rag-api"]
    Q = "How long is the notice period for a confirmed employee?"
    short = lambda cid: re.sub(r"([0-9a-f]{8})[0-9a-f]{56}", r"\1...", cid)
    tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}",
                          f"--impersonate-service-account=documind-ui-sa@{P}.iam.gserviceaccount.com"],
                         capture_output=True, text=True, check=True).stdout.strip()
    req = urllib.request.Request(API + "/v1/query", data=json.dumps({"query": Q, "tenant_id": "acme"}).encode(),
                                 headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
    a = json.load(urllib.request.urlopen(req, timeout=180))
    s = a["stages"]
    print(f"the API: retrieval_backend {s['retrieval_backend']}, {s['managed_chunks']} of the pool's {s['pool']} chunks from the store")
    import retriever                                        # the kit's retrieval stage, run in this shell with your credentials
    pool = retriever.retrieve(Q, "acme", 5, backend="rag_engine")
    kinds = {}
    for c in pool:
        kinds.setdefault(c.get("found_by"), []).append(c)
    print(f"the same question through the kit's retrieve(), backend rag_engine: {len(pool)} chunks")
    for k, v in kinds.items():
        print(f"  found_by {k or '(none)':13} {len(v):2}   for example {short(v[0]['id'])}")
    by_id = {c["id"]: c for c in pool}
    for c in a["citations"]:
        hit = by_id.get(c["chunk_id"])
        print(f"the chunk the answer cites: {short(c['chunk_id'])}")
        if hit:
            print(f"  found_by {hit['found_by']}, score {hit['score']:.3f} (1 minus its distance), from {hit['source_uri'].rsplit('/', 1)[-1]}")
        else:
            print("  not in this pool: ask again (the store answers the same text for the same question)")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_17', step_01_ask_the_stores_and_find_who_found_the_cite),
        ('source_19', step_02_ask_the_stores_and_find_who_found_the_cite),
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
