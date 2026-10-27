"""The DEPLOY blocks make deploy-services runs, read offline (8 October 2026). No command runs; nothing is fetched.

make up's deploy step cuts the block between `# ---- DEPLOY ----` and the next marker out of each script and runs
it with `sh -ec`, so the first command that fails stops make up there: the services after it, then wait-index,
roster, managed-stores and operators, never run. lesson-12.3.sh's block did exactly that until 8 October 2026. It
called `gcloud builds submit --file=`, a flag gcloud does not have; it wrote us-central1 where the other blocks
use REGION; it bound a placeholder group to IAP; and it mounted a secret the admin's account may not read.

Every block make deploy-services can be handed is cut out the way the recipe cuts it, and held to these rules:
  - no --file flag: gcloud builds submit has none, and make build has already built every image;
  - a gcloud builds submit names --config: --tag needs a Dockerfile at the root of the uploaded source, and
    deploy/ has none (cloudbuild.yaml names each service's);
  - every --region is ${REGION...}, every Artifact Registry host ${REGION...}-docker.pkg.dev, and no other region
    is written, except as the default of ${REGION...} or for a location that is not where the services run
    (LOCATIONS, each with its reason);
  - no group: member: IAP and IAM refuse a group that does not exist, and the kit grants IAP to the ADMIN_EMAILS
    addresses one by one;
  - a secret a command mounts is one Terraform lets that command's service account read.
"""
import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
MAKE = (KIT / "Makefile").read_text(encoding="utf-8") + "".join(
    "\n" + p.read_text(encoding="utf-8") for p in sorted((KIT / "mk").glob("*.mk")))
# deploy-services' own extraction, as the recipe spells it ($$ is make's $). deploy_block() below is the same cut.
EXTRACT = "sh -ec \"$$(sed -n '/^# ---- DEPLOY ----/,/^# ---- [A-Z_]* ----$$/p' $$f | grep -v '^# ----')\""
SED = "sed -n '/^# ---- DEPLOY ----/,/^# ---- [A-Z_]* ----$/p' \"$1\" | grep -v '^# ----'"
START, END = re.compile(r"^# ---- DEPLOY ----"), re.compile(r"^# ---- [A-Z_]* ----$")
REGION_NAME = re.compile(r"\b(?:africa|asia|australia|europe|me|northamerica|southamerica|us)-[a-z]+[0-9]+\b")
LOCATIONS = {   # the variables whose value is a region by design, not the services' REGION
    "SPEECH_REGION": "the UI's Speech-to-Text endpoint, {region}-speech.googleapis.com (frontend/voice.py)",
    "ARMOR_LOCATION": "Model Armor's template, kept with the data it inspects (lesson-12.2.sh)",
    "RAG_LOCATION": "serverless RAG Engine corpora, which exist in us-central1 only (the Makefile's RAG_LOCATION)",
}
SECRET_ACCESSOR = "roles/secretmanager.secretAccessor"


def deploy_block(text: str) -> str:
    """What deploy-services hands to sh -ec: sed's range from each DEPLOY marker through the next marker line (sed
    tries the end address from the line after the start), then grep -v dropping every line that starts `# ----`."""
    kept, inside = [], False
    for line in text.splitlines():
        if inside:
            kept.append(line)
            inside = not END.search(line)
        elif START.search(line):
            kept.append(line)
            inside = True
    return "\n".join(line for line in kept if not line.startswith("# ----"))


def commands(block: str) -> list:
    """The block's commands as sh reads them: comment lines dropped, continuation lines joined."""
    code = "\n".join(line for line in block.splitlines() if not line.lstrip().startswith("#"))
    return [line.strip() for line in code.replace("\\\n", " ").splitlines() if line.strip()]


def secret_readers() -> dict:
    """secret id -> the service account ids Terraform lets read it: a grant on the secret, or a project role list that
    holds roles/secretmanager.secretAccessor. Read from the kit's Terraform as text, as terraform fmt writes it."""
    tf = "\n".join(p.read_text(encoding="utf-8") for p in sorted((KIT / "terraform").glob("*.tf")))
    blocks = {(kind, name): body for kind, name, body in
              re.findall(r'^resource "(\w+)" "(\w+)" \{\n(.*?)^\}', tf, re.M | re.S)}
    account = {name: re.search(r'account_id\s*=\s*"([^"]+)"', body).group(1)
               for (kind, name), body in blocks.items() if kind == "google_service_account"}
    listed = re.search(r'variable "secret_names" \{.*?default\s*=\s*\[(.*?)\]', tf, re.S).group(1)
    names = {}
    for (kind, name), body in blocks.items():
        if kind == "google_secret_manager_secret":
            literal = re.search(r'secret_id\s*=\s*"([^"]+)"', body)
            names[name] = [literal.group(1)] if literal else re.findall(r'^\s*"([^"]+)"', listed, re.M)
    readers = {secret: set() for ids in names.values() for secret in ids}
    everywhere = set()
    for (kind, name), body in blocks.items():
        member = re.search(r"google_service_account\.(\w+)\.email", body)
        if not member:
            continue
        who = account[member.group(1)]
        if kind == "google_secret_manager_secret_iam_member" and SECRET_ACCESSOR in body:
            target = re.search(r'secret_id\s*=\s*google_secret_manager_secret\.(\w+)(?:\["([^"]+)"\])?\.id', body)
            if target:
                ids = [target.group(2)] if target.group(2) else names[target.group(1)]
            else:
                ids = names[re.search(r"for_each\s*=\s*google_secret_manager_secret\.(\w+)", body).group(1)]
            for secret in ids:
                readers[secret].add(who)
        elif kind == "google_project_iam_member":
            roles = re.search(r'role\s*=\s*"([^"]+)"', body)
            listing = re.search(r"for_each\s*=\s*toset\(local\.(\w+)\)", body)
            if listing:
                found = re.search(r"^\s*" + listing.group(1) + r"\s*=\s*\[(.*?)^\s*\]", tf, re.M | re.S).group(1)
                roles = re.findall(r'"(roles/[^"]+)"', re.sub(r"(?m)^\s*#.*$", "", found))
            else:
                roles = [roles.group(1)] if roles else []
            if SECRET_ACCESSOR in roles:
                everywhere.add(who)
    return {secret: who | everywhere for secret, who in readers.items()}


class DeployBlockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        listed = re.search(r"^SCRIPTS\s*=\s*((?:.*\\\n)*.*)$", MAKE, re.M).group(1)
        cls.named = list(dict.fromkeys(re.findall(r"commands/[\w.-]+\.sh", listed)
                                       + re.findall(r"\bSCRIPTS=(commands/[\w.-]+\.sh)", MAKE)))
        marked = sorted(p.relative_to(KIT).as_posix() for p in (KIT / "commands").glob("*.sh")
                        if re.search(r"^# ---- DEPLOY ----", p.read_text(encoding="utf-8"), re.M))
        cls.blocks = {name: deploy_block((KIT / name).read_text(encoding="utf-8"))
                      for name in dict.fromkeys(cls.named + marked)}

    def each_command(self):
        for name, block in self.blocks.items():
            for command in commands(block):
                yield name, command

    def test_the_cut_is_deploy_services_own(self):
        self.assertIn(EXTRACT, MAKE, "deploy-services cuts the DEPLOY blocks differently now: change deploy_block() with it")
        self.assertEqual(deploy_block("a\n# ---- DEPLOY ----\nb\n# ---- SMOKE ----\nc\n# ---- DEPLOY ----\nd\n"), "b\nd")

    @unittest.skipUnless(os.name == "posix" and shutil.which("sed") and shutil.which("grep"), "needs a POSIX sed and grep")
    def test_the_cut_matches_sed(self):
        for name in self.blocks:
            cut = subprocess.run(["sh", "-c", SED, "sh", str(KIT / name)], capture_output=True, text=True, encoding="utf-8").stdout
            self.assertEqual(cut.rstrip("\n"), self.blocks[name].rstrip("\n"), name)

    def test_every_script_make_runs_has_a_block(self):
        self.assertIn("commands/lesson-12.3.sh", self.named)
        self.assertIn("commands/gchat.sh", self.named)                  # make deploy-gchat hands it to deploy-services
        for name in self.named:
            self.assertTrue(any(c.startswith("gcloud run deploy ") for c in commands(self.blocks[name])), name)

    def test_no_file_flag(self):
        bad = [f"{name}: {c[:120]}" for name, c in self.each_command() if re.search(r"(?<![\w-])--file\b", c)]
        self.assertEqual(bad, [], "gcloud builds submit has no --file; make build builds every image make up deploys")

    def test_builds_submit_names_its_config(self):
        bad = [f"{name}: {c[:120]}" for name, c in self.each_command() if "builds submit" in c and "--config" not in c]
        self.assertEqual(bad, [], "--tag builds a Dockerfile at the root of the source, and deploy/ has none")

    def test_region_flags_and_registry_hosts_are_REGION(self):
        bad = []
        for name, c in self.each_command():
            bad += [f"{name}: --region {m.group(1)}" for m in re.finditer(r"--region[= ](\S+)", c)
                    if not m.group(1).startswith("${REGION")]
            bad += [f"{name}: {m.group(1)}-docker.pkg.dev" for m in re.finditer(r"([^\s=\"',]*)-docker\.pkg\.dev", c)
                    if not m.group(1).startswith("${REGION")]
        self.assertEqual(bad, [], "make passes REGION, and make build pushes to ${REGION}-docker.pkg.dev")

    def test_no_other_region_written(self):
        bad = []
        for name, c in self.each_command():
            for m in REGION_NAME.finditer(c):
                before = c[:m.start()]
                if before.endswith(("${REGION:-", "${REGION-")):
                    continue                                             # REGION's own fallback; make always passes REGION
                owner = re.search(r"(?:\$\{(\w+):?-|\b(\w+)=)$", before)
                if not (owner and (owner.group(1) or owner.group(2)) in LOCATIONS):
                    bad.append(f"{name}: ...{c[max(0, m.start() - 50):m.end() + 10]}")
        self.assertEqual(bad, [], "a region written where ${REGION} belongs")

    def test_no_group_members(self):
        bad = [f"{name}: {c[:120]}" for name, c in self.each_command() if re.search(r"--member[= ][\"']?group:", c)]
        self.assertEqual(bad, [], "grant IAP and IAM to the ADMIN_EMAILS addresses, one by one")

    def test_mounted_secrets_are_readable(self):
        readers, bad = secret_readers(), []
        for name, c in self.each_command():
            mounts = re.findall(r"--set-secrets[= ]\"?([^\"\s}]+)", c)
            if not mounts:
                continue
            account = re.search(r"--service-account[= ]([\w.-]+)@", c)
            for pair in ",".join(mounts).split(","):
                secret = pair.split("=", 1)[1].split(":", 1)[0]
                if not account or account.group(1) not in readers.get(secret, ()):
                    bad.append(f"{name}: {secret} for {account.group(1) if account else 'no --service-account'}")
        self.assertEqual(bad, [], "Cloud Run refuses to deploy a revision whose account may not read a secret it mounts")


if __name__ == "__main__":
    unittest.main()
