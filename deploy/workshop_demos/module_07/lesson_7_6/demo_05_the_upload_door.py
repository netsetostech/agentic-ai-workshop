"""Lesson 7.6: The upload door

Do it

Run order inside this file:
1. Do it (source window 16)

Prerequisites: demo_04_a_generated_image_and_its_usage_row.
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


def step_01_the_upload_door(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (two refusals, then lesson 7.5's video through the door).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: upload-url townhall.zip as application/zip: (400, "content_type must be one of ['application/pdf', 'audio/mpeg', 'image/jpeg', 'image/png', 'text/markdown', 'text/plain', 'video/mp4']")
    upload-url ../globex/townhall_2026_q1.mp4 as video/mp4: (400, 'filename must be a bare name')
    upload-url townhall_2026_q1.mp4 as video/mp4: 200, a PUT into gs://documind-ai-YOUR-ID-uploads/acme/townhall_2026_q1.mp4, signed for 15 minutes
    PUT 1,474,032 bytes straight to the bucket: HTTP 200
    the worker: {"event": "ingest_duplicate", "doc_key": "acme_2b7f0b3acad009d5e38d869a87861150807d598e862de6d72a5349bafaee97d8"}
    """
    import datetime as dt, hashlib, json, os, subprocess, time, urllib.error, urllib.parse, urllib.request
    P, API = os.environ["PROJECT"], os.environ["API"]
    UI = f"documind-ui-sa@{P}.iam.gserviceaccount.com"
    tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}", f"--impersonate-service-account={UI}"],
                         capture_output=True, text=True, check=True).stdout.strip()
    
    
    def door(filename, content_type):                             # POST /v1/media/upload-url, as a roster member
        """Try the upload contract with this filename and content type and print admission or refusal.
        
        Example: door('townhall_2026_q1.mp4', 'video/mp4')
        """
        q = urllib.parse.urlencode({"filename": filename, "content_type": content_type, "tenant_id": "acme"})
        req = urllib.request.Request(f"{API}/v1/media/upload-url?{q}", data=b"", method="POST", headers={"Authorization": "Bearer " + tok})
        try:
            return 200, json.load(urllib.request.urlopen(req, timeout=60))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode()).get("detail")
    
    
    for fn, ct in (("townhall.zip", "application/zip"), ("../globex/townhall_2026_q1.mp4", "video/mp4")):
        print(f"upload-url {fn} as {ct}: {door(fn, ct)}")
    code, body = door("townhall_2026_q1.mp4", "video/mp4")
    print(f"upload-url townhall_2026_q1.mp4 as video/mp4: {code}, a PUT into gs://{body['bucket']}/{body['blob']}, signed for 15 minutes")
    data = open("evals/corpus/acme/townhall_2026_q1.mp4", "rb").read()        # lesson 7.5's video
    since = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    put = urllib.request.Request(body["url"], data=data, method="PUT", headers={"Content-Type": "video/mp4"})
    print(f"PUT {len(data):,} bytes straight to the bucket: HTTP {urllib.request.urlopen(put, timeout=300).status}")
    key = "acme_" + hashlib.sha256(data).hexdigest()              # the worker's claim key: the bytes' own hash
    for _ in range(30):
        time.sleep(10)
        rows = json.loads(subprocess.run(["gcloud", "logging", "read", 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-ingest" '
                                          f'AND jsonPayload.doc_key="{key}" AND timestamp>="{since}"', f"--project={P}", "--format=json", "--limit=5"],
                                         capture_output=True, text=True, check=True).stdout)
        if rows:
            break
    for e in reversed(rows):
        print("the worker:", json.dumps(e["jsonPayload"]))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_16', step_01_the_upload_door),
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
