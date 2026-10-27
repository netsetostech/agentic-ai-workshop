"""Lesson 8.1: The burst: thirty-one objects against five instances

Why squeeze. A bus that pushes has to learn how fast its reader can go, and it learns only from the answers. Pub/Sub starts a subscription's push window small, widens it with each success and narrows it with each failure (Google's push page). Cloud Run holds a request that finds no free instance in its pending queue and then refuses it with a 429. The subscription counts each refusal as a failed delivery, retries it after the backoff, and charges it against the 12 attempts; the comment in step 4's subscription is the kit's record of a first live load that learned this the hard way. At 30 in flight, 31 messages are 2 rounds of work; at 5 they are at least 7, and they have to queue. Squeezing the ceiling makes the reader the bottleneck, so you can watch the bus adapt to it. Why the corpus. make ingest-corpus uploads the kit's corpus again: by upload.sh's rule, 21 objects for acme, 3 for globex and 7 for zeta, 31 in all. Each upload is a new generation, so each fires a notice, and each notice is pushed until the worker takes it. But the bytes are the ones your lane indexed when it was built, so every claim is already taken: the worker downloads the generation, hashes it, finds the claim and answers 200 duplicate. Nothing is parsed, nothing is embedded and no model is called. The burst costs deliveries and nothing else, as long as that "every" holds, and the first cell checks it before anything moves: The ceiling is a setting of the worker's revision: the same --max-instances flag lesson-12.5.sh deploys with. Changing it deploys a new revision with the same image and the same environment. Google recommends a service-level maximum for most uses, which needs no new revision (its maximum-instances page); the revision's flag is used here so that the restore at the end puts back exactly what the kit deployed. The ceiling is a setting of the worker's revision: the same --max-instances flag lesson-12.5.sh deploys with. Changing it deploys a new revision with the same image and the same environment. Google recommends a service-level maximum for most uses, which needs no new revision (its maximum-instances page); the revision's flag is used here so that the restore at the end puts back exactly what the kit deployed. Now note the time and upload the corpus. Keep this shell open: the next three cells read BURST_SINCE. If the shell does close, export it again with the time this cell printed. Give it two minutes, then read every request Cloud Run received for the worker since BURST_SINCE, by status and by ten-second slice, with the worker's verdicts for the same window: Pub/Sub keeps its own counts for each subscription: the backlog (messages not yet acknowledged), the age of the oldest of them, and every push it made, by how the push ended. Cloud Run counts its instances the same way. These metrics are sampled every 60 seconds and can take up to 120 seconds to appear (Google's list of metrics), so run this cell at least three minutes after the upload: Put the ceiling back

Run order inside this file:
1. The burst: thirty-one objects against five instances (source window 27)
2. Squeeze, then upload (source window 29)
3. Squeeze, then upload (source window 31)
4. What the worker saw (source window 33)
5. What Pub/Sub saw (source window 36)
6. Put the ceiling back (source window 38)

Prerequisites: demo_06_direct_reads_the_records_the_push_left_and_the_answer_through_the_api.
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


def step_01_the_burst_thirty_one_objects_against_five(session):
    """Run The burst: thirty-one objects against five instances at this checkpoint.

    Why squeeze. A bus that pushes has to learn how fast its reader can go, and it learns only from the answers. Pub/Sub starts a subscription's push window small, widens it with each success and narrows it with each failure (Google's push page). Cloud Run holds a request that finds no free instance in its pending queue and then refuses it with a 429. The subscription counts each refusal as a failed delivery, retries it after the backoff, and charges it against the 12 attempts; the comment in step 4's subscription is the kit's record of a first live load that learned this the hard way. At 30 in flight, 31 messages are 2 rounds of work; at 5 they are at least 7, and they have to queue. Squeezing the ceiling makes the reader the bottleneck, so you can watch the bus adapt to it. Why the corpus. make ingest-corpus uploads the kit's corpus again: by upload.sh's rule, 21 objects for acme, 3 for globex and 7 for zeta, 31 in all. Each upload is a new generation, so each fires a notice, and each notice is pushed until the worker takes it. But the bytes are the ones your lane indexed when it was built, so every claim is already taken: the worker downloads the generation, hashes it, finds the claim and answers 200 duplicate. Nothing is parsed, nothing is embedded and no model is called. The burst costs deliveries and nothing else, as long as that "every" holds, and the first cell checks it before anything moves:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (hashes your clone's corpus against the ledger; writes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/burst_precheck.txt]
    """
    import hashlib, os, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    from google.cloud import firestore
    db = firestore.Client(project=os.environ["PROJECT"])
    
    
    def would_upload(tenant_dir):
        """evals/upload.sh's rule for one tenant: every file, but a .md whose .pdf or .mp4 twin exists, and a .segments.json.
        
        Example: would_upload(folder)
        """
        out = []
        for name in sorted(os.listdir(tenant_dir)):
            path = os.path.join(tenant_dir, name)
            stem, ext = os.path.splitext(path)
            if not os.path.isfile(path) or name.endswith(".segments.json"):
                continue
            if ext == ".md" and (os.path.isfile(stem + ".pdf") or os.path.isfile(stem + ".mp4")):
                continue
            out.append(name)
        return out
    
    
    total, same, other = 0, 0, []
    for tenant in sorted(os.listdir("evals/corpus")):
        folder = os.path.join("evals/corpus", tenant)
        if not os.path.isdir(folder):
            continue
        names = would_upload(folder)
        total += len(names)
        print(f"{tenant}: {len(names)} objects")
        for name in names:
            sha = hashlib.sha256(open(os.path.join(folder, name), "rb").read()).hexdigest()
            row = db.document(f"sources/{tenant}~{name}").get().to_dict() or {}
            if row.get("status") == "indexed" and row.get("sha256") == sha:
                same += 1
            else:
                other.append(f"{tenant}/{name}: the ledger holds {row.get('status') or 'nothing'}"
                             + (f", sha256 {str(row.get('sha256'))[:8]}..., this file {sha[:8]}..." if row else ""))
    print(f"{same} of {total} files are the version the ledger holds current" + (": every delivery will be a duplicate" if same == total else ""))
    for line in other:
        print("  differs:", line)

# Original CLI workflow for step_02_squeeze_then_upload.
COMMANDS_02 = """gcloud run services update documind-ingest --region "$REGION" --project "$PROJECT" --max-instances=5
gcloud run services describe documind-ingest --region "$REGION" --project "$PROJECT" \\
  --format='yaml(status.latestReadyRevisionName,spec.template.metadata.annotations)' | grep -E 'latestReadyRevisionName|maxScale'

"""

def step_02_squeeze_then_upload(session):
    """Run Squeeze, then upload at this checkpoint.

    The ceiling is a setting of the worker's revision: the same --max-instances flag lesson-12.5.sh deploys with. Changing it deploys a new revision with the same image and the same environment. Google recommends a service-level maximum for most uses, which needs no new revision (its maximum-instances page); the revision's flag is used here so that the restore at the end puts back exactly what the kit deployed.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (a new revision of the worker, the same image; a minute).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/burst_squeeze.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_squeeze_then_upload.
COMMANDS_03 = """export BURST_SINCE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"; echo "BURST_SINCE=$BURST_SINCE"
make ingest-corpus PROJECT=$PROJECT

"""

def step_03_squeeze_then_upload(session):
    """Run Squeeze, then upload at this checkpoint.

    The ceiling is a setting of the worker's revision: the same --max-instances flag lesson-12.5.sh deploys with. Changing it deploys a new revision with the same image and the same environment. Google recommends a service-level maximum for most uses, which needs no new revision (its maximum-instances page); the revision's flag is used here so that the restore at the end puts back exactly what the kit deployed. Now note the time and upload the corpus. Keep this shell open: the next three cells read BURST_SINCE. If the shell does close, export it again with the time this cell printed.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (31 uploads, every one already indexed).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: BURST_SINCE=YYYY-MM-DDTHH:MM:SSZ
    PROJECT_ID=documind-ai-YOUR-ID bash evals/upload.sh
    project : documind-ai-YOUR-ID
    bucket  : gs://documind-ai-YOUR-ID-uploads

    ==> acme (21 files) -> gs://documind-ai-YOUR-ID-uploads/acme/
        annual_report_2026.md
        annual_report_2026_fig3.png
        cgst_act_2017.pdf
        code_on_social_security_2020.pdf
        code_on_wages_2019.pdf
        dpdp_act_2023.pdf
        hr_policy_2026.md
        industrial_relations_code_2020.pdf
        inv_2026_0412.md
        inv_2026_0412.png
        it_act_2000.pdf
        labour_codes_compliance_handbook.pdf
        maternity_benefit_act_1961.pdf
        maternity_benefit_amendment_act_2017.pdf
        msa_acme_2026.md
        osh_code_2020.pdf
        payment_of_bonus_act_
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def step_04_what_the_worker_saw(session):
    """Run What the worker saw at this checkpoint.

    Give it two minutes, then read every request Cloud Run received for the worker since BURST_SINCE, by status and by ten-second slice, with the worker's verdicts for the same window:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, two minutes after the upload (Cloud Logging reads; changes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/burst_requests.txt]
    """
    import collections, datetime as dt, json, os, statistics, subprocess, urllib.request, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    P, SINCE = os.environ["PROJECT"], os.environ["BURST_SINCE"]
    TOKEN = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
    
    
    def api(url, body=None):
        """GET one Google API URL, or POST it a JSON body, with the operator's token; returns the parsed JSON.
        
        Example: api('https://logging.googleapis.com/v2/entries:list', body)
        """
        req = urllib.request.Request(url, data=None if body is None else json.dumps(body).encode(),
                                     headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
        return json.load(urllib.request.urlopen(req, timeout=60))
    
    
    def when(stamp):
        """An RFC 3339 time from a Google API as a UTC datetime (nanoseconds cut to microseconds).
        
        Example: when(SINCE)
        """
        head, _, frac = stamp.rstrip("Z").partition(".")
        return dt.datetime.fromisoformat(f"{head}.{(frac + '000000')[:6]}+00:00")
    
    
    def entries(flt):
        """Every Cloud Logging entry that matches a filter, oldest first, page by page.
        
        Example: entries(f'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-ingest" AND timestamp>="{SINCE}"')
        """
        out, page = [], None
        while True:
            body = {"resourceNames": [f"projects/{P}"], "filter": flt, "orderBy": "timestamp asc", "pageSize": 1000}
            if page:
                body["pageToken"] = page
            r = api("https://logging.googleapis.com/v2/entries:list", body)
            out += r.get("entries", [])
            page = r.get("nextPageToken")
            if not page:
                return out
    
    
    t0 = when(SINCE)
    seen = entries(f'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-ingest" AND timestamp>="{SINCE}"')
    posts = [(when(e["timestamp"]), int(e["httpRequest"].get("status", 0)), float(str(e["httpRequest"].get("latency", "0s")).rstrip("s") or 0))
             for e in seen if (e.get("httpRequest") or {}).get("requestMethod") == "POST"]
    verdicts = collections.Counter(e["jsonPayload"]["event"] for e in seen
                                   if str((e.get("jsonPayload") or {}).get("event", "")).startswith("ingest_"))
    print(f"deliveries to documind-ingest since {SINCE}: {len(posts)}")
    for status in sorted({s for _, s, _ in posts}):
        mine = [p for p in posts if p[1] == status]
        print(f"  HTTP {status}: {len(mine):3}, the first at +{(mine[0][0] - t0).total_seconds():.0f} s, the last at "
              f"+{(mine[-1][0] - t0).total_seconds():.0f} s, median latency {statistics.median(p[2] for p in mine):.2f} s")
    slices = collections.defaultdict(collections.Counter)
    for t, s, _ in posts:
        slices[int((t - t0).total_seconds()) // 10 * 10][s] += 1
    print("by ten-second slice after BURST_SINCE:")
    for b in sorted(slices):
        print(f"  +{b:4} s  " + "  ".join(f"HTTP {s} x{n}" for s, n in sorted(slices[b].items())))
    print("the worker's verdicts: " + (", ".join(f"{k} {v}" for k, v in sorted(verdicts.items())) or "none"))

def step_05_what_pub_sub_saw(session):
    """Run What Pub/Sub saw at this checkpoint.

    Pub/Sub keeps its own counts for each subscription: the backlog (messages not yet acknowledged), the age of the oldest of them, and every push it made, by how the push ended. Cloud Run counts its instances the same way. These metrics are sampled every 60 seconds and can take up to 120 seconds to appear (Google's list of metrics), so run this cell at least three minutes after the upload:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, at least three minutes after the upload (Cloud Monitoring reads; changes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/burst_metrics.txt]
    """
    import datetime as dt, json, os, subprocess, urllib.parse, urllib.request, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    P, SINCE = os.environ["PROJECT"], os.environ["BURST_SINCE"]
    TOKEN = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
    
    
    def api(url, body=None):
        """GET one Google API URL, or POST it a JSON body, with the operator's token; returns the parsed JSON.
        
        Example: api(f'https://monitoring.googleapis.com/v3/projects/{P}/timeSeries?{urllib.parse.urlencode(q)}')
        """
        req = urllib.request.Request(url, data=None if body is None else json.dumps(body).encode(),
                                     headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
        return json.load(urllib.request.urlopen(req, timeout=60))
    
    
    def when(stamp):
        """An RFC 3339 time from a Google API as a UTC datetime (nanoseconds cut to microseconds).
        
        Example: when(SINCE)
        """
        head, _, frac = stamp.rstrip("Z").partition(".")
        return dt.datetime.fromisoformat(f"{head}.{(frac + '000000')[:6]}+00:00")
    
    
    start = when(SINCE) - dt.timedelta(minutes=2)
    end = dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0)
    iso = lambda t: t.strftime("%Y-%m-%dT%H:%M:%SZ")
    SUB = 'resource.type="pubsub_subscription" AND resource.labels.subscription_id="{}"'
    RUN = 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-ingest" AND metric.labels.state="active"'
    
    
    def minutes(metric, where, aligner, group=None):
        """One metric over the window in one-minute steps, summed across series: {label: {"HH:MM": value}}.
        
        Example: minutes('pubsub.googleapis.com/subscription/push_request_count', SUB.format('documind-ingest-push'), 'ALIGN_DELTA', 'response_class')
        """
        q = {"filter": f'metric.type="{metric}" AND {where}', "interval.startTime": iso(start), "interval.endTime": iso(end),
             "aggregation.alignmentPeriod": "60s", "aggregation.perSeriesAligner": aligner,
             "aggregation.crossSeriesReducer": "REDUCE_SUM"}
        if group:
            q["aggregation.groupByFields"] = f"metric.label.{group}"
        out = {}
        for s in api(f"https://monitoring.googleapis.com/v3/projects/{P}/timeSeries?{urllib.parse.urlencode(q)}").get("timeSeries", []):
            label = (s.get("metric", {}).get("labels") or {}).get(group, "?") if group else "all"
            for pt in s.get("points", []):
                v = pt["value"]
                out.setdefault(label, {})[pt["interval"]["endTime"][11:16]] = float(v.get("int64Value", v.get("doubleValue", 0)))
        return out
    
    
    backlog = minutes("pubsub.googleapis.com/subscription/num_undelivered_messages", SUB.format("documind-ingest-push"), "ALIGN_MAX").get("all", {})
    oldest = minutes("pubsub.googleapis.com/subscription/oldest_unacked_message_age", SUB.format("documind-ingest-push"), "ALIGN_MAX").get("all", {})
    pushes = minutes("pubsub.googleapis.com/subscription/push_request_count", SUB.format("documind-ingest-push"), "ALIGN_DELTA", "response_class")
    dead = minutes("pubsub.googleapis.com/subscription/dead_letter_message_count", SUB.format("documind-ingest-push"), "ALIGN_DELTA").get("all", {})
    dlq = minutes("pubsub.googleapis.com/subscription/num_undelivered_messages", SUB.format("ingest-dlq-sub"), "ALIGN_MAX").get("all", {})
    active = minutes("run.googleapis.com/container/instance_count", RUN, "ALIGN_MAX").get("all", {})
    named = ("ack", "remote_server_4xx", "remote_server_5xx")
    print(f"{'UTC':5}  {'backlog':>7}  {'oldest':>7}  {'ack':>4}  {'4xx':>4}  {'5xx':>4}  {'other':>5}  {'instances':>9}")
    for m in sorted(set(backlog) | set(oldest) | set(active) | {k for v in pushes.values() for k in v}):
        other = sum(v.get(m, 0) for k, v in pushes.items() if k not in named)
        print(f"{m}  {backlog.get(m, 0):7.0f}  {oldest.get(m, 0):6.0f}s  " + "  ".join(f"{pushes.get(k, {}).get(m, 0):4.0f}" for k in named)
              + f"  {other:5.0f}  {active.get(m, 0):9.0f}")
    print(f"forwarded to the dead-letter topic in the window: {sum(dead.values()):.0f}")
    print(f"ingest-dlq-sub undelivered, the last sample: {dlq[max(dlq)]:.0f}" if dlq else "ingest-dlq-sub: no sample in the window")

# Original CLI workflow for step_06_put_the_ceiling_back.
COMMANDS_06 = """gcloud run services update documind-ingest --region "$REGION" --project "$PROJECT" --max-instances=30
gcloud run services describe documind-ingest --region "$REGION" --project "$PROJECT" \\
  --format='yaml(status.latestReadyRevisionName,spec.template.metadata.annotations)' | grep -E 'latestReadyRevisionName|maxScale'
make dlq PROJECT=$PROJECT

"""

def step_06_put_the_ceiling_back(session):
    """Run Put the ceiling back at this checkpoint.

    Put the ceiling back

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, before you leave this step (the ceiling back to the kit's; a minute).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/burst_restore.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_06)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_27', step_01_the_burst_thirty_one_objects_against_five),
        ('source_29', step_02_squeeze_then_upload),
        ('source_31', step_03_squeeze_then_upload),
        ('source_33', step_04_what_the_worker_saw),
        ('source_36', step_05_what_pub_sub_saw),
        ('source_38', step_06_put_the_ceiling_back),
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
