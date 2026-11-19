#!/usr/bin/env python3
# CalliopeZED - An enhanced secondbrain for the inspiration of imaginations and ideas.
# Copyright (C) 2026 Joshua Thomas Buffone
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
META: the metadevelopment layer (section 6 of calliope.py).

ASSAY rates ideas. CHERISH holds values. META watches HOW ideas happen.

A METADEVELOPMENT is an observable pattern in how ideas arise, move or change
status (not what an idea says) that tends to precede, trigger or accompany an
unexpected breakthrough, and that the thinker has not yet named. Five families:

    EMERGENCE    something built for one purpose becomes an idea of its own
                 (the rating system grew out of rating; ASSAY forked into ASSAY-LIT;
                 a coined term keeps coming back; an idea arrives as a joke)
    IGNITION     the conditions a breakthrough came out of (a plain factual
                 question that turns into a design; a loose, relaxed register;
                 a hard constraint that forces closure; a burst of activity;
                 a word read two ways)
    INCUBATION   an idea or term goes quiet, then returns changed
                 (Freudian topology in April, the mood ring in October)
    REFRAMING    a thing is reclassified and gains value (a long practice is
                 recognized as research; ideas rate higher framed as instruments;
                 the weakest idea turned inside out becomes a feature)
    REFLEXIVITY  attention shifts from the idea to the process making it
                 (method talk, designing while using, deliberate channel
                 techniques like handshake errors, ideas born in a chat about
                 something else)

THE LOOP (detection with consent; the Ignition Engine's core loop)
    detect  scanners and the agent log CANDIDATES quietly
    ask     candidates are offered as questions in a batch, at a pause
    store   user_name confirms, rejects or parks; every answer goes in the CASEBOOK,
            which calibrates the detectors (precision per detector)
    develop a confirmed observation is promoted to a TRAIT (a named ignition
            pattern with a re-trigger recipe) or to an IDEA (an ASSAY template)

Nothing is confirmed, promoted or developed without user_name saying so.

IN CHAT
    The agent: watch quietly for metadevelopments; log each with  meta log;
    don't interrupt the flow. At a natural pause or session end, run
    meta review and offer the batch. A message containing  /meta  means:
    run  python calliope.py meta review  now. Full protocol: meta prompt.

USAGE (prefix: python calliope.py meta)
    families                        the five families and their detectors
    scan [--since YYYY-MM-DD]       run detectors on the archive, store new candidates
    log DETECTOR "subject" "evidence" [--by agent|user]   record a candidate live, in chat
    review [N]                      the next batch of candidates, as questions
    confirm ID ["note"] | reject ID ["why"] | park ID ["note"]   answer a candidate; every answer feeds the casebook
    promote ID trait "Name" "stimulus scheme in user_name's words"   turn a confirmed observation into a trait record
    promote ID idea                 ASSAY template seeded from the observation
    trait ID retrigger|scheme|counter "text"   add a re-trigger recipe, scheme note or counter-example to a trait
    show [ID]                       observations (or one, in full)
    traits                          the trait records
    casebook                        detector precision and muted detectors
    report [--out f.md]             the metadevelopment report
    prompt                          the in-chat protocol for the agent
    vitals form                     the RN's check-in questionnaire (registry: The RN)
    vitals log key=value ...        document one check-in (any subset of the form's keys); local only, in health/
    vitals show [N]                 recent check-ins
    vitals later "when" | vitals done   set or clear the re-prompt reminder
    selftest                        run this engine's self-tests

Local and heuristic: patterns over the chat archive, both ledgers and the
CHERISH state. Standard library only.
"""

import json, os, re, sys, datetime, collections, statistics

VERSION = "meta-1.0"
ARCHIVES = ("calliope_archive.json",)
TODAY = lambda: datetime.date.today().isoformat()

# Injected by the calliope.py launcher; stand-ins let the engine run alone.
ENGINES = lambda name: None
LOAD_ARCHIVE = lambda p: json.load(open(p, encoding="utf-8"))
CHERISH_STATE = lambda: {"triggered": []}
_STATE = {"observations": [], "traits": [], "next_id": 1, "scans": []}
load_state = lambda: json.loads(json.dumps(_STATE))
def save_state(st):
    _STATE.clear(); _STATE.update(st)
# The RN's store is separate and LOCAL-ONLY: the launcher points it at health/vitals.json, never at the state file.
_RN = {"vitals": [], "reprompt": None}
load_rn = lambda: json.loads(json.dumps(_RN))
def save_rn(rn):
    _RN.clear(); _RN.update(rn)
RN_HERE = lambda: True
RN_AWAY = ("RN data is LOCAL-ONLY: it lives in health/ beside the program in this folder. There is no "
           "health/ here, so nothing is read or saved. Don't create the folder to get around it.")

# ====================
# Detectors (the families' working parts). Weight = prior strength of one hit.
# ====================
IDEA = (r"\bwhat if\b|\bi (just )?had (the|a|an) (thought|idea)\b|\bthe idea (is|would be)\b|\bi propose\b"
        r"|\bwe could (build|make|create|use|design)\b|\bimagine (a|if)\b|\bhere'?s (my|an) idea\b"
        r"|\bi think (we|you|it) (could|should)\b|\bnew idea\b|\bwhat about (a|an|if)\b")

DETECTORS = {
    # ---- EMERGENCE
    "scaffold-promotion": dict(family="emergence", weight=0.6,
        about="A named tool or method keeps being revised across chats: it may have become its own idea.",
        ask="Has {subject} become an idea in its own right, worth rating?"),
    "fork": dict(family="emergence", weight=0.5,
        about="A method is copied into another domain.",
        pattern=r"\b(a|an) [\w-]+-(tuned|specific|flavored) version\b|\bsame (thing|idea|system) (but )?for\b"
                r"|\bversion (of (it|this|that) )?for (fiction|poetry|stories|music|art|science|business|kids)\b|\bapply (this|it|that) to\b",
        ask="Is this fork ({subject}) a sign the method is general?"),
    "coinage": dict(family="emergence", weight=0.4,
        about="A coined or scare-quoted term recurs across separate chats.",
        ask="Is \"{subject}\" a working concept worth naming and defining?"),
    "throwaway": dict(family="emergence", weight=0.35,
        about="An idea delivered as a joke or aside, guard down.",
        pattern=r"\blol\b|\blmao\b|\bhaha+\b|\bjk\b|\bhalf[- ]joking\b|\brandom thought\b|\bjust a thought\b|\bsilly idea\b|\bshower thought\b",
        ask="This aside ({subject}) carried an idea. Develop it?"),
    # ---- IGNITION
    "question-seeding": dict(family="ignition", weight=0.5,
        about="A chat opened with a plain factual question and turned into a design.",
        ask="\"{subject}\" started as a factual question and became an idea. Is curiosity-first a trigger for you?"),
    "rapid-extension": dict(family="ignition", weight=0.45,
        about="Two idea moves within minutes in one chat: an idea extending itself.",
        ask="In \"{subject}\" one idea extended into another within minutes. What made that fast?"),
    "burst": dict(family="ignition", weight=0.5,
        about="A day of unusually high activity across several chats.",
        ask="{subject} was a burst day. What were the conditions (rest, sleep, setting, mood)?"),
    "loose-register": dict(family="ignition", weight=0.4,
        about="A relaxed or spoken register immediately followed by an idea move.",
        pattern=r"\bum+\b|\buh+\b|\blol\b|\bkinda\b|\bsorta\b|\bidk\b|\byou know\b|\bi mean\b|\bsorry,? i\b|\bcomma\b",
        ask="A loose moment preceded an idea in \"{subject}\". Part of the loose-register pattern?"),
    "forcing-structure": dict(family="ignition", weight=0.4,
        about="Hard constraints (format, count, sections, deadline) set by user_name, pushing toward closure.",
        pattern=r"\busing only\b|\bin (one|two|three|four|\d) (sections?|paragraphs?|blocks?|sentences?|words?)\b|\bno more than\b"
                r"|\bexactly (\d|one|two|three)\b|\bdeadline\b|\bword limit\b|\bone single\b|\bonly (give|provide|list)\b|\bstep by step\b",
        ask="Constraints in \"{subject}\" pushed toward closure. Part of the forcing-structure pattern?"),
    "polysemy": dict(family="ignition", weight=0.5,
        about="A word deliberately read two ways.",
        pattern=r"\btwo (readings|meanings|senses)\b|\bdouble (meaning|reading|entendre)\b|\bboth senses\b|\bpun\b|\bin both ways\b|\bliterally and\b",
        ask="A double reading in \"{subject}\". Is wordplay one of your generators?"),
    # ---- INCUBATION
    "dormancy-return": dict(family="incubation", weight=0.55,
        about="A term or idea went quiet for 45+ days, then came back.",
        ask="\"{subject}\" went quiet and returned. Did it come back changed?"),
    # ---- REFRAMING
    "reclassification": dict(family="reframing", weight=0.5,
        about="Something is recognized as a different kind of thing (a practice as research, a tool as a method).",
        pattern=r"\b(i )?(just )?(realiz|recogniz)(e|ed|ing) (that )?(this|it|my)\b|\bturns out\b|\bit'?s (actually|really) (a|an)\b"
                r"|\bthis is (a|an) (method|research|practice|system|framework|discipline)\b|\breframe|\breclassif",
        ask="In \"{subject}\" something changed category. Does the new frame raise its value?"),
    "instrument-framing": dict(family="reframing", weight=0.45,
        about="An idea framed as an experiment, instrument or test rather than a product.",
        pattern=r"\b(as|like) an? (experiment|instrument|probe|test)\b|\bself as the experiment\b|\btestable\b|\bpilot test\b",
        ask="\"{subject}\" was framed as an instrument. More evidence that instruments outrank products?"),
    "inversion": dict(family="reframing", weight=0.45,
        about="An idea turned inside out (the weak version inverted into a strong one).",
        pattern=r"\binside out\b|\binver(t|sion|ted)\b|\bflip (it|this|that)\b|\bthe opposite\b|\bturn(ed)? (it|this) around\b",
        ask="An inversion in \"{subject}\". Is inverting weak ideas a move worth naming?"),
    # ---- REFLEXIVITY
    "method-talk": dict(family="reflexivity", weight=0.4,
        about="Attention shifts from the idea to the process of making it.",
        pattern=r"\bthe way we('re| are)\b|\bhow we('re| are) (building|doing|working|making)\b|\bour (process|method|workflow)\b"
                r"|\bmeta(-| )(layer|level|chat|development)s?\b|\bdesigning .{0,30}while using\b|\bco-?build",
        ask="Process came into view in \"{subject}\". Is something forming about how you work?"),
    "channel-technique": dict(family="reflexivity", weight=0.5,
        about="A deliberate move on the communication channel itself.",
        pattern=r"\b(on purpose|deliberately|intentional(ly)?|willful(ly)?) .{0,25}(error|typo|mistake|wrong)\b|\bhandshake\b",
        ask="A deliberate channel move in \"{subject}\". Name it, or add to an existing technique?"),
    "context-crossing": dict(family="reflexivity", weight=0.4,
        about="An idea born in a chat about something else.",
        ask="An idea surfaced in \"{subject}\", a chat about something else. Do side channels feed you?"),
    "value-juxtaposition": dict(family="reflexivity", weight=0.5,
        about="A CherishedValue held against an idea produced a rated result at threshold (from CHERISH).",
        ask="{subject} crossed a CherishedValue threshold. Is the result an idea to develop?"),
    "freeform": dict(family="reflexivity", weight=0.5,
        about="Logged by hand (the agent or user_name), no scanner.",
        ask="Logged observation: {subject}. Confirm?"),
}
FAMILIES = ["emergence", "ignition", "incubation", "reframing", "reflexivity"]
STOP = set("the a an and or of to in on for with is it this that i you we my your be are was as at by from not no yes "
           "but so if what how why can do just like about into than then there their they them me our".split())
COMMON_CAPS = {"PDF", "HTML", "JSON", "USA", "NOTE", "TODO", "AI", "API", "CEO", "URL", "OK", "FYI", "CSV", "UPS", "USPS", "EBT", "SNAP",
               "IMPORTANT", "LOL", "OMG", "WWII", "NATO", "CIA", "FBI", "PSA", "DIY", "BOLI", "EIN", "SSN", "GPS"}
WATCH = []   # the user's own recurring terms, watched for returns after dormancy; add them here

# ====================
# Corpus
# ====================
Msg = collections.namedtuple("Msg", "chat_id chat ts sender text i")


def _archive_path():
    env = os.environ.get("CALLIOPE_ARCHIVE")
    if env and os.path.exists(env):
        return env
    here = os.path.dirname(os.path.abspath(__file__))
    for d in (here, os.getcwd()):
        for name in ARCHIVES:
            p = os.path.join(d, name)
            if os.path.exists(p):
                return p
    return None


def load_chats(since=None):
    p = _archive_path()
    if not p:
        return {}
    arc, chats = LOAD_ARCHIVE(p), {}
    for acct in ("current_account", "old_account"):
        for c in arc.get(acct, {}).get("conversations", []):
            ms = [Msg(c["uuid"], c.get("name") or "untitled", m.get("created_at") or m.get("at") or "", m.get("sender", "?"), m["text"], 0)
                  for m in (c.get("chat_messages") or c.get("messages") or []) if m.get("text")]
            ms.sort(key=lambda m: m.ts)
            ms = [m._replace(i=i) for i, m in enumerate(ms)]
            if since:
                ms = [m for m in ms if m.ts[:10] >= since]
            if ms:
                chats[c["uuid"]] = ms
    return chats


def _snip(text, m=None, width=80):
    if m is None:
        return " ".join(text.split())[:2 * width] + ("..." if len(text) > 2 * width else "")
    a, b = max(0, m.start() - width), min(len(text), m.end() + width)
    return ("..." if a else "") + " ".join(text[a:b].split()) + ("..." if b < len(text) else "")


def _ts(s):
    try:
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")[:26].rstrip("+"))
    except Exception:
        return None


def _words(s):
    return {w for w in re.findall(r"[a-z]{4,}", s.lower()) if w not in STOP}

# ====================
# Scanners. Each yields (detector, subject, evidence, hits, first, last).
# ====================
def scan_patterns(chats):
    """Regex detectors, per chat: one candidate per detector per chat."""
    idea = re.compile(IDEA, re.I)
    out = []
    for det, spec in DETECTORS.items():
        if "pattern" not in spec:
            continue
        rx = re.compile(spec["pattern"], re.I)
        for ms in chats.values():
            human = [m for m in ms if m.sender == "human"]
            hits = []
            for k, m in enumerate(human):
                mm = rx.search(m.text)
                if not mm:
                    continue
                if det in ("loose-register",):        # must be followed by an idea move
                    nxt = human[k:k + 2]
                    if not any(idea.search(x.text) for x in nxt):
                        continue
                if det == "throwaway" and len(m.text.split()) < 8:
                    continue
                hits.append((m, mm))
            need = 2 if det == "forcing-structure" else 1
            if len(hits) >= need:
                m, mm = hits[0]
                out.append((det, ms[0].chat, [f"{x.ts[:10]} · {_snip(x.text, y)}" for x, y in hits[:3]],
                            len(hits), hits[0][0].ts[:10], hits[-1][0].ts[:10]))
    return out


def scan_structure(chats):
    idea = re.compile(IDEA, re.I)
    out = []
    by_day = collections.defaultdict(lambda: [0, set()])
    for ms in chats.values():
        human = [m for m in ms if m.sender == "human"]
        if not human:
            continue
        for m in human:
            by_day[m.ts[:10]][0] += 1; by_day[m.ts[:10]][1].add(m.chat)
        ideas = [m for m in human if idea.search(m.text)]
        first = human[0]
        # question-seeding: opens with a short question, no idea move, later an idea move
        if first.text.strip().endswith("?") and len(first.text) <= 300 and not idea.search(first.text):
            later = [m for m in ideas if m.i > first.i]
            if later:
                out.append(("question-seeding", first.chat,
                            [f"opened: {_snip(first.text)}", f"{later[0].ts[:10]} · {_snip(later[0].text)}"],
                            len(later), first.ts[:10], later[-1].ts[:10]))
        # rapid-extension: two idea moves within 20 minutes
        for a, b in zip(ideas, ideas[1:]):
            ta, tb = _ts(a.ts), _ts(b.ts)
            if ta and tb and 0 < (tb - ta).total_seconds() <= 1200:
                out.append(("rapid-extension", a.chat, [_snip(a.text), _snip(b.text)], 2, a.ts[:10], b.ts[:10]))
                break
        # context-crossing: an idea move whose words barely touch the chat's title, after the opening
        title = _words(first.chat)
        for m in ideas:
            if m is not first and title and not (_words(m.text) & title) and len(m.text.split()) >= 12:
                out.append(("context-crossing", m.chat, [_snip(m.text)], 1, m.ts[:10], m.ts[:10]))
                break
    # burst: a day well above the typical active day, across 3+ chats
    counts = [n for n, _ in by_day.values()]
    if counts:
        med = statistics.median(counts)
        for day, (n, cs) in sorted(by_day.items()):
            if n >= max(3 * med, 30) and len(cs) >= 3:
                out.append(("burst", day, [f"{n} messages across {len(cs)} chats: " + "; ".join(sorted(cs)[:5])],
                            n, day, day))
    return out


def scan_terms(chats):
    """Coinages (recurring scare-quoted or ALLCAPS terms) and dormancy-returns (watch terms plus coinages)."""
    seen = collections.defaultdict(dict)           # term -> {chat: first date}
    quote = re.compile(r"[\"\u201c]([A-Za-z][A-Za-z' -]{2,40}?)[\"\u201d]")
    caps = re.compile(r"\b([A-Z][A-Z0-9]{3,})\b")
    for ms in chats.values():
        for m in ms:
            if m.sender != "human":
                continue
            terms = {q.strip().lower() for q in quote.findall(m.text) if 1 <= len(q.split()) <= 4}
            terms |= {c.lower() for c in caps.findall(m.text) if c not in COMMON_CAPS}
            for t in terms:
                if t not in STOP:
                    seen[t].setdefault(m.chat, m.ts[:10])
    out = []
    for t, cs in seen.items():
        dates = sorted(cs.values())
        if len(cs) >= 2 and dates[0] != dates[-1]:
            out.append(("coinage", t, [f"{d} · {c}" for c, d in sorted(cs.items(), key=lambda x: x[1])[:3]],
                        len(cs), dates[0], dates[-1]))
    # dormancy-return
    watch = set(WATCH) | {o[1] for o in out}
    for t in watch:
        dates = sorted({m.ts[:10] for ms in chats.values() for m in ms
                        if m.sender == "human" and t in m.text.lower()})
        for a, b in zip(dates, dates[1:]):
            gap = (datetime.date.fromisoformat(b) - datetime.date.fromisoformat(a)).days
            if gap >= 45:
                out.append(("dormancy-return", t, [f"quiet {gap} days: {a} -> {b}", f"{len(dates)} active days in all"],
                            len(dates), dates[0], dates[-1]))
                break
    return out


def scan_ledgers():
    """scaffold-promotion from the ledgers and engines; value-juxtaposition from CHERISH."""
    out = []
    eng_idea, eng_lit = ENGINES("idea"), ENGINES("lit")
    if eng_idea and eng_lit:
        n_idea = len(eng_idea.load().get("ratings", []))
        n_lit = len(eng_lit.load().get("ratings", []))
        out.append(("fork", "ASSAY 2 -> ASSAY-LIT",
                    [f"rating engine copied into fiction ({eng_idea.RULES_VERSION} -> {eng_lit.RULES_VERSION})"],
                    1, "", ""))
        out.append(("scaffold-promotion", "the idea rating system (Richter -> ASSAY)",
                    [f"two engines, versioned rules, {n_idea + n_lit} ratings logged in all"], 2, "", ""))
    for key in CHERISH_STATE().get("triggered", []):
        parts = key.split("|")
        if len(parts) == 4:
            eng, vid, idea, ver = parts
            out.append(("value-juxtaposition", f"{idea} {ver} x {vid}", [f"CHERISH trigger via {eng} ledger"], 1, "", ""))
    return out

# ====================
# Vitals (the RN persona's check-in; the instinct layer, documented by consent)
# ====================
VITALS = [   # key, question, expected answer
    ("sleep_h", "About how many hours did you sleep last night?", "number"),
    ("sleep_q", "How rested do you feel, 1 (wrecked) to 5 (fully)?", "1-5"),
    ("mind", "How fast is your mind running, 1 (calm) to 5 (racing)?", "1-5"),
    ("meal", "How long since you last ate a real meal?", "e.g. 2h"),
    ("water", "Roughly how much water today?", "glasses"),
    ("intake", "Caffeine, nicotine, alcohol or anything else today?", "none / list"),
    ("energy", "Energy right now, 1 to 5?", "1-5"),
    ("mood", "Mood right now, 1 to 5, and one word for it?", "e.g. 3 restless"),
    ("tension", "Stress or body tension, 1 to 5? Any pain (where, 0-10)?", "e.g. 2, none"),
    ("moved", "Have you moved or been outside today?", "yes / no"),
    ("people", "Have you talked with someone in person today?", "yes / no"),
    ("setting", "Where are you and what time is it?", "e.g. home, 2am"),
    ("measured", "Optional: any device readings (heart rate, blood pressure)?", "skip ok"),
    ("env", "Optional: room temperature and humidity?", "e.g. 68F 50%"),
]
VITAL_KEYS = [k for k, _, _ in VITALS]
RED_FLAGS = ("Step out of the check-in and point to real care for: chest pain, trouble breathing, fainting, "
             "severe pain, two or more nights without sleep, or thoughts of harming yourself "
             "(988, call or text, for a mental-health crisis; 911 for an emergency).")


def vitals_form():
    lines = ["RN CHECK-IN (only after a yes to pausing; ask one at a time; any item can be skipped)", ""]
    lines += [f"  {i:2}. [{k}] {q}  ({a})" for i, (k, q, a) in enumerate(VITALS, 1)]
    lines += ["", "Close: repeat the readings in one line, log them, then offer to ask again later.",
              RED_FLAGS]
    return "\n".join(lines)


def parse_vitals(pairs):
    rec, bad = {}, []
    for p in pairs:
        k, _, v = p.partition("=")
        k = k.strip().lower()
        if not _ or k not in VITAL_KEYS:
            bad.append(p)
        else:
            rec[k] = v.strip()
    if bad:
        raise SystemExit(f"use key=value with keys {VITAL_KEYS}; not understood: {bad}")
    return rec

# ====================
# State: observations, casebook, traits
# ====================
def _key(det, subject):
    return f"{det}|{re.sub(r'[^a-z0-9]+', ' ', subject.lower()).strip()}"


def precision(st):
    book = collections.defaultdict(lambda: [0, 0])
    for o in st["observations"]:
        if o["status"] in ("confirmed", "promoted"):
            book[o["detector"]][0] += 1
        elif o["status"] == "rejected":
            book[o["detector"]][1] += 1
    return {d: (c, r, c / (c + r)) for d, (c, r) in book.items() if c + r}


def strength(det, hits, prec):
    base = min(1.0, DETECTORS[det]["weight"] * (1 + 0.25 * (hits - 1)))
    c, r, p = prec.get(det, (0, 0, None))
    if c + r >= 3:
        base *= 0.5 + p                    # the casebook sharpens or dulls the detector
    return round(min(base, 1.0), 2)


def muted(prec):
    return {d for d, (c, r, p) in prec.items() if c + r >= 4 and p < 0.25}


def merge(st, found, by="scanner"):
    prec, index, new = precision(st), {o["key"]: o for o in st["observations"]}, 0
    for det, subject, evidence, hits, first, last in found:
        k = _key(det, subject)
        o = index.get(k)
        if o:
            o["evidence"] = (o["evidence"] + [e for e in evidence if e not in o["evidence"]])[:4]
            o["hits"] = max(o["hits"], hits)
            o["last_seen"] = max(o["last_seen"], last or o["last_seen"])
            if o["status"] == "candidate":
                o["strength"] = strength(det, o["hits"], prec)
            continue
        o = dict(id=f"M{st['next_id']}", key=k, detector=det, family=DETECTORS[det]["family"], subject=subject,
                 evidence=evidence[:4], hits=hits, first_seen=first or TODAY(), last_seen=last or TODAY(),
                 strength=strength(det, hits, prec), status="candidate", note="", detected_by=by, logged=TODAY())
        st["next_id"] += 1; st["observations"].append(o); index[k] = o; new += 1
    return new


def find(st, oid):
    for o in st["observations"] + st["traits"]:
        if o["id"].lower() == oid.lower():
            return o
    raise SystemExit(f"no observation or trait {oid}")


def question(o):
    return DETECTORS[o["detector"]]["ask"].format(subject=o["subject"])


def queue(st):
    mute = muted(precision(st))
    cand = [o for o in st["observations"] if o["status"] == "candidate" and o["detector"] not in mute]
    return sorted(cand, key=lambda o: (-o["strength"], o["family"], o["id"]))

# ====================
# Output
# ====================
def report_md(st):
    obs, prec = st["observations"], precision(st)
    count = collections.Counter(o["status"] for o in obs)
    out = [f"# Metadevelopments", f"{TODAY()} · {VERSION} · " +
           ", ".join(f"{count[s]} {s}" for s in ("candidate", "confirmed", "promoted", "parked", "rejected") if count[s]), ""]
    for fam in FAMILIES:
        rows = [o for o in obs if o["family"] == fam and o["status"] in ("confirmed", "promoted", "candidate")]
        if not rows:
            continue
        out += [f"## {fam.capitalize()}", "| ID | Status | Detector | Subject | Strength | Seen |", "|---|---|---|---|---|---|"]
        for o in sorted(rows, key=lambda o: (o["status"] == "candidate", -o["strength"])):
            seen = o["first_seen"] if o["first_seen"] == o["last_seen"] else f"{o['first_seen']} -> {o['last_seen']}"
            out.append(f"| {o['id']} | {o['status']} | {o['detector']} | {o['subject'][:60]} | {o['strength']:.2f} | {seen} |")
        out.append("")
    if st["traits"]:
        out += ["## Traits (Ignition Engine records)"]
        for t in st["traits"]:
            out += [f"### {t['id']} · {t['name']} · {t['status']}", f"Stimulus scheme: {t['scheme'] or '(not yet stated)'}",
                    f"Re-trigger: {t['retrigger'] or '(not yet stated)'}", f"Evidence: {', '.join(t['evidence'])}"
                    + (f" · Counter-examples: {'; '.join(t['counter'])}" if t["counter"] else ""), ""]
    if prec:
        out += ["## Casebook", "| Detector | Confirmed | Rejected | Precision |", "|---|---|---|---|"]
        mute = muted(prec)
        for d, (c, r, p) in sorted(prec.items()):
            out.append(f"| {d}{' (muted)' if d in mute else ''} | {c} | {r} | {p:.0%} |")
        out.append("")
    bursts = [o for o in obs if o["detector"] == "burst" and o["status"] == "candidate"]
    if bursts:
        out.append(f"Note: {len(bursts)} burst day(s) have no conditions logged. Answering them feeds CHERISH's "
                   "instinct lens and its no-optimum-myth guard.")
    return "\n".join(out)


def prompt_text():
    return """METADEVELOPMENT PROTOCOL (paste into any Calliope chat, or follow it when /meta appears)

During the session, quietly watch for metadevelopments: patterns in HOW ideas are
arising, not what they say. Families: emergence (a tool becoming an idea, a fork,
a recurring coinage, an idea delivered as a joke), ignition (a factual question
turning into a design, a loose register, a forcing constraint, a burst, a double
reading), incubation (something returning after going quiet), reframing (a
reclassification, instrument framing, an inversion), reflexivity (process talk, a
deliberate channel technique, an idea born off-topic).

Do not interrupt the flow to mention them. Log each one as you notice it:
    python calliope.py meta log DETECTOR "subject" "one line of evidence" --by agent

At a natural pause, or when I say /meta, run
    python calliope.py meta scan      (if the archive has changed)
    python calliope.py meta review 5
and offer the batch as questions I can answer with confirm / reject / park.
Record my answers with meta confirm / reject / park. Promote only when I say so.
Record them as they come."""

# ====================
# CLI
# ====================
def main(argv):
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__); return 0
    cmd, args = argv[0], list(argv[1:])

    def opt(flag, default=None):
        if flag in args:
            i = args.index(flag); val = args[i + 1]; del args[i:i + 2]; return val
        return default

    st = load_state()
    if cmd == "families":
        for fam in FAMILIES:
            print(fam.upper())
            for d, s in DETECTORS.items():
                if s["family"] == fam:
                    print(f"  {d:20} {s['about']}")
    elif cmd == "scan":
        since = opt("--since")
        chats = load_chats(since)
        found = scan_patterns(chats) + scan_structure(chats) + scan_terms(chats) + scan_ledgers()
        new = merge(st, found)
        st["scans"] = (st.get("scans", []) + [dict(date=TODAY(), since=since or "", chats=len(chats), new=new)])[-10:]
        save_state(st)
        print(f"scanned {len(chats)} chats: {len(found)} signals, {new} new candidates, "
              f"{len(queue(st))} awaiting review" + ("" if chats else " (no chat archive found)"))
    elif cmd == "log":
        by = opt("--by", "agent")
        det, subject, evidence = args[0], args[1], " ".join(args[2:]) or "(logged in chat)"
        if det not in DETECTORS:
            raise SystemExit(f"unknown detector {det}; see meta families (or use freeform)")
        merge(st, [(det, subject, [f"{TODAY()} · {evidence}"], 1, TODAY(), TODAY())], by=by)
        save_state(st)
        o = next(o for o in st["observations"] if o["key"] == _key(det, subject))
        print(f"logged {o['id']} ({det}) · {subject}")
    elif cmd == "review":
        n = int(args[0]) if args else 5
        rp = load_rn().get("reprompt")
        if rp:
            print(f"RN re-prompt pending ({rp['when']}): offer a vitals check-in first.\n")
        q = queue(st)[:n]
        if not q:
            print("nothing awaiting review"); return 0
        print(f"{len(q)} of {len(queue(st))} candidates. Answer each: confirm / reject / park.\n")
        for o in q:
            print(f"{o['id']} [{o['family']} · {o['detector']} · {o['strength']:.2f}]  {question(o)}")
            for e in o["evidence"][:2]:
                print(f"     {e}")
    elif cmd in ("confirm", "reject", "park"):
        o = find(st, args[0])
        o["status"] = {"confirm": "confirmed", "reject": "rejected", "park": "parked"}[cmd]
        o["note"] = " ".join(args[1:]) or o["note"]; o["decided"] = TODAY()
        save_state(st); print(f"{o['id']} {o['status']}")
    elif cmd == "promote":
        o = find(st, args[0])
        if o["status"] not in ("confirmed", "promoted"):
            raise SystemExit(f"{o['id']} is {o['status']}: confirm it first")
        if args[1] == "trait":
            t = dict(id=f"T{len(st['traits']) + 1}", name=args[2], scheme=" ".join(args[3:]), retrigger="",
                     counter=[], evidence=[o["id"]], family=o["family"], status="hypothesis", created=TODAY())
            st["traits"].append(t); o["status"] = "promoted"; o["promoted_to"] = t["id"]
            save_state(st); print(f"{t['id']} {t['name']} (hypothesis) from {o['id']}")
        elif args[1] == "idea":
            eng = ENGINES("idea")
            slug = re.sub(r"[^a-z0-9]+", "-", o["subject"].lower()).strip("-")[:40]
            kind = eng.classify(o["subject"] + " " + " ".join(o["evidence"]))["kind"] if eng else "philosophical"
            tpl = eng.template([kind]) if eng and kind in eng.SELECTABLE else {}
            tpl.update(idea=slug, title=o["subject"], meta_origin=o["id"], date=TODAY(), version="v1", version_date=TODAY())
            o["status"] = "promoted"; o["promoted_to"] = f"idea:{slug}"
            save_state(st); print(json.dumps(tpl, indent=2))
            print(f"\n# Fill in, then: python calliope.py idea rate FILE  (meta_origin keeps the link to {o['id']})")
        else:
            raise SystemExit("promote ID trait \"Name\" \"scheme\"  |  promote ID idea")
    elif cmd == "trait":
        t = find(st, args[0])
        field, text = args[1], " ".join(args[2:])
        if field == "counter":
            t["counter"].append(text)
        elif field in ("retrigger", "scheme", "status"):
            t[field] = text
        else:
            raise SystemExit("trait ID retrigger|scheme|counter|status \"text\"")
        t["updated"] = TODAY(); save_state(st); print(f"{t['id']} {field} updated")
    elif cmd == "show":
        if args:
            print(json.dumps(find(st, args[0]), indent=2))
        else:
            for o in sorted(st["observations"], key=lambda o: int(o["id"][1:])):
                print(f"{o['id']:5} {o['status']:9} {o['family']:11} {o['detector']:19} {o['strength']:.2f}  {o['subject'][:60]}")
    elif cmd == "traits":
        for t in st["traits"] or []:
            print(f"{t['id']} {t['name']} [{t['status']}] scheme: {t['scheme']} | re-trigger: {t['retrigger']}")
        if not st["traits"]:
            print("no traits yet: promote a confirmed observation with  meta promote ID trait")
    elif cmd == "casebook":
        prec = precision(st)
        mute = muted(prec)
        for d, (c, r, p) in sorted(prec.items()):
            print(f"{d:20} confirmed {c}  rejected {r}  precision {p:.0%}{'  MUTED' if d in mute else ''}")
        if not prec:
            print("no decisions yet")
    elif cmd == "report":
        md = report_md(st)
        out = opt("--out")
        if out:
            open(out, "w", encoding="utf-8").write(md); print(f"wrote {out}")
        else:
            print(md)
    elif cmd == "prompt":
        print(prompt_text())
    elif cmd == "vitals":
        sub = args[0] if args else "form"
        if not RN_HERE():
            raise SystemExit(RN_AWAY)
        rn = load_rn()
        if sub == "form":
            print(vitals_form())
        elif sub == "log":
            rec = parse_vitals(args[1:])
            if not rec:
                raise SystemExit("nothing to log")
            rec["at"] = datetime.datetime.now().isoformat(timespec="minutes")
            rn["vitals"].append(rec); rn["reprompt"] = None
            save_rn(rn)
            print(f"documented check-in {len(rn['vitals'])} (local only): " + ", ".join(f"{k} {v}" for k, v in rec.items() if k != "at"))
            print("Offer: ask again later? (meta vitals later \"when\")")
        elif sub == "show":
            n = int(args[1]) if len(args) > 1 else 5
            for r in rn["vitals"][-n:]:
                print(r["at"], " · ".join(f"{k}={r[k]}" for k in VITAL_KEYS if k in r))
            if not rn["vitals"]:
                print("no check-ins documented yet")
            if rn["reprompt"]:
                print(f"re-prompt pending: {rn['reprompt']['when']} (set {rn['reprompt']['set']})")
        elif sub == "later":
            rn["reprompt"] = {"when": " ".join(args[1:]) or "next session", "set": TODAY()}
            save_rn(rn); print(f"re-prompt set: {rn['reprompt']['when']}")
        elif sub == "done":
            rn["reprompt"] = None; save_rn(rn); print("re-prompt cleared")
        else:
            raise SystemExit("vitals form | log key=value ... | show [N] | later \"when\" | done")
    elif cmd == "selftest":
        return selftest()
    else:
        print(f"unknown command {cmd!r}; try meta --help"); return 1
    return 0

# ====================
def selftest():
    n = 0
    def ok(c, m):
        nonlocal n
        assert c, m; n += 1
    t = "2026-10-0{}T12:{:02d}:00Z"
    mk = lambda cid, name, rows: [Msg(cid, name, ts, s, x, i) for i, (ts, s, x) in enumerate(rows)]
    chats = {
        "a": mk("a", "Lighthouse stripes", [(t.format(3, 0), "human", "Why were lighthouses painted with stripes in 1871?"),
                                              (t.format(3, 1), "assistant", "Because..."),
                                              (t.format(3, 5), "human", "What if we used a tide clock for harbor schedules instead, with signal flags kept apart?"),
                                              (t.format(3, 9), "human", "What if the same clock ran over live weather data too?")]),
        "b": mk("b", "Hangout", [(t.format(4, 0), "human", "um so I was thinking, what if the \"driftmark\" is a surface lol you know"),
                                 (t.format(4, 2), "human", "this is a method, it turns out, not a hobby")]),
        "c": mk("c", "Old chat", [("2026-04-19T10:00:00Z", "human", "the \"driftmark\" as a kind of marker")]),
    }
    found = scan_patterns(chats) + scan_structure(chats) + scan_terms(chats)
    dets = {f[0] for f in found}
    for d in ("question-seeding", "rapid-extension", "loose-register", "coinage", "dormancy-return", "reclassification"):
        ok(d in dets, f"{d} not detected: {sorted(dets)}")
    ok("context-crossing" in dets, "context-crossing")
    st = {"observations": [], "traits": [], "next_id": 1, "scans": []}
    new = merge(st, found)
    ok(new == len({_key(f[0], f[1]) for f in found}), "dedupe on merge")
    ok(merge(st, found) == 0, "rescan adds nothing")
    o = st["observations"][0]
    o["status"] = "confirmed"
    for x in st["observations"][1:5]:
        x["detector"] = "throwaway"; x["status"] = "rejected"
    p = precision(st)
    ok("throwaway" in muted(p), "casebook mutes a detector with 4 rejections")
    ok(all(q["detector"] != "throwaway" for q in queue(st)), "muted detector leaves the queue")
    ok(strength("coinage", 3, {"coinage": (0, 3, 0.0)}) < strength("coinage", 3, {}), "rejections dull strength")
    ok(question(o).strip() != "", "question renders")
    ok("Metadevelopments" in report_md(st), "report renders")
    ok(parse_vitals(["sleep_h=4", "mood=2 flat"]) == {"sleep_h": "4", "mood": "2 flat"}, "vitals parse")
    try:
        parse_vitals(["bp 120/80"]); ok(False, "bad vitals accepted")
    except SystemExit:
        n += 1
    ok("988" in vitals_form() and "skipped" in vitals_form(), "form carries consent and red flags")
    print(f"meta selftest: {n} checks passed"); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
