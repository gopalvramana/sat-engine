# Weekend TODO — SAT Engine

## React App + API Build Plan

### Phase 0 — Google Auth + User APIs *(start here)*
- [ ] Add Spring Security + OAuth2 Client + JJWT to `pom.xml`
- [ ] Configure Google OAuth2 (client-id, client-secret in `.env`)
- [ ] Implement OAuth callback → issue JWT → redirect to React app
- [ ] Create `User` entity, `UserRepository`, `UserService` (upsert on login)
- [ ] `GET /api/user/me` — return profile from JWT
- [ ] `POST /api/auth/logout` — client-side token discard
- [ ] `JwtFilter` — validate Bearer token, populate SecurityContext
- [ ] Secure `/api/sessions/**` and `/api/questions/**` with JWT

### Phase 1 — Practice Session API Hardening
- [ ] Wire `userId` from JWT into `POST /api/sessions` (not from request body)
- [ ] Add ownership check to `GET /api/sessions/{id}` and `POST /api/sessions/{id}/answers`
- [ ] Add `GET /api/sessions/{id}/questions` — return all question IDs + metadata upfront
- [ ] Extend `CreateSessionRequest` with future exam fields (`timedMode`, `moduleNumber`) — ignored for now

### Phase 2 — React App (Practice Flow)
- [ ] Scaffold Vite + React + TypeScript project
- [ ] Set up Tailwind CSS, React Router v6, TanStack Query
- [ ] `AuthProvider` context — JWT from cookie, redirect to `/login` if missing
- [ ] `/login` page — Google Sign-in button → `/auth/google`
- [ ] `/practice` — Setup screen (section / domain / difficulty / count)
- [ ] `/practice/session/:id` — Question screen (MCQ + SPR + submit)
- [ ] Port `renderer.js` → `renderer.ts` for diagrams
- [ ] Integrate KaTeX (`react-katex`) for math
- [ ] Feedback bar — ✓/✗ only during session (explanations held for review)
- [ ] `/practice/session/:id/summary` — Score + domain breakdown
- [ ] `/practice/session/:id/review` — Single-card review overlay (port from `practice.js`)

### Phase 3 — Data Tracking *(later)*
- [ ] Flyway V33: create `user_login_events` table
- [ ] Log login events in OAuth callback handler
- [ ] Analytics queries: DAU, session completion rate, per-domain accuracy over time

---

## Notes
- Sessions, question APIs, and answer submission already exist — don't rebuild
- `users` table already in DB (V1 migration) — just needs Java code
- `renderer.js` diagram engine can be ported directly to TypeScript
- Full exam mode: designed for in Phase 1, build later
- Topic Refresher (Screen 4): separate plan in `ReviewSite/docs/11-topic-refresher-plan.md`
