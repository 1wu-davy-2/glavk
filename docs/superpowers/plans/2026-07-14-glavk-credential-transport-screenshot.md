# Credential Transport And Screenshot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make project credentials optional, capture safe public webpage screenshots, and protect credential API payloads with application-layer envelope encryption when HTTPS is unavailable.

**Architecture:** Keep Fernet as the database-at-rest encryption layer. Add a backend RSA-OAEP transport key and a browser-only WebCrypto session key. Add a Playwright screenshot service that never receives project credentials, stores PNGs under a persistent data directory, and fails open to the existing avatar card when capture is unavailable.

**Tech Stack:** Existing React/Vite, FastAPI, SQLAlchemy, MariaDB, PyJWT, cryptography, Vitest, pytest; add Python Playwright Chromium and browser WebCrypto AES-GCM/RSA-OAEP.

---

### Task 1: Extend backend models and schemas for optional credentials and screenshots

**Files:**
- Modify: `backend/app/models.py`
- Modify: `backend/app/schemas.py`
- Modify: `backend/sql/001_initial_schema.sql`
- Test: `backend/tests/test_projects.py`

- [ ] Write failing tests for creating a project with no username/password, one credential field only, and list responses containing `has_credentials`/`has_screenshot` without credential plaintext.
- [ ] Run `python -m pytest backend/tests/test_projects.py -q` and confirm the new assertions fail against required password validation and current response fields.
- [ ] Make `ProjectCreate.password` optional, make `WebProject.password_ciphertext` nullable, add screenshot path and `has_credentials`/`has_screenshot` response fields, and preserve existing encrypted rows.
- [ ] Run the targeted tests and expect them to pass.

### Task 2: Add RSA/AES transport envelopes

**Files:**
- Create: `backend/app/transport_crypto.py`
- Create: `frontend/src/utils/credentialTransport.ts`
- Create: `frontend/src/utils/credentialTransport.test.ts`
- Modify: `backend/app/config.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/api/projects.py`
- Modify: `backend/app/schemas.py`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/components/DashboardPage.tsx`
- Modify: `frontend/src/components/ProjectDrawer.tsx`
- Test: `backend/tests/test_transport_crypto.py`
- Test: `backend/tests/test_projects.py`

- [ ] Write failing backend tests for public-key exposure, decrypting a frontend-created envelope, rejecting malformed envelopes, and encrypting a credential response for a client public key.
- [ ] Write failing frontend tests that encrypt username/password without putting plaintext in the request body and decrypt a response envelope only with the in-memory private key.
- [ ] Run the targeted pytest and Vitest files and verify the expected missing-module/behavior failures.
- [ ] Implement server-side RSA-OAEP + AES-GCM envelope helpers and WebCrypto browser helpers; use an ephemeral non-exportable browser private key and never store it in localStorage.
- [ ] Make create/update send `credential_envelope` when either field is filled; make credential reveal/copy send `X-Client-Public-Key` and decrypt in memory.
- [ ] Run the targeted tests and expect them to pass.

### Task 3: Integrate encrypted project CRUD and protected reveal

**Files:**
- Modify: `backend/app/services/projects.py`
- Modify: `backend/app/api/projects.py`
- Modify: `frontend/src/components/ProjectCard.tsx`
- Modify: `frontend/src/components/DashboardPage.tsx`
- Modify: `frontend/src/App.feature.test.tsx`

- [ ] Add failing tests for the no-credential card state, optional form submission, encrypted reveal, copy success, and clearing decrypted state after use.
- [ ] Implement service decrypt-on-save, Fernet-at-rest persistence, encrypted reveal response, and no-plaintext list output.
- [ ] Update the card to show “无需登录” for empty credentials and keep a short-lived decrypted credential only in React memory.
- [ ] Run all backend and frontend tests.

### Task 4: Implement safe screenshot capture

**Files:**
- Create: `backend/app/screenshot_service.py`
- Create: `backend/tests/test_screenshot_service.py`
- Modify: `backend/app/config.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/models.py`
- Modify: `backend/app/services/projects.py`
- Modify: `backend/app/api/projects.py`
- Modify: `backend/requirements.txt`
- Modify: `backend/Dockerfile`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/components/ProjectCard.tsx`
- Modify: `frontend/src/components/DashboardPage.tsx`
- Modify: `frontend/src/styles.css`

- [ ] Write failing tests for SSRF target rejection, successful fake capture path persistence, screenshot failure not aborting project save, authenticated PNG response, and missing screenshot fallback.
- [ ] Run the targeted screenshot tests and verify failure before implementation.
- [ ] Implement Playwright Chromium capture with 8-second navigation timeout, fixed viewport, no credentials, private-network blocking by default, persistent `SCREENSHOT_DIR`, authenticated file response, and graceful failure.
- [ ] Add `playwright` dependency and install Chromium in the backend image; add screenshot data volume and env vars to Compose.
- [ ] Fetch screenshot blobs with bearer auth in the frontend, revoke object URLs on refresh/unmount, and render the avatar fallback when no screenshot exists.
- [ ] Run backend tests, frontend tests, and build.

### Task 5: Harden HTTP deployment documentation and verify

**Files:**
- Modify: `frontend/nginx.conf`
- Modify: `docker-compose.yml`
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `docs/stitch-prompt.md`
- Modify: `scripts/smoke_test.py`
- Modify: `progress.md`
- Modify: `task_plan.md`

- [ ] Add CSP/security headers, `TRANSPORT_PRIVATE_KEY_B64`, `SCREENSHOT_DIR`, `SCREENSHOT_ALLOW_PRIVATE_NETWORKS`, and `backend_data` volume settings.
- [ ] Document the HTTP limitation and trusted-network/localhost requirement; provide a private-key generation command and explain that HTTPS remains required for public deployment.
- [ ] Run `python -m pytest backend/tests -q`, `npm test`, `npm run build`, and the smoke test.
- [ ] Use browser automation to verify static-project save, screenshot fallback/preview, encrypted credential save, reveal, copy, and responsive card rendering.
- [ ] Commit the changes and push the updated `main` branch after fresh verification.

