# Dependencies

What CALLIOPE ZED needs, with the versions it was tested with on 2026-11-14.

## AI

ZED has no AI built in. The program never calls a model or the network: `calliope.py`, its engines and `zed.py` import the Python standard library only. The judgement in it (ratings, personas, briefs, Snapshots) comes from an agent: an agentic LLM tool opened in this folder, following `AGENTS.md` and the skills in `skills/` (brief, persona, snapshot, studybook). Any agentic LLM tool will do, with any model it can run, proprietary or open-weight, provided it can do the following.

| Needed | What for | Tested with |
|---|---|---|
| An agentic LLM tool that runs shell commands in the folder and reads and writes its files | Runs every session: reads `AGENTS.md`, reads the skills, runs the program's commands, writes the documents | Claude Code 2.1.325 |
| A model that the tool can use, through whatever account, key or local server the tool needs | The judgement the program's rules are fed with | |
| Web search and page fetch (optional) | Briefs ("catch me up on X") search the present state of a field and open each source before citing it. Nothing else uses the web | |

### Running it entirely on free software

The program side is free software already (GPL-3.0-or-later, standard-library Python, reportlab, poppler). For the agent side, pair a free-software agent tool with an open-weight model served locally:

- **Agent tool.** Any free-software terminal agent that can run shell commands and edit files, such as Aider, OpenHands or opencode. Check its license and its docs for how it loads an instruction file.
- **Model server.** A local server such as Ollama, llama.cpp's `llama-server` or vLLM, which the agent tool reaches through its OpenAI-compatible endpoint. No account or key leaves the machine.
- **Model.** An open-weight model with dependable tool calling (function calling) and a context window of at least 32k tokens. A session reads `AGENTS.md` and `CALLIOPE_DATA.md` and the output of the commands it runs, and `python3 calliope.py guidebook` alone is about 25 KB. Smaller models work for status, release and logging; ratings, briefs and personas ask the most of the model's judgement.

This pairing is not yet tested. Record the tool, model and versions here when it is.

### What carries over between tools

- **Instruction file.** `AGENTS.md` is the instruction file. Many agent tools read it by that name. A tool that reads only another file name needs a copy or a link under that name (Claude Code reads `AGENTS.md` when the folder has no `CLAUDE.md`, checked in 2.1.327). A tool that reads no instruction file at all can be told to read `AGENTS.md` at the start of each session.
- **Skills.** `skills/*/SKILL.md` are plain Markdown with a short header. A tool that loads skills by itself uses them as they are. With any other tool the agent reads the file when its trigger comes up, as `AGENTS.md` says, and takes `$ARGUMENTS` as the words user_name gave after the trigger.
- **Model.** ZED names none, so it uses whichever model the session runs. The ratings follow fixed rules in the program, but the judgements fed into those rules come from the model, so a different model can rate the same idea differently. The calibration anchors (`python3 calliope.py idea anchors`) show how far a new model drifts. Cold-rate the three anchors once after changing models.
- **Weaker models.** The program checks every rating and record before it writes state, and refuses a malformed one with a reason. A model that gets the JSON wrong is stopped there and has to correct it; it cannot write bad state into the file.
- **Nothing in ZED's files.** No API key, MCP server, plugin or hook is needed by ZED itself. Any account, key or server is the agent tool's own.
- **Permissions.** Each tool sets its own. `adapters/claude-code/settings.json` is the Claude Code example: copy it to `.claude/settings.json` and Claude Code may run `python3 zed.py ...` and `python3 calliope.py ...` in this folder without asking each time. Everything else still asks. Another tool needs the same two command patterns in its own settings.

## Python

| Needed | What for | Tested with |
|---|---|---|
| Python 3, a current release | `calliope.py`, its engines and `zed.py` use the standard library only | 3.12.3 |
| reportlab | Every PDF: Snapshots, briefs, STUDYBOOK (the scripts in `tools/`) | 4.1.0 |

Install it with `pip install -r requirements.txt`, or with your system's package (`python3-reportlab` on Debian and Ubuntu).

## Other programs

| Needed | What for | Tested with |
|---|---|---|
| poppler-utils (`pdfunite`, `pdfinfo`) | STUDYBOOK only: joining the briefs into one PDF and counting pages | 24.02.0 |
| Noto or Liberation fonts in `/usr/share/fonts/truetype/` | The PDFs' typefaces. Without them the PDFs fall back to the built-in PDF fonts (Times, Helvetica, Courier), which lack some symbols | Noto |
| git (optional) | A commit after each release, as the README suggests | 2.43.0 |

## Systems

- **Linux:** tested.
- **macOS:** expected to work, but untested. Install poppler from Homebrew (`brew install poppler`). The font folder above doesn't exist on a Mac, so the PDFs use the built-in fonts.
- **Windows:** use WSL. Run natively, `zed.py brief new` fails on its date format (`%-d`), and the font and poppler notes above apply.
