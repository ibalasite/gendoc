<!-- DOC-ID: README-GENDOC-20260423 | Version: v1.0 | Status: ACTIVE | Author: ibalasite | Date: 2026-04-23 -->

# gendoc

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey)](https://github.com/ibalasite/gendoc)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-skill-blueviolet)](https://claude.ai/code)

**AI-driven engineering document generation system for Claude Code.** One command generates BRD, PRD, EDD, ARCH, API, Schema, Runbook and more — each document inherits knowledge from all upstream docs automatically.

---

## Overview

`gendoc` is a Claude Code skill suite that automates the full engineering documentation lifecycle. Using a three-layer template architecture (`TYPE.md` structure + `TYPE.gen.md` generation rules + `TYPE.review.md` review criteria), it generates and iteratively reviews production-quality engineering documents from an initial idea through deployment runbooks.

Key capabilities:
- **Cumulative upstream reading** — every doc reads all ancestor docs, never just its direct parent
- **Universal generation** — `/gendoc <type>` for any document type, driven by templates
- **Universal review loop** — `/reviewdoc <type>` with configurable strategy (rapid / standard / exhaustive)
- **Auto-update via SessionStart hook** — harness-enforced, LLM-independent, runs in background
- **Windows native support** — Python-based hook for Windows, bash for macOS/Linux

---

## Skills

| Skill | Command | Purpose |
|-------|---------|---------|
| `gendoc` | `/gendoc <type>` | Generate any document type |
| `reviewdoc` | `/reviewdoc <type>` | Review & iteratively fix any document |
| `gendoc-auto` | `/gendoc-auto` | Full pipeline: all docs + reviews in sequence |
| `gendoc-flow` | `/gendoc-flow` | Step-through pipeline with pause points |
| `gendoc-config` | `/gendoc-config` | Configure execution mode & review strategy |
| `gendoc-align-check` | `/gendoc-align-check` | Cross-document alignment scan |
| `gendoc-align-fix` | `/gendoc-align-fix` | Auto-fix alignment issues |
| `gendoc-gen-html` | `/gendoc-gen-html` | Generate HTML documentation site |
| `gendoc-gen-diagrams` | `/gendoc-gen-diagrams` | Generate architecture diagrams |
| `gendoc-gen-client-bdd` | `/gendoc-gen-client-bdd` | Client-facing BDD features |
| `gendoc-update` | `/gendoc-update` | Manual skill upgrade |

### Supported Document Types

`edd` · `brd` · `prd` · `pdd` · `arch` · `api` · `schema` · `bdd` · `test-plan` · `runbook` · `local-deploy` · `idea` · `readme`

---

## Quick Start

### Install (macOS / Linux / WSL)

```bash
# 1. Clone
git clone https://github.com/ibalasite/gendoc.git ~/projects/gendoc

# 2. Install skills + register auto-update hook
cd ~/projects/gendoc && ./setup

# 3. Restart Claude Code — skills are now available
```

### Install (Windows native)

```powershell
# Requires: Git for Windows + Python 3
git clone https://github.com/ibalasite/gendoc.git ~/projects/gendoc
cd ~/projects/gendoc
.\setup.ps1
```

### Uninstall

```bash
~/projects/gendoc/setup --uninstall   # macOS/Linux
# Or: .\setup.ps1 -Uninstall          # Windows
```

---

## Usage

```bash
# Generate a single document (reads templates automatically)
/gendoc edd
/gendoc brd
/gendoc runbook

# Review a document with iterative fix loop
/reviewdoc edd
/reviewdoc runbook

# Full pipeline (interactive)
/gendoc-config       # set mode: interactive or full-auto
/gendoc-auto         # run all docs sequentially

# Manual upgrade
/gendoc-update
```

---

## Auto-Update

After `./setup`, a **SessionStart hook** is registered in `~/.claude/settings.json`. Every time Claude Code starts a session, the harness automatically runs `git pull + install` in the background (throttled to once per hour). No LLM involvement — 100% reliable.

```
Session start → harness triggers hook → git pull (background) → skills updated
```

Manual update: `/gendoc-update` or `~/projects/gendoc/bin/gendoc-upgrade`

---

## Template Architecture

```
templates/
├── <TYPE>.md          ← document structure skeleton
├── <TYPE>.gen.md      ← AI generation rules (Iron Law: must be read first)
└── <TYPE>.review.md   ← review criteria & quality gates
```

The **Iron Law**: no document is generated without reading both `TYPE.md` AND `TYPE.gen.md` first. Templates are the single source of truth — editing a template immediately changes behavior of all `/gendoc` and `/reviewdoc` calls.

### Upstream Dependency Chain

```
IDEA → BRD → PRD → PDD
              ↓      ↓
             EDD → ARCH → API → SCHEMA
                    ↓      ↓      ↓
              test-plan  BDD   runbook
                    ↓
              local-deploy → README
```

Each document accumulates knowledge from all ancestors (skips silently if missing).

---

## Repository Structure

```
gendoc/
├── setup               # Install script (macOS/Linux)
├── setup.ps1           # Install script (Windows PowerShell)
├── install.sh          # Sync skills/ → ~/.claude/skills/ (bash)
├── install.py          # Sync skills/ → ~/.claude/skills/ (Python/Windows)
├── bin/
│   ├── gendoc-session-update      # SessionStart hook (bash)
│   ├── gendoc-session-update.py   # SessionStart hook (Python)
│   ├── _gendoc-update-worker.py   # Background update worker
│   ├── gendoc-settings-hook       # settings.json editor (bash wrapper)
│   ├── gendoc-settings-hook.py    # settings.json editor (Python)
│   └── gendoc-upgrade             # Manual upgrade script
├── skills/                        # Source of truth for all SKILL.md files
│   ├── gendoc/
│   ├── gendoc-auto/
│   ├── gendoc-flow/
│   └── ...
├── templates/                     # Document templates (structure + gen rules + review)
│   ├── EDD.md / EDD.gen.md
│   ├── BRD.md / BRD.gen.md
│   └── ...
└── docs/                          # gendoc's own project documentation
```

---

## Review Strategies

Configure via `/gendoc-config`:

| Strategy | Max Rounds | Stop Condition |
|----------|-----------|----------------|
| `rapid` | 3 | first round with 0 findings |
| `standard` | 5 | first round with 0 findings (default) |
| `exhaustive` | unlimited | findings = 0 |
| `tiered` | unlimited | rounds 1–5: findings=0; round 6+: CRITICAL+HIGH+MEDIUM=0 |
| `custom` | unlimited | user-defined condition |

---

## Requirements

| Platform | Requirements |
|----------|-------------|
| macOS / Linux | Git, Python 3, Claude Code |
| Windows (PowerShell) | Git for Windows, Python 3, Claude Code |
| Windows (WSL / git-bash) | Same as macOS/Linux |

---

## Contributing

1. Edit skill files in `skills/<skill-name>/SKILL.md` or templates in `templates/`
2. Run `./install.sh` to deploy changes to `~/.claude/skills/`
3. Test with Claude Code
4. Commit and push — other machines auto-pull via SessionStart hook

---

## License

MIT © ibalasite
