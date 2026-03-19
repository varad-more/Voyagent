# Voyagent Implementation Plan (Build Guide)

This document is a practical blueprint to build a Voyagent-like product from scratch on a new machine/team.

## Product Goal
Build an AI travel planning product that creates reliable, editable, and shareable day-by-day itineraries in minutes.

## Success Criteria (v1)
- User creates a trip in under 2 minutes
- First itinerary generated in under 20 seconds
- Itinerary is editable block-by-block
- Share link works for collaborators
- Retry/fallback protects user experience during model/provider failures

## Current Product Benchmark (from live Voyagent UX)
Observed anchors to preserve while implementing:
- Fast "start planning" funnel from destination + dates
- Personalized travel-style framing
- Day by day itinerary generation
- Group collaboration positioning
- Destination inspiration cards
- Clear 3-step onboarding narrative (profile, plan, collaborate)

This implementation plan is structured to preserve these strengths and improve reliability, explainability, and collaboration depth.

---

## Phase Plan

## Phase 0 — Foundations (3 to 5 days)

### Scope
- Repo setup, environments, CI, baseline observability
- Data model scaffolding
- Auth and basic user profile

### Deliverables
- Django project bootstrapped with local + prod settings
- Postgres + Redis wired
- Auth (email + OAuth)
- Core models:
  - `User`
  - `Trip`
  - `TripDay`
  - `TripStop`
  - `GenerationRun`
  - `CollaborationMember`

### Exit criteria
- App boots in local and Docker
- Smoke tests pass in CI

---

## Phase 1 — MVP Trip Planner (10 to 14 days)

### Scope
- Trip creation flow
- One-shot itinerary generation
- Itinerary timeline rendering
- Manual edit and reorder stops

### API contracts
- `POST /api/itineraries/generate`
- `GET /api/itineraries/:id`
- `PATCH /api/itineraries/:id/stops/:stop_id`
- `POST /api/itineraries/:id/stops/reorder`

### Core logic
- Prompt template + schema-constrained JSON output
- Validate output against:
  - opening hours
  - time-window feasibility
  - transit buffer
- Persist the final itinerary and generation metadata

### Exit criteria
- Valid itinerary generated for 80%+ requests
- User can edit and save without losing structure

---

## Phase 2 — Multi-Agent Orchestration (7 to 10 days)

### Scope
Introduce specialized agents coordinated by orchestrator.

### Recommended agents
- `ResearchAgent` (city context + neighborhoods)
- `AttractionsAgent` (candidate places)
- `RouteAgent` (travel-time aware ordering)
- `FoodAgent` (meal recommendations)
- `BudgetAgent` (cost envelope checks)
- `ValidatorAgent` (hard constraints + sanity)

### Orchestration contract
Each agent receives:
- `trip_context`
- `user_profile`
- `partial_plan`
- `constraints`

Each agent returns:
- `suggestions`
- `confidence`
- `evidence`
- `warnings`

### Exit criteria
- Orchestrator can recover from one agent failure
- Validator blocks impossible plans
- Agent traces visible in admin/debug view

---

## Phase 3 — Collaboration + Sharing (5 to 7 days)

### Scope
- Shared trip links
- Role permissions (owner/editor/viewer)
- Voting/comments per stop
- Version history and rollback

### Exit criteria
- Two users can collaboratively edit same trip
- Audit trail exists for edits

---

## Phase 4 — Reliability + Performance (5 to 7 days)

### Scope
- Rate-limit handling + queueing
- Caching and graceful fallbacks
- Cost and latency controls

### Reliability requirements
- Exponential backoff for provider 429/5xx
- Circuit breaker when provider degrades
- Fallback itinerary mode when AI unavailable
- Retry budget to avoid infinite loops

### Exit criteria
- No hard app crash on provider outage
- p95 generation latency under target

---

## Data Model (Recommended)

## `Trip`
- `id`, `owner_id`, `title`, `destination`, `start_date`, `end_date`, `currency`, `preferences_json`

## `TripDay`
- `id`, `trip_id`, `day_index`, `summary`, `weather_context`

## `TripStop`
- `id`, `trip_day_id`, `name`, `category`, `start_time`, `end_time`, `lat`, `lng`, `cost_estimate`, `notes`, `source_confidence`

## `GenerationRun`
- `id`, `trip_id`, `provider`, `model`, `prompt_version`, `input_tokens`, `output_tokens`, `latency_ms`, `status`, `error_code`

## `CollaborationMember`
- `id`, `trip_id`, `user_id`, `role`

---

## System Architecture

- Frontend: Next.js + Tailwind
- Backend: Django REST API
- Database: Postgres
- Queue/cache: Redis + Celery
- AI provider abstraction: OpenAI/Gemini/Anthropic adapter layer
- Maps data: Google Places / Mapbox
- Observability: Sentry + structured logs + request IDs

---

## Quality Guardrails

- Reject overpacked itineraries
- Enforce meal + travel buffers
- Detect duplicate attractions across days
- Hard fail invalid schema outputs
- Keep prompt templates versioned and testable

---

## Security + Privacy

- Encrypt API keys and secrets
- Store minimal PII
- Add delete-trip + delete-account
- Role-based access for shared trips
- Log redaction for prompts containing personal details

---

## Milestone Timeline (example)

- Week 1: Foundations + MVP skeleton
- Week 2: Generation + editing + persistence
- Week 3: Multi-agent orchestration + validation
- Week 4: Collaboration + reliability hardening

---

## Definition of Done (Production Candidate)

- Core flows fully tested
- Retries/fallback proven in chaos tests
- Cost and latency dashboards available
- Error budget and alerting configured
- Deployment runbook documented
