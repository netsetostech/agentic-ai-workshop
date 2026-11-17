"""Lesson 8.1: REST: the trace hop by hop, and the subscription as Pub/Sub holds it

Three Google APIs, read with your operator token: Cloud Storage for the object, Cloud Logging for the push and the worker's lines, Pub/Sub for the subscription and its topic. The first cell asks Cloud Storage's JSON API for the note's metadata, which is the record the notice carried. Then it asks Cloud Logging for everything documind-ingest logged in the ten minutes after the object was created: the request log entry Cloud Run writes for each POST it receives, and the worker's own JSON lines for this version. It prints them as one timeline, in seconds from the object's creation: Step 4 read what Terraform declared. The platform holds more: every field Google filled in with a default. The cell reads the subscription and its topic from the Pub/Sub API, then reads terraform/eventarc.tf in your clone of the kit and marks each field with who set it:

Run order inside this file:
1. REST: the trace hop by hop, and the subscription as Pub/Sub holds it (source window 18)
2. The subscription, as Pub/Sub holds it (source window 20)

Prerequisites: demo_03_the_ui_one_note_in_its_row_and_an_answer_that_cites_it.
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


def step_01_rest_the_trace_hop_by_hop_and_the_subscrip(session):
    """Run REST: the trace hop by hop, and the subscription as Pub/Sub holds it at this checkpoint.

    Three Google APIs, read with your operator token: Cloud Storage for the object, Cloud Logging for the push and the worker's lines, Pub/Sub for the subscription and its topic. The first cell asks Cloud Storage's JSON API for the note's metadata, which is the record the notice carried. Then it asks Cloud Logging for everything documind-ingest logged in the ten minutes after the object was created: the request log entry Cloud Run writes for each POST it receives, and the worker's own JSON lines for this version. It prints them as one timeline, in seconds from the object's creation:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, a minute after the upload (one Cloud Storage read, one Cloud Logging read).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/trace_timeline.txt]
    """
    import datetime as dt, json, os, subprocess, urllib.parse, urllib.request, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    P, NAME = os.environ["PROJECT"], "acme/pubsub_trace_note.md"
    TOKEN = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
    
    
    def api(url, body=None):
        """GET one Google API URL, or POST it a JSON body, with the operator's token; returns the parsed JSON.
        
        Example: api(f"https://storage.googleapis.com/storage/v1/b/{P}-uploads/o/{urllib.parse.quote(NAME, safe='')}")
        """
        req = urllib.request.Request(url, data=None if body is None else json.dumps(body).encode(),
                                     headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
        return json.load(urllib.request.urlopen(req, timeout=60))
    
    
    def when(stamp):
        """An RFC 3339 time from a Google API as a UTC datetime (nanoseconds cut to microseconds).
        
        Example: when(obj['timeCreated'])
        """
        head, _, frac = stamp.rstrip("Z").partition(".")
        return dt.datetime.fromisoformat(f"{head}.{(frac + '000000')[:6]}+00:00")
    
    
    obj = api(f"https://storage.googleapis.com/storage/v1/b/{P}-uploads/o/{urllib.parse.quote(NAME, safe='')}")
    t0, gen = when(obj["timeCreated"]), str(obj["generation"])
    print(f"gs://{P}-uploads/{NAME}: generation {gen}, {obj['size']} bytes, {obj['contentType']}, created {obj['timeCreated']}")
    iso = lambda t: t.strftime("%Y-%m-%dT%H:%M:%SZ")
    first, last = iso(t0 - dt.timedelta(seconds=5)), iso(t0 + dt.timedelta(minutes=10))
    flt = (f'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-ingest" '
           f'AND timestamp>="{first}" AND timestamp<="{last}"')
    seen = api("https://logging.googleapis.com/v2/entries:list",
               {"resourceNames": [f"projects/{P}"], "filter": flt, "orderBy": "timestamp asc", "pageSize": 500}).get("entries", [])
    ok = [e for e in seen if (e.get("jsonPayload") or {}).get("event") == "ingest_ok"
          and str(e["jsonPayload"].get("generation")) == gen]
    key = ok[0]["jsonPayload"]["doc_key"] if ok else None
    print("seconds after the object was created:")
    for e in seen:
        h, j, at = e.get("httpRequest") or {}, e.get("jsonPayload") or {}, (when(e["timestamp"]) - t0).total_seconds()
        if h.get("requestMethod") == "POST":
            print(f"{at:7.1f}  POST {h.get('status')}, latency {float(str(h.get('latency', '0s')).rstrip('s') or 0):.3f} s (Cloud Run's request log)")
        elif key and (j.get("doc_key") == key or (j.get("event") == "ledger_fingerprint" and j.get("tenant") == "acme")):
            rest = {k: j[k] for k in ("store", "op", "chunks", "reused", "embedded", "generation", "versions") if k in j}
            print(f"{at:7.1f}  {j['event']}  " + "  ".join(f"{k} {v}" for k, v in rest.items()))
    if ok:
        print(f"ingest_ok's generation equals the object's: {str(ok[0]['jsonPayload']['generation']) == gen}; doc_key {key[:13]}...")
    else:
        print(f"no ingest_ok for generation {gen} between {first} and {last}: Cloud Logging can lag a minute; run this again")

def step_02_the_subscription_as_pub_sub_holds_it(session):
    """Run The subscription, as Pub/Sub holds it at this checkpoint.

    Step 4 read what Terraform declared. The platform holds more: every field Google filled in with a default. The cell reads the subscription and its topic from the Pub/Sub API, then reads terraform/eventarc.tf in your clone of the kit and marks each field with who set it:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (two Pub/Sub reads and your clone's eventarc.tf; changes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/subscription_rest.txt]
    """
    import json, os, re, subprocess, urllib.request, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    P = os.environ["PROJECT"]
    TOKEN = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
    
    
    def api(url, body=None):
        """GET one Google API URL, or POST it a JSON body, with the operator's token; returns the parsed JSON.
        
        Example: api(f'https://pubsub.googleapis.com/v1/projects/{P}/subscriptions/documind-ingest-push')
        """
        req = urllib.request.Request(url, data=None if body is None else json.dumps(body).encode(),
                                     headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
        return json.load(urllib.request.urlopen(req, timeout=60))
    
    
    def short(value):
        """A field's value on one line: nested settings flattened, a field the API left out said in words.
        
        Example: short(top.get('messageRetentionDuration'))
        """
        if value is None:
            return "(absent)"
        if isinstance(value, dict):
            return ", ".join(f"{k} {short(v)}" for k, v in value.items()) or "{} (set, and empty: never expires)"
        return str(value)
    
    
    sub = api(f"https://pubsub.googleapis.com/v1/projects/{P}/subscriptions/documind-ingest-push")
    top = api(f"https://pubsub.googleapis.com/v1/projects/{P}/topics/documind-ingest")
    tf = open("terraform/eventarc.tf", encoding="utf-8").read()
    declared = tf.split('resource "google_pubsub_subscription" "ingest_push"', 1)[1].split("\n}\n", 1)[0]
    FIELDS = [("pushConfig", "push_config"), ("ackDeadlineSeconds", "ack_deadline_seconds"), ("retryPolicy", "retry_policy"),
              ("deadLetterPolicy", "dead_letter_policy"), ("messageRetentionDuration", "message_retention_duration"),
              ("retainAckedMessages", "retain_acked_messages"), ("expirationPolicy", "expiration_policy"),
              ("enableMessageOrdering", "enable_message_ordering"),
              ("enableExactlyOnceDelivery", "enable_exactly_once_delivery"), ("filter", "filter")]
    print(f"subscription {sub['name'].rsplit('/', 1)[1]}, topic {sub['topic'].rsplit('/', 1)[1]}, state {sub.get('state')}")
    for rest, arg in FIELDS:
        who = "eventarc.tf" if re.search(rf"^\s*{arg}\b", declared, re.M) else "Google"
        print(f"  {rest:26} {who:12} {short(sub.get(rest))}")
    topic_tf = re.search(r'resource "google_pubsub_topic" "ingest" \{[^}]*\}', tf).group(0)
    print(f"topic {top['name'].rsplit('/', 1)[1]}")
    print(f"  {'messageRetentionDuration':26} {'eventarc.tf' if 'message_retention_duration' in topic_tf else 'Google':12} "
          f"{short(top.get('messageRetentionDuration'))}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_18', step_01_rest_the_trace_hop_by_hop_and_the_subscrip),
        ('source_20', step_02_the_subscription_as_pub_sub_holds_it),
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
