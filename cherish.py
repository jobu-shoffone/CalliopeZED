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
CHERISH: a lite monitor for Calliope's CherishedValues (section 5 of calliope.py).

A CherishedValue is an idea Calliope holds as valuable in itself: not rated
and filed like other ideas, but kept as a standing lens the whole project is
checked against. The first one is INTUITION / INSTINCT, from a David Lynch
remark on intuition as the artist's number one tool:

    Instinct  = the input layer. Rest, food, stimulus, the conditions you think
                well under. Can be monitored directly.
    Intuition = the correction signal. Knowing something is off and seeing the
                fix. Pre-verbal, so only its traces can be caught: rejections,
                reversals, "no, it's more like X".
    Guards    = amplify without substituting (surface, don't originate), and
                learn good conditions from evidence instead of assuming them.

TWO TRIGGERS
    1. In-line. A chat message containing  /cherish  runs an analysis:
           /cherish                                    every value, whole project
           /cherish intuition-instinct                 one value
           /cherish intuition-instinct places-things   focused on one rated idea
       The agent: when a message contains /cherish, run
           python calliope.py cherish inline "<the message>"
    2. Juxtaposition. Rate an idea produced by holding a value against an idea,
       with  "juxtaposes": ["intuition-instinct"]  in its rating file:
           python calliope.py cherish rate rating.json          (ASSAY 2)
           python calliope.py cherish rate lit rating.json      (ASSAY-LIT)
       It logs through the engine as usual; if any kind's magnitude is at or
       above the value's threshold (4.5), the analysis runs, focused on that
       idea. `sweep` catches juxtapositions rated straight through `idea rate`
       or `lit rate`. Each trigger fires once per idea version.

USAGE (prefix: python calliope.py cherish)
    values                          list CherishedValues
    show VALUE                      one value in full (JSON)
    new ID "Name"                   blank value JSON to fill in
    add value.json                  store a value (or replace one) in calliope_state.json
    analyze [VALUE ...] [--focus IDEA] [--out report.md]   run the analysis: every value, or the ones named
    inline "message text"           in-line /cherish trigger
    juxtapose VALUE "idea text"     seed prompt for a juxtaposition
    rate [idea|lit] rating.json     engine rate + threshold trigger
    sweep                           analyze untriggered juxtapositions in both ledgers
    selftest                        run this engine's self-tests

Corpus: user_name's messages in the chat archive (calliope_archive.json
beside calliope.py or attached, or any file named by CALLIOPE_ARCHIVE), plus design text: the archive's memory files and index of
ideas, the REGISTRY and GUIDEBOOK sections, and assistant replies.
Heuristic: keyword and pattern counts. It shows where to look; it doesn't judge.
"""

import json, os, re, sys, datetime, collections
from dataclasses import dataclass, field, asdict
from typing import List, Optional

VERSION = "cherish-1.1"
ARCHIVES = ("calliope_archive.json",)

# Injected by the calliope.py launcher; these stand-ins let the engine run alone.
ENGINES = lambda name: None                                # name -> engine module or None
LOAD_ARCHIVE = lambda p: json.load(open(p, encoding="utf-8"))   # the launcher shares one parse
DESIGN = {}                                                # title -> design text
_STATE = {"values": [], "triggered": []}
load_state = lambda: json.loads(json.dumps(_STATE))
def save_state(st):
    _STATE.clear(); _STATE.update(st)

# ====================
# The datatype
# ====================
@dataclass
class Lens:
    """One part of a value's thesis, as something checkable in the project."""
    id: str
    role: str                                   # input | correction | guard
    question: str
    signals: List[str]                          # evidence in user_name's messages (regex)
    design_signals: List[str] = field(default_factory=list)   # evidence the design accounts for it
    gap_advice: str = ""


@dataclass
class CherishedValue:
    id: str
    name: str
    thesis: str
    origin: str
    adopted: str
    lenses: List[Lens]
    cautions: List[str] = field(default_factory=list)
    threshold: float = 4.5                      # juxtaposition magnitude that triggers analysis
    self_rating: Optional[float] = None         # Richter of the value itself when adopted

    @staticmethod
    def from_dict(d):
        d = dict(d)
        d["lenses"] = [Lens(**l) for l in d.get("lenses", [])]
        v = CherishedValue(**d)
        bad = [l.id for l in v.lenses if l.role not in ("input", "correction", "guard")]
        if not v.id or not v.lenses or bad:
            raise ValueError(f"value needs an id and lenses with role input|correction|guard (bad: {bad})")
        for l in v.lenses:
            for p in l.signals + l.design_signals:
                re.compile(p)
        return v

    def to_dict(self):
        return asdict(self)


INTUITION_INSTINCT = CherishedValue(
    id="intuition-instinct",
    name="Intuition and Instinct",
    thesis=("Calliope amplifies cognition by monitoring instinct as the input layer (the conditions "
            "behind good work) and reading intuition as the correction signal (knowing something is "
            "off and seeing the fix), without letting the software substitute for either."),
    origin=("David Lynch on intuition as the artist's number one tool: knowing when something is not "
            "correct and seeing a way to make it correct, as distinct from instinct (hunger, eating). "
            "Framed for Calliope by user_name, Oct 2026."),
    adopted="2026-10-07",
    self_rating=4.5,
    lenses=[
        Lens("instinct-input", "input",
             "Does Calliope capture the conditions (rest, energy, stimulus, time, mood) present when thinking goes well?",
             [r"\bsleep", r"\bslept", r"\brest(ed|ing)?\b", r"\btired", r"\bexhaust", r"\benergy\b",
              r"\bcaffeine", r"\bcoffee\b", r"\bwalk(ing)?\b", r"\blate at night", r"\bmood\b", r"\binspired",
              r"\bin the zone", r"\bflow state", r"\bnourish", r"\bfocus(ed)?\b", r"\bdistracted", r"\bheadspace"],
             [r"stimulus scheme", r"cognitive trait", r"nourish", r"inspired, productive", r"conditions? (behind|under|for) "],
             "Log a few conditions (sleep, energy, time, setting) with chats or ratings so inspired sessions "
             "can be matched to what preceded them."),
        Lens("intuition-correction", "correction",
             "Does Calliope notice correction events, the traces intuition leaves, and learn from them?",
             [r"\bactually\b", r"\bnot quite\b", r"\bthat'?s not (it|right|what)", r"^no\b", r"\bno, ",
              r"\bscratch that\b", r"\bi meant\b", r"\blet me rephrase", r"\bmore like\b", r"\bon second thought",
              r"\bthat'?s wrong\b", r"\bcorrection\b", r"\breframe", r"\bredo\b", r"\brevise"],
             [r"correction", r"handshake error", r"\breversal", r"\bdetect(ed|s)? "],
             "Treat correction events as first-class data: log what was rejected, what replaced it, and the "
             "conditions at the time."),
        Lens("no-substitution", "guard",
             "Does Calliope confirm or sharpen corrections user_name starts, rather than originating them for them?",
             [r"should i develop", r"\bask me (first|before)", r"\bflag .{0,40}ask", r"\bconfirm with me"],
             [r"should i develop", r"surfaced to them as a prompt", r"ask (me|him|her|them) (first|before)",
              r"\bflag .{0,40} and ask", r"recommendation, not a mandate", r"before being developed"],
             "Write a rule that detected traits and suspected errors are offered as questions, never applied."),
        Lens("no-optimum-myth", "guard",
             "Are good conditions learned from evidence rather than assumed (rested and fed is not always best)?",
             [r"\bfriction\b", r"\bbored(om)?\b", r"\bdeplet", r"\bdespite (being )?(tired|exhausted)",
              r"\bunder pressure", r"\bbest (work|ideas?) (came|come) "],
             [r"track which conditions", r"actually preceded", r"counter-?example", r"weak sessions?"],
             "Record conditions for weak sessions too, so the model can find counter-examples."),
    ],
    cautions=["Amplification can become substitution: flag errors as questions, don't pre-empt the feel.",
              "'Optimally nourished' is a hypothesis per person, not a rule."],
)

BUILTIN = {INTUITION_INSTINCT.id: INTUITION_INSTINCT}


def load_values():
    vals = dict(BUILTIN)
    for d in load_state().get("values", []):
        v = CherishedValue.from_dict(d)
        vals[v.id] = v
    return vals

# ====================
# Corpus
# ====================
Doc = collections.namedtuple("Doc", "source title sender date text")


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


def load_corpus():
    docs = [Doc("design", title, "-", "", text) for title, text in DESIGN.items()]
    p = _archive_path()
    if not p:
        return docs
    arc = LOAD_ARCHIVE(p)
    for acct in ("current_account", "old_account"):
        a = arc.get(acct, {})
        for c in a.get("conversations", []):
            for m in (c.get("chat_messages") or c.get("messages") or []):
                if m.get("text"):
                    docs.append(Doc("chat", c.get("name") or "untitled", m.get("sender", "?"),
                                    (m.get("created_at") or m.get("at") or "")[:10], m["text"]))
        mem = a.get("memories", {})
        for f in mem.get("memory_files", []):
            txt = f.get("content") if isinstance(f, dict) else str(f)
            if txt:
                docs.append(Doc("design", f.get("path", "memory") if isinstance(f, dict) else "memory", "-", "", txt))
        if isinstance(mem.get("conversations_memory"), str):
            docs.append(Doc("design", "conversations_memory", "-", "", mem["conversations_memory"]))
    if arc.get("index_of_ideas"):
        docs.append(Doc("design", "index_of_ideas", "-", "", arc["index_of_ideas"]))
    return docs

# ====================
# Ledgers (both engines expose load / current / idea_text; facets carry "magnitude")
# ====================
def rated(engine_name, value_id=None):
    """[(idea, version, top magnitude, rating text, juxtaposed value ids)] from one engine's ledger."""
    eng = ENGINES(engine_name)
    if not eng:
        return []
    db, out = eng.load(), []
    for idea in sorted({r["idea"] for r in db.get("ratings", [])}):
        ver, facets, rs = eng.current(db, idea)
        top = max((a["magnitude"] for a in facets.values()), default=0)
        jx = sorted({j for r in rs for j in r.get("juxtaposes", [])})
        out.append((idea, ver, top, " ".join(eng.idea_text(r) for r in rs), jx))
    return out

# ====================
# Analysis
# ====================
def _rx(pats):
    return re.compile("|".join(f"(?:{p})" for p in pats), re.I | re.M) if pats else None


def _snip(text, m, width=70):
    a, b = max(0, m.start() - width), min(len(text), m.end() + width)
    return ("..." if a else "") + " ".join(text[a:b].split()) + ("..." if b < len(text) else "")


def analyze(value, docs, focus=None, ledgers=None):
    human = [d for d in docs if d.source == "chat" and d.sender == "human"]
    design = [d for d in docs if d.source == "design" or (d.source == "chat" and d.sender != "human")]
    lens_out = []
    for L in value.lenses:
        rx, drx = _rx(L.signals), _rx(L.design_signals)
        months, examples = collections.Counter(), []
        for d in human:
            m = rx.search(d.text)
            if m:
                months[d.date[:7] or "undated"] += 1
                if len(examples) < 4:
                    examples.append(f"{d.date} · {d.title}: {_snip(d.text, m)}")
        dhits = sum(len(drx.findall(d.text)) for d in design) if drx else 0
        msgs = sum(months.values())
        if L.role == "guard":                       # a guard lives in the design
            status = "Covered" if dhits >= 2 else "Partial" if (dhits or msgs) else "Gap"
        else:
            status = "Covered" if dhits >= 2 and msgs else "Partial" if (dhits or msgs) else "Gap"
        lens_out.append(dict(lens=L, msgs=msgs, rate=msgs / len(human) if human else 0, design_hits=dhits,
                             months=dict(sorted(months.items())), examples=examples, status=status))

    link = None
    corr = next((L for L in value.lenses if L.role == "correction"), None)
    inp = next((L for L in value.lenses if L.role == "input"), None)
    if corr and inp:
        c_rx, i_rx = _rx(corr.signals), _rx(inp.signals)
        by_chat = collections.defaultdict(lambda: [False, False])
        for d in human:
            f = by_chat[d.title]
            f[0] |= bool(c_rx.search(d.text)); f[1] |= bool(i_rx.search(d.text))
        both = [t for t, (c, i) in by_chat.items() if c and i]
        link = dict(chats=len(by_chat), both=len(both), sample=both[:5])

    allrx = _rx([s for L in value.lenses for s in L.signals + L.design_signals])
    ideas = []
    for eng, rows in (ledgers or {}).items():
        for idea, ver, top, text, jx in rows:
            if focus and idea != focus:
                continue
            ideas.append(dict(engine=eng, idea=idea, version=ver, magnitude=top,
                              touches=len(allrx.findall(text)), juxtaposed=value.id in jx))
    return dict(value=value, n_human=len(human), n_design=len(design), lenses=lens_out,
                link=link, ideas=ideas, focus=focus, archive=bool(_archive_path()))


def report_md(a, trigger="direct"):
    v = a["value"]
    out = [f"# CherishedValue check: {v.name}",
           f"{datetime.date.today().isoformat()} · trigger: {trigger} · {VERSION}"
           + (f" · focus: {a['focus']}" if a["focus"] else ""), "",
           f"**Thesis.** {v.thesis}", "",
           f"Corpus: {a['n_human']} of user_name's messages, {a['n_design']} design/assistant texts."
           + ("" if a["archive"] else " (no chat archive found: design text only.)"), "",
           "| Lens | Role | Status | user_name's messages with signal | Design mentions |",
           "|---|---|---|---|---|"]
    for l in a["lenses"]:
        out.append(f"| {l['lens'].id} | {l['lens'].role} | {l['status']} | {l['msgs']} ({l['rate']:.0%}) | {l['design_hits']} |")
    for l in a["lenses"]:
        L = l["lens"]
        out += ["", f"## {L.id} · {l['status']}", L.question]
        if l["months"]:
            out.append("By month: " + ", ".join(f"{k} {n}" for k, n in l["months"].items()))
        out += [f"- {e}" for e in l["examples"]]
        if l["status"] != "Covered" and L.gap_advice:
            out.append(f"**Next:** {L.gap_advice}")
    if a["link"]:
        k = a["link"]
        out += ["", "## Instinct-intuition linkage",
                f"{k['both']} of {k['chats']} chats hold both a correction event and a condition signal: the raw "
                "material for learning which conditions precede good corrections"
                + (". " + "; ".join(k["sample"]) if k["sample"] else ".")]
    if a["ideas"]:
        out += ["", "## Rated ideas", "| Engine | Idea | Version | Top magnitude | Lens touches | Juxtaposed |",
                "|---|---|---|---|---|---|"]
        for i in sorted(a["ideas"], key=lambda x: (-x["touches"], x["idea"])):
            out.append(f"| {i['engine']} | {i['idea']} | {i['version']} | {i['magnitude']:g} | {i['touches']} | "
                       f"{'yes' if i['juxtaposed'] else ''} |")
    elif a["focus"]:
        out += ["", f"(No rated idea named {a['focus']} in either ledger.)"]
    gaps = [l["lens"].id for l in a["lenses"] if l["status"] == "Gap"]
    out += ["", "## Verdict",
            f"Gaps: {', '.join(gaps)}. Address these before building on the value." if gaps
            else "No outright gaps; strengthen Partial lenses next.",
            "", "Cautions: " + " ".join(v.cautions)]
    return "\n".join(out)

# ====================
# Triggers
# ====================
INLINE = re.compile(r"(?:^|\s)/cherish\b(?:[ \t]+([a-z0-9][\w-]*))?(?:[ \t]+([a-z0-9][\w-]*))?", re.I)


def parse_inline(text, values):
    m = INLINE.search(text)
    if not m:
        return None
    vid, focus = m.group(1), m.group(2)
    if vid and vid.lower() not in values:           # first word is a focus, not a value id
        vid, focus = None, vid
    return dict(values=[vid.lower()] if vid else list(values), focus=focus)


def juxtaposition_hits(values, only=None):
    """(engine, value id, idea, version, magnitude) at or above each value's threshold."""
    hits = []
    for eng in ("idea", "lit"):
        for idea, ver, top, _, jx in rated(eng):
            if only and idea != only:
                continue
            for vid in jx:
                if vid in values and top >= values[vid].threshold:
                    hits.append((eng, vid, idea, ver, top))
    return hits


def run_analysis(vids, values, focus=None, trigger="direct", out=None):
    docs = load_corpus()
    ledgers = {e: rated(e) for e in ("idea", "lit")}
    text = "\n\n---\n\n".join(report_md(analyze(values[v], docs, focus, ledgers), trigger) for v in vids)
    if out:
        open(out, "w", encoding="utf-8").write(text); print(f"wrote {out}")
    else:
        print(text)
    return text


def fire(hits, values):
    st = load_state(); done = set(st.get("triggered", []))
    fired = 0
    for eng, vid, idea, ver, m in hits:
        key = f"{eng}|{vid}|{idea}|{ver}"
        if key in done:
            continue
        print(f"\nTRIGGER: {idea} {ver} x {vid} at magnitude {m:g} (threshold {values[vid].threshold})\n")
        run_analysis([vid], values, idea, f"juxtaposition {idea} {ver} M{m:g}")
        st.setdefault("triggered", []).append(key); fired += 1
    if fired:
        save_state(st)
    return fired


def juxtapose_seed(v, idea_text):
    lenses = "\n".join(f"  - {L.id} ({L.role}): {L.question}" for L in v.lenses)
    return f"""JUXTAPOSITION SEED · {v.name}
Value thesis: {v.thesis}
Idea: {idea_text}

Task: state the idea that results from holding this idea against the value, in 2-4 sentences.
Then rate the RESULT (not the original idea). Lenses to press on:
{lenses}

Add to the rating file:  "juxtaposes": ["{v.id}"]
Then:  python calliope.py cherish rate rating.json   (analysis runs at magnitude {v.threshold}+)"""


def main(argv):
    values = load_values()
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__); return 0
    cmd, args = argv[0], list(argv[1:])

    def opt(flag):
        if flag in args:
            i = args.index(flag); val = args[i + 1]; del args[i:i + 2]; return val
        return None

    def need(vid):
        if vid not in values:
            raise SystemExit(f"no CherishedValue {vid!r}; have {sorted(values)}")
        return values[vid]

    if cmd == "values":
        for v in values.values():
            print(f"{v.id:22} {v.name} · threshold {v.threshold} · adopted {v.adopted}"
                  + (f" · Richter {v.self_rating:g}" if v.self_rating is not None else "")
                  + ("" if v.id not in BUILTIN else " · built in"))
    elif cmd == "show":
        print(json.dumps(need(args[0]).to_dict(), indent=2))
    elif cmd == "new":
        vid, name = args[0], " ".join(args[1:]) or args[0]
        blank = CherishedValue(vid, name, "", "", datetime.date.today().isoformat(),
                               [Lens("lens-1", "input", "", [], [], "")])
        print(json.dumps(blank.to_dict(), indent=2))
        print("\n# Fill in, save as a .json file, then: python calliope.py cherish add FILE")
    elif cmd == "add":
        v = CherishedValue.from_dict(json.load(open(args[0], encoding="utf-8")))
        st = load_state()
        st["values"] = [d for d in st.get("values", []) if d.get("id") != v.id] + [v.to_dict()]
        save_state(st); print(f"stored {v.id}" + (" (overrides the built-in)" if v.id in BUILTIN else ""))
    elif cmd == "analyze":
        focus, out = opt("--focus"), opt("--out")
        run_analysis([need(a).id for a in args] or list(values), values, focus, "direct", out)
    elif cmd == "inline":
        p = parse_inline(" ".join(args), values)
        if not p:
            print("no /cherish command in message"); return 0
        run_analysis(p["values"], values, p["focus"], "in-line /cherish")
    elif cmd == "juxtapose":
        print(juxtapose_seed(need(args[0]), " ".join(args[1:])))
    elif cmd == "rate":
        eng_name = args.pop(0) if args and args[0] in ("idea", "lit") else "idea"
        eng = ENGINES(eng_name)
        if not eng:
            print("rating engines are only available through calliope.py"); return 1
        r = json.load(open(args[0], encoding="utf-8"))
        unknown = [j for j in r.get("juxtaposes", []) if j not in values]
        if unknown:
            print(f"unknown CherishedValue(s) {unknown}; have {sorted(values)}"); return 1
        try:
            rc = eng.main(["rate", args[0]]) or 0
        except eng.RatingError as e:
            print("rating error:", e); return 2
        if not fire(juxtaposition_hits(values, r["idea"]), values) and r.get("juxtaposes"):
            print("\nJuxtaposition below threshold (or already analyzed): no analysis triggered.")
        return rc
    elif cmd == "sweep":
        if not fire(juxtaposition_hits(values), values):
            print("nothing new at or above threshold")
    elif cmd == "selftest":
        return selftest()
    else:
        print(f"unknown command {cmd!r}; try cherish --help"); return 1
    return 0

# ====================
def selftest():
    vals = dict(BUILTIN)
    checks = 0
    def ok(cond, msg):
        nonlocal checks
        assert cond, msg; checks += 1
    ok(parse_inline("hey /cherish", vals)["values"] == list(vals), "bare /cherish")
    p = parse_inline("ok /cherish intuition-instinct places-things please", vals)
    ok(p == {"values": ["intuition-instinct"], "focus": "places-things"}, p)
    ok(parse_inline("/cherish ledger", vals)["focus"] == "ledger", "focus without value")
    ok(parse_inline("I cherish this", vals) is None, "no false trigger")
    ok(parse_inline("/cherish\nnext line", vals)["focus"] is None, "no focus across lines")
    docs = [Doc("chat", "a", "human", "2026-10-01", "Actually no, it's more like a ring. I slept badly."),
            Doc("chat", "b", "human", "2026-10-02", "Build the thing."),
            Doc("design", "d", "-", "", "traits surfaced to them as a prompt; should I develop it? before being developed")]
    a = analyze(INTUITION_INSTINCT, docs)
    st = {l["lens"].id: l["status"] for l in a["lenses"]}
    ok(st["intuition-correction"] == "Partial" and st["no-substitution"] == "Covered", st)
    ok(st["no-optimum-myth"] == "Gap", st)
    ok(a["link"]["both"] == 1, a["link"])
    ok(CherishedValue.from_dict(INTUITION_INSTINCT.to_dict()).lenses[0].id == "instinct-input", "round trip")
    try:
        CherishedValue.from_dict({**INTUITION_INSTINCT.to_dict(), "lenses": [{"id": "x", "role": "mood",
                                  "question": "", "signals": []}]}); ok(False, "bad role accepted")
    except ValueError:
        checks += 1
    led = {"idea": [("hi", "v1", 5, "detect correction", ["intuition-instinct"]), ("lo", "v1", 4, "", ["intuition-instinct"])]}
    a = analyze(INTUITION_INSTINCT, docs, "hi", led)
    ok([i["idea"] for i in a["ideas"]] == ["hi"] and a["ideas"][0]["juxtaposed"], a["ideas"])
    print(f"cherish selftest: {checks} checks passed"); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
