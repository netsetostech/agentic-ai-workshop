"""Lesson 3.9: Cost at 10×: the limits the kit declares, and the one it does not

The first cell reads the four ceilings from the kit's files and does the arithmetic for 1k, 10k, 100k and a million claims a month. The second block reads the same values from your lane: the API's scale and concurrency, the deployed index's machine and replicas, and whether quota.tf's override is in your Terraform state.

Run order inside this file:
1. Do it: the ceilings from the kit's files, then your lane's (source window 41)
2. Do it: the ceilings from the kit's files, then your lane's (source window 43)

Prerequisites: demo_06_cost_a_claim_a_month_and_a_floor_at_1k_10k_and_100k_claims.
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


def step_01_the_ceilings_from_the_kit_s_files_then_you(session):
    """Run Do it: the ceilings from the kit's files, then your lane's at this checkpoint.

    The first cell reads the four ceilings from the kit's files and does the arithmetic for 1k, 10k, 100k and a million claims a month. The second block reads the same values from your lane: the API's scale and concurrency, the deployed index's machine and replicas, and whether quota.tf's override is in your Terraform state.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: documind-api: 40 at a time x 20 instances = 800 claims in flight; 0 kept warm; cut at 120 s
    Vector Search: min 1 and max 1 replica: one node answers every claim's search
    quota.tf: 600 generate_content requests a minute for the whole project; GEMINI_QUOTA_OVERRIDE ?= false
    800 slots turn over 16,000 claims a minute at the 3 s SLO and 400 at the 120 s cut; they bind before the quota once a claim takes 80 s
        1,000 a month:  0.023 a minute, one every 2,628.0 s | the quota binds at a busiest minute 26,280.0 x the average; the slots, at 120 s a claim, at 17,520.0 x
       10,000 a month:  0.228 a minute, one every   262.8 s | the quota binds at a busiest minute  2,628.0 x the average; the slots, at
    """
    import re, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    src = lambda p: open(p, encoding="utf-8").read()
    api, vec, quota, mk, alerts = (src(p) for p in ("commands/lesson-12.2.sh", "terraform/vector.tf", "terraform/quota.tf", "Makefile", "terraform/alerts.tf"))
    flag = lambda name: int(re.search(rf"--{name}=(\d+)", api).group(1))
    conc, most, least, timeout = flag("concurrency"), flag("max-instances"), flag("min-instances"), flag("timeout")
    replicas = re.findall(r"(min|max)_replica_count = (\d+)", vec)
    rpm = int(re.search(r'override_value = "(\d+)"', quota).group(1))
    switch = re.search(r"^GEMINI_QUOTA_OVERRIDE \?= (\w+)", mk, re.M).group(1)
    slo = int(re.search(r'"api_latency" \{.*?threshold_value = (\d+)', alerts, re.S).group(1)) / 1000
    slots = conc * most
    print(f"documind-api: {conc} at a time x {most} instances = {slots} claims in flight; {least} kept warm; cut at {timeout} s")
    print(f"Vector Search: {' and '.join(f'{k} {v}' for k, v in replicas)} replica: one node answers every claim's search")
    print(f"quota.tf: {rpm} generate_content requests a minute for the whole project; GEMINI_QUOTA_OVERRIDE ?= {switch}")
    print(f"{slots} slots turn over {slots * 60 / slo:,.0f} claims a minute at the {slo:g} s SLO and {slots * 60 / timeout:,.0f} at the {timeout} s cut;"
          f" they bind before the quota once a claim takes {slots * 60 / rpm:g} s")
    for q in (1_000, 10_000, 100_000, 1_000_000):
        avg = q / (730 * 60)                                              # claims a minute; 730 hours, the price pages' month
        print(f"{q:>9,} a month: {avg:6.3f} a minute, one every {60 / avg:7,.1f} s | the quota binds at a busiest minute"
              f" {rpm / avg:>8,.1f} x the average; the slots, at {timeout} s a claim, at {slots * 60 / timeout / avg:>8,.1f} x")

# Original CLI workflow for step_02_the_ceilings_from_the_kit_s_files_then_you.
COMMANDS_02 = """set +e +o pipefail   # as the page runs it: grep -c prints 0 and exits 1 when the override is not in the state
gcloud run services describe documind-api --region "$REGION" --project "$PROJECT" \\
  --format='yaml(spec.template.spec.timeoutSeconds,spec.template.spec.containerConcurrency,spec.template.metadata.annotations)' \\
  | grep -E 'maxScale|containerConcurrency|timeoutSeconds'
EP=$(terraform -chdir=terraform output -raw vector_index_endpoint)
gcloud ai index-endpoints describe "$(basename "$EP")" --region="$REGION" --project="$PROJECT" \\
  --format='value(deployedIndexes[0].dedicatedResources.machineSpec.machineType,deployedIndexes[0].dedicatedResources.minReplicaCount,deployedIndexes[0].dedicatedResources.maxReplicaCount)'
terraform -chdir=terraform state list | grep -c gemini_rpm
true                 # the cell's status is not grep's: its 0 is the answer


"""

def step_02_the_ceilings_from_the_kit_s_files_then_you(session):
    """Run Do it: the ceilings from the kit's files, then your lane's at this checkpoint.

    The first cell reads the four ceilings from the kit's files and does the arithmetic for 1k, 10k, 100k and a million claims a month. The second block reads the same values from your lane: the API's scale and concurrency, the deployed index's machine and replicas, and whether quota.tf's override is in your Terraform state.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: reads only, nothing changed).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: autoscaling.knative.dev/maxScale: '20'
          containerConcurrency: 40
          timeoutSeconds: 120
    e2-standard-2	1	1
    0
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_41', step_01_the_ceilings_from_the_kit_s_files_then_you),
        ('source_43', step_02_the_ceilings_from_the_kit_s_files_then_you),
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
