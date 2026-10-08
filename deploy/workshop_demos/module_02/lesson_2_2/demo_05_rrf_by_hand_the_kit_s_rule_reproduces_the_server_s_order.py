"""Lesson 2.2: RRF by hand: the kit's rule reproduces the server's order

Do it: fuse the saved lists, compare with the index's fused list

Run order inside this file:
1. Do it: fuse the saved lists, compare with the index's fused list (source window 20)

Prerequisites: demo_04_three_ways_through_the_index_dense_sparse_only_fused.
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


def step_01_fuse_the_saved_lists_compare_with_the_inde(session):
    """Run Do it: fuse the saved lists, compare with the index's fused list at this checkpoint.

    Do it: fuse the saved lists, compare with the index's fused list

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: the lists are on disk).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the legs differ: True | shared of 20: 0
    by hand, alpha 0.7:
       w0 inv_2026_0412.md                  0.01148   dense rank  1  sparse rank  -
       p23-0 payment_of_bonus_act_1         0.01129   dense rank  2  sparse rank  -
       ...
    the index's fused first five: ['w0 inv_2026_0412.md', 'p23-0 payment_of_bonus_act_1', ...]
    heads agree on 5 of 5 | first is the same: True
    all twenty in the index's order: True
    alpha 1.0 gives the dense list back: True
    alpha 0.0 gives the sparse list back: True
    the bound: dense #1 0.01148, dense #20 0.00875, sparse #1 alone 0.00492
    """
    import json, sys
    sys.path[:0] = [".", "services/rag-api"]
    from hybrid import rrf_fuse
    d = json.load(open("/tmp/legs52.json"))
    name = lambda cid: f"{d['label'][cid][0]} {d['label'][cid][1][:22]}"
    print("the legs differ:", d["dense"] != d["sparse"], "| shared of 20:", len(set(d["dense"]) & set(d["sparse"])))
    fused = rrf_fuse(d["dense"], d["sparse"], alpha=0.7)             # the kit's rule on the two lists you fetched
    print("by hand, alpha 0.7:")
    for cid, score in fused[:5]:
        print(f"   {name(cid):36} {score:.5f}   dense rank {d['dense'].index(cid) + 1 if cid in d['dense'] else '-':>2}  sparse rank {d['sparse'].index(cid) + 1 if cid in d['sparse'] else '-':>2}")
    hand = [cid for cid, _ in fused][:5]
    print("the index's fused first five:", [name(c) for c in d["hybrid"][:5]])
    print("heads agree on", len(set(hand) & set(d["hybrid"][:5])), "of 5 | first is the same:", hand[0] == d["hybrid"][0])
    print("all twenty in the index's order:", [c for c, _ in fused][:20] == d["hybrid"])
    print("alpha 1.0 gives the dense list back:", [c for c, _ in rrf_fuse(d["dense"], d["sparse"], alpha=1.0)][:20] == d["dense"])
    print("alpha 0.0 gives the sparse list back:", [c for c, _ in rrf_fuse(d["dense"], d["sparse"], alpha=0.0)][:20] == d["sparse"])
    print(f"the bound: dense #1 {0.7 / 61:.5f}, dense #20 {0.7 / 80:.5f}, sparse #1 alone {0.3 / 61:.5f}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_20', step_01_fuse_the_saved_lists_compare_with_the_inde),
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
