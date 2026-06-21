# Multi-Agent AI Research & Automated Presentation Generator

Orchestrates three specialized agents — **Researcher**, **Analyst**, **Designer** —
via LangGraph to turn a topic into a downloadable, professionally designed `.pptx`.

## Phase 1 status (this delivery)
- ✅ Folder structure & config (`Settings`, `.env`, logging)
- ✅ LLM router (GPT-4o / Claude 3.5 Sonnet / Llama-3.1-on-Groq, swappable per agent via env vars)
- ✅ LangGraph state schema (`ResearchState`, `SourceDocument`, `SlideContent`, `AgentLogEvent`)
- ✅ Agent 1 (Researcher): query expansion → Tavily/Serper search → deep scrape → summary
- ✅ Agent 2 (Analyst): fact-checked, typed, slide-by-slide JSON outline
- ✅ Agent 3 (Designer): wired into the graph, with a minimal but real `python-pptx` output
- ✅ FastAPI app with synchronous `/api/v1/generate` + `/api/v1/download/{filename}` endpoints
- ✅ Dockerfile + docker-compose for local/dev deployment

## Coming in later phases
- **Phase 2**: Full design engine — corporate layouts, color palettes, typography system,
  metric callouts, comparison tables, anti-overlap text-wrapping rules.
- **Phase 3**: WebSocket endpoint streaming `AgentLogEvent`s live as the graph runs.
- **Phase 4**: Next.js (TS/Tailwind/Shadcn) frontend with a live agent terminal, plus
  cloud deployment configs (Render/Vercel/AWS/GCP).

## Quickstart

```bash
cd backend
cp .env.example .env        # then fill in your API keys
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for interactive Swagger UI.

### Try it
```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "The rise of small modular nuclear reactors", "max_sources": 6, "max_slides": 8}'
```

### Docker
```bash
docker compose up --build
```

## Required API keys (`backend/.env`)
| Key | Purpose |
|---|---|
| `OPENAI_API_KEY` | GPT-4o (Designer agent, by default) |
| `ANTHROPIC_API_KEY` | Claude 3.5 Sonnet (Analyst agent, by default) |
| `GROQ_API_KEY` | Llama 3.1 70B (Researcher agent, by default) |
| `TAVILY_API_KEY` | Primary web search |
| `SERPER_API_KEY` | Fallback web search |

Swap which provider powers which agent purely via `.env` — no code changes
(`DESIGNER_MODEL_PROVIDER`, `ANALYST_MODEL_PROVIDER`, `RESEARCHER_MODEL_PROVIDER`).
