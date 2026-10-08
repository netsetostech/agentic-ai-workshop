"""The DocuMind Desk's callers in tools/check_authz.py (workshop lesson 5.6): the five eval accounts and the Google Chat
bridge's account are read on both sides of documind-chat's caller graph, and minting_as() finds every way the kit
could let someone mint as the bridge - and finds none in the kit as it is.
"""
import importlib.util
import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "deploy"
_spec = importlib.util.spec_from_file_location("check_authz_under_test", ROOT / "tools" / "check_authz.py")
authz = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(authz)

SIX = set(authz.DESK_EVAL) | {authz.GCHAT}


def kit_texts() -> dict:
    texts = {"Makefile": (KIT / "Makefile").read_text(encoding="utf-8")}
    for sub, ext in (("mk", ".mk"), ("commands", ".sh"), ("commands", ".py"), ("terraform", ".tf")):
        for f in sorted(os.listdir(KIT / sub)):
            if f.endswith(ext):
                texts[f"{sub}/{f}"] = (KIT / sub / f).read_text(encoding="utf-8")
    return texts


class CallersTests(unittest.TestCase):
    def test_the_six_on_both_sides(self):
        graph = authz.graph_from((KIT / "terraform" / "sa.tf").read_text(encoding="utf-8"))
        bound = authz.bindings_in((KIT / "commands" / "lesson-12.8.sh").read_text(encoding="utf-8"))
        self.assertLessEqual(SIX, graph["documind-chat"][0])
        self.assertLessEqual(SIX, bound["documind-chat"])
        self.assertEqual(graph["documind-chat"][0], bound["documind-chat"])
        for service, (callers, _) in graph.items():
            if service != "documind-chat":
                self.assertFalse(SIX & callers, service)

    def test_each_name_is_a_caller_token(self):
        for acct in SIX:
            self.assertEqual(authz.callers_in(f"#   documind-chat <- {acct}  (lesson-12.8.sh)"), {acct})
            self.assertLessEqual(len(acct), 30, "a service account id is 6 to 30 characters")
        # a hyphenated name matches nothing: the graph would list fewer callers than the script binds
        self.assertEqual(authz.callers_in("documind-desk-eval-acme documind-desk-eval-acme-sa"), set())

    def test_desk_operators_does_not_name_the_bridge(self):
        mk = (KIT / "mk" / "agents.mk").read_text(encoding="utf-8")
        block = mk.split("\ndesk-operators:", 1)[1].split("\n\n", 1)[0]
        self.assertIn("$(DESK_EVAL_SAS)", block)
        self.assertNotIn(authz.GCHAT, block)
        sas = authz._make_defs({"mk/agents.mk": mk})["DESK_EVAL_SAS"].split()
        self.assertEqual(sas, list(authz.DESK_EVAL))


class MintingTests(unittest.TestCase):
    def test_the_kit_lets_nobody_mint_as_the_bridge(self):
        self.assertEqual(authz.minting_as(kit_texts(), authz.GCHAT), [])

    def assertCaught(self, path, text, extra=None):
        texts = {**kit_texts(), **(extra or {})}
        texts[path] = texts.get(path, "") + "\n" + text + "\n"
        found = authz.minting_as(texts, authz.GCHAT)
        self.assertTrue(found, f"not caught: {text[:80]}")
        return found

    def test_mints_and_grants_are_caught(self):
        self.assertCaught("Makefile", "operators2:\n\t@for sa in documind-ui-sa documind-gchat-sa; do \\\n"
                                      "\t  gcloud iam service-accounts add-iam-policy-binding $$sa@$(PROJECT).iam.gserviceaccount.com \\\n"
                                      "\t    --member=\"user:$$who\" --role=roles/iam.serviceAccountTokenCreator; done")
        self.assertCaught("mk/agents.mk", "DESK_EVAL_SAS += documind-gchat-sa")
        self.assertCaught("mk/agents.mk", "smoke-x:\n\tDOCUMIND_IMPERSONATE_SA=documind-gchat-sa@$(PROJECT).iam.gserviceaccount.com python x.py")
        self.assertCaught("commands/x.sh", "gcloud auth print-identity-token --impersonate-service-account=documind-gchat-sa@$PROJECT.iam.gserviceaccount.com")
        self.assertCaught("commands/x.sh", "gcloud iam service-accounts keys create k.json --iam-account=documind-gchat-sa@$PROJECT.iam.gserviceaccount.com")
        self.assertCaught("commands/x.py", 'subprocess.run(["gcloud", "auth", "print-identity-token", '
                                           '"--impersonate-service-account=documind-gchat-sa@p.iam.gserviceaccount.com"])')
        self.assertCaught("commands/x.sh", "gcloud projects add-iam-policy-binding $PROJECT --member=user:you@example.com "
                                           "--role=roles/iam.serviceAccountTokenCreator")
        self.assertCaught("commands/x.sh", "gcloud projects add-iam-policy-binding $PROJECT "
                                           "--member=serviceAccount:documind-gchat-sa@$PROJECT.iam.gserviceaccount.com --role=roles/viewer")
        for ref in ("google_service_account.gchat.name", "google_service_account.gchat[0].name"):    # [0]: counted on GCHAT_DOOR
            self.assertCaught("terraform/x.tf", 'resource "google_service_account_iam_member" "x" {\n'
                                                f'  service_account_id = {ref}\n'
                                                '  role               = "roles/iam.serviceAccountUser"\n'
                                                '  member             = "user:you@example.com"\n}')
        self.assertCaught("terraform/x.tf", 'resource "google_project_iam_member" "x" {\n  project = var.project_id\n'
                                            '  role    = "roles/datastore.user"\n'
                                            '  member  = "serviceAccount:${google_service_account.gchat.email}"\n}')
        self.assertCaught("terraform/x.tf", 'resource "google_project_iam_member" "x" {\n  project = var.project_id\n'
                                            '  role    = "roles/iam.serviceAccountTokenCreator"\n'
                                            '  member  = "user:you@example.com"\n}')
        sa = kit_texts()["terraform/sa.tf"]
        found = authz.minting_as({**kit_texts(), "terraform/sa.tf": sa.replace(
            "    chat   = google_service_account.chat.name\n",
            "    chat   = google_service_account.chat.name\n    gchat  = google_service_account.gchat.name\n")}, authz.GCHAT)
        self.assertTrue(any("cicd_actas" in f for f in found), found)

    def test_what_is_allowed(self):
        clean = kit_texts()
        # an invoker binding on a service, in a loop that names the bridge, is not a mint
        loop = ("for who in documind-ui-sa documind-gchat-sa; do\n  gcloud run services add-iam-policy-binding documind-chat \\\n"
                "    --member=\"serviceAccount:$who@$PROJECT.iam.gserviceaccount.com\" --role=roles/run.invoker --quiet\ndone")
        # its own self-grant, the one exception (posting as the app, if the probe needs it)
        self_grant = ('resource "google_service_account_iam_member" "gchat_self" {\n'
                      '  service_account_id = google_service_account.gchat.name\n'
                      '  role               = "roles/iam.serviceAccountTokenCreator"\n'
                      '  member             = "serviceAccount:${google_service_account.gchat.email}"\n}')
        comment = "# nobody gets roles/iam.serviceAccountTokenCreator on documind-gchat-sa, nor impersonates it"
        self.assertEqual(authz.minting_as({**clean, "commands/x.sh": loop + "\n" + comment, "terraform/x.tf": self_grant},
                                          authz.GCHAT), [])


class GchatDoorTests(unittest.TestCase):
    """The Google Chat door (workshop lesson 10.4): the bridge's two project roles, the push account, the topic."""

    def grant(self, role, condition=None, member="${google_service_account.gchat.email}"):
        cond = ("\n  condition {\n    title      = \"x\"\n    expression = \"" + condition + "\"\n  }") if condition else ""
        return ('resource "google_project_iam_member" "x" {\n  project = var.project_id\n'
                f'  role    = "{role}"\n  member  = "serviceAccount:{member}"{cond}\n}}')

    def test_the_bridge_roles_as_conditioned(self):
        own = authz.BRIDGE_PROJECT_ROLES["roles/datastore.user"]
        blocks = lambda text: list(authz._tf_blocks(text))[0]
        self.assertTrue(authz.bridge_project_role("google_project_iam_member", blocks(self.grant("roles/logging.logWriter"))[2]))
        self.assertTrue(authz.bridge_project_role("google_project_iam_member", blocks(self.grant("roles/datastore.user", own))[2]))
        for text in (self.grant("roles/datastore.user"),                                     # every database
                     self.grant("roles/datastore.user", own.replace("documind-gchat", "(default)")),
                     self.grant("roles/datastore.user", own + " || true"),
                     self.grant("roles/datastore.owner", own),
                     self.grant("roles/logging.logWriter", "true"),
                     self.grant("roles/pubsub.publisher")):
            kind, _, body = blocks(text)
            self.assertFalse(authz.bridge_project_role(kind, body), text)
            found = authz.minting_as({**kit_texts(), "terraform/x.tf": text}, authz.GCHAT)
            self.assertTrue(any("gives documind-gchat-sa a project role" in f for f in found), text)

    def test_only_pubsub_mints_as_the_push_account(self):
        found = authz.minting_as(kit_texts(), authz.GCHAT_PUSH)
        self.assertEqual(len(found), 1, found)
        self.assertIn("pubsub_mints_gchatpush_token", found[0])
        person = ('resource "google_service_account_iam_member" "y" {\n'
                  '  service_account_id = google_service_account.gchatpush.name\n'
                  '  role               = "roles/iam.serviceAccountTokenCreator"\n  member             = "user:you@example.com"\n}')
        found = authz.minting_as({**kit_texts(), "terraform/x.tf": person}, authz.GCHAT_PUSH)
        self.assertTrue(any("terraform/x.tf" in f for f in found), found)

    def door(self, extra: dict) -> list:
        texts = kit_texts()
        for path, text in extra.items():
            texts[path] = texts.get(path, "") + "\n" + text + "\n"
        return authz.gchat_door_problems({p: t for p, t in texts.items() if p.endswith(".tf")}, texts)

    def test_the_kit_keeps_the_topic_to_the_bridge(self):
        self.assertEqual(self.door({}), [])

    def test_a_second_publisher_on_the_topic_is_caught_however_it_names_it(self):
        member = '  role   = "roles/pubsub.publisher"\n  member = "user:you@example.com"\n}'
        for topic in ('"documind-gchat-work"', '"projects/${var.project_id}/topics/documind-gchat-work"',
                      "google_pubsub_topic.gchat_work.id", "google_pubsub_topic.gchat_work.name", "google_pubsub_topic.gchat_work[0].id"):
            found = self.door({"terraform/x.tf": f'resource "google_pubsub_topic_iam_member" "x" {{\n  topic  = {topic}\n{member}'})
            self.assertTrue(any("documind-gchat-work: one binding" in f for f in found), topic)
        found = self.door({"terraform/x.tf": 'resource "google_pubsub_topic_iam_binding" "x" {\n'
                                             '  topic   = "documind-gchat-work"\n  role    = "roles/pubsub.publisher"\n'
                                             '  members = ["serviceAccount:documind-ui-sa@p.iam.gserviceaccount.com"]\n}'})
        self.assertTrue(any("documind-gchat-work: one binding" in f for f in found), found)
        for line in ("gcloud pubsub topics add-iam-policy-binding documind-gchat-work --member=user:you@example.com "
                     "--role=roles/pubsub.publisher",
                     "gcloud pubsub topics add-iam-policy-binding \\\n  documind-gchat-work --role=roles/pubsub.publisher"):
            found = self.door({"commands/x.sh": line})
            self.assertTrue(any(f.startswith("commands/x.sh: a Pub/Sub grant") for f in found), line)

    def test_a_project_wide_pubsub_role_is_caught(self):
        for role in authz.PUBSUB_WIDE:
            found = self.door({"terraform/x.tf": f'resource "google_project_iam_member" "x" {{\n  project = var.project_id\n'
                                                 f'  role    = "{role}"\n  member  = "user:you@example.com"\n}}'})
            self.assertTrue(any("project-wide" in f for f in found), role)
        for roles in ('["roles/pubsub.editor"]', '[\n    "roles/viewer",\n    "roles/pubsub.editor",\n  ]'):
            found = self.door({"terraform/x.tf": f'locals {{\n  wide_roles = {roles}\n}}\n'
                                                 'resource "google_project_iam_member" "x" {\n  for_each = toset(local.wide_roles)\n'
                                                 '  project  = var.project_id\n  role     = each.value\n'
                                                 '  member   = "user:you@example.com"\n}'})
            self.assertTrue(any("project-wide" in f for f in found), roles)
        found = self.door({"commands/x.sh": "gcloud projects add-iam-policy-binding $PROJECT --member=user:you@example.com "
                                            "--role=roles/pubsub.admin"})
        self.assertTrue(any(f.startswith("commands/x.sh: a Pub/Sub grant") for f in found), found)

    def test_the_subscription_dead_letters_nothing(self):
        tf = kit_texts()["terraform/gchat.tf"].replace(
            "  ack_deadline_seconds       = 300\n",
            "  dead_letter_policy {\n    dead_letter_topic = google_pubsub_topic.gchat_work.id\n  }\n"
            "  ack_deadline_seconds       = 300\n")
        texts = {**kit_texts(), "terraform/gchat.tf": tf}
        found = authz.gchat_door_problems({p: t for p, t in texts.items() if p.endswith(".tf")}, texts)
        self.assertIn("the push subscription mints as the push account, and dead-letters nothing", found)

    def test_the_push_account_is_not_a_delegate(self):
        delegation = (KIT / "services" / "chat" / "delegation.py").read_text(encoding="utf-8")
        self.assertNotIn(authz.GCHAT_PUSH[:-3], delegation)
        graph = authz.graph_from((KIT / "terraform" / "sa.tf").read_text(encoding="utf-8"))
        self.assertEqual({s for s, (c, _) in graph.items() if authz.GCHAT_PUSH in c}, {"documind-gchat"})


if __name__ == "__main__":
    unittest.main()
