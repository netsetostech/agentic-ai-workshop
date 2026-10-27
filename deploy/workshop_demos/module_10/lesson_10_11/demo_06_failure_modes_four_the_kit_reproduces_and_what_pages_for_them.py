"""Lesson 10.11: Failure modes: four the kit reproduces, and what pages for them

The cell prints the catalog's two silent signals, then gives remediate's rules six states: the kit's recordings of the first three failures, the pinned lane two ways, built as the kit's test builds them, and the rolled-back lane with the failing revision's lines gone from the window. Last, the good revision carries a value with a denied word in it.

Run order inside this file:
1. Do it: the failure modes, offline (source window 55)

Prerequisites: demo_05_architecture_why_rules_and_not_a_model_and_two_more_designs_rejected.
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


def step_01_the_failure_modes_offline(session):
    """Run Do it: the failure modes, offline at this checkpoint.

    The cell prints the catalog's two silent signals, then gives remediate's rules six states: the kit's recordings of the first three failures, the pinned lane two ways, built as the kit's test builds them, and the rolled-back lane with the failing revision's lines gone from the window. Last, the good revision carries a value with a denied word in it.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: silent: 5xx answers: no alert policy the kit declares counts a service's 5xx answers
    silent: chat turns stopped by a limit: every chat row carries stopped_by and no policy counts it yet: an agent alert policy is designed for after 6 December
    a mistyped model                       bad_revision, on 5xx answers
    a call cap                             bad_revision, on chat turns stopped by a limit
    a failure no change explains           no_change, on 5xx answers
    pinned, the change undone              pinned_clean
    pinned, a newer revision that differs  pinned_new
    rolled back, the window gone by        pinned_new
    a denied word in a value: printed; the denylist read gcloud run services update documin
    """
    import copy, importlib.util, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    spec = importlib.util.spec_from_file_location("remediate", "commands/remediate.py")
    rm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rm)
    catalog = rm.load_catalog()
    rows = rm.runbooks(rm.TF_DIR, catalog)
    
    
    def state(name):
        """A recorded lane state from ops/incidents/, read as make remediate OFFLINE=1 reads it.
        
        Example: state('rolled_back')
        """
        return rm.load_state(rm.KIT / "ops" / "incidents" / f"{name}.json")
    
    
    def decided(s):
        """The rule diagnose() chooses for a state, with the signals it fails on.
        
        Example: decided(s)
        """
        d = rm.diagnose(s, rows, catalog)
        return d["rule"] + "".join(f", on {f['label']}" for f in d.get("fails") or [])
    
    
    for s in catalog["silent"]:
        print(f"silent: {s['label']}: {s['why']}")
    pinned = state("rolled_back")                                 # the change undone in a new revision, traffic still pinned
    fix = copy.deepcopy(pinned["revisions"][1])
    fix.update(name="documind-chat-00043-mzq", created="2026-10-12T09:50:10.000001Z")
    pinned["revisions"].append(fix)
    other = copy.deepcopy(pinned)                                 # a newer revision that differs, and has served nothing
    other["revisions"][-1]["env"]["RAG_TIMEOUT_S"] = "30"
    aged = state("rolled_back")                                   # the bad revision's lines older than the window
    aged["lines"] = [x for x in aged["lines"] if x["revision"] != "documind-chat-00042-tvd"]
    cases = {"a mistyped model": state("held_model"), "a call cap": state("held_model_calls"),
             "a failure no change explains": state("old_revision"), "pinned, the change undone": pinned,
             "pinned, a newer revision that differs": other, "rolled back, the window gone by": aged}
    for name, s in cases.items():
        print(f"{name:38} {decided(s)}")
    deny = state("held_model")                                    # a value on the good revision with a denied word in it
    deny["revisions"][1]["env"]["ROLLOUT"] = "canary-deploy"
    plan = rm.render(deny, rm.diagnose(deny, rows, catalog), rows, catalog)
    restore = next(line.strip() for line in plan if "ROLLOUT=canary-deploy" in line)
    print("a denied word in a value: printed; the denylist read", rm.shape_of(restore))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_55', step_01_the_failure_modes_offline),
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
