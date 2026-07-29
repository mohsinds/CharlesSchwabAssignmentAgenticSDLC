# Scenarios

## 1. Greenfield

**Input:** `scenarios/greenfield/requirement.md`  
**Path:** classify → requirement → design → plans → implementation → test → docs → release_review  
**Shows:** full decomposition, code generation, layered gates, artifact output.

## 2. Brownfield

**Input:** `scenarios/brownfield/change_request.md` + `seed_repo/`  
**Path:** classify → codebase_ingest → requirement → …  
**Shows:** ingest/retrieval, impact-aware design citations.

## 3. Ambiguous

**Input:** `scenarios/ambiguous/requirement.md`  
**Path:** classify → clarify (HITL) → requirement → …  
**Shows:** controlled autonomy, human clarification, replan into a concrete build.

Walk each scenario from the UI (Home → scenario chip → Start) in **Replay** for offline demos or **Live** with LiteLLM configured.
