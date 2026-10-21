# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

skeleton-and-core-workflow

## Roadmap

### skeleton-and-core-workflow — FastAPI/React skeleton with plugin discovery workflow

Status: done

Acceptance:
- Backend FastAPI app runs with /health endpoint
- Frontend React app builds and serves
- Plugin discovery API returns structured plugin data from reference repo
- Frontend displays plugin list with search/filter
- Docker compose runs backend, frontend, and Keycloak
- Backend tests pass (>=12 meaningful tests)
- Frontend tests pass (>=3 meaningful tests)
- CI workflow configured

Implementation: `backend/app/main.py`, `backend/app/api/plugins.py`, `backend/app/services/plugin_sync.py`, `backend/app/services/plugin_query.py`, `backend/app/models/plugin.py`, `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/app/core/security.py`, `frontend/src/App.tsx`, `frontend/src/main.tsx`, `frontend/src/pages/PluginListPage.tsx`, `frontend/src/pages/PluginDetailPage.tsx`, `frontend/src/components/PluginCard.tsx`, `frontend/src/components/SearchInput.tsx`, `frontend/src/components/StabilityBadge.tsx`, `frontend/src/components/SyncButton.tsx`, `frontend/src/components/Button.tsx`, `frontend/src/components/Layout.tsx`, `frontend/src/api/client.ts`, `frontend/src/hooks/usePlugins.ts`, `frontend/src/types/index.ts`, `compose.yaml`, `backend/Dockerfile`, `frontend/Dockerfile`, `.github/workflows/ci.yml`

Tests: `backend/tests/test_health.py`, `backend/tests/test_plugins_api.py`, `backend/tests/test_models.py`, `backend/tests/test_services.py`, `backend/tests/test_security.py`, `backend/tests/test_config.py`, `frontend/src/__tests__/utils.test.tsx`, `frontend/src/__tests__/components.test.tsx`, `frontend/src/__tests__/hooks.test.tsx`

### plugin-detail-workflow — Plugin detail view with skills/commands/connectors

Status: done

Acceptance:
- API endpoint for plugin detail with skills, commands, connectors
- Frontend plugin detail page with tabs for skills/commands/connectors
- Skill markdown rendering with frontmatter parsing

Implementation: `backend/app/api/plugins.py (get_plugin endpoint)`, `frontend/src/pages/PluginDetailPage.tsx`

Tests: `backend/tests/test_plugins_api.py::test_get_plugin_detail`, `backend/tests/test_plugins_api.py::test_list_plugin_skills`, `backend/tests/test_plugins_api.py::test_list_plugin_skills_filter_stability`, `backend/tests/test_plugins_api.py::test_get_skill_detail`

### skill-stability-filtering — Skill stability lifecycle filtering (experimental/stable/deprecated)

Status: done

Acceptance:
- Stability frontmatter parsed from SKILL.md files
- API filter by stability level
- Frontend stability badge and filter UI

Implementation: `backend/app/models/plugin.py (StabilityLevel enum)`, `backend/app/services/plugin_sync.py (_parse_markdown_frontmatter)`, `backend/app/services/plugin_query.py (list_skills with stability filter)`, `frontend/src/components/StabilityBadge.tsx`, `frontend/src/pages/PluginDetailPage.tsx (stability filter)`

Tests: `backend/tests/test_models.py::test_skill_model_with_stability`, `backend/tests/test_services.py::test_plugin_query_service_list_skills_with_stability_filter`, `backend/tests/test_services.py::test_plugin_query_service_get_stability_counts`, `backend/tests/test_plugins_api.py::test_list_plugin_skills_filter_stability`, `frontend/src/__tests__/components.test.tsx (StabilityBadge tests)`

### auth-oidc-keycloak — OIDC authentication with Keycloak

Status: planned

Acceptance:
- Backend OIDC validation with PKCE
- Frontend login/logout flow
- Protected API endpoints
- Role-based access (viewer/operator/admin)

### llm-adapter-framework — LLM adapter framework for AI/ML features

Status: planned

Acceptance:
- OpenAI-compatible, Anthropic, Gemini, Ollama adapters
- Configurable provider/model/endpoint
- Opt-in LLM explanations labeled advisory

