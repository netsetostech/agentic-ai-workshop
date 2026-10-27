"""Lesson 11.7: The release no gate judged, loud against silent, and what the kit does not do yet

This is the hazard in step 1's red box. make up runs make deploy-services, whose default SCRIPTS include lesson-12.2.sh, the API's deploy. After it the recipe moves documind-api's traffic to the revision it just made, by name (step 4). Lesson 11.2's gate runs on a candidate, and make deploy-services makes none. Add an entry whose drill and check commands/gotchas.py does not run, and the registry refuses to load: make gotchas, every drill and every detector stop with exit 2 and name the problems. commands/tests/test_gotchas.py holds the same rule, in test_a_detector_that_does_not_exist_is_refused, one of its 50 tests. The kit's dry-run workflow runs that file on every push, so a pull request that adds such an entry goes red. The cell copies pinned-traffic as made-up-gotcha, runs the registry, and puts the file back.

Run order inside this file:
1. The release no gate judged (source window 40)
2. Change it: a gotcha with no detector (source window 42)

Prerequisites: demo_08_the_detectors_what_your_lane_shows_now.
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


# Original CLI workflow for step_01_the_release_no_gate_judged.
COMMANDS_01 = """make gotcha-drill ID=ungated-api-release

"""

def step_01_the_release_no_gate_judged(session):
    """Run The release no gate judged at this checkpoint.

    This is the hazard in step 1's red box. make up runs make deploy-services, whose default SCRIPTS include lesson-12.2.sh, the API's deploy. After it the recipe moves documind-api's traffic to the revision it just made, by name (step 4). Lesson 11.2's gate runs on a candidate, and make deploy-services makes none.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a stand-in of Cloud Run; no lane, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: == ungated-api-release, offline (a stand-in, Rs 0): make deploy-services and make up put an ungated API revision live
    documind-api after make release-candidate GIT_SHA=b2c3d4e, the gate and make promote: documind-api-00002-zeq serves 100%, recorded in deploy/.candidate-revision
    a routine deploy from a newer checkout:
    $ make deploy-services GIT_SHA=c3d4e5f   (SCRIPTS: 7 scripts, lesson-12.2.sh among them)
    documind-api: documind-api-00003-rix serves 100%, GIT_SHA c3d4e5f
    detector: documind-api serves documind-api-00003-rix, which this checkout neither recorded as a candidate (documind-api-00002-zeq) nor rolled back to (documind-api-00001-mup): make deploy-services, make up or a hand update-tra
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_change_it_a_gotcha_with_no_detector.
COMMANDS_02 = """set +e +o pipefail   # as the page runs it: its expected output shows a command here failing, as the cell means it to
python - <<'PY'
import json, warnings
warnings.filterwarnings("ignore", category=UserWarning)
path = "ops/gotchas.json"
with open(path, encoding="utf-8") as f:
    reg = json.load(f)
made = json.loads(json.dumps(next(g for g in reg["gotchas"] if g["id"] == "pinned-traffic")))     # a copy of one entry
made["id"], made["title"] = "made-up-gotcha", "A gotcha nobody wrote a drill or a check for"
made["detector"]["run"] = "make gotcha-detect ID=made-up-gotcha PROJECT=documind-ai-YOUR-ID REGION=<region>"
made["drill"]["live"]["run"] = "make gotcha-drill ID=made-up-gotcha LIVE=1 PROJECT=documind-ai-YOUR-ID"
reg["gotchas"].append(made)
with open(path, "w", encoding="utf-8", newline="\\n") as f:
    json.dump(reg, f, indent=2)
    f.write("\\n")
print(f"{path}: {len(reg['gotchas'])} entries, the last one {made['id']}")
PY
python commands/gotchas.py list; echo "exit $?"   # the command make gotchas runs
git checkout -- ops/gotchas.json && python commands/gotchas.py list | head -1
true   # that failure is the cell's answer: compare the output with the page's expected window


"""

def step_02_change_it_a_gotcha_with_no_detector(session):
    """Run Change it: a gotcha with no detector at this checkpoint.

    Add an entry whose drill and check commands/gotchas.py does not run, and the registry refuses to load: make gotchas, every drill and every detector stop with exit 2 and name the problems. commands/tests/test_gotchas.py holds the same rule, in test_a_detector_that_does_not_exist_is_refused, one of its 50 tests. The kit's dry-run workflow runs that file on every push, so a pull request that adds such an entry goes red. The cell copies pinned-traffic as made-up-gotcha, runs the registry, and puts the file back.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (edits ops/gotchas.json, then puts it back; no lane, no cost).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ops/gotchas.json: 14 entries, the last one made-up-gotcha
    STOP: gotchas.json breaks its rules: made-up-gotcha: drill.offline names a drill commands/gotchas.py does not run; made-up-gotcha: detector.kind is check, and commands/gotchas.py has no check for this id
    exit 2
    13 gotchas in ops/gotchas.json (workshop lesson 11.7). make gotchas ID=<id> shows one; make gotcha-drill runs every offline drill, Rs 0
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_40', step_01_the_release_no_gate_judged),
        ('source_42', step_02_change_it_a_gotcha_with_no_detector),
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
