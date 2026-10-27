"""Lesson 11.7: Your two services, as Cloud Run's API returns them

Do it: the two services, before the drills

Run order inside this file:
1. Do it: the two services, before the drills (source window 27)

Prerequisites: demo_05_every_offline_drill_on_a_stand_in_of_cloud_run.
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


def step_01_the_two_services_before_the_drills(session):
    """Run Do it: the two services, before the drills at this checkpoint.

    Do it: the two services, before the drills

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads only: two services and their serving revisions).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/rest_traffic.txt]
    """
    import json, os, subprocess, urllib.request, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    P, R = os.environ["PROJECT"], os.environ["REGION"]
    TOKEN = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
    
    
    def get(kind, name):
        """One object from Cloud Run's Admin API v1, services or revisions: the JSON gcloud's describe prints.
        
        Example: get('services', name)
        """
        url = f"https://{R}-run.googleapis.com/apis/serving.knative.dev/v1/namespaces/{P}/{kind}/{name}"
        req = urllib.request.Request(url, headers={"Authorization": "Bearer " + TOKEN})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    
    
    def env(spec):
        """A revision spec's literal variables, by name; a secret's reference is not one.
        
        Example: env(svc['spec']['template']['spec'])
        """
        return {e["name"]: e.get("value", "") for e in spec["containers"][0].get("env", []) if "valueFrom" not in e}
    
    
    for name in ("documind-chat", "documind-api"):
        svc = get("services", name)
        traffic, made = svc["status"].get("traffic", []), env(svc["spec"]["template"]["spec"])
        print(f"{name}: newest revision {svc['status']['latestCreatedRevisionName']}")
        for t in traffic:
            how = "follows the latest revision" if t.get("latestRevision") else "held by name"
            print(f"  {t.get('percent', 0):>3}%  {t['revisionName']}  {how}" + (f", tag {t['tag']}" if t.get("tag") else ""))
        serving = next((t["revisionName"] for t in traffic if t.get("percent") == 100), None)
        if serving:
            answers = env(get("revisions", serving)["spec"])
            moved = [f"{k} {answers.get(k, 'unset')} -> {made.get(k, 'unset')}" for k in sorted(set(made) | set(answers))
                     if made.get(k) != answers.get(k)]
            print(f"  the template against {serving}: " + ("; ".join(moved) or "the same variables"))
        if name == "documind-chat":
            print(f"  CHAT_MAX_MODEL_CALLS on the template: {made.get('CHAT_MAX_MODEL_CALLS', 'unset (limits.py: 12)')}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_27', step_01_the_two_services_before_the_drills),
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
