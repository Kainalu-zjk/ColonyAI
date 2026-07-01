<p align="center">
  <img src="./frontend/src/assets/icon.png" alt="Colony AI Logo" width="120"/>
</p>
<h1 align="center">🧬 Colony AI</h1>
<p align="center">
  <b>Multi-Agent Collaboration Platform</b><br>
  <i>Orchestrate AI agents to automate complex end-to-end workflows.</i>
</p>

<p align="center">
  <a href="#-architecture">Architecture</a> •
  <a href="#-features">Features</a> •
  <a href="#-getting-started">Getting Started</a>
</p>

---

## Overview

**Colony AI** orchestrates multiple specialized AI Agents (Coordinator, Modeler, Coder, Writer) to collaborate on complex tasks end-to-end. Originally focused on mathematical modeling competitions, designed to be extensible to any multi-step AI workflow.

### Differences from Upstream

| Feature | MathModelAgent | Colony AI |
|---------|---------------|-----------|
| Branding | MathModelAgent | **Colony AI** |
| i18n | Chinese only | **Full zh/en** |
| Templates | 2 | **4 (China/MCM/Huashu/Huawei)** |
| Citations | Empty footnotes | **OpenAlex -> APA/GB7714** |
| UI | Original | **Rebranded + Task History** |
| CLI | None | **Interactive/Single/Headless** |
| Redis | Required | **Optional (file fallback)** |
| Retry Guard | Infinite loop | **10 max + error propagation** |

---

## Architecture

```
Input Problem -> CoordinatorAgent (parse)
              -> ModelerAgent (model design)
              -> CoderAgent (code + Jupyter execution)
              -> WriterAgent (paper + citations)
              -> UserOutput (merge -> res.md)
```

| Agent | Role |
|-------|------|
| **Coordinator** | Parse and distribute tasks |
| **Modeler** | Model selection and solution design |
| **Coder** | Code generation, execution, error recovery |
| **Writer** | Paper writing and citation management |

---

## Features

- **4 Specialized Agents** with independent LLM configuration
- **LLM Agnostic** -- OpenAI / Anthropic / any compatible API
- **Code Interpreter** -- Local Jupyter kernel or E2B sandbox
- **4 Paper Templates** -- China / MCM-ICM / Huashu / Huawei
- **Academic Citations** -- OpenAlex -> APA / GB7714 format
- **Bilingual** -- Full zh/en UI, prompts, and output
- **CLI** -- Interactive, single-file, and headless modes
- **WebSocket** -- Real-time updates (Redis or file-polling)

---

## Getting Started

### Prerequisites

- Python 3.11+, Node.js 18+, Redis (optional)

```bash
git clone https://github.com/Kainalu-zjk/ColonyAI.git
cd ColonyAI

# Backend
cd backend
pip install uv && uv sync
cp .env.example .env.dev
# Edit .env.dev -- set API keys and models
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (new terminal)
cd frontend
npm install -g pnpm && pnpm i
pnpm run dev
```

Open **http://localhost:5173**

### CLI

```bash
python -m app.main cli --mode interactive
python -m app.main cli --file problem.txt --template american --lang en
```

---

## License

Forked from [MathModelAgent](https://github.com/jihe520/MathModelAgent). Modifications provided under the same terms.

---

<p align="center"><sub>Colony AI -- Multi-Agent Collaboration, Amplified.</sub></p>
