"""Lesson 7.1: The rules, run

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


def step_01_the_rules_run(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the rules, run; no model, no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: extraction: gemini-3.1-flash-lite, entity types person, org, product, policy, system, location, date
    resolution: normalise(), then text-embedding-005 cosine >= 0.92
      normalise('ACME Pvt. Ltd.'        ) = 'acme'
      normalise('Acme Private Limited'  ) = 'acme'
      normalise('ACME Inc'              ) = 'acme'
      normalise('function head'         ) = 'function head'
      normalise('Function Head'         ) = 'function head'
      normalise('CFO'                   ) = 'cfo'
      normalise('Chief Financial Officer') = 'chief financial officer'
    resolve_entities(), with an embedding that tells every name apart:
      'ACME Pvt. Ltd.'         -> 'ACME Pvt. Ltd.'
      'Acme Private Limited'   -> 'ACME Pvt. Ltd.'
      'ACME 
    """
    import sys
    sys.path[:0] = ["services/ingest", "."]
    import graph                                                   # the kit's own pipeline; nothing below calls a model
    X = graph.GraphExtraction
    print(f"extraction: {graph.EXTRACT_MODEL}, entity types {', '.join(graph.Entity.model_fields['type'].annotation.__args__)}")
    print(f"resolution: normalise(), then {graph.EMBED_MODEL} cosine >= {graph.RESOLVE_THRESHOLD}")
    forms = ["ACME Pvt. Ltd.", "Acme Private Limited", "ACME Inc", "function head", "Function Head", "CFO", "Chief Financial Officer"]
    for f in forms:
        print(f"  normalise({f!r:24}) = {graph.normalise(f)!r}")
    apart = lambda names: [[1.0 if i == j else 0.0 for j in range(len(names))] for i in range(len(names))]
    canon = graph.resolve_entities(forms, apart)                   # an embedding that tells every name apart: only normalise() merges
    print("resolve_entities(), with an embedding that tells every name apart:")
    for f in forms:
        print(f"  {f!r:24} -> {canon[f]!r}")
    ex = [{"chunk_id": "c1", "graph": X.model_validate({"entities": [{"name": "function head", "type": "person"}, {"name": "CFO", "type": "person"},
                                                                     {"name": "Purchase approval", "type": "policy"}],
                                                        "relations": [{"source": "CFO", "target": "Purchase approval", "rel": "APPROVES", "confidence": 0.9},
                                                                      {"source": "CFO", "target": "board", "rel": "REPORTS_TO", "confidence": 0.8}]})},
          {"chunk_id": "c2", "graph": X.model_validate({"entities": [{"name": "Function Head", "type": "person"}, {"name": "Travel reimbursement", "type": "policy"}],
                                                        "relations": [{"source": "Function Head", "target": "Travel reimbursement", "rel": "APPROVES", "confidence": 0.9},
                                                                      {"source": "Function Head", "target": "Function Head", "rel": "IS", "confidence": 0.5}]})}]
    names = [e.name for x in ex for e in x["graph"].entities]
    canon = graph.resolve_entities(names, apart)
    nodes, edges = graph.build_graph(ex, canon)
    print("build_graph() on two passages:")
    for nid, n in sorted(nodes.items(), key=lambda kv: kv[1]["name"]):
        print(f"  node {n['name']!r:24} {n['kind']:7} id {nid[:12]}...  cited by {sorted(n['chunks'])}")
    for (s, d, rel), v in edges.items():
        print(f"  edge {nodes[s]['name']} -[{rel}]-> {nodes[d]['name']}  from {v['chunk_id']}, confidence {v['confidence']}")
    print(f"  {sum(len(x['graph'].relations) for x in ex) - len(edges)} relations dropped: 'board' is no entity (dangling), and Function Head -[IS]-> itself")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_9', step_01_the_rules_run),
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
