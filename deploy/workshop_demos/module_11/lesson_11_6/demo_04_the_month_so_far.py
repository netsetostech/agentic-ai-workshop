"""Lesson 11.6: The month so far

Do it

Run order inside this file:
1. Do it (source window 11)

Prerequisites: demo_03_the_controls_as_the_kit_writes_them_down.
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


# Original CLI workflow for step_01_the_month_so_far.
COMMANDS_01 = """python - <<'PY'
import datetime as dt, json, os, subprocess
from google.cloud import firestore
P, R = os.environ["PROJECT"], os.environ["REGION"]
def gcloud(*a):
    return subprocess.run(["gcloud", *a], capture_output=True, text=True)
svc = json.loads(gcloud("run", "services", "describe", "documind-api", "--region", R, "--project", P, "--format", "json").stdout)
env = {e["name"]: e.get("value") for e in svc["spec"]["template"]["spec"]["containers"][0].get("env", [])}
month = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m")
snap = firestore.Client(project=P).collection("budget").document(month).get()
usd = float((snap.to_dict() or {}).get("usd", 0.0)) if snap.exists else 0.0
cap = float(env.get("BUDGET_USD") or 100)
pct = float(env["SPEND_PCT"]) if env.get("SPEND_PCT") else 100 * usd / cap
print(f"documind-api: ROUTING={env.get('ROUTING', 'off')}, BUDGET_USD={cap:g}, SPEND_PCT={env.get('SPEND_PCT') or 'unset'}")
print(f"the counter, budget/{month}: USD {usd:.4f} of {cap:g} = {pct:.2f}% - the breaker would read '{'strict' if pct >= 80 else 'normal'}'")
account = gcloud("billing", "projects", "describe", P, "--format=value(billingAccountName)").stdout.strip().rsplit("/", 1)[-1]
b = gcloud("billing", "budgets", "list", f"--billing-account={account}", "--format=json")
if b.returncode != 0:
    print("the billing budget: not readable as you (the Budgets API needs billing.budgets.list on the billing account)")
for budget in json.loads(b.stdout or "[]") if b.returncode == 0 else []:
    if budget.get("displayName") == "DocuMind monthly budget":
        amount = budget["amount"]["specifiedAmount"]
        rules = ", ".join(f"{float(t['thresholdPercent']):.0%}" + (" forecast" if t.get("spendBasis") == "FORECASTED_SPEND" else "")
                          for t in budget.get("thresholdRules", []))
        print(f"the billing budget: {amount.get('units')} {amount.get('currencyCode')} a month on the whole project; emails at {rules}")
PY
make gpu-quota PROJECT="$PROJECT"

"""

def step_01_the_month_so_far(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: documind-api: ROUTING=off, BUDGET_USD=100, SPEND_PCT=unset
    the counter, budget/2026-09: USD 7.8412 of 100 = 7.84% - the breaker would read 'normal'
    the billing budget: 5000 INR a month on the whole project; emails at 50%, 80%, 100%, 120% forecast
    python services/slm/gpu_quota.py --project documind-ai-YOUR-ID --region us-central1

    Total NVIDIA L4 GPU allocation without zonal redundancy
      run.googleapis.com/nvidia_l4_gpu_allocation_no_zonal_redundancy
      1/{project}/{region}         us-central1  effective 3 (default 3)
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_11', step_01_the_month_so_far),
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
