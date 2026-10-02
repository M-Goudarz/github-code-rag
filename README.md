# GitHub Code RAG

A production-oriented **Retrieval-Augmented Generation (RAG)** system for understanding and answering questions about GitHub repositories.

Generic document RAG treats text as an undifferentiated stream of tokens. Software repositories are not documents: they are structured, symbol-dense, and full of cross-file references that make naive fixed-size splitting and pure semantic search unreliable. `github-code-rag` is designed specifically for software repositories, with planned support for code-aware chunking, hybrid retrieval, precise line-level citations, and benchmark-driven evaluation.

> **Status:** 🚧 Initial foundation stage — the core RAG pipeline is not implemented yet.

---

## Overview

The intended workflow:

```text
GitHub repository
  → ingestion
  → parsing / filtering
  → code-aware chunking
  → embeddings
  → PostgreSQL + pgvector
  → vector + keyword retrieval
  → reranking
  → context building
  → LLM
  → grounded answer + citations
```

The eventual system should be able to answer questions such as:

- Where is authentication implemented?
- How does the caching system work?
- What happens when a user registers?
- Which files are responsible for database access?
- How does a request flow from an API endpoint to the database?

Answers are intended to contain precise citations such as:

```text
app/auth/service.py:L42-L67
```

together with stable GitHub permalinks pinned to the indexed commit SHA.

Two principles apply from the first line of ingestion code:

- Repository code is treated as **untrusted input**.
- Repository code is **never executed**.

---

## Goals

- Code-aware retrieval that understands repository structure and symbols
- Structural / AST-aware chunking, with recursive chunking as a baseline and fallback
- Hybrid retrieval combining vector and keyword search using Reciprocal Rank Fusion (RRF)
- Optional reranking of retrieved candidates
- Precise file/line citations pinned to a commit SHA
- Benchmark-driven development, so retrieval decisions are measured rather than assumed

---

## Architecture

The following diagram is the **planned** end-to-end architecture. Only the API shell and configuration layer exist today.

```text
                    GitHub Repository
                           │
                           ▼
                      Ingestion
                           │
                           ▼
                 File Filtering / Parsing
                           │
                           ▼
                   Code-aware Chunking
                           │
                           ▼
                      Embeddings
                           │
                           ▼
                  PostgreSQL + pgvector
                           │
                 ┌─────────┴─────────┐
                 ▼                   ▼
           Vector Search        Keyword Search
                 │                   │
                 └─────────┬─────────┘
                           ▼
                    Hybrid Retrieval
                         (RRF)
                           │
                           ▼
                       Reranker
                           │
                           ▼
                    Context Builder
                           │
                           ▼
                           LLM
                           │
                           ▼
                 Answer + Citations
```

Evaluation is a separate package that connects to the pipeline rather than living inside it:

```text
evaluation/
    │
    ├── datasets/      Fixed questions + expected evidence
    ├── runner.py      Run a dataset against one configuration
    ├── metrics.py     Retrieval and citation metrics
    └── report.py      Compare configurations
```

---

## Planned Retrieval Pipeline

The system is intentionally designed to *compare* retrieval configurations instead of assuming one strategy is superior. Candidate configurations under evaluation will include:

```text
Recursive Chunking
        +
Vector Search

AST Chunking
        +
Vector Search

AST Chunking
        +
Hybrid Search

AST Chunking
        +
Hybrid Search
        +
Reranking
```

Each configuration will be measured under the same datasets and, as far as possible, the same experimental conditions.

---

## Evaluation & Benchmarking

Benchmarking is one of this project's main differentiators, not an afterthought.

- **Evaluation** measures how well a single configuration performs.
- **A benchmark** compares multiple configurations under controlled conditions.

The project will use fixed repositories, fixed commits, fixed questions, and consistent evaluation conditions wherever possible. LLM-generated questions may assist dataset creation, but benchmark questions should be reviewed rather than blindly generated — an unreviewed dataset produces numbers that look rigorous and mean nothing.

**Planned retrieval metrics**

- Recall@K
- Precision@K
- MRR
- File-level retrieval accuracy
- Chunk-level retrieval accuracy
- Line-range overlap

**Planned citation metrics**

- Citation correctness
- Citation range overlap
- Citation coverage
- Source-grounded answer rate

**Planned generation metrics**

- Faithfulness / groundedness
- Answer relevance
- Appropriate abstention when evidence is insufficient

**Planned system metrics**

- End-to-end latency
- Retrieval latency
- Generation latency
- Token usage
- Estimated cost

> No benchmark results are claimed until the corresponding pipeline and evaluation datasets are implemented.

---

## Data Model

The planned logical hierarchy:

```text
Repository
    │
    └── Snapshot
           │
           └── Document
                  │
                  └── Chunk
```

A **Snapshot** represents a specific Git commit SHA. This is what makes indexing reproducible and citations stable: a line range only means something relative to a commit.

Example of the information a citation must carry:

```text
repository: owner/project
commit: 8f31c2...
file: app/auth/service.py
lines: 42-67
```

From this, a stable GitHub source reference can be constructed. **None of these models exist yet** — there is no database layer in the current implementation.

---

## Project Structure

```text
github-code-rag/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── health.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   └── README.md
│   │
│   ├── ingestion/
│   │   ├── __init__.py
│   │   └── README.md
│   │
│   ├── retrieval/
│   │   ├── __init__.py
│   │   └── README.md
│   │
│   ├── generation/
│   │   ├── __init__.py
│   │   └── README.md
│   │
│   └── citations/
│       ├── __init__.py
│       └── README.md
│
├── evaluation/
│   ├── __init__.py
│   ├── datasets/
│   │   └── .gitkeep
│   ├── metrics.py
│   ├── runner.py
│   └── report.py
│
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   └── __init__.py
│   ├── integration/
│   │   └── __init__.py
│   └── api/
│       ├── __init__.py
│       └── test_health.py
│
├── scripts/
│   └── README.md
│
├── data/
│   └── .gitkeep
│
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── README.md
└── uv.lock
```

**Currently implemented**

- `app/main.py` — FastAPI application factory and app instance
- `app/api/v1/health.py` — versioned health endpoint
- `app/core/config.py` — environment-driven settings
- `tests/` — test suite with unit, integration, and API groupings
- `pyproject.toml`, `uv.lock`, `Dockerfile`, `docker-compose.yml`, `.env.example`, `.gitignore`

**Planned / placeholder layers** (each contains only a `README.md` describing its future responsibility)

- `app/database/` — PostgreSQL + pgvector schema, sessions, persistence
- `app/ingestion/` — repository loading, file filtering, parsing, chunking
- `app/retrieval/` — vector and keyword search, hybrid fusion, reranking, context building
- `app/generation/` — LLM answer generation and conversations
- `app/citations/` — line-range citations and GitHub permalinks
- `scripts/` — small operational and developer helpers

**Evaluation**

- `evaluation/` exists as a first-class package, but currently contains only the skeleton: module-level documentation, an empty `datasets/` directory, and no metrics, runner, or report logic. It is not a working benchmark system.

---

## Technology Stack

### Current

- Python 3.12+
- FastAPI
- Pydantic / Pydantic Settings
- uv
- Pytest
- Ruff

### Planned

- PostgreSQL + pgvector
- SQLAlchemy
- Alembic
- AST / tree-based parsing
- Embedding models
- Keyword search
- Hybrid retrieval (RRF)
- Reranking
- LLM generation
- Redis for background processing
- Dockerized deployment

None of the planned technologies are integrated yet. Dependencies are added only when a feature that needs them is actually being implemented.

Frameworks such as LangChain and LlamaIndex are intentionally **not** part of the core architecture. If a concrete future requirement justifies one, it will be introduced deliberately and evaluated against the simpler alternative.

---

## Security Principles

These are design constraints for the ingestion and indexing layers (not yet implemented):

- Repository content is untrusted input.
- Repository code is never executed.
- Sensitive and unsafe files (secrets, keys, credentials, local environment files) must be filtered out before indexing.
- Binary and unsuitable files must be excluded.
- Repository size and per-file size limits must be applied.
- Secrets and local `.env` files must never be indexed or committed.
- Ingestion and execution remain separate concerns — the system reads code, it does not run it.

Current repository-level protections: `.env` is gitignored, `.env.example` is committed, and no repository content is fetched or executed at all yet.

---

## Current Status

### Implemented

- FastAPI application (`app.main:app`)
- API versioning structure (`/api/v1`)
- `GET /api/v1/health`
- Pydantic-based configuration (`app.core.config.Settings`)
- `.env` configuration support
- Python packaging and dependency management with `uv`
- Ruff linting and formatting configuration
- Pytest configuration
- Unit, integration, and API test directory structure
- Evaluation module skeleton
- Initial project architecture and layer documentation

### Not Implemented Yet

- PostgreSQL
- pgvector
- Repository ingestion
- File filtering
- Code parsing
- AST-aware chunking
- Recursive chunking
- Embeddings
- Keyword search
- Vector search
- Hybrid retrieval
- Reranking
- LLM generation
- Line-level citation generation
- Conversations
- Benchmark datasets
- Benchmark execution

---

## Roadmap

### Phase 1 — Foundation

- [x] Project structure
- [x] FastAPI application
- [x] Configuration
- [x] Testing and linting
- [ ] PostgreSQL + pgvector
- [ ] SQLAlchemy models
- [ ] Alembic migrations

### Phase 2 — Repository Ingestion

- [ ] GitHub repository acquisition
- [ ] Repository filtering
- [ ] File metadata extraction
- [ ] Recursive chunking baseline
- [ ] Incremental indexing using file hashes

### Phase 3 — First RAG Pipeline

- [ ] Embeddings
- [ ] Vector search
- [ ] Context builder
- [ ] LLM generation
- [ ] Basic line-level citations

### Phase 4 — Evaluation

- [ ] Fixed benchmark repositories
- [ ] Retrieval evaluation dataset
- [ ] Recall@K / Precision@K / MRR
- [ ] Citation accuracy
- [ ] Initial benchmark report

### Phase 5 — Advanced Retrieval

- [ ] AST-aware chunking
- [ ] Keyword search
- [ ] Hybrid retrieval with RRF
- [ ] Reranking
- [ ] Benchmark comparison

### Phase 6 — Production Features

- [ ] Repository snapshots
- [ ] Conversation history
- [ ] Streaming responses
- [ ] Background ingestion
- [ ] Observability
- [ ] Citation verification
- [ ] Dockerized deployment

---

## Getting Started

### Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Docker (optional, for the container image)

### Install

```bash
uv sync
```

### Run API

```bash
uv run uvicorn app.main:app --reload
```

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:

```json
{
  "status": "ok"
}
```

### Tests and Lint

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

### Configuration

Settings are read from environment variables, loaded from a `.env` file if present. `.env.example` documents the currently supported keys:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

`.env` is gitignored and must never be committed. Do not place secrets that are shared or committed into it — no real `.env` is provided in the repository.

### Docker

```bash
docker compose up --build
```

The Compose file currently defines the API service only. Database and cache services will be added when the components they serve actually exist.

---

## Development Philosophy

1. **Implement incrementally.** Each phase adds one capability, with tests, and stays working.
2. **Measure before optimizing.** Retrieval changes are justified by benchmark numbers, not intuition.
3. **Prefer simple architecture.** Fewer moving parts, clearer data flow, independently testable components.
4. **Preserve source provenance.** Every retrieved chunk must be traceable to a file, a line range, and a commit.
5. **Treat repositories as untrusted input.** Read and parse code; never run it.
6. **Keep experiments reproducible.** Fixed datasets, pinned commits, and recorded configurations so results can be re-run and compared.

---

## License

License information will be added when the project reaches its initial public release.