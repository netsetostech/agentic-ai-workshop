"""Lesson 1.1 / HTML section 5: Version: the bytes decide, and the same file in two tenants proves it

Upload evals/demo/gratuity_amendment_2026.md through the ACME UI first.
This file verifies those exact bytes, uploads them to Zeta, waits for both saved
generations and inspects their claims. Existing identical fixtures are reused;
different bytes are not overwritten. The uploads remain after cleanup.
ACME_UPLOAD="operator" is a labelled alternative, not proof of the UI path.
Expected: equal content hashes, distinct tenant keys, indexed claims and current rows.

Example: open this file at the matching HTML heading and choose Run/Debug
with rag-shell-venv. Complete the preceding required files in README.md.
Set breakpoints in the named functions below; demonstrate() shows their order.
After this lesson, run setup/finish.py even if a live observation failed.
"""
from workshop_helpers.lesson31 import LessonCloud, require, contract_step
from workshop_helpers.steps import run_steps
from workshop_helpers.session import DemoSession
REPEAT = False
# Inspect the failed attempt before explicitly retrying an unfinished function.
RETRY_FAILED_STEP = False
ACME_UPLOAD = "ui"
FILENAME = "gratuity_amendment_2026.md"


def upload_same_bytes(cloud):
    """Check ACME first so a missing UI step cannot leave an unexplained Zeta-only run.
    
    Example: upload_same_bytes(cloud) runs after the preceding function in demonstrate().
    Failures propagate; compare the saved/printed evidence with this section.
    """
    require(ACME_UPLOAD in {"ui", "operator"}, "ACME_UPLOAD must be 'ui' or 'operator'.")
    path = cloud.session.config.kit_root / "evals/demo" / FILENAME
    data = path.read_bytes()  # Binary read preserves the SHA, including line endings.
    print("Fixture:", path, "| ACME upload mode:", ACME_UPLOAD)
    versions = [cloud.fixture("acme", FILENAME, data, upload=ACME_UPLOAD == "operator"),
                cloud.fixture("zeta", FILENAME, data, upload=True)]
    cloud.session.state["lesson31_versions"] = versions
    cloud.session.save()  # Later files use exactly these version keys, not today's latest document.
    cloud.save("expected_versions", versions)
    print("SHA-256:", versions[0]["sha256"])
    return versions


def inspect_indexed_versions(cloud, versions):
    """Upload completion is not indexing; wait for matching ledger, claim and chunks.
    
    Example: inspect_indexed_versions(cloud, versions) runs after the preceding function in demonstrate().
    Failures propagate; compare the saved/printed evidence with this section.
    """
    for version in versions:
        observed = cloud.wait_indexed(version)
        claim = observed["claim"]
        print(version["tenant"], version["doc_key"], claim["status"], claim["chunks"], claim["gcs_uri"])
        cloud.worker_logs(version)
    require(versions[0]["sha256"] == versions[1]["sha256"]
            and versions[0]["doc_key"] != versions[1]["doc_key"], "Expected equal bytes with distinct tenant keys.")
    print("Version proof: same content hash; separate claims for acme and zeta.")


def demonstrate(session):
    """Run this section in order and checkpoint each completed function.

    Example: main() supplies the active session; a failed read resumes after an explicit retry.
    """
    require(not session.state.get("lesson31_closed"), "Run was cleaned up; start a new lesson session.")
    run_steps(session, [
        ("source_21", contract_step(upload_same_bytes)),
        ("source_23", contract_step(inspect_indexed_versions, saved_versions=True)),
    ], retry_failed=RETRY_FAILED_STEP)


def main():
    """Run this HTML section with the IDE interpreter.

    Example: choose Run or Debug on this file after the README prerequisites.
    """
    with DemoSession(__file__, live=True, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
