"""Lesson 2.1: Before you run anything: set up the shell

Continue only after PASS. Keep Acme on vector through steps 3–9. The API environment's RETRIEVAL_BACKEND is a default; the tenant pin overrides it. If step 3 still reports the old backend, wait for that one-minute cache to expire, then retry. This is a configuration repair for an existing index, not an index-creation step. Read the ID from the intended Terraform state and prove that it is deployed on the same endpoint. The following block refuses an endpoint mismatch or missing deployment. It creates a corrected API revision and routes 100% of the demo service's traffic to it. Other environment variables are retained; do not rerun the full infrastructure deployment to fix this one setting.

Run order inside this file:
1. Run first: check the serving revision and save the original pin (source window 5)

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

    Continue only after PASS. Keep Acme on vector through steps 3–9. The API environment's RETRIEVAL_BACKEND is a default; the tenant pin overrides it. If step 3 still reports the old backend, wait for that one-minute cache to expire, then retry. This is a configuration repair for an existing index, not an index-creation step. Read the ID from the intended Terraform state and prove that it is deployed on the same endpoint. The following block refuses an endpoint mismatch or missing deployment. It creates a corrected API revision and routes 100% of the demo service's traffic to it. Other environment variables are retained; do not rerun the full infrastructure deployment to fix this one setting.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — optional repair; updates the API revision and its traffic.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    import json, os, subprocess, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    from google.cloud import aiplatform
    project, region = os.environ["PROJECT"], os.environ["REGION"]
    def run(args):
        """Run the specified CLI argument list and return its output; propagate command failures.
        
        Example: run(['gcloud', 'run', 'services', 'update', 'documind-api'] + flags + [f'--update-env-vars=VECTOR_DEPLOYED_INDEX_ID={deployed_id}', '--no-traffic', '--format=value(status.latestCreatedRevisionName)'])
        """
        return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()
    def output(name):
        """Read the named Terraform output used to identify the actual deployed vector resources.
        
        Example: output('vector_index_endpoint')
        """
        return run(["terraform", "-chdir=terraform", "output", "-raw", name])
    endpoint_name = output("vector_index_endpoint")
    deployed_id = output("vector_deployed_index_id")
    flags = [f"--project={project}", f"--region={region}"]
    service = json.loads(run(["gcloud", "run", "services", "describe", "documind-api"] + flags + ["--format=json"]))
    traffic = [t for t in service["status"].get("traffic", []) if t.get("percent", 0) > 0]
    if len(traffic) != 1 or traffic[0].get("percent") != 100:
        raise SystemExit("STOP: inspect split traffic before a repair.")
    serving = traffic[0]["revisionName"]
    if service["status"].get("latestCreatedRevisionName") != serving:
        raise SystemExit("STOP: a different candidate revision exists; inspect it before updating the service template.")
    env = {e["name"]: e.get("value", "") for e in
           service["spec"]["template"]["spec"]["containers"][0].get("env", [])}
    if env.get("VECTOR_INDEX_ENDPOINT") != endpoint_name:
        raise SystemExit("STOP: API and Terraform endpoints differ; inspect the intended state before repair.")
    aiplatform.init(project=project, location=region)
    endpoint = aiplatform.MatchingEngineIndexEndpoint(endpoint_name)
    if deployed_id not in [d.id for d in endpoint.deployed_indexes]:
        raise SystemExit("STOP: Terraform's ID is not deployed here. Inspect the infrastructure setup.")
    print("Verified deployed ID:", deployed_id, flush=True)
    revision = run(["gcloud", "run", "services", "update", "documind-api"] + flags +
                   [f"--update-env-vars=VECTOR_DEPLOYED_INDEX_ID={deployed_id}", "--no-traffic",
                    "--format=value(status.latestCreatedRevisionName)"])
    if not revision:
        raise SystemExit("STOP: no revision returned; inspect Cloud Run before changing traffic.")
    subprocess.run(["gcloud", "run", "services", "update-traffic", "documind-api"] + flags +
                   [f"--to-revisions={revision}=100"], check=True)
    print("Rerun the preflight block to verify the serving configuration before step 3.")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_5', step_01_run_first_check_the_serving_revision_and_s),
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
