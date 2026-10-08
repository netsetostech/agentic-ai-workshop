"""Lesson 7.6: A generated image, and its usage row

Do it

Run order inside this file:
1. Do it (source window 13)

Prerequisites: demo_03_the_studio_s_and_the_voice_s_rules_run.
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


def step_01_a_generated_image_and_its_usage_row(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one image, then a DEMO_MODE hit).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: generate 1: {'blob': 'acme/gen/9b79e5785c446f20e956772bbe9e2781.png', 'bucket': 'documind-ai-YOUR-ID-media', 'cached': False}
    generate 2: {'blob': 'acme/gen/9b79e5785c446f20e956772bbe9e2781.png', 'bucket': 'documind-ai-YOUR-ID-media', 'cached': True}
    the usage rows since 2026-09-24T08:10:00Z (Cloud Logging, oldest first):
      tenant acme, modality image, model gemini-3.1-flash-image, cost_usd 0.039, cached False, user documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
      tenant acme, modality image, model gemini-3.1-flash-image, cost_usd 0.0, cached True, user documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
    the audit events since then, in documind-ai-YOUR-ID-audit (kept five 
    """
    import ast, datetime as dt, json, os, subprocess, time, urllib.request
    import google.auth
    from google.auth import impersonated_credentials
    from google.cloud import storage
    P, API = os.environ["PROJECT"], os.environ["API"]
    UI = f"documind-ui-sa@{P}.iam.gserviceaccount.com"
    PROMPT = next(ast.literal_eval(n.value) for n in ast.parse(open("services/frontend/studio.py", encoding="utf-8").read()).body
                  if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "DEFAULT_PROMPT")     # the Studio tab's own prompt
    tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}", f"--impersonate-service-account={UI}"],
                         capture_output=True, text=True, check=True).stdout.strip()
    since = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for n in (1, 2):                                              # the second is DEMO_MODE's to serve
        req = urllib.request.Request(API + "/v1/media/generate", data=json.dumps({"prompt": PROMPT, "tenant_id": "acme"}).encode(),
                                     headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
        body = json.load(urllib.request.urlopen(req, timeout=180))
        print(f"generate {n}: {body}")
    time.sleep(15)                                                # a moment for Cloud Logging to hold the rows
    rows = json.loads(subprocess.run(["gcloud", "logging", "read", 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" '
                                      f'AND jsonPayload.event="media" AND timestamp>="{since}"', f"--project={P}", "--format=json", "--limit=10"],
                                     capture_output=True, text=True, check=True).stdout)
    print(f"the usage rows since {since} (Cloud Logging, oldest first):")
    for e in reversed(rows):
        j = e["jsonPayload"]
        print(f"  tenant {j['tenant']}, modality {j['modality']}, model {j['model']}, cost_usd {j['cost_usd']}, cached {j['cached']}, user {j['user']}")
    start = dt.datetime.fromisoformat(since.replace("Z", "+00:00"))
    events = [json.loads(b.download_as_text()) for b in storage.Client(project=P).bucket(f"{P}-audit").list_blobs(
        prefix=f"{start:%Y/%m/%d}/acme/media.generate-") if b.time_created >= start]
    print(f"the audit events since then, in {P}-audit (kept five years): {len(events)}")
    for ev in events:
        print(f"  {ev['action']} by {ev['actor']['user_email']}: {ev['target']['blob']}, meta {ev['meta']}")
    signer = impersonated_credentials.Credentials(source_credentials=google.auth.default()[0], target_principal=UI, lifetime=900,
                                                  target_scopes=["https://www.googleapis.com/auth/devstorage.read_only"])
    url = storage.Client(project=P, credentials=signer).bucket(body["bucket"]).blob(body["blob"]).generate_signed_url(
        version="v4", expiration=dt.timedelta(minutes=15), method="GET", credentials=signer)
    print(f"the image, for 15 minutes, as documind-ui-sa (the Studio's own signer):\n  {url}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_13', step_01_a_generated_image_and_its_usage_row),
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
