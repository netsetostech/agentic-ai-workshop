"""Lesson 4.3: CI: the offline gate on every push, and the job every release needs first

The cell reads both workflow files with the standard library and prints each job: what it needs, whether it signs in to Google, who approves it, and every line that runs an eval. A red row has two honest fixes: correct the system that answered, or correct the row against its clause. The quick, dishonest one is to edit the row until the build is green, and this check exists for that edit. The cell moves lk-06's figure from 60 to 120 days, a figure no acme document holds, then runs the line CI runs. A red row has two honest fixes: correct the system that answered, or correct the row against its clause. The quick, dishonest one is to edit the row until the build is green, and this check exists for that edit. The cell moves lk-06's figure from 60 to 120 days, a figure no acme document holds, then runs the line CI runs. Give the kit its file back:

Run order inside this file:
1. Do it: the pipeline, read from its two files (source window 9)
2. Do it: break a row the way a hand edit would (source window 11)
3. Do it: break a row the way a hand edit would (source window 13)

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


def step_01_the_pipeline_read_from_its_two_files(session):
    """Run Do it: the pipeline, read from its two files at this checkpoint.

    The cell reads both workflow files with the standard library and prints each job: what it needs, whether it signs in to Google, who approves it, and every line that runs an eval.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads the two workflow files; no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: documind-dryrun.yml: on push, pull_request, workflow_dispatch
      tier-a              needs -                  signs in to Google: no
          runs python evals/run_eval.py
    documind-cd.yml: on workflow_dispatch
      eval-gate           needs -                  signs in to Google: no
          runs python evals/run_eval.py
      release-candidate   needs eval-gate          signs in to Google: yes, only if inputs.path == 'candidate'
          runs make eval-live PROJECT="$PROJECT" REGION="$REGION" API="https://candidate---documind-api-$NUMBER.$REGION.run.app"
      promote             needs release-candidate  signs in to Google: yes, then a person (production reviewers)
      release-clouddeploy needs eval-gate          
    """
    import re, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    
    
    def jobs_of(path):
        """A workflow's triggers, then each job: what it needs, its condition, who approves it, whether it signs in to Google, its eval lines.
        
        Example: jobs_of(path)
        """
        lines = [l for l in open(path, encoding="utf-8").read().splitlines() if l.strip() and not l.lstrip().startswith("#")]
        tops = [i for i, l in enumerate(lines) if not l.startswith(" ")] + [len(lines)]
    
        def section(key):
            """Return the lines of one top-level key of a workflow file (on: or jobs:), up to the next top-level key.
            
            Example: section('jobs:')
            """
            i = lines.index(key)
            return lines[i + 1:next(t for t in tops if t > i)]
        triggers = [m.group(1) for l in section("on:") if (m := re.match(r"  ([\w-]+):", l))]
        body = section("jobs:")
        starts = [i for i, l in enumerate(body) if re.fullmatch(r"  [\w-]+:", l)] + [len(body)]
        jobs = []
        for a, b in zip(starts, starts[1:]):
            job = body[a + 1:b]
            key = lambda k: next((l.split(":", 1)[1].split("#")[0].strip() for l in job if l.startswith(f"    {k}:")), "")
            evals = [l.strip().removeprefix("run:").strip() for l in job if "run_eval.py" in l or "make eval-live" in l]
            jobs.append((body[a].strip(" :"), key("needs"), key("if"), key("environment"),
                         any("google-github-actions/auth" in l for l in job), evals))
        return triggers, jobs
    
    
    for path in (".github/workflows/documind-dryrun.yml", ".github/workflows/documind-cd.yml"):
        triggers, jobs = jobs_of(path)
        print(f"{path.rsplit('/', 1)[1]}: on {', '.join(triggers)}")
        for name, needs, cond, env, google, evals in jobs:
            extra = (f", only if {cond.strip('${} ')}" if cond else "") + (f", then a person ({env} reviewers)" if env else "")
            print(f"  {name:19} needs {needs or '-':18} signs in to Google: {'yes' if google else 'no'}{extra}")
            for e in evals:
                print(f"      runs {e}")

# Original CLI workflow for step_02_break_a_row_the_way_a_hand_edit_would.
COMMANDS_02 = """python - <<'PY'
import json, warnings
warnings.filterwarnings("ignore", category=UserWarning)
path, old, new = "evals/golden.jsonl", '"must_contain": ["60"]', '"must_contain": ["120 days"]'
lines = open(path, encoding="utf-8").read().split("\\n")
i = next(k for k, line in enumerate(lines) if line.startswith('{"id": "lk-06",'))
assert old in lines[i], "lk-06 is not as the kit ships it: git checkout evals/golden.jsonl, then run this again"
lines[i] = lines[i].replace(old, new)
open(path, "w", encoding="utf-8", newline="\\n").write("\\n".join(lines))
print("lk-06 now asks for", json.loads(lines[i])["must_contain"])
PY
git diff --stat evals/golden.jsonl
python evals/run_eval.py > /tmp/gate43.txt 2>&1 && s=0 || s=$?; cat /tmp/gate43.txt; echo "exit $s"
[ "$s" -eq 1 ] && grep -q "lk-06: must_contain '120 days' is not in acme's corpus" /tmp/gate43.txt


"""

def step_02_break_a_row_the_way_a_hand_edit_would(session):
    """Run Do it: break a row the way a hand edit would at this checkpoint.

    A red row has two honest fixes: correct the system that answered, or correct the row against its clause. The quick, dishonest one is to edit the row until the build is green, and this check exists for that edit. The cell moves lk-06's figure from 60 to 120 days, a figure no acme document holds, then runs the line CI runs.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (edits one line of your clone on purpose, then runs what CI runs).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: lk-06 now asks for ['120 days']
     evals/golden.jsonl | 2 +-
     1 file changed, 1 insertion(+), 1 deletion(-)
    == eval gate: OFFLINE (no credentials, no cost) ==
      65 golden rows over 3 tenants, 27 documents

      [FAIL] falsifiable
             lk-06: must_contain '120 days' is not in acme's corpus - the row can only fail
      [PASS] anchors
      [PASS] coverage

      1 problem(s). The golden set cannot judge the model until it judges itself.
    exit 1
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_break_a_row_the_way_a_hand_edit_would.
COMMANDS_03 = """git checkout evals/golden.jsonl
python evals/run_eval.py | tail -1; git status --short evals/golden.jsonl

"""

def step_03_break_a_row_the_way_a_hand_edit_would(session):
    """Run Do it: break a row the way a hand edit would at this checkpoint.

    A red row has two honest fixes: correct the system that answered, or correct the row against its clause. The quick, dishonest one is to edit the row until the build is green, and this check exists for that edit. The cell moves lk-06's figure from 60 to 120 days, a figure no acme document holds, then runs the line CI runs. Give the kit its file back:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the kit's file back).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: Updated 1 path from the index
      The golden set is sound. It can go red, and it still contains the rows that would.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_9', step_01_the_pipeline_read_from_its_two_files),
        ('source_11', step_02_break_a_row_the_way_a_hand_edit_would),
        ('source_13', step_03_break_a_row_the_way_a_hand_edit_would),
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
