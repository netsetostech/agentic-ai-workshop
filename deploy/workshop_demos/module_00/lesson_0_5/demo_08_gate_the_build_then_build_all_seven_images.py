"""Lesson 0.5: Gate the build, then build all seven images

The kit's own regression tests, before anything is built. Run the regression tests that ship with the pinned commit against the local source. Stop if the task-type, carry-over or repair tests fail. Seven images, all tagged with the same GIT_SHA. First prepare the build-source bucket. On an existing demo the bucket is reused; it is only created when the lookup says it does not exist. First prepare the build-source bucket. On an existing demo the bucket is reused; it is only created when the lookup says it does not exist. Then prepare a fresh temporary build context from the original source directories and cloudbuild.yaml. It excludes Terraform state, providers and plan files. Rerun this block whenever any source file changes. Then prepare a fresh temporary build context from the original source directories and cloudbuild.yaml. It excludes Terraform state, providers and plan files. Rerun this block whenever any source file changes. Build the images. The helper submits one build; the chain runs them in order and stops at the first build that does not report SUCCESS. The UI is built from its own directory because its Dockerfile expects requirements.txt at the context root.

Run order inside this file:
1. Build gate: regression tests and shared imports (source window 34)
2. F3. Build all seven images (source window 35)
3. F3. Build all seven images (source window 36)
4. F3. Build all seven images (source window 37)

Prerequisites: demo_07_restore_the_shell_pin_git_sha_export_the_runtime_settings_and_prepare_the_secret.
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


# Original CLI workflow for step_01_build_gate_regression_tests_and_shared_imp.
COMMANDS_01 = """cd "${DEMO_ROOT:?Restore DEMO_ROOT}" &&
[[ "$(git rev-parse --short HEAD)" == "${GIT_SHA:?Run the pin block first}" ]] &&
git ls-files --error-unmatch commands/tests/test_document_embeddings.py commands/tests/test_spanner_graph.py >/dev/null &&
python -m unittest discover -s commands/tests -p test_document_embeddings.py &&
python -m unittest discover -s commands/tests -p test_spanner_graph.py &&
python - <<'PY'
from pathlib import Path
from shared.sparse_encoder import sparse_encode, SPARSE_ENCODER_VERSION
for name in ('shared/sparse_encoder.py','shared/documind_graph.py','services/rag-api/schemas.py',
             'services/rag-api/hybrid.py','services/ingest/indexer.py','services/frontend/documents.py','services/frontend/chat.py'):
    assert Path(name).is_file(), name
values, dimensions = sparse_encode('Module-4 smoke lantern smoke lantern')
assert values and len(values) == len(dimensions) == len(set(dimensions))
assert dimensions == sorted(dimensions)
print('PASS: shared sparse encoder available:', SPARSE_ENCODER_VERSION)
PY

"""

def step_01_build_gate_regression_tests_and_shared_imp(session):
    """Run Build gate: regression tests and shared imports at this checkpoint.

    The kit's own regression tests, before anything is built. Run the regression tests that ship with the pinned commit against the local source. Stop if the task-type, carry-over or repair tests fail.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Build gate.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_f3_build_all_seven_images.
COMMANDS_02 = """(
set -euo pipefail
: "${PROJECT:?Run F1}" "${REGION:?Run F1}" "${BUILD_SA:?Run F1}" "${OPERATOR_EMAIL:?Restore session}"
: "${BUILD_SOURCE_BUCKET:?restore ~/rag-env.sh (S3 sets it)}"
if out="$(gcloud storage buckets describe "gs://$BUILD_SOURCE_BUCKET" --project="$PROJECT" --format='value(name)' 2>&1)"; then
  echo "Reusing gs://$BUILD_SOURCE_BUCKET"
elif grep -qiE 'not found|404' <<<"$out"; then
  gcloud storage buckets create "gs://$BUILD_SOURCE_BUCKET" --project="$PROJECT" \\
    --location="$REGION" --uniform-bucket-level-access --public-access-prevention
else
  printf '%s\\n' "$out" >&2
  echo 'STOP: bucket lookup failed for a reason other than not-found. Fix access first.' >&2
  exit 1
fi
gcloud storage buckets add-iam-policy-binding "gs://$BUILD_SOURCE_BUCKET" \\
  --member="serviceAccount:$BUILD_SA" --role=roles/storage.objectViewer >/dev/null
gcloud projects add-iam-policy-binding "$PROJECT" \\
  --member="serviceAccount:$BUILD_SA" --role=roles/logging.logWriter --condition=None >/dev/null
gcloud iam service-accounts add-iam-policy-binding "$BUILD_SA" --project="$PROJECT" \\
  --member="user:$OPERATOR_EMAIL" --role=roles/iam.serviceAccountUser --condition=None >/dev/null
echo 'PASS: build bucket and build-account access ready.'
)

"""

def step_02_f3_build_all_seven_images(session):
    """Run F3. Build all seven images at this checkpoint.

    Seven images, all tagged with the same GIT_SHA. First prepare the build-source bucket. On an existing demo the bucket is reused; it is only created when the lookup says it does not exist.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Build bucket.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_f3_build_all_seven_images.
COMMANDS_03 = """rag_prepare_build_context() {
  cd "$DEMO_ROOT" || return
  [[ "$(git rev-parse --short HEAD)" == "${GIT_SHA:-}" ]] || { printf 'STOP: checkout is not GIT_SHA; rerun the pin block.\\n' >&2; return 1; }
  [[ -z "$(git status --porcelain -- shared services cloudbuild.yaml)" ]] || { printf 'STOP: build inputs have local changes.\\n' >&2; return 1; }
  for path in shared/documind_schemas.py services/rag-api/schemas.py services/rag-api/main.py services/ingest/main.py cloudbuild.yaml; do
    test -s "$path" || { printf 'STOP: missing source file %s\\n' "$path" >&2; return 1; }
  done
  PYTHONPATH="$DEMO_ROOT/services/rag-api:$DEMO_ROOT" "$HOME/rag-shell-venv/bin/python" -c 'import schemas; import shared.documind_schemas as c; assert schemas.RAGAnswer is c.RAGAnswer; print("PASS: actual schema imports")' || return
  BUILD_CONTEXT="$(mktemp -d)" || return
  cp -a shared services cloudbuild.yaml "$BUILD_CONTEXT/" || return
  for service in ingest rag-api admin frontend chat mcp agent; do
    test -s "$BUILD_CONTEXT/services/$service/Dockerfile" || { printf 'STOP: no Dockerfile for %s\\n' "$service" >&2; return 1; }
    test -s "$BUILD_CONTEXT/services/$service/requirements.txt" || { printf 'STOP: no requirements.txt for %s\\n' "$service" >&2; return 1; }
  done
  test -s "$BUILD_CONTEXT/services/rag-api/schemas.py" || return 1
  test -s "$BUILD_CONTEXT/shared/documind_schemas.py" || return 1
  export BUILD_CONTEXT
  printf 'Verified fresh build context: %s\\n' "$BUILD_CONTEXT"
}
rag_prepare_build_context

"""

def step_03_f3_build_all_seven_images(session):
    """Run F3. Build all seven images at this checkpoint.

    First prepare the build-source bucket. On an existing demo the bucket is reused; it is only created when the lookup says it does not exist. Then prepare a fresh temporary build context from the original source directories and cloudbuild.yaml. It excludes Terraform state, providers and plan files. Rerun this block whenever any source file changes.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Build context.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_f3_build_all_seven_images.
COMMANDS_04 = """: "${PROJECT:?Run F1}" "${REGION:?Run F1}" "${IMAGE_REPO:?Run F1}" "${BUILD_SA:?Run F1}"
: "${GIT_SHA:?Restore the session}" "${BUILD_CONTEXT:?Run the build-context block}" "${BUILD_SOURCE_BUCKET:?Set BUILD_SOURCE_BUCKET}"
echo "Building tag $GIT_SHA into $IMAGE_REPO from $BUILD_CONTEXT"

rag_build() {  # image-name  context-dir  dockerfile
  gcloud builds submit "$2" --project="$PROJECT" --region="$REGION" \\
    --config="$DEMO_ROOT/cloudbuild.yaml" \\
    --service-account="projects/$PROJECT/serviceAccounts/$BUILD_SA" \\
    --gcs-source-staging-dir="gs://$BUILD_SOURCE_BUCKET/source" \\
    --substitutions="_IMAGE=$IMAGE_REPO/$1:$GIT_SHA,_DOCKERFILE=$3"
}

rag_build ingest "$BUILD_CONTEXT"                   services/ingest/Dockerfile &&
rag_build api    "$BUILD_CONTEXT"                   services/rag-api/Dockerfile &&
rag_build admin  "$BUILD_CONTEXT"                   services/admin/Dockerfile &&
rag_build ui     "$BUILD_CONTEXT/services/frontend" Dockerfile &&
rag_build chat   "$BUILD_CONTEXT"                   services/chat/Dockerfile &&
rag_build mcp    "$BUILD_CONTEXT"                   services/mcp/Dockerfile &&
rag_build agent  "$BUILD_CONTEXT"                   services/agent/Dockerfile &&
gcloud artifacts docker images list "$IMAGE_REPO" --project="$PROJECT" --include-tags

"""

def step_04_f3_build_all_seven_images(session):
    """Run F3. Build all seven images at this checkpoint.

    Then prepare a fresh temporary build context from the original source directories and cloudbuild.yaml. It excludes Terraform state, providers and plan files. Rerun this block whenever any source file changes. Build the images. The helper submits one build; the chain runs them in order and stops at the first build that does not report SUCCESS. The UI is built from its own directory because its Dockerfile expects requirements.txt at the context root.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Build images.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_34', step_01_build_gate_regression_tests_and_shared_imp),
        ('source_35', step_02_f3_build_all_seven_images),
        ('source_36', step_03_f3_build_all_seven_images),
        ('source_37', step_04_f3_build_all_seven_images),
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
