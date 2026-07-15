# glavk Progress

## 2026-07-14

- Confirmed the new app belongs in `E:/opt/vide coding/glavk`.
- Confirmed single-admin login and 30-day token persistence.
- Reviewed the existing `photo` project for React, FastAPI, SQLAlchemy, MariaDB, testing, and Docker patterns.
- Opened the shared Stitch project and confirmed the project title and generated design iframe structure.
- Created the initial plan, findings, and design specification files.
- Next: inspect reusable backend details, finalize the implementation plan, then start TDD with backend authentication tests.
- Backend TDD completed: health, authentication, project CRUD, validation, password masking, and Fernet reveal tests pass.
- Frontend TDD completed: login/session, project card reveal, add drawer, save, refresh, and toast workflow tests pass.
- Frontend build passes after adding Vite env types and resolving the Vitest/Vite plugin type mismatch.
- Docker files are present, but the current environment has no Docker CLI; local browser verification uses ports 6622/6655 and a temporary SQLite database because 6222/6555 are occupied by the existing `photo` dev servers.
- Browser verification reached the real Chinese login page at `http://127.0.0.1:6622`.
- Browser login succeeded after allowing the local verification origin in CORS; health endpoint and login API are reachable.
- Manual browser field lookup exposed a label collision between the search input and drawer field; precise `aria-label` selectors are used for the remainder of the flow.
- Real browser workflow succeeded: login, create project (`201 Created`), list refresh, and credential reveal returned `crm-secret`.
- The browser automation environment denied clipboard permission; the copy control reached its explicit Chinese fallback error state instead of silently failing.
- Desktop screenshot review shows the blue-white sidebar, metric strip, search/filter row, and project card render without visible overlap; the screenshot was captured after scrolling within the dashboard, so the top heading is above the current viewport.
- Mobile screenshot review at 390x844 confirms compact navigation, full-width add action, metric row, filters, and single-column project card layout without visible overlap.
- Final verification: `scripts/smoke_test.py` passed; backend `7 passed`; frontend `4 passed`; frontend `npm run build` passed.
- Docker Compose files are complete and ports are documented; `docker compose config` could not run because Docker CLI is not installed.
- Implementation status: complete. The local preview remains available on `http://127.0.0.1:6622`; generated screenshots and server logs are temporary verification artifacts.

## 2026-07-15

- New request: simplify deployment to one root `.env` and diagnose why the dot-prefixed server template could not be dragged to the server.
- Decision: use visible `glavk.env.example` as the upload template, copy it to the single root `.env`, use same-origin `/api` through nginx, and bind backend/MariaDB to localhost by default.
- Next: write failing runtime-secret tests, then implement entrypoint, Compose build args, server `.env` template, and tutorial.
- Runtime secret TDD completed: missing production keys generate once, existing values are preserved, and shell output is safely quoted.
- Replaced the two hidden env templates with one visible `glavk.env.example`; server IP and frontend API origin are no longer required because nginx proxies same-origin `/api`.
- Added backend Docker entrypoint to persist generated secrets in `backend_data`, direct frontend API build args, local-only MariaDB binding, and `docs/docker-deploy-server.md`.
- Verification: backend `26 passed`, frontend `9 passed`, frontend production build passed, and `git diff --check` passed. Docker CLI and POSIX shell are unavailable in this environment, so real image/Compose execution remains unverified.
