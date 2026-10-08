"""Lesson 11.4: Trace it, name the cause, put it back

Do it: the trace Do it: the versions view and the two probes Do it: put version 1 back

Run order inside this file:
1. Do it: the trace (source window 15)
2. Do it: the versions view and the two probes (source window 17)
3. Do it: put version 1 back (source window 20)

Prerequisites: demo_05_break_it_a_version_reaches_the_lane.
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


def step_01_the_trace(session):
    """Run Do it: the trace at this checkpoint.

    Do it: the trace

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the trace: reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: serving: COMMIT, gemini-3.6-flash via vertex, prompt documind-rag@v3, text-embedding-005@1, current-only off, answer cache off
    events since the break: none
    the trail of ~/ask131-after.json, in the order the answer was made:
      1 the answer cache         clean  cache_hit none: retrieval ran
      2 the store and its rungs  clean  vector: 20 of the pool's 20 from its own index; no fallback event
      3 the pool                 clean  20 of the 20 the ablation decided
      4 the reranker             clean  the Ranking API ordered the pool
      5 the version              OFF    acme/hr_policy_2026.md: the ledger's current since 2026-09-23T10:41 is 5560308823a6, not the golden set's 497809ffbaa6; it declares e
    """
    import hashlib, json, os, subprocess, urllib.request
    from google.cloud import firestore
    P, R, API, SINCE = os.environ["PROJECT"], os.environ["REGION"], os.environ["API"], os.environ["SINCE131"]
    def gcloud(*a):
        """Run this cell's gcloud command with its project/region context and decode the requested output.
        
        Example: gcloud('run', 'services', 'describe', 'documind-api', '--region', R, '--project', P, '--format', 'json')
        """
        return subprocess.run(["gcloud", *a], capture_output=True, text=True, check=True).stdout
    tok = gcloud("auth", "print-identity-token", "--include-email", f"--audiences={API}",
                 f"--impersonate-service-account=documind-ui-sa@{P}.iam.gserviceaccount.com").strip()
    def api(path):
        """Read the specified authenticated API path as JSON while tracing the current source version.
        
        Example: api('/version')
        """
        return json.load(urllib.request.urlopen(urllib.request.Request(API + path, headers={"Authorization": "Bearer " + tok}), timeout=60))
    DECIDED = 20      # the pool's depth: config.py's TOP_K_RETRIEVE default, the number evals/ablate.py decided
    RUNG_EVENTS = ("vector_search_fallback", "rag_engine_fallback", "vertex_search_fallback", "retrieval_pin_ignored")
    CAUSE = {"the answer cache": "the answer cache", "the store and its rungs": "a fallback rung", "the pool": "a pool too small",
             "the reranker": "a fallback rung", "the version": "a version", "the model": "the model"}
    
    def read_trail(ans, top_k, events, v):
        """The marks, in the order the answer was made: (link, True clean / False off / None not reached, what it says).
        
        Example: read_trail(ans, top_k, events, v)
        """
        s, hit, none = ans["stages"], ans["cache_hit"] != "none", ans["backend"] == "none"
        pool, backend, fell = s.get("pool", 0), s.get("retrieval_backend"), [e for e in events if e in RUNG_EVENTS]
        marks = [("the answer cache", not hit, "served from the answer cache: an earlier answer, retrieval never ran" if hit
                  else "cache_hit none: retrieval ran")]
        if hit:
            marks += [(link, None, "not reached: retrieval never ran") for link in ("the store and its rungs", "the pool", "the reranker")]
        else:
            own = s.get("vector_chunks", 0) if backend == "vector" else pool
            marks.append(("the store and its rungs", not fell and not s.get("policy_fallback") and own == pool,
                          f"{backend}: {own} of the pool's {pool} from its own index; "
                          + (f"fell back: {', '.join(fell)}" if fell else "no fallback event")
                          + ("; the tenant's data_region sent it to the kit's index" if s.get("policy_fallback") else "")))
            why = (f" (TOP_K_RETRIEVE={top_k} on the revision)" if top_k < DECIDED else
                   " (nothing retrieved: a filter, or no such document)" if not pool else " (retired rows or a filter took the rest)")
            marks.append(("the pool", pool >= DECIDED, f"{pool} of the {DECIDED} the ablation decided" + ("" if pool >= DECIDED else why)))
            marks.append(("the reranker", None if not pool else not s.get("rerank_fallback"),
                          "not reached: nothing to order" if not pool else
                          "the Ranking API did not answer: the pool stood in by retrieval score" if s.get("rerank_fallback")
                          else "the Ranking API ordered the pool"))
        if not v:
            marks.append(("the version", None, "no citation to trace"))
        elif v["cited"] != v["ledger"]:
            marks.append(("the version", False, f"cites {v['cited'][:12]}, a version the ledger has retired; its current is {v['ledger'][:12]}"))
        elif not v["bucket_agrees"]:
            marks.append(("the version", False, "the bucket holds a newer object than the ledger: the last upload never landed"))
        elif v["golden"] and v["ledger"] != v["golden"]:
            marks.append(("the version", False, f"{v['source']}: the ledger's current since {v['since'][:16]} is {v['ledger'][:12]}, "
                          f"not the golden set's {v['golden'][:12]}" + (f"; it declares effective_from {v['effective']}" if v["effective"] else "")))
        else:
            marks.append(("the version", True, f"cites {v['cited'][:12]}, the ledger's current and the golden set's"))
        if none or hit:
            marks.append(("the model", None, "not called: " + ("the empty-pool refusal" if none else "a stored answer")))
        elif not ans["answerable"]:
            marks.append(("the model", False, f"refused with {pool} chunks in the pool: read what was packed, then make judge"))
        else:
            n = len(ans["citations"])
            marks.append(("the model", True, f"answered from {n} citation{'s' if n != 1 else ''}; groundedness is make judge's"))
        return marks
    
    def cause(marks):
        """Classify the observed version/retrieval markers into the kit's wrong-answer cause.
        
        Example: cause(marks)
        """
        off = [(n, link) for n, (link, ok, _) in enumerate(marks, 1) if ok is False]
        if not off:
            return "CAUSE: no link is off - the answer is what the lane holds; if it is still wrong, the golden set or the question is"
        n, link = off[0]
        return f"CAUSE: {CAUSE[link]} (link {n}) - every link before it is clean"
    ans = json.load(open(os.path.expanduser("~/ask131-after.json")))           # the answer that was reported
    ver = api("/version")
    print(f"serving: {ver['git_sha']}, {ver['generator_model']} via {ver['model_backend']}, prompt {ver['prompt']}, "
          f"{ver['embedding']}, current-only {ver['retrieval_current_only']}, answer cache {ver['semantic_cache']}")
    svc = json.loads(gcloud("run", "services", "describe", "documind-api", "--region", R, "--project", P, "--format", "json"))
    env = {e["name"]: e.get("value") for e in svc["spec"]["template"]["spec"]["containers"][0].get("env", [])}
    top_k = int(env.get("TOP_K_RETRIEVE") or 20)                                # config.py's default when the revision sets none
    ors = " OR ".join('jsonPayload.event="%s"' % e for e in RUNG_EVENTS + ("rerank_fallback", "cache_stale"))
    flt = (f'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" '
           f'AND timestamp>="{SINCE}" AND ({ors})')
    events = [e["jsonPayload"]["event"] for e in json.loads(gcloud("logging", "read", flt, "--project", P, "--format", "json") or "[]")]
    print(f"events since the break: {', '.join(events) or 'none'}")
    v = None
    if ans["citations"]:
        c = ans["citations"][0]
        name = c["source_uri"].split("/", 3)[3]                                   # acme/hr_policy_2026.md
        row = firestore.Client(project=P).collection("chunks").document(c["chunk_id"]).get().to_dict() or {}
        led = next(s for s in api("/v1/sources?tenant_id=" + name.split("/")[0])["sources"] if s["name"] == name)
        gen = gcloud("storage", "objects", "describe", c["source_uri"], "--format=value(generation)").strip()
        frozen = "evals/corpus/" + name                                           # the bytes the golden set was written against
        v = {"source": name, "cited": c["chunk_id"].split(":", 1)[1].split("#")[0], "ledger": led["doc_key"].split("_", 1)[1],
             "golden": hashlib.sha256(open(frozen, "rb").read()).hexdigest() if os.path.exists(frozen) else None,
             "since": led["indexed_at"] or "", "effective": row.get("effective_from"), "bucket_agrees": gen == led["generation"]}
    print("the trail of ~/ask131-after.json, in the order the answer was made:")
    marks = read_trail(ans, top_k, events, v)
    for n, (link, ok, said) in enumerate(marks, 1):
        print(f"  {n} {link:24} {'clean' if ok else '-' if ok is None else 'OFF':5}  {said}")
    print(cause(marks))

# Original CLI workflow for step_02_the_versions_view_and_the_two_probes.
COMMANDS_02 = """make sources PROJECT="$PROJECT" TENANT_ONLY=acme | grep -E "^source|hr_policy_2026"
python commands/verify-vector-index.py --deploy-root "$DEMO_ROOT" --project "$PROJECT" --region "$REGION"
GOOGLE_CLOUD_PROJECT="$PROJECT" python commands/check-firestore-fallback.py

"""

def step_02_the_versions_view_and_the_two_probes(session):
    """Run Do it: the versions view and the two probes at this checkpoint.

    Do it: the versions view and the two probes

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the versions view and the two probes; reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: source                                       status                  gen chunks reused embed retired effective  embedding              indexed_at
    acme/hr_policy_2026.md                       indexed    1758624067215604    283    283     0     283 -          text-embedding-005@1   2026-09-23T10:41:07
    Project: documind-ai-YOUR-ID (NUMBER)
    Terraform index: projects/documind-ai-YOUR-ID/locations/asia-south1/indexes/1234567890123456789
    Terraform endpoint: projects/documind-ai-YOUR-ID/locations/asia-south1/indexEndpoints/9876543210987654321
    API index: projects/NUMBER/locations/asia-south1/indexes/1234567890123456789
    API endpoint: projects/NUMBER/locations/asia-south1/indexEndpoints/987654321098765
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_put_version_1_back.
COMMANDS_03 = """make reindex PROJECT="$PROJECT" TENANT=acme FILE=evals/corpus/acme/hr_policy_2026.md
ask131 restored
GOOGLE_CLOUD_PROJECT="$PROJECT" python commands/check-firestore-fallback.py | tail -1

"""

def step_03_put_version_1_back(session):
    """Run Do it: put version 1 back at this checkpoint.

    Do it: put version 1 back

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (version 1 back, the question again, the probe again).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md - waiting for the worker (up to 5 min)
    >> event doc_key chunks reused embedded retired effective_from
    >> ingest_reactivated	acme_497809ffbaa603c4...	283	283	0	283
    >> the gate, scoped to this document, on a candidate: make eval-live PROJECT=documind-ai-YOUR-ID SOURCE=hr_policy_2026.md API=<candidate url>
    A confirmed employee at grade E3 or above serves a notice period of 60 days [1].
      [1] hr_policy_2026.md  version 497809ffbaa6  chunk 1  'serves a notice period of 60 days'
      cache_hit none | backend vertex | answerable True
      store vector | vector_chunks 20 | pool 20 | rerank_fallback 0 | policy_fallback 0
      kept in ~/ask131-restored
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_15', step_01_the_trace),
        ('source_17', step_02_the_versions_view_and_the_two_probes),
        ('source_20', step_03_put_version_1_back),
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
