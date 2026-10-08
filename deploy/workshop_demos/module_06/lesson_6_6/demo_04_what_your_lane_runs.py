"""Lesson 6.6: What your lane runs

Do it

Run order inside this file:
1. Do it (source window 14)

Prerequisites: demo_03_what_a_turn_writes.
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


def step_01_what_your_lane_runs(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (what holds the conversations on your lane).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: instance      documind-checkpoint: POSTGRES_16, db-f1-micro, zonal, 10 GB
      backups       off
      network       public IP on, 0 authorized networks
      databases     postgres, documind
      users         chat, postgres
      the DSN       secret documind-checkpoint-dsn, 1 version(s), the latest enabled
      setup job     last run 2026-09-12T10:41, succeeded 1
      images        job chat:3f9c2a1d0b7e, service chat:8e41d7c2f5a9 - DIFFERENT
      ADK sessions  in memory: ADK DatabaseSessionService unavailable (The 'sqlalchemy' packa
    """
    import json, os, subprocess
    def gc(*args):
        """Run the requested gcloud inspection and return its decoded JSON for this section.
        
        Example: gc('sql', 'instances', 'describe', 'documind-checkpoint')
        """
        r = subprocess.run(["gcloud", *args, "--project", os.environ["PROJECT"], "--format", "json"], capture_output=True, text=True)
        return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None
    i = gc("sql", "instances", "describe", "documind-checkpoint")
    s, ip = i["settings"], i["settings"].get("ipConfiguration", {})
    print(f"  instance      {i['name']}: {i['databaseVersion']}, {s['tier']}, {s['availabilityType'].lower()}, {s['dataDiskSizeGb']} GB")
    print(f"  backups       {'on' if s.get('backupConfiguration', {}).get('enabled') else 'off'}")
    print(f"  network       public IP {'on' if ip.get('ipv4Enabled') else 'off'}, {len(ip.get('authorizedNetworks', []))} authorized networks")
    print(f"  databases     {', '.join(d['name'] for d in gc('sql', 'databases', 'list', '--instance', i['name']))}")
    print(f"  users         {', '.join(u['name'] for u in gc('sql', 'users', 'list', '--instance', i['name']))}")
    v = gc("secrets", "versions", "list", "documind-checkpoint-dsn") or []
    print(f"  the DSN       secret documind-checkpoint-dsn, {len(v)} version(s), the latest {v[0]['state'].lower() if v else 'missing'}")
    tag = lambda image: image.rsplit(":", 1)[-1][:12]
    job = gc("run", "jobs", "describe", "documind-checkpoint-setup", "--region", os.environ["REGION"])
    svc = gc("run", "services", "describe", "documind-chat", "--region", os.environ["REGION"])
    if job and svc:
        ran = (gc("run", "jobs", "executions", "list", "--job", "documind-checkpoint-setup", "--region", os.environ["REGION"], "--limit", "1") or [{}])[0]
        ji, si = job["spec"]["template"]["spec"]["template"]["spec"]["containers"][0]["image"], svc["spec"]["template"]["spec"]["containers"][0]["image"]
        print(f"  setup job     last run {ran.get('metadata', {}).get('creationTimestamp', 'never')[:16]}, succeeded {ran.get('status', {}).get('succeededCount', 0)}")
        print(f"  images        job chat:{tag(ji)}, service chat:{tag(si)} - {'the same' if ji == si else 'DIFFERENT'}")
    else:
        print(f"  setup job     not found beside documind-chat in {os.environ['REGION']}")
    adk = subprocess.run(["gcloud", "logging", "read", 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-chat" '
                          'AND textPayload:"DatabaseSessionService unavailable"', "--project", os.environ["PROJECT"], "--freshness", "30d",
                          "--limit", "1", "--format", "value(textPayload)"], capture_output=True, text=True).stdout.strip()
    print("  ADK sessions  " + ("in memory: " + adk[:62] if adk else "no fallback warning in 30 days of the log"))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_14', step_01_what_your_lane_runs),
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
