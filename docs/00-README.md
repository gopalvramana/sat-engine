# SAT Prep Platform — Master Knowledge Base

> Built by a parent frustrated with every existing SAT platform. Teaches students WHY they got a question wrong — not just what the right answer is.

**Date Started:** March 2026  
**Status:** Active Development  
**Target Launch:** Month 4 (approx July 2026)  
**Success Target:** Level 2 — $2,000–$4,000/month recurring revenue

---

## Documents in This Knowledge Base

| # | Document | What It Covers |
|---|----------|----------------|
| 01 | [Vision and Goals](01-vision-and-goals.md) | What we're building, who for, why, success definition |
| 02 | [Technology Stack](02-technology-stack.md) | Every technology choice with alternatives and reasons |
| 03 | [Architecture Decisions](03-architecture-decisions.md) | Rendering, DB schema, infrastructure, all ADRs |
| 04 | [Product Design](04-product-design.md) | Exam mode, adaptive engine, UI decisions |
| 05 | [AI Features](05-ai-features.md) | 3-tab panel, interactive modes, cost model |
| 06 | [Question Bank](06-question-bank.md) | Generation workflow, domain distribution, review process |
| 07 | [Business Model](07-business-model.md) | Pricing, H1B strategy, distribution, competitive positioning |
| 08 | [Build Roadmap](08-build-roadmap.md) | 3-month week-by-week plan, parallel tracks |
| 09 | [Competitive Analysis](09-competitive-analysis.md) | 8 players, 5 market gaps, your positioning |
| 10 | [What Has Been Validated](10-validated.md) | Everything built and proven so far |
| 11 | [Decision Log](11-decision-log.md) | All 41 decisions in one place |
| 12 | [SAT Skill Taxonomy](12-sat-skill-taxonomy.md) | All 66 skills across 8 domains |
| 14 | [Adaptive Learning Engine](14-adaptive-engine.md) | Diagnostic-first flow, mastery loop, session types, research backing |
| 15 | [Prerequisite Graph](15-prerequisite-graph.md) | 5-level DAG for all 66 skills — Math chains + R&W chains |
| 16 | [Question Pool Strategy](16-question-pool-strategy.md) | Two-pool model (drill vs test), pool size targets, generation priority |

---

## Quick Reference

### The One-Line Description
> The SAT platform that teaches you WHY — not just WHAT.

### Core Differentiator
Three structured AI tabs per question in review mode: **Solution**, **Core Concept**, **Prerequisites**. Each is a separate live Claude API call. No competitor has this.

### Target Market
Any motivated SAT student scoring 1100–1350 targeting 1400+. Indian-American community as warm launch channel — not permanent limit. Total addressable market: 1.7 million US SAT takers annually.

### Price
**$14.99/month** | $119.99/year | First test always free

### Tech Stack (summary)
Spring Boot 3.x · Java 21 · PostgreSQL · Thymeleaf · KaTeX · Chart.js · Claude AI · Railway · Supabase

---

## Current Status

- [x] KaTeX math rendering validated
- [x] SVG programmatic diagram rendering validated
- [x] Chart.js graph rendering validated
- [x] Combined rendering (all three together) validated
- [x] Dynamic data-driven question display validated
- [x] AI Learning Panel (3 tabs, live API calls) validated
- [x] Question generation script (generate_questions.py) built
- [x] Visual review tool (review_questions.html) built
- [ ] Spring Boot application — in progress
- [ ] User authentication
- [ ] Stripe payment integration
- [ ] Launch

---

## Key Numbers to Remember

| Metric | Number |
|--------|--------|
| Full SAT questions | 98 (54 R&W + 44 Math) |
| Questions to launch | 500–600 |
| Full tests at 500 questions | ~5 |
| Questions per week (evening routine) | ~80 reviewed |
| Weeks to 500 questions | 6–7 |
| API cost per student per month | ~$0.50 |
| Gross margin at scale | ~97% |
| Break-even students | 5–10 |
| 0.1% of SAT market | 1,700 students |
| Revenue at 0.1% | $25,000/month |
