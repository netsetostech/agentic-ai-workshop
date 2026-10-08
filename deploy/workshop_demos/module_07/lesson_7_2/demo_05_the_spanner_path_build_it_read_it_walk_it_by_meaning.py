"""Lesson 7.2: The Spanner path: build it, read it, walk it by meaning

Do it The CFO's edge came back two ways. As tables, GraphEdge is joined to GraphNode twice, for the names at both ends. As a graph, the kit's GQL walk goes from the CFO. Both reach Purchase approval and FIN-02. Now the kit's question, seeded by meaning. On Spanner, --ask prints the five nearest names, each with its distance and whether it passed 0.4. Then it walks from the names that passed.

Run order inside this file:
1. Do it (source window 15)
2. Do it (source window 17)

Prerequisites: demo_04_the_firestore_path_a_name_the_question_contains.
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


# Original CLI workflow for step_01_the_spanner_path_build_it_read_it_walk_it.
COMMANDS_01 = """make graph PROJECT="$PROJECT" TENANT=acme GRAPH_BACKEND=spanner GRAPH_ARGS="--source hr_policy_2026.md --rebuild"
python - <<'PY'
import os, sys
sys.path.insert(0, ".")
from google.cloud import firestore, spanner
from google.cloud.spanner_v1 import param_types as T
from shared.documind_graph import SpannerGraph
P, TENANT = os.environ["PROJECT"], "acme"
db = spanner.Client(project=P).instance("documind-graph").database("documind")
fs = firestore.Client(project=P)
loc = lambda cid: (fs.collection("chunks").document(cid).get().to_dict() or {}).get("locator")
p, t = {"t": TENANT}, {"t": T.STRING}
with db.snapshot(multi_use=True) as s:                         # one consistent read of both tables
    nodes, vectors, dims = list(s.execute_sql('SELECT COUNT(*), COUNTIF(embedding IS NOT NULL), MAX(ARRAY_LENGTH(embedding)) FROM GraphNode WHERE tenant_id = @t',
                                              params=p, param_types=t))[0]
    edges = list(s.execute_sql('SELECT COUNT(*) FROM GraphEdge WHERE tenant_id = @t', params=p, param_types=t))[0][0]
    named = list(s.execute_sql('SELECT n.node_id, n.name, e.rel, d.name, e.chunk_id FROM GraphEdge e '
                               'JOIN GraphNode n ON n.tenant_id = e.tenant_id AND n.node_id = e.node_id '
                               'JOIN GraphNode d ON d.tenant_id = e.tenant_id AND d.node_id = e.dst_id '
                               'WHERE e.tenant_id = @t ORDER BY n.name, e.rel', params=p, param_types=t))
print(f"tenant {TENANT}: {nodes} nodes ({vectors} with a {dims}-number vector), {edges} edges in Spanner")
cfo = [r for r in named if "cfo" in (r[1] + " " + r[3]).lower()] or named[:1]
print("the edges that name the CFO, as tables (the names joined from GraphNode):")
for nid, a, rel, b, cid in cfo:
    print(f"  {a} -[{rel}]-> {b}   stated in {loc(cid)}")
walked = SpannerGraph(db).expand([cfo[0][0]], TENANT, hops=1)       # the same rows as a graph: the kit's GQL walk
print(f"one hop from {cfo[0][1]}, by the kit's GQL walk: {', '.join(n['name'] for n in walked)}")
print(f"  the chunks they cite: {', '.join(sorted({loc(c) for n in walked for c in n['chunk_ids']}))}")
PY

"""

def step_01_the_spanner_path_build_it_read_it_walk_it(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the same graph written to Spanner, then read back).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: cd services/ingest && GOOGLE_CLOUD_PROJECT=documind-ai-YOUR-ID PYTHONPATH=../.. \\
      SPANNER_INSTANCE=documind-graph SPANNER_DATABASE=documind \\
      python graph.py --project documind-ai-YOUR-ID --tenant acme --backend spanner --source hr_policy_2026.md --rebuild
    11 current text chunks for tenant 'acme' from 'hr_policy_2026.md'
    {"event": "graph_extracted", "tenant": "acme", "chunks": 11, "extracted": 11, "fresh": 0}
    {"event": "graph_built", "tenant": "acme", "backend": "spanner", "chunks": 11, "surface_forms": 28, "nodes": 25, "edges": 15}
    tenant acme: 25 nodes (25 with a 768-number vector), 15 edges in Spanner
    the edges that name the CFO, as tables (the names joined from GraphNode):
      CFO -[AP
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_spanner_path_build_it_read_it_walk_it.
COMMANDS_02 = """make graph PROJECT="$PROJECT" TENANT=acme GRAPH_BACKEND=spanner GRAPH_ARGS='--ask "Who signs off on a big purchase?"'

"""

def step_02_the_spanner_path_build_it_read_it_walk_it(session):
    """Run Do it at this checkpoint.

    The CFO's edge came back two ways. As tables, GraphEdge is joined to GraphNode twice, for the names at both ends. As a graph, the kit's GQL walk goes from the CFO. Both reach Purchase approval and FIN-02. Now the kit's question, seeded by meaning. On Spanner, --ask prints the five nearest names, each with its distance and whether it passed 0.4. Then it walks from the names that passed.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one walk of the Spanner graph, seeded by meaning; one embedding call).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: cd services/ingest && GOOGLE_CLOUD_PROJECT=documind-ai-YOUR-ID PYTHONPATH=../.. \\
      SPANNER_INSTANCE=documind-graph SPANNER_DATABASE=documind \\
      python graph.py --project documind-ai-YOUR-ID --tenant acme --backend spanner --ask "Who signs off on a big purchase?"
    {
     "question": "Who signs off on a big purchase?",
     "backend": "spanner",
     "seeded_by": "meaning",
     "seed_distance": 0.4,
     "nearest": [
      {
       "name": "Purchase approval",
       "kind": "policy",
       "distance": 0.183,
       "seeded": true
      },
      {
       "name": "CFO",
       "kind": "person",
       "distance": 0.415,
       "seeded": false
      },
      {
       "name": "approved cloud bucket",
       "kind": "system",
       "distance": 0.434,
       "seeded": false
      },
 
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_15', step_01_the_spanner_path_build_it_read_it_walk_it),
        ('source_17', step_02_the_spanner_path_build_it_read_it_walk_it),
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
