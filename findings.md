# glavk Findings

## Workspace

- The workspace root contains an existing `photo` project, but the root itself is not a Git repository.
- `photo` already demonstrates React + Vite, Python 3.12 + FastAPI, SQLAlchemy, MariaDB, bearer auth, frontend tests, and Docker Compose patterns.
- `glavk` should remain a separate project directory to avoid coupling photo management to credential management.

## User decisions

- Product name: `glavk`.
- Primary purpose: manage all web projects as visual cards.
- Required fields include web URL, username, and password; the implementation also includes name, category, description, notes, favorite, and enabled status.
- Login is required.
- Single administrator account in the first version; no multi-user or role-management UI.
- Browser token retention: 30 days.
- UI: Chinese only, blue-white initial palette, remaining visual direction delegated to the implementation.
- Final delivery: Docker deployment.

## Stitch reference

- Shared project URL: https://stitch.withgoogle.com/projects/10559855834040172715
- Page title: `Stitch - Projects`.
- Project title visible in the shared page: `glavk 网页系统管理后台`.
- The shared project exposes generated design screens in multiple iframes and has controls labelled `Primary`, `Secondary`, `Inverted`, and `Outlined`.
- The implementation should use the approved blue-white admin direction while keeping the actual app functional rather than embedding Stitch output.
- Screenshot review confirms the visual composition: pale blue canvas, white login panel, compact top bar, left navigation, empty/dashboard state boards, and a right-side add-system drawer. The generated project is a reference only; the production UI will be implemented in React with real controls.

## Delivery decisions

- Frontend host port: `6222` -> container port `80`.
- Backend host port: `6555` -> container port `8000`.
- MariaDB host port: `3307` -> container port `3306` for optional local access.
- Compose service-to-service traffic uses the internal names `backend` and `mariadb`.
- Project passwords must be encrypted at rest and never returned in the normal project list response.
