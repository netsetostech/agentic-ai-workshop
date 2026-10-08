"""Lesson 9.3: The lane's cluster, inspected

Do it

Run order inside this file:
1. Do it (source window 17)
2. Do it (source window 19)

Prerequisites: demo_04_the_manifest_read.
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


def step_01_the_lane_s_cluster_inspected(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (read-only: describes the lane's cluster, looks for the vLLM service and image).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: documind-autopilot: STANDARD, a regional control plane in asia-south1, on documind-vpc, RUNNING
      node pool documind-lab: 1 x e2-standard-2 in asia-south1-a, 30 GB pd-standard, GPU: none
      what it bills while it exists: $0.10 an hour for the control plane (the free tier covers only zonal and Autopilot clusters) + $0.0805 for the node = $0.1805 an hour, Rs 15.34; Rs 11,199 for a 730-hour month, plus the disk
    documind-vllm on Cloud Run (us-central1): not deployed
    the gemma-vllm image in asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind: not built
    """
    import json, os, subprocess
    P, R = os.environ["PROJECT"], os.environ["REGION"]
    
    
    def gc(*args):
        """Run the requested gcloud inspection and return its decoded JSON for this section.
        
        Example: gc('container', 'clusters', 'describe', 'documind-autopilot', '--region', R)
        """
        r = subprocess.run(["gcloud", *args, "--project", P, "--format=json"], capture_output=True, text=True)
        return json.loads(r.stdout) if r.returncode == 0 else None
    
    
    c = gc("container", "clusters", "describe", "documind-autopilot", "--region", R)
    auto = (c.get("autopilot") or {}).get("enabled", False)
    plane = "regional" if c["location"] == R else "zonal"
    print(f"documind-autopilot: {'AUTOPILOT' if auto else 'STANDARD'}, a {plane} control plane in {c['location']}, on {c['network']}, {c['status']}")
    for pool in c.get("nodePools", []):
        cfg = pool["config"]
        print(f"  node pool {pool['name']}: {pool['initialNodeCount']} x {cfg['machineType']} in {', '.join(pool['locations'])}, "
              f"{cfg['diskSizeGb']} GB {cfg['diskType']}, GPU: {cfg.get('accelerators') or 'none'}")
    E2 = {"us-central1": 0.06701142, "asia-south1": 0.08048436}       # e2-standard-2, USD an hour (Compute Engine pricing, 24 September 2026)
    if not auto and plane == "regional" and R in E2:
        hour = 0.10 + E2[R] * c["currentNodeCount"]
        print(f"  what it bills while it exists: $0.10 an hour for the control plane (the free tier covers only zonal and Autopilot "
              f"clusters) + ${E2[R] * c['currentNodeCount']:.4f} for the node = ${hour:.4f} an hour, Rs {hour * 85:.2f}; "
              f"Rs {hour * 85 * 730:,.0f} for a 730-hour month, plus the disk")
    v = gc("run", "services", "describe", "documind-vllm", "--region", "us-central1")
    print("documind-vllm on Cloud Run (us-central1): " + ("deployed" if v else "not deployed"))
    images = gc("artifacts", "docker", "images", "list", f"{R}-docker.pkg.dev/{P}/documind/gemma-vllm")
    print(f"the gemma-vllm image in {R}-docker.pkg.dev/{P}/documind: " + (f"{len(images)} version(s)" if images else "not built"))

def step_02_the_lane_s_cluster_inspected(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (it stops before changing anything on a Standard lab).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: STOP: the Standard CPU lab cannot run the L4 GPU lesson. Set gke_autopilot=true in Terraform, review cluster replacement and quota, and apply before make gke-up.
    make: *** [Makefile:711: gke-up] Error 1
    """
    from workshop_helpers.gates import expect_guard
    expect_guard(session, ["make", "gke-up", "PROJECT=" + session.config.project],
                 stop="STOP: the Standard CPU lab cannot run the L4 GPU lesson")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_17', step_01_the_lane_s_cluster_inspected),
        ('source_19', step_02_the_lane_s_cluster_inspected),
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
