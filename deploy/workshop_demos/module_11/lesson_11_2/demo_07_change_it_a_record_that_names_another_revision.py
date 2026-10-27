"""Lesson 11.2: Change it: a record that names another revision

A copy of your record with one field changed, offered to make promote-gated through GATE_FILE. The cell copies your record to evals/reports/scratch-gate.json with one field changed: the revision, set to the one serving now. It offers the copy to make promote-gated through GATE_FILE, deletes it, and runs gate-check on your own record, which it never touched. The copy is green, fresh, judged by today's rules, and its report still hashes to its sha256: everything in it is true except the name.

Run order inside this file:
1. Change it: a record that names another revision (source window 37)

Prerequisites: demo_06_the_record_read_back_against_cloud_run_and_gate_check_alone.
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


# Original CLI workflow for step_01_change_it_a_record_that_names_another_revi.
COMMANDS_01 = """set +e +o pipefail   # as the page runs it: its expected output shows a command here failing, as the cell means it to
python - <<'PY'
import json, os, subprocess, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P, R = os.environ["PROJECT"], os.environ["REGION"]
svc = json.loads(subprocess.run(["gcloud", "run", "services", "describe", "documind-api", f"--project={P}", f"--region={R}",
                                 "--format=json"], capture_output=True, text=True, check=True).stdout)
serving = max((t for t in svc["status"]["traffic"] if t.get("percent")), key=lambda t: t["percent"])["revisionName"]
rec = json.load(open("evals/reports/gate.json", encoding="utf-8"))
if serving == rec["revision"]:
    raise SystemExit(f"{serving} already serves: there is no other revision to name")
with open("evals/reports/scratch-gate.json", "w", encoding="utf-8") as f:
    json.dump({**rec, "revision": serving}, f, indent=1)
print(f"evals/reports/scratch-gate.json: your record, with {rec['revision']} replaced by {serving}, the revision serving now")
PY
make promote-gated PROJECT="$PROJECT" REGION="$REGION" GATE_FILE=evals/reports/scratch-gate.json; echo "exit $?"
rm -f evals/reports/scratch-gate.json
python commands/release.py gate-check --project "$PROJECT" --region "$REGION" > /dev/null; echo "your record: gate-check exit $?"
true   # that failure is the cell's answer: compare the output with the page's expected window


"""

def step_01_change_it_a_record_that_names_another_revi(session):
    """Run Change it: a record that names another revision at this checkpoint.

    A copy of your record with one field changed, offered to make promote-gated through GATE_FILE. The cell copies your record to evals/reports/scratch-gate.json with one field changed: the revision, set to the one serving now. It offers the copy to make promote-gated through GATE_FILE, deletes it, and runs gate-check on your own record, which it never touched. The copy is green, fresh, judged by today's rules, and its report still hashes to its sha256: everything in it is true except the name.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a copy of your record, refused; it is deleted afterwards).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: evals/reports/scratch-gate.json: your record, with documind-api-00042-xyz replaced by documind-api-00041-kel, the revision serving now
    REFUSED: the gate record evals/reports/scratch-gate.json does not let make promote move traffic:
      - another revision: the record names documind-api-00041-kel, and make promote would move traffic to documind-api-00042-xyz (.candidate-revision). The gate judged documind-api-00041-kel; make gate judges documind-api-00042-xyz
    make: *** [mk/release.mk:46: promote-gated] Error 1
    exit 2
    your record: gate-check exit 0
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_37', step_01_change_it_a_record_that_names_another_revi),
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
