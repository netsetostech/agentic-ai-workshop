# {{YOUR COMPANY}} on DocuMind: the runbook

<!--
The capstone's component 8 (lesson 11.8). Copy this file to your fork's root as RUNBOOK.md, replace every
placeholder in double curly braces, braces included, and delete these comments.

make capstone-check reads two things for component 8: that this file says how to roll documind-api back, with the
command lesson 11.3 taught or with gcloud's traffic update; and two successive make smoke-deployed runs in
evals/reports/smoke-deployed.jsonl that show a rollback, with /version answered before and after, which lesson 11.3's
runs record. make handover writes HANDOVER.md whole each time, with every alert policy the Terraform declares and what
ops/runbooks.json says to do when it pages: this file keeps what you learned on top of that, and the next handover
leaves it alone. commands/tests/capstone_fork/RUNBOOK.md is one filled in, for a made-up company.
-->

## When a policy pages

<!-- One item per alert policy that can page you: HANDOVER.md's Alert policies table lists them all. -->

- {{POLICY}}: {{What to do when it pages, with the command.}}
- {{POLICY}}: {{What to do when it pages, with the command.}}

## Roll back the API

`{{THE ROLLBACK COMMAND, WITH YOUR PROJECT AND REGION}}` {{What it moves the traffic back to, and what you run next.}}

## The recorded rollback

{{When, which revision was promoted and why it was rolled back, and the two smoke runs that show it.}}
