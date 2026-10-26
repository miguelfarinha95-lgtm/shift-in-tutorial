# snip

A tiny URL shortener — the **starter application** for the Shift In tutorial. This is the `start`
state: it runs, but it has **no tests, no CI, and no AI tooling yet**. That is the point.

## Before the workshop

Do this a few days out, not on the morning of:

1. Install and authenticate Claude Code with your own Claude subscription; clone this repo.
   Confirm `python3 --version` shows 3.11+ — that's all the pre-check for "Run it" below needs.
2. Install the [GitHub CLI](https://cli.github.com/) if you don't have it, and authenticate under
   your own GitHub account — this is the one-time setup, not something you do live on the day:
   ```bash
   gh auth login
   ```
   Confirm it worked with `gh auth status` — it should show you logged in and active. That's the
   whole setup; Claude Code can run `gh` like any other terminal command, no separate connection
   step needed.
3. Run one smoke prompt — e.g. ask Claude Code to read this file and summarize it — to confirm
   everything's wired up before the room fills.

*(GitHub MCP is an alternative way to give Claude Code GitHub actions, and it's worth knowing
about as its own agent-feature category — but its official remote server currently can't complete
OAuth setup (a live upstream bug, not something wrong with your setup), so it isn't the path this
workshop depends on. See `docs/github-cli-notes.md` from M2 onward if you want to try it anyway.)*

## Run it

```bash
python3 -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e .
uvicorn snip.main:app --reload --app-dir src
```

`pip`/`uvicorn` as bare commands only exist once a virtualenv is active — if you see "command not
found" for either, that's what's missing, not a broken install.

- Interactive docs: http://127.0.0.1:8000/docs
- OpenAPI schema: http://127.0.0.1:8000/openapi.json

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/links` | Create a short link from `{ "url": "..." }` |
| GET | `/api/links` | List links |
| GET | `/api/links/{code}/stats` | Click stats for a code |
| GET | `/{code}` | Follow a short link (redirect) |

## Where to look

<!-- workshop progress tracked in CLAUDE.md -->
- `docs/business-context.md`, `docs/quality-characteristics.md`, `docs/slis.md` — what "good" means.
- `src/snip/` — the implementation.
- `tests/` — empty on purpose; you add tests during the workshop.
