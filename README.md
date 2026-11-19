# Calliope ZED

A blank edition of Calliope: a workspace for developing ideas over time with the agent. It rates ideas by fixed rules, keeps the values they are weighed against, watches how ideas arise, lets you talk ideas through with personas you make, and turns the work into documents you can read.

Nothing of any earlier user travels with it: no ideas, ratings, personas or records. Your name is kept in one file, `zed_config.json`; the program's files say `user_name` and the program reads your name in its place, so setting up changes none of them.

## Set up

In the folder (cloned or copied):

```
python3 zed.py init                # asks your name; writes zed_config.json, an empty state, your persona registry and the first release
git add -A && git commit -m "first release"   # recommended; run git init first if the folder is not a repository
```

`init` writes the four files that hold your name and your work: `zed_config.json`, `calliope_state.json`, `CALLIOPE_DATA.md` and `personas/REGISTRY.md`. Keep them out of any public copy of the program; `.gitignore` already does for git, along with `calliope_release.zip` (each release packs your state into it, as your backup), your Snapshots, briefs, STUDYBOOK, `health/` and the chat archive. Releases are written beside `calliope.py` unless `CALLIOPE_OUT` names another folder.

Then open your agent in this folder. `AGENTS.md` tells it how to work here. Many agent tools read it by that name; a tool that reads only another file name needs a copy under that name, and one that reads none can be told to read it first.

Assumes an agentic LLM tool, with any model it can run (an open-weight model on a local server works as well as a hosted one), and a current Python 3 with reportlab. The program itself never calls a model or the network. STUDYBOOK also uses poppler-utils (`pdfunite`, `pdfinfo`). `DEPENDENCIES.md` lists everything ZED needs, with tested versions, and how to run it entirely on free software.

## What it does

| Part | Command | What you get |
|---|---|---|
| ASSAY | `python3 calliope.py idea ...` | Ratings of ideas: how much would change if it worked, how hard it is to make real, judged by the idea's kind |
| ASSAY-LIT | `python3 calliope.py lit ...` | Ratings for fiction and poetry, with your share of each idea kept visible |
| META | `python3 calliope.py meta ...` | Patterns in how your ideas arise, proposed for you to confirm, reject or park |
| CHERISH | `python3 calliope.py cherish ...` | The values an idea is weighed against |
| Personas | `python3 zed.py persona new "Name"`, then `show persona menu -x` in chat | Personas you define, a Council of them, and a record of each exploration |
| Snapshots | `python3 zed.py snapshot new "moment"`, `snapshot render` | One-page field records of moments in your work |
| Briefs | `python3 zed.py brief new "topic"`, `brief render` | A PDF bringing you up to date on a field, ending with where your thinking meets it |
| STUDYBOOK | `python3 zed.py studybook` | Your collections compiled for reading: the idea ledger, every brief, every Snapshot, the glossary |
| Session | `python3 calliope.py status`, `release` | A health check, and a stamped release of program and state |

`python3 zed.py --help` and `python3 calliope.py glossary` list everything.

## Made from

Calliope, designed by Josh, with its code written by Claude. This edition is maintained on its own. Nothing in Calliope writes to it, and it does not regenerate from Calliope.

## License

Copyright (C) 2026 Joshua Thomas Buffone.

CalliopeZED is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version (GPL-3.0-or-later). It comes with ABSOLUTELY NO WARRANTY. The full text is in `LICENSE`; `python3 zed.py license` shows the notice and the warranty disclaimer.
