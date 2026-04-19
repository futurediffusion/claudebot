# Skills Library — Gemini CLI Instructions

This directory contains 171 production-ready skills organized in 8 domain HUBs.

## Activating a Skill

Use the skill name directly:
```
activate_skill(name="senior-architect")
activate_skill(name="content-creator")
activate_skill(name="product-manager-toolkit")
```

Skills are in `.gemini/skills/` as symlinks. Gemini will find `SKILL.md` automatically.

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

## Rules

- Load only 1-2 skills per request
- Read the HUB SKILL.md first for domain context, then the sub-skill SKILL.md
- Python tools are in each skill's `scripts/` folder (stdlib-only, CLI-first)
