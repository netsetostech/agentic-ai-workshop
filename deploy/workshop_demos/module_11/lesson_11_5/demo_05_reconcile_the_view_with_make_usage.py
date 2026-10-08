"""Lesson 11.5: Reconcile the view with make usage

Do it

Run order inside this file:
1. Do it (source window 13)

Prerequisites: demo_04_four_questions_four_rows.
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


def step_01_reconcile_the_view_with_make_usage(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads only: Cloud Logging and one small BigQuery query).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: today since 00:00 IST: 4 usage rows in Cloud Logging, 2 tenant_daily rows
      group (the view GROUP BY)                    answers refused   tokens in          Rs
      acme query vertex v3 dense vector text           3/3     1/1   2153/2153   0.36/0.36  equal
      zeta query vertex v3 dense firestore text        1/1     0/0     843/843   0.14/0.14  equal
      (each pair is tenant_daily/make usage's grouping; p95 is left out: the view's APPROX_QUANTILES is not the tool's nearest rank)
    acme: tenant_daily Rs 0.36, make usage's grouping Rs 0.36 - equal
    zeta: tenant_daily Rs 0.14, make usage's grouping Rs 0.14 - equal
    media rows today: 0
    RECONCILED: every group equal in answers, refusals, tokens and rupees
    """
    import datetime as dt, json, os, subprocess, sys
    sys.path.insert(0, "evals")
    from usage_rows import USD_INR, group                       # make usage's own GROUP BY, and its rate
    P = os.environ["PROJECT"]
    KEYS = ("tenant", "surface", "model_backend", "prompt_version", "retrieval_mode", "retrieval_backend", "modality")   # the view's, less the day
    IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
    midnight = dt.datetime.now(IST).replace(hour=0, minute=0, second=0, microsecond=0)
    since = midnight.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    flt = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND '
           f'(jsonPayload.event="query" OR jsonPayload.event="stream" OR jsonPayload.event="media") AND timestamp>="{since}"')
    log = subprocess.run(["gcloud", "logging", "read", flt, "--project", P, "--limit", "5000", "--format=json"],
                         capture_output=True, text=True, check=True).stdout
    rows = [e["jsonPayload"] for e in json.loads(log or "[]")]
    tool = {tuple(str(g[k]) for k in KEYS): g for g in group(rows, KEYS)}
    sql = "SELECT * EXCEPT(day) FROM `documind_observability.tenant_daily` WHERE day = CURRENT_DATE('Asia/Kolkata')"
    out = subprocess.run(["bq", "--project_id", P, "query", "--use_legacy_sql=false", "--format=json", "--max_rows=1000", sql],
                         capture_output=True, text=True, check=True).stdout
    view = {tuple(str(r[k]) for k in KEYS): r for r in json.loads(out or "[]")}
    print(f"today since 00:00 IST: {len(rows)} usage rows in Cloud Logging, {len(view)} tenant_daily rows")
    print(f"  {'group (the view GROUP BY)':42} {'answers':>9} {'refused':>7} {'tokens in':>11} {'Rs':>11}")
    agree, totals = True, {}
    for k in sorted(set(tool) | set(view)):
        t, v = tool.get(k), view.get(k)
        tv = (t["answers"], round(t["unanswerable_rate"] * t["answers"]), t["tokens_in"], t["tokens_out"], t["inr"]) if t else None
        vv = (int(v["queries"]), int(v["unanswerable"]), int(v["tokens_in"]), int(v["tokens_out"]), float(v["cost_inr"])) if v else None
        same = tv is not None and vv is not None and tv[:4] == vv[:4] and abs(tv[4] - vv[4]) < 0.005
        agree &= same
        for side, x in (("view", vv), ("tool", tv)):
            totals.setdefault(k[0], {"view": 0.0, "tool": 0.0})[side] += x[4] if x else 0.0
        cell = lambda a, b: f"{a}/{b}"
        print(f"  {' '.join(k)[:42]:42} {cell(vv and vv[0], tv and tv[0]):>9} {cell(vv and vv[1], tv and tv[1]):>7} "
              f"{cell(vv and vv[2], tv and tv[2]):>11} {cell(vv and vv[4], tv and tv[4]):>11}  {'equal' if same else 'DIFFERENT'}")
    print("  (each pair is tenant_daily/make usage's grouping; p95 is left out: the view's APPROX_QUANTILES is not the tool's nearest rank)")
    for tenant, s in sorted(totals.items()):
        print(f"{tenant}: tenant_daily Rs {s['view']:.2f}, make usage's grouping Rs {s['tool']:.2f} - " + ("equal" if abs(s['view'] - s['tool']) < 0.005 else "DIFFERENT"))
    media = [r for r in rows if r.get("event") == "media"]
    print(f"media rows today: {len(media)}" + (f" (Rs {sum(r['cost_usd'] for r in media) * USD_INR:.2f}) - make usage counts them, the sink never copies them" if media else ""))
    print("RECONCILED: every group equal in answers, refusals, tokens and rupees" if agree else "NOT RECONCILED: read the DIFFERENT rows")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_13', step_01_reconcile_the_view_with_make_usage),
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
