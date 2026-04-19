# Skills Library — Codex CLI Instructions

This directory contains 171 production-ready skills organized in 8 domain HUBs.

## Skill Discovery

Skills are in `.codex/skills/` as symlinks pointing to their HUB folders.
Each skill has a `SKILL.md` with full instructions and `scripts/` with Python CLI tools.

## Domain HUBs

| HUB | Skills | Domain |
|-----|--------|--------|
| `_ENGINEERING_HUB/` | 90+ | Architecture, backend, frontend, DevOps, security, AI/ML, cloud |
| `_MARKETING_HUB/` | 44 | Content, SEO, CRO, growth, paid ads, social, email |
| `_MANAGEMENT_HUB/` | 16 | Product management, UX/UI, agile, roadmaps, SaaS |
| `_AGENT_INTELLIGENCE_HUB/` | 9 | Agent design, prompt engineering, self-improvement |
| `_WEB_DESIGN_HUB/` | 8 | Frontend design, GSAP, canvas, themes, testing |
| `_DATA_HUB/` | 5 | DOCX, PDF, PPTX, XLSX, financial analysis |
| `_IMAGE_CREATION_HUB/` | 3 | Image direction, brand guidelines, prompt mastery |
| `_MUSIC_CREATION_HUB/` | 2 | Songwriting, rhyming, lyrics |

## Routing Rules

1. Identify the domain from the task
2. Read the HUB's SKILL.md first, then the specific sub-skill SKILL.md
3. Load only 1-2 skills per request
4. Use Python tools in `scripts/` for analysis and scaffolding

## Key Skills by Task

| Task | Skill |
|------|-------|
| System design | `_ENGINEERING_HUB/senior-architect` |
| React/Next.js | `_ENGINEERING_HUB/senior-frontend` |
| API design | `_ENGINEERING_HUB/senior-backend` |
| Full project scaffold | `_ENGINEERING_HUB/senior-fullstack` |
| CI/CD pipelines | `_ENGINEERING_HUB/senior-devops` |
| Security | `_ENGINEERING_HUB/senior-security` |
| Code review | `_ENGINEERING_HUB/code-reviewer` |
| E2E testing | `_ENGINEERING_HUB/playwright-pro` |
| Content creation | `_MARKETING_HUB/content-creator` |
| Product management | `_MANAGEMENT_HUB/product-manager-toolkit` |
| Agent design | `_AGENT_INTELLIGENCE_HUB/agent-designer` |
