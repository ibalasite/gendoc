<!--
  DOC-ID:  README-PIXEL-PET-ARENA-20260511
  Version: v1.4
  Status:  IN_REVIEW
  Author:  AI Generated (gendoc readme)
  Date:    2026-05-11
  Upstream docs:
    - BRD:   docs/BRD.md   (BRD-PIXEL-PET-ARENA-20260503)
    - PRD:   docs/PRD.md   (PRD-PIXEL-PET-ARENA-20260503, v1.5)
    - PDD:   docs/PDD.md   (PDD-PIXEL-PET-ARENA-20260503)
    - EDD:   docs/EDD.md   (EDD-PIXEL-PET-ARENA-20260503)
    - ARCH:  docs/ARCH.md  (ARCH-PIXEL-PET-ARENA-20260503)
    - API:   docs/API.md   (API-PIXEL-PET-ARENA-20260503)
    - SCHEMA: docs/SCHEMA.md
    - LOCAL_DEPLOY: docs/LOCAL_DEPLOY.md
    - CICD: docs/CICD.md
  Change log:
    v1.0  2026-05-05  AI Generated  Initial generated draft
    v1.1  2026-05-05  AI Generated  Fix GitHub repo URLs to ibalasite/pet
    v1.2  2026-05-09  AI Generated  Refresh from upstream — switch npm→pnpm (per LOCAL_DEPLOY),
                                     update API endpoint paths to match docs/API.md, sync features
                                     list with features/*.feature, post-HTML pipeline state
    v1.3  2026-05-11  AI Generated  Refresh from upstream — add Interactive Demos section
                                     (UI Prototype + API Explorer + Admin Portal)
    v1.4  2026-05-11  AI Generated  Re-verified upstream consistency in /gendoc-gen-html
                                     full-auto cycle (BRD/PRD/PDD/EDD/ARCH/API/SCHEMA/CICD)
-->

# pixel-pet-arena

> Zero-account-barrier HTML5 browser game where players claim, train, and battle procedurally-generated pixel pets via email — no registration required.

[![CI](https://github.com/ibalasite/pet/actions/workflows/ci.yml/badge.svg)](https://github.com/ibalasite/pet/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Node.js](https://img.shields.io/badge/Node.js-20%20LTS-green.svg)](https://nodejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-blue.svg)](https://www.typescriptlang.org/)
[![pnpm](https://img.shields.io/badge/pnpm-9.x-orange.svg)](https://pnpm.io/)

---

## Table of Contents

- [Overview](#overview)
- [Core Features](#core-features)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [API Quick Reference](#api-quick-reference)
- [Directory Structure](#directory-structure)
- [Documentation](#documentation)
- [Testing](#testing)
- [Known Limitations](#known-limitations)
- [Changelog](#changelog)
- [Development Guide](#development-guide)
- [License](#license)
- [Security Policy](#security-policy)
- [Architecture Quick Reference](#architecture-quick-reference)
- [Code of Conduct](#code-of-conduct)

---

## Overview

**pixel-pet-arena** is a zero-account-barrier HTML5 browser game where players discover and claim procedurally-generated pixel pets using only their email address — no account registration, no password to remember.

It was built to solve the mutual exclusivity between "no account barrier" and "persistent data" that has prevented casual players from truly owning virtual pets on the web. The core innovation is **email as a lightweight identity layer**: a 6-digit OTP issues a 32-byte cryptographic URL token. Players bookmark their unique URL — that URL is their identity, accessible from any device, forever.

The project is governed by the upstream documents below; every design decision maps to a tracked requirement:

| Document | Purpose |
|----------|---------|
| [BRD](docs/BRD.md) | Business goals, success metrics, stakeholder sign-off |
| [PRD](docs/PRD.md) | User stories, acceptance criteria, priority tiers |
| [PDD](docs/PDD.md) | UX flows, interaction specs, design tokens |
| [EDD](docs/EDD.md) | Architecture decisions, technology choices, data models |
| [ARCH](docs/ARCH.md) | C4 diagrams, component architecture, ADRs |

See [System Architecture](#system-architecture) below for a visual overview, and [Documentation](#documentation) for the full HTML reference site.

---

## Core Features

**P0 — Must ship for v1.0:**

- **Random Pixel Pet Generation** — Each pet is procedurally generated across 6 attribute dimensions (body, head, color_palette, accessory, rarity_trait, pattern) guaranteeing ≥ 1 billion unique combinations. 32×32 px sprite rendered on HTML5 Canvas via Phaser.js 3.
- **Email Claim Flow** — Guests interact immediately with no login wall. Entering an email sends a 6-digit OTP plus a permanent unique URL. The pet is accessible from any device via that bookmarked URL forever.
- **Pet Training & Feeding System** — 3 training actions per day (reset UTC 00:00). Special food items grant temporary or permanent stat buffs to Speed, Strength, or Stamina (max 100 each). Pets visually degrade after 3 days of neglect.
- **Arena Combat** — Race mode (Speed-weighted) and Sumo mode (Strength-weighted) with ±15% seeded random modifier. Real-time matchmaking with 30-second AI fallback. Default rate-limit 10 battles/hour per pet (admin-tunable).
- **Global Leaderboard** — Top 100 pets by win rate, updated within 30 seconds via Redis sorted set. Filterable by rarity tier (Common / Rare / Epic / Legendary).
- **Battle Records Page** — Shareable URL displaying the last 20 battles per pet with outcomes, stat snapshots, and opponent info.
- **Admin Portal** — Vue 3 + Element Plus admin SPA for moderation, GDPR processing, runtime parameter tuning, suspicious-pet detection, and game economy configuration.

**P1 — Roadmap:**

- Rarity scoring system (Common 60% / Rare 25% / Epic 12% / Legendary 3%) with visual badges and dedicated rarity-distribution tracking.

**P2 — Future (feature-flagged):**

- Pet trading marketplace (`FF_MARKETPLACE`, 5% platform fee), tournament system, seasonal competitions.

---

## System Architecture

```mermaid
flowchart TB
    subgraph Browser["Browser — Vercel CDN"]
        PA["Player App\nReact 18 + Phaser.js 3\nVite 5 / TypeScript 5"]
        AP["Admin Portal\nVue 3 + Element Plus\nVite 5 / TypeScript 5"]
    end

    subgraph API["API Layer — Railway (autoscale HPA 70% CPU)"]
        GA["Game API\nFastify 4 / Node.js 20 LTS\n≥ 2 replicas"]
        AA["Admin API\nFastify 4 / Node.js 20 LTS\n1 replica (mounted at /admin)"]
    end

    subgraph Data["Data Tier"]
        PG[("PostgreSQL 15+\nSupabase managed\nDaily S3 backup")]
        RD[("Redis 7+\nUpstash serverless\nLeaderboard · Rate-limits · Sessions · Matchmaking")]
    end

    subgraph Email["Email Services"]
        SG["SendGrid v3\nprimary"]
        NM["Nodemailer SMTP\nfallback — activates after\n3 consecutive SendGrid failures"]
    end

    PA -->|"REST /api/v1/*"| GA
    AP -->|"REST /admin/api/*"| AA
    GA --> PG
    GA --> RD
    AA --> PG
    AA --> RD
    GA -->|"transactional email"| SG
    SG -.->|"failover"| NM
```

> For component-level detail, data flow diagrams, and ADR records see:
> - [EDD — Engineering Design Document](docs/EDD.md) (architecture + implementation)
> - [ARCH — System Architecture](docs/ARCH.md) (C4 diagrams + ADRs)
> - [docs/diagrams/](docs/diagrams/) (Mermaid UML — 9 server + 16 frontend + 5 CI/CD + 2 modulith)

---

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| **Frontend (Player)** | React 18 + Phaser.js 3 + Vite 5 + TypeScript 5 | Canvas rendering for pixel pets; TanStack Query v5, Zustand, React Hook Form + Zod |
| **Frontend (Admin)** | Vue 3 + Element Plus + Vite 5 + TypeScript 5 | Data-dense admin portal; separate Vite build deployed independently |
| **Backend** | Node.js 20 LTS + Fastify 4 | Game API + Admin API as two Fastify plugins in one Node process; admin mounted at `/admin` |
| **Package Manager** | pnpm 9.x (workspaces) | Monorepo via `pnpm-workspace.yaml`; cross-app linking via `workspace:*` |
| **Database** | PostgreSQL 15+ (Supabase managed) | Primary writer + 1 read replica; auto-failover 60s; daily S3 backup |
| **Cache / Queue** | Redis 7+ (Upstash serverless) | Leaderboard sorted set, rate-limit counters, admin sessions, matchmaking queue |
| **Infrastructure** | Vercel (frontend CDN) + Railway (API, autoscale) | HPA triggers at 70% CPU; ≥ 2 API replicas for game server |
| **CI / CD** | GitHub Actions | Lint → Test → Build → Deploy pipeline; coverage gate ≥ 80%; see `docs/CICD.md` |
| **Email** | SendGrid v3 (primary) + Nodemailer SMTP (fallback) | Failover after 3 consecutive SendGrid failures; SPF + DKIM configured |
| **Testing** | Vitest (unit) + Supertest (integration) + Playwright (E2E) + Cucumber (BDD) | 80% coverage enforced as CI gate |
| **Observability** | Pino (structured JSON logs) + OpenTelemetry + Prometheus | Traces exported via OTel collector |

---

## Quick Start

### Prerequisites

All three installation paths share these requirements:

- [Git](https://git-scm.com/) 2.40+
- An `.env` file — copy from `.env.example` (see [Environment Variables](#environment-variables))

---

### Docker (Recommended)

The fastest path: Docker Compose starts the app, PostgreSQL, Redis, and MailHog (local email catcher) with a single command.

**Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) 24+ (includes Compose v2)

```bash
git clone https://github.com/ibalasite/pet.git
cd pet

# Configure environment
cp .env.example .env
# Edit .env — at minimum confirm POSTGRES_PASSWORD and generate EMAIL_ENCRYPTION_KEY:
#   openssl rand -hex 32

# Start all services (api + postgres + redis + mailhog)
docker compose up -d

# Confirm everything is healthy
docker compose ps
# Expected: all services show "running (healthy)"
```

Verify the app is responding:

```bash
curl http://localhost:3000/health
# {"status":"ok","version":"1.0.0","uptime":3}
```

Open the player app at **http://localhost:5173** and the admin portal at **http://localhost:5174**.

MailHog web UI (captured claim emails): **http://localhost:8025**

---

### macOS / Linux (Native)

**Prerequisites:**

- Node.js 20 LTS ([install guide](https://nodejs.org/en/download/))
- pnpm 9.x — `npm install -g pnpm@latest`
- PostgreSQL 15+ (local or Supabase CLI) and Redis 7+ (local or Upstash)
- See [docs/LOCAL_DEPLOY.md](docs/LOCAL_DEPLOY.md) for the full local setup including Supabase CLI and TOTP admin bootstrap.

```bash
git clone https://github.com/ibalasite/pet.git
cd pet

# Install all workspace dependencies (resolves the pnpm workspace tree)
pnpm install

# Configure environment for each app (api, player-app, admin-app)
cp .env.example .env
# Edit .env with your local database, Redis, and email credentials

# Run database migrations
pnpm db:migrate

# Seed the database (creates a default admin account; SAVE THE PRINTED CREDENTIALS)
pnpm db:seed

# Start the development servers (API + player app + admin portal concurrently)
pnpm dev
# or per-app:
#   pnpm --filter api dev
#   pnpm --filter player-app dev
#   pnpm --filter admin-app dev
```

Expected output:

```
[api]         Listening on http://localhost:3000
[api]         Database: connected (postgres://localhost:5432/pixel_pet_arena)
[api]         Redis: connected (redis://localhost:6379)
[player-app]  VITE v5.x.x  ready in  800 ms  →  http://localhost:5173/
[admin-app]   VITE v5.x.x  ready in  900 ms  →  http://localhost:5174/
```

---

### Windows (PowerShell)

> **Recommendation:** Use [WSL 2](https://learn.microsoft.com/windows/wsl/install) + Docker Desktop for the smoothest experience. The commands below work in PowerShell 7+ natively.

**Prerequisites:** Node.js 20 LTS, pnpm 9.x, PostgreSQL 15+, Redis 7+ (all installable via [winget](https://learn.microsoft.com/windows/package-manager/)).

```powershell
git clone https://github.com/ibalasite/pet.git
Set-Location pet

# Install all workspace dependencies
pnpm install

# Configure environment
Copy-Item .env.example .env
# Open .env in your editor and fill in database / Redis / email credentials

# Run database migrations
pnpm db:migrate

# Start the development servers
pnpm dev
```

Verify the server started:

```powershell
Invoke-RestMethod http://localhost:3000/health
```

---

## Environment Variables

Copy `.env.example` to `.env` before starting. The app validates all required variables at startup and exits with a clear error if any are missing. Each app in the monorepo (`api`, `player-app`, `admin-app`) has its own `.env.example` — see [docs/LOCAL_DEPLOY.md §Environment Setup](docs/LOCAL_DEPLOY.md) for the full per-app matrix.

| Variable | Description | Required | Default | Example |
|----------|-------------|----------|---------|---------|
| `POSTGRES_DB` | PostgreSQL database name | Yes | — | `pixel_pet_arena` |
| `POSTGRES_USER` | PostgreSQL username | Yes | — | `postgres` |
| `POSTGRES_PASSWORD` | PostgreSQL password | Yes | — | `changeme_local` |
| `DATABASE_URL` | Full PostgreSQL connection string (overrides `POSTGRES_*` if set) | No | built from `POSTGRES_*` | `postgresql://user:pass@localhost:5432/pixel_pet_arena` |
| `REDIS_URL` | Redis connection string (Upstash or local) | No | `redis://localhost:6379` | `rediss://user:pass@host:6380` |
| `SENDGRID_API_KEY` | SendGrid v3 API key for transactional email | Yes (prod) | — | `SG.xxxxx` |
| `EMAIL_ENCRYPTION_KEY` | AES-256-GCM key for GDPR email storage (hex 32 bytes) | Yes | — | `openssl rand -hex 32` |
| `JWT_SECRET` | HMAC secret for short-lived signed tokens (admin TOTP setup, etc.) | Yes | — | `openssl rand -hex 32` |
| `APP_PORT` | HTTP port the Game API listens on | No | `3000` | `8080` |
| `LOG_LEVEL` | Minimum log level (`debug`, `info`, `warn`, `error`) | No | `info` | `debug` |
| `ADMIN_TOTP_ISSUER` | TOTP issuer label shown in authenticator apps | No | `pixel-pet-arena` | `Pixel Pet Arena (Staging)` |
| `FF_MARKETPLACE` | Feature flag — pet trading marketplace (Phase 3) | No | `false` | `true` |
| `FF_BATTLE_RECORDS` | Feature flag — Battle Records page (P0/ON, kill-switch) | No | `true` | `false` |

See `.env.example` for the full annotated list and optional tuning parameters (rate-limit overrides, food-buff multiplier ranges, etc.).

---

## API Quick Reference

All player-facing endpoints use the `/api/v1/` prefix. All admin endpoints use the `/admin/api/` prefix and are served by the same Node.js/Fastify process. Authentication: pet endpoints use `Authorization: Bearer <pet_access_token>`; admin endpoints use httpOnly session cookie + TOTP.

| Method + Path | Auth | Description |
|---------------|------|-------------|
| `POST /api/v1/claim` | None | Send 6-digit OTP to email address to begin claim |
| `POST /api/v1/claim/verify` | None | Verify OTP code → receive permanent pet access token + URL |
| `POST /api/v1/claim/recover` | None | Recover access for a lost bookmarked URL (issues fresh token, invalidates old) |
| `GET /api/v1/pets/random` | None | Generate and preview a fresh procedural pet (pre-claim) |
| `GET /api/v1/pets/:petId` | None | Retrieve public pet profile (stats, appearance, rarity) |
| `POST /api/v1/pets/:petId/train` | Pet token | Perform 1 training action (max 3/day, reset UTC 00:00) |
| `POST /api/v1/pets/:petId/feed` | Pet token | Apply a food buff (temporary or permanent stat boost) |
| `POST /api/v1/arena/enter` | Pet token | Enter arena queue (race or sumo mode); rate-limited 10/hr default |
| `GET /api/v1/leaderboard` | None | Top 100 pets by win rate; filterable by rarity |
| `GET /health` | None | Service health check with version and uptime |

For full request/response schemas, error codes, rate limits, and admin endpoints see:

- Markdown source: [docs/API.md](docs/API.md)
- HTML online: [docs/pages/api.html](docs/pages/api.html)
- Mock server: [docs/blueprint/mock/](docs/blueprint/mock/) (FastAPI-based stub for frontend development)
- OpenAPI 3.1 contract: [docs/blueprint/contracts/openapi.yaml](docs/blueprint/contracts/openapi.yaml)

---

## Directory Structure

```
pixel-pet-arena/
├── .github/                    # GitHub Actions CI/CD workflows
│   └── workflows/
│       ├── ci.yml              # Lint, test, build on every PR
│       └── deploy.yml          # Deploy to Railway + Vercel
├── apps/
│   ├── api/                    # Fastify 4 unified API process (Game + Admin plugins)
│   │   └── src/
│   │       ├── claim/          # OTP generation, email dispatch, token issuance
│   │       ├── pets/           # Pet CRUD, training, feeding
│   │       ├── arena/          # Matchmaking, battle engine, result recording
│   │       ├── leaderboard/    # Redis sorted set reads + PostgreSQL fallback
│   │       ├── admin/          # Admin plugin (mounted at /admin/api)
│   │       └── shared/         # Config, logger, Zod schemas, DB client
│   ├── player-app/             # React 18 + Phaser.js 3 player SPA
│   │   └── src/
│   │       ├── game/           # Phaser.js canvas engine, sprite generator
│   │       ├── claim/          # Claim flow (3-step compound component)
│   │       ├── arena/          # Arena lobby, match UI
│   │       └── leaderboard/    # Leaderboard page
│   └── admin-app/              # Vue 3 + Element Plus admin SPA
├── packages/
│   ├── shared-types/           # Shared TypeScript types across all apps
│   └── constants/              # Shared game constants from constants.json
├── docs/                       # Markdown source for all design documents
│   ├── BRD.md                  # Business Requirements Document
│   ├── PRD.md                  # Product Requirements Document
│   ├── PDD.md                  # Product Design Document (UX)
│   ├── EDD.md                  # Engineering Design Document
│   ├── ARCH.md                 # System Architecture + ADRs
│   ├── API.md                  # REST API reference
│   ├── SCHEMA.md               # Database schema reference
│   ├── CICD.md                 # CI/CD pipeline design
│   ├── LOCAL_DEPLOY.md         # Local development deployment guide
│   ├── test-plan.md            # Test Plan + RTM
│   ├── diagrams/               # Generated UML (9 server + 16 frontend + 5 CI/CD + 2 modulith)
│   ├── blueprint/              # Generated contracts (OpenAPI, JSON Schema, Pact, IaC, mock server)
│   └── pages/                  # Generated HTML documentation site (incl. interactive prototypes)
├── features/                   # Cucumber/Gherkin BDD feature files (server-side)
│   ├── claim-flow.feature
│   ├── arena-battle.feature
│   ├── battle-records.feature
│   ├── leaderboard.feature
│   ├── training-food.feature
│   ├── trading-system.feature
│   ├── rarity-distribution.feature
│   ├── economy-config.feature
│   ├── admin-moderation.feature
│   ├── admin-search-performance.feature
│   ├── suspicious-detection.feature
│   ├── gdpr-erasure.feature
│   └── client/                 # Playwright E2E feature files
│       ├── claim-flow-ui.feature
│       ├── pet-display.feature
│       ├── training-ui.feature
│       ├── food-system.feature
│       ├── arena-ui.feature
│       ├── battle-records.feature
│       ├── leaderboard-ui.feature
│       ├── admin-portal.feature
│       └── settings.feature
├── .env.example                # Annotated environment variable template
├── docker-compose.yml          # Local multi-service development stack
├── pnpm-workspace.yaml         # pnpm workspace definition
└── package.json                # Monorepo root
```

---

## Documentation

The full documentation suite is generated into a static HTML site in `docs/pages/`.

| Document | Markdown Source | HTML | Description |
|----------|----------------|------|-------------|
| BRD | [docs/BRD.md](docs/BRD.md) | [brd.html](docs/pages/brd.html) | Business goals, ROI analysis, stakeholder sign-off |
| PRD | [docs/PRD.md](docs/PRD.md) | [prd.html](docs/pages/prd.html) | User stories, acceptance criteria, priority tiers |
| PDD | [docs/PDD.md](docs/PDD.md) | [pdd.html](docs/pages/pdd.html) | UX flows, wireframes, component specs |
| EDD | [docs/EDD.md](docs/EDD.md) | [edd.html](docs/pages/edd.html) | Architecture, technology choices, data models |
| ARCH | [docs/ARCH.md](docs/ARCH.md) | [arch.html](docs/pages/arch.html) | C4 diagrams, component architecture, ADRs |
| API | [docs/API.md](docs/API.md) | [api.html](docs/pages/api.html) | REST API endpoints, schemas, error codes |
| SCHEMA | [docs/SCHEMA.md](docs/SCHEMA.md) | [schema.html](docs/pages/schema.html) | Database table definitions and ERD |
| CICD | [docs/CICD.md](docs/CICD.md) | [cicd.html](docs/pages/cicd.html) | CI/CD pipeline, secrets flow, infra topology |
| LOCAL_DEPLOY | [docs/LOCAL_DEPLOY.md](docs/LOCAL_DEPLOY.md) | [local-deploy.html](docs/pages/local-deploy.html) | Local development setup walkthrough |
| BDD (server) | [features/](features/) | [bdd-server.html](docs/pages/bdd-server.html) | Gherkin server feature files |
| BDD (client / E2E) | [features/client/](features/client/) | [bdd-client.html](docs/pages/bdd-client.html) | Playwright E2E feature files |
| Test Plan | [docs/test-plan.md](docs/test-plan.md) | [test-plan.html](docs/pages/test-plan.html) | Test strategy, coverage matrix, RTM |

### Interactive Demos

Three runnable, zero-backend prototypes ship with the docs site so reviewers can experience the full surface area without a local dev stack:

| Demo | Link | Description |
|------|------|-------------|
| UI Prototype (Player) | [docs/pages/prototype/index.html](docs/pages/prototype/index.html) | 10 player-facing screens (Landing → Claim → My Pet → Training → Arena → Battle Result → Leaderboard → Battle Records → Marketplace → GDPR) with hash-routing, mock data, Web Audio synth, and 28 P0/P1 animations |
| API Explorer | [docs/pages/prototype/api-explorer/index.html](docs/pages/prototype/api-explorer/index.html) | Postman-style explorer for all 53 endpoints across 16 groups; chip quick-select for enum params, request body presets, copy-as-cURL, hash deep-links, and JavaScript mock responses (no backend required) |
| Admin Portal Prototype | [docs/pages/prototype/admin/admin-login.html](docs/pages/prototype/admin/admin-login.html) | 5-page Admin Portal walkthrough — Login (admin / Admin@2026 / TOTP 123456) → Dashboard → Users → Roles → Audit Log; covers RBAC (5 roles, 30 permissions), GDPR queue, suspicious-pet review, and 18-entry CSV-exportable immutable audit trail |

Regenerate the HTML site:

```bash
python3 ~/.claude/skills/gendoc/tools/bin/gen_html.py
# Output: docs/pages/*.html
```

---

## Testing

### Run All Tests

```bash
pnpm test
```

### Generate Coverage Report

```bash
pnpm test:coverage
# Report written to coverage/lcov-report/index.html
```

Coverage target: **80% lines, branches, functions.** The CI pipeline fails if coverage drops below this threshold.

### Individual Test Types

```bash
# Unit tests only (Vitest)
pnpm test:unit

# Integration tests (requires DATABASE_URL and REDIS_URL)
pnpm test:integration

# BDD / Cucumber feature tests (server)
pnpm test:bdd

# End-to-end tests (Playwright, requires a running app instance)
pnpm test:e2e
```

### Performance Targets

| Metric | Target |
|--------|--------|
| P99 read latency | < 200 ms at 100 RPS |
| P99 write latency | < 500 ms at 100 RPS |
| LCP (player app) | < 2.5 s |
| FCP (player app) | < 1.5 s |
| CLS | < 0.1 |
| Leaderboard update lag | ≤ 30 s (Redis sorted set vs. PostgreSQL `battle_records`) |

---

## Known Limitations

1. **Email pre-scan (Gmail/Outlook)**: Email clients may auto-click URLs in emails. Mitigated by using a 6-digit numeric code + a separate URL (not a magic-link), requiring manual code entry.
2. **Token enumeration surface**: Pet access tokens are 32-byte cryptographically random — brute-force infeasible — but long-lived. Pets with no owner interaction for `PET_RESERVATION_TTL_HOURS` (24h) are cleaned up.
3. **Arena matchmaking at low CCU**: With < ~50 online players, AI-controlled opponents fill matchmaking after the 30-second timeout. AI fallback stats are seeded from the global average.
4. **Leaderboard eventual consistency**: Redis sorted set may lag up to 30 seconds behind the authoritative PostgreSQL `battle_records` table during peak load. Displayed with a "last updated" timestamp.
5. **Marketplace (P2) not yet implemented**: Pet trading feature (`FF_MARKETPLACE`) is behind a feature flag and not available in v1.0.
6. **Admin runtime config cache**: Admin parameter changes (`PUT /admin/api/config/runtime`) take effect within 5 minutes due to `config_cache_refresh_time_minutes = 5`.

---

## Changelog

See [GitHub Releases](https://github.com/ibalasite/pet/releases) for versioned release notes. Changes to design docs are tracked in each `docs/*.md` file's Change Log section.

---

## Development Guide

> This README is auto-generated from `docs/BRD.md`, `docs/PRD.md`, `docs/EDD.md`, `docs/ARCH.md`, `docs/API.md`, and related upstream documents via the `gendoc` pipeline. To regenerate: `/gendoc readme` or `/gendoc-gen-html`.

See [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) for the full onboarding guide including branch strategy, commit message format, PR checklist, local environment tips, and release process.

### Branch Strategy

| Branch | Purpose | Direct Push |
|--------|---------|-------------|
| `main` | Production-ready code, tagged releases | No — PR only |
| `develop` | Integration branch; staging deploys from here | No — PR only |
| `feature/<ticket-id>-short-description` | New features | Yes (author) |
| `fix/<ticket-id>-short-description` | Bug fixes | Yes (author) |

### Commit Message Format

Follows [Conventional Commits](https://www.conventionalcommits.org/): `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `perf`, `ci`.

```
feat(arena): add per-pet rate-limit override for admin tuning
fix(claim): reject expired OTP codes with 410 instead of 400
docs(readme): refresh from upstream after ALIGN-FIX
```

---

## License

MIT License

Copyright (c) 2026 pixel-pet-arena contributors

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.

See [LICENSE](LICENSE) for the full text.

---

## Security Policy

### Responsible Disclosure

If you discover a security vulnerability, **do not open a public GitHub Issue**. Instead, email **security@pixel-pet-arena.com** (or use [GitHub Security Advisories](https://github.com/ibalasite/pet/security/advisories/new)) with:

1. A description of the vulnerability and its potential impact
2. Steps to reproduce
3. Any suggested mitigations

**Response SLA:**

| Severity | Acknowledgement | Initial Assessment | Patch Target |
|----------|----------------|-------------------|--------------|
| Critical | 72 hours | 72 hours | 7 days |
| High | 72 hours | 7 days | 30 days |
| Medium | 72 hours | 14 days | 90 days |

We credit responsible disclosures in release notes. See [SECURITY.md](SECURITY.md) for the full policy.

---

## Architecture Quick Reference

| Key Decision | Choice | Document |
|-------------|--------|----------|
| API paradigm | REST (`/api/v1/`, `/admin/api/`) — URI path versioning | [docs/ARCH.md](docs/ARCH.md) |
| Database | PostgreSQL 15+ (Supabase managed) + Redis 7+ (Upstash) | [docs/SCHEMA.md](docs/SCHEMA.md) |
| Authentication | Email OTP → 32-byte cryptographic URL token (no sessions for players); httpOnly session + TOTP for admin | [docs/ARCH.md §5 Security](docs/ARCH.md) |
| Frontend separation | Player app (React + Phaser.js) and Admin portal (Vue 3 + Element Plus) as separate Vite builds | [docs/EDD.md](docs/EDD.md) |
| Multi-tenancy strategy | Single-tenant (one game instance per deployment); per-pet isolation via token-bound rows | [docs/SCHEMA.md](docs/SCHEMA.md) |
| Deployment platform | Vercel (frontend CDN) + Railway (API, autoscale HPA 70% CPU) | [docs/LOCAL_DEPLOY.md](docs/LOCAL_DEPLOY.md) |

Main ADRs: [docs/ARCH.md — Architecture Decision Records](docs/ARCH.md#14-architecture-decision-records)

---

## Code of Conduct

This project adopts the [Contributor Covenant](https://www.contributor-covenant.org/) v2.1 as its Code of Conduct.

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for the full text.

For violations, contact the maintainers at **conduct@pixel-pet-arena.com**.
