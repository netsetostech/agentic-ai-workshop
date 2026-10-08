"""Lesson 0.3: A blank project, made ready for a plan

A Google Cloud API is off until a project turns it on, and Terraform cannot create a resource whose API is off. make apis turns on the 40 the lane uses, in two calls, because the Service Usage API takes at most twenty at a time. It is safe to run again; an API already on stays on. Terraform keeps its record of what it built, the state, in a bucket, so that the next plan in any shell compares the files with what exists instead of trying to create everything again. Bucket names are global: the first person in the world to create a name owns it. The Makefile's default, documind-tfstate, is one name for the whole world and can serve only one lane, so the setup block named yours after your project, the form the kit's own smoke/preflight.sh uses in its example. It exported TFSTATE_BUCKET and TFSTATE_PREFIX too, so the targets that connect to the state later (make tf-backend, make down) find this one. Versioning keeps every earlier copy of the state file, which is how a damaged state is recovered. The kit includes a keyless pipeline: terraform/wif.tf declares a workload identity pool that lets GitHub Actions workflows from one repository, on one branch, become sa-documind-cicd, the pipeline's account, with no key file anywhere. That account may act as 8 accounts (step 4), which makes this one of the most powerful settings in your project: whoever controls that repository's workflows can deploy code that runs as your services. Lesson 11.1 builds and deploys through this trust. A new project has to name it now, and the kit refuses to guess. Name a repository you own, for instance your fork of netsetos/agents_workshop_learner. Its numeric id is what the trust is really keyed on, because a repository's name can be released and claimed by someone else and its id cannot. prepare then reads your project and its billing account, checks that the project has no GitHub provider the state does not know about, and saves the three values with your project, region and billing account in terraform/runbook-project.auto.tfvars.json, a local file Git ignores. Every later plan reads them from there. IAP signs people in with Google's OAuth, and an OAuth sign-in needs a consent screen with a name on it. Configure it once in the console, under Google Auth Platform > Branding: an app name such as DocuMind and your address as the support e-mail. The kit cannot check this for you, and its preflight says so on its last line. Whether you need more depends on where your project lives: IAP signs people in with Google's OAuth, and an OAuth sign-in needs a consent screen with a name on it. Configure it once in the console, under Google Auth Platform > Branding: an app name such as DocuMind and your address as the support e-mail. The kit cannot check this for you, and its preflight says so on its last line. Whether you need more depends on where your project lives: If it prints organization and the people you will let in belong to that organization, IAP's Google-managed sign-in is enough. If it prints nothing, which is the usual case for a project made with a personal account, Google's IAP guide says you must bring your own OAuth client: IAP's managed client serves only people inside an organization, and a project outside any organization has none. In the console, create one under Google Auth Platform > Clients (or APIs & Services > Credentials), type Web application; once it exists, add the redirect URI https://iap.googleapis.com/v1/oauth/clientIds/CLIENT_ID:handleRedirect with its own client id in place of CLIENT_ID. Set the consent screen's audience to External; while it is in testing, list each address in ADMIN_EMAILS as a test user. Then hand the client to IAP for the whole project: make preflight reads, and creates nothing: the four tools on PATH and Terraform's version, your sign-in, the project and its billing, the state bucket, 22 of the APIs, and the one Python package make roster needs. A line that starts with MISS carries the command that fixes it.

Run order inside this file:
1. 1. The APIs (source window 5)
2. 2. A state bucket of your own (source window 6)
3. 3. The one repository you trust to deploy (source window 9)
4. 4. The sign-in screen IAP will show (source window 11)
5. 4. The sign-in screen IAP will show (source window 12)
6. 5. Ask the kit whether the project is ready (source window 14)

Prerequisites: workshop setup; see this lesson README.
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


# Original CLI workflow for step_01_1_the_apis.
COMMANDS_01 = """make apis PROJECT="$PROJECT"

"""

def step_01_1_the_apis(session):
    """Run 1. The APIs at this checkpoint.

    A Google Cloud API is off until a project turns it on, and Terraform cannot create a resource whose API is off. make apis turns on the 40 the lane uses, in two calls, because the Service Usage API takes at most twenty at a time. It is safe to run again; an API already on stays on.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, once per project.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_2_a_state_bucket_of_your_own.
COMMANDS_02 = """gcloud storage buckets create "gs://$TFSTATE_BUCKET" --project="$PROJECT" --location=asia-south1 --uniform-bucket-level-access
gcloud storage buckets update "gs://$TFSTATE_BUCKET" --versioning
terraform -chdir=terraform init -input=false \\
  -backend-config="bucket=$TFSTATE_BUCKET" -backend-config="prefix=$TFSTATE_PREFIX"

"""

def step_02_2_a_state_bucket_of_your_own(session):
    """Run 2. A state bucket of your own at this checkpoint.

    Terraform keeps its record of what it built, the state, in a bucket, so that the next plan in any shell compares the files with what exists instead of trying to create everything again. Bucket names are global: the first person in the world to create a name owns it. The Makefile's default, documind-tfstate, is one name for the whole world and can serve only one lane, so the setup block named yours after your project, the form the kit's own smoke/preflight.sh uses in its example. It exported TFSTATE_BUCKET and TFSTATE_PREFIX too, so the targets that connect to the state later (make tf-backend, make down) find this one. Versioning keeps every earlier copy of the state file, which is how a damaged state is recovered.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, once per project.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_3_the_one_repository_you_trust_to_deploy.
COMMANDS_03 = """export GH_REPO=YOUR-GITHUB-USER/YOUR-REPO     # a repository you own
export GH_REPO_ID="$(curl -s "https://api.github.com/repos/$GH_REPO" | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
echo "trusting $GH_REPO, id $GH_REPO_ID"    # a private repository: gh api repos/$GH_REPO --jq .id
python commands/infrastructure.py prepare --project "$PROJECT" --region "$REGION" \\
  --github-repository "$GH_REPO" --github-repository-id "$GH_REPO_ID" --deploy-ref refs/heads/main

"""

def step_03_3_the_one_repository_you_trust_to_deploy(session):
    """Run 3. The one repository you trust to deploy at this checkpoint.

    The kit includes a keyless pipeline: terraform/wif.tf declares a workload identity pool that lets GitHub Actions workflows from one repository, on one branch, become sa-documind-cicd, the pipeline's account, with no key file anywhere. That account may act as 8 accounts (step 4), which makes this one of the most powerful settings in your project: whoever controls that repository's workflows can deploy code that runs as your services. Lesson 11.1 builds and deploys through this trust. A new project has to name it now, and the kit refuses to guess. Name a repository you own, for instance your fork of netsetos/agents_workshop_learner. Its numeric id is what the trust is really keyed on, because a repository's name can be released and claimed by someone else and its id cannot. prepare then reads your project and its billing account, checks that the project has no GitHub provider the state does not know about, and saves the three values with your project, region and billing account in terraform/runbook-project.auto.tfvars.json, a local file Git ignores. Every later plan reads them from there.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, once per project (your repository, not the example's).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: PASS: saved confirmed inputs to /home/you/deploy_module_rag/terraform/runbook-project.auto.tfvars.json
    CI trust: YOUR-GITHUB-USER/YOUR-REPO (ID NUMBER) / refs/heads/main
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_4_the_sign_in_screen_iap_will_show.
COMMANDS_04 = """gcloud projects describe "$PROJECT" --format='value(parent.type,parent.id)'   # empty: no organization

"""

def step_04_4_the_sign_in_screen_iap_will_show(session):
    """Run 4. The sign-in screen IAP will show at this checkpoint.

    IAP signs people in with Google's OAuth, and an OAuth sign-in needs a consent screen with a name on it. Configure it once in the console, under Google Auth Platform > Branding: an app name such as DocuMind and your address as the support e-mail. The kit cannot check this for you, and its preflight says so on its last line. Whether you need more depends on where your project lives:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell: is your project inside an organization?.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

# Original CLI workflow for step_05_4_the_sign_in_screen_iap_will_show.
COMMANDS_05 = """cat > "$HOME/iap-oauth.yaml" <<'EOF'
accessSettings:
  oauthSettings:
    clientId: CLIENT_ID
    clientSecret: CLIENT_SECRET
EOF
# edit the two values in $HOME/iap-oauth.yaml first; the file holds a secret, so it never goes in the kit's folder
gcloud iap settings set "$HOME/iap-oauth.yaml" --project="$PROJECT" && rm "$HOME/iap-oauth.yaml"

"""

def step_05_4_the_sign_in_screen_iap_will_show(session):
    """Run 4. The sign-in screen IAP will show at this checkpoint.

    IAP signs people in with Google's OAuth, and an OAuth sign-in needs a consent screen with a name on it. Configure it once in the console, under Google Auth Platform > Branding: an app name such as DocuMind and your address as the support e-mail. The kit cannot check this for you, and its preflight says so on its last line. Whether you need more depends on where your project lives: If it prints organization and the people you will let in belong to that organization, IAP's Google-managed sign-in is enough. If it prints nothing, which is the usual case for a project made with a personal account, Google's IAP guide says you must bring your own OAuth client: IAP's managed client serves only people inside an organization, and a project outside any organization has none. In the console, create one under Google Auth Platform > Clients (or APIs & Services > Credentials), type Web application; once it exists, add the redirect URI https://iap.googleapis.com/v1/oauth/clientIds/CLIENT_ID:handleRedirect with its own client id in place of CLIENT_ID. Set the consent screen's audience to External; while it is in testing, list each address in ADMIN_EMAILS as a test user. Then hand the client to IAP for the whole project:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, only for a project with no organization.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_05)

# Original CLI workflow for step_06_5_ask_the_kit_whether_the_project_is_ready.
COMMANDS_06 = """make preflight PROJECT="$PROJECT" TFSTATE_BUCKET="$TFSTATE_BUCKET" REGION="$REGION"

"""

def step_06_5_ask_the_kit_whether_the_project_is_ready(session):
    """Run 5. Ask the kit whether the project is ready at this checkpoint.

    make preflight reads, and creates nothing: the four tools on PATH and Terraform's version, your sign-in, the project and its billing, the state bucket, 22 of the APIs, and the one Python package make roster needs. A line that starts with MISS carries the command that fixes it.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ok    gcloud on PATH
      ok    terraform on PATH
      ok    make on PATH
      ok    python on PATH
      ok    terraform VERSION (backend.tf wants >= 1.9)
      ok    signed in as you@example.com
      ok    project documind-ai-YOUR-ID exists
      ok    billing linked
      ok    state bucket gs://documind-ai-YOUR-ID-tfstate
      ok    APIs enabled
      ok    google-cloud-firestore for make roster

    preflight clean - next: make plan, then make up
    not checkable from here: the OAuth consent screen (Google Auth Platform > Branding) - IAP needs it
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_06)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_5', step_01_1_the_apis),
        ('source_6', step_02_2_a_state_bucket_of_your_own),
        ('source_9', step_03_3_the_one_repository_you_trust_to_deploy),
        ('source_11', step_04_4_the_sign_in_screen_iap_will_show),
        ('source_12', step_05_4_the_sign_in_screen_iap_will_show),
        ('source_14', step_06_5_ask_the_kit_whether_the_project_is_ready),
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
