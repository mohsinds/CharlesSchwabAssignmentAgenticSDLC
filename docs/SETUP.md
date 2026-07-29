# Setup

## Prerequisites

- Python 3.11+  
- Node 20+  
- Docker / Docker Compose  
- Optional: `OPENAI_API_KEY` (or Anthropic) for live agent runs via LiteLLM  

## Configure

```bash
cp .env.example .env
# Edit LITELLM_* and optional OPENAI_API_KEY / ANTHROPIC_API_KEY
```

Point `LITELLM_BASE_URL` at the bundled proxy (`http://localhost:4000`) or a corporate LiteLLM endpoint. Agents never hold upstream provider keys.

## Bring up stack

```bash
make install
make seed
make up
```

## Dev without full compose

```bash
pip install -e ".[dev]"
uvicorn services.api.main:app --reload --port 8000
cd frontend && npm install && npm run dev
```

The API uses the **local runner** when Temporal is unreachable — useful for UI demos.

## Demo scripts

```bash
make demo-greenfield
make demo-brownfield
make demo-ambiguous
```
