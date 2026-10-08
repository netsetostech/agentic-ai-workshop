"""Lesson 7.3: The mirror's rules, run

Do it

Run order inside this file:
1. Do it (source window 9)

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


def step_01_the_mirror_s_rules_run(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the mirror's rules, run; no store, no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: policy_of: {'None': 'in', 'any': 'any', 'ANY ': 'any', 'us': 'in'}
    permits: {'any -> us-central1': True, 'any -> global': True, 'any -> asia-south1': True, 'in -> us-central1': False, 'in -> global': False, 'in -> asia-south1': True}
    1. acme (any) makes version v1 current:
         mirror_ok              rag_engine    upsert            acme_v1 uploaded
         mirror_ok              vertex_search upsert            acme_v1 uploaded
       held {'rag_engine': 'us-central1', 'vertex_search': 'global'}
    2. globex (in) adds a note:
         mirror_policy_skipped  rag_engine    upsert            in
         mirror_policy_skipped  vertex_search upsert            in
       held {}
    3. globex adds a second note:
       held {}
    4
    """
    import json, logging, sys
    sys.path[:0] = ["services/ingest", "."]
    import managed                                        # the kit's mirror, as the worker holds it; the two stores below are stand-ins
    from shared.tenancy import permits, policy_of
    
    
    class Brief(logging.Handler):                         # the mirror's JSON lines, one short line each
        """Collect a concise trace of mirror decisions in this offline simulation; this does not write a cloud audit record.
        
        Example: Brief()
        """
        def emit(self, r):
            """Print the simulated audit event so the policy decision is visible beside the store operations.
            
            Example: self.emit(r) in the owning lesson/helper context
            """
            j = json.loads(r.getMessage())
            print(f"     {j['event']:22} {j.get('store', ''):13} {j.get('op', ''):17} {j.get('result', j.get('data_region', ''))}")
    logging.getLogger("documind.ingest").addHandler(Brief())
    logging.getLogger("documind.ingest").setLevel(logging.INFO)
    
    
    class Store:                                          # what the Mirror needs of a store: a name, a region, upsert, delete
        """Simulate a named regional managed store for the real mirror policy functions without making network calls.
        
        Example: Store('rag_engine', 'us-central1')
        """
        def __init__(self, name, region):
            """Initialize this local simulation from the supplied fixture values; no cloud client is created.
            
            Example: Construct the owning class with the arguments shown above; subsequent methods reuse these settings.
            """
            self.name, self.region, self.docs = name, region, set()
    
        def upsert(self, tenant, doc_key, source_uri, text, meta):
            """Record/print the simulated tenant document upsert; no managed GCP store is modified.
            
            Example: m.upsert('acme', 'acme_v1', 'gs://b/acme/hr.md', 'Notice period: 60 days.')
            """
            self.docs.add(doc_key)
            return f"{doc_key} uploaded"
    
        def delete(self, tenant, doc_key):
            """Record/print the simulated tenant document deletion for the mirror lifecycle comparison.
            
            Example: self.delete(tenant, doc_key) in the owning lesson/helper context
            """
            gone = doc_key in self.docs
            self.docs.discard(doc_key)
            return int(gone)
    
    
    print("policy_of:", {str(d.get("data_region")): policy_of(d) for d in ({}, {"data_region": "any"}, {"data_region": "ANY "}, {"data_region": "us"})})
    print("permits:", {f"{p} -> {r}": permits(p, r) for p in ("any", "in") for r in ("us-central1", "global", "asia-south1")})
    policy, audit = {"acme": "any", "globex": "in"}, []
    stores = [Store("rag_engine", "us-central1"), Store("vertex_search", "global")]
    m = managed.Mirror(None, stores, "both", policy_for=policy.get,
                       audit=lambda action, actor, target, meta: audit.append(f"{action} {meta['op']} {meta['store']} {target['id']}"))
    print("1. acme (any) makes version v1 current:")
    print("   held", m.upsert("acme", "acme_v1", "gs://b/acme/hr.md", "Notice period: 60 days."))
    print("2. globex (in) adds a note:")
    print("   held", m.upsert("globex", "globex_n1", "gs://b/globex/n1.md", "Visitors sign the register."))
    print("3. globex adds a second note:")
    print("   held", m.upsert("globex", "globex_n2", "gs://b/globex/n2.md", "Badges at all times."))
    policy["acme"] = "in"
    print("4. acme's policy is turned to in, and version v2 becomes current:")
    print("   held", m.upsert("acme", "acme_v2", "gs://b/acme/hr.md", "Notice period: 90 days."))
    print("   the stores still hold", {s.name: sorted(s.docs) for s in stores})
    print("5. v1 is retired:")
    m.retired("acme", ["acme_v1"], "superseded")
    print("   the stores hold", {s.name: sorted(s.docs) for s in stores})
    print("the audit trail:", *audit, sep="\n   ")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_9', step_01_the_mirror_s_rules_run),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=False, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
