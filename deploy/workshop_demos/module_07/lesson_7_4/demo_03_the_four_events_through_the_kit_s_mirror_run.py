"""Lesson 7.4: The four events through the kit's mirror, run

Do it

Run order inside this file:
1. Do it (source window 7)

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


def step_01_the_four_events_through_the_kit_s_mirror_r(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the kit's mirror through the four events; no store, no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 1. v1 is ingested: the worker's swap, then after_swap()
         mirror_ok     rag_engine    upsert            v1 uploaded, 73 characters
         mirror_ok     vertex_search upsert            v1 uploaded, 73 characters
       make managed-status: rag_engine    in sync
       make managed-status: vertex_search in sync
    2. v2 replaces it: after_swap(), with v1 in the swap's retired_doc_keys
         mirror_ok     rag_engine    upsert            v2 uploaded, 73 characters
         mirror_ok     vertex_search upsert            v2 uploaded, 73 characters
         mirror_ok     rag_engine    delete:superseded 1
         mirror_ok     vertex_search delete:superseded 1
       make managed-status: rag_engine    in sync
       make managed-
    """
    import json, logging, sys
    from types import SimpleNamespace
    sys.path[:0] = ["services/ingest", "."]
    import managed                                        # the kit's mirror and make managed-status's check; the stores and the ledger are stand-ins
    
    
    class Brief(logging.Handler):                         # the mirror's JSON lines, one short line each
        """Collect a concise trace of mirror decisions in this offline simulation; this does not write a cloud audit record.
        
        Example: Brief()
        """
        def emit(self, r):
            """Print the simulated audit event so the policy decision is visible beside the store operations.
            
            Example: self.emit(r) in the owning lesson/helper context
            """
            j = json.loads(r.getMessage())
            print(f"     {j['event']:13} {j.get('store', ''):13} {j.get('op', ''):17} {j.get('result', j.get('error', ''))}")
    logging.getLogger("documind.ingest").addHandler(Brief())
    logging.getLogger("documind.ingest").setLevel(logging.INFO)
    
    
    class Store:                                          # a store: upsert, delete, and the listing make managed-status reads
        """Simulate a named regional managed store for the real mirror policy functions without making network calls.
        
        Example: Store('rag_engine', 'us-central1')
        """
        def __init__(self, name, region):
            """Initialize this local simulation from the supplied fixture values; no cloud client is created.
            
            Example: Construct the owning class with the arguments shown above; subsequent methods reuse these settings.
            """
            self.name, self.region, self.docs, self.fail_next = name, region, {}, False
    
        def upsert(self, tenant, doc_key, source_uri, text, meta):
            """Record/print the simulated tenant document upsert; no managed GCP store is modified.
            
            Example: self.upsert(tenant, doc_key, source_uri, text, meta) in the owning lesson/helper context
            """
            if self.fail_next:
                self.fail_next = False
                raise TimeoutError("the import did not finish")
            self.docs[doc_key] = text
            return f"{doc_key} uploaded, {len(text)} characters"
    
        def delete(self, tenant, doc_key):
            """Record/print the simulated tenant document deletion for the mirror lifecycle comparison.
            
            Example: self.delete(tenant, doc_key) in the owning lesson/helper context
            """
            return int(self.docs.pop(doc_key, None) is not None)
    
        def listing(self, tenant):
            """Return the simulated store records belonging to this tenant for the freshness check.
            
            Example: self.listing(tenant) in the owning lesson/helper context
            """
            return dict.fromkeys(self.docs)
    
    
    class Table:                                          # the two collections the mirror and status() read: chunks and sources
        """Provide the Firestore-like query surface used by the offline propagation example.
        
        Example: Table(getattr(db, name))
        """
        def __init__(self, rows, filters=()):
            """Initialize this local simulation from the supplied fixture values; no cloud client is created.
            
            Example: Construct the owning class with the arguments shown above; subsequent methods reuse these settings.
            """
            self.rows, self.filters = rows, filters
    
        def where(self, field, op, value):
            """Return a query with the additional equality filter used by this offline Firestore-shaped stub.
            
            Example: self.where(field, op, value) in the owning lesson/helper context
            """
            return Table(self.rows, self.filters + ((field, value),))
    
        def stream(self):
            """Yield simulated document snapshots that satisfy this table's accumulated filters.
            
            Example: self.stream() in the owning lesson/helper context
            """
            return [SimpleNamespace(id=k, to_dict=lambda d=d: dict(d)) for k, d in self.rows.items()
                    if all(d.get(f) == v for f, v in self.filters)]
    
    
    db = SimpleNamespace(chunks={}, sources={})
    db.collection = lambda name: Table(getattr(db, name))
    stores = [Store("rag_engine", "us-central1"), Store("vertex_search", "global")]
    m = managed.Mirror(db, stores, "both", policy_for=lambda tenant: "any", audit=lambda *a, **kw: None)
    URI = "gs://documind-ai-YOUR-ID-uploads/zeta/hr_policy_zeta_2026.md"
    V = {"v1": ["# Zeta HR policy", "A confirmed employee serves a notice period of 30 days."]}
    V["v2"] = [V["v1"][0], V["v1"][1].replace("30 days", "45 days")]
    
    
    def current(key, status="indexed"):                   # the rows after the worker's swap (or make retire), and the ledger row
        """Construct the current source-ledger fact used by the simulated mirror event.
        
        Example: current('v1')
        """
        for k in V:
            for i, text in enumerate(V[k]):
                db.chunks[f"zeta:{k}#{i}"] = {"tenant_id": "zeta", "doc_key": k, "text": text, "kind": "text", "current": k == key and status == "indexed"}
        db.sources["zeta~hr_policy_zeta_2026.md"] = {"tenant_id": "zeta", "doc_key": key, "status": status}
    
    
    def doc(key):
        """Construct the document/chunk fact corresponding to this version key in the offline scenario.
        
        Example: doc('v1')
        """
        return SimpleNamespace(tenant_id="zeta", doc_key=key, gcs_uri=URI, doc_type="policy", effective_from=None)
    
    
    def check():
        """Run the actual freshness check against the current simulated ledger and store contents.
        
        Example: check()
        """
        for s in managed.status(db, stores, "zeta"):
            print(f"   make managed-status: {s['store']:13} {s['status']}" + "".join(f", {k} {s[k + '_doc_keys']}" for k in ("missing", "orphan") if s[k + "_doc_keys"]))
    
    
    print("1. v1 is ingested: the worker's swap, then after_swap()")
    current("v1"); m.after_swap(doc("v1"), "\n\n".join(V["v1"]), {})
    check()
    print("2. v2 replaces it: after_swap(), with v1 in the swap's retired_doc_keys")
    current("v2"); m.after_swap(doc("v2"), "\n\n".join(V["v2"]), {"retired_doc_keys": ["v1"]})
    check()
    print("3. the undo, v1's bytes again: the worker flips the rows back, then after_undo(), which is given no text")
    current("v1"); m.after_undo("zeta", URI, "v1", {"retired_doc_keys": ["v2"]})
    print("   the stores now hold for v1:", {s.name: "..." + s.docs["v1"].split("serves ")[1] for s in stores})
    check()
    print("4. make retire: the rows retired, the ledger row withdrawn, then retired(..., 'withdrawn')")
    current("v1", "withdrawn"); m.retired("zeta", ["v1"], "withdrawn")
    check()
    print("5. make restore, while Vertex AI Search refuses one import: the worker's reactivation, then after_undo()")
    stores[1].fail_next = True
    current("v1"); m.after_undo("zeta", URI, "v1", {"retired_doc_keys": []})
    check()

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_7', step_01_the_four_events_through_the_kit_s_mirror_r),
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
