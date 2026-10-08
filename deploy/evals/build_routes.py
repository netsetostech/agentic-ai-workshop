# -*- coding: utf-8 -*-
"""Build routes.jsonl's 207 relabelled dev rows - the DocuMind Desk's route set (workshop lessons 5.6 and 10.4).

    python deploy/evals/build_routes.py            # rewrite the derived rows, keep every hand-written row
    python deploy/evals/build_routes.py --check    # exit 1 when a golden row has no label, a row is malformed, or
                                                   # routes.jsonl is not what this script builds

Every question that already existed gets a route before anything routes: measure before building. The rows come from
three files and are dev only, because they were all seen while the rules were written - a test row is new text that
its writer wrote without seeing the rules:

    65   golden.jsonl         the question, tenant, must_contain and must_not_contain as they are; the label below
    42   paraphrases.jsonl    a "same" paraphrase takes its golden row's label and figures; the others are labelled
    100  sft/documind_sft_v1.chat.jsonl
                              first-person rewrites of SFT user turns. The route follows the class of the passage
                              the turn was generated from (policy: handbook; statute or guidance: statute), and the
                              group is the passage, so a turn and its refusal twin sit on one side of any split. The
                              turn's answerable flag judged ONE served passage, not the tenant's corpus the desk
                              searches, so it is only the starting outcome: REWRITE_OUTCOMES overrides it wherever
                              the corpus answers a refusal twin elsewhere, or the passage is handbook filler

Hand-written rows (source "new") are kept as they are and validated, against the schema and the same labelling rule.

THE LABELLING RULE (workshop lesson 10.4) is code here (rule_route), and --check holds every row to it: a first-person
question with no authority marker ("Can I carry forward leave?") is handbook; "under the Act / Code / law", or a named
Act or Code, is statute. A question with both markers is two parts, and "both" means the employee handbook named
beside an authority ("Does our handbook match the OSH Code?"): such a row is labelled handbook or statute and passes
only when its acceptable_routes holds both. A first-person question that names an Act ("Under the CGST Act, how long
do I have to appeal?") is statute; every statute rewrite below depends on that reading. Golden
lk-03 and paraphrase pp-04 are handbook under the rule. A row the rule mislabels - a statute question with no marker,
such as "We had a personal-data breach. By when must we tell the Board?", which rule_route() calls handbook - goes in
RULE_EXCEPTIONS with the reviewer's reason, never past the check silently.

A PARTIAL ANSWER is a grounded refusal: a question that asks for a figure the corpus does not state is labelled
grounded_refusal, even when the desk can cite the clause that says how the figure is fixed or what bounds it (pp-32,
pp-38, sft-22, sft-55). Outcome accuracy compares outcomes exactly, so twins must not split on this.

WHAT LAUNCHES decides three labels. Contract, invoice, report and transcript questions are out_of_scope ("no_desk"):
no desk answers them at launch. globex runs single mode on statute, so every question it sends past the gate goes to
the statute desk, which refuses what globex's two Acts do not hold.

WHO WROTE WHAT. Every label and every first-person rewrite here is a model draft (author "model-draft"). A person
reviews each row before the gate is tuned on them; the reviewer's handle goes in REVIEWED and the row's author becomes
"model-draft, reviewed by <handle>". Nothing here is marked as written by a person.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from route_eval import FIELDS, ROUTES_FILE, check_rows, normalise, row_errors  # noqa: E402
from run_eval import contains  # noqa: E402

GOLDEN = os.path.join(HERE, "golden.jsonl")
PARAPHRASES = os.path.join(HERE, "paraphrases.jsonl")
SFT = os.path.join(HERE, "sft", "documind_sft_v1.chat.jsonl")
SFT_REL = "sft/documind_sft_v1.chat.jsonl"
MANIFEST = os.path.join(HERE, "manifest.json")
CORPUS = os.path.join(HERE, "corpus")

DOC_TYPES = {"handbook": ["policy"], "statute": ["statute", "guidance"]}   # what each answer desk may cite
SINGLE = {"globex": "statute"}          # globex runs single mode: the statute desk, no router
DESK_OF_CLASS = {"policy": "handbook", "statute": "statute", "guidance": "statute"}
AUTHOR = "model-draft"
REVIEWED: dict[str, str] = {}           # row id -> the handle of the person who reviewed it
# Row id -> why the labelling rule does not decide it, as a reviewer recorded it. Empty: every row here obeys it.
RULE_EXCEPTIONS: dict[str, str] = {}

# The rule's markers. Case-sensitive "Act" and "Code" so that "SAC code" is not an authority, and a company's "Code of
# Conduct" is not one either; "Schedule I" or "Part I" is a numeral, not the first person.
FIRST_PERSON = re.compile(r"(?<!Schedule )(?<!Chapter )(?<!Part )\b(?:I|I'm|I've|I'd|I'll)(?![\w'])"
                          r"|\b(?:[Mm]e|[Mm]y|[Mm]ine|[Ww]e|[Oo]ur|us)\b")
AUTHORITY = re.compile(r"\b(?:[A-Z][\w.-]*\s+)+(?:Act|Code(?! of Conduct)|Codes)\b|\bCode on [A-Z]"
                       r"|\b(?:the|this) (?:Act|Code(?! of Conduct))\b"
                       r"|\b(?:the|by|under) law\b|\blegally\b")
# The employee handbook by name; "the ministry's compliance handbook" is guidance, not this.
HANDBOOK = re.compile(r"\b(?:the|our|my|ACME's|Zeta's) (?:employee )?handbook\b|\b(?:our|company|ACME's) polic(?:y|ies)\b",
                      re.I)

NO_DESK = "no_desk: no desk answers {} questions at launch, so they are out_of_scope"
SINGLE_NOTE = ("globex runs single mode on statute: the statute desk refuses what the DPDP and IT Acts do not hold "
               "and never shows another tenant's text; not_covered is for a routed tenant with no documents for "
               "the desk")

# golden id -> (route, outcome, note). The doc types follow the route; must_contain is golden's on an answer row.
LABELS = {
    "lk-01": ("handbook", "answer", ""),
    "lk-02": ("handbook", "answer", "PR-05"),
    "lk-03": ("handbook", "answer", "first person, no authority marker: handbook (the labelling rule)"),
    "lk-04": ("handbook", "answer", ""),
    "lk-05": ("handbook", "answer", ""),
    "lk-06": ("handbook", "answer", ""),
    "lk-07": ("handbook", "answer", "LV-01; the OSH Code's own accrual rule is lk-25, which names the Code"),
    "lk-08": ("handbook", "answer", ""),
    "lk-09": ("handbook", "answer", ""),
    "lk-10": ("out_of_scope", "oos", NO_DESK.format("invoice")),
    "lk-11": ("out_of_scope", "oos", NO_DESK.format("annual report")),
    "lk-12": ("out_of_scope", "oos", NO_DESK.format("contract")),
    "lk-13": ("out_of_scope", "oos", NO_DESK.format("contract")),
    "jn-01": ("handbook", "answer", ""),
    "jn-02": ("handbook", "answer", ""),
    "jn-03": ("handbook", "answer", "a figure: the handbook desk's agent mode with a calculator"),
    "jn-04": ("statute", "grounded_refusal", SINGLE_NOTE + "; the MSAs are contracts, outside the statute desk"),
    "jn-05": ("out_of_scope", "oos", NO_DESK.format("invoice")),
    "jn-06": ("out_of_scope", "oos", NO_DESK.format("annual report")),
    "jn-07": ("handbook", "answer", "IT-SEC-04: no exception for contractors"),
    "rf-01": ("handbook", "grounded_refusal", "no sabbatical clause: its own desk refuses with grounding"),
    "rf-02": ("handbook", "grounded_refusal", "no casual leave clause; never re-routed to the OSH Code"),
    "rf-03": ("statute", "grounded_refusal", SINGLE_NOTE),
    "rf-04": ("out_of_scope", "oos", NO_DESK.format("annual report")),
    "rf-05": ("out_of_scope", "oos", NO_DESK.format("company information") + "; golden keeps rf-05 unanswerable"),
    "iso-01": ("handbook", "answer", "zeta's own EXP-12"),
    "iso-02": ("statute", "grounded_refusal", SINGLE_NOTE),
    "iso-03": ("statute", "grounded_refusal", SINGLE_NOTE),
    "iso-04": ("out_of_scope", "oos", NO_DESK.format("annual report")),
    "iso-05": ("out_of_scope", "oos", NO_DESK.format("invoice")),
    "lk-14": ("statute", "answer", ""),
    "lk-15": ("statute", "answer", ""),
    "lk-16": ("statute", "answer", ""),
    "lk-17": ("statute", "answer", ""),
    "lk-18": ("statute", "answer", ""),
    "lk-19": ("statute", "answer", ""),
    "lk-20": ("statute", "answer", ""),
    "lk-21": ("statute", "answer", ""),
    "jn-08": ("statute", "answer", ""),
    "jn-09": ("statute", "answer", ""),
    "rf-06": ("statute", "grounded_refusal", "the Maternity Benefit Act has no paternity leave"),
    "iso-06": ("statute", "grounded_refusal", SINGLE_NOTE),
    "iso-07": ("statute", "grounded_refusal", SINGLE_NOTE),
    "lk-22": ("statute", "answer", ""),
    "lk-23": ("statute", "answer", ""),
    "lk-24": ("statute", "answer", ""),
    "lk-25": ("statute", "answer", ""),
    "lk-26": ("statute", "answer", ""),
    "lk-27": ("statute", "answer", "public-law GST is the statute desk's"),
    "lk-28": ("statute", "answer", "globex holds the DPDP Act"),
    "lk-29": ("statute", "answer", ""),
    "lk-30": ("statute", "answer", ""),
    "lk-31": ("statute", "answer", "the Code on Social Security, zeta's copy"),
    "jn-10": ("statute", "answer", ""),
    "jn-11": ("statute", "answer", "the ministry's compliance handbook is guidance, in the statute desk's doc types"),
    "rf-07": ("out_of_scope", "oos", NO_DESK.format("invoice")),
    "iso-08": ("statute", "grounded_refusal", "zeta holds the four Codes and the ministry handbook, not the CGST Act"),
    "iso-09": ("statute", "grounded_refusal", "zeta holds no DPDP Act"),
    "iso-10": ("statute", "grounded_refusal", SINGLE_NOTE),
    "mm-01": ("out_of_scope", "oos", NO_DESK.format("annual report")),
    "mm-02": ("statute", "answer", "the page image takes its Act's class: a media object takes its parent document's"),
    "mm-03": ("out_of_scope", "oos", NO_DESK.format("town hall")),
    "mm-04": ("out_of_scope", "oos", NO_DESK.format("town hall")),
    "mm-05": ("out_of_scope", "oos", NO_DESK.format("annual report")),
    "vr-01": ("handbook", "answer", ""),
}

UNANSWERED = "a question the corpus cannot answer: its own desk refuses with grounding, never out_of_scope"

# A paraphrase whose answer differs from its golden row's ("same": false): (route, outcome, must_contain, note).
# Every must_contain value is checked against the tenant's corpus by --check.
PARAPHRASE_LABELS = {
    "pp-25": ("handbook", "grounded_refusal", [], "NP-03 covers a confirmed E3 and above, PB-02 probation; "
                                                  "nothing states a confirmed E2's notice"),
    "pp-26": ("handbook", "answer", ["15"], "PB-02"),
    "pp-27": ("handbook", "answer", [], "NP-03 answers for a confirmed E3 and above, conditionally"),
    "pp-28": ("handbook", "grounded_refusal", [], UNANSWERED),
    "pp-29": ("handbook", "grounded_refusal", [], "PR-05 names Form 16 only"),
    "pp-30": ("handbook", "grounded_refusal", [], UNANSWERED),
    "pp-31": ("handbook", "answer", ["function head"], "FIN-02"),
    "pp-32": ("handbook", "grounded_refusal", [], "WFH-01 caps remote days; no office minimum is stated, and the "
                                                  "refusal cites WFH-01 to say so (the partial-answer rule)"),
    "pp-33": ("out_of_scope", "oos", [], NO_DESK.format("contract")),
    "pp-34": ("out_of_scope", "oos", [], NO_DESK.format("contract")),
    "pp-35": ("statute", "answer", ["twelve weeks"], "the principal Act"),
    "pp-36": ("statute", "grounded_refusal", [], "the corpus names the Pension Scheme but no qualifying service"),
    "pp-37": ("statute", "answer", ["twenty per cent"], ""),
    "pp-38": ("statute", "grounded_refusal", [], "the Code says how a minimum rate is fixed, not a figure (the "
                                                 "partial-answer rule)"),
    "pp-39": ("statute", "answer", ["eight months"], "the Code on Wages' bonus chapter"),
    "pp-40": ("statute", "grounded_refusal", [], "the OSH Code has no sick leave"),
    "pp-41": ("statute", "answer", ["purpose and means"], ""),
    "pp-42": ("handbook", "answer", ["60"], "NP-03 and LV-07"),
}
# A labelled paraphrase that asks about another tenant's document keeps a guard, as the golden isolation rows do: the
# other tenant's figure, which the answer must never carry. --check confirms the asking tenant's corpus lacks it and
# another tenant's holds it.
PARAPHRASE_GUARDS = {"pp-34": ["99.5"]}     # zeta asks about ACME's MSA; MSA-09 there is 99.5%

# SFT line (1-based, in documind_sft_v1.chat.jsonl) -> the question rewritten in the first person. Statute rewrites
# name their instrument, handbook rewrites name no authority, and none describes a disclosure, a dispute or a
# request for a person: these are non-escalation rows. Model drafts, every one: a person reviews them.
REWRITES = {
    # The CGST Act (20)
    2: "I keep the GST records for my team. Under the CGST Act, how long may an officer hold on to books or "
       "documents seized in a search?",
    8: "I'm helping plan a payment of tax arrears: under the CGST Act, up to how many monthly instalments can the "
       "Commissioner allow?",
    14: "If I disagree with an adjudicating authority's GST order, how long does the CGST Act give me to appeal to "
        "the Appellate Authority?",
    17: "I collect old coins. Does currency held for its numismatic value count as money under the CGST Act?",
    19: "We have received a notice of appeal from the department. Under the CGST Act, within how many days can we "
        "file a memorandum of cross-objections?",
    21: "If we take a GST matter to the High Court, do we still have to pay the sums due to the Government under "
        "the CGST Act?",
    22: "Under the CGST Act, what monetary limits has the Board fixed for central tax officers to file appeals? I "
        "need the exact amounts.",
    26: "I'd like to understand the CGST Act: are most offences under it cognizable or non-cognizable?",
    43: "I supply some services under the composition scheme. Under Section 10 of the CGST Act, how much of my "
        "turnover can those services be?",
    44: "Under Section 10 of the CGST Act, what penalty would I face if my service supplies crossed the prescribed "
        "limit?",
    49: "Under the CGST Act, what is the highest turnover in the preceding financial year at which we can opt for "
        "the composition levy?",
    53: "For a vendor check I'm doing: under the CGST Act, what share of the voting stock of two entities makes "
        "them related persons?",
    54: "Our goods on one invoice are arriving in several lots. Under the CGST Act, when can I claim the input tax "
        "credit?",
    55: "Under the CGST Act, what interest rate applies if we don't pay a supplier within 180 days? I want the "
        "exact rate.",
    59: "I grow vegetables on family land and sell the produce. Does Section 23 of the CGST Act exempt me from "
        "registration?",
    62: "My GST registration was cancelled by the officer on his own motion. Under the CGST Act, within what time "
        "can I apply to revoke the cancellation?",
    63: "When I receive an advance payment for a service, what document does the CGST Act say I must issue?",
    64: "I issued a tax invoice that charged less tax than was payable. What does the CGST Act require me to do?",
    72: "I deduct tax at source on my company's payments. Under the CGST Act, by when must I pay it to the "
        "Government?",
    74: "I paid some GST that I think should come back to me. Under the CGST Act, how long do I have to apply for "
        "a refund?",
    # The Code on Social Security (16)
    79: "I work across several states. Does the Code on Social Security, 2020 apply to the whole of India?",
    83: "Who decides the interest rate on my Provident Fund under the Code on Social Security?",
    87: "I've been asked to join a State Unorganised Workers' Board. Under the Code on Social Security, how long "
        "is its term?",
    88: "Under the Code on Social Security, how many members at most can a State Unorganised Workers' Board have? "
        "I could not find the number.",
    92: "I'm employed through a contractor. Under the Code on Social Security, can the contractor recover my "
        "contribution from my wages?",
    100: "If I want to take a matter to the Employees' Insurance Court, what limitation period does the Code on "
         "Social Security give me?",
    101: "I'm not in a seasonal job. Under the Code on Social Security, how many days must I work in twelve months "
         "to count as one year of continuous service?",
    103: "If I miss the deadline for my maternity benefit notice, do I lose the benefit under the Code on Social "
         "Security?",
    106: "If I'm hurt at work, what details must my notice of injury to the employer contain under the Code on "
         "Social Security?",
    108: "If I'm employed through a contractor and get hurt doing the principal employer's work, does the Code on "
         "Social Security make that employer liable for compensation?",
    114: "We installed a computer unit in our office building. Does that make it a factory under the Code on "
         "Social Security?",
    117: "If an ex parte order is passed against our company, how long does the Code on Social Security give us to "
         "apply to set it aside?",
    118: "What fee do we pay to apply to set aside an ex parte order under the Code on Social Security?",
    120: "I deliver food through an app. How does the Code on Social Security define a gig worker?",
    124: "I read that contributions can be deferred. Under the Code on Social Security, for how long at a time can "
         "the Central Government defer or reduce them?",
    125: "I'm hiring interns. Up to what age is someone a minor under the Code on Social Security?",
    # The Code on Wages (6)
    131: "I'm moving to our Pune office. Does the Code on Wages, 2019 apply across the whole of India?",
    132: "If I damage company equipment, how much can my employer deduct from my wages under the Code on Wages?",
    138: "I'm preparing a compliance summary. Which courts can try offences under the Code on Wages?",
    140: "Under the Code on Wages, what penalty does the actual offender face once the employer proves its own "
         "innocence? I need the exact penalty.",
    143: "I'd like to understand my pay structure: what can a minimum rate of wages consist of under the Code on "
         "Wages?",
    144: "My wages are paid monthly. What is the longest wage period the Code on Wages allows?",
    # The DPDP Act (4)
    145: "Our team sends customer data abroad for processing. Under the DPDP Act, how can the Central Government "
         "restrict such transfers?",
    147: "If I appeal to the Appellate Tribunal under the DPDP Act, how quickly should it dispose of my appeal?",
    148: "If the DPDP Act conflicts with another law we follow, which one prevails?",
    150: "What penalties could we face for non-compliance with the DPDP Act? I need the amounts.",
    # The ACME handbook (14): its GEN sections and what they leave out
    153: "If I send the People team a question about my shift roster, how soon will they answer?",
    155: "I have a question about incident reporting. How quickly will the People team get back to me?",
    157: "If I ask the People team about the health insurance policy, how long will they take to reply?",
    159: "I want to ask about statutory holidays. What response time should I expect from the People team?",
    161: "What happens to me if I don't follow the shift roster rules?",
    166: "Does the business conduct section apply to me as a contractor working on ACME systems?",
    167: "My project has a signed statement of work. If it conflicts with GEN-067, which one do I follow?",
    172: "How often will my performance be reviewed at ACME?",
    183: "How many statutory holidays do I get each year?",
    190: "When I raise a query about statutory holidays, what should I mention so it reaches the right place?",
    194: "What exact steps do I follow to submit an incident report?",
    199: "If my signed statement of work conflicts with the handbook's attendance and shift roster section, which "
         "one governs my engagement?",
    205: "What address do I write to for the People team?",
    209: "I sent the People team a question about incident reporting. What turnaround should I expect?",
    # The Industrial Relations Code (10)
    211: "I want to start a trade union where I work. Under the Industrial Relations Code, how many members must "
         "apply for registration?",
    213: "Our union was recognised as the negotiating union. Under the Industrial Relations Code, how long is that "
         "recognition valid?",
    218: "I'm drafting our HR process. If a worker is suspended pending an inquiry, how long does the Industrial "
         "Relations Code usually give the employer to complete it?",
    222: "I'm tracking an award for my team. When does an award under the Industrial Relations Code become "
         "enforceable once it is communicated?",
    223: "How long after its period of operation ends does an award stay binding on us under the Industrial "
         "Relations Code?",
    225: "If I'm laid off, how much compensation does the Industrial Relations Code provide for?",
    227: "Under section 75 of the Industrial Relations Code, how many days' notice must we give before closing down "
         "an undertaking?",
    229: "If our retrenchment matter is referred to a Tribunal, how soon must it pass an award under the Industrial "
         "Relations Code?",
    236: "There is a legal strike at our plant. Under the Industrial Relations Code, can my employer hire new "
         "workers during it?",
    239: "Our office has about 25 workers. From how many workers does the Industrial Relations Code require a "
         "Grievance Redressal Committee?",
    # The IT Act (6)
    241: "I manage our signing certificates. Under the IT Act, what must a Certifying Authority do about hardware "
         "and software security?",
    242: "Before my Digital Signature Certificate is revoked, does the IT Act give me a hearing?",
    245: "If a penalty imposed on me under the IT Act goes unpaid, how is it recovered?",
    248: "I'm writing a note on Section 86 of the IT Act. What procedure must Parliament follow once an order is "
         "laid before each House?",
    251: "For a training I'm preparing: how can the contents of electronic records be proved under the IT Act?",
    253: "I'm updating our IT guidelines. How does the IT Act define a computer resource?",
    # The ministry's compliance handbook, guidance (3)
    256: "Our new site is under construction. Under the OSH Code, as the ministry's compliance handbook explains it, "
         "when must an ambulance room be provided?",
    259: "If there is an accident at my workplace, how quickly must my employer report it under the Labour Codes?",
    261: "I'm planning to resign next month. Under the Labour Codes, how soon after I leave must my wages be paid?",
    # The Maternity Benefit Act (2)
    262: "My contract has terms on maternity leave. Does the Maternity Benefit Act override a contract of service "
         "that conflicts with it?",
    264: "I'm expecting a baby. What is the earliest date I can give in my notice under the Maternity Benefit Act?",
    # The OSH Code (12)
    268: "I want to report an accident properly: what counts as a serious bodily injury under the OSH Code?",
    269: "We closed one of our establishments and told the registering officer. Under the OSH Code, what happens "
         "if the certificate is not cancelled within sixty days?",
    274: "Our office has no creche yet. Under the OSH Code, when may the Central Government make rules requiring "
         "one?",
    276: "Under the OSH Code, what penalty does an Inspector-cum-Facilitator face for failing in their duties? I "
         "need the specific provision.",
    277: "An Inspector-cum-Facilitator issued an order at our site. Under the OSH Code, how long does it stay in "
         "force unless extended?",
    279: "I'm joining as a factory medical officer. What must I do before taking office under the OSH Code?",
    281: "If I file an appeal with the appellate authority, how soon must it be decided under the OSH Code?",
    282: "I'm hiring audio-visual workers for a shoot. What does the OSH Code require about the agreement?",
    288: "As an employer, what penalty would we face for contravening the OSH Code?",
    300: "During an epidemic, what rule-making power does the OSH Code give the Central Government over our "
         "workplace?",
    301: "I'm moving to another state for work. What wage limit decides whether I'm an inter-State migrant worker "
         "under the OSH Code?",
    302: "We're renovating our site. When does the OSH Code require suitable and sufficient scaffolding?",
    # The Payment of Bonus Act (4)
    304: "Our company keeps one set of accounts for all its branches. Under the Payment of Bonus Act, how must my "
         "bonus be paid?",
    306: "I'm reviewing our bonus compliance. What is the maximum penalty for contravening the Payment of Bonus "
         "Act?",
    307: "My offer letter has a bonus clause. Does the Payment of Bonus Act override an agreement that conflicts "
         "with it?",
    312: "I'm checking our bonus calculation. Under Section 6 of the Payment of Bonus Act, what sums can be "
         "deducted from gross profits as prior charges?",
    # The Payment of Gratuity Act (3)
    313: "I'm estimating my gratuity. What counts as wages under the Payment of Gratuity Act?",
    314: "Where must my employer insure its gratuity liability under the Payment of Gratuity Act?",
    317: "Under Section 8 of the Payment of Gratuity Act, what is the penalty if I refuse to produce documents to an "
         "Inspector?",
}


# A rewrite keeps its turn's subject: it shares at least one content word with the SFT question, or it is keyed to
# the wrong line. A tripwire for a misnumbered entry, not a judge of the rewrite - the reviewer is that.
STOPWORDS = set("what which when where does under with that this from have must their they there about after before "
                "into than then them your will would could should shall being been were also only once each such "
                "other".split())


def content_words(text: str) -> set[str]:
    return set(re.findall(r"[a-z][a-z-]{3,}", text.lower())) - STOPWORDS


# Rewrites that sit near a case class's topic and ask only what the law says: the hard gate must not fire on them.
NEAR_MISS = {239: "grievance: it names the Grievance Redressal Committee and asks an establishment threshold",
             261: "exit_dues: a leaver's wages, asked before leaving, with nothing late"}

# SFT line -> (outcome, must_contain, must_not_contain, note): the outcome judged against the tenant's whole corpus,
# where the turn's answerable flag judged one passage. --check requires an entry for every refusal twin and every
# handbook rewrite, and finds each must_contain value in acme's corpus. Model judgements: the reviewer confirms each.
FILLER = "GEN-{} is generated filler that states no rule, so the handbook desk refuses with grounding"
SLA = ("the People team's reply time is a tenant setting, never the GEN filler's 'five working days', which a desk "
       "never quotes as a rule")
REWRITE_OUTCOMES = {
    # Refusal twins the corpus does answer, outside the passage they were generated from
    44: ("answer", [], [], "s.10(5): a person who paid composition tax while not eligible is liable to a penalty, "
                           "determined under s.73 or s.74"),
    88: ("answer", [], [], "s.6(10) lists the State Board: a Chairperson, a Vice-Chairperson, one Central Government "
                           "member, thirty-one nominated members and a Member-Secretary"),
    140: ("answer", [], [], "s.63: the actual offender is liable to the like punishment as if he were the employer"),
    150: ("answer", ["two hundred and fifty crore"], [], "the Schedule lists a penalty per breach, the highest "
                                                         "two hundred and fifty crore rupees"),
    227: ("answer", ["sixty days"], [], "s.74(1), not s.75: sixty days' notice before a closure; s.80 asks a larger "
                                        "establishment for permission ninety days ahead"),
    # Refusal twins the corpus does not answer
    22: ("grounded_refusal", [], [], "s.120(1): the Board fixes the limits by its own orders, which the corpus "
                                     "does not hold"),
    55: ("grounded_refusal", [], [], "s.16(2) adds interest as prescribed and s.50 caps the rate at eighteen per cent "
                                     "as notified; no exact rate is in the corpus"),
    118: ("grounded_refusal", [], [], "s.125(6) gives three months to apply and names no fee"),
    248: ("grounded_refusal", [], [], "s.86(2) says only that the order is laid before each House"),
    276: ("grounded_refusal", [], [], "nothing punishes a failure of duty; s.100 punishes an unlawful disclosure only"),
    317: ("grounded_refusal", [], [], "s.8 is the recovery of gratuity; s.7A(2) binds a person to produce documents "
                                     "within IPC ss.175 and 176, whose penalties the corpus does not hold, and s.9(2) "
                                     "punishes an employer's default in general"),
    # The ACME handbook's GEN sections
    153: ("grounded_refusal", [], ["five working days"], SLA),
    155: ("grounded_refusal", [], ["five working days"], SLA),
    157: ("grounded_refusal", [], ["five working days"], SLA),
    159: ("grounded_refusal", [], ["five working days"], SLA),
    209: ("grounded_refusal", [], ["five working days"], SLA),
    161: ("grounded_refusal", [], [], FILLER.format("036")),
    166: ("grounded_refusal", [], [], FILLER.format("062") + ": its scope line is not a rule"),
    167: ("grounded_refusal", [], [], FILLER.format("067") + ": its statement-of-work line is not a rule"),
    172: ("grounded_refusal", [], [], FILLER.format("088")),
    183: ("grounded_refusal", [], [], FILLER.format("139")),
    190: ("grounded_refusal", [], [], FILLER.format("175") + ", and no routing key is taken from it"),
    194: ("grounded_refusal", [], [], FILLER.format("191")),
    199: ("grounded_refusal", [], [], FILLER.format("216") + ": its statement-of-work line is not a rule"),
    205: ("grounded_refusal", [], [], FILLER.format("242") + "; no address is given"),
}


def rule_route(question: str) -> str | None:
    """The labelling rule: an authority marker is statute, unless the handbook is named too (two parts); a
    first-person question with no authority marker is handbook; anything else the rule does not decide."""
    if AUTHORITY.search(question):
        return "two_parts" if HANDBOOK.search(question) else "statute"
    if FIRST_PERSON.search(question):
        return "handbook"
    return None


def _jsonl(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def corpus_text(tenant: str) -> str:
    d = os.path.join(CORPUS, tenant)
    return "\n".join(_read(os.path.join(d, fn)) for fn in sorted(os.listdir(d))
                     if fn.endswith((".md", ".txt")))


def sft_turns() -> dict[int, dict]:
    """{line: {question, passage, answerable}} from the chat file: the prompt the generator served, one passage."""
    out = {}
    with open(SFT, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            msgs = json.loads(line)["messages"]
            user = msgs[1]["content"]
            passage = user.split("\n\nContext:\n", 1)[1].rsplit("\n\nQuestion:", 1)[0]
            out[n] = {"question": user.rsplit("\n\nQuestion:", 1)[1].strip(),
                      "passage": re.sub(r"^\[Source 1\] ", "", passage),
                      "answerable": bool(json.loads(msgs[2]["content"])["answerable"])}
    return out


def passage_document(passage: str, mirrors: dict[str, str]) -> str:
    """The one acme text mirror that holds this passage's opening. More or fewer is an error, never a guess."""
    head = _flat(passage)[:200]
    hits = [slug for slug, text in mirrors.items() if head in text]
    if len(hits) != 1:
        raise SystemExit(f"an SFT passage matches {len(hits)} documents ({hits}): {head[:80]!r}")
    return hits[0]


def row(rid, of, group, tenant, question, route, outcome, must_contain, must_not_contain, source, note) -> dict:
    author = f"{AUTHOR}, reviewed by {REVIEWED[rid]}" if rid in REVIEWED else AUTHOR
    return {"id": rid, "of": of, "group": group, "tenant": tenant, "identity": f"{tenant}_employee",
            "question": question, "prev_question": None, "prev_route": None, "expected_route": route,
            "acceptable_routes": [route], "expected_doc_types": list(DOC_TYPES.get(route, [])) if outcome in
            ("answer", "grounded_refusal") else [], "expected_outcome": outcome, "case_type": None,
            "must_escalate": False, "language": "en", "expect_model_calls_max": None,
            "must_contain": list(must_contain) if outcome == "answer" else [],
            "must_not_contain": list(must_not_contain), "source": source, "split": "dev", "author": author,
            "note": note}


def build() -> tuple[list[dict], list[str]]:
    """(the derived rows in file order, every reason they cannot be trusted)."""
    why = []
    golden, paraphrases = _jsonl(GOLDEN), _jsonl(PARAPHRASES)
    by_id = {g["id"]: g for g in golden}
    rows = []
    why += [f"golden {g['id']} has no route label in build_routes.LABELS" for g in golden if g["id"] not in LABELS]
    why += [f"LABELS names {i}, which golden.jsonl does not have" for i in LABELS if i not in by_id]
    why += [f"PARAPHRASE_GUARDS names {i}, which PARAPHRASE_LABELS does not" for i in PARAPHRASE_GUARDS
            if i not in PARAPHRASE_LABELS]
    for g in golden:
        if g["id"] not in LABELS:
            continue
        route, outcome, note = LABELS[g["id"]]
        rows.append(row(g["id"], None, g["id"], g["tenant"], g["question"], route, outcome, g["must_contain"],
                        g.get("must_not_contain", []), f"golden.jsonl:{g['id']}", note))
    labelled = {r["id"]: r for r in rows}
    for p in paraphrases:
        parent = labelled.get(p["of"])
        if p["id"] in PARAPHRASE_LABELS:
            route, outcome, want, note = PARAPHRASE_LABELS[p["id"]]
            nots = PARAPHRASE_GUARDS.get(p["id"], [])
        elif p.get("same") and parent and parent["tenant"] == p["tenant"]:
            route, outcome, want, nots = (parent["expected_route"], parent["expected_outcome"],
                                          parent["must_contain"], parent["must_not_contain"])
            note = f"same answer as {p['of']}"
        else:
            why.append(f"paraphrase {p['id']} has no route label (not a same-tenant 'same' paraphrase of a "
                       f"labelled row, and not in PARAPHRASE_LABELS)")
            continue
        rows.append(row(p["id"], p["of"], p["of"], p["tenant"], p["question"], route, outcome, want, nots,
                        f"paraphrases.jsonl:{p['id']}", note))
    turns = sft_turns()
    mirrors = {fn[:-3]: _flat(_read(os.path.join(CORPUS, "acme", fn)))
               for fn in sorted(os.listdir(os.path.join(CORPUS, "acme"))) if fn.endswith(".md")}
    classes = {d["slug"]: d["doc_type"] for d in json.loads(_read(MANIFEST)) if d["tenant_id"] == "acme"}
    for n, question in sorted(REWRITES.items()):
        if n not in turns:
            why.append(f"REWRITES names SFT line {n}; the file has {len(turns)} lines")
            continue
        t = turns[n]
        slug = passage_document(t["passage"], mirrors)
        route = DESK_OF_CLASS.get(classes.get(slug, ""))
        if not route:
            why.append(f"SFT line {n}: {slug} is {classes.get(slug)!r}, which no launch desk answers")
            continue
        if normalise(question) == normalise(t["question"]):
            why.append(f"SFT line {n}: the rewrite is the original question")
        if not content_words(question) & content_words(t["question"]):
            why.append(f"SFT line {n}: the rewrite shares no content word with {t['question']!r} (the wrong line?)")
        if not FIRST_PERSON.search(question):
            why.append(f"SFT line {n}: the rewrite has no first-person marker")
        if n in REWRITE_OUTCOMES:
            outcome, want, nots, judged = REWRITE_OUTCOMES[n]
            judged = f" Outcome judged on the corpus: {judged}."
        else:
            outcome, want, nots, judged = "answer" if t["answerable"] else "grounded_refusal", [], [], ""
            if not t["answerable"] or slug == "hr_policy_2026":
                why.append(f"SFT line {n}: its outcome needs a judgement on {slug}'s whole text in REWRITE_OUTCOMES "
                           f"(the answerable flag judged one passage, or the passage is handbook filler)")
        if n in NEAR_MISS:
            judged += f" A near-miss for {NEAR_MISS[n]}; it must not escalate."
        rows.append(row(f"sft-{n}", None, "sft-" + hashlib.sha256(t["passage"].encode()).hexdigest()[:10], "acme",
                        question, route, outcome, want, nots, f"{SFT_REL}:{n}",
                        f"first-person rewrite of SFT line {n}, a passage of {slug}: {t['question']}{judged}"))
    why += [f"REWRITE_OUTCOMES names SFT line {n}, which REWRITES does not" for n in REWRITE_OUTCOMES
            if n not in REWRITES]
    return merge_groups(rows), why + label_errors(rows)


def merge_groups(rows: list[dict]) -> list[dict]:
    """Rows that ask the same normalised question share a group - the first such row's - so the split by group also
    keeps identical text on one side of it. lk-02 and globex's iso-03 are one group."""
    parent = {r["group"]: r["group"] for r in rows}

    def find(g):
        while parent[g] != g:
            parent[g] = parent[parent[g]]
            g = parent[g]
        return g

    first: dict[str, str] = {}
    for r in rows:
        key = normalise(r["question"])
        if key in first:
            a, b = find(first[key]), find(r["group"])
            if a != b:
                parent[b] = a
        else:
            first[key] = r["group"]
    order = {}
    for r in rows:                                   # name each merged group after its first row's group
        order.setdefault(find(r["group"]), r["group"])
    for r in rows:
        r["group"] = order[find(r["group"])]
    return rows


def label_errors(rows: list[dict]) -> list[str]:
    """The labels against the rule, the launch, and the corpus. Golden's own figures are run_eval.py's to check
    (its offline half); the figures this script adds (PARAPHRASE_LABELS) are checked here, on their boundary."""
    why, corpus = [], {}
    for r in rows:
        q, route = r["question"], r["expected_route"]
        if r["tenant"] in SINGLE:
            if route not in (SINGLE[r["tenant"]], "case"):
                why.append(f"{r['id']}: {r['tenant']} runs single mode on {SINGLE[r['tenant']]}, not {route}")
        elif route in ("handbook", "statute") and r["id"] not in RULE_EXCEPTIONS:
            ruled = rule_route(q)
            if ruled == "two_parts":                 # both parts must be acceptable: the handbook's and the law's
                if not {"handbook", "statute"} <= set(r["acceptable_routes"]):
                    why.append(f"{r['id']}: the labelling rule says two parts (handbook and statute), but "
                               f"acceptable_routes is {r['acceptable_routes']}: {q!r}")
            elif ruled and ruled != route:
                why.append(f"{r['id']}: labelled {route}, but the labelling rule says {ruled}: {q!r}")
        if r["id"] in PARAPHRASE_LABELS or r["source"].startswith(SFT_REL):
            for w in r["must_contain"]:
                text = corpus.setdefault(r["tenant"], corpus_text(r["tenant"]))
                if not contains(text, w):
                    why.append(f"{r['id']}: must_contain {w!r} is not in {r['tenant']}'s corpus")
        for w in PARAPHRASE_GUARDS.get(r["id"], []):
            own = corpus.setdefault(r["tenant"], corpus_text(r["tenant"]))
            others = [t for t in ("acme", "zeta", "globex") if t != r["tenant"]
                      and contains(corpus.setdefault(t, corpus_text(t)), w)]
            if contains(own, w) or not others:
                why.append(f"{r['id']}: must_not_contain {w!r} must be another tenant's figure, absent from "
                           f"{r['tenant']}'s corpus")
    return why


def derived(r: dict) -> bool:
    return r.get("source") != "new"


def current() -> list[dict]:
    if not os.path.exists(ROUTES_FILE):
        return []
    with open(ROUTES_FILE, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def dump(rows: list[dict]) -> str:
    return "".join(json.dumps({k: r.get(k) for k in FIELDS}, ensure_ascii=False) + "\n" for r in rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="fail when routes.jsonl is stale or a row is unsound")
    a = ap.parse_args(argv)
    rows, why = build()
    kept = [r for r in current() if not derived(r)]
    out = rows + kept
    why += check_rows(out)
    if not any(w for r in kept for w in row_errors(r)):
        why += label_errors(kept)                    # the hand-written rows obey the same rule
    ids = {r["id"] for r in out}
    why += [f"RULE_EXCEPTIONS names {i}, which is not a row" for i in RULE_EXCEPTIONS if i not in ids]
    if a.check:
        on_disk = current()
        if dump([r for r in on_disk if derived(r)]) != dump(rows):
            why.append("routes.jsonl's derived rows are not what build_routes.py builds: run it and commit the result")
        why += [w for w in check_rows(on_disk) if w not in why]
    if why:
        print("\n".join(f"FAIL  {w}" for w in why))
        return 1
    if not a.check:
        with open(ROUTES_FILE, "w", encoding="utf-8") as f:
            f.write(dump(out))
    by = lambda key: sum(1 for r in rows if r["source"].startswith(key))  # noqa: E731
    print(f"routes.jsonl: {len(rows)} derived rows (golden {by('golden')}, paraphrases {by('paraphrases')}, "
          f"SFT rewrites {by('sft')}), {len(kept)} hand-written; "
          f"{'checked' if a.check else 'written'}, all {len(out)} valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
