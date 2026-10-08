"""The DocuMind Desk's hard gate: the questions the law hands to a person, found by rule (workshop lesson 5.6).

A gate class fires when a first-person marker and one of the class's topic patterns are both in the question, in
English, in Devanagari Hindi or in Hinglish (Hindi typed in Latin letters). Five classes, most protective first:

    posh             a disclosure of sexual harassment at work: the employer's Internal Committee
    grievance        a complaint about how the person is treated: the Grievance Redressal Committee
    privacy_request  the person's own data - see it, correct it, erase it, withdraw consent: the privacy contact
    exit_dues        a leaver's wages, full and final settlement or gratuity that has not been paid
    human_requested  "let me talk to a person"

gate() returns the class and nothing else - never the words that matched - so no caller can log or echo them. A hit
is answered with the fixed text in shared/desk_law.py, by code. rag-api's door (services/rag-api/desk_door.py) calls
it before any handler, so on a hit rag-api retrieves nothing, calls no model and caches nothing. The chat service's
agent brains send a turn to their own model before they call rag-api, so on those paths rag-api's door reads only
the search words that model wrote: it stops the search when they hit, which they need not, and the brain's model
writes the reply. So the chat service has a door of its own (services/chat/desk.py) in front of POST /v1/chat: it
calls gate() on the person's own words before any brain runs, and unless the tenant's desk_gate is off, a turn that
hits reaches no model at all. gate_state() reads that switch: rules unless an operator says off, or on - the rules
and a model check behind them (shared/desk_recall.py) for what no pattern catches.

A question about how the law or the process works is not a disclosure. "Under the POSH Act, where do I file a
complaint?" and "How do I raise a grievance?" ask what the statute or the handbook says, and they are answered from
the documents. So each class has two kinds of topic pattern:

    DISCLOSE   the person says it happened to them, or asks for it now ("my manager touched me", "harassment ho raha
               hai", "मुझे धमकी देते हैं", "connect me to a human"): fires with a first-person marker, whatever else
               the question says
    PROCESS    a step the person may be asking about or asking for ("file a POSH complaint", "withdraw my consent",
               "raise a grievance"): fires only when the question carries no information frame (INFO: "under the
               Act", an Act's name, "how do I", "what is", "can I", "policy", "kya hai", "कैसे") - or when the person
               plainly asks for the step itself ("I want to raise a grievance", "please delete my data", "karni hai")

A DISCLOSE pattern has a person in it - the one it happened to, or the one who did it ("my boss keeps making sexual
jokes", "unwelcome advances towards me", "manager ki shikayat") - never a bare subject word: "harassment" alone is
the POSH Act's subject, "the anti-bullying policy" a document, "grievance" the IR Code's committee, and a complaint
about a laptop or the leave policy is not about a person. Most disclosures end by asking for help ("What can I do?",
"What are my options?", "kya karun?"); that is the person's own situation, not an information frame, so those
phrases are taken out before INFO is read ("What should I do if ..." stays a question about a rule). The
first-person markers leave out what only looks like one: the Roman numeral in "clause (i)", "i.e." and "Schedule I"
(after a statute's own nouns, and never before a verb: "at the dinner table I was ..." is the person), "me" in "tell
me" or "help me understand" and in Hinglish (where it means "in"), and "im" outside "im being ...".

Precision is held by both halves: "What does the POSH Act say about harassment?" has no first person, and "Can I
carry forward my earned leave?" no topic. commands/tests/test_desk_rules.py holds the lexicon to 0 fires on every
question the course already sends, and to its model-written examples and near misses, per class and script.

mask() removes the identifiers a model must not see - Aadhaar (Verhoeff-checked) and card numbers (Luhn-checked),
shared/identifiers.py - and says which kinds it removed. PAN and GSTIN pass. Each number becomes a token no longer
than the number, so a masked question is never longer than the one the handler's length check would see.

action() is the router's out_of_scope candidate: an action in another system ("apply my leave", "approve my claim")
or a look-up of the person's own record ("my leave balance", "my payslip"). It is a candidate, not a gate: the
router decides.

RULES_VERSION goes on every desk_gate log row. Change any pattern here and bump it, so a fire rate that moves can be
read against the lexicon that moved it.
"""
from __future__ import annotations

import re
import unicodedata

try:                                   # the package import (the services, the tests) and the flat one (an image
    from shared import identifiers     # that copies shared/ beside its modules) both work
except ImportError:                    # pragma: no cover
    import identifiers  # type: ignore

RULES_VERSION = "2026-10-01.4"

CLASSES = ("posh", "grievance", "privacy_request", "exit_dues", "human_requested")
SENSITIVE = frozenset({"posh", "grievance", "privacy_request"})   # logged with user null and class "sensitive"

# Devanagari has combining vowel signs that re's \b treats as word breaks, so a Hindi pattern is anchored by these
# instead: not preceded (or followed) by another Devanagari character.
_DV = "ऀ-ॿ"
_DB = rf"(?<![{_DV}])"
_DE = rf"(?![{_DV}])"


def _rx(*parts: str) -> re.Pattern:
    return re.compile("|".join(f"(?:{p})" for p in parts))


# ---------------------------------------------------------------- first-person markers
# English singular first person, Devanagari singular first person, and Hinglish. "We" and "our" are left out on
# purpose: the course's questions use them for the company ("we received a notice of appeal"), and a disclosure is
# made by a person. Two English words are also Hinglish words: "me" is Hinglish for "in" ("POSH Act me kya likha
# hai"), so it counts only in a question that is not Hinglish; "main"/"mai" is Hinglish for "I" and English for
# "main", so it counts only beside a first-person verb ending ("main baat karna chahti hoon").
_FIRST_EN = (r"\b(?:i|my|mine|myself|i'm|i've|i'd|i'll)\b",
             r"\bim\s+(?:being|getting|not|so|really|still|scared|afraid|facing|a\s+victim|the\s+victim|fed\s+up)\b")
_FIRST_HI = _DB + r"(?:मैं|मैंने|मुझे|मुझसे|मुझको|मुझ|मेरा|मेरी|मेरे)" + _DE
_FIRST_HG = r"\b(?:mujhe|mujhey|mujhko|muje|mjhe|mujhse|mujse|mujh|mera|meraa|meri|mere|maine|mainey|mene)\b"
FIRST_PERSON = _rx(*_FIRST_EN, _FIRST_HI, _FIRST_HG)
# What only looks like "I" or "me": a Roman numeral (a clause, a schedule, a form, "i.e."), and "me" as the object
# of a request for information ("tell me", "help me understand"). The numeral is read only after a statute's own
# nouns, and never when a verb follows it: "Schedule I lists ..." is a numeral, "at the dinner table I was ..." and
# "no, I was ..." are the person.
_I_VERB = (r"(?:was|am|were|have|had|has|want|wanted|need|needed|feel|felt|got|get|did|do|don't|didn't|dont|didnt|"
           r"can|cannot|can't|could|couldn't|will|won't|would|should|shall|may|might|must|wish|really|just|also|still|"
           r"keep|kept|think|thought|believe|told|asked|said|reported|complained|filed|raised|received|resigned|left|"
           r"quit|joined|work|worked|saw|heard|know|knew|went|came|tried|never|always|often|only|then|too|recently|"
           r"already|personally|myself)")
_NOT_I = re.compile(r"\(i\)|\bi\)|\bi\.e\b\.?|\b(?:part|schedule|form|clause|sub-?clause|item|section|sub-?section|"
                    r"annexure|annex|chapter|appendix|article|rule|para|paragraph|column|division|volume|vol)\.?\s+i\b"
                    r"(?!'|\s+" + _I_VERB + r"\b)")
_ME_INFO = re.compile(r"\b(?:tell|help|show|give|explain\s+to|remind|guide|teach|let|walk|brief|inform|update)\s+me\b")
_ME = re.compile(r"\bme\b")
_MAIN = re.compile(r"\b(?:main|mai)\b")
_MAIN_VERB = re.compile(r"\b(?:hoon|hun|hu|hoo|chahta|chahti|chahunga|chahungi|sakta|sakti|karunga|karungi|karoon|karun|karu|"
                        r"jaun|jaaun|gaya\s+(?:hoon|hun|hu|tha)|gayi\s+(?:hoon|hun|hu|thi))\b")
_HINGLISH_WORDS = frozenset("hai hain kya ka ki ke ko se nahi nahin nhi mein aur bhi kaise kab kitne kitna kitni raha rahi "
                            "rahe hota hoti tha thi karna karni chahiye wala wali".split())


def _hinglish(t: str) -> bool:
    """Two or more Hinglish function words: the question is written in Hinglish."""
    return len(_HINGLISH_WORDS & set(re.findall(r"[a-z]+", t))) >= 2


def _first_person(t: str) -> bool:
    t = _NOT_I.sub(" ", t)
    if FIRST_PERSON.search(t):
        return True
    if _ME.search(_ME_INFO.sub(" ", t)) and not _hinglish(t):
        return True
    return bool(_MAIN.search(t) and _MAIN_VERB.search(t))


# ---------------------------------------------------------------- the information frame, and a plain request
# INFO: the question asks what a law, a policy or a process says. A PROCESS pattern does not fire beside it.
INFO = _rx(
    # an authority: "under the Act / Code / law", an Act's or a Code's name, a section
    r"\bunder\s+(?:the\s+|this\s+|that\s+|which\s+|what\s+|a\s+|an\s+)?(?:[\w&'-]+\s+){0,6}?"
    r"(?:act|acts|code|codes|law|laws|rules?|regulations?|sections?|statute|policy)\b",
    r"\b(?:posh|dpdp|it|ir|payment\s+of\s+gratuity|payment\s+of\s+wages|data\s+protection)\s+act\b",
    r"\b(?:act|code)\s*,?\s*(?:19|20)\d\d\b", r"\bcode\s+on\s+(?:wages|social\s+security)\b",
    r"\b(?:industrial\s+relations|social\s+security|wage|wages)\s+code\b", r"\bsection\s+\d", r"\bs\.\s?\d",
    # asking how it works
    r"\bhow\s+(?:do|does|did|can|could|should|would|will|is|are|to|long|soon|many|much|often)\b",
    r"\bwhere\s+(?:do|does|can|could|should|would|to|is|are)\b",
    r"\b(?:what|which|who|whom|when)\s+(?:is|are|was|were|does|do|did|must|should|can|could|counts|happens|qualifies|"
    r"constitutes|handles|hears|decides|form|forms|committee|authority|officer|rights?|options?|steps?|kind|types?)\b",
    r"\b(?:is|are)\s+there\s+(?:a|an|any)\b", r"\bcan\s+i\b", r"\bcould\s+i\b",
    r"\bam\s+i\s+(?:allowed|entitled|eligible|able|required|protected|covered)\b",
    r"\bis\s+it\s+(?:possible|allowed|legal|mandatory|necessary|compulsory)\b",
    r"\bdefin\w+", r"\bmean(?:s|ing|t)?\b", r"\bprocess(?:es)?\b", r"\bprocedures?\b", r"\btimelines?\b",
    r"\btime\s*limits?\b", r"\bdeadlines?\b", r"\bpolic(?:y|ies)\b", r"\btraining\b", r"\bdraft\w*", r"\bhandbook\b",
    r"\bunderstand\w*", r"\bexplain\w*", r"\bknow\b", r"\blearn\b", r"\bexamples?\b",
    r"\bas\s+(?:an?\s+|the\s+)?(?:ic|icc|internal\s+committee|grc|committee|hr|manager|employer|presiding\s+officer|"
    r"member|team\s+lead|lead|dpo|data\s+protection\s+officer)\b",
    r"\bhandle\s+(?:a|an|the|such)\b",
    # Hinglish
    r"\b(?:kaise|kaisey|kahan|kahaan|kab\s+tak|kitne|kitna|kitni|kaun\s+sa|kaunsa|kaun\s+si|matlab|definition|niyam|"
    r"kanoon|kanun|batao|bataiye|bataye|bataao|samjhao|samjhaiye|samjhaye|policy|act)\b",
    r"\bkya\s+(?:hai|hain|hota|hoti|hote|kehta|kehti|kahta|kahti|bolta|likha)\b", r"\bke\s+(?:baare|bare|bar)\b",
    # Devanagari
    _DB + r"(?:अधिनियम|कानून|क़ानून|नियम|नीति|पॉलिसी|परिभाषा|मतलब|कैसे|कहाँ|कहां|कितने|कितना|कितनी|कौन|प्रक्रिया|बताइए|बताओ|समझाइए)",
    _DB + r"क्या\s+(?:है|हैं|होता|होती|होते|कहता|कहती|लिखा)" + _DE, _DB + r"के\s+बारे" + _DE,
)
# Asking for help with one's own situation is not an information frame: "My boss makes sexual jokes about me. What
# can I do?" ends a disclosure the way most do. These phrases are taken out before INFO is read, so the "what can",
# "how do", "know" and "options" inside them do not suppress a PROCESS pattern. "What should I do if ..." stays a
# question about a rule.
_HELP = _rx(
    r"\bwhat\s+(?:else\s+)?(?:can|should|do|shall|could|must|would)\s+i\s+(?:even\s+|now\s+|possibly\s+)?do\b"
    r"(?!\s+(?:if|when|in\s+case|whenever)\b)(?:\s+(?:now|next|here|about\s+(?:this|it|him|her|them)))?",
    r"\bwhat\s+(?:are|r)\s+my\s+(?:options|rights|choices|next\s+steps)\b(?!\s+(?:under|as\s+per|according)\b)",
    r"\b(?:please\s+)?help\s+me\s+(?:understand\s+)?(?:my\s+options|what\s+(?:to|i\s+(?:can|should))\s+do)\b",
    r"\bhow\s+(?:do|can|could|should|shall)\s+i\s+(?:stop|handle|deal\s+with|cope\s+with|get\s+out\s+of|make\s+(?:it|"
    r"this|him|her|them)\s+stop|report|escalate|complain\s+about)\s+(?:this|it|him|her|them|that)\b",
    r"\bis\s+there\s+(?:a|any)\s+way\s+to\s+(?:stop|end|report|escalate)\s+(?:this|it|him|her|them|that)\b",
    r"\bi\s+(?:don't|dont|do\s+not|didn't|didnt|did\s+not)\s+know\s+what\s+to\s+do\b",
    r"\bkya\s+(?:karun|karoon|karu|karoo|kru|karna\s+chahiye|kar\s+(?:sakta|sakti|sakte)\s*(?:hoon|hun|hu|hain)?)\b",
    r"\bkisko\s+(?:bataun|bataoon|batau|bolun|boloon)\b",
    _DB + r"क्या\s+(?:करूँ|करूं|करू|करना\s+चाहिए|कर\s+(?:सकता|सकती)(?:\s+(?:हूँ|हूं))?)" + _DE,
    _DB + r"किसको\s+(?:बताऊँ|बताऊं|बताऊ)" + _DE,
)


def _info(t: str) -> bool:
    """An information frame, read after the person's own call for help is taken out."""
    return bool(INFO.search(_HELP.sub(" ", t)))


# A plain request: the person asks for the step itself, so a PROCESS pattern fires beside an information frame too
# ("Under the DPDP Act I want my data deleted"). "I want to know / understand" is a question, not a request, and so
# is "can I withdraw ...".
_I = "".join(rf"(?<!{w}\s)" for w in ("can", "could", "may", "should", "do", "if", "would", "will", "shall", "when", "how")) + r"\bi"
_STEP = (r"(?:raise|file|lodge|submit|register|make|report|complain|withdraw|revoke|delete|erase|remove|wipe|correct|"
         r"rectify|update|access|get|see|open|stop|object|escalate|speak|talk|meet|contact)")
REQUEST = _rx(
    _I + r"\s+(?:really\s+)?(?:want|need|wish|would\s+like|have|am\s+going)\s+to\s+" + _STEP + r"\b",
    r"\bi'd\s+like\s+to\s+" + _STEP + r"\b",
    _I + r"\s+(?:hereby\s+|formally\s+)?(?:withdraw|revoke|request|demand|object)\b",
    _I + r"\s+(?:am|'m)\s+(?:raising|filing|lodging|submitting|making|reporting|withdrawing|requesting)\b",
    _I + r"\s+(?:want|need|would\s+like)\s+(?:a|an|my)\s+(?:copy|list|record|grievance|complaint)\b",
    _I + r"\s+(?:want|need|would\s+like)\s+(?:all\s+)?(?:of\s+)?my\s+(?:personal\s+)?(?:data|details|information|info|records?|"
    r"profile)\s+(?:deleted|erased|removed|corrected|updated|back)\b",
    r"\b(?:please|kindly|pls|plz)\s+(?:delete|erase|remove|wipe|withdraw|correct|stop|register|escalate|connect)\b",
    # Hinglish and Hindi
    r"\b(?:karna|karni|krna|krni|karwana|karwani|dena|deni|lena|leni)\s+(?:hai|h|he|chahta|chahti|chahunga|chahungi)\b",
    r"\b(?:kar|kr)\s+(?:do|dijiye|dijie|dena|dein|den)\b", r"\b(?:chahta|chahti)\s+(?:hoon|hun|hu|hoo)\b",
    _DB + r"(?:करना|करनी|लेना|लेनी|देना|देनी|करवाना|करवानी)\s+(?:है|हैं|चाहता|चाहती|चाहूँगा|चाहूँगी)" + _DE,
    _DB + r"(?:चाहता|चाहती)\s+(?:हूँ|हूं|हु)" + _DE, _DB + r"(?:दीजिए|दीजिये|कीजिए|कीजिये|करवाइए|करवाइये|करें|दें)" + _DE,
)

# ---------------------------------------------------------------- topic patterns, per class
# A person who can do something to the speaker, and (_PERSON) the same with the bodies a complaint can be against.
_WHO = (r"(?:manager|managers|boss|bosses|lead|team\s+lead|tl|supervisor|senior|seniors|colleague|colleagues|coworker|"
        r"coworkers|co-worker|co-workers|reporting\s+manager|hod|head\s+of\s+(?:the\s+)?department|client|clients|"
        r"customer|customers|vendor|teammate|teammates|director|ceo|cto|founder|peer|peers|junior|juniors|trainer|"
        r"mentor|interviewer|guy|man|woman)")
_PERSON = r"(?:" + _WHO[3:-1] + r"|employer|company|management|hr|him|her|them)"
# Someone doing it, not a rule about it: "if a client makes ..." is a question, "a client makes ..." is not.
_ACTOR = (r"(?<!\bif\s)(?<!\bwhen\s)(?<!\bwhenever\s)(?<!\bcase\s)(?<!\bsuppose\s)(?<!\bunless\s)"
          r"(?:\b(?:my|a|an|the|our|this|that|his|her|some|one\s+of\s+(?:my|the|our))\s+(?:\w+\s+){0,2}?" + _WHO +
          r"\b|\b(?:he|she|they|someone|somebody)\b)")
# Conduct of a sexual kind, named by its form ("sexual jokes", "unwelcome advances", "obscene messages"). A DISCLOSE
# pattern when someone does it ("my manager keeps making sexual comments") or it is aimed at the person ("... about
# me"); on its own it is a PROCESS pattern.
_CONDUCT = (r"(?:sexual(?:ly)?(?:\s+explicit)?|lewd|vulgar|dirty|obscene|explicit|unwelcome|inappropriate|indecent|"
            r"suggestive|nude|naked|porn\w*|double[-\s]meaning|sleazy|creepy)\s+(?:(?!consent\b)\w+\s+)?"
            r"(?:comments?|jokes?|remarks?|advances?|favou?rs?|innuendos?|messages?|msgs?|texts?|pictures?|pics?|photos?|"
            r"images?|videos?|gestures?|emails?|memes?|calls?|propositions?|proposals?|stares?|staring|looks?|touch\w*|"
            r"contact|attention|behaviou?r|conduct|requests?|questions?|songs?|stories)\b")
_DOES = (r"(?:(?:keeps?|kept|has\s+been|have\s+been|had\s+been|is|was|are|were|always|often|constantly|repeatedly|"
         r"again|still|also|now|even|regularly|continuously|started|starts)\s+){0,3}"
         r"(?:mak(?:e|es|ing)|made|send(?:s|ing)?|sent|pass(?:es|ed|ing)?|crack(?:s|ed|ing)?|tell(?:s|ing)?|told|"
         r"ask(?:s|ed|ing)?\s+(?:me\s+)?for|demand(?:s|ed|ing)?|show(?:s|ed|ing)?|shar(?:es|ed|ing)|"
         r"forward(?:s|ed|ing)?|text(?:s|ed|ing)?|messag(?:es|ed|ing)|post(?:s|ed|ing)?|giv(?:es|ing)|gave|"
         r"direct(?:s|ed|ing)?|throw(?:s|ing)?|threw)")
# What a complaint can be about without being about how a person is treated: a rule, a system, or a service.
_THINGS = (r"(?:policy|policies|process\w*|procedure\w*|portal|system|rules?|software|tool|app|laptop|cab|cabs|"
           r"transport|pickups?|drops?|delays?|service|services|quality|food|canteen|wifi|internet|parking|invoices?|"
           r"bills?|billing|deliver(?:y|ies)|timings?|schedule|payroll|payslip|reimbursement)")
_NOT_A_RULE = (r"(?!'s?\s+(?:\w+\s+){0,2}?" + _THINGS + r"\b|\s+(?:\w+\s+)?" + _THINGS + r"\b)")
_WHO_HG = (r"(?:manager|boss|senior|colleague|lead|tl|team\s+lead|supervisor|hr|sir|madam|ma'am|saheb|sahab|director|"
           r"client|hod|teammate|junior|bhaiya|didi)")
_THING = r"\s+(?:me\s+|to\s+me\s+)?(?:(?:a|an|the|some|many|more|these|those|such|his|her|their|lots\s+of|so\s+many)\s+)?"
_BODY = (r"(?:body|chest|back|legs?|thighs?|waist|hair|face|hands?|shoulders?|breasts?|bottom|hips?|lips?|neck|"
         r"looks|appearance|figure|clothes|dress|outfit|private\s+parts?)")
# What a quid pro quo asks for: "... a good rating if I spend the night with him", "... fire me if I didn't go out with him".
_SEXUAL_ACT = (r"(?:don't\s+|didn't\s+|do\s+not\s+|did\s+not\s+|won't\s+|refuse\s+to\s+|agree\s+to\s+)?"
               r"(?:spend\s+(?:the|a|one)\s+night|sleep\s+with|go\s+(?:out|on\s+a\s+date|on\s+dates)\s+with|date\s+(?:him|her)|"
               r"have\s+sex|kiss\s+(?:him|her)|meet\s+(?:him|her)\s+alone|come\s+to\s+(?:his|her|their)\s+(?:room|hotel|"
               r"house|flat|place)|sit\s+on\s+(?:his|her)\s+lap|send\s+(?:him|her)\s+(?:my\s+)?(?:photos|pictures|pics))")
# "I was / I am being / I've been ..." - the person says it happened to them.
_I_WAS = (r"(?:\bi\s+(?:was|am|have\s+been|had\s+been|got|get|keep\s+getting|feel|felt)|\bi'm|\bi've\s+been|\bim)\s+"
          r"(?:being\s+|getting\s+|constantly\s+|repeatedly\s+|always\s+|continuously\s+|still\s+)?")

DISCLOSE: dict[str, re.Pattern] = {
    "posh": _rx(
        # English
        _I_WAS + r"(?:sexually\s+)?(?:harr?ass?ed|molested|groped|raped|assaulted|stalked|fondled|flashed|touched)\b",
        r"\b(?:sexually\s+)?harr?ass?(?:es|ed|ing)?\s+me\b",
        r"\bharr?ass?ed\s+(?:by|from)\s+(?:my|a|an|the|his|her|one\s+of|two|some|our)\b",
        r"\bharr?ass?ment\s+(?:by|from)\s+(?:my|our|his|her|one\s+of\s+my)\b",
        r"\b(?:facing|faced|face|experiencing|experienced|suffering|suffered|going\s+through|went\s+through|victim\s+of|"
        r"subjected\s+to|survivor\s+of|dealing\s+with)\s+(?:sexual\s+)?(?:harr?ass?ment|abuse|assault|misconduct)\b",
        r"\b(?:molest|grop|fondl|rap|assault|stalk|kiss|lick|touch)\w*\s+me\b",
        r"\b(?:grabbed|grabs|grabbing|flashed|flashes|flashing)\s+me\b",
        r"\b(?:posh|harr?ass?ment|sexual\s+harr?ass?ment)\s+(?:complaint|case)\s+against\s+(?:my|a|an|the|our|this|that|his|her)\b",
        r"\b(?:molested|groped|raped|stalked)\b",
        r"\bforc(?:ed|es|ing|e)\s+(?:himself|herself|themselves)\s+(?:on|upon)\s+me\b",
        r"\bforc(?:ed|es|ing|e)\s+me\s+to\s+(?:kiss|have\s+sex|sleep|touch|undress|sit\s+on)",
        r"\b(?:kissed|hugged|touched|grabbed|held|pulled)\s+me\s+(?:\w+\s+){0,2}?(?:without|against)\s+(?:my\s+)?"
        r"(?:consent|will|permission)\b",
        r"\btouch(?:es|ed|ing)?\s+(?:me\s+on\s+)?my\s+" + _BODY + r"\b",
        r"\b(?:comment|comments|commented|commenting|remark|remarks|remarked|joke|jokes|joked)\s+(?:on|about)\s+my\s+"
        + _BODY + r"\b",
        # sent to the person ("sent me", not the request "send me the ... policy")
        r"\b(?:sends|sent|sending|shows|showed|showing|forwards|forwarded|forwarding|texts|texted|texting)\s+me\s+"
        r"(?:\w+\s+){0,2}?(?:obscene|explicit|vulgar|dirty|nude|naked|sexual|porn\w*|lewd|indecent)\b"
        r"(?!\s+(?:\w+\s+)?(?:policy|policies|training|form|forms|deck|document|documents|consent|guidelines?|contracts?|"
        r"clauses?|terms|agreements?|instructions?|requirements?|answers?|repl(?:y|ies)|responses?|deadlines?|statements?|"
        r"confirmations?|approvals?|permissions?|warnings?|feedback|list|summary|note|notes|reminders?|"
        r"handbook|material|module|course|act)\b)",
        r"\bpictures?\s+of\s+(?:his|her|their)\s+(?:private\s+parts?|genitals?|body)\b",
        r"\b(?:showed|shows|showing|exposed|exposes|exposing|flashed|flashes|flashing)\s+(?:me\s+)?(?:his|her|their)\s+"
        r"(?:private\s+parts?|genitals?)\b",
        # conduct someone does, or aims at the person
        _ACTOR + r"\s+(?:\w+\s+){0,3}?" + _DOES + _THING + r"(?:\w+\s+)?" + _CONDUCT,
        _CONDUCT + r"\s+(?:\w+\s+){0,3}?(?:about|towards?|at|on|against)\s+me\b",
        r"(?<!\bif\si\s)(?<!\bwhen\si\s)\b(?:getting|receiving|received|receive|got|get|gets)\s+(?:\w+\s+){0,2}?"
        + _CONDUCT + r"(?:\s+\w+){0,4}?\s+(?:from|by)\s+" + _ACTOR,
        # something at work offered or threatened for a sexual act: quid pro quo, the POSH Act's own example
        r"\b(?:rating|ratings|raise|hike|promotion|promote|increment|job|bonus|appraisal|confirmation|onsite|project|"
        r"fire|sack|terminate|transfer|demote)\b(?:\s+\S+){0,6}?\s+if\s+i\s+" + _SEXUAL_ACT,
        r"\bif\s+i\s+" + _SEXUAL_ACT + r"(?:\s+\S+){0,8}?\s+(?:rating|raise|hike|promot\w*|increment|job|bonus|"
        r"appraisal|confirm\w*|onsite|project|fire|sack|terminat\w*|transfer|demot\w*)\b",
        r"\b(?:stares?|stared|staring|leers?|leered|leering|ogles?|ogled|ogling)\s+(?:at\s+)?my\s+" + _BODY + r"\b",
        r"\b(?:leers?|leered|leering|ogles?|ogled|ogling)\s+at\s+me\b",
        r"\b(?:exposed|exposes|exposing|flashed|flashes|flashing)\s+(?:himself|herself|themselves)\b",
        r"\b(?:made|makes|making|make)\s+(?:a\s+)?pass(?:es)?\s+at\s+me\b", r"\bhit(?:s|ting)?\s+on\s+me\b",
        r"\basked\s+me\s+(?:out|to\s+sleep|for\s+sex|for\s+sexual|for\s+(?:sexual\s+)?favou?rs?|to\s+come\s+to\s+"
        r"(?:his|her|their)\s+(?:room|hotel|house|flat|place))",
        # Devanagari Hindi
        _DB + r"(?:मुझे|मुझको)\s+(?:\S+\s+){0,3}?(?:छेड़|छेड|छुआ|छूआ|छूता|छूती|छूने|गलत\s+तरीके)",
        _DB + r"मेरे\s+साथ\s+(?:\S+\s+){0,3}?(?:छेड़|छेड|उत्पीड़न|उत्पीडन|अश्लील)",
        _DB + r"गलत\s+(?:तरीके|तरह|जगह)\s+से\s+(?:छु|छू)", _DB + r"(?:गंदे|गंदा|गंदी|अश्लील)\s+(?:मैसेज|मेसेज|संदेश|फोटो|फ़ोटो|तस्वीर|तस्वीरें|वीडियो|बातें|कमेंट|इशारे)", _DB + r"यौन\s+(?:उत्पीड़न|उत्पीडन|शोषण)\s+(?:का|की)\s+(?:सामना|शिकार)",
        # Hinglish
        r"\b(?:mujhe|mujhko|muje|mjhe|mere\s+saath|mere\s+sath|meri\s+saath)\s+(?:\w+\s+){0,3}?(?:chhed\w*|"
        r"ched(?:khani|chhad|chad)\w*|chh?u(?:a|ya|ye|i|ne)?\b|chhoo\w*|(?:touch|kiss|hug)\s+(?:kiya|kar\w*)|gand[aei]\s|"
        r"galat\s+(?:jagah|tarike|tareeke)|ashleel\w*)",
        r"\bgalat\s+(?:tarike|tareeke|tarah|jagah)\s+(?:se\s+)?(?:chhu|chu|chhoo|choo|touch)\w*",
        r"\b(?:ne|by)\s+(?:mujhe|mujhko|muje|mjhe)\s+(?:\w+\s+){0,2}?(?:kiss|hug|touch)\s+(?:kiya|ki|kar\s+(?:liya|diya))\b",
        r"\bharr?ass?(?:ment)?\s+(?:ho\s+raha|ho\s+rahi|ho\s+rahe|hua|hui|kar\s+raha|kar\s+rahi|kar\s+rahe|karta|karti|"
        r"karte|kiya|ki)\b",
        r"\bchhed\w*\s+(?:raha|rahi|rahe|karta|karti|karte|kiya|ki)\b",
        r"\bgand[aei]\s+(?:message|messages|msg|msgs|photo|photos|pic|pics|comment|comments|jokes?|video|videos|baat|"
        r"baatein|ishare|ishaare|ishara)\b",
        r"\b(?:body|kapdon|kapdo|kapde|figure|shakal)\s+(?:pe|par|pr)\s+(?:comment|comments|remark|remarks)\b",
    ),
    "grievance": _rx(
        # English
        # a complaint about a person, or against the company - not about its policy, process or system
        r"\b(?:grievance|complaint|complain|complaining|complained)\s+(?:against|about)\s+(?:my|our|the|a|an|this|that|his|"
        r"her)?\s*(?:\w+\s+){0,2}?(?:" + _WHO[3:-1] + r"|him|her|them)\b" + _NOT_A_RULE,
        r"\b(?:grievance|complaint|complain|complaining|complained)\s+against\s+(?:my|our|the|this)?\s*"
        r"(?:employer|company|management|hr)\b" + _NOT_A_RULE,
        r"\b(?:bull(?:y|ies|ied|ying)|humiliat\w*|threaten\w*|abus(?:e|es|ed|ing)|insult\w*|victimi[sz]\w*|"
        r"target(?:s|ed|ing)|torment\w*|intimidat\w*|belittl\w*|mock(?:s|ed|ing)|ridicul\w*|scold\w*|demean\w*|"
        r"sideline\w*|isolat\w*)\s+me\b",
        r"\b(?:discriminat\w*|retaliat\w*)\s+against\s+me\b",
        r"\b(?:shout|shouts|shouted|shouting|yell|yells|yelled|yelling|scream|screams|screamed|screaming|swear|swears|"
        r"swore|cursed?|curses)\s+at\s+me\b",
        r"\bthreaten\w*\s+to\s+(?:fire|sack|terminate|transfer|demote|dismiss|suspend)\s+me\b",
        _I_WAS + r"(?:bullied|humiliated|threatened|abused|insulted|victimi[sz]ed|targeted|discriminated(?:\s+against)?|"
        r"retaliated\s+against|singled\s+out|passed\s+over|treated\s+unfairly|unfairly\s+(?:treated|dismissed|terminated|"
        r"fired|sacked|rated|transferred|demoted)|mistreated|sidelined|demoted|denied\s+(?:a\s+|my\s+)?promotion|"
        r"punished|shouted\s+at|yelled\s+at|verbally\s+abused|ostracised|ostracized|excluded|left\s+out)\b",
        r"\b(?:because|since|after)\s+i\s+(?:had\s+)?(?:complained|reported|raised|filed|lodged)\b(?:\s+\w+){0,4}?\s+"
        r"(?:complaint|grievance|harr?ass\w*|misconduct|discriminat\w*|against|about\s+(?:my|our|the|a|an|his|her)\s+"
        r"(?:\w+\s+){0,2}?" + _WHO + r")\b",
        r"\b(?:because|since|after)\s+i\s+(?:had\s+)?(?:spoke\s+up|blew\s+the\s+whistle)\b",
        _ACTOR + r"\s+(?:\w+\s+){0,2}?(?:gave|gives|giving|given|has\s+given|had\s+given)\s+me\s+(?:a\s+|an\s+|the\s+)?"
        r"(?:\w+\s+)?unfair(?:ly\s+low)?\s+(?:\w+\s+)?(?:appraisal|rating|review|warning|transfer|treatment|evaluation|"
        r"score|feedback|increment|hike)\b",
        # Devanagari Hindi
        _DB + r"(?:के|की)\s+(?:खिलाफ|ख़िलाफ़|ख़िलाफ|विरुद्ध)\s+(?:\S+\s+){0,2}?शिकायत",
        _DB + r"(?:मुझे|मुझको)\s+(?:\S+\s+){0,3}?(?:धमकी|धमका|गाली|गालियाँ|परेशान\s+(?:कर|किया)|ज़लील|जलील)",
        _DB + r"मेरे\s+साथ\s+(?:\S+\s+){0,2}?(?:भेदभाव|बुरा|गलत|बदतमीज़ी|बदतमीजी|अन्याय)",
        _DB + r"(?:मेरा|मेरी)\s+(?:\S+\s+){0,2}?(?:अपमान|बेइज़्ज़ती|बेइज्जती)",
        # Hinglish
        r"\b" + _WHO_HG + r"\s+(?:\w+\s+)?(?:ki|ke\s+(?:khilaf|khilaaf|against))\s+(?:shikayat|shikayaat|complaint)\s+"
        r"(?:karni|karna|krni|krna|darj|karunga|karungi|kar\s+(?:di|diya|raha|rahi|rahe|chuka|chuki))\b",
        r"\b(?:mujhe|mujhko|muje|mjhe)\s+(?:\w+\s+){0,3}?(?:dhamki|dhamka\w*|gaali|gaaliyan|galiyan|gali\s+de\w*|"
        r"pareshan\s+kar\w*|tang\s+kar\w*|zaleel|jaleel|torture)",
        r"\b(?:mere|meri)\s+(?:saath|sath)\s+(?:\w+\s+){0,2}?(?:bhed\s?bhav|bhedbhaav|galat|bura|badtameezi|badtamizi|"
        r"nainsafi|naainsaafi|anyay|partiality|discrimination)",
        r"\b(?:meri|mera)\s+(?:beizzati|beizzat\w*|bezzati|beijjati|apmaan|insult)\b",
    ),
    "privacy_request": _rx(
        r"\bwhat\s+(?:all\s+)?(?:personal\s+)?(?:data|information|details|info)\s+(?:(?:do|does)\s+)?(?:you|the\s+company|"
        r"acme|my\s+employer|the\s+employer|hr|they|documind)\s+(?:have|hold|keep|store|process|collect|has|holds|keeps|"
        r"stores)\s+(?:about|on|of)\s+me\b",
        r"\b(?:delete|erase|remove|wipe|purge)\s+(?:all\s+)?(?:of\s+)?my\s+(?:personal\s+)?(?:data|details|information|"
        r"info|records?|profile)\s+(?:from|in|on|off)\s+(?:your|the\s+company's|acme's|documind's|all\s+your)\b",
    ),
    "exit_dues": None,          # three parts, below: an exit, money owed, and that it has not come
    "human_requested": _rx(
        # English
        r"\b(?:talk|speak|chat)\s+(?:to|with)\s+(?:a\s+|an\s+|some\s+|the\s+|your\s+)?(?:human|person|real\s+person|"
        r"someone|somebody|actual\s+person|live\s+agent|human\s+agent|agent|representative|hr|hr\s+person|people\s+team|"
        r"hr\s+team|operator)\b",
        r"\b(?:connect|transfer|put|forward|route|hand|pass)\s+me\s+(?:through\s+|over\s+|on\s+)?(?:to|with)\s+(?:a\s+|an\s+|"
        r"some\s+|the\s+|your\s+)?(?:human|person|real\s+person|someone|somebody|hr|agent|live\s+agent|human\s+agent|"
        r"representative|people\s+team|operator)\b",
        r"\bescalate\s+(?:this|it|my\s+\w+|the\s+\w+)?\s*to\s+(?:a\s+|an\s+|the\s+)?(?:human|person|real\s+person|"
        r"someone|hr|people\s+team)\b",
        r"\b(?:want|need|like|get\s+me|give\s+me)\s+(?:to\s+(?:reach|have)\s+)?(?:a|an|some)\s+(?:human|real\s+person|"
        r"human\s+agent|live\s+agent|actual\s+person|human\s+being)\b",
        r"\b(?:help|answer|reply|response)\s+from\s+(?:a|an|some|the)\s+(?:human|real\s+person|actual\s+person|"
        r"human\s+being)\b",
        r"\bhuman\s+(?:agent|please|pls|plz)\b",
        # Devanagari Hindi
        _DB + r"(?:किसी\s+)?(?:इंसान|व्यक्ति|आदमी|एचआर|HR|hr)\s+से\s+बात", _DB + r"किसी\s+से\s+बात",
        # Hinglish
        r"\b(?:kisi\s+)?(?:insaan|insan|vyakti|aadmi|bande|banda|hr|real\s+person|person)\s+se\s+baat\b",
        r"\bkisi\s+se\s+baat\b",
    ),
}

PROCESS: dict[str, re.Pattern] = {
    "posh": _rx(
        r"\b(?:posh|harr?ass?ment|sexual\s+harr?ass?ment|internal\s+committee|icc|ic)\s+(?:complaint|case)\b",
        r"\bposh\b.*\b(?:complaint|case)\b",
        r"\b(?:report|reporting|raise|file|lodge|complain\s+about)\s+(?:a\s+case\s+of\s+|an?\s+incident\s+of\s+)?"
        r"(?:sexual\s+)?harr?ass?ment\b",
        r"\bsexual(?:ly)?\s+(?:harr?ass?\w*|assault\w*|advances?|remarks?|comments?|jokes?|favou?rs?|innuendo|"
        r"misconduct|abuse\w*)",
        r"\binappropriate(?:ly)?\s+(?:touch\w*|contact|comments?|remarks?|messages?|photos?|pictures?|behaviou?r|advances?)",
        r"\bunwelcome\s+(?:touch\w*|advances?|contact|comments?|remarks?|messages?|attention|behaviou?r)",
        r"\b(?:obscene|explicit|vulgar|nude|naked|porn\w*|lewd|indecent)\s+(?:messages?|texts?|pictures?|pics?|photos?|"
        r"images?|videos?|jokes?|calls?|comments?|remarks?|gestures?|emails?|memes?)\b",
        r"\bstalker\b",
        # Devanagari Hindi
        _DB + r"यौन", _DB + r"उत्पीड़न", _DB + r"उत्पीडन", _DB + r"छेड़छाड़", _DB + r"अश्लील",
        # Hinglish
        r"\bharr?ass?\w*\s+(?:report|complaint|ki\s+shikayat)\b", r"\bched(?:khani|chhad|chad)\w*", r"\bchhedchhad\w*",
        r"\bashleel\w*",
    ),
    "grievance": _rx(
        # English
        r"\b(?:raise|file|lodge|submit|register|bring)\s+(?:a\s+|my\s+|an?\s+formal\s+)?grievance\b",
        r"\bmy\s+grievance\b",
        r"\bmy\s+complaint\s+(?:against|about\s+(?:my|our|the|a|an|his|her)\s+(?:\w+\s+){0,2}?" + _WHO + r"\b)",
        r"\b(?:raise|file|lodge|submit|register|make)\s+(?:a\s+|my\s+|an?\s+formal\s+)?complaint\s+(?:with|to)\s+"
        r"(?:the\s+)?(?:hr|grc|grievance|committee|people\s+team|management|my\s+manager|ethics|ombuds\w*)\b"
        r"(?!\s+(?:about|regarding|on|over|for)\s+(?:the\s+|our\s+|a\s+|an\s+|this\s+|that\s+|my\s+)?(?:[\w'-]+\s+){0,3}?"
        + _THINGS + r"\b)",
        r"\b(?:discriminat\w*|retaliat\w*|victimi[sz]ation|bullying)\s+(?:by|from|at\s+the\s+hands\s+of)\s+(?:my|a|the)\b",
        r"\bunfair(?:ly)?\s+(?:treated|treatment|dismiss\w*|terminat\w*|fired|sacked|rating|appraisal|warning|transfer\w*)",
        r"\bhostile\s+(?:work\s+environment|behaviou?r)",
        # Devanagari Hindi
        _DB + r"(?:मेरी|मेरा)\s+शिकायत",
        _DB + r"(?:मैनेजर|बॉस|सीनियर|लीड|टीम\s+लीड|सहकर्मी|सुपरवाइज़र|सुपरवाइजर|अधिकारी|एचआर|HR|hr)\s+(?:\S+\s+)?(?:की|के)\s+"
        r"(?:खिलाफ\s+|ख़िलाफ़\s+)?शिकायत",
        _DB + r"भेदभाव",
        _DB + r"धमकी", _DB + r"अपमान", _DB + r"गाली",
        # Hinglish
        r"\b(?:meri|mera)\s+(?:shikayat|shikayaat)\b", r"\bbhed\s?bhav\w*", r"\bdhamki\w*", r"\bbeizzat\w*", r"\bbezzati\w*",
        r"\bapmaan\w*", r"\bgaali\w*", r"\bpareshan\s+(?:kar|kiya|karta|karti|karte)\w*",
        r"\bgrievance\s+(?:dalni|dalna|daalni|daalna|file|raise)\b",
    ),
    "privacy_request": _rx(
        # English
        r"\b(?:delete|erase|remove|wipe|purge|destroy)\s+(?:all\s+)?(?:of\s+)?my\s+(?:personal\s+)?(?:data|details|"
        r"information|info|records?|profile)\b(?!\s+(?:from|on|off)\s+(?:it|them|there)\b)(?!\s+(?:from|on|off)\s+(?:the\s+|my\s+|this\s+|that\s+|an?\s+|our\s+)?"
        r"(?:old\s+|work\s+|office\s+|company\s+|personal\s+|new\s+)?(?:laptop|phone|mobile|device|computer|pc|desktop|"
        r"drive|disk|machine|browser|tablet|pen\s*drive|usb|hard\s*disk|sim)\b)",
        r"\berasure\s+of\s+my\b", r"\bmy\s+(?:personal\s+)?data\s+(?:deleted|erased|removed)\b",
        r"\bcopy\s+of\s+(?:all\s+)?my\s+(?:personal\s+)?(?:data|information|details|records)\b",
        r"\b(?:access|see|view|get)\s+(?:all\s+)?my\s+personal\s+(?:data|information|details)\b",
        r"\b(?:correct|update|fix|rectify)\s+my\s+personal\s+(?:data|details|information)",
        r"\b(?:withdraw|revoke)\s+(?:my\s+)?consent\b(?!\s+(?:to|for)\s+(?:the\s+|my\s+|a\s+|an\s+)?(?:relocat\w*|"
        r"transfer\w*|travel\w*|overtime|night\s+shifts?|shift\s+change|work\w*|join\w*|deputation|secondment|move|moving|"
        r"posting|bond|non-?compete|arbitration|deduction\w*|salary\s+deduction\w*))",
        r"\b(?:stop|object\s+to)\s+(?:processing|using|sharing)\s+my\s+(?:personal\s+)?(?:data|details|information)",
        # Devanagari Hindi
        _DB + r"(?:मेरा|मेरी|मेरे)\s+(?:डेटा|डाटा|जानकारी|विवरण)(?:\s+\S+){0,4}?\s+(?:हटा|मिटा|डिलीट)",
        _DB + r"(?:मेरा|मेरी|मेरे)\s+(?:डेटा|डाटा|जानकारी)\s+(?:की|का)\s+(?:कॉपी|प्रति)",
        _DB + r"सहमति\s+वापस",
        # Hinglish
        r"\b(?:mera|meri|mere)\s+(?:data|details|jankari|jaankari|info)(?:\s+\w+){0,4}?\s+(?:delete|hata|hatao|hatana|mita|"
        r"mitao|remove|erase)\w*",
        r"\b(?:mera|meri|mere)\s+(?:data|details|jankari|jaankari|info)\s+(?:kya|kaunsa|kaun\s+sa|kitna)\b",
        r"\bconsent\s+(?:wapas|vapas|withdraw)\w*",
    ),
    "exit_dues": None,
    "human_requested": None,
}
TOPICS = {cls: [p for p in (DISCLOSE[cls], PROCESS[cls]) if p is not None] for cls in CLASSES}

# exit_dues: something a leaver is owed, that the person left, and that it has not been paid - and the leaving has
# happened ("If I resign, is my gratuity withheld?" asks how the rule works).
_EXIT_MONEY = _rx(
    r"\bfull\s*(?:and|&|n)\s*final\b", r"\bf\s*&\s*f\b", r"\bfnf\b", r"\bf\s+and\s+f\b",
    r"\bfinal\s+(?:settlement|dues|salary|pay|payment)\b", r"\b(?:exit|settlement|separation)\s+dues\b",
    r"\bgratuity\b", r"\bleave\s+encashment\b", r"\bnotice\s+(?:period\s+)?pay\b",
    _DB + r"(?:फुल\s+एंड\s+फाइनल|अंतिम\s+(?:भुगतान|वेतन)|ग्रेच्युटी|आखिरी\s+(?:सैलरी|वेतन|तनख्वाह)|बकाया)",
    r"\b(?:aakhri|aakhiri|akhri)\s+(?:salary|tankhwah|tankha|payment)\b", r"\bbakaya\b",
)
_EXIT_CONTEXT = _rx(
    r"\b(?:resigned|quit|relieved|retrenched|laid\s+off|terminated|dismissed|separated)\b",
    r"\b(?:since|after|when|before)\s+i\s+(?:had\s+)?left\b",
    r"\bi\s+(?:had\s+)?left\s+(?:the|acme|in|on|last|my|this|that|work|office|\d)",   # not "do i have left"
    r"\bleft\s+(?:the\s+)?(?:company|organisation|organization|job|firm|acme)\b",
    r"\blast\s+working\s+day\b", r"\blwd\b", r"\bexit(?:ed)?\b", r"\bresignation\b", r"\bserved\s+(?:my\s+)?notice\b",
    _DB + r"(?:नौकरी\s+छोड़|इस्तीफा|इस्तीफ़ा|आखिरी\s+कार्य\s+दिवस)",
    r"\b(?:naukri|job|company)\s+(?:chhod|chod|chhodi|chodi)\w*", r"\bresign\s+(?:kiya|kar\s+diya|de\s+diya)\b",
    r"\b(?:resign|resignation|relieving|lwd)\s+(?:ke|k)\s+(?:baad|bad)\b", _DB + r"(?:इस्तीफे|इस्तीफ़े|रिज़ाइन|रिजाइन)",
)
_GENERIC_MONEY = _rx(r"\b(?:salary|wages|dues|payment|pay|money|settlement)\b",
                     _DB + r"(?:वेतन|सैलरी|पैसे|पैसा|भुगतान)", r"\b(?:paisa|paise|tankhwah|tankha|payment)\b")
_OWED = (r"(?:salary|wages|dues|payment|pay|money|settlement|amount|gratuity|f\s*&\s*f|fnf|full\s*(?:and|&|n)\s*final|"
         r"encashment|bonus|reimbursement)")
_NOT_PAID = _rx(
    r"\b(?:not|never)\s+(?:been\s+|yet\s+)?(?:paid|received|credited|settled|released|processed|cleared)\b",
    r"\b(?:hasn't|has\s+not|haven't|have\s+not|hadn't|didn't|did\s+not|wasn't|isn't|aren't)\s+(?:yet\s+)?(?:been\s+)?(?:paid|received|got|get|credited|settled|released|processed|cleared|come|arrived)\b",
    r"\bstill\s+(?:not|no|nothing|waiting|pending|unpaid|haven't|hasn't|don't|doesn't|have\s+not|has\s+not)\b",
    r"\b(?:unpaid|overdue|withheld|delayed)\b",
    # "pending" and "outstanding" only of the money ("I have 20 pending leaves", "my appraisal was outstanding")
    r"\b(?:pending|outstanding)\s+(?:\w+\s+)?" + _OWED + r"\b",
    r"\b" + _OWED + r"\b(?:\s+\w+){0,4}?\s+(?:is|are|was|were|still|remains?|remained|been|lying|kept)\s+(?:\w+\s+)?"
    r"(?:pending|outstanding)\b",
    r"\byet\s+to\s+(?:be\s+paid|receive|get|be\s+credited|be\s+settled)\b",
    r"\b(?:is|are|was|were|been|running)\s+(?:\w+\s+){0,3}?late\b", r"\b(?:days?|weeks?|months?)\s+late\b",
    r"\bno\s+(?:sign|news|update)\s+of\b", r"\b(?:holding|withholding|held)\s+(?:back\s+)?my\b",
    _DB + r"(?:नहीं\s+(?:मिला|मिली|मिले|आया|आई|आए|हुआ|हुई)|अभी\s+तक\s+नहीं|बाकी\s+है|रोक)",
    r"\b(?:nahi|nahin|nhi)\s+(?:mila|mili|mile|aaya|aayi|aya|ayi|aaye|hua|hui|diya|di)\b", r"\babhi\s+tak\s+(?:nahi|nahin|nhi)\b",
    r"\b(?:pending|baaki|baki)\s+(?:hai|he|h)\b", r"\b(?:roka|roki|rok\s+(?:diya|di|rakha|rakhi))\b",
)
# Leaving that has not happened yet, or a rule asked about; and leaving that has.
_EXIT_IF = _rx(r"\b(?:if|when|once|after|before|should|suppose)\s+i\s+(?:resign|leave|quit|exit|serve|retire|"
               r"get\s+(?:terminated|fired|laid\s+off|relieved|dismissed)|am\s+(?:terminated|fired|laid\s+off|relieved|dismissed))\b",
               r"\bwhat\s+happens\s+if\b", r"\b(?:if|agar)\s+(?:main|mai|मैं)\b",
               r"\b(?:if|in\s+case|suppose)\s+(?:my|the|a)\s+(?:\S+\s+){0,4}?(?:is|are|was|were|gets?|isn't|aren't|hasn't|"
               r"doesn't|is\s+not|has\s+not)\b")
_EXIT_DONE = _rx(r"\bi\s+(?:have\s+|had\s+)?(?:resigned|left|quit|retired|was\s+(?:terminated|fired|laid\s+off|relieved|"
                 r"dismissed|retrenched))\b", r"\bmy\s+last\s+working\s+day\s+was\b", r"\bsince\s+i\s+left\b")


def _exit_dues(t: str) -> bool:
    if not _NOT_PAID.search(t):
        return False
    if _EXIT_IF.search(t) and not _EXIT_DONE.search(t):
        return False
    return bool(_EXIT_MONEY.search(t) or (_GENERIC_MONEY.search(t) and _EXIT_CONTEXT.search(t)))


# A request for a person is first person by its grammar even when it names no "I": "Talk to a human, please", and
# Hinglish and Hindi, which drop the pronoun ("HR se baat karni hai").
_HUMAN_IMPERATIVE = _rx(
    r"^(?:(?:hi|hello|hey)\b[\s,.!]*)?(?:please\s+|pls\s+|plz\s+|can\s+i\s+|could\s+i\s+|let\s+me\s+)?(?:talk|speak|connect\s+me)\s+(?:to|with)\s+"
    r"(?:a\s+|an\s+|some\s+)?(?:human|person|real\s+person|someone|somebody|agent|representative)\b",
    r"^(?:(?:hi|hello|hey)\b[\s,.!]*)?(?:please\s+|pls\s+|plz\s+|kindly\s+)?escalate\b",
    r"\b(?:insaan|insan|hr|kisi|person|bande|banda|vyakti|aadmi)\s+se\s+baat\s+(?:karni|karna|karwa\w*|karva\w*|karao|kara\s+do)\b",
    _DB + r"(?:इंसान|व्यक्ति|आदमी|एचआर|hr|किसी)\s+से\s+बात\s+(?:करनी|करना|कराओ|कराइए|करवाओ|करवाइए|करवा)",
)


# Asking whether or when to talk to someone is a question, not a request: "Should I talk to HR before resigning?",
# "Do I need a human being to witness my form?". "Can I talk to a human?" asks for one; "Can I speak to HR
# anonymously about a payroll error?" asks how the process works - so "can I" counts as a request only when nothing
# follows the person asked for.
_HUMAN_ADVICE = _rx(
    r"\b(?:should|must|shall|do|does|would|will|need)\s+i\s+(?:\w+\s+){0,2}?(?:talk|speak|chat|contact|need|have|go|"
    r"approach|reach)\b",
    r"\b(?:when|whom|who|why|whether|if)\s+(?:\w+\s+){0,2}?(?:i|we|one|employees?|staff)\s+(?:\w+\s+){0,2}?"
    r"(?:talk|speak|chat|contact|need)\b",
    r"\b(?:can|could|may)\s+i\s+(?:\w+\s+){0,1}?(?:talk|speak|chat)\s+(?:to|with)\s+(?:a\s+|an\s+|some\s+|the\s+|your\s+)?"
    r"(?:\w+\s+){0,2}?(?:human|person|someone|somebody|agent|representative|hr|team|operator)\b"
    r"(?!\s*(?:please|pls|plz|now|right\s+now|today|instead|asap)?\s*[?.!]*\s*$)",
)


_FORMAT = re.compile("[\u00ad\u200b-\u200f\u2060\ufeff]")    # soft hyphen, zero-width characters, marks, BOM


def normalise(question: str) -> str:
    """Format characters dropped, NFKC, lower case, one kind of apostrophe, one space."""
    t = unicodedata.normalize("NFKC", _FORMAT.sub("", question or "")).lower()
    t = t.replace("’", "'").replace("‘", "'").replace("`", "'")
    return re.sub(r"\s+", " ", t).strip()


def _fires(cls: str, t: str) -> bool:
    if cls == "exit_dues":
        return _exit_dues(t)
    if cls == "human_requested":
        return bool(DISCLOSE[cls].search(t) and (REQUEST.search(t) or not _HUMAN_ADVICE.search(t)))
    if DISCLOSE[cls].search(t):
        return True
    step = PROCESS[cls]
    return bool(step is not None and step.search(t) and (REQUEST.search(t) or not _info(t)))


# A member of the committee, or of HR, asking about a complaint they received speaks in the first person about
# their role, not about something done to them: "I am on the ICC. We received a complaint against a senior ...".
# Then posh and grievance fire only on a sign the person is the one it happened to.
_ON_COMMITTEE = re.compile(r"\b(?:i\s+am|i'm|im)\s+(?:on|in|part\s+of|a\s+member\s+of|an?\s+(?:member|presiding\s+officer)\s+"
                           r"of|the\s+presiding\s+officer\s+of|an?)\s+(?:the\s+|our\s+|an?\s+)?(?:ic|icc|internal\s+(?:complaints?\s+)?"
                           r"committee|posh\s+committee|grc|grievance\s+(?:redressal\s+)?committee|ethics\s+committee|hr|hr\s+team|"
                           r"people\s+team|hrbp|hr\s+manager|hr\s+business\s+partner)(?:\s+member)?\b")
_VICTIM = re.compile(r"\b(?:me|my|myself|mine)\b|\bi\s+(?:was|am\s+being|have\s+been|had\s+been|got|feel|felt)\b|\bi've\s+been\b")


def gate(question: str) -> str | None:
    """The gate class this question belongs to, or None. The class only: never the matched words."""
    t = normalise(question)
    if not t:
        return None
    if not (_HUMAN_IMPERATIVE.search(t) or _first_person(t)):
        return None
    role = _ON_COMMITTEE.search(t) and not _VICTIM.search(_ON_COMMITTEE.sub(" ", t))
    for cls in CLASSES:
        if role and cls in ("posh", "grievance"):
            continue
        if _fires(cls, t):
            return cls
    return None


# ---------------------------------------------------------------- the out_of_scope candidates
# An action is something only another system does; an own record is a look-up in it. Neither is in any document.
ACTIONS: dict[str, re.Pattern] = {
    "action": _rx(
        r"\b(?:apply|approve|reject|cancel|withdraw|submit|book|raise)\s+(?:for\s+)?my\s+(?:leave|claim|expense|expenses|"
        r"reimbursement|timesheet|attendance|regularisation|regularization|loan|advance|ticket|travel|request)",
        r"\b(?:apply|approve|book|submit)\s+(?:a\s+|an\s+)?(?:leave|claim|ticket|cab|flight|hotel)\s+for\s+me\b",
        r"\b(?:update|change)\s+my\s+(?:bank|account|address|phone|mobile|email|nominee|pan|tax\s+regime|shift|manager|"
        r"designation|name)\b",
        r"\breset\s+my\s+password\b", r"\bunlock\s+my\s+account\b",
        _DB + r"(?:छुट्टी|लीव)\s+(?:लगा|अप्लाई\s+कर)\s+(?:दो|दीजिए|दें)",
        r"\b(?:chhutti|chutti|leave)\s+(?:laga|apply\s+kar|approve\s+kar)\s*(?:do|dijiye|dena|de)\b",
    ),
    "own_record": _rx(
        r"\bmy\s+(?:leave|holiday)\s+balance\b", r"\bhow\s+(?:many|much)\s+(?:leaves?|days)\s+(?:do\s+i\s+have\s+left|are\s+left|have\s+i\s+taken)\b",
        r"\b(?:download|send|show|share|get)\s+(?:me\s+)?my\s+(?:payslip|pay\s+slip|salary\s+slip|form\s*16|form-16|appraisal\s+letter|offer\s+letter|attendance)\b",
        r"\bwhere\s+is\s+my\s+(?:payslip|pay\s+slip|salary\s+slip|form\s*16|form-16|reimbursement|claim|bonus|increment)\b",
        r"\b(?:status|approval\s+status)\s+of\s+my\s+(?:claim|reimbursement|leave|request|ticket)\b",
        r"\bmy\s+(?:ctc|salary\s+breakup|tax\s+deducted|pf\s+balance|uan)\b",
        _DB + r"(?:मेरी|मेरा)\s+(?:पेस्लिप|सैलरी\s+स्लिप|छुट्टी\s+का\s+बैलेंस)",
        r"\b(?:meri|mera)\s+(?:payslip|salary\s+slip|leave\s+balance|form\s*16)\b",
    ),
}


def action(question: str) -> str | None:
    """'action' or 'own_record' when the question asks for something no document holds, else None."""
    t = normalise(question)
    for kind, rx in ACTIONS.items():
        if rx.search(t):
            return kind
    return None


def near(question: str) -> bool:
    """A near-hit: a first-person marker, or any class's topic, in the question - gate() needs both, this either.
    The router (services/chat/desk_router.py) lets an identifier anchor decide a route without a model call only
    when there is none, so "Under the Code on Wages, my dues ..." still reaches the model's case check."""
    t = normalise(question)
    if not t:
        return False
    if _first_person(t) or _HUMAN_IMPERATIVE.search(t) or _exit_dues(t):
        return True
    return any(p.search(t) for patterns in TOPICS.values() for p in patterns)


# ---------------------------------------------------------------- the switch
# tenant_settings/{tenant}.desk_gate, as both doors read it (services/rag-api/desk_door.py, services/chat/desk.py):
#     rules   the default - a missing field, or any value that is not exactly one of these - gate() and mask() run
#             on every question a person sends through a door
#     on      the rules, and the model check behind them (shared/desk_recall.py) on POST /v1/chat, and on rag-api's
#             /v1/query and /v1/stream for a question with no brain label or the Chat page's "ui", for the questions
#             the rules let through
#     off     neither: the body goes through as it was sent. Only an operator's explicit "off" turns the rules off,
#             never a missing field, a typo or a failed read
# The values are read exactly as make desk writes them (lower case; True and False too), as desk_recall.read_on_tenants
# queries them: "On" or " off " is a hand edit, read as rules, so every reader agrees and an edit errs to the rules.
GATE_STATES = ("off", "rules", "on")


def gate_state(doc) -> str:
    """off, rules or on: the tenant's desk_gate as the doors apply it. rules unless the field is exactly off or on."""
    v = (doc or {}).get("desk_gate")
    if v is True:
        return "on"
    if v is False:
        return "off"
    return v if isinstance(v, str) and v in GATE_STATES else "rules"


# ---------------------------------------------------------------- masking
# No longer than the shortest number each replaces (12 digits, 13), so a masked question is never longer than the
# one rag-api's QueryRequest already accepted.
MASK_TEXT = {"aadhaar": "[Aadhaar]", "card": "[card no.]"}


def mask(question: str) -> tuple[str, list[str]]:
    """(the question with every checked Aadhaar and card number replaced, the kinds replaced, sorted). The text is
    returned unchanged, and the list empty, when there is nothing to mask."""
    found = identifiers.find_numbers(question or "")
    if not found:
        return question, []
    out, last = [], 0
    for start, end, kind in found:
        out.append(question[last:start])
        out.append(MASK_TEXT[kind])
        last = end
    out.append(question[last:])
    return "".join(out), sorted({k for _, _, k in found})
