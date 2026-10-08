"""Read cloud evidence, then ask the kit's pure planning functions for decisions."""
from collections import Counter

ACTIONS = ("retire", "reingest", "backfill", "touch", "queued", "withdrawn", "ok")


def evaluate_widget(kit, rows):
    """Translate the 4.4 widget's facts into inputs for the actual Python planner.
    
    Args:
        kit: KitAdapter loading the installed reconcile.py implementation.
        rows: The HTML's name/bucket/ledger/bytes/queued teaching rows.
    Returns:
        The real planner's actions and drift summary, with applied=False.
    No cloud calls occur. Synthetic hashes distinguish same/known/new bytes;
    they are teaching labels rather than claimed SHA-256 values from GCS.
    
    Example: report = evaluate_widget(kit, rows) uses the HTML widget's five simulated documents
    """
    objects, ledger, claims, hashes = [], {}, {}, {}
    for index, row in enumerate(rows):
        name = row["name"]
        tenant = name.split("/", 1)[0]
        generation = "2" if row["bucket"] == "newer" else "1"
        old_hash = f"original-{index}"
        sha = old_hash if row["bytes"] == "same" else f"{row['bytes']}-{index}"
        hashes[name] = sha
        uri = "gs://example-uploads/" + name
        if row["bucket"] != "absent":
            objects.append({"name": name, "tenant_id": tenant, "generation": generation})
        if row["ledger"] != "none":
            ledger[name.replace("/", "~")] = {"name": name, "tenant_id": tenant, "gcs_uri": uri,
                "status": row["ledger"], "generation": "1", "sha256": old_hash, "doc_key": f"{tenant}_{old_hash}"}
        if row["bytes"] == "known":
            claims[f"{tenant}_{sha}"] = {"gcs_uri": uri, "status": "indexed"}
        if row["queued"]:
            claims[f"{tenant}_{sha}"] = {"gcs_uri": uri, "generation": generation, "status": "queued"}
    return evaluate(kit, objects, ledger, claims, lambda action: hashes[action["name"]])


def evaluate(kit, objects, ledger, documents, sha_for):
    """Resolve check_bytes with the supplied hash callback and return actual planner actions and drift.
    
    Example: evaluate(kit, objects, ledger, claims, lambda action: hashes[action['name']])
    """
    actions = kit.planner.plan(objects, ledger, documents)
    for action in actions:
        if action["action"] == "check_bytes":
            sha = sha_for(action)
            row = ledger.get(kit.planner.source_id_for(action["tenant_id"], action["name"]))
            action["action"] = kit.planner.decide_bytes(sha, action["tenant_id"], row, documents)
            action["sha256"] = sha
    counts = Counter(action["action"] for action in actions)
    summary = {name: counts[name] for name in ACTIONS}
    summary.update(event="reconcile_done", applied=False, drift=kit.planner.drift_of(summary))
    return {"actions": actions, "summary": summary}


def print_plan(report):
    """Print each decision and explain which actions contribute to drift.
    
    Example: print_plan(report) prints each decision and the resulting drift count
    """
    for row in report["actions"]:
        print(f"  {row['action']:10} {row['name']:55} {row.get('why', '')}")
    print("Summary:", report["summary"])
    print("Drift = retire + reingest + backfill. Queued and touch do not add drift.")
