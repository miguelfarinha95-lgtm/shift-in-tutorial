# CLAUDE.md — snip

snip is an internal URL-shortening service. Source in `src/snip/`. Run with
`uvicorn snip.main:app --reload --app-dir src`.

---

## Users — priority order

1. **Recipients** following short links — highest traffic by far; never break the redirect path.
2. **Employees** creating short links for docs, dashboards, and slides.
3. **Link owners** checking click stats for their links.

---

## Quality bar (highest priority first)

1. **Functional correctness** — a follow must always resolve to the exact URL it was created with; click counts must be accurate.
2. **Performance efficiency** — `GET /{code}` is the hot path; p95 latency must stay under 50 ms.
3. **Reliability** — the redirect path must stay available (≥ 99.9%); create can tolerate brief degradation.
4. **Security** — only safe, well-formed URLs are accepted; no open-redirect or script-scheme abuse.
5. **Maintainability** — four modules, in-memory store; any change must remain comprehensible by reading `main.py` plus at most one other file. Complexity added to the redirect path is a reliability risk, not just a style concern.

---

## SLI table (what CI gates on)

| # | SLI | Definition | Target (SLO) |
|---|-----|------------|--------------|
| 1 | Redirect latency | p95 server time for `GET /{code}` | < 50 ms |
| 2 | Redirect availability | share of `GET /{code}` returning a valid redirect or correct 404 | ≥ 99.9% |
| 3 | Resolve correctness | share of follows that redirect to the exact stored URL | 100% |
| 4 | Create validation | share of invalid/unsafe create requests correctly rejected | 100% |
| 5 | Stats accuracy | recorded clicks equal actual follows | 100% |

Weight test and CI-gate effort toward SLIs 1–3 (redirect hot path). SLIs 3–5 are correctness invariants that must never regress.

---

## Working agreements

- **Definition of Ready**: SLI impact is understood before work starts; for redirect-touching stories, acceptance criteria include the expected HTTP status code and `Location` header value.
- **Definition of Done**: SLI-affecting changes are reflected in CI pipeline gates; redirect-path changes are covered at the HTTP integration level (not just unit); click-count changes include a stats-accuracy test that calls `GET /{code}` then checks `/api/links/{code}/stats`.
- The click increment in `shortener.resolve` has no guard — any refactor of that function must carry a test that follows a link N times and asserts `clicks == N` in the stats response.
- Security concerns (URL validation, open-redirect, script-scheme abuse) live entirely on the create path — every change to URL acceptance logic must include boundary-input tests.
- A turn never ends with a failing test. If a test is red, fix it before finishing — or state explicitly that you could not and why.

---

## Stack conventions

- **Framework**: FastAPI (`src/snip/main.py`)
- **Modules**: `models.py` (Pydantic schemas), `store.py` (in-memory persistence), `shortener.py` (code generation)
- **Run**: `uvicorn snip.main:app --reload --app-dir src`
- **Tests**: `pytest tests/unit tests/api -q`; use `FastAPI TestClient` (requires `httpx2`) for HTTP-level tests; a per-test fresh `Store` instance is required — the global `store` singleton in `store.py` leaks state between tests
- Stats increment happens on the follow path — tests for stats accuracy must exercise `GET /{code}`, not just the create endpoint
