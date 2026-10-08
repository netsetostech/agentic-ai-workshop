"""Reviewed additions where an interactive example or a missing HTML needs a demo.

The nine course-plan lessons are explicitly attributed to the manifest/plan and
real kit entry points. They are not represented as conversions of nonexistent
HTML. The two 1.8 offline examples reproduce its displayed scenarios.
"""
import json
from pathlib import Path
import re
import textwrap


def extra_windows(lesson, page):
    """Expose 1.8's queued illustration and widget using the actual planner."""
    if lesson != "1.8":
        return []
    rows = json.loads(re.search(r"var ROWS = (\[.*?\]);", page)[1])
    queued = '''from workshop_helpers.kit import KitAdapter
from workshop_helpers.reconciliation import evaluate, print_plan
kit = KitAdapter(session.config.kit_root)
objects = [dict(name="acme/cgst_act_2017.pdf", generation="1", tenant_id="acme"),
           dict(name="acme/cgst_it_bundle.pdf", generation="4", tenant_id="acme")]
claims = {"acme_bundle": {"status": "queued", "generation": "4",
                          "gcs_uri": "gs://example-uploads/acme/cgst_it_bundle.pdf"}}
report = evaluate(kit, objects, {}, claims, lambda action: "new-act-bytes")
print_plan(report)
assert report["summary"]["reingest"] == report["summary"]["queued"] == 1
assert report["summary"]["drift"] == 1
print("The queued claim names this object AND generation. It does not prove the batch job finished.")
'''
    widget = f'''from copy import deepcopy
from workshop_helpers.kit import KitAdapter
from workshop_helpers.reconciliation import evaluate_widget, print_plan
# These are the exact default rows from the HTML widget; edit a copy for variations.
rows = {rows!r}
kit = KitAdapter(session.config.kit_root)
report = evaluate_widget(kit, rows)
print_plan(report)
assert report["summary"]["drift"] == 2
assert all(report["summary"][name] == 1 for name in ("ok", "retire", "touch", "reingest", "withdrawn"))
known = deepcopy(rows)
known[3]["bytes"] = "known"
print("\\nVariation: the circular's bytes already have an indexed claim.")
print_plan(evaluate_widget(kit, known))
queued = deepcopy(rows)
queued[3]["queued"] = True
print("\\nVariation: a queued claim owns the circular's generation.")
print_plan(evaluate_widget(kit, queued))
'''
    return [{"window": name, "label": "Python — simulated facts, actual kit planner; no network", "code": "python - <<'PY'\n" + code + "PY",
             "copy": True, "heading": "How reconciliation decides", "subheading": title, "anchor": "s2",
             "purpose": purpose, "expected": expected, "line": line} for name, code, title, purpose, expected, line in (
                 ("queued-example", queued, "How do we know a PDF is queued?", "Explain the page's two-PDF illustration. Reconciliation leaves the matching queued generation to the batch lane; only the new Act contributes to drift.", "reingest 1, queued 1, drift 1; applied false", 335),
                 ("widget", widget, "Explore a different bucket and ledger", "Reproduce the five default widget documents before exploring its known-bytes and queued variations. The real plan(), decide_bytes() and drift_of() functions make the decisions.", "ok 1, retire 1, touch 1, reingest 1, withdrawn 1; drift 2", 431))]


def adapt_window(lesson, window, code, body):
    """Record targeted differences needed for reliable IDE execution of source steps."""
    changes = []
    if lesson == "1.8" and window["window"] == 10:
        body = 'session.state["backend_restore_required"] = True\nsession.save()\nsession.shell(' + repr(code) + ')'
        changes.append("Persist that backend cleanup is required even if baseline preparation fails.")
    if lesson == "1.8" and window["window"] == 44:
        start = code.index("ch44_restore_backend()")
        body = ('try:\n    session.shell("ch44_source && ch44_plan clean")\nfinally:\n'
                '    session.shell(' + repr(code[start:]) + ')\n'
                '    session.state["backend_restore_required"] = False\n    session.save()')
        changes.append("Restore the saved backend in finally even when the final observation fails; the failed observation remains a failure.")
    if lesson == "1.8" and window["window"] == 42:
        body = ('session.shell("make retire PROJECT=$PROJECT SOURCE=acme/smoke_note_v1.md")\n'
                'try:\n    session.shell("make smoke-reindex PROJECT=$PROJECT")\n'
                'finally:\n    session.shell("make restore PROJECT=$PROJECT SOURCE=acme/smoke_note_v1.md")')
        changes.append("Restore the temporarily withdrawn smoke note even when the separate smoke fails.")
    from workshop_demo_runtime_adaptations import adapt
    code, body, extra = adapt(lesson, window, code, body)
    return code, body, changes + extra


def recipe(title, purpose, code, *, live=False, category="required", expected=""):
    """Describe an explicitly authored checkpoint with its actual kit operation."""
    return {"title": title, "purpose": purpose, "code": textwrap.dedent(code).strip(),
            "live": live, "category": category, "expected": expected}


def build_access_recipe():
    """The conditional repair for a first Cloud Build on an organization project (lesson 5.3's box, 24 September 2026)."""
    return recipe("Grant the build account what a build needs",
        "Only if the build stopped at storage.objects.get: 'could not resolve source' and a 403 naming the Compute Engine "
        "default account. The kit names no account for Cloud Build, so a build runs as the project's default build account, "
        "and in an organization created on or after 3 May 2024 that account is created without the Editor role. Run once, as "
        "a project owner: read access to its source in the PROJECT_cloudbuild bucket only, push access to the documind "
        "repository, and log writing. Not Editor or roles/cloudbuild.builds.builder: granted on the project, either one can "
        "read, write and delete every object in every bucket, the uploads bucket included. IAM applies a grant in about two "
        "minutes, sometimes seven or more; then run the build again.", '''
            import os
            p, r = session.config.project, session.config.cloud_run_region
            member = "serviceAccount:" + os.environ["NUMBER"] + "-compute@developer.gserviceaccount.com"   # the account the 403 names; use yours if it names another
            session.command(["gcloud", "storage", "buckets", "add-iam-policy-binding", "gs://" + p + "_cloudbuild",
                             "--member=" + member, "--role=roles/storage.objectViewer", "--format=none"])
            session.command(["gcloud", "artifacts", "repositories", "add-iam-policy-binding", "documind", "--location=" + r,
                             "--project=" + p, "--member=" + member, "--role=roles/artifactregistry.writer", "--format=none"])
            session.command(["gcloud", "projects", "add-iam-policy-binding", p, "--member=" + member,
                             "--role=roles/logging.logWriter", "--condition=None", "--format=none"])
            print("Granted. IAM applies a grant in about two minutes, sometimes seven or more; then run the build again.")
        ''', live=True, category="recovery", expected="Three bindings added for the account the 403 named; the next build reads its source.")


def course_plan_recipes():
    """Return concrete experiments for the lessons whose main page is not written yet.

    11.1-11.3 and 11.8 are the earlier plan's 14.1-14.4 (the Cohort 2 renumbering). Module 0's recipes retired when
    lessons 0.2 to 0.4 got their pages.
    """
    return {
      "11.1": [
        recipe("Inspect the keyless build identity", "Read the kit's workload-identity and build definitions. Verify repository/ref conditions in the real deployment configuration before submitting a build; no service-account key is generated.", '''
            from pathlib import Path
            for path in (Path("terraform/ci.tf"), Path("cloudbuild.yaml")):
                if path.exists():
                    print("\\n", path, "\\n", path.read_text(encoding="utf-8"))
            for path in Path("terraform").glob("*.tf"):
                text = path.read_text(encoding="utf-8")
                if "workload_identity" in text:
                    print(path, "\\n", text)
        '''),
        recipe("Build the deployment images", "Use the actual kit build target and the current authenticated identity. Record the build output and image tags; a successful local credential check alone does not prove a deployed GitHub workload-identity run.", '''
            import sys
            session.command(["make", "build", "PROJECT=" + session.config.project, "REGION=" + session.config.cloud_run_region, "PY=" + sys.executable])
        ''', live=True),
        build_access_recipe(),
      ],
      "11.2": [
        recipe("Create the recorded candidate", "Create a no-traffic API revision with the kit's candidate target. The recorded revision name, not whatever is newest later, is the release identity.", '''
            import sys
            session.command(["make", "candidate", "PROJECT=" + session.config.project, "REGION=" + session.config.cloud_run_region, "PY=" + sys.executable])
            from pathlib import Path
            print("Recorded candidate:", Path(".candidate-revision").read_text().strip())
        ''', live=True),
        recipe("Evaluate the exact candidate", "Resolve the candidate tag and require it to name the recorded revision before the live gate. Save a project/region/revision-bound gate record only after the evaluator exits successfully.", '''
            import json, os, sys
            from pathlib import Path
            from workshop_helpers.auth import gcloud
            from workshop_helpers.artifacts import write_json
            expected = Path(".candidate-revision").read_text().strip()
            service = json.loads(gcloud("run", "services", "describe", "documind-api", "--project=" + session.config.project, "--region=" + session.config.cloud_run_region, "--format=json"))
            tagged = next(row for row in service["status"]["traffic"] if row.get("tag") == "candidate")
            assert tagged["revisionName"] == expected, "The candidate tag moved; evaluate the intended revision."
            report = session.attempt / "candidate_gate.json"
            session.command(["make", "eval-live", "PROJECT=" + session.config.project, "REGION=" + session.config.cloud_run_region, "API=" + tagged["url"], "REPORT=" + str(report), "PY=" + sys.executable])
            gate = {"project": session.config.project, "region": session.config.cloud_run_region, "revision": expected, "report": str(report), "passed": True}
            write_json(session.config.results_dir / "release_gate.json", gate)
            print("Gate passed for:", expected)
        ''', live=True, expected="A successful live gate tied to the same recorded candidate revision."),
      ],
      "11.3": [
        recipe("Promote the gated revision", "Require the saved gate from 11.2 to match this project, region and candidate, then use the kit's by-name promotion. The kit records the previous serving revision for rollback.", '''
            import json, sys
            from pathlib import Path
            gate = json.loads((session.config.results_dir / "release_gate.json").read_text())
            candidate = Path(".candidate-revision").read_text().strip()
            assert gate["passed"] and gate["project"] == session.config.project and gate["region"] == session.config.cloud_run_region
            assert gate["revision"] == candidate, "A different candidate was gated; do not promote this one."
            session.command(["make", "promote", "PROJECT=" + session.config.project, "REGION=" + session.config.cloud_run_region, "PY=" + sys.executable])
        ''', live=True),
        recipe("Roll back and verify recovery", "Return traffic to the exact previous revision recorded by the kit. Measure actual elapsed time, then run smoke; a quick traffic command alone is not proof of a healthy recovered service.", '''
            import sys, time
            started = time.perf_counter()
            session.command(["make", "rollback", "PROJECT=" + session.config.project, "REGION=" + session.config.cloud_run_region, "PY=" + sys.executable])
            print("Rollback command seconds:", round(time.perf_counter() - started, 2))
            session.command(["make", "smoke", "PROJECT=" + session.config.project, "REGION=" + session.config.cloud_run_region, "PY=" + sys.executable])
        ''', live=True),
      ],
      "11.8": [
        recipe("Run the operational gate", "Run the real smoke-all gate and preserve its output, including unavailable optional services and failures. Do not mark the capstone complete merely because earlier individual demos ran.", '''
            import sys
            session.command(["make", "smoke-all", "PROJECT=" + session.config.project, "REGION=" + session.config.cloud_run_region, "PY=" + sys.executable])
        ''', live=True),
        recipe("Write an evidence handover", "Summarize actual lesson attempts and retain the exact candidate gate, failures and evidence locations. This is an evidence index for a human capstone review, not an automatic rubric score.", '''
            import json
            from workshop_helpers.artifacts import write_json
            records = []
            for path in sorted(session.config.results_dir.glob("module_*/lesson_*/*/session.json")):
                state = json.loads(path.read_text(encoding="utf-8"))
                records.append({"lesson": state["lesson"], "project": state["identity"]["project"], "evidence": str(path),
                                "completed": state["completed"], "failed_attempts": [a for a in state["attempts"] if a["status"] == "failed"],
                                "backend_restore_required": state.get("backend_restore_required", False)})
            write_json(session.attempt / "handover.json", records)
            print("Evidence index:", session.attempt / "handover.json")
            print("Review the capstone rubric against the actual artifacts; no score was invented.")
        '''),
      ],
    }


def generate_course_plan_lessons(builder):
    """Generate the folders of the lessons whose main HTML is not written yet, with honest source attribution."""
    mappings = []
    for lesson, recipes in course_plan_recipes().items():
        number = f"{int(lesson.split('.')[0]):02}"
        module = builder.MANIFEST["modules"][number]
        spec = module["lessons"][lesson]
        folder = builder.WORKSHOP / f"module_{number}" / f"lesson_{lesson.replace('.', '_')}"
        records = []
        previous = []
        for n, item in enumerate(recipes, 1):
            prefix = "finish" if item["category"] == "cleanup" else "recover" if item["category"] == "recovery" else "demo"
            filename = f"{prefix}_{n:02}_{builder.slug(item['title'])}.py"
            record = {"lesson": lesson, "file": filename, "id": filename[:-3], "anchor": f"plan-{n}",
                      "heading": item["title"], "subheading": item["title"], "purpose": item["purpose"],
                      "label": "Course-plan experiment — " + ("live deployment" if item["live"] else "local Python/kit inspection"),
                      "category": item["category"], "requires": previous[-1:] if item["category"] == "required" else [],
                      "expected": item["expected"], "source": builder.published(folder, "README.md"),   # the course plan is not published; this README says so
                      "line": 1, "offline": not item["live"], "live_verified": False, "next": "Read the next checkpoint in README.md"}
            if item["category"] == "required":
                previous.append(record["id"])
            builder.make_demo(folder, record, item["code"], item["code"], live=item["live"])
            records.append(record)
        mapping = {"schema_version": 1, "lesson": lesson, "title": spec["name"], "source_kind": "course_plan_and_kit",
                   "source_sha": builder.hashlib.sha256(json.dumps(recipes, sort_keys=True).encode()).hexdigest(),
                   "persist_variables": ["API", "API_URL", "PROJECT", "REGION", "TENANT", "ME", "NUMBER"],
                   "demos": records, "live_verification": "Not performed; main HTML has not yet been authored."}
        builder.emit(folder / "lesson_map.json", json.dumps(mapping, indent=2))
        lines = [f"# Lesson {lesson}: {spec['name']}", "", f"**Summary:** {spec['proof']}.", "",
                 "**Source:** this lesson has no main HTML yet. These examples are authored from the existing course plan and actual kit entry points, not presented as an HTML conversion. Read the module prerequisites and each file's top summary before Run.", "",
                 "Use the existing rag-shell-venv interpreter and workshop setup. Each file is independent to Run/Debug; session state persists. Optional long-running services run in a separate console. Cloud-changing steps are separate from inspection/planning steps.", "", "## Run order", ""]
        for item, record in zip(recipes, records):
            lines += [f"### {record['file']}", "", f"[{item['title']}]({record['file']}) — {item['category']}", "", item["purpose"], "",
                      "Expected observation: " + (item["expected"] or "Inspect the actual command/read output; a nonzero exit stops the attempt."), ""]
        lines += ["## Limits and evidence", "", "These additions have offline source/runtime checks but have not been run against your GCP project. They do not replace the missing lesson prose, browser/UI observations, or a human review of the capstone rubric. Evidence is saved under workshop_demos/results; credentials are not copied into handover data.", ""]
        builder.emit(folder / "README.md", "\n".join(lines))
        mappings.append(mapping)
    return mappings
