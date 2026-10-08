"""Lesson 1.1 / HTML section 4: Source: the object path is the document's identity

Read one HR source through Storage, the sources API and the Firestore ledger.
This section reads cloud state; it does not upload a new file.
Expected: tenant-scoped rows with matching indexed generation, document key and URI.

Example: open this file at the matching HTML heading and choose Run/Debug
with rag-shell-venv. Complete the preceding required files in README.md.
Set breakpoints in the named functions below; demonstrate() shows their order.
After this lesson, run setup/finish.py even if a live observation failed.
"""
import os
import sys
from workshop_helpers.lesson31 import LessonCloud, require, contract_step
from workshop_helpers.steps import run_steps
from workshop_helpers.session import DemoSession
REPEAT = False
# Inspect the failed attempt before explicitly retrying an unfinished function.
RETRY_FAILED_STEP = False
TENANT = "acme"
SOURCE = "hr_policy_2026.md"
QUESTION = "What is the notice period?"


def trace_source(cloud):
    """HTML 4: consume complete responses before printing selected rows; no head/pipefail.
    
    Example: trace_source(cloud) runs after the preceding function in demonstrate().
    Failures propagate; compare the saved/printed evidence with this section.
    """
    from services.ingest.idempotency import source_id_for
    objects = [{"name": b.name, "generation": str(b.generation), "size": b.size}
               for b in cloud.bucket.list_blobs(prefix=TENANT + "/", retry=None, timeout=15)]
    cloud.save("bucket_objects", objects)
    print("Tenant objects:", len(objects), "| first five:", objects[:5])
    blob = cloud.bucket.blob(f"{TENANT}/{SOURCE}")
    blob.reload(retry=None, timeout=15)
    api = cloud.request("sources_api", "/v1/sources?tenant_id=acme")["json"]
    require(isinstance(api, dict) and api.get("tenant_id") == TENANT, "Unexpected sources response.")
    require(all(row["name"].startswith(TENANT + "/") for row in api["sources"]), "Cross-tenant source appeared in the API.")
    source = next((r for r in api["sources"] if r["name"] == blob.name), None)
    ledger = cloud.rows("sources", tenant_id=TENANT)
    cloud.save("source_ledger", ledger)
    row = ledger.get(source_id_for(TENANT, blob.name), {})
    require(source and row, "HR source missing from the API or ledger; seed/index the lesson corpus first.")
    require(row.get("status") == source["status"] == "indexed"
            and str(blob.generation) == str(source["generation"]) == str(row.get("generation"))
            and row.get("doc_key") == source["doc_key"]
            and row.get("gcs_uri") == f"gs://{cloud.bucket.name}/{blob.name}",
            "Storage/API/ledger disagree. Wait for ingestion or inspect reconciliation in lesson 1.8.")
    print("Same source:", blob.name, "| generation:", blob.generation, "| version:", row["doc_key"])
    print("Source ledger:", row)


def demonstrate(session):
    """Run this section in order and checkpoint each completed function.

    Example: main() supplies the active session; a failed read resumes after an explicit retry.
    """
    require(not session.state.get("lesson31_closed"), "Run was cleaned up; start a new lesson session.")
    run_steps(session, [
        ("source_16", contract_step(trace_source)),
    ], retry_failed=RETRY_FAILED_STEP)


def main():
    """Run this HTML section with the IDE interpreter.

    Example: choose Run or Debug on this file after the README prerequisites.
    """
    with DemoSession(__file__, live=True, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
