"""The fixed replies of the DocuMind Desk's hard gate, one per class of shared/desk_rules.py (workshop lesson 5.6).

One text per class, so a person gets the same words from every door that applies the gate; in this kit those are
rag-api's (services/rag-api/desk_door.py) and the chat service's (services/chat/desk.py). Code returns these; no
model writes or rewords them on that path.

Each reply says three things and no more: that DocuMind did not answer, that it did not search its documents for
this or write an answer to it, and who the law or the company names to handle it. It says only what holds wherever
the door stands: it does not say the words went nowhere, because a chat brain's own model reads a turn before it
calls rag-api, and it opens no case: a case is opened by the person who asks for one (POST /v1/cases on the chat
service, shared/cases.py), never by a door. It never judges the merits, promises an outcome or an amount, or names a
date the operator has not checked.

The statutory references are to the corpus's own text:

    grievance        Industrial Relations Code, 2020, s.4(1)        evals/corpus/acme/industrial_relations_code_2020.md:397-399
    privacy_request  Digital Personal Data Protection Act, 2023, s.8(9)   evals/corpus/acme/dpdp_act_2023.md:379-382
    exit_dues        Code on Wages, 2019, s.17(2)                    evals/corpus/acme/code_on_wages_2019.md:459-464

The POSH Act in the corpus is a scan with no text layer (evals/README.md), so the posh reply names the Act and its
committees and cites no section.

The second half of this file is the case table (the case queue, shared/cases.py): for each case type the queue the
law or the company names, the clock shown to the person, and the basis, each passage by its corpus file and lines and
by the publisher's URL. Then the instrument table: the Acts the Labour Codes repealed, from the Codes' own repeal
sections. A date an Act or a Code came into force is entered only after a person has checked it against the Gazette,
and none is shown until then (IN_FORCE). Last, the statute desk's in-force note (workshop lesson 10.4): one line for
each instrument a statute answer cites, saying only what the corpus's own text says about it.
"""
from __future__ import annotations

NOWHERE = "DocuMind does not answer this itself: it did not search its documents for this or write an answer to it."

TEMPLATES: dict[str, str] = {
    "posh": (
        "It sounds as if this may be about sexual harassment at work. " + NOWHERE + "\n\n"
        "Under the Sexual Harassment of Women at Workplace (Prevention, Prohibition and Redressal) Act, 2013, your "
        "employer's Internal Committee receives complaints. Each district also has a Local Committee, which receives "
        "complaints in the cases the Act names. You choose what to share with them.\n\n"
        "If the Act does not cover you, your company's own policy may still apply."
    ),
    "grievance": (
        "It sounds as if this is a grievance about how you are treated at work. " + NOWHERE + "\n\n"
        "Under section 4(1) of the Industrial Relations Code, 2020, an industrial establishment employing twenty or "
        "more workers must have one or more Grievance Redressal Committees, for disputes that arise out of "
        "individual grievances. The People team can tell you how to reach yours; you decide what it hears."
    ),
    "privacy_request": (
        "This sounds like a request about your own personal data. " + NOWHERE + "\n\n"
        "Section 8(9) of the Digital Personal Data Protection Act, 2023 asks the company to publish the contact of a "
        "Data Protection Officer, or of a person who answers questions about how your personal data is processed. "
        "That is the person to send this request to."
    ),
    "exit_dues": (
        "This sounds like money owed to you after leaving that has not reached you. " + NOWHERE + "\n\n"
        "Section 17(2) of the Code on Wages, 2019 says that the wages of an employee who has resigned, or been "
        "removed, dismissed or retrenched, are paid within two working days. The company's payroll team handles "
        "what is owed to you."
    ),
    "human_requested": (
        "You asked for a person. " + NOWHERE + "\n\n"
        "DocuMind does not pass this to a person by itself. Contact the People team directly, or raise a case for "
        "them where your company's DocuMind offers it."
    ),
}


def template(cls: str) -> str:
    """The fixed reply for a gate class. A class with no text is a programming error, never a silent default."""
    return TEMPLATES[cls]


# ---------------------------------------------------------------- the case table (workshop lesson 5.6)
# What a case shows the person who raised it, and which queue reads it. A clock is information, never a promise: a
# period an Act sets is quoted or named, and a date the company sets is labelled as the company's own target
# (tenant_settings/{tenant}.case_queues, which the operator writes with make desk-queues). Nothing here judges a case.

URLS = {   # the publisher's copy each corpus file was taken from: evals/manifest.json's source_url (the tests hold them equal)
    "industrial_relations_code_2020": "https://www.labour.gov.in/static/uploads/2025/07/682a44b5426bff2c1f4943ee1b2fd566.pdf",
    "dpdp_act_2023": "https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf",
    "code_on_wages_2019": "https://www.labour.gov.in/static/uploads/2025/06/c328da14bbb15fc4ad571dc33e7a4ab3.pdf",
    "osh_code_2020": "https://www.labour.gov.in/static/uploads/2025/07/36fcfa5d8e6b9145e282bf7b950d6c47.pdf",
    "code_on_social_security_2020": "https://www.labour.gov.in/static/uploads/2025/07/b0620548445580767b5c0d18c95c26f7.pdf",
    "posh_act_2013": "https://gil.gujarat.gov.in/Media/DocumentUpload/posh_act._english.pdf",
}


def _basis(slug: str, instrument: str, section: str | None, lines: str | None, says: str) -> dict:
    """One passage a case rests on: the Act, the section, the corpus file and its lines (the same text in every tenant
    that holds the file), the publisher's URL for a tenant that does not, and what it says, in plain words."""
    return {"instrument": instrument, "section": section, "file": f"{slug}.md" if lines else f"{slug}.pdf",
            "lines": lines, "url": URLS[slug], "says": says}


IR, DPDP, WAGES = "Industrial Relations Code, 2020", "Digital Personal Data Protection Act, 2023", "Code on Wages, 2019"
OSH, CSS = "Occupational Safety, Health and Working Conditions Code, 2020", "Code on Social Security, 2020"
POSH_ACT = "Sexual Harassment of Women at Workplace (Prevention, Prohibition and Redressal) Act, 2013"

BASIS: dict[str, dict] = {
    "ir_s4_1": _basis("industrial_relations_code_2020", IR, "s.4(1)", "397-399",
                      "An industrial establishment employing twenty or more workers must have one or more Grievance Redressal "
                      "Committees, for disputes arising out of individual grievances."),
    "ir_s4_5": _basis("industrial_relations_code_2020", IR, "s.4(5)", "422-425",
                      "An aggrieved worker may apply to the committee within one year from the date on which the cause "
                      "of action arises."),
    "ir_s4_6": _basis("industrial_relations_code_2020", IR, "s.4(6)", "426-427",
                      "The committee may complete its proceedings within thirty days of receiving the application."),
    "dpdp_s8_9": _basis("dpdp_act_2023", DPDP, "s.8(9)", "379-382",
                        "The company publishes the contact of a Data Protection Officer, or of a person who answers "
                        "questions about how your personal data is processed."),
    "dpdp_s13_2": _basis("dpdp_act_2023", DPDP, "s.13(2)", "490-492",
                         "The company responds to a grievance within such period as may be prescribed."),
    "wages_s17_2": _basis("code_on_wages_2019", WAGES, "s.17(2)", "459-464",
                          "The wages of an employee who is removed, dismissed or retrenched, or who resigns, are paid "
                          "within two working days of the removal, dismissal, retrenchment or resignation."),
    "osh_s32_1_vi": _basis("osh_code_2020", OSH, "s.32(1)(vi)", "1537-1548",
                           "A worker who is discharged or dismissed or who quits is paid wages in lieu of unused leave "
                           "before the expiry of the second working day from the date of the discharge, dismissal or "
                           "quitting. The Code's worker (section 2(1)(zzl)) leaves out, among others, a person employed "
                           "mainly in a managerial or administrative capacity."),
    "css_s56_3": _basis("code_on_social_security_2020", CSS, "s.56(3)", "2365-2366",
                        "Gratuity is paid within thirty days from the date it becomes payable."),
    # The Act is a scan with no text layer in the corpus: named, with no section, until a person has checked the
    # sections against the Act's text.
    "posh_act": _basis("posh_act_2013", POSH_ACT, None, None,
                       "The employer's Internal Committee receives complaints. Each district also has a Local Committee, "
                       "which receives complaints in the cases the Act names."),
}

CLOCKS: dict[str, str] = {
    "posh": ("The Act sets time limits for making a written complaint and for the committee's inquiry. The members you "
             "chose, or the Local Committee, can tell you what they are and how they apply to you."),
    "grievance": ("Under section 4(5) of the Industrial Relations Code, 2020, a worker may apply to the Grievance "
                  "Redressal Committee within one year from the date on which the cause of action arises. A case raised "
                  "here is not that application: the year keeps running until you apply in the manner prescribed. Under "
                  "section 4(6), the committee may complete its proceedings within thirty days of receiving an "
                  "application. These sections are for a worker as the Code defines one (section 2(zr)), which leaves "
                  "out, among others, a person employed mainly in a managerial or administrative capacity."),
    "grievance_accepted": ("Your company's Grievance Redressal Committee takes a case raised here as your application. "
                           "Under section 4(6) of the Industrial Relations Code, 2020, the committee may complete its "
                           "proceedings within thirty days of receiving it."),
    "privacy_request": ("The Digital Personal Data Protection Act, 2023 comes into force on the dates the Central "
                        "Government notifies, which may differ from one provision to another (section 1(2)). It leaves "
                        "the period for answering a grievance to rules (section 13(2)). The date shown is the company's "
                        "own target."),
    "exit_dues": ("Section 17(2) of the Code on Wages, 2019: \"the wages payable to him shall be paid within two working "
                  "days of his removal, dismissal, retrenchment or, as the case may be, his resignation.\" A worker's "
                  "wages in lieu of unused leave are paid before the expiry of the second working day from the date of "
                  "the discharge, dismissal or quitting (section 32(1)(vi) of the Occupational Safety, Health and "
                  "Working Conditions Code, 2020, whose worker leaves out, among others, a person employed mainly in a "
                  "managerial or administrative capacity), and gratuity within thirty days from the date it becomes "
                  "payable (section 56(3) of the Code on Social Security, 2020)."),
    "exit_dues_late": ("By the desk's own reading, counting two working days (Monday to Friday) from the last working "
                       "day you gave, the date in section 17(2) may have passed. This is not a legal opinion."),
    "company_target": "The date shown is the company's own target for this queue, not a date set by law.",
}

# The queues and who reads them. A queue's roles (shared/roles.py) read it; "status" may also move a case along;
# "opt_in" reads a case only when the person who raised it chose to share it. ic:<unit> is a POSH queue: only the
# Internal Committee members of that unit whom the person chose (ic_member:<unit> and in chosen_contacts).
QUEUES: dict[str, dict] = {
    "grc": {"name": "Grievance Redressal Committee", "status": ("grc_member",), "read": ("grc_member",),
            "opt_in": ("people_ops",)},
    "privacy": {"name": "Privacy contact", "status": ("privacy",), "read": ("privacy",), "opt_in": ()},
    "payroll": {"name": "Payroll", "status": ("payroll",), "read": ("payroll", "people_ops"), "opt_in": ()},
    "people": {"name": "People team", "status": ("people_ops",), "read": ("people_ops",), "opt_in": ()},
}
IC_QUEUE = "ic:"

# The six types the "Raise a case" button offers. draft False: the button opens the case itself (posh holds no text,
# so there is nothing to draft and confirm). fallback: the queue a type goes to when its own is not configured, the
# type kept. A type whose queue is configured nowhere cannot be raised.
CASE_TYPES: dict[str, dict] = {
    "posh": {"queue": "ic", "draft": False, "fallback": None, "clock": "posh", "basis": ("posh_act",)},
    "grievance": {"queue": "grc", "draft": True, "fallback": None, "clock": "grievance",
                  "basis": ("ir_s4_1", "ir_s4_5", "ir_s4_6")},
    "privacy_request": {"queue": "privacy", "draft": True, "fallback": "people", "clock": "privacy_request",
                        "basis": ("dpdp_s8_9", "dpdp_s13_2")},
    "exit_dues": {"queue": "payroll", "draft": True, "fallback": None, "clock": "exit_dues",
                  "basis": ("wages_s17_2", "osh_s32_1_vi", "css_s56_3")},
    "people_query": {"queue": "people", "draft": True, "fallback": None, "clock": None, "basis": ()},
    "human_requested": {"queue": "people", "draft": True, "fallback": None, "clock": None, "basis": ()},
}
SENSITIVE_CASES = frozenset({"posh", "grievance", "privacy_request"})   # desk_rules.SENSITIVE: logged as "sensitive"

# The instrument table: Acts the Labour Codes repealed, by the Codes' own repeal sections in the corpus. A repeal takes
# effect when its Code comes into force (IN_FORCE["labour_codes"]), so nothing shows "repealed" before that date is set.
_WAGES_69 = {"status": "repealed", "by": "Code on Wages, 2019, s.69(1)", "file": "code_on_wages_2019.md",
             "lines": "1632-1633"}
_CSS_164 = {"status": "repealed", "by": "Code on Social Security, 2020, s.164(1)",
            "file": "code_on_social_security_2020.md", "lines": "5409-5418"}
INSTRUMENTS: dict[str, dict] = {
    "Payment of Wages Act, 1936": _WAGES_69,
    "Minimum Wages Act, 1948": _WAGES_69,
    "Payment of Bonus Act, 1965": _WAGES_69,
    "Equal Remuneration Act, 1976": _WAGES_69,
    "Maternity Benefit Act, 1961": _CSS_164,
    "Payment of Gratuity Act, 1972": _CSS_164,
}
# The dates the operator enters after checking the Gazette: the Labour Codes in force, and the DPDP Act's provisions on
# a Data Principal's rights. None is never shown to a person.
IN_FORCE: dict[str, str | None] = {"labour_codes": None, "dpdp_rights": None}


def basis_for(case_type: str) -> list[dict]:
    """The passages a case type rests on, in the order a person reads them."""
    return [dict(BASIS[k]) for k in CASE_TYPES[case_type]["basis"]]


# The statute desk's in-force note (workshop lesson 10.4), by the corpus file a citation comes from. Each line says
# what the corpus's own text says and nothing more: the four Codes and the DPDP Act come into force on dates the
# Central Government notifies (each one's section 1), an Act a Code repeals is repealed from the day that Code comes
# into force, and a text's as-of wording is its file's own header ("as on 1 August 2021", "as enacted"). A date is
# shown only once IN_FORCE holds one a person has checked. The POSH Act is a scan with no text layer, so no answer
# cites it and it has no line.
GUIDANCE = "Compliance Handbook for Employers Under the Four Labour Codes (Central Government Sphere)"
STATUTES: dict[str, dict] = {
    "code_on_wages_2019": {"title": WAGES, "commences": ("s.1(3)", "22-25"), "in_force": "labour_codes"},
    "code_on_social_security_2020": {"title": CSS, "commences": ("s.1(3)", "25-28"), "in_force": "labour_codes"},
    "industrial_relations_code_2020": {"title": IR, "commences": ("s.1(3)", "25-28"), "in_force": "labour_codes"},
    "osh_code_2020": {"title": OSH, "commences": ("s.1(2)", "25-28"), "in_force": "labour_codes"},
    "dpdp_act_2023": {"title": DPDP, "commences": ("s.1(2)", "24-27"), "in_force": "dpdp_rights"},
    "payment_of_bonus_act_1965": {"title": "Payment of Bonus Act, 1965", "repealed": "Payment of Bonus Act, 1965"},
    "payment_of_gratuity_act_1972": {"title": "Payment of Gratuity Act, 1972", "repealed": "Payment of Gratuity Act, 1972"},
    "maternity_benefit_act_1961": {"title": "Maternity Benefit Act, 1961", "repealed": "Maternity Benefit Act, 1961"},
    "maternity_benefit_amendment_act_2017": {"title": "Maternity Benefit (Amendment) Act, 2017",
                                             "amends": "Maternity Benefit Act, 1961"},
    "cgst_act_2017": {"title": "Central Goods and Services Tax Act, 2017", "as_of": "as on 1 August 2021"},
    "it_act_2000": {"title": "Information Technology Act, 2000", "as_of": "as enacted"},
    "labour_codes_compliance_handbook": {"title": GUIDANCE, "guidance": True},
}
NOT_ADVICE = "Legal information, not advice."
UNCHECKED = "the date is not shown here until a person has checked it against the Gazette"


def statute_of(name: str) -> str | None:
    """The STATUTES key a cited object belongs to: its file stem, or the longest key a figure's name starts with
    (payment_of_bonus_act_1965_p30.png is the Bonus Act's page)."""
    stem = (name or "").rsplit("/", 1)[-1].rsplit(".", 1)[0]
    return max((k for k in STATUTES if stem == k or stem.startswith(k + "_")), key=len, default=None)


def _repeal(act: str, subject: str) -> str:
    by = INSTRUMENTS[act]["by"]
    date = IN_FORCE["labour_codes"]
    if date:
        return f"{subject} was repealed with effect from {date} by the {by}"
    return f"the {by} repeals {subject} from the day the {by.split(', s.')[0]} comes into force ({UNCHECKED})"


def in_force_line(key: str) -> str:
    """The note for one instrument, by its STATUTES key."""
    s = STATUTES[key]
    if "commences" in s:
        section, lines = s["commences"]
        date = IN_FORCE[s["in_force"]]
        if date:
            what = "its provisions on a Data Principal's rights are" if s["in_force"] == "dpdp_rights" else "it is"
            return f"{s['title']}: {what} in force from {date}, as checked against the Gazette."
        return (f"{s['title']}: it comes into force on such date as the Central Government may, by notification, "
                f"appoint, and different dates may be appointed for different provisions ({section}); {UNCHECKED}.")
    if "repealed" in s:
        return f"{s['title']}: {_repeal(s['repealed'], 'it')}; shown for comparison."
    if "amends" in s:
        return f"{s['title']}: it amends the {s['amends']}; {_repeal(s['amends'], 'that Act')}; shown for comparison."
    if "as_of" in s:
        return f"{s['title']}: the text here is {s['as_of']}; an amendment made after that is not in it."
    return f"{s['title']}: the ministry's guidance on the Codes, not the text of a Code."


def in_force_lines(names) -> list[str]:
    """The statute desk's note for the objects an answer cites, in the order cited, each instrument once, and always
    the closing line."""
    keys = []
    for n in names or ():
        k = statute_of(n)
        if k and k not in keys:
            keys.append(k)
    return [in_force_line(k) for k in keys] + [NOT_ADVICE]
