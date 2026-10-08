"""Lesson 1.1 / HTML section 3: Tenant: something you are, never something you send

Write the kit roster, compare member/outsider/anonymous calls, then read membership.
The roster changes membership/policy; the member query can incur model work.
Expected: admitted member; API JSON refusal for an outsider; Cloud Run refusal without a token.

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


def establish_roster(cloud):
    """HTML 3: use the kit's actual roster command, including its documented policies.
    
    Example: establish_roster(cloud) runs after the preceding function in demonstrate().
    Failures propagate; compare the saved/printed evidence with this section.
    """
    session = cloud.session
    session.command([sys.executable, "commands/lane.py", "--project", session.config.project,
                     "roster", "--tenant", TENANT, "--members", os.environ["ME"]])


def compare_access(cloud):
    """HTML 3: identical bodies, three identities; the refusal body identifies the gate.
    
    Example: compare_access(cloud) runs after the preceding function in demonstrate().
    Failures propagate; compare the saved/printed evidence with this section.
    """
    body = {"query": QUESTION, "tenant_id": TENANT, "stream": False}
    member = cloud.request("member", "/v1/query", body)["json"]
    require(isinstance(member, dict) and member.get("answerable") and member.get("citations"),
            "The member was admitted but no cited answer was produced. Check the seeded HR fixture.")
    outsider = cloud.request("outsider", "/v1/query", body, identity="outsider", expected_status=403)
    require(outsider["json"] == {"detail": "not a member of this tenant"},
            "The outsider did not reach the expected roster refusal. Check its Cloud Run invoker role and roster.")
    anonymous = cloud.request("anonymous", "/v1/query", body, identity="none", expected_status=403)
    require("html" in anonymous["content_type"].lower() and anonymous["json"] is None,
            "The unauthenticated refusal was not the expected Cloud Run HTML response; inspect service admission.")


def inspect_membership(cloud):
    """HTML 3: read the forward roster, UI reverse lookup and tenant settings.
    
    Example: inspect_membership(cloud) runs after the preceding function in demonstrate().
    Failures propagate; compare the saved/printed evidence with this section.
    """
    from google.cloud.firestore_v1.base_query import FieldFilter
    members = cloud.rows("tenants/acme/members")
    email = os.environ["ME"].lower()
    require(email in members, "The operator is missing from ACME's roster after the roster command.")
    matches = cloud.db.collection_group("members").where(filter=FieldFilter("email", "==", email)).limit(1).get(retry=None, timeout=15)
    tenants = [row.reference.parent.parent.id for row in matches]
    require(tenants, "No membership reverse lookup result for this operator.")
    settings = cloud.document("tenant_settings/acme")
    require(settings.get("retrieval_backend") == "vector", "ACME's vector pin changed; rerun preparation deliberately.")
    cloud.save("membership", {"members": members, "reverse_lookup": tenants, "settings": settings})
    print("Roster:", list(members), "| first reverse lookup:", tenants, "| settings:", settings)
    if tenants != [TENANT]:
        print("This operator belongs to another tenant too; the UI's limit(1) may select it. Select an ACME member for the UI upload.")


def demonstrate(session):
    """Run this section in order and checkpoint each completed function.

    Example: main() supplies the active session; a failed read resumes after an explicit retry.
    """
    require(not session.state.get("lesson31_closed"), "Run was cleaned up; start a new lesson session.")
    run_steps(session, [
        ("source_9", contract_step(establish_roster)),
        ("source_10", contract_step(compare_access)),
        ("source_12", contract_step(inspect_membership)),
    ], retry_failed=RETRY_FAILED_STEP)


def main():
    """Run this HTML section with the IDE interpreter.

    Example: choose Run or Debug on this file after the README prerequisites.
    """
    with DemoSession(__file__, live=True, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
