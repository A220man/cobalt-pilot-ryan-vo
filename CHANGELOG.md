# Changelog

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-10-21

### Added
- Initial release of Cobalt Pilot
- FastAPI backend with plugin discovery API
- React + TypeScript + Vite frontend
- Plugin listing with search, filter, and pagination
- Plugin detail view with skills, commands, connectors, and README tabs
- Skill stability filtering (experimental/stable/deprecated)
- Sync from reference repository (anthropics/knowledge-work-plugins)
- SQLite persistent storage with SQLAlchemy
- Docker Compose with backend, frontend, and Keycloak
- Keycloak realm configuration with viewer/operator/admin roles
- Backend tests (12+ meaningful tests)
- Frontend tests (3+ meaningful tests)
- CI/CD workflow with GitHub Actions

### AI/ML Features
- Plugin discovery for AI/ML developer tools (bio-research, data, etc.)
- Structured access to skills with stability lifecycle
- Foundation for LLM adapter framework (planned)