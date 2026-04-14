# Squad Team

> OpenTreasury — Open-source bank transaction management for NGOs

## Coordinator

| Name | Role | Notes |
|------|------|-------|
| Squad | Coordinator | Routes work, enforces handoffs and reviewer gates. |

## Members

| Name | Role | Charter | Status |
|------|------|---------|--------|
| Neo | Lead | .squad/agents/neo/charter.md | 🏗️ Lead |
| Trinity | Frontend Dev | .squad/agents/trinity/charter.md | ⚛️ Frontend |
| Morpheus | Backend Dev | .squad/agents/morpheus/charter.md | 🔧 Backend |
| Cypher | Tester | .squad/agents/cypher/charter.md | 🧪 Tester |
| Oracle | Docs / Feature Writer | .squad/agents/oracle/charter.md | 📝 Docs |
| Tank | DevOps / CI/CD | .squad/agents/tank/charter.md | ⚙️ DevOps |
| Switch | Security Engineer | .squad/agents/switch/charter.md | 🔒 Security |
| Niobe | Spec / UX Analyst | .squad/agents/niobe/charter.md | 📐 Spec/UX |
| Mouse | UI Designer | .squad/agents/mouse/charter.md | 🎨 UI Design |
| Scribe | Session Logger | .squad/agents/scribe/charter.md | 📋 Scribe |
| Ralph | Work Monitor | — | 🔄 Monitor |

## Project Context

- **Project:** OpenTreasury — Open-source bank transaction management for NGOs
- **User:** Pedro (perocha)
- **Frontend:** Angular 19 (standalone components, signals, OnPush, Angular Material)
- **Auth:** Microsoft Entra ID (configurable tenant) — organization employees only
- **Backend:** Python FastAPI, async Cosmos DB SDK, repository pattern
- **Database:** Azure Cosmos DB NoSQL (Serverless)
- **IaC:** Bicep (fully parameterized), GitHub Actions CI/CD
- **Hosting:** Azure App Service (B1, container) + Azure Static Web Apps (Free)
- **Repo Strategy:** Public product repo + private per-org deployment repos
- **Purpose:** Help NGO administrative staff track bank transactions (income, expenses) with categories, subcategories, and tags for proper financial oversight
- **Created:** 2026-04-10
- **Migrated to public repo:** 2026-04-13
