"""Lesson 7.1: Read it back: the counts, and one edge with its source

Do it

Run order inside this file:
1. Do it (source window 14)

Prerequisites: demo_04_build_the_handbook_s_graph.
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


def step_01_read_it_back_the_counts_and_one_edge_with(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: tenant acme: 25 nodes, 15 edges in Firestore
    the nodes the most chunks cite:
      Earned leave                     policy  3 chunk(s)
      Notice period                    policy  2 chunk(s)
      function head                    person  2 chunk(s)
      probation                        policy  2 chunk(s)
    one edge, read back with its source chunk:
      CFO -[APPROVES_ABOVE_RS_2_00_000]-> Purchase approval   confidence 0.9
      stated in acme:497809ffbaa6...#9 (FIN-02, hr_policy_2026.md):
        FIN-02 — Purchase approval
        Purchases up to Rs 2,00,000 are approved by the function head. Above that, the CFO
        approves. Splitting a purchase to stay under a threshold is a disciplinary matter.
      both names in the pa
    """
    import os
    from google.cloud import firestore
    from google.cloud.firestore_v1.base_query import FieldFilter
    P, TENANT = os.environ["PROJECT"], "acme"
    db = firestore.Client(project=P)
    q = lambda coll: db.collection(coll).where(filter=FieldFilter("tenant_id", "==", TENANT))
    nodes = {d.get("node_id"): d.to_dict() for d in q("graph_nodes").stream()}
    edges = [d.to_dict() for d in q("graph_edges").stream()]
    print(f"tenant {TENANT}: {len(nodes)} nodes, {len(edges)} edges in Firestore")
    print("the nodes the most chunks cite:")
    for n in sorted(nodes.values(), key=lambda n: (-len(n["chunk_ids"]), n["name"]))[:4]:
        print(f"  {n['name'][:32]:32} {n['kind']:7} {len(n['chunk_ids'])} chunk(s)")
    pick = [e for e in edges if "cfo" in (nodes[e["node_id"]]["name"] + nodes[e["dst_id"]]["name"]).lower()] or sorted(edges, key=lambda e: -e["confidence"])
    e = pick[0]
    src_name, dst_name = nodes[e["node_id"]]["name"], nodes[e["dst_id"]]["name"]
    chunk = db.collection("chunks").document(e["chunk_id"]).get().to_dict() or {}
    print("one edge, read back with its source chunk:")
    print(f"  {src_name} -[{e['rel']}]-> {dst_name}   confidence {e['confidence']}")
    version, n = e["chunk_id"].split("#")
    print(f"  stated in {version[:17]}...#{n} ({chunk.get('locator')}, {chunk.get('source_uri', '').rsplit('/', 1)[-1]}):")
    for line in chunk.get("text", "").splitlines():
        print("    " + line)
    text = " ".join(chunk.get("text", "").split()).lower()          # a name may wrap across a line
    print(f"  both names in the passage as written: {src_name} {'yes' if src_name.lower() in text else 'NO'}, {dst_name} {'yes' if dst_name.lower() in text else 'NO'}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_14', step_01_read_it_back_the_counts_and_one_edge_with),
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
