# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Install all dependencies
uv sync

# Install with development tools (black, flake8, isort, mypy)
uv sync --group dev

# Add new dependencies
uv add package_name

# Environment variables required (.env file in root):
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### Running the Application
```bash
# Quick start using shell script
chmod +x run.sh
./run.sh

# Manual start (from root directory)
cd backend && uv run uvicorn app:app --reload --port 8000

# Application URLs:
# - Web Interface: http://localhost:8000
# - API Documentation: http://localhost:8000/docs
```

### Running Tests
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest backend/tests/test_vector_store.py

# Run single test function
uv run pytest backend/tests/test_vector_store.py::test_search_with_filters

# Run tests with markers
uv run pytest -m unit          # Only unit tests
uv run pytest -m integration   # Only integration tests
uv run pytest -m "not slow"    # Skip slow tests

# Run with verbose output
uv run pytest -v

# Run with coverage (if coverage is installed)
uv run pytest --cov=backend --cov-report=html
```

Available test markers: `unit`, `integration`, `api`, `slow`

### Code Quality Tools

**Format Script (Modifies Files)**
```bash
./scripts/format.sh
```
Automatically fixes: import ordering (isort), code style (Black), then reports: linting issues (flake8), type errors (mypy).

**Lint Script (Read-Only)**
```bash
./scripts/lint.sh
```
Verifies code quality without modifications. Exit code 0 = pass.

**Prerequisites:** `uv sync --group dev`

**Troubleshooting:** If scripts aren't executable: `chmod +x scripts/*.sh`

### Python Execution
Always use `uv run` to execute commands in the project's virtual environment:
```bash
uv run python script.py
uv run pytest
uv run black backend/
```

## Architecture Overview

RAG system for course materials using FastAPI backend, vanilla JS frontend, and tool-based AI search.

### Core Architecture Patterns

**Tool-Based Search (Non-deterministic):**
The system uses Anthropic's tool calling rather than always searching. The AI (`AIGenerator`) decides when to use search tools based on the query:
- General questions → AI answers directly without searching
- Course-specific questions → AI calls `search_course_content` or `get_course_outline` tools
- Multi-round capability: AI can call tools up to 2 times per query to gather comprehensive information
- Tools are registered with `ToolManager` and executed dynamically based on AI decisions

**Dual-Collection Vector Strategy:**
Two separate ChromaDB collections solve the partial name matching problem:
- `course_catalog` collection: Stores course titles as searchable vectors
  - Enables semantic matching: "Anthropic" → "Building Towards Computer Use with Anthropic"
  - Metadata includes: title, instructor, course_link, lesson_count, lessons_json
- `course_content` collection: Stores actual course content chunks
  - Each chunk has metadata: course_title, lesson_number, chunk_index
  - Search flow: resolve course name via catalog → filter content search by resolved title

This two-step approach allows flexible course name queries while maintaining precise content filtering.

**Document Processing Flow:**
Documents in `docs/` folder must follow this format:
```
Course Title: [title]
Course Link: [url]
Course Instructor: [name]

Lesson N: [lesson title]
Lesson Link: [url]
[lesson content...]
```

On startup (`app.py:startup_event`):
1. `DocumentProcessor` parses course metadata from first 3 lines
2. Extracts lessons by detecting "Lesson N:" markers
3. Chunks lesson content (800 chars, 100 char overlap, sentence-aware)
4. Adds context prefix to chunks: "Course [title] Lesson [N] content: [chunk]"
5. Stores course metadata in `course_catalog`, chunks in `course_content`

**Session-Based Conversation:**
`SessionManager` maintains conversation context (2 message pairs) in-memory for follow-up questions.
- Session ID generated on first query, returned to frontend
- Subsequent queries include session_id to maintain context
- History passed to AI for contextual responses

### Key Components

**RAGSystem (orchestrator):** Coordinates document loading, query processing, and response generation. Entry point for all RAG operations.

**VectorStore:** Manages ChromaDB with dual collections. Key method: `search(query, course_name, lesson_number)` handles name resolution and filtered search.

**AIGenerator:** Wraps Anthropic API with multi-round tool calling. System prompt instructs AI on tool usage and response formatting.

**CourseSearchTool/CourseOutlineTool:** Implement tool interface. `execute()` methods return formatted search results. Track sources for UI attribution.

**DocumentProcessor:** Parses structured course documents. Critical: `chunk_text()` uses sentence-aware splitting to avoid mid-sentence cuts.

### Component Interactions

Query flow: Frontend → FastAPI (`app.py`) → RAGSystem.query() → AIGenerator.generate_response() → [AI decides to search] → ToolManager.execute_tool() → CourseSearchTool.execute() → VectorStore.search() → [2-step: resolve course name, then search content] → Results formatted → AI synthesizes response → Frontend displays with sources.

### Configuration (backend/config.py)
- Chunk: 800 chars, 100 overlap
- Embedding: all-MiniLM-L6-v2 (384 dimensions)
- Search: top 5 results
- History: 2 exchanges
- Model: claude-sonnet-4-20250514
- ChromaDB: persists in backend/chroma_db/

### Development Notes

- Documents auto-load from `docs/` on startup (supports .txt, .pdf, .docx)
- Existing courses are skipped on subsequent startups (checks by title)
- FastAPI serves static frontend files from root path
- API endpoints under `/api/*` namespace
- Tests use fixtures from `conftest.py` for consistent mocking
- Frontend uses marked.js for markdown rendering of AI responses