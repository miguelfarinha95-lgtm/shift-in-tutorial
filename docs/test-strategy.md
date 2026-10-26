# snip — Test Strategy v1

> Living document. Update when the pyramid weights, SLI targets, or tech stack change.

---

## Context

snip has three groups of users (recipients > employees > link owners), five SLIs, and a single
hot path: `GET /{code}`. The strategy concentrates effort there and at the boundaries where
correctness and security risks live (create / validate). There are no tests yet — this document
is the target.

---

## Test pyramid

| Level | What we test here | Target weight |
|-------|-------------------|---------------|
| **Unit** | Pure logic in isolation: `generate_code`, `Store.put/get/exists/all`, URL validation rules | ~30% of tests |
| **Integration (HTTP)** | Full request→response through FastAPI + `shortener` + `store`: status codes, response bodies, redirect `Location`, click increment, 404 behaviour | ~60% of tests |
| **Contract / performance** | SLI 1 latency gate: p95 of `GET /{code}` measured against the 50 ms target in CI | ~10% of tests |

**Why this shape.** The redirect path is a thin stack (route → `shortener.resolve` → `store.get` →
`RedirectResponse`). Most bugs will be observable at the HTTP level. Unit tests cover the two
isolated pieces worth testing independently — code generation and store operations — but do not
duplicate what HTTP tests already prove. A dedicated latency check protects SLI 1 without adding
noise to the functional suite.

---

## SLI coverage map

| # | SLI | Target | Test level | What the test does |
|---|-----|--------|------------|--------------------|
| 1 | Redirect latency (p95 `GET /{code}` < 50 ms) | < 50 ms | Performance | Fires N requests against `TestClient`, records wall time, asserts p95 < 50 ms |
| 2 | Redirect availability (valid redirect or correct 404) | ≥ 99.9% | Integration | Asserts `GET /{code}` returns 307 for a known code and 404 for an unknown code — no 5xx |
| 3 | Resolve correctness (redirect goes to exact stored URL) | 100% | Integration | Creates a link, follows it, asserts `Location` header equals the original URL byte-for-byte |
| 4 | Create validation (invalid/unsafe URLs rejected) | 100% | Unit + Integration | Unit: validation function rejects script-scheme, bare words, empty strings. Integration: `POST /api/links` with bad URLs returns 422 |
| 5 | Stats accuracy (recorded clicks = actual follows) | 100% | Integration | Follows the same code N times, calls `GET /api/links/{code}/stats`, asserts `clicks == N` |

SLIs 3, 4, and 5 are correctness invariants — any failure is a P0, so they must be in the
default test run, not a separate suite.

---

## Mutation testing — how we check tests actually assert something

We will verify each test layer by **hand mutation**: change one behaviour in the source, run the
suite, confirm at least one test fails. If no test fails the test is not asserting what we think.

### Planned mutations

| Module | Mutation | Expected failing test |
|--------|-----------|-----------------------|
| `shortener.py` | In `resolve`, remove `record.clicks += 1` | Stats accuracy test (SLI 5) |
| `shortener.py` | In `resolve`, return a hardcoded wrong URL | Resolve correctness test (SLI 3) |
| `main.py` | Change `follow` to return 301 instead of 307 | Availability / redirect status test (SLI 2) |
| `models.py` | Remove URL validation (if/when added) | Create validation unit test (SLI 4) |
| `store.py` | In `get`, always return `_links[list(self._links)[0]]` (wrong record) | Resolve correctness test (SLI 3) |

### Procedure

1. Make the mutation in the source file.
2. Run `pytest` (full suite).
3. Confirm the expected test(s) fail and nothing else is broken by the mutation itself.
4. Revert the mutation with `git restore`.

Each mutation must be run as a mob before that test layer is considered done. If the expected test
does **not** fail, the test is missing an assertion — fix the test, then re-run the mutation.

---

## Tooling

- **Test runner**: pytest
- **HTTP client**: `httpx.AsyncClient` with FastAPI `app` (via `pytest-anyio` or `httpx`
  `TestClient` for synchronous tests)
- **Fixtures**: a per-test fresh `Store` instance to prevent state leaking between tests
  (the global `store` in `store.py` must be reset or replaced in test setup)
- **Latency test**: `time.perf_counter` around `TestClient` calls; assert `p95 < 0.050`
- **No mocking of `store`** in integration tests — the real in-memory store is fast enough and
  mocking it would hide the click-increment bug that mutation testing is designed to catch

---

## Out of scope for v1

- Load / stress testing beyond the p95 latency gate
- Persistence (store is intentionally in-memory)
- Authentication / authorisation (not yet a feature)
- Link expiry (on the roadmap — test strategy will be updated in M5)
