"""Reusable I/O for lesson 1.1; the examples remain in numbered HTML-section files.

Clients are created only inside an active DemoSession. HTTP evidence includes
status and body, never bearer tokens. Exact-version polling replaces arbitrary
sleeps and unrelated 'latest ingest' logs. Cloud writes are limited to the
explicit preparation, roster command and fixture-upload checkpoints.
"""
from __future__ import annotations

import json
from functools import wraps
import os
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .artifacts import write_json
from .auth import gcloud
from .discovery import read_serving


def contract_step(function, *, saved_versions=False, local=False):
    """Bind an authored contract example to the common resumable-step interface.

    The function stays in its lesson file. Clients are created at execution time;
    the version check reads the exact identities saved by the preceding upload.
    Example: run_steps(session, [("source_23", contract_step(inspect_indexed_versions,
    saved_versions=True))]) resumes inspection without repeating the upload.
    """
    @wraps(function)
    def run(session):
        """Supply this checkpoint's clients/state when run_steps invokes it.

        Example: run(session) calls the wrapped lesson function after prerequisites.
        """
        if local:
            return function()
        cloud = LessonCloud(session)
        if saved_versions:
            return function(cloud, session.state['lesson31_versions'])
        return function(cloud)
    return run


def require(condition, message):
    """Keep evidence checks active even if Python is launched with optimization.
    
    Example: require(answer.get('cache_hit') == 'none', 'Cached answer: rerun setup/prepare.py after cleanup; no fresh retrieval was demonstrated.')
    """
    if not condition:
        raise RuntimeError(message)


def require_fresh_vector(answer):
    """A backend pin alone cannot prove a fresh index read; inspect its stages.
    
    Example: require_fresh_vector(result)
    """
    stages = answer.get("stages") or {}
    require(answer.get("cache_hit") == "none", "Cached answer: rerun setup/prepare.py after cleanup; no fresh retrieval was demonstrated.")
    require(stages.get("retrieval_backend") == "vector" and stages.get("pool", 0) > 0
            and stages.get("vector_chunks", 0) > 0,
            "No fresh Vector Search contribution. Inspect saved stages, index deployment and API logs; a Firestore fallback is not this proof.")


def version_ready(expected, source, claim, chunks):
    """Require this object's generation, content key and complete current rows.
    
    A document claim identifies CONTENT. Its generation can be an earlier upload
    of those same bytes; the source ledger identifies the current generation.
    Empty/missing claims and unrelated indexed documents must never pass.
    
    Example: version_ready(expected, r['source'], r['claim'], r['chunks'])
    """
    return bool(source and claim and chunks
                and source.get("tenant_id") == expected["tenant"]
                and source.get("name") == expected["name"]
                and source.get("gcs_uri") == expected["uri"]
                and source.get("doc_key") == expected["doc_key"]
                and source.get("sha256") == expected["sha256"]
                and str(source.get("generation")) == expected["generation"]
                and source.get("status") == claim.get("status") == "indexed"
                and claim.get("tenant_id") == expected["tenant"]
                and claim.get("gcs_uri") == expected["uri"]
                and source.get("chunks") == claim.get("chunks") == len(chunks)
                and all(row.get("current") is True
                        and row.get("doc_key") == expected["doc_key"]
                        and row.get("tenant_id") == expected["tenant"]
                        and row.get("source_uri") == expected["uri"] for row in chunks.values()))


def poll_until(read, ready, seconds, interval, *, clock=time.monotonic, sleep=time.sleep):
    """Poll bounded SDK reads; timeout reports the last observed state, not success.
    
    Example: poll_until(read, lambda r: version_ready(expected, r['source'], r['claim'], r['chunks']), self.session.config.ingest_wait_seconds, self.session.config.poll_seconds)
    """
    deadline = clock() + seconds
    while True:
        value = read()
        if ready(value):
            return value
        remaining = deadline - clock()
        if remaining <= 0:
            raise TimeoutError(f"Indexing did not reach the expected version in {seconds}s. Last state: {value['summary']}")
        print("Waiting:", value["summary"], flush=True)
        sleep(min(interval, remaining))


def _cache_flags(config):
    """Name the project and region for the API's Cloud Run calls.

    Example: gcloud("run", "services", "describe", config.api_service, *_cache_flags(config), "--format=json")
    """
    return (f"--project={config.project}", f"--region={config.cloud_run_region}")


def _settings_apart_from_cache(config, revision):
    """Return what a revision runs apart from SEMANTIC_CACHE, and its SEMANTIC_CACHE value.

    Equal settings mean the same image digest, account and resources, and every other environment row, literal
    values and secret references alike: two such revisions differ only in the answer-cache switch.

    Example: settings, cache = _settings_apart_from_cache(config, "documind-api-00042-abc")
    """
    document = json.loads(gcloud("run", "revisions", "describe", revision, *_cache_flags(config), "--format=json"))
    spec = document.get("spec", {})
    container = (spec.get("containers") or [{}])[0]
    rows = container.get("env", [])
    settings = {"image": container.get("image"), "digest": document.get("status", {}).get("imageDigest"),
                "account": spec.get("serviceAccountName"), "resources": container.get("resources"),
                "env": sorted(json.dumps(row, sort_keys=True) for row in rows if row.get("name") != "SEMANTIC_CACHE")}
    return settings, next((row.get("value") for row in rows if row.get("name") == "SEMANTIC_CACHE"), None)


def prepare_cache(session, disable=True):
    """Serve the API from a copy of its serving revision with SEMANTIC_CACHE=off; cleanup routes traffic back.

    It affects all tenants using this API. The kit routes traffic to a named revision after every deploy
    (F44), and so does this: the copy is created with --no-traffic, compared with the serving revision, and
    only then given 100% of traffic by name. Cloud Run builds the copy from the service configuration, so the
    configuration must run what the serving revision runs apart from the cache switch - never a candidate's
    settings. A copy an earlier lesson left is reused. Both revision names are saved before traffic moves.

    Example: prepare_cache(session, disable=True) saves the previous setting before an update
    """
    config = session.config
    serving = read_serving(config, config.api_service)
    value = serving.environment.get("SEMANTIC_CACHE")
    if value != "on":
        return
    require(disable, "SEMANTIC_CACHE=on. Set DISABLE_ANSWER_CACHE=True in prepare.py to temporarily disable it, or disable it yourself before this lesson.")
    flags = _cache_flags(config)
    status = json.loads(gcloud("run", "services", "describe", config.api_service, *flags, "--format=json")).get("status", {})
    latest = status.get("latestCreatedRevisionName", "")
    wanted, _ = _settings_apart_from_cache(config, serving.revision)
    template, template_cache = _settings_apart_from_cache(config, latest)
    require(template == wanted,
            f"The service configuration ({latest}) runs different settings from the serving revision ({serving.revision}), "
            "probably a candidate from another lesson. A cache-off copy would carry them: inspect Cloud Run before this lesson.")
    saved = session.state.setdefault("lesson31_cache", {"previous": value, "restore_required": True})
    require(saved["previous"] == value, "Cache setting changed outside this session; inspect before overwriting it.")
    saved.update(restore_required=True, revision_before=serving.revision)
    session.save()  # Intent is durable even if the deployment times out.
    print("Temporarily disabling the API answer cache for all tenants; cleanup restores it.")
    target = latest
    if latest == serving.revision or template_cache != "off" or latest != status.get("latestReadyRevisionName"):
        gcloud("run", "services", "update", config.api_service, *flags,
               "--update-env-vars=SEMANTIC_CACHE=off", "--no-traffic", "--quiet", timeout=600)
        status = json.loads(gcloud("run", "services", "describe", config.api_service, *flags, "--format=json")).get("status", {})
        target = status.get("latestCreatedRevisionName", "")
        copy, copy_cache = _settings_apart_from_cache(config, target)
        require(target != serving.revision and target == status.get("latestReadyRevisionName")
                and copy == wanted and copy_cache == "off",
                f"The new revision {target} is not a ready cache-off copy of {serving.revision}, so traffic was not moved. Inspect Cloud Run, then run cleanup.")
    saved["revision_after"] = target
    session.save()
    gcloud("run", "services", "update-traffic", config.api_service, *flags, f"--to-revisions={target}=100", "--quiet", timeout=600)
    now = read_serving(config, config.api_service)
    require(now.revision == target and now.environment.get("SEMANTIC_CACHE") == "off",
            "Cache update did not reach the serving revision. Run cleanup and inspect Cloud Run.")


def restore_cache(session):
    """Route traffic back, by name, to the revision that served before preparation.

    Nothing is rebuilt: the original revision serves again with every setting it had. If traffic moved to any
    revision other than the cache-off copy in the meantime, restoring would undo someone else's change, so
    this refuses and names the revision to restore.

    Example: restore_cache(session) restores the value saved during preparation
    """
    saved = session.state.get("lesson31_cache") or {}
    if not saved.get("restore_required"):
        return
    config = session.config
    serving = read_serving(config, config.api_service)
    if serving.environment.get("SEMANTIC_CACHE") != saved["previous"]:
        before = saved.get("revision_before")
        require(before and serving.revision == saved.get("revision_after"),
                f"Traffic changed since preparation ({serving.revision} is serving). Route it to "
                f"{before or 'the revision that served before'} (SEMANTIC_CACHE={saved['previous']}) yourself, then rerun cleanup.")
        print(f"Restoring the API answer cache: 100% of traffic back to {before}.")
        gcloud("run", "services", "update-traffic", config.api_service, *_cache_flags(config),
               f"--to-revisions={before}=100", "--quiet", timeout=600)
        now = read_serving(config, config.api_service)
        require(now.revision == before and now.environment.get("SEMANTIC_CACHE") == saved["previous"],
                "Cache restoration is not serving yet; inspect Cloud Run and rerun cleanup.")
    saved["restore_required"] = False
    session.save()


class LessonCloud:
    """Share authentication, clients and evidence between short teaching functions.
    
    Example: cloud = LessonCloud(session); rows = cloud.chunks("acme", "hr_policy_2026.md")
    """

    def __init__(self, session):
        """Use the IDE's ADC and explicit project; never inherit a terminal's token.
        
        Example: Construct the owning class with the arguments shown above; subsequent methods reuse these settings.
        """
        from google.cloud import firestore, storage
        require(session.config.tenant_id == "acme", "Lesson 1.1 uses the course's acme/zeta fixtures; set tenant_id to acme.")
        self.session = session
        self.db = firestore.Client(project=session.config.project, credentials=session.credentials)
        self.bucket = storage.Client(project=session.config.project, credentials=session.credentials).bucket(session.config.uploads_bucket)

    def save(self, name, value):
        """Retain a complete response locally before selecting a short display view.
        
        Example: session.save()
        """
        write_json(self.session.attempt / f"{name}.json", value)

    def document(self, path):
        """Read one document without a multi-minute implicit retry loop.
        
        Example: self.document('sources/' + source_id_for(expected['tenant'], expected['name']))
        """
        return self.db.document(path).get(retry=None, timeout=15).to_dict() or {}

    def rows(self, collection, **equal):
        """Read matching rows; dictionaries preserve IDs beside their payloads.
        
        Example: self.rows('chunks', tenant_id=tenant, source_uri=f'gs://{self.bucket.name}/{tenant}/{name}', current=True)
        """
        from google.cloud.firestore_v1.base_query import FieldFilter
        query = self.db.collection(collection)
        for field, value in equal.items():
            query = query.where(filter=FieldFilter(field, "==", value))
        return {row.id: row.to_dict() for row in query.stream(retry=None, timeout=15)}

    def chunks(self, tenant, name):
        """Retired rows cannot satisfy a current-version or locator demonstration.
        
        Example: self.chunks(expected['tenant'], expected['name'].split('/', 1)[1])
        """
        return self.rows("chunks", tenant_id=tenant, source_uri=f"gs://{self.bucket.name}/{tenant}/{name}", current=True)

    def request(self, name, path, body=None, identity="member", expected_status=200):
        """Consume the entire HTTP body, record refusals and enforce the expected status.
        
        Example: self.request(name, '/v1/query', body)
        """
        headers = {"Content-Type": "application/json"}
        require(identity in {"member", "outsider", "none"}, "Unknown request identity.")
        if identity != "none":
            headers["Authorization"] = "Bearer " + self.session.identity_token(outsider=identity == "outsider")
        request = Request(os.environ["API"].rstrip("/") + path,
                          data=json.dumps(body).encode() if body is not None else None, headers=headers)
        try:
            response = urlopen(request, timeout=self.session.config.answer_wait_seconds)
        except HTTPError as error:
            response = error  # A refusal is evidence, not a failed JSON parse.
        with response:
            text = response.read().decode("utf-8", errors="replace")
            status, content_type = response.code, response.headers.get("Content-Type", "")
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = None
        self.save(name, {"status": status, "content_type": content_type, "json": payload, "body": text})
        print(f"{name}: HTTP {status}", text[:200])
        require(status == expected_status, f"{name}: expected HTTP {expected_status}, got {status}; inspect {name}.json.")
        return {"json": payload, "body": text, "content_type": content_type}

    def query(self, name, question, *, filters=None, fresh=True):
        """Ask ACME and optionally require evidence that Vector Search ran now.
        
        Example: self.query(name, question, filters, fresh) in the owning lesson/helper context
        """
        # The API caches tenant settings for 60s. Only wait out what remains of
        # this preparation's propagation window, then still inspect real stages.
        while True:
            remaining = self.session.state.get("lesson31_pin_ready_after", 0) - time.time()
            if remaining <= 0:
                break
            print(f"Allowing the API's tenant-settings cache to expire: {remaining:.0f}s", flush=True)
            time.sleep(min(5, remaining))
        body = {"query": question, "tenant_id": "acme", "stream": False}
        if filters is not None:
            body["filters"] = filters
        result = self.request(name, "/v1/query", body)["json"]
        require(isinstance(result, dict), "The API did not return a JSON object.")
        if fresh:
            require_fresh_vector(result)
        return result

    def fixture(self, tenant, filename, data, *, upload):
        """Use exact bytes and a generation guard; never overwrite a different file.
        
        UI mode only verifies the existing object. Operator mode creates a missing
        fixture and reuses an identical existing object, avoiding duplicate-upload
        events whose content claim may already have been completed.
        
        Example: self.fixture(tenant, filename, data, upload) in the owning lesson/helper context
        """
        from google.api_core.exceptions import NotFound
        from services.ingest.contracts import DocumentContract, sha256_of
        name = f"{tenant}/{filename}"
        blob = self.bucket.blob(name)
        try:
            blob.reload(retry=None, timeout=15)
        except NotFound:
            require(upload, f"Upload evals/demo/{filename} in the ACME UI (Documents -> Upload -> Index documents), then rerun demo 2. Or explicitly choose ACME_UPLOAD='operator' in that file.")
            blob.upload_from_string(data, content_type="text/markdown", if_generation_match=0, timeout=60)
            print("Operator uploaded:", name)
        require(blob.size == len(data), f"{name} has different bytes. Use the exact kit fixture; this demo will not overwrite it.")
        remote = blob.download_as_bytes(if_generation_match=blob.generation, retry=None, timeout=30)
        require(remote == data, f"{name} differs from the local fixture (including line endings). Inspect it before continuing.")
        contract = DocumentContract(tenant_id=tenant, sha256=sha256_of(data), gcs_uri=f"gs://{self.bucket.name}/{name}", pages=0)
        return {"tenant": tenant, "name": name, "uri": contract.gcs_uri,
                "sha256": contract.sha256, "doc_key": contract.doc_key, "generation": str(blob.generation)}

    def wait_indexed(self, expected):
        """Wait for this exact version, then save the ledger, claim and current chunks.
        
        Example: self.wait_indexed(expected) in the owning lesson/helper context
        """
        from services.ingest.idempotency import source_id_for

        def read():
            """Read the exact source ledger, content claim and current chunks for the saved object generation.
            
            Example: read()
            """
            source = self.document("sources/" + source_id_for(expected["tenant"], expected["name"]))
            claim = self.document("documents/" + expected["doc_key"])
            chunks = self.chunks(expected["tenant"], expected["name"].split("/", 1)[1])
            result = {"source": source, "claim": claim, "chunks": chunks,
                      "summary": {"source_status": source.get("status"), "generation": source.get("generation"),
                                  "expected_generation": expected["generation"], "doc_key": source.get("doc_key"),
                                  "claim_status": claim.get("status"), "current_chunks": len(chunks)}}
            self.save(expected["tenant"] + "_index_observation", result)
            require(source.get("status") != "withdrawn", "This source was withdrawn. Inspect it and use the lesson 1.8 restore procedure deliberately.")
            require(claim.get("status") != "failed", f"Worker failed: {claim.get('error')}; inspect the saved claim and ingest logs.")
            return result

        return poll_until(read, lambda r: version_ready(expected, r["source"], r["claim"], r["chunks"]),
                          self.session.config.ingest_wait_seconds, self.session.config.poll_seconds)

    def worker_logs(self, expected):
        """Show only this tenant/key/generation's events; absence is not success evidence.
        
        Example: self.worker_logs(expected) in the owning lesson/helper context
        """
        values = {"resource.type": "cloud_run_revision", "resource.labels.service_name": self.session.config.ingest_service,
                  "jsonPayload.tenant": expected["tenant"], "jsonPayload.doc_key": expected["doc_key"],
                  "jsonPayload.generation": expected["generation"]}
        query = " AND ".join(f"{key}={json.dumps(value)}" for key, value in values.items())
        rows = json.loads(gcloud("logging", "read", query, f"--project={self.session.config.project}",
                                 "--limit=10", "--freshness=30d", "--format=json"))
        self.save(expected["tenant"] + "_worker_logs", rows)
        print("Exact-version worker events:", [r.get("jsonPayload", {}).get("event") for r in rows]
              or "none retained/visible yet; ledger + claim + chunks are the indexing evidence")
