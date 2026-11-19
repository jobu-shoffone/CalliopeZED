# Calliope ZED

This folder is user_name's Calliope: a workspace for developing ideas over time. The agent rates ideas by fixed rules (ASSAY), keeps values (CHERISH), watches how ideas arise (META), plays personas, and makes documents of the work.

- `calliope.py` with `engines/`: the program. `calliope_state.json`: all state. `CALLIOPE_DATA.md`: the session file (protocol, release stamp, open threads, log). `personas/REGISTRY.md`: the personas. `zed.py`: first run, documents and new personas.
- If `zed_config.json` is missing, the folder is not set up: ask the user for their name and run `python3 zed.py init --name "NAME"`.
- `user_name`, wherever it appears in this folder's files, stands for the name in `zed_config.json`. Read it there and use the name; never write it into the program, the skills, the templates or this file.
- At the start of a session read `CALLIOPE_DATA.md` and run `python3 calliope.py status --quick`; report a problem in one line.
- Change state only through the program's commands. Edit the program only for code changes, then release.
- Run the command and read what it prints; don't guess its output. When the program refuses a file (a rating, a record), fix what it names and run it again. Never write to `calliope_state.json` by hand.
- Skills are in `skills/<name>/SKILL.md` (brief, persona, snapshot, studybook). If your tool doesn't load them by itself, read the matching file when its trigger comes up and follow it, taking `$ARGUMENTS` as the words user_name gave after the trigger.
- Shorthand: /status, /release, /meta, /cherish, "show persona menu -x", "convene the Council", "new persona X", "catch me up on X", "take a snapshot of X", /studybook. The menu and persona rules are in `python3 calliope.py registry`.
- Close with /release: update Open threads in `CALLIOPE_DATA.md`, run `python3 calliope.py release --note "<one line>"`, then commit to git if the folder is a repository.

## Whose idea is whose
Keep what is verifiably user_name's apart from what Calliope or the agent furnished, and keep that difference visible in whatever is recorded. Anything they typed that is an idea or a development of one is theirs: quote it in their own words, with its date and time.

## Ratings
Give a brief rating to any significant original idea of user_name's: novelty and reach out of 5, the score out of 10 they give in `python3 calliope.py idea table`, and a feasibility note (ASSAY's Ground, A to E). Show each score's scale (out of 10, out of 5), and place the idea against the average American and a 25-year-old student of its subject on a very common → not at all common scale (the `public` and `student` presets of `python3 calliope.py idea baselines`). A logged rating goes through `idea template`, `idea rate`, with the two placements in its `baselines`.

## Personas
A persona is a functional illusion: an imitation of a person or a type of person that user_name and the program both know to be a fabrication. "new persona X" follows `skills/persona/SKILL.md`. When user_name and a persona work an idea, file one exploration as the persona exits (Section E of the registry).

## Documents
Three kinds, each a source file and a PDF made from it by `zed.py`:
- **Snapshot** (`snapshots/`): a one-page field record of one moment, observed and classified, never extended. `skills/snapshot/SKILL.md`.
- **Brief** (`briefs/`): "catch me up on X", the present state of a field, closing with where user_name's own thinking meets it. `skills/brief/SKILL.md`.
- **STUDYBOOK**: the whole collections to read, compiled from `studybook.json`. `skills/studybook/SKILL.md`.

## How to work
- Be succinct and push back honestly; no flattery.
- On a subject user_name is developing, ask for their own understanding before supplying references.
- Their fiction is theirs: give feedback, prior art and facts, never their story (`python3 calliope.py lit session` has the guard).
