# The Ralph loop's image (workshop lesson 10.10): Gemini CLI at a pinned version, Python 3.12 for the task's fast test
# and for the oracle, and nothing else - no gcloud, no credential, no kit file. make ralph-image builds it with this
# directory as the whole build context, so no other kit file can enter it:
#     make ralph-image      Gemini CLI at GEMINI_CLI_VERSION, the kit's pin in mk/coding.mk (GEMINI_CLI_VERSION=<x.y.z> moves it)
# commands/ralph.py runs two containers from it: the agent (the workspace mounted, a model-only credential in an
# --env-file) and the oracle (no network at all, everything mounted read-only); with RALPH_EGRESS=proxy a third, the
# proxy (commands/ralph/egress.py, mounted read-only), the agent's one way out, to the model endpoint alone.
FROM node:22-bookworm-slim AS node

FROM python:3.12-slim-bookworm
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
 && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx
# No default: an unpinned build would take whatever npm calls latest that day.
ARG GEMINI_CLI_VERSION
RUN test -n "$GEMINI_CLI_VERSION" || { echo "set GEMINI_CLI_VERSION: make ralph-image GEMINI_CLI_VERSION=<x.y.z>" >&2; exit 1; } \
 && npm install --global --no-fund --no-audit "@google/gemini-cli@${GEMINI_CLI_VERSION}" \
 && npm cache clean --force
LABEL documind.gemini-cli="${GEMINI_CLI_VERSION}"
COPY iteration.sh /usr/local/bin/ralph-iteration
RUN chmod 0755 /usr/local/bin/ralph-iteration && useradd --create-home --uid 1000 ralph
USER ralph
WORKDIR /work
