# glavk Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an independently deployable Chinese web-system credential manager named `glavk` with a React frontend, Python 3.12/FastAPI backend, MariaDB database, 30-day admin sessions, and a Stitch-inspired blue-white dashboard.

**Architecture:** `glavk` is isolated from the existing `photo` directory. FastAPI owns authentication, validation, encrypted project credential storage, and CRUD APIs. React/Vite owns the login shell, project grid, search/filter state, drawer forms, masked credential controls, and 30-day browser session persistence. Docker Compose runs frontend, backend, and MariaDB with fixed host ports 6222, 6555, and 3307.

**Tech Stack:** React 18 + TypeScript + Vite + lucide-react; Python 3.12 + FastAPI + SQLAlchemy + PyMySQL + cryptography; MariaDB 11; Docker Compose; pytest; Vitest + Testing Library.

**Status:** Complete. Backend, frontend, Docker delivery files, smoke test, browser verification, and server deployment documentation are finished. Docker runtime validation remains environment-blocked because the Docker CLI is not installed.

## Phase 6: Server deployment configuration

- [x] Add a server-focused `.env` template containing only server IP, ports, database credentials, and admin credentials.
- [x] Bake the real API origin into the frontend Docker build and derive backend CORS from the same server values.
- [x] Generate missing production encryption secrets on first backend startup and persist them in `backend_data`.
- [x] Write the Chinese server deployment tutorial, firewall guidance, health checks, upgrade/backup notes, and HTTP limitation.
- [x] Run configuration tests, backend/frontend tests, and production build; Compose runtime remains blocked by missing Docker CLI.

---

## Phase 1: Backend foundation and authentication

- [ ] Create backend package, settings, SQLAlchemy base, app factory, health endpoint, and test dependencies.
- [ ] Write failing tests for default admin creation, valid login, invalid login, bearer authentication, and 30-day expiry.
- [ ] Implement admin password hashing and HMAC-signed bearer tokens with configurable 30-day TTL.
- [ ] Add `/api/auth/login` and `/api/auth/me` with Chinese-safe validation errors.

## Phase 2: Project data and credential protection

- [ ] Write failing tests for project validation, encrypted password persistence, list filtering, update, and delete.
- [ ] Implement `WebProject` model, Fernet credential encryption, service layer, and project API routes.
- [ ] Ensure list responses return masked passwords only; reveal endpoint returns the decrypted password only for an authenticated request.
- [ ] Add MariaDB schema and startup table creation for the `glavk` database.

## Phase 3: React shell and authentication flow

- [ ] Create Vite React app, API client, session persistence, route state, and failing component tests for login and token expiry.
- [ ] Implement login screen, 30-day localStorage session, automatic 401 logout, and app shell navigation.

## Phase 4: Dashboard and project workflows

- [ ] Write failing component tests for empty state, project rendering, search, filter, create, edit, favorite, reveal, copy, and delete confirmation.
- [ ] Implement dashboard metrics, responsive card grid, project drawer form, credential controls, toast feedback, and loading/error states.
- [ ] Apply Stitch-inspired blue-white styling with fixed dimensions, accessible icons, mobile layout, and Chinese copy.

## Phase 5: Docker delivery and verification

- [ ] Add Dockerfiles, Compose services, nginx API proxy, `.env.example`, SQL bootstrap, and README with fixed ports.
- [ ] Run backend tests, frontend tests, frontend build, and API smoke checks.
- [ ] Start Docker services when Docker is available; otherwise verify Compose configuration and report the runtime limitation.
- [ ] Use browser automation against the local app for login, project creation, password reveal/copy, filtering, and responsive screenshots.

## Errors Encountered

| Error | Attempt | Resolution |
|---|---:|---|
| Root directory is not a Git repository | 1 | Preserve the existing workspace and build `glavk` as a new directory; do not use git-only operations. |
| `agent-browser` is not installed globally | 1 | Use `npx agent-browser` for Stitch inspection and later local browser verification. |
