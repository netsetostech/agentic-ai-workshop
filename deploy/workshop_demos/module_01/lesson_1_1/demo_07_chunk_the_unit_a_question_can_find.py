"""Lesson 1.1 / HTML section 7: Chunk: the unit a question can find

Compare accepted and refused filters, then compare the exact ACME/Zeta versions
created in section 5. Queries can incur model work; the remaining operations read state.
Expected: disjoint tenant chunk IDs, equal hash multisets and refusal of tenant_id as a filter.
The doc_type=policy empty match is valid only for the stock unknown-stamped corpus.

Example: open this file at the matching HTML heading and choose Run/Debug
with rag-shell-venv. Complete the preceding required files in README.md.
Set breakpoints in the named functions below; demonstrate() shows their order.
After this lesson, run setup/finish.py even if a live observation failed.
"""
from collections import Counter
from workshop_helpers.lesson31 import LessonCloud, require, contract_step
from workshop_helpers.steps import run_steps
from workshop_helpers.session import DemoSession
REPEAT = False
# Inspect the failed attempt before explicitly retrying an unfinished function.
RETRY_FAILED_STEP = False
QUESTIONS = [
    ("markdown", "What is the notice period for a confirmed E3?", "hr_policy_2026.md"),
    ("pdf", "What does the Code on Wages say about the payment of wages?", "code_on_wages_2019.pdf"),
]


def compare_filters(cloud):
    """HTML 7: an allowed field can match nothing; tenant_id is never an allowed filter.
    
    Example: compare_filters(cloud) runs after the preceding function in demonstrate().
    Failures propagate; compare the saved/printed evidence with this section.
    """
    question = QUESTIONS[0][1]
    text = cloud.query("filter_text", question, filters={"kind": "text"})
    require(text.get("answerable") and text.get("citations"), "kind=text returned no cited answer.")
    require(all(c.get("kind", "text") == "text" for c in text["citations"]), "A non-text citation bypassed kind=text.")
    policy = cloud.query("filter_policy", question, filters={"doc_type": "policy"}, fresh=False)
    require(policy.get("cache_hit") == "none", "Filter example unexpectedly used the answer cache.")
    # The stock writer stamps doc_type=unknown. A customized corpus may legitimately
    # have policy rows, in which case the HTML's empty-match example needs new data.
    require(not policy.get("answerable") and not policy.get("citations"),
            "doc_type=policy matched your corpus; the stock lesson expects unknown. Inspect saved filter_policy.json.")
    refused = cloud.request("filter_tenant_refused", "/v1/query",
                            {"query": question, "tenant_id": "acme", "stream": False, "filters": {"tenant_id": "zeta"}},
                            expected_status=400)
    require(isinstance(refused["json"], dict) and "tenant_id" in str(refused["json"].get("detail", "")),
            "Expected a validation refusal naming the forbidden tenant_id filter.")


def compare_tenant_chunks(cloud):
    """HTML 7: use section 5's exact keys, then compare IDs and the multiset of text hashes.
    
    Example: compare_tenant_chunks(cloud) runs after the preceding function in demonstrate().
    Failures propagate; compare the saved/printed evidence with this section.
    """
    versions = cloud.session.state["lesson31_versions"]
    groups = [cloud.wait_indexed(v)["chunks"] for v in versions]
    acme, zeta = groups
    require(not (set(acme) & set(zeta)), "Identical tenant chunk IDs would overwrite each other's payloads.")
    for version, rows in zip(versions, groups):
        require(all(cid.startswith(version["tenant"] + ":" + version["sha256"] + "#") for cid in rows),
                "Chunk IDs do not carry this tenant and version SHA.")
        require(all(row.get("chunk_hash") for row in rows.values()), "A current chunk is missing its content hash.")
    require(Counter(r["chunk_hash"] for r in acme.values()) == Counter(r["chunk_hash"] for r in zeta.values()),
            "Same bytes did not produce the same chunk-hash multiset; inspect chunker/schema differences.")
    cid, row = next(iter(acme.items()))
    print("Chunk proof:", len(acme), len(zeta), "rows; no IDs shared; same hashes.")
    print("Example ID:", cid)
    for key in ("tenant_id", "doc_key", "current", "locator", "chunk_hash", "embedding_model", "embedding_task_type", "schema_version"):
        print(f"{key:22}", row.get(key))
    print("Vector dimensions:", len(row.get("embedding", [])))


def demonstrate(session):
    """Run this section in order and checkpoint each completed function.

    Example: main() supplies the active session; a failed read resumes after an explicit retry.
    """
    require(not session.state.get("lesson31_closed"), "Run was cleaned up; start a new lesson session.")
    run_steps(session, [
        ("source_32", contract_step(compare_filters)),
        ("source_34", contract_step(compare_tenant_chunks)),
    ], retry_failed=RETRY_FAILED_STEP)


def main():
    """Run this HTML section with the IDE interpreter.

    Example: choose Run or Debug on this file after the README prerequisites.
    """
    with DemoSession(__file__, live=True, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
