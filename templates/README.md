<!--
  DOC-ID:  README-{{PROJECT_SLUG}}-{{YYYYMMDD}}
  Version: v1.0
  Status:  DRAFT | IN_REVIEW | APPROVED
  Author:  {{AUTHOR}}
  Date:    {{DATE}}
  Upstream docs:
    - BRD: docs/BRD.md  (Business Requirements Document)
    - PRD: docs/PRD.md  (Product Requirements Document)
    - PDD: docs/PDD.md  (Product Design Document)
    - EDD: docs/EDD.md  (Engineering Design Document)
  Change log:
    v1.0  {{DATE}}  {{AUTHOR}}  Initial generated draft
-->

# {{PROJECT_NAME}}

> {{ONE_LINE_TAGLINE}}
> *(Example: "A self-hosted webhook relay that fans out events to multiple downstream services with zero message loss.")*

[![CI](https://github.com/{{GH_OWNER}}/{{GH_REPO}}/actions/workflows/ci.yml/badge.svg)](https://github.com/{{GH_OWNER}}/{{GH_REPO}}/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/{{GH_OWNER}}/{{GH_REPO}}/branch/main/graph/badge.svg)](https://codecov.io/gh/{{GH_OWNER}}/{{GH_REPO}})
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/github/v/release/{{GH_OWNER}}/{{GH_REPO}})](https://github.com/{{GH_OWNER}}/{{GH_REPO}}/releases)
[![Docker Pulls](https://img.shields.io/docker/pulls/{{DOCKER_HUB_IMAGE}})](https://hub.docker.com/r/{{DOCKER_HUB_IMAGE}})

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
- [Development Workflow](#development-workflow)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)

---

## Overview

{{PROJECT_NAME}} is {{PRODUCT_TYPE_DESCRIPTION}}.
*(Example: "a lightweight, self-hosted event-routing gateway built for platform engineering teams who need reliable webhook fan-out without depending on third-party SaaS.")*

It was built to solve **{{CORE_PROBLEM}}** — a gap that matters to **{{TARGET_AUDIENCE}}** because {{WHY_IT_MATTERS}}.
*(Example: "It was built to solve the sprawling, unmaintained webhook integrations that appear inside every growing monolith — a gap that matters to backend and infrastructure engineers because missed events silently break downstream workflows and are nearly impossible to trace.")*

The project is governed by the upstream documents below; every design decision maps to a tracked requirement:

| Document | Purpose |
|----------|---------|
| [BRD](docs/BRD.md) | Business goals, success metrics, stakeholder sign-off |
| [PRD](docs/PRD.md) | User stories, acceptance criteria, priority tiers |
| [PDD](docs/PDD.md) | UX flows, interaction specs, design tokens |
| [EDD](docs/EDD.md) | Architecture decisions, technology choices, data models |

See [System Architecture](#system-architecture) below for a visual overview, and [Documentation](#documentation) for the full HTML reference site.

---

## Core Features

**P0 — Must ship for v1.0:**

- **{{FEATURE_1_NAME}}** — {{FEATURE_1_DESCRIPTION}}
  *(Example: "Event Ingestion — Accepts signed webhook payloads over HTTPS with HMAC-SHA256 verification and idempotency key deduplication.")*
- **{{FEATURE_2_NAME}}** — {{FEATURE_2_DESCRIPTION}}
  *(Example: "Fan-out Routing — Delivers each event to N configured downstream targets in parallel with per-target retry budgets.")*
- **{{FEATURE_3_NAME}}** — {{FEATURE_3_DESCRIPTION}}
  *(Example: "Dead-Letter Queue — Persists undeliverable events to a configurable DLQ (Redis Stream or PostgreSQL table) for manual replay.")*
- **{{FEATURE_4_NAME}}** — {{FEATURE_4_DESCRIPTION}}
  *(Example: "Observability — Emits structured JSON logs, Prometheus metrics, and OpenTelemetry traces out of the box.")*
- **{{FEATURE_5_NAME}}** — {{FEATURE_5_DESCRIPTION}}
  *(Example: "Admin API — REST API for managing routes, secrets, and replaying DLQ events; protected by API-key auth.")*
- **{{FEATURE_6_NAME}}** — {{FEATURE_6_DESCRIPTION}}
  *(Example: "Zero-downtime Deploys — Graceful shutdown drains in-flight requests before the process exits.")*

---

## System Architecture

```mermaid
flowchart LR
    subgraph Ingress
        A([Client / Webhook Source])
    end

    subgraph {{PROJECT_NAME}} Core
        B[Ingestion API\nHMAC verify + dedup]
        C[Event Router]
        D[(PostgreSQL\nEvent Store)]
        E[(Redis\nDLQ + Job Queue)]
    end

    subgraph Downstream Targets
        F[Target Service A]
        G[Target Service B]
        H[Target Service N]
    end

    subgraph Observability
        I[Prometheus\n+ Grafana]
        J[OpenTelemetry\nCollector]
    end

    A -->|HTTPS POST| B
    B --> D
    B --> C
    C -->|parallel fan-out| F & G & H
    C -->|on failure| E
    E -->|retry worker| C
    B --> J
    C --> I
```

> For component-level detail, data flow diagrams, and ADR records see:
> - [PDD — Product Design Document]({{GH_PAGES_URL}}pdd.html) (UX + interaction specs)
> - [EDD — Engineering Design Document]({{GH_PAGES_URL}}edd.html) (architecture + implementation)

---

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| **Frontend** | {{FRONTEND_TECH}} | *(Example: React 18 + TypeScript + Vite)* |
| **Backend** | {{BACKEND_TECH}} | *(Example: Node.js 20 + Fastify 4)* |
| **Database** | {{DATABASE_TECH}} | *(Example: PostgreSQL 16 — primary store for events and routing config)* |
| **Cache / Queue** | {{CACHE_TECH}} | *(Example: Redis 7 — DLQ, rate-limit counters, ephemeral job state)* |
| **Infrastructure** | {{INFRA_TECH}} | *(Example: Docker + Kubernetes (k8s/); manifests in k8s/)* |
| **CI / CD** | {{CICD_TECH}} | *(Example: GitHub Actions — see .github/workflows/)* |
| **Observability** | {{OBS_TECH}} | *(Example: Prometheus + Grafana + OpenTelemetry)* |
| **Testing** | {{TEST_TECH}} | *(Example: Jest + Supertest (unit/integration), Playwright (e2e), Cucumber (BDD))* |

---

## Quick Start

### Prerequisites

All three installation paths share these requirements:

- [Git](https://git-scm.com/) 2.40+
- An `.env` file — copy from `.env.example` (see [Environment Variables](#environment-variables))

---

### Docker (Recommended)

The fastest path to a running instance. Docker Compose starts all services — app, database, and cache — with a single command.

**Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) 24+ (includes Compose v2)

```bash
git clone https://github.com/{{GH_OWNER}}/{{GH_REPO}}.git
cd {{GH_REPO}}

# Configure environment
cp .env.example .env
# Edit .env — at minimum set DATABASE_URL and REDIS_URL

# Start all services
docker compose up -d

# Confirm everything is healthy
docker compose ps
# Expected: all services show "running (healthy)"
```

Verify the app is responding:

```bash
curl http://localhost:{{APP_PORT}}/health
# {"status":"ok","version":"{{VERSION}}","uptime":3}
```

---

### macOS / Linux (Native)

Use this path when you want to run the app process directly on your machine.

**Prerequisites:**

- {{RUNTIME_NAME}} {{RUNTIME_VERSION}}+ ([install guide]({{RUNTIME_INSTALL_URL}}))
- PostgreSQL 16+ (local) or a remote connection string in `DATABASE_URL`
- Redis 7+ (local) or a remote connection string in `REDIS_URL`

```bash
git clone https://github.com/{{GH_OWNER}}/{{GH_REPO}}.git
cd {{GH_REPO}}

# Install dependencies
{{INSTALL_CMD}}
# Example: npm install

# Configure environment
cp .env.example .env
# Edit .env with your local database and Redis credentials

# Run database migrations
{{MIGRATE_CMD}}
# Example: npm run db:migrate

# Start the development server
{{DEV_START_CMD}}
# Example: npm run dev
```

Expected output:

```
[{{PROJECT_NAME}}] Listening on http://localhost:{{APP_PORT}}
[{{PROJECT_NAME}}] Database: connected (postgres://localhost:5432/{{DB_NAME}})
[{{PROJECT_NAME}}] Redis: connected (redis://localhost:6379)
```

---

### Windows (PowerShell)

> **Recommendation:** Use [WSL 2](https://learn.microsoft.com/windows/wsl/install) + Docker Desktop for the smoothest experience on Windows. The commands below work in PowerShell 7+ natively.

**Prerequisites:** Same runtime requirements as macOS / Linux above, installed via [winget](https://learn.microsoft.com/windows/package-manager/) or the official installers.

```powershell
git clone https://github.com/{{GH_OWNER}}/{{GH_REPO}}.git
Set-Location {{GH_REPO}}

# Install dependencies
{{INSTALL_CMD}}

# Configure environment
Copy-Item .env.example .env
# Open .env in your editor and fill in database / Redis credentials

# Run database migrations
{{MIGRATE_CMD}}

# Start the development server
{{DEV_START_CMD}}
```

Verify the server started:

```powershell
Invoke-RestMethod http://localhost:{{APP_PORT}}/health
```

---

## Environment Variables

Copy `.env.example` to `.env` before starting the application. The app validates all required variables at startup and exits with a clear error if any are missing.

| Variable | Description | Required | Default | Example |
|----------|-------------|----------|---------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | — | `postgresql://user:pass@localhost:5432/mydb` |
| `REDIS_URL` | Redis connection string | Yes | — | `redis://localhost:6379` |
| `APP_PORT` | HTTP port the server listens on | No | `3000` | `8080` |
| `LOG_LEVEL` | Minimum log level (`debug`, `info`, `warn`, `error`) | No | `info` | `debug` |
| `WEBHOOK_SECRET` | HMAC secret used to verify incoming payloads | Yes | — | `s3cr3t-at-least-32-chars` |
| `ADMIN_API_KEY` | API key for the admin endpoints | Yes | — | `adm_abc123xyz` |
| `{{ENV_VAR_1}}` | {{ENV_VAR_1_DESC}} | {{REQUIRED_1}} | `{{DEFAULT_1}}` | `{{EXAMPLE_1}}` |
| `{{ENV_VAR_2}}` | {{ENV_VAR_2_DESC}} | {{REQUIRED_2}} | `{{DEFAULT_2}}` | `{{EXAMPLE_2}}` |

See `.env.example` for the full annotated list and optional tuning parameters.

---

## API Quick Reference

All endpoints are prefixed with `/api/v1`. Authentication uses `Authorization: Bearer <ADMIN_API_KEY>` for admin routes and `X-Webhook-Signature` for inbound event routes.

| Method + Path | Auth | Description |
|---------------|------|-------------|
| `POST /api/v1/events` | Signature | Ingest a new webhook event |
| `GET /api/v1/events/:id` | Bearer | Retrieve a single event by ID |
| `GET /api/v1/routes` | Bearer | List all configured fan-out routes |
| `POST /api/v1/routes` | Bearer | Create a new routing rule |
| `POST /api/v1/dlq/:id/replay` | Bearer | Replay a dead-letter event |

For request/response schemas, error codes, rate limits, and pagination see the full API reference:

- Markdown source: [docs/API.md](docs/API.md)
- HTML online: [{{GH_PAGES_URL}}api.html]({{GH_PAGES_URL}}api.html)

---

## Directory Structure

```
{{GH_REPO}}/
├── .github/                  # GitHub Actions CI/CD workflows and PR templates
│   └── workflows/
│       ├── ci.yml            # Lint, test, build on every PR
│       └── deploy.yml        # Deploy to staging / production
├── docs/                     # Markdown source for all design documents
│   ├── BRD.md                # Business Requirements Document
│   ├── PRD.md                # Product Requirements Document
│   ├── PDD.md                # Product Design Document (UX)
│   ├── EDD.md                # Engineering Design Document
│   ├── API.md                # REST API reference
│   ├── SCHEMA.md             # Database schema reference
│   └── ARCH.md               # Architecture Decision Records (ADRs)
├── features/                 # BDD Gherkin feature files (Cucumber)
│   └── {{FEATURE_FILE}}.feature
├── k8s/                      # Kubernetes manifests (Deployment, Service, Ingress, HPA)
│   ├── base/
│   └── overlays/
│       ├── staging/
│       └── production/
├── scripts/                  # Developer and ops utility scripts
│   ├── db-migrate.sh         # Run pending database migrations
│   ├── seed.sh               # Seed development data
│   └── smoke-test.sh         # Post-deploy smoke test
├── src/                      # Application source code
│   ├── {{MODULE_1}}/         # *(Example: events/ — ingest and dedup)*
│   ├── {{MODULE_2}}/         # *(Example: router/ — fan-out worker)*
│   ├── {{MODULE_3}}/         # *(Example: admin/ — admin REST API)*
│   └── shared/               # Shared utilities, config, logger
├── tests/                    # Automated tests
│   ├── unit/                 # Pure function unit tests
│   ├── integration/          # API and database integration tests
│   └── e2e/                  # End-to-end tests (Playwright / Cucumber)
├── .env.example              # Annotated environment variable template
├── docker-compose.yml        # Local multi-service development stack
├── Dockerfile                # Production container image definition
└── {{PACKAGE_MANIFEST}}      # *(Example: package.json / go.mod / pyproject.toml)*
```

---

## Documentation

The full documentation suite is auto-generated into a static HTML site hosted on GitHub Pages at **[{{GH_PAGES_URL}}]({{GH_PAGES_URL}})**.

| Document | Markdown Source | HTML Online | Description |
|----------|----------------|-------------|-------------|
| BRD | [docs/BRD.md](docs/BRD.md) | [brd.html]({{GH_PAGES_URL}}brd.html) | Business goals, ROI analysis, stakeholder sign-off |
| PRD | [docs/PRD.md](docs/PRD.md) | [prd.html]({{GH_PAGES_URL}}prd.html) | User stories, acceptance criteria, priority tiers |
| PDD | [docs/PDD.md](docs/PDD.md) | [pdd.html]({{GH_PAGES_URL}}pdd.html) | UX flows, wireframes, component specs |
| EDD | [docs/EDD.md](docs/EDD.md) | [edd.html]({{GH_PAGES_URL}}edd.html) | Architecture, technology choices, data models |
| ARCH | [docs/ARCH.md](docs/ARCH.md) | [arch.html]({{GH_PAGES_URL}}arch.html) | Architecture Decision Records (ADRs) |
| API | [docs/API.md](docs/API.md) | [api.html]({{GH_PAGES_URL}}api.html) | REST API endpoints, schemas, error codes |
| SCHEMA | [docs/SCHEMA.md](docs/SCHEMA.md) | [schema.html]({{GH_PAGES_URL}}schema.html) | Database table definitions and ERD |
| BDD | [features/](features/) | [bdd.html]({{GH_PAGES_URL}}bdd.html) | Gherkin feature files and living documentation |

---

## Testing

### Run All Tests

```bash
{{TEST_CMD}}
# Example: npm test
```

### Generate Coverage Report

```bash
{{COVERAGE_CMD}}
# Example: npm run test:coverage
# Report written to coverage/lcov-report/index.html
```

Coverage target: **80% lines, branches, functions.** The CI pipeline fails if coverage drops below this threshold.

### Individual Test Types

```bash
# Unit tests only
{{UNIT_TEST_CMD}}
# Example: npm run test:unit

# Integration tests (requires DATABASE_URL and REDIS_URL)
{{INTEGRATION_TEST_CMD}}
# Example: npm run test:integration

# BDD / Cucumber feature tests
{{BDD_TEST_CMD}}
# Example: npm run test:bdd

# End-to-end tests (requires a running app instance)
{{E2E_TEST_CMD}}
# Example: npm run test:e2e
```

### CI Badge

The badge at the top of this file reflects the current `main` branch build status. A failing badge means the build, lint, or test suite is broken — do not merge PRs while it is red.

---

## Development Workflow

### Branch Strategy

| Branch | Purpose | Direct Push |
|--------|---------|-------------|
| `main` | Production-ready code, tagged releases | No — PR only |
| `develop` | Integration branch; staging deploys from here | No — PR only |
| `feature/{{TICKET_ID}}-short-description` | New features | Yes (author) |
| `fix/{{TICKET_ID}}-short-description` | Bug fixes | Yes (author) |
| `chore/{{TICKET_ID}}-short-description` | Tooling and maintenance | Yes (author) |

### Commit Message Format

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary in imperative mood>

[optional body — what and why, not how]

[optional footer — BREAKING CHANGE, closes #issue]
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `perf`, `ci`

Examples:
```
feat(router): add per-target retry budget configuration
fix(ingestion): reject payloads with replay-attack timestamps older than 5 min
docs(readme): add Windows PowerShell quick-start section
```

### Pull Request Checklist

Before requesting review, confirm all of the following:

- [ ] All CI checks are green (build, lint, type-check, tests)
- [ ] Coverage has not dropped below 80%
- [ ] New or changed public API behavior is documented in `docs/API.md`
- [ ] Breaking changes include a migration note and a `BREAKING CHANGE:` footer in the commit
- [ ] Relevant `docs/` files (EDD, SCHEMA, etc.) are updated if the implementation changed
- [ ] The PR description explains *why* the change is needed, not just *what* it does

---

## Deployment

### Staging

Staging deploys automatically on every merge to `develop`. The pipeline runs the full test suite, builds the Docker image, pushes it to the registry, and triggers a Kubernetes rolling update.

```bash
# Trigger a manual staging deploy (GitHub Actions)
gh workflow run deploy.yml -f environment=staging -f ref=develop
```

### Production

Production deploys are triggered by tagging a release on `main`:

```bash
git tag v{{NEXT_VERSION}} && git push origin v{{NEXT_VERSION}}
```

The CI pipeline promotes the staging image (already tested) to production without a rebuild.

### Rollback

If a production issue is detected:

```bash
# Identify the previous stable image tag
gh release list --limit 5

# Roll back Kubernetes deployment to previous tag
kubectl set image deployment/{{DEPLOYMENT_NAME}} \
  app={{DOCKER_HUB_IMAGE}}:{{PREVIOUS_TAG}} \
  -n {{K8S_NAMESPACE}}

# Verify pods are healthy
kubectl rollout status deployment/{{DEPLOYMENT_NAME}} -n {{K8S_NAMESPACE}}
```

For detailed runbook steps including database rollback procedures see [docs/EDD.md — Deployment]({{GH_PAGES_URL}}edd.html#deployment).

---

## Troubleshooting

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| `Error: connect ECONNREFUSED 127.0.0.1:5432` on startup | PostgreSQL is not running or `DATABASE_URL` is wrong | Start PostgreSQL, verify `DATABASE_URL` in `.env`, and run `npm run db:migrate` |
| `Error: Redis connection refused` | Redis is not running or `REDIS_URL` is misconfigured | Start Redis (`redis-server`) and confirm `REDIS_URL` in `.env` |
| `401 Unauthorized` on `POST /api/v1/events` | Webhook signature is invalid or `WEBHOOK_SECRET` mismatch | Ensure the sending service signs payloads with the same `WEBHOOK_SECRET` value |
| Docker Compose services restart repeatedly | Port conflict or missing `.env` values | Run `docker compose logs app` to read the startup error; confirm all required variables are set in `.env` |
| Test suite fails with `Cannot find module` | Dependencies not installed after a branch switch | Run `{{INSTALL_CMD}}` again; if using Node.js, delete `node_modules` and reinstall |

For issues not listed here, search [existing GitHub Issues](https://github.com/{{GH_OWNER}}/{{GH_REPO}}/issues) before opening a new one.

---

## Contributing

Contributions are welcome. Please read this section before submitting a pull request.

### Fork and PR Flow

1. Fork the repository on GitHub
2. Create a feature branch from `develop`: `git checkout -b feature/your-feature develop`
3. Write tests first (TDD) — the test suite must stay green
4. Commit using the Conventional Commits format described in [Development Workflow](#development-workflow)
5. Push your branch and open a PR against `develop` (not `main`)
6. Address all review feedback; request re-review after each update

### Code Style

- Code is formatted by {{FORMATTER}} on save (configured in `.{{FORMATTER_CONFIG}}`)
- Lint rules are defined in `.{{LINTER_CONFIG}}`
- Type-checking uses `{{TYPE_CHECK_CMD}}` — the CI blocks on type errors
- Run `{{FORMAT_CMD}}` locally before committing to avoid CI failures

### Issue Templates

Use the issue templates in `.github/ISSUE_TEMPLATE/`:

- **Bug report** — reproduction steps, expected vs actual behavior, environment details
- **Feature request** — problem statement, proposed solution, acceptance criteria
- **Documentation gap** — which document, what is missing or wrong

---

## License

MIT License

Copyright (c) {{YEAR}} {{COPYRIGHT_HOLDER}}

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

See [LICENSE](LICENSE) for the full text.

---

## Support

| Channel | Link | Response Time |
|---------|------|--------------|
| Bug reports & feature requests | [GitHub Issues](https://github.com/{{GH_OWNER}}/{{GH_REPO}}/issues) | Triaged within 3 business days |
| Security vulnerabilities | {{SECURITY_EMAIL}} | Acknowledged within 48 hours |
| General questions | [GitHub Discussions](https://github.com/{{GH_OWNER}}/{{GH_REPO}}/discussions) | Community-driven |

### Security Disclosure Policy

If you discover a security vulnerability, **do not open a public GitHub Issue**. Instead, email **{{SECURITY_EMAIL}}** with:

1. A description of the vulnerability and its potential impact
2. Steps to reproduce
3. Any suggested mitigations you have identified

You will receive an acknowledgement within 48 hours. We aim to release a patch within 14 days of a confirmed critical vulnerability and will credit responsible disclosures in the release notes.

---

## Security Policy（安全政策）

如發現安全漏洞，請**不要**透過公開 Issue 回報。

**負責任揭露（Responsible Disclosure）：**
- 發送 Email 至：{{SECURITY_EMAIL}}（或 `security@{{DOMAIN}}`）
- 或使用 GitHub 私人漏洞回報：[Security Advisories]({{GITHUB_REPO}}/security/advisories/new)

**回應承諾：**
- 72 小時內確認收到
- 7 日內提供初步評估
- 90 日內修復並公開披露（CVE）

詳見 [SECURITY.md](SECURITY.md)

---

## Architecture Quick Reference（架構速查）

| 關鍵決策 | 選擇 | 文件 |
|---------|------|------|
| API 範式 | REST / {{PARADIGM}} | [docs/ARCH.md](docs/ARCH.md#api-paradigm) |
| 資料庫 | {{DATABASE}} | [docs/SCHEMA.md](docs/SCHEMA.md) |
| 認證機制 | {{AUTH_METHOD}} | [docs/ARCH.md](docs/ARCH.md#security) |
| 多租戶策略 | {{TENANCY_STRATEGY}} | [docs/SCHEMA.md](docs/SCHEMA.md#multi-tenancy) |
| 部署平台 | {{DEPLOYMENT_PLATFORM}} | [docs/LOCAL_DEPLOY.md](docs/LOCAL_DEPLOY.md) |

主要 ADR（Architecture Decision Records）：[docs/ARCH.md#adr](docs/ARCH.md#adr)

---

## Code of Conduct（行為準則）

本專案採用 [Contributor Covenant](https://www.contributor-covenant.org/) v2.1 作為行為準則。
詳見 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

如有違規事宜，請聯繫 {{CONDUCT_EMAIL}}
