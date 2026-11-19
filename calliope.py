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
CALLIOPE ZED: the blank edition of Calliope, a workspace for developing ideas, for user_name.

Contents, in order:
    1. REGISTRY       the persona registry (Markdown text)
    2. GUIDEBOOK      the story guidebook (Markdown text)
    3-6. ENGINES      a pointer: idea (ASSAY 2), lit (ASSAY-LIT), cherish (CHERISH) and
                      meta (META) live in engines/ beside this file
    7. STATE          a pointer: every rating and record lives in calliope_state.json
    8. Launcher       the commands below, plus the session tools (status, release, sync, glossary)

The layers: ASSAY rates ideas, CHERISH holds values, META watches how ideas
happen. META reads the ledgers and CHERISH's triggers; no engine writes into
another engine's state. PERSONA, the exploration layer under the registry, is a
fifth engine, engines/persona.py: it records how user_name and a
persona explored an idea.

FILES (keep them together)
    calliope.py           this program: launcher, registry, guidebook and session tools
    engines/              idea.py, lit.py, cherish.py, meta.py (they travel with the program and
                          share its hash) and persona.py
    calliope_state.json   all state: both rating ledgers, CHERISH, META and persona explorations (RN check-ins stay in health/, local only)
    CALLIOPE_DATA.md      the session file: protocol, release stamp, open threads, session log
Each stays under 256 KiB, so an agent tool with a small read limit or a small
model's context can take any one file whole; status and release warn as a file
approaches that. The chat archive
(calliope_archive.json) is loaded only for
meta scan, cherish analyze and CATCH ME UP.

SESSION FLOW
    One folder, one writer: the program writes state and releases. The steps are
    the session protocol in CALLIOPE_DATA.md; `glossary` lists them. zed.py makes
    the documents (Snapshots, briefs, STUDYBOOK) and adds personas.

USAGE
    python calliope.py status [--data FILE] [--quick]   session check: program and state vs release stamp, self-tests, file sizes, next steps
    python calliope.py release [--data FILE] [--note "text"] [--out DIR] [--force]   self-test, restamp CALLIOPE_DATA.md, write calliope_release.zip
    python calliope.py sync [--data FILE] [--expect CODE]   one sync code for the three files; --expect checks this copy against another copy's code
    python calliope.py glossary [--json] [--out FILE]   every command and in-chat shorthand (Markdown, or JSON for the PDF)
    python calliope.py idea <command> ...     ASSAY 2 (run "idea --help")
    python calliope.py lit <command> ...      ASSAY-LIT (run "lit --help")
    python calliope.py cherish <command> ...  CherishedValues (run "cherish --help")
                                              in chat: a message with /cherish -> cherish inline "<message>"
    python calliope.py meta <command> ...     metadevelopments (run "meta --help"; protocol: "meta prompt")
                                              in chat: a message with /meta -> meta review
    python calliope.py persona <command> ...  explorations with a persona (run "persona --help"; needs engines/persona.py)
    python calliope.py registry               print the persona registry
    python calliope.py guidebook              print the story guidebook
    python calliope.py export [DIR]           write registry, guidebook, ledgers, CHERISH, META and persona state as separate files
    python calliope.py import idea|lit FILE   merge an external ledger JSON into calliope_state.json
    python calliope.py selftest               run every engine's self-tests and the launcher's (never touches real state)

State: rating and logging commands rewrite calliope_state.json atomically (temp
file, then rename), so a crash can't leave a half-written file. If the state file
is read-only (for example a copy mounted read-only), the updated copy goes to the
output folder (CALLIOPE_OUT, else the folder beside calliope.py) and later
commands use that copy. CALLIOPE_STATE points at a
state file kept elsewhere; ASSAY_LEDGER, ASSAY_LIT_LEDGER, CHERISH_STATE,
META_STATE or PERSONA_STATE give one engine an external file of its own.

Standard library only, Python 3.8+.
"""
import json, os, re, sys, types, tempfile, glob, hashlib, zipfile, subprocess, datetime

SELF = os.path.abspath(__file__)
TOKEN = "user_name"


def _zed_user():
    """The user's name, from zed_config.json beside the program (zed.py init writes it); the token until then."""
    try:
        with open(os.path.join(os.path.dirname(SELF), "zed_config.json"), encoding="utf-8") as f:
            return json.load(f).get("user_name") or TOKEN
    except (OSError, ValueError):
        return TOKEN


USER = _zed_user()


class _Named:
    """Standard output with the token read as the user's name: the files keep the token, what the program says has the name."""

    def __init__(self, stream):
        self._stream = stream

    def write(self, text):
        return self._stream.write(text.replace(TOKEN, USER))

    def __getattr__(self, attr):
        return getattr(self._stream, attr)

# ====================
# 1. REGISTRY
# ====================
REGISTRY_FILE = os.path.join("personas", "REGISTRY.md")


def _load_registry():
    """The persona registry: personas/REGISTRY.md beside this program (`zed.py init` writes it; `zed.py persona new` adds to it)."""
    p = os.path.join(os.path.dirname(SELF), REGISTRY_FILE)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return f.read()
    return "# Persona registry\n\n(no registry yet: run python3 zed.py init)\n\n## Section D: Persona menu (hidden)\n  - C The Council\n  - 0 Exit persona\n\n## Maintenance\n"


REGISTRY = _load_registry()

# ====================
# 2. GUIDEBOOK
# ====================
GUIDEBOOK = r'''# Calliope Story Guidebook
Version 1 · October 7, 2026 · Part of calliope.py, companion to its `lit` engine (ASSAY-LIT)

## 0. How the agent uses this file
This is a reference for the agent, not a rulebook for user_name. It names structures, devices and genre patterns so the agent can offer accurate lenses, diagnose problems and point to precedent.

Rules of use:
- **Influence guard.** Offer these as lenses or questions ("Is this a man-in-a-hole shape or an Icarus shape?"), never as instructions. Don't pick a structure for user_name, and don't fill a story's gaps with a device from here unless they ask.
- **Name the source and its standing.** Most of this is craft lore: durable, widely taught, but not proven. Section 13 lists what has empirical support. Don't present lore as law.
- **Diagnose before prescribing.** Use Section 11 to find what's missing, then ask user_name about it.
- **Patterns are defaults, not requirements.** Strong work often breaks one deliberately. The useful question is always whether a break is chosen or accidental.

---

## 1. The engine (what makes a story move)
- **Story question.** A question the reader wants answered (Will she escape? What is he hiding?). Tension lasts as long as the question stays open and the answer stays uncertain.
- **Want vs. need.** The conscious goal (want) versus what the character actually lacks (need). Many strong arcs come from pursuing the want and discovering the need.
- **Opposition.** A force that actively wants something incompatible. Opposition with its own coherent desire is stronger than a pure obstacle.
- **Stakes.** What is lost on failure. Personal stakes usually outperform abstract ones; large stakes work best when anchored to a person.
- **Clock.** Pressure that forces action now (a deadline, a dwindling resource, an approaching event).
- **Agency.** The protagonist's choices drive events. A passive protagonist is a common failure, except where passivity is the point (and then it must be felt as a cost).
- **The minimum.** Someone wants something, something opposes them, and something is at stake. Without all three, there's a premise or a mood but not yet a story (ASSAY-LIT Resolution 1).

## 2. Macro structures
- **Three acts.** Setup, confrontation, resolution, with turning points near the quarter and three-quarter marks. Mostly a description of proportion, not a formula.
- **Freytag's pyramid.** Exposition, rising action, climax, falling action, denouement. Built on tragedy; useful for stories with a central reversal.
- **Kishōtenketsu.** Introduction, development, twist (an unexpected juxtaposition), reconciliation. Conflict isn't required; tension comes from the twist recasting what came before. Good for quiet, literary and lyrical work.
- **Hero's journey (Campbell; Vogler's screenwriting version).** Departure, initiation, return. Useful for transformation stories; overapplied, and it flattens stories that aren't about a hero.
- **Story Circle (Dan Harmon).** Comfort, want, unfamiliar situation, adapt, get what they wanted, pay a price, return, changed. A compact, repeatable loop for episodes and chapters.
- **Fichtean curve.** Starts in crisis, escalates through a series of crises, minimal exposition. Thrillers and horror.
- **MICE quotient (Orson Scott Card).** Milieu, Idea, Character, Event: what kind of question opens the story determines what must close it. Nested threads close in reverse order of opening.
- **Try-fail cycles.** Yes-but (succeed with a cost) and no-and (fail and it gets worse) drive escalation.
- **Promise, progress, payoff (Brandon Sanderson).** The opening promises a kind of story; the middle shows progress on that promise; the ending pays it off. A broken promise reads as a bait-and-switch.
- **Frame, braided, mosaic.** A frame story wraps the main one; braided plots alternate threads that converge; mosaic novels assemble a whole from fragments.
- **Found-document and epistolary.** Letters, transcripts, reports. Strong for horror and for unreliable narration; cost is reduced immediacy.

## 3. Story shapes (Vonnegut's graph)
Vonnegut proposed plotting fortune over time. A 2016 computational study of about 1,700 Project Gutenberg books (Reagan et al.) found six dominant emotional arcs:
- Rags to riches (rise)
- Tragedy, or riches to rags (fall)
- Man in a hole (fall, then rise)
- Icarus (rise, then fall)
- Cinderella (rise, fall, rise)
- Oedipus (fall, rise, fall)
The study found man-in-a-hole, Cinderella and Oedipus shapes associated with higher download counts in that sample. Treat as suggestive, not predictive.

## 4. Scene-level craft
- **Scene and sequel (Dwight Swain).** Scene: goal, conflict, disaster. Sequel: reaction, dilemma, decision. Alternation controls pace.
- **Turning values (Robert McKee).** A scene should change something that matters (safety to danger, trust to suspicion). A scene where nothing turns is a candidate for cutting.
- **"Therefore" and "but," not "and then" (Trey Parker and Matt Stone).** Events linked by causation or reversal feel driven; events merely listed feel episodic.
- **Enter late, leave early.** Start the scene after the throat-clearing; end before the wrap-up.
- **Every scene does two jobs.** Advance plot plus reveal character, or build world plus raise tension.
- **Escalation.** Each complication should cost more than the last.

## 5. Character
- **Contradiction.** Characters feel alive when they hold opposed traits or values that the story puts under pressure.
- **Ghost, wound, lie (K.M. Weiland and others).** A past event, the belief it produced, and the arc that tests that belief. Powerful but easy to make schematic.
- **Foil and mirror.** A character who shares a situation but chooses differently shows the protagonist's choices by contrast.
- **Moral argument (John Truby).** The protagonist and opponent embody competing answers to the same moral question; the plot is the argument.
- **Round and flat (E.M. Forster).** Round characters can surprise convincingly; flat ones serve a function. Both have a place.
- **Want made visible.** Show desire through behavior and cost, not stated intention.

## 6. Point of view and narration
- **First person.** Intimacy, voice, built-in limits on knowledge; unreliability available.
- **Close third.** Near-first intimacy with more flexibility; the most common modern default.
- **Omniscient.** Can move between minds and comment; demands a strong narrating voice.
- **Second person.** Immersive or accusatory; hard to sustain at length.
- **Psychic distance (John Gardner).** A scale from distant ("It was winter in the year 1853") to deep inside a mind. Deliberate shifts create effects; accidental ones create blur.
- **Free indirect discourse.** Third person colored by a character's idiom and thought without tags. The workhorse of literary fiction.
- **Unreliable narrator.** Works when the reader can detect the gap between what's said and what's true. Retrospective narration adds a second, wiser (or still self-deceived) narrator.
- **Tense.** Past is the invisible default; present adds immediacy and can flatten time.

## 7. Dialogue
- **Subtext.** People rarely say what they mean, especially under pressure. Strong dialogue lets the real conversation happen underneath.
- **Oblique answers.** A character answering a different question than the one asked signals evasion, fear or priority.
- **Status (Keith Johnstone).** Every exchange shifts status up or down. Tracking who's winning makes dialogue dramatic.
- **Interruption, silence, refusal.** What isn't said, or is cut off, carries weight.
- **Avoid on-the-nose lines,** where characters state feelings or themes outright, and "as you know" exposition between people who already know it.
- **Tags.** "Said" is near-invisible; action beats can replace tags and add physical life. Ornate tags draw attention to themselves.
- **Voice differentiation.** Rhythm, vocabulary and what each character notices, more than accent spelling. Use dialect lightly.
- **Dialogue as action.** Each exchange should change a relationship or a situation.

## 8. Tension devices
- **Dramatic irony.** The reader knows what the character doesn't. Hitchcock's bomb under the table: surprise lasts seconds, suspense lasts the whole scene.
- **Chekhov's gun / plant and payoff.** Set up what you'll use; use what you set up.
- **Foreshadowing.** Hints that make a later turn feel inevitable in hindsight.
- **Reversal (peripeteia) and recognition (anagnorisis) (Aristotle).** A change of fortune and a moment of realization, strongest when they coincide.
- **Ticking clock.** Visible, shrinking time.
- **Mystery box.** An open question withheld. Payoff must be at least as interesting as the withholding.
- **Red herring.** A false lead. Fair when the true answer was also available.
- **Rule of three.** Pattern, confirmation, break.
- **Cliffhanger.** Cut at peak uncertainty. Overuse breeds distrust.

## 9. Theme
- **Theme as question, not statement.** Stories that argue both sides through characters tend to outlast stories that preach one.
- **Controlling idea (McKee).** One sentence: value plus cause ("Justice prevails when one person refuses to look away"). Useful for revision, risky as a starting point.
- **Theme lives in choices.** What characters do under pressure expresses theme more than what they say.
- **Motif and symbol.** Recurring images accrue meaning through repetition and variation. A symbol should work literally first.
- **The preaching test.** If a character could be replaced by the author's opinion without loss, the theme is on the surface.

---

## 10. Genre patterns: what reliably works and how it fails

### Horror
Works:
- **The rules.** The threat obeys rules the reader learns; dread comes from watching characters approach them.
- **Why don't they leave?** Isolation (place, weather, social, financial) or complicity answers this. Without an answer, the premise collapses.
- **Dread over shock.** Anticipation and partial revelation; what is unseen scares more than what is shown.
- **The ordinary made wrong.** A home, a family, a routine, a device.
- **The protagonist's choice brings it closer.** Horror often hinges on a decision that seemed reasonable.
- **Body horror.** Violation of bodily integrity as a figure for loss of control.
- **Cosmic horror.** Insignificance before an indifferent order.
- **Folk horror.** Community, ritual, land.
- **Stephen King's toolkit (from his public work and *On Writing*).** Ordinary people in a specific small community, brand-name realism, intimate interior voice, slow buildup before the supernatural, community secrets, addiction and failure as real stakes.
- **Harlan Ellison's "I Have No Mouth, and I Must Scream."** The archetype of AI as god-like tormentor; horror from total, permanent helplessness.
Fails: the monster explained to death, characters made stupid to keep the plot going, gore without dread, an ending that resets everything.

### Speculative (SF, fantasy, dystopia)
Works:
- **The novum (Darko Suvin).** One central new thing, worked out consistently.
- **What if / if only / if this goes on.** Heinlein's three modes of extrapolation.
- **One impossible premise (attributed to H.G. Wells).** Readers grant one big leap; stacking several strains belief.
- **Cost (Sanderson's laws of magic).** Limitations and costs are more interesting than powers. A system that solves problems should be understood by the reader first.
- **Iceberg worldbuilding.** Imply far more than you explain; reveal through use, not lecture.
- **The ordinary person in the changed world.** The view from below makes the system legible.
- **Dystopian staples.** The protective state that lies; the enclave; the forbidden knowledge; the official history versus the real one.
Fails: info dumps, a world that never costs anyone anything, the rule broken when the plot needs it.

### Thriller, crime, suspense
Works:
- **Clock plus pursuit.** Who's hunting whom, and how long until they arrive.
- **Escalating stakes** from personal to wider.
- **Fair-play mystery (Knox's rules, the Golden Age tradition).** The reader could solve it.
- **Inverted mystery ("Columbo").** We know who did it; tension is in how they're caught.
- **The investigator with a stake** in the answer.
Fails: coincidence doing the plot's work, villains who explain the plan, twists that invalidate everything before them.

### Literary
Works:
- **Epiphany (Joyce).** A quiet moment of realization as climax.
- **Iceberg (Hemingway).** Omit the thing the story is about; let pressure show it.
- **Chekhovian endings.** Unresolved situations with a resolved emotional insight.
- **Interiority.** Consciousness as action.
- **Moral ambiguity** sustained to the end.
Fails: beautiful sentences with no pressure, vagueness mistaken for ambiguity, epiphanies announced rather than earned.

### Satire and dark comedy
Works:
- **A clear target**, usually power, and a true thing the exaggeration reveals.
- **Horatian (gentle) vs. Juvenalian (savage).** Choose deliberately.
- **Deadpan.** The absurd presented as normal; the straight-faced institutional voice.
- **Escalation.** A premise pushed one logical step further each beat (Swift's "A Modest Proposal").
- **The straight man.** A sane observer measures the madness.
Fails: one joke stretched, a target too easy or too weak, cruelty toward victims rather than power. Satire involving real atrocities and real victims is the highest-risk register: the target has to be unmistakable.

### Poetry
Works:
- **The turn (volta).** The poem changes direction, register or understanding.
- **Image over statement.** A concrete thing carries the feeling.
- **Compression.** Every word load-bearing.
- **Refrain and repetition.** Accumulation, incantation, change through return.
- **Sound.** Rhythm, assonance, consonance; line breaks as breath and emphasis.
- **Forms as pressure.** Sonnet, villanelle, ghazal, haiku; constraint generating discovery.
- **Invented and borrowed language.** Neologism, code-switching and foreign register can name what plain speech can't, when anchored by context.
Fails: abstraction without image, explaining the image, a final line that summarizes.

---

## 11. Diagnostic questions (for finding gaps, then asking user_name)
1. Whose story is it, and what do they want?
2. What opposes them, and does it want something?
3. What's at stake, for whom?
4. Why now?
5. Where does it turn?
6. Do you know the ending, or at least the final state?
7. What promise does the opening make, and does the ending pay it?
8. Does each scene change something?
9. Is the theme carried by a choice or by a speech?
10. For genre: does it answer the genre's core question (horror: why not leave; speculative: what does the rule cost; thriller: what's the clock; satire: what's the target; poetry: where's the turn)?

## 12. Openings, endings and prose
- **Openings.** Voice, a disruption, or a question. In medias res drops into action; a strong voice can open on anything.
- **Endings.** Closed, open, ironic, circular. The classic test is "surprising yet inevitable."
- **Concreteness.** Specific detail persuades.
- **Defamiliarization (Viktor Shklovsky).** Make the familiar strange so it's seen again.
- **Show and tell.** Showing dramatizes; telling summarizes. Both are tools; tell when the moment doesn't need a scene.
- **Rhythm.** Vary sentence length; long sentences for accumulation, short for impact.

## 13. What has empirical support (and how much)
- **Narrative transportation** (Green and Brock, 2000, and later work): absorption in a story is measurable and associated with belief and attitude change. Supports the general claim that immersion matters.
- **Emotional arcs** (Reagan et al., 2016): six dominant shapes in a large public-domain corpus, with some associated with higher downloads. Correlational, one corpus.
- **Bestseller text features** (Archer and Jockers, *The Bestseller Code*, 2016): claimed machine-learning prediction of bestsellers from text features, such as a strong emotional rhythm and a focused topic set. Interesting but commercially framed and debated.
- **Suspense and spoilers** (Leavitt and Christenfeld, 2011): readers in one study enjoyed spoiled short stories slightly more. Suggests anticipation isn't only about uncertainty. Replication has been mixed.
- Everything else here is craft tradition. Present it as such.
'''

# ====================
# 3-6. ENGINES idea, lit, cherish, meta: kept in engines/ beside this file
# ====================
# Each is its own file (engines/idea.py, lit.py, cherish.py, meta.py), loaded by the launcher
# below as calliope.py loads the persona engine. The program's hash covers all four.

# ====================
# 7. STATE (kept in calliope_state.json beside this file)
# ====================
# Every rating, CherishedValue, META observation and persona exploration lives in
# calliope_state.json, one section per engine. RN check-ins stay in health/ (local
# only). Keeping state out of this file keeps every file under the 256 KiB
# per-file size budget.

# ====================
# 8. Launcher
# ====================
_ENV = {"idea": "ASSAY_LEDGER", "lit": "ASSAY_LIT_LEDGER", "cherish": "CHERISH_STATE", "meta": "META_STATE",
        "persona": "PERSONA_STATE"}
ENGINE_DIR = "engines"                   # the engines' folder, beside this file
_SRC = ("idea", "lit", "cherish", "meta")  # travel with the program: in the zip, and its hash
PERSONA_FILE = "engines/persona.py"      # the persona engine: never in the zip
_STATE_ENGINES = ("cherish", "meta", "persona")
_ARCHIVE = {}

PROGRAM_FILE = "calliope.py"
STATE_FILE = "calliope_state.json"
STATE_FORMAT = "calliope-state-1"
READ_LIMIT = 262144      # per-file size budget: what an agent tool can read whole in one piece
SIZE_WARN = 235000       # status and release warn when a file passes this
_BLANK = {"idea": {"rules_version": "assay-2.1", "ratings": [], "predictions": []},
          "lit": {"rules_version": "assay-lit-1.1", "ratings": []},
          "cherish": {"values": [], "triggered": []},
          "meta": {"observations": [], "traits": [], "next_id": 1, "scans": []},
          "persona": {"explorations": [], "next_id": 1}}
_OVERRIDE = []           # state paths pushed by the self-tests, so they never touch real state


def _load_archive(path):
    """Parse the chat archive once per run; CHERISH and META share it."""
    if path not in _ARCHIVE:
        with open(path, encoding="utf-8") as f:
            _ARCHIVE[path] = json.load(f)
    return _ARCHIVE[path]


def _out_dir():
    """Where updated copies and releases go: $CALLIOPE_OUT, else the folder beside this file."""
    d = os.environ.get("CALLIOPE_OUT")
    if d and os.path.isdir(d):
        return d
    return os.path.dirname(SELF)


def _writable(path):
    return os.access(path, os.W_OK) and os.access(os.path.dirname(os.path.abspath(path)), os.W_OK)


def _state_home():
    """Where calliope_state.json lives: $CALLIOPE_STATE, else beside this file, else the cwd."""
    if _OVERRIDE:
        return _OVERRIDE[-1]
    env = os.environ.get("CALLIOPE_STATE")
    if env:
        return os.path.abspath(env)
    for d in (os.path.dirname(SELF), os.getcwd()):
        p = os.path.join(d, STATE_FILE)
        if os.path.exists(p):
            return p
    return os.path.join(os.path.dirname(SELF), STATE_FILE)


def _state_path():
    """The copy holding the newest state: the home copy, or the updated copy made when that one is read-only."""
    home = _state_home()
    fb = os.path.join(_out_dir(), STATE_FILE)
    if (not _OVERRIDE and os.path.exists(home) and not _writable(home)
            and os.path.abspath(fb) != os.path.abspath(home) and os.path.exists(fb)):
        return fb
    return home


def _encode_state(st):
    return json.dumps(st, indent=1, ensure_ascii=False) + "\n"


def _blank_state():
    return json.loads(json.dumps({"format": STATE_FORMAT, **_BLANK}))


def _load_state_file():
    p = _state_path()
    if not os.path.exists(p):
        raise SystemExit(f"{STATE_FILE} not found (looked beside {os.path.basename(SELF)} and in the current folder). "
                         "It holds every rating and record: load it from your copy or the newest calliope_release.zip, "
                         "or set CALLIOPE_STATE to its path. Nothing was changed.")
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _read_ledger(name):
    sec = _load_state_file().get(name)
    return json.loads(json.dumps(sec if sec is not None else _BLANK[name]))


def _write_state(name, db):
    """Replace one engine's section of calliope_state.json, atomically (temp file, then rename)."""
    p = _state_path()
    st = _load_state_file()
    st.setdefault("format", STATE_FORMAT)
    st[name] = db
    text = _encode_state(st)
    if _OVERRIDE or _writable(p):
        _atomic_write(p, text)
        return
    target = os.path.join(_out_dir(), STATE_FILE)
    if os.path.abspath(target) == os.path.abspath(p):
        raise SystemExit(f"{p} is read-only and there is no other output folder; set CALLIOPE_OUT")
    _atomic_write(target, text)
    print(f"({p} is read-only; updated copy written to {target}: it goes into the next release)")


_CACHE = {}


def _rn_path():
    """The RN's store, health/vitals.json. LOCAL-ONLY: used where a health/ folder already sits beside the program, never created."""
    d = os.path.join(os.path.dirname(_OVERRIDE[-1] if _OVERRIDE else SELF), "health")
    return os.path.join(d, "vitals.json") if os.path.isdir(d) else None


def _rn_load():
    p = _rn_path()
    return json.load(open(p, encoding="utf-8")) if p and os.path.exists(p) else {"vitals": [], "reprompt": None}


def _rn_save(rn):
    if not _rn_path():
        raise SystemExit("no health/ folder beside the program: RN data was not saved")
    _atomic_write(_rn_path(), json.dumps(rn, indent=1, ensure_ascii=False) + "\n")


def _persona_file(prog=None):
    return os.path.join(os.path.dirname(os.path.abspath(prog or SELF)), PERSONA_FILE)


def _engine_file(name, prog=None):
    return os.path.join(os.path.dirname(os.path.abspath(prog or SELF)), ENGINE_DIR, f"{name}.py")


def _engines(prog=None):
    """The engines a copy of the program has: the four that travel with it, plus persona where its file is there."""
    return list(_SRC) + (["persona"] if os.path.exists(_persona_file(prog)) else [])


def _program_files(prog=None):
    """calliope.py and the four engines that travel with it, in hash order."""
    return [os.path.abspath(prog or SELF)] + [_engine_file(n, prog) for n in _SRC]


def _program_sha(prog=None):
    """One hash for the program: calliope.py and its four engines, each by name and content."""
    h = hashlib.sha256()
    for p in _program_files(prog):
        if not os.path.exists(p):
            raise SystemExit(f"{os.path.relpath(p, os.path.dirname(os.path.abspath(prog or SELF)))} is missing: "
                             "the program needs calliope.py and engines/ together; restore it from git or the release")
        h.update(os.path.basename(p).encode() + b"\0" + open(p, "rb").read() + b"\0")
    return h.hexdigest()[:16]


def _program_size(prog=None):
    return sum(os.path.getsize(p) for p in _program_files(prog) if os.path.exists(p))


def _source(name):
    """(source, label) for one engine: embedded here, except persona, which is read from the file beside the program."""
    if name in _SRC:
        p = _engine_file(name)
        try:
            with open(p, encoding="utf-8") as f:
                return f.read().replace(TOKEN, USER), p
        except (OSError, UnicodeError) as e:
            raise SystemExit(f"{ENGINE_DIR}/{name}.py could not be read ({e}); restore it from git or the release")
    if not os.path.exists(_persona_file()):
        raise SystemExit(f"the persona engine is kept beside the program as {PERSONA_FILE}; it is not here.")
    try:
        with open(_persona_file(), encoding="utf-8") as f:
            return f.read().replace(TOKEN, USER), _persona_file()
    except (OSError, UnicodeError) as e:
        raise SystemExit(f"{PERSONA_FILE} could not be read ({e}); restore it from git")


def _engine(name):
    """Load one engine as its own module, with its ledger (or state) redirected into calliope_state.json."""
    if name in _CACHE:
        return _CACHE[name]
    src, label = _source(name)
    mod = types.ModuleType(f"calliope_{name}")
    mod.__dict__.update(__name__=f"calliope_{name}", __file__=SELF)
    sys.modules[mod.__name__] = mod          # dataclasses look their module up here
    if name == "lit":                        # ASSAY-LIT takes coherence from ASSAY (engines/idea.py) as it loads
        mod.ENGINES = lambda n: _engine(n) if n == "idea" else None
    try:
        exec(compile(src, label, "exec"), mod.__dict__)
    except SyntaxError as e:                 # an engine file edited and not yet released
        del sys.modules[mod.__name__]
        raise SystemExit(f"{os.path.basename(label)} could not be loaded: {e}. Fix that line or restore the file from git.")
    ext = os.environ.get(_ENV[name])
    if name in _STATE_ENGINES:
        empty = mod.load_state()                 # the engine's own blank state
        if ext:
            mod.load_state = lambda: json.load(open(ext)) if os.path.exists(ext) else json.loads(json.dumps(empty))
            mod.save_state = lambda st: json.dump(st, open(ext, "w"), indent=2)
        else:
            mod.load_state = lambda: _read_ledger(name)
            mod.save_state = lambda st: _write_state(name, st)
        mod.ENGINES = lambda n: _engine(n) if n in ("idea", "lit") else None
        mod.LOAD_ARCHIVE = _load_archive
    if name == "cherish":
        mod.DESIGN = {"persona_registry": REGISTRY, "story_guidebook": GUIDEBOOK}
    if name == "persona":
        mod.REGISTRY, mod.MENU = REGISTRY, _persona_codes
    if name == "meta":
        mod.CHERISH_STATE = lambda: _engine("cherish").load_state()
        mod.load_rn, mod.save_rn, mod.RN_HERE = _rn_load, _rn_save, lambda: bool(_rn_path())
    elif name not in _STATE_ENGINES and not ext:
        mod.load = lambda: _read_ledger(name)
        mod.save = lambda db: _write_state(name, {**db, "rules_version": mod.RULES_VERSION})
    _CACHE[name] = mod
    return mod


def _stray(doc, cmd, args):
    """A one-line answer when ARGS holds an option that CMD's usage line in DOC does not list, else None."""
    use = [u for u in (re.split(r"\s{3,}", l.strip())[0] for l in (doc or "").splitlines() if re.match(r"    \S", l))
           if re.search(rf"(^|\.py |\| ){re.escape(cmd)}\b", u)]
    takes, skip = dict(re.findall(r"(--[\w-]+)( [^]\s]+)?", " ".join(use))), False
    for a in args if use else ():
        if skip or not re.fullmatch(r"--?[A-Za-z][\w-]*", a):
            skip = False             # a value, or not shaped like an option
        elif a in takes:
            skip = bool(takes[a])    # listed with a value: skip that value
        else:
            return f"{cmd} doesn't take {a}; nothing was done. Usage: {' | '.join(use)}"


def _run(name, args):
    mod = _engine(name)
    bad = args and _stray(mod.__doc__, args[0], args[1:])
    if bad:
        print(bad); return 1
    try:
        return mod.main(args) or 0
    except getattr(mod, "RatingError", ()) as e:
        print("rating error:", e); return 2
    except (IndexError, StopIteration, FileNotFoundError) as e:
        what = f"no such file: {e.filename}" if isinstance(e, FileNotFoundError) else "an argument is missing or names nothing on record"
        print(f"{name} {' '.join(args[:1])}: {what}; try {name} --help"); return 1


# --------------------
# Session tools: status, release, sync, glossary
# --------------------
DATA_FILE = "CALLIOPE_DATA.md"
RELEASE_ZIP = "calliope_release.zip"
ARCHIVE_NAMES = ("calliope_archive.json",)
_DATA_STEMS = ("CALLIOPE_DATA",)
_AUTO = ("<!-- AUTO:BEGIN -->", "<!-- AUTO:END -->")
_LOG = ("<!-- LOG:BEGIN -->", "<!-- LOG:END -->")
LOG_KEEP = 12
_REL = re.compile(r"\b(\d{4}-\d{2}-\d{2})\.(\d+)\b")

PROTOCOL = """\
## Session protocol (the agent: follow this whenever this file is loaded)
1. **Read this file first; load the program only when it's needed.** Conversation needs only this file. Run the program when the session rates, logs, reviews (/meta, /cherish), checks in (/status) or releases. `calliope.py` (with its `engines/` folder), `calliope_state.json` and this file stay together in the CALLIOPE_ZED folder; `zed.py` beside them makes the documents (Snapshots, briefs, STUDYBOOK) and new personas.
2. **Check in.** Run `python3 calliope.py status --quick`. If it reports a problem (program or state differs from the release below, a failed test, a file near the size limit), say so in one line; otherwise just start.
3. **Work.** Ratings, META logs, CHERISH values and persona explorations are written to `calliope_state.json` only through the program's commands. Keep "Open threads" current: an item is an idea of user_name's (their exact words, with date and time), a decision, or work left open. Keep what is verifiably user_name's apart from what Calliope furnished.
4. **Close.** When anything changed, the session isn't done until a release exists: update "Open threads" and run `python3 calliope.py release --note "<what changed, one line>"`.

Shorthand: /status · /release · /meta · /cherish · `show persona menu -x` · convene the Council · catch me up on [topic] · take a snapshot of [moment] · /studybook. Full list: `python3 calliope.py glossary`.""".replace(TOKEN, USER)

DATA_HEAD = """# CALLIOPE_DATA (session file)
This file lives beside `calliope.py` and `calliope_state.json` in the CALLIOPE_ZED folder and is read at the start of a session. The program holds the engines, the state file holds every rating and record, and this file carries the session protocol, the release stamp and the open threads between sessions. Everything between the AUTO markers is written by `release`; the rest is kept as written.
"""
DATA_TAIL = """
## Open threads
- (none recorded)

## Session log
<!-- LOG:BEGIN -->
<!-- LOG:END -->
"""

SHORTHAND = [
    ("/status", "Health and state check at any point: python3 calliope.py status."),
    ("/release", "Close-out: update Open threads, run python3 calliope.py release --note \"...\"."),
    ("/sync [CODE]", "Confirm two copies match: python3 calliope.py sync prints one code for the three files; sync --expect CODE names any file that differs."),
    ("/meta", "Run a META review batch now (meta review); answer each candidate with confirm, reject or park."),
    ("/cherish [VALUE] [IDEA]", "CherishedValue analysis (cherish inline \"<message>\"), optionally one value and one rated idea."),
    ("show persona menu -x", "Opens the hidden persona menu; reply with a persona code."),
    ("convene the Council", "Two to four relevant personas speak in turn; disagreements noted; one synthesis with a rating."),
    ("new persona [name]", "Write a blank persona card into personas/REGISTRY.md and add it to the menu: python3 zed.py persona new \"Name\"."),
    ("catch me up on [topic]", "A brief bringing user_name to the present state of a field, closing with where their own thinking meets it: python3 zed.py brief new \"topic\", fill it in, python3 zed.py brief render."),
    ("take a snapshot of [moment]", "A one-page field record of a moment: python3 zed.py snapshot new \"name\", fill it in, python3 zed.py snapshot render."),
    ("/studybook", "Rebuild STUDYBOOK, the folder of whole collections to read: python3 zed.py studybook."),
    ("BUILD · EXPAND · RATE · COMPILE · COLD", "Fiction collaborator moves under the influence guard; full protocol: lit session."),
]
ENVVARS = [
    ("CALLIOPE_STATE", "path to calliope_state.json when it isn't beside calliope.py"),
    ("ASSAY_LEDGER", "use an external idea-ledger file instead of the idea section of calliope_state.json"),
    ("ASSAY_LIT_LEDGER", "the same for the fiction ledger"),
    ("CHERISH_STATE", "the same for CHERISH's values and trigger log"),
    ("META_STATE", "the same for META's observations, traits and scans"),
    ("PERSONA_STATE", "the same for the persona explorations"),
    ("CALLIOPE_OUT", "folder for updated copies and release files (default: the folder beside calliope.py)"),
    ("CALLIOPE_ARCHIVE", "path to the chat archive"),
]
FILES = [
    ("calliope.py", "The program: launcher, story guidebook and session tools. Changes only when the code does. Travels with engines/."),
    ("engines/", "The engines: idea.py, lit.py, cherish.py, meta.py and persona.py."),
    ("calliope_state.json", "Every rating, CherishedValue, META observation and persona exploration, one section per engine."),
    ("personas/REGISTRY.md", "The persona registry: the rules every persona follows, the cards, the Council and the menu."),
    ("CALLIOPE_DATA.md", "The session file: protocol, release stamp, open threads, session log."),
    ("zed.py", "First run (init), and the documents: snapshot, brief, studybook, and persona new."),
    ("calliope_release.zip", "The close-out package: calliope.py, its engines, calliope_state.json and CALLIOPE_DATA.md."),
]
FLOW = [
    ("Start", "Open your agent (any agentic LLM tool) in the CALLIOPE_ZED folder. The agent reads CALLIOPE_DATA.md and runs status."),
    ("Work", "Rate, log, review, explore with personas and make documents. State changes only through the program's commands."),
    ("Close", "/release: The agent updates Open threads and runs release --note \"...\"."),
]


def _opt(args, flag):
    if flag in args:
        i = args.index(flag)
        if i + 1 < len(args):
            return args[i + 1]
        raise SystemExit(f"{flag} needs a value")
    return None


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _atomic_write(path, text):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


def _tests(path):
    """Run every self-test in a child process against the file at `path`. Returns (ok, summary)."""
    try:
        p = subprocess.run([sys.executable, path, "selftest"], capture_output=True, text=True, timeout=600)
    except Exception as e:                                   # noqa: BLE001
        return False, f"could not run the self-tests ({e})"
    out, got = p.stdout + p.stderr, {}
    for line in out.splitlines():
        m = re.match(r"\s*(\d+)/(\d+) passed", line)
        if m:
            got["idea"] = f"{m.group(1)}/{m.group(2)}"
            continue
        m = re.match(r"\s*(cherish |meta |persona |launcher )?selftest: (\d+) checks passed", line)
        if m:
            got[(m.group(1) or "lit ").strip()] = f"{m.group(2)}/{m.group(2)}"
    names = _engines(path) + ["launcher"]
    ok = p.returncode == 0 and all(n in got for n in names) and "FAILED" not in out and "Traceback" not in out
    summary = " · ".join(f"{n} {got.get(n, 'FAILED')}" for n in names)
    if not ok:
        tail = [l for l in out.strip().splitlines() if l.strip()][-1:]
        summary += f" (exit {p.returncode}" + (f": {tail[0][:160]}" if tail else "") + ")"
    return ok, summary


def _find_data(explicit=None):
    """The session file: the path given, else the newest *CALLIOPE_DATA*.md."""
    if explicit:
        return explicit if os.path.isfile(explicit) else None
    roots = [os.getcwd(), os.path.dirname(SELF), _out_dir()]
    for stem in _DATA_STEMS:
        hits = set()
        for r in roots:
            for pat in (f"*{stem}*.md", os.path.join("*", f"*{stem}*.md")):
                hits.update(glob.glob(os.path.join(r, pat)))
        hits = [h for h in hits if os.path.isfile(h)]
        if hits:
            return max(hits, key=os.path.getmtime)
    return None


def _between(text, marks):
    a, b = text.find(marks[0]), text.find(marks[1])
    return (a, b) if 0 <= a < b else (None, None)


def _stamp(text):
    """(release id, program sha, state sha) recorded in a session file's AUTO block."""
    a, b = _between(text, _AUTO)
    block = text[a:b] if a is not None else ""
    rel = re.search(r"Release:\s*(\d{4}-\d{2}-\d{2}\.\d+)", block)
    prog = re.search(r"Program:[^\n]*?sha256\s+([0-9a-f]{12,64})", block)
    state = re.search(r"State:[^\n]*?sha256\s+([0-9a-f]{12,64})", block)
    return tuple(m.group(1) if m else None for m in (rel, prog, state))


def _next_release(text):
    """Today's date plus a sequence number, continuing from any release id already recorded today."""
    today = datetime.date.today().isoformat()
    seqs = [int(n) for d, n in _REL.findall(text or "") if d == today]
    return f"{today}.{max(seqs) + 1 if seqs else 1}"


def _log_add(text, rel, note):
    """Append one line to the session log; past LOG_KEEP entries, the oldest roll into one summary line."""
    a, b = _between(text, _LOG)
    if a is None:
        text = text.rstrip() + "\n\n## Session log\n" + _LOG[0] + "\n" + _LOG[1] + "\n"
        a, b = _between(text, _LOG)
    body = [l for l in text[a + len(_LOG[0]):b].splitlines() if l.strip()]
    early = next((l for l in body if l.startswith("- Earlier:")), None)
    entries = [l for l in body if not l.startswith("- Earlier:")] + [f"- {rel}: {' '.join(note.split())}"]
    if len(entries) > LOG_KEEP:
        old, entries = entries[:-LOG_KEEP], entries[-LOG_KEEP:]
        ids = [m.group(0) for m in (_REL.search(l) for l in old) if m]
        prev_n, first = 0, None
        m = re.match(r"- Earlier: (\d+) releases?, (\S+) to (\S+)", early or "")
        if m:
            prev_n, first = int(m.group(1)), m.group(2)
        k = prev_n + len(old)
        early = (f"- Earlier: {k} release{'' if k == 1 else 's'}, {first or (ids[0] if ids else '?')} "
                 f"to {ids[-1] if ids else '?'} (notes rolled up)")
    new = "\n".join(([early] if early else []) + entries)
    return text[:a + len(_LOG[0])] + "\n" + new + "\n" + text[b:]


def _size_notes(paths):
    """Warnings for files near or over the per-file size budget."""
    notes = []
    for p in paths:
        if p and os.path.exists(p):
            n = os.path.getsize(p)
            if n > READ_LIMIT:
                notes.append(f"{os.path.basename(p)} is {n:,} bytes, over the {READ_LIMIT:,} an agent tool may read "
                             "in one piece: trim or split it")
            elif n > SIZE_WARN:
                notes.append(f"{os.path.basename(p)} is {n:,} bytes, close to the {READ_LIMIT:,}-byte per-file size budget")
    return notes


def _state():
    """Counts for status and the release stamp, read straight from calliope_state.json."""
    idea, lit = _read_ledger("idea"), _read_ledger("lit")
    ch, me, pe = _read_ledger("cherish"), _read_ledger("meta"), _read_ledger("persona")
    today = datetime.date.today().isoformat()
    rs, lit_rs = idea.get("ratings", []), lit.get("ratings", [])
    by = {k: sum(1 for r in rs if r.get("rater") == k) for k in "CIP"}
    preds = [p for p in idea.get("predictions", []) if p.get("outcome") is None]
    due = [p for p in preds if str(p.get("due", "9999")) <= today]
    obs = me.get("observations", [])
    n = lambda *st: sum(1 for o in obs if o.get("status") in st)
    try:
        waiting = len(_engine("meta").queue(me))
    except Exception:                                        # noqa: BLE001
        waiting = n("candidate")
    try:
        builtin = len(getattr(_engine("cherish"), "BUILTIN", {}))
    except Exception:                                        # noqa: BLE001
        builtin = 0
    scan = (me.get("scans") or [None])[-1]
    rn = _rn_load()
    rp = rn.get("reprompt")
    rp_text = (f"{rp.get('when')} (set {rp.get('set')})" if isinstance(rp, dict) else str(rp)) if rp else "none"
    lines = [
        f"Ideas: {len({r['idea'] for r in rs})} ideas, {len(rs)} ratings (collaborator {by['C']}, cold {by['I']}, "
        f"panel {by['P']}) · predictions open {len(preds)}" + (f", {len(due)} past due" if due else ""),
        f"Fiction: {len({r['idea'] for r in lit_rs})} ideas, {len(lit_rs)} ratings",
        f"META: {waiting} awaiting review · {n('confirmed', 'promoted')} confirmed · {n('rejected')} rejected · "
        f"{n('parked')} parked · {len(me.get('traits', []))} traits · last scan "
        + (f"{scan.get('date')} ({scan.get('chats')} chats)" if scan else "never"),
        f"CHERISH: {builtin} built-in value(s) + {len(ch.get('values', []))} added · "
        f"{len(ch.get('triggered', []))} triggers logged",
        f"Personas: {len(pe.get('explorations', []))} exploration(s) on record",
        "RN: local only (readings stay in health/ in this folder; none are recorded here)",
    ]
    return lines, {"waiting": waiting, "scan_chats": (scan or {}).get("chats") or 0, "reprompt": rp_text if rp else "",
                   "due": len(due),
                   "rn": f"{len(rn['vitals'])} check-ins · re-prompt: {rp_text} (local only)" if _rn_path() else ""}


def _status(args):
    data = _find_data(_opt(args, "--data"))
    sha, size = _program_sha(), _program_size()
    sp = _state_path()
    print(f"CALLIOPE STATUS · {datetime.date.today().isoformat()}")
    print(f"  Program   {SELF} + {ENGINE_DIR}/ ({len(_SRC)}) · {size:,} bytes · sha256 {sha}")
    if not os.path.exists(sp):
        print(f"  State     {STATE_FILE} NOT FOUND beside the program: load it before working (nothing else can run)")
        return 1
    ssha = _sha(sp)
    print(f"  State     {sp} · {os.path.getsize(sp):,} bytes · sha256 {ssha}")
    stale = []
    if not data:
        print(f"  Release   no {DATA_FILE} found (pass --data FILE)")
    else:
        rel, rec, rec_state = _stamp(open(data, encoding="utf-8").read())
        name = os.path.basename(data)
        if not rec:
            print(f"  Release   {name} has no release stamp yet (older format); the next release adds one")
        else:
            stale = ([] if rec == sha else ["program"]) + (["state"] if rec_state and rec_state != ssha else [])
            if not stale:
                print(f"  Release   matches {rel} recorded in {name}"
                      + ("" if rec_state else " (program only: this stamp predates the state file)"))
            else:
                print(f"  Release   {' and '.join(stale)} DIFFER{'S' if len(stale) == 1 else ''} from {rel} recorded in {name}. "
                      "At the start of a session this means the copies are stale: load them from the newest "
                      "calliope_release.zip. Mid-session, state changes are expected after ratings or logs.")
    if "--quick" not in args:
        ok, summary = _tests(SELF)
        print(f"  Tests     {summary}" + ("" if ok else "  <- fix before release"))
    lines, st = _state()
    for line in lines:
        key, _, val = line.partition(": ")
        print(f"  {key:<9} {st['rn'] if key == 'RN' and st['rn'] else val}")
    notes = _size_notes(_program_files() + [sp, data])
    print("  Sizes     " + ("; ".join(notes) if notes else f"every file under {SIZE_WARN:,} bytes (per-file size budget {READ_LIMIT:,})"))
    try:
        meta = _engine("meta")
        ap = meta._archive_path()
        chats = len(meta.load_chats()) if ap else 0
    except Exception:                                        # noqa: BLE001
        ap, chats = None, 0
    print("  Archive   " + (f"{os.path.basename(ap)} · {chats} chats" if ap else
                            f"not loaded (load {ARCHIVE_NAMES[0]} only for meta scan or cherish analyze)"))
    nxt = []
    if stale:
        nxt.append("at the start of a session: load calliope.py and calliope_state.json from the newest release")
    if notes:
        nxt.append("bring the large file back under the read limit")
    if ap and chats > st["scan_chats"]:
        nxt.append(f"meta scan (archive {chats} chats; last scan saw {st['scan_chats']})")
    if st["waiting"]:
        nxt.append(f"meta review 5 ({st['waiting']} waiting)")
    if st["reprompt"]:
        nxt.append(f"RN re-prompt pending: {st['reprompt']}")
    if st["due"]:
        nxt.append(f"idea resolve ({st['due']} prediction(s) past due)")
    print("  Next      " + (" · ".join(nxt) if nxt else "nothing pending"))
    return 0


def _release(data=None, out=None, note="", run_tests=True, force=False):
    """Self-test, restamp the session file, and write calliope_release.zip (calliope.py, calliope_state.json, CALLIOPE_DATA.md)."""
    sp = _state_path()
    if not os.path.exists(sp):
        raise SystemExit(f"release stopped: {STATE_FILE} not found beside the program. Nothing was written.")
    summary = "not run"
    if run_tests:
        ok, summary = _tests(SELF)
        if not ok and not force:
            raise SystemExit(f"release stopped: self-tests failed ({summary}). Nothing was written. "
                             "Fix the failure, or pass --force to ship it marked UNTESTED.")
        if not ok:
            summary += " · SHIPPED UNTESTED (--force)"
    out = out or _out_dir()
    os.makedirs(out, exist_ok=True)
    text = (open(data, encoding="utf-8").read() if data else
            DATA_HEAD + "\n" + _AUTO[0] + "\n" + _AUTO[1] + "\n" + DATA_TAIL)
    rel = _next_release(text)
    sha, size = _program_sha(), _program_size()
    ssha, ssize = _sha(sp), os.path.getsize(sp)
    lines, _ = _state()
    block = "\n".join([_AUTO[0], PROTOCOL, "", "## Release (written by `release`; don't edit)",
                       f"- Release: {rel}",
                       f"- Program: `{PROGRAM_FILE}` + `{ENGINE_DIR}/` ({', '.join(_SRC)}) · {size:,} bytes · sha256 {sha}",
                       f"- State: `{STATE_FILE}` · {ssize:,} bytes · sha256 {ssha}",
                       f"- Self-tests: {summary}"] + [f"- {l}" for l in lines] +
                      [f"- Archive: {ARCHIVE_NAMES[0]}; load it only for meta scan, cherish analyze or a CATCH ME UP",
                       _AUTO[1]])
    a, b = _between(text, _AUTO)
    if a is None:
        i = text.find("\n## ")
        text = (text[:i] + "\n\n" + block + "\n" + text[i:]) if i >= 0 else (text.rstrip() + "\n\n" + block + "\n")
    else:
        text = text[:a] + block + text[b + len(_AUTO[1]):]
    if note.strip():
        text = _log_add(text, rel, note)
    md_out = os.path.join(out, DATA_FILE)
    _atomic_write(md_out, text)
    zpath = os.path.join(out, RELEASE_ZIP)
    with zipfile.ZipFile(zpath + ".tmp", "w", zipfile.ZIP_DEFLATED) as z:
        z.write(SELF, PROGRAM_FILE)
        for n in _SRC:
            z.write(_engine_file(n), f"{ENGINE_DIR}/{n}.py")
        z.write(sp, STATE_FILE)
        z.write(md_out, DATA_FILE)
    os.replace(zpath + ".tmp", zpath)
    return {"release": rel, "program": SELF, "size": size, "sha": sha, "state": sp, "state_size": ssize,
            "state_sha": ssha, "tests": summary, "data": md_out, "zip": zpath,
            "notes": _size_notes(_program_files() + [sp, md_out])}


def _sync_parts(data):
    """(file name, path, 8-hex sha256) for the program, the state file and the session file, in sync-code order."""
    return [(PROGRAM_FILE, SELF, _program_sha()[:8]), (STATE_FILE, _state_path(), _sha(_state_path())[:8]),
            (DATA_FILE, data, _sha(data)[:8])]


def _sync_code(data):
    return "-".join(sha for _, _, sha in _sync_parts(data))


def _sync_diff(data, code):
    """Names of the files whose hash differs from the matching part of another copy's sync code."""
    want = code.strip().lower().split("-")
    if len(want) != 3 or not all(re.fullmatch(r"[0-9a-f]{8}", w) for w in want):
        raise SystemExit("a sync code is three 8-character parts, program-state-session, like 30c09ea5-39d6da02-1a2b3c4d")
    return [name for (name, _, sha), w in zip(_sync_parts(data), want) if sha != w]


def _sync(args):
    data = _find_data(_opt(args, "--data"))
    if not data or not os.path.exists(_state_path()):
        missing = STATE_FILE if data else DATA_FILE
        print(f"sync needs all three files; {missing} was not found" + ("" if data else " (pass --data FILE)"))
        return 1
    expect = _opt(args, "--expect")
    diff = _sync_diff(data, expect) if expect else []
    rel = _stamp(open(data, encoding="utf-8").read())[0]
    print(f"CALLIOPE SYNC · release {rel or 'not stamped'}")
    for name, path, sha in _sync_parts(data):
        mark = ("  DIFFERS" if name in diff else "  matches") if expect else ""
        print(f"  {name:<20} {os.path.getsize(path):>9,} bytes · {sha}{mark}")
    print(f"  Sync code  {_sync_code(data)}")
    if not expect:
        print("On the other copy, run: python calliope.py sync --expect " + _sync_code(data))
        return 0
    if diff:
        print(f"OUT OF SYNC: {', '.join(diff)} differ{'s' if len(diff) == 1 else ''} from the copy that gave {expect.strip().lower()}. "
              "Replace with the files from the newer release.")
        return 1
    print("IN SYNC: all three files are byte-identical to the copy that gave this code.")
    return 0


def _usage_rows(doc):
    """Rows of (command, description) from a docstring's USAGE block."""
    lines = (doc or "").splitlines()
    for i, line in enumerate(lines):
        if not line.startswith("USAGE"):
            continue
        m = re.search(r"\(prefix: ([^)]+)\)", line)
        prefix, rows = (m.group(1).strip() if m else ""), []
        for l2 in lines[i + 1:]:
            if not l2.strip() or not l2.startswith(" "):
                break
            body = l2.strip()
            if body.startswith("in chat:") and rows:
                rows[-1][1] += ("; " if rows[-1][1] else "") + body
                continue
            parts = re.split(r"\s{2,}", body, maxsplit=1)
            rows.append([f"{prefix} {parts[0]}".strip(), parts[1] if len(parts) > 1 else ""])
        return rows
    return []


def _persona_codes(text=None):
    """[code, name] rows from the persona menu of a registry (this one unless another is given). The persona engine reads its menu here too."""
    text = REGISTRY if text is None else text
    rows, sec = [], text[text.find("## Section D"):text.find("## Maintenance")]
    for line in sec.splitlines():
        m = re.match(r"\s{2,}- (.+)", line)
        if m and re.match(r"[A-Z0-9]{1,2} ", m.group(1)):
            for item in m.group(1).split(" · "):
                code, _, name = item.partition(" ")
                rows.append([code, name])
    return rows


def _glossary():
    titles = {"idea": "ASSAY 2: ideas (python calliope.py idea ...)",
              "lit": "ASSAY-LIT: fiction and poetry (python calliope.py lit ...)",
              "cherish": "CHERISH: CherishedValues (python calliope.py cherish ...)",
              "meta": "META: metadevelopments and RN vitals (python calliope.py meta ...)",
              "persona": "PERSONA: explorations with a persona (python calliope.py persona ...)"}
    secs = [
        {"title": "Session flow", "rows": [list(r) for r in FLOW]},
        {"title": "In-chat shorthand", "intro": "Typed in chat; the agent runs the matching command.",
         "rows": [list(r) for r in SHORTHAND]},
        {"title": "Persona codes", "intro": "Reply with a code after show persona menu -x; 0 returns to the plain agent.",
         "rows": _persona_codes()},
        {"title": "Launcher (python calliope.py ...)", "rows": _usage_rows(__doc__)},
    ]
    secs += [{"title": titles[n], "rows": _usage_rows(_engine(n).__doc__)} for n in _engines()]
    secs += [{"title": "Environment variables", "rows": [list(r) for r in ENVVARS]},
             {"title": "Files", "rows": [list(r) for r in FILES]}]
    return {"title": "Calliope command glossary", "generated": datetime.date.today().isoformat(),
            "program_sha256": _program_sha(), "sections": secs}


def _glossary_md(g):
    cell = lambda x: str(x).replace("|", "\\|")
    L = [f"# {g['title']}", "", f"Generated {g['generated']} from calliope.py (sha256 {g['program_sha256']}).", ""]
    for s in g["sections"]:
        L += [f"## {s['title']}", ""] + ([s["intro"], ""] if s.get("intro") else [])
        L += ["| Command | What it does |", "|---|---|"] + [f"| `{cell(c)}` | {cell(d)} |" for c, d in s["rows"]] + [""]
    return "\n".join(L)


def _selftest_launcher():
    n = 0

    def t(cond, msg):
        nonlocal n
        assert cond, msg
        n += 1
    today = datetime.date.today().isoformat()
    t(_next_release("") == f"{today}.1", "first release of the day")
    t(_next_release(f"- {today}.3: x") == f"{today}.4", "sequence continues")
    t(_next_release("- 2020-01-01.9: x") == f"{today}.1", "a new day restarts the sequence")
    text = "x\n" + _LOG[0] + "\n" + _LOG[1] + "\n"
    for i in range(LOG_KEEP + 3):
        text = _log_add(text, f"{today}.{i + 1}", f"note {i}")
    body = text[text.find(_LOG[0]):text.find(_LOG[1])]
    t(body.count("\n- ") == LOG_KEEP + 1 and "- Earlier: 3 releases" in body, "the log rolls up old entries")
    with tempfile.TemporaryDirectory() as d:
        sp = os.path.join(d, STATE_FILE)
        _atomic_write(sp, _encode_state(_blank_state()))
        _OVERRIDE.append(sp)
        try:
            md = os.path.join(d, "in.md")
            _atomic_write(md, "# t\n\n## Open threads\n- keep me\n")
            r = _release(md, out=d, note="first", run_tests=False)
            txt = open(r["data"], encoding="utf-8").read()
            t(_stamp(txt) == (r["release"], _program_sha(), _sha(sp)), "the stamp records the release, program and state hashes")
            t("- keep me" in txt and "## Session protocol" in txt and "zed.py" in txt, "hand-written sections kept, protocol added")
            with zipfile.ZipFile(r["zip"]) as z:
                eng = [f"{ENGINE_DIR}/{n}.py" for n in _SRC]
                t(sorted(z.namelist()) == sorted([PROGRAM_FILE, STATE_FILE, DATA_FILE] + eng),
                  "the zip holds program, its four engines, state and session file, and not the persona engine")
                t(hashlib.sha256(z.read(PROGRAM_FILE)).hexdigest()[:16] == _sha(SELF)
                  and all(z.read(e) == open(_engine_file(n), "rb").read() for e, n in zip(eng, _SRC))
                  and hashlib.sha256(z.read(STATE_FILE)).hexdigest()[:16] == _sha(sp), "the zipped files are the live ones")
            code = _sync_code(r["data"])
            t(re.fullmatch(r"[0-9a-f]{8}(-[0-9a-f]{8}){2}", code) and code.startswith(_program_sha()[:8])
              and _sync_diff(r["data"], code) == [], "a copy matches its own sync code")
            edited = os.path.join(d, "edited.md")
            _atomic_write(edited, txt + "- one more thread\n")
            t(_sync_diff(edited, code) == [DATA_FILE], "sync names the one file that differs")
            import contextlib, io
            refused = False
            try:
                _run("meta", ["vitals", "log", "sleep_h=test"])
            except SystemExit:
                refused = True
            t(refused, "with no health/ folder the RN saves nothing")
            os.mkdir(os.path.join(d, "health"))
            with contextlib.redirect_stdout(io.StringIO()):
                _run("meta", ["vitals", "log", "sleep_h=test"])
            t(_rn_load()["vitals"][0]["sleep_h"] == "test" and "sleep_h" not in open(sp, encoding="utf-8").read(),
              "an RN check-in stays in health/ and out of the state file")
            r2 = _release(r["data"], out=d, note="second", run_tests=False)
            with zipfile.ZipFile(r2["zip"]) as z:
                t(len(z.namelist()) == 3 + len(_SRC) and "RN: local only" in open(r2["data"], encoding="utf-8").read()
                  and "sleep_h" not in open(r2["data"], encoding="utf-8").read(), "a release carries nothing from health/")
            t(r2["release"].rsplit(".", 1)[1] == str(int(r["release"].rsplit(".", 1)[1]) + 1), "a second release increments")
            t(open(r2["data"], encoding="utf-8").read().count(_AUTO[0]) == 1, "one AUTO block after re-release")
            if "persona" in _engines():
                rec = os.path.join(d, "exploration.json")
                moves = [{"by": by, "kind": "ask", "text": "t"} for by in "JP"]
                _atomic_write(rec, json.dumps(dict(persona="Test", kind="type", lens="l", subject="s", idea="i", start="a",
                                                   end="b", moves=moves)))
                with contextlib.redirect_stdout(io.StringIO()):
                    filed = _run("persona", ["log", rec])
                t(filed == 0 and json.load(open(sp, encoding="utf-8"))["persona"]["explorations"][0]["id"] == "X1",
                  "the persona engine files an exploration in its own section")
            _write_state("cherish", {"values": [], "triggered": ["idea|v|x|v1"]})
            st = json.load(open(sp, encoding="utf-8"))
            t(st["cherish"]["triggered"] == ["idea|v|x|v1"] and st["meta"] == _BLANK["meta"]
              and st["format"] == STATE_FORMAT, "a state write replaces one section only")
            big = os.path.join(d, "big.txt")
            with open(big, "w") as f:
                f.write("x" * (READ_LIMIT + 1))
            t(_size_notes([big]) and "over" in _size_notes([big])[0] and not _size_notes([md]), "size guard flags a file over the read limit")
        finally:
            _OVERRIDE.pop()
    g = _glossary()
    t(all(any(s["title"].startswith(p) for s in g["sections"]) for p in ("ASSAY 2", "ASSAY-LIT", "CHERISH", "META")),
      "the glossary covers every engine")
    t(_stray(__doc__, "release", ["--note", "--x", "--help"]) and not _stray(__doc__, "release", ["--note", "-h", "--force"])
      and _stray(_engine("meta").__doc__, "park", ["M1", "-h"]), "a command refuses an option its usage line does not list")
    t(any(c == "C" for s in g["sections"] for c, _ in s["rows"]), "persona codes parsed from the registry")
    t(all(len(s["rows"]) >= 2 for s in g["sections"]), "no empty glossary section (a blank registry has the Council and the exit)")
    print(f"launcher selftest: {n} checks passed")
    return 0


def main(argv):
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__); return 0
    cmd, args = argv[0], argv[1:]
    if cmd in _ENV:
        return _run(cmd, args)
    bad = _stray(__doc__, cmd, args)
    if bad:
        print(bad); return 1
    if cmd == "registry":
        print(REGISTRY); return 0
    if cmd == "guidebook":
        print(GUIDEBOOK); return 0
    if cmd == "export":
        d = args[0] if args else "."
        os.makedirs(d, exist_ok=True)
        files = {"calliope_persona_registry.md": REGISTRY, "calliope_story_guidebook.md": GUIDEBOOK,
                 "assay_ledger.json": json.dumps(_read_ledger("idea"), indent=2),
                 "assay_lit_ledger.json": json.dumps(_read_ledger("lit"), indent=2),
                 "cherish_state.json": json.dumps(_read_ledger("cherish"), indent=2),
                 "meta_state.json": json.dumps(_read_ledger("meta"), indent=2),
                 "persona_state.json": json.dumps(_read_ledger("persona"), indent=2)}
        for fn, text in files.items():
            with open(os.path.join(d, fn), "w", encoding="utf-8") as f:
                f.write(text)
            print("wrote", os.path.join(d, fn))
        return 0
    if cmd == "import":
        if len(args) != 2 or args[0] not in ("idea", "lit"):
            print("usage: import idea|lit FILE"); return 1
        name, path = args
        if not os.path.exists(path):
            print("import: no such file:", path); return 1
        db = _read_ledger(name)
        ext = json.load(open(path))
        key = lambda r: json.dumps(r, sort_keys=True)
        seen = {key(r) for r in db.get("ratings", [])}
        new = [r for r in ext.get("ratings", []) if key(r) not in seen]
        db.setdefault("ratings", []).extend(new)
        if name == "idea":
            ids = {p["id"] for p in db.get("predictions", [])}
            db.setdefault("predictions", []).extend(p for p in ext.get("predictions", []) if p["id"] not in ids)
        _write_state(name, db)
        print(f"imported {len(new)} new ratings into the {name} ledger"); return 0
    if cmd == "selftest":
        with tempfile.TemporaryDirectory() as d:
            sp = os.path.join(d, STATE_FILE)
            _atomic_write(sp, _encode_state(_blank_state()))
            _OVERRIDE.append(sp)
            try:
                code = max(_run(n, ["selftest"]) for n in _engines())
                return max(code, _selftest_launcher())
            finally:
                _OVERRIDE.pop()
    if cmd == "status":
        return _status(args)
    if cmd == "release":
        data = _find_data(_opt(args, "--data"))
        if _opt(args, "--data") and not data:
            raise SystemExit(f"no such file: {_opt(args, '--data')}")
        if not data:
            print(f"(no {DATA_FILE} found: starting a fresh one from the template)")
        r = _release(data, out=_opt(args, "--out"), note=_opt(args, "--note") or "", force="--force" in args)
        print(f"release {r['release']}")
        print(f"  {PROGRAM_FILE:<20} {os.path.getsize(SELF):,} bytes; with {ENGINE_DIR}/ ({len(_SRC)}) {r['size']:,} · sha256 {r['sha']}  (from {r['program']})")
        print(f"  {STATE_FILE:<20} {r['state_size']:,} bytes · sha256 {r['state_sha']}  (from {r['state']})")
        print(f"  {DATA_FILE:<20} {r['data']}")
        print(f"  {'zip':<20} {r['zip']}")
        print(f"  {'self-tests':<20} {r['tests']}")
        print(f"  {'sync code':<20} {_sync_code(r['data'])}")
        for w in r["notes"]:
            print(f"  WARNING: {w}")
        print("Released. Commit when ready: git add -A && git commit -m \"" + r["release"] + ": <note>\"")
        return 0
    if cmd == "sync":
        return _sync(args)
    if cmd == "glossary":
        g = _glossary()
        text = json.dumps(g, indent=1, ensure_ascii=False) if "--json" in args else _glossary_md(g)
        dest = _opt(args, "--out")
        if dest:
            _atomic_write(dest, text + "\n"); print("wrote", dest)
        else:
            print(text)
        return 0
    print(f"unknown command {cmd!r}; try --help"); return 1


if __name__ == "__main__":
    if USER != TOKEN:
        sys.stdout = _Named(sys.stdout)
    sys.exit(main(sys.argv[1:]))
