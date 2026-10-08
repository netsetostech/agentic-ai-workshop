# mk/ - the Makefile, one file per lane

The kit's `Makefile` keeps what every target shares: the variables (`PROJECT`, `REGION`, the Terraform variable
list, the service list), `guard-project`, `.PHONY`, and the core lifecycle of a lane (`plan`, `up`, `build`,
`deploy-services`, `down`, the smokes, the release). Everything a course module teaches as its own operations lives
here, one file per lane, pulled in by `include mk/*.mk`:

| File | Targets | Course module |
|---|---|---|
| `ingestion.mk` | `roster`, `tenant-policy`, `tenant-backend`, `vector-status`, `wait-vectors`, `backfill-vectors`, `ingest-one`, `poison`, `dlq` | 3 Ingestion |
| `lifecycle.mk` | `reindex`, `retire`, `restore`, `reconcile`, `backfill-current`, `reconcile-job`, `sources`, `purge`, `smoke-reindex`, `batch-job`, `batch`, `queued` | 4 Lifecycle |
| `agents.mk` | `desk-check`, `route-probe`, `route-index`, `route-calibrate`, `doc-types`, `limits`, `limits-check`, `limits-drill`, `desk`, `roles`, `desk-queues`, `cases`, `cases-overdue`, `smoke-cases`, `smoke-desk`, `route-eval`, `desk-views`, `desk-job`, `desk-operators`, `deploy-gchat`, `smoke-gchat` | 10 Agents (a chat turn's limits, lesson 5.5; the DocuMind Desk, lessons 5.6 and 10.4, and its Google Chat door) |

The Makefile pins the default goal to `dryrun` (Tier A: offline, free), so a bare `make` never depends on which file
here sorts first. Still, always name the target. One file adds variables of its own: `agents.mk` declares `DESK_JOB`,
`CHAT_IMAGE`, `DESK_EVAL_SAS`, `DESK_ROUTER_ALERTS`, `DESK_GATE_ALERTS` and `GCHAT_DOOR`, and appends all but
`DESK_EVAL_SAS` to the Makefile's Terraform variable list (`TF_EXTRA_VARS +=`, which works because that list is a
recursive variable and the `include` comes after it).

Three rules keep the files small:

1. **A target is a one-line entry.** A recipe longer than a few lines is a script under `commands/` (`ingest-one.sh`,
   `poison.sh`, `reindex.sh`, `wait-vectors.sh`, `vector-status.sh`, `limits-check.sh`, `limits-drill.sh`, `desk-check.sh`) or a
   subcommand of `commands/lane.py` (`sources`, `queued`, `vector-status`, `backfill-vectors`, `roster`,
   `tenant-backend`, `tenant-policy`, `limits`), or of `commands/desk_ops.py` for the DocuMind Desk's targets
   (`doc-types`, `desk`, `roles`, `desk-queues`, `cases`, `route-index`). The make target and the direct call run the same code, so a learner without `make` -
   Windows, Colab - runs `PROJECT=<id> TENANT=acme FILE=... bash commands/ingest-one.sh` or
   `python commands/lane.py sources`.
2. **The comment travels with the target.** The design notes that explained a target in the Makefile sit above it
   here, unchanged.
3. **A new module is a new file.** Add `mk/<lane>.mk`, list its targets in the Makefile's `.PHONY`, and give any
   long recipe a script, a `lane.py` subcommand or, for the Desk, a `desk_ops.py` subcommand first. Nothing else
   changes: `tools/check_*.py` read the Makefile and `mk/*.mk` as one text, and the publish (`tools/publish_learner.py`
   in the authoring repository) copies every tracked file under the kit.

Moved on 22 September 2026, with every target's name, comment and recipe kept byte for byte except the six that
became scripts and one comment that still said five delivery attempts (eventarc.tf says twelve); the scripts also fix a latent slip in the old recipes, where a `FILE=` or golden-set check that
failed inside `( ...; exit 1 )` did not stop the recipe.
