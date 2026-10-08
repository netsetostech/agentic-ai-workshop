"""Lesson 2.1: Before you run anything: set up the shell

Run in $DEMO_ROOT. This reads the single revision receiving traffic, checks that its deployed ID exists, saves only the relevant settings under operator-evidence/lesson51/, and then selects vector for Acme. Empty optional settings take their code defaults. It stops before any embedding or tenant change if the deployment is invalid. A split-traffic service needs a chosen revision before this single-revision demonstration can proceed.

Run order inside this file:
1. Run first: check the serving revision and save the original pin (source window 4)

Prerequisites: workshop setup; see this lesson README.
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


def step_01_run_first_check_the_serving_revision_and_s(session):
    """Run Run first: check the serving revision and save the original pin at this checkpoint.

    Run in $DEMO_ROOT. This reads the single revision receiving traffic, checks that its deployed ID exists, saves only the relevant settings under operator-evidence/lesson51/, and then selects vector for Acme. Empty optional settings take their code defaults. It stops before any embedding or tenant change if the deployment is invalid. A split-traffic service needs a chosen revision before this single-revision demonstration can proceed.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run before step 3; reads configuration and saves/sets the Acme pin.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    import json, os, subprocess, warnings
    from pathlib import Path
    warnings.filterwarnings("ignore", category=UserWarning)
    from google.cloud import aiplatform
    from shared.tenancy import backend_for, set_backend
    
    project, region = os.environ["PROJECT"], os.environ["REGION"]
    flags = [f"--project={project}", f"--region={region}", "--format=json"]
    def read_run(kind, name):
        """Read the requested Cloud Run resource as JSON to inspect its deployed configuration.
        
        Example: read_run('services', 'documind-api')
        """
        return json.loads(subprocess.run(
            ["gcloud", "run", kind, "describe", name] + flags,
            check=True, capture_output=True, text=True).stdout)
    
    service = read_run("services", "documind-api")
    # One service, two URLs: status.url (often the hashed a.run.app one) and the
    # deterministic documind-api-NUMBER.REGION.run.app that API is built from.
    urls = {service["status"]["url"].rstrip("/"), f"https://documind-api-{os.environ['NUMBER']}.{region}.run.app"}
    if os.environ["API"].rstrip("/") not in urls:
        raise SystemExit(f"STOP: API={os.environ['API']} is not one of this service's URLs: {sorted(urls)}")
    traffic = [t for t in service["status"].get("traffic", []) if t.get("percent", 0) > 0]
    if len(traffic) != 1 or traffic[0].get("percent") != 100:
        raise SystemExit("STOP: inspect split traffic; this demo expects one serving revision.")
    revision = traffic[0]["revisionName"]
    env = {e["name"]: e.get("value", "") for e in
           read_run("revisions", revision)["spec"]["containers"][0].get("env", [])}
    cfg = {"project": project, "api": os.environ["API"], "revision": revision,
           "endpoint": env.get("VECTOR_INDEX_ENDPOINT", ""),
           "deployed_id": env.get("VECTOR_DEPLOYED_INDEX_ID", ""),
           "mode": env.get("RETRIEVAL_MODE") or "dense",
           "current_only": env.get("RETRIEVAL_CURRENT_ONLY") or "off",
           "top_k": int(env.get("TOP_K_RETRIEVE") or 20),
           "embed_model": env.get("EMBEDDING_MODEL") or "text-embedding-005",
           "graph": env.get("RETRIEVAL_GRAPH") or "off"}
    print(json.dumps(cfg, indent=2))
    if not cfg["endpoint"] or not cfg["deployed_id"]:
        raise SystemExit("STOP: the serving revision has no complete Vector Search configuration.")
    if cfg["current_only"] not in ("on", "off") or cfg["top_k"] < 1:
        raise SystemExit("STOP: invalid current-only or pool-size setting.")
    aiplatform.init(project=project, location=region)
    endpoint = aiplatform.MatchingEngineIndexEndpoint(cfg["endpoint"])
    deployed = [d.id for d in endpoint.deployed_indexes]
    print("Actual deployed IDs:", deployed)
    if cfg["deployed_id"] not in deployed:
        raise SystemExit("STOP: API deployed ID is absent. Use the repair note below, then rerun this block.")
    
    os.environ["GOOGLE_CLOUD_PROJECT"] = project
    evidence = Path("operator-evidence/lesson51")
    evidence.mkdir(parents=True, exist_ok=True)
    backup = evidence / "pin-before.json"
    current = backend_for("acme") or "default"
    if backup.exists():
        before = json.loads(backup.read_text())
        if before["project"] != project or current not in (before["backend"], "vector"):
            raise SystemExit("STOP: saved pin belongs to a different project or the pin changed independently.")
    else:
        before = {"project": project, "backend": current}
        with backup.open("x") as f:
            json.dump(before, f)
    (evidence / "settings.json").write_text(json.dumps(cfg, indent=2))
    print("Original Acme pin:", before["backend"])
    print("Acme demo pin:", set_backend("acme", "vector"))
    print("PASS: index configuration verified. Allow up to 60 seconds for the API's tenant-setting cache.")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_4', step_01_run_first_check_the_serving_revision_and_s),
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
