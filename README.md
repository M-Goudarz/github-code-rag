# GitHub Code RAG

## Overview

`github-code-rag` is a production-oriented Retrieval-Augmented Generation
(RAG) system designed to understand and answer questions about GitHub
repositories.

It ingests a repository, keeps only relevant and safe-to-process files,
splits them into code-aware chunks, indexes those chunks for both vector and
keyword search, and answers questions with grounded answers that cite exact
files and line ranges via stable GitHub permalinks.

## Goals

- Code-aware retrieval that understands repository structure
- Structural / AST-aware chunking, plus a recursive fallback
- Hybrid retrieval: vector search combined with keyword search (RRF)
- Optional reranking of retrieved candidates
- Precise, line-level citations pinned to a commit SHA
- Benchmark-driven evaluation of every RAG configuration change

## Architecture

```text
GitHub Repository
        ↓
   Ingestion
        ↓
 Parsing / Chunking
        ↓
    Embeddings
        ↓
 PostgreSQL + pgvector
        ↓
 Vector + Keyword Retrieval
        ↓
      Reranker
        ↓
  Context Builder
        ↓
       LLM
        ↓
Answer + Citations
```

The evaluation system is a separate package that connects to the pipeline:

```text
 evaluation/
      │
      ├── datasets/   fixed questions + expected evidence
      ├── runner.py   runs a dataset against one RAG configuration
      ├── metrics.py  Recall@K, Precision@K, MRR, citation accuracy, ...
      └── report.py   compares configurations
```

## Project Structure

```text
app/
  api/v1/        versioned HTTP routers (health only for now)
  core/          application configuration
  database/      PostgreSQL + pgvector layer (planned)
  ingestion/     repository loading, filtering, parsing, chunking (planned)
  retrieval/     vector + keyword retrieval, hybrid fusion, reranking (planned)
  generation/    LLM answer generation and conversations (planned)
  citations/     file/line citations and GitHub permalinks (planned)
evaluation/      first-class benchmarking: datasets, metrics, runner, report
tests/           unit, integration, and API tests
scripts/         small operational and developer helpers (planned)
data/            local scratch data (gitignored except .gitkeep)
```

## Current Status

The project is at the **initial foundation stage**. It currently contains
only:

- a FastAPI application with a `GET /api/v1/health` endpoint
- `pydantic-settings` based configuration loaded from `.env`
- a minimal test, lint, and packaging setup
- the directory scaffold and READMEs for the future layers

None of the advanced RAG features are implemented yet. PostgreSQL,
pgvector, embeddings, retrieval, reranking, and LLM generation do **not**
exist yet, and no benchmark results have been produced.

## Development Principles

- Incremental implementation: each phase adds one capability with tests
- Benchmark-driven decisions: no retrieval change without measurement
- No unnecessary frameworks; dependencies are added only with a concrete need
- Repository code is treated as **untrusted input**
- Repository code is **never executed**, only read, filtered, and parsed

## Getting Started

```bash
uv sync
uv run uvicorn app.main:app --reload
curl http://localhost:8000/api/v1/health
```

Configuration is documented in `.env.example`. Copy it to `.env` to
customise local settings; `.env` is gitignored.

## License

See [LICENSE](LICENSE).