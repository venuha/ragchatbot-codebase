# RAG Chatbot System - Architecture Diagram

## High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         Frontend Layer                                │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │  │
│  │  │  index.html  │  │  script.js   │  │   style.css  │              │  │
│  │  │              │  │              │  │              │              │  │
│  │  │ • UI Layout  │  │ • API Calls  │  │ • Styling    │              │  │
│  │  │ • Chat Box   │  │ • Session    │  │ • Theme      │              │  │
│  │  │ • Sources    │  │ • Markdown   │  │ • Responsive │              │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                   │                                          │
│                                   │ HTTP/REST                                │
│                                   ▼                                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            API LAYER (FastAPI)                               │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  app.py - FastAPI Application                                        │  │
│  │                                                                        │  │
│  │  Endpoints:                                                            │  │
│  │  • POST /api/query        - Process user queries                      │  │
│  │  • GET  /api/courses      - Get course statistics                     │  │
│  │  • POST /api/clear-session - Clear conversation history               │  │
│  │  • GET  /                 - Serve frontend static files               │  │
│  │                                                                        │  │
│  │  Startup Event:                                                        │  │
│  │  • Load documents from docs/ folder                                   │  │
│  │  • Initialize RAG system                                              │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                   │                                          │
│                                   ▼                                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        RAG SYSTEM ORCHESTRATOR                               │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  rag_system.py - RAGSystem Class                                      │  │
│  │                                                                        │  │
│  │  Main Methods:                                                         │  │
│  │  • add_course_document()   - Process single document                  │  │
│  │  • add_course_folder()     - Process all documents                    │  │
│  │  • query()                 - Handle user queries                      │  │
│  │  • get_course_analytics()  - Return course stats                      │  │
│  │                                                                        │  │
│  │  Coordinates all core components below ↓                              │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                   │                                          │
│          ┌────────────────────────┼────────────────────────┐                │
│          │                        │                        │                │
│          ▼                        ▼                        ▼                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           CORE COMPONENTS                                    │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │ DocumentProces. │  │  VectorStore    │  │    AIGenerator              │ │
│  │                 │  │                 │  │                             │ │
│  │ • Parse course  │  │ • ChromaDB      │  │ • Anthropic API             │ │
│  │ • Extract meta  │  │ • Embeddings    │  │ • Tool calling              │ │
│  │ • Chunk text    │  │ • Dual colls.   │  │ • Multi-round               │ │
│  │ • Add context   │  │ • Search        │  │ • Response gen              │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
│          │                     │                         │                  │
│          │                     │                         ▼                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │ SessionManager  │  │  ToolManager    │  │     Search Tools            │ │
│  │                 │  │                 │  │                             │ │
│  │ • Session mgmt  │  │ • Register      │  │ • CourseSearchTool          │ │
│  │ • History (2)   │  │ • Execute       │  │ • CourseOutlineTool         │ │
│  │ • Context       │  │ • Track sources │  │ • Tool definitions          │ │
│  │                 │  │                 │  │ • Result formatting         │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
│                              │                         │                    │
│                              └────────────┬────────────┘                    │
│                                           │                                 │
└───────────────────────────────────────────┼─────────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                         │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  ChromaDB (backend/chroma_db/)                                        │  │
│  │                                                                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │  │
│  │  │  Collection: course_catalog                                     │ │  │
│  │  │  Purpose: Semantic course name matching                         │ │  │
│  │  │                                                                  │ │  │
│  │  │  Documents: Course titles (vectorized)                          │ │  │
│  │  │  Metadata:                                                       │ │  │
│  │  │    • title          - Full course title                         │ │  │
│  │  │    • instructor     - Instructor name                           │ │  │
│  │  │    • course_link    - Course URL                                │ │  │
│  │  │    • lesson_count   - Number of lessons                         │ │  │
│  │  │    • lessons_json   - JSON list of lessons                      │ │  │
│  │  │                                                                  │ │  │
│  │  │  Use Case: "Anthropic" → finds "Building with Anthropic"       │ │  │
│  │  └─────────────────────────────────────────────────────────────────┘ │  │
│  │                                                                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │  │
│  │  │  Collection: course_content                                     │ │  │
│  │  │  Purpose: Store actual course material chunks                   │ │  │
│  │  │                                                                  │ │  │
│  │  │  Documents: Content chunks (vectorized with context prefix)    │ │  │
│  │  │  Metadata:                                                       │ │  │
│  │  │    • course_title   - Associated course                         │ │  │
│  │  │    • lesson_number  - Which lesson                              │ │  │
│  │  │    • lesson_title   - Lesson name                               │ │  │
│  │  │    • lesson_link    - Lesson URL                                │ │  │
│  │  │    • chunk_index    - Chunk position                            │ │  │
│  │  │                                                                  │ │  │
│  │  │  Use Case: Semantic search with course/lesson filtering        │ │  │
│  │  └─────────────────────────────────────────────────────────────────┘ │  │
│  │                                                                        │  │
│  │  Embedding Model: all-MiniLM-L6-v2 (384 dimensions)                  │  │
│  │  Persistence: Disk-based (survives restarts)                          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL SERVICES                                     │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Anthropic API (claude-sonnet-4-20250514)                            │  │
│  │                                                                        │  │
│  │  • Receives: User query + conversation history + tool definitions     │  │
│  │  • Decides: Whether to use tools or answer directly                   │  │
│  │  • Returns: Tool calls OR direct response                             │  │
│  │  • Multi-round: Can call tools up to 2 times per query                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         DOCUMENT INPUT                                       │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  docs/ folder                                                         │  │
│  │                                                                        │  │
│  │  Supported formats: .txt, .pdf, .docx                                 │  │
│  │                                                                        │  │
│  │  Required structure:                                                   │  │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │  │
│  │  │ Course Title: [Title]                                            │ │  │
│  │  │ Course Link: [URL]                                               │ │  │
│  │  │ Course Instructor: [Name]                                        │ │  │
│  │  │                                                                   │ │  │
│  │  │ Lesson 1: [Lesson Title]                                         │ │  │
│  │  │ Lesson Link: [URL]                                               │ │  │
│  │  │ [Content...]                                                      │ │  │
│  │  │                                                                   │ │  │
│  │  │ Lesson 2: [Lesson Title]                                         │ │  │
│  │  │ Lesson Link: [URL]                                               │ │  │
│  │  │ [Content...]                                                      │ │  │
│  │  └──────────────────────────────────────────────────────────────────┘ │  │
│  │                                                                        │  │
│  │  Processing: Automatic on startup, skips existing courses             │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Query Flow Sequence

```
┌─────────┐
│  User   │
└────┬────┘
     │ 1. Types question
     ▼
┌─────────────────┐
│   Frontend      │
│   (script.js)   │
└────┬────────────┘
     │ 2. POST /api/query
     │    { query: "...", session_id: "..." }
     ▼
┌─────────────────┐
│  FastAPI        │
│  (app.py)       │
└────┬────────────┘
     │ 3. rag_system.query()
     ▼
┌─────────────────────────┐
│  RAGSystem              │
│  (rag_system.py)        │
└────┬────────────────────┘
     │ 4. Get conversation history
     ▼
┌─────────────────┐
│ SessionManager  │
└────┬────────────┘
     │ 5. Returns last 2 exchanges
     ▼
┌─────────────────────────┐
│  RAGSystem              │
└────┬────────────────────┘
     │ 6. ai_generator.generate_response()
     │    (with tool definitions)
     ▼
┌─────────────────────────┐
│  AIGenerator            │
│  (ai_generator.py)      │
└────┬────────────────────┘
     │ 7. Call Anthropic API
     │    (query + history + tools)
     ▼
┌─────────────────────────┐
│  Anthropic API          │
│  (Claude Sonnet 4)      │
└────┬────────────────────┘
     │ 8. Decision Point:
     │    • General Q? → Answer directly
     │    • Course Q? → Tool call
     │
     │ If tool call needed:
     ▼
┌─────────────────────────┐
│  AIGenerator            │
└────┬────────────────────┘
     │ 9. tool_manager.execute_tool()
     ▼
┌─────────────────────────┐
│  ToolManager            │
│  (search_tools.py)      │
└────┬────────────────────┘
     │ 10. Route to correct tool
     │     (CourseSearchTool or CourseOutlineTool)
     ▼
┌─────────────────────────┐
│  CourseSearchTool       │
└────┬────────────────────┘
     │ 11. vector_store.search()
     ▼
┌─────────────────────────────────────┐
│  VectorStore                        │
│  (vector_store.py)                  │
└────┬────────────────────────────────┘
     │ 12. Two-step search:
     │
     │ Step 1: Resolve course name
     ▼
┌─────────────────────────────────────┐
│  ChromaDB: course_catalog           │
│  Search for: course_name            │
│  Returns: Exact course title        │
└────┬────────────────────────────────┘
     │ 13. Found: "Building with Anthropic"
     │
     │ Step 2: Search content
     ▼
┌─────────────────────────────────────┐
│  ChromaDB: course_content           │
│  Search for: query                  │
│  Filter by: course_title + lesson   │
│  Returns: Top 5 chunks              │
└────┬────────────────────────────────┘
     │ 14. Return SearchResults
     ▼
┌─────────────────────────┐
│  CourseSearchTool       │
└────┬────────────────────┘
     │ 15. Format results + track sources
     ▼
┌─────────────────────────┐
│  ToolManager            │
└────┬────────────────────┘
     │ 16. Return formatted results
     ▼
┌─────────────────────────┐
│  AIGenerator            │
└────┬────────────────────┘
     │ 17. Send results back to Anthropic
     │     (AI can call tools again if needed)
     ▼
┌─────────────────────────┐
│  Anthropic API          │
│  (Claude Sonnet 4)      │
└────┬────────────────────┘
     │ 18. Synthesize final response
     │     using search results
     ▼
┌─────────────────────────┐
│  AIGenerator            │
└────┬────────────────────┘
     │ 19. Return response text
     ▼
┌─────────────────────────┐
│  RAGSystem              │
└────┬────────────────────┘
     │ 20. Get sources from tool_manager
     │ 21. Update session history
     ▼
┌─────────────────┐
│ SessionManager  │
└────┬────────────┘
     │ 22. Store exchange
     ▼
┌─────────────────────────┐
│  RAGSystem              │
└────┬────────────────────┘
     │ 23. Return (answer, sources, links)
     ▼
┌─────────────────┐
│  FastAPI        │
│  (app.py)       │
└────┬────────────┘
     │ 24. JSON response
     │    { answer, sources, source_links, session_id }
     ▼
┌─────────────────┐
│   Frontend      │
│   (script.js)   │
└────┬────────────┘
     │ 25. Render markdown response
     │ 26. Display source links
     ▼
┌─────────┐
│  User   │
└─────────┘
```

## Component Details

### Frontend (Vanilla JavaScript)
- **Files**: `index.html`, `script.js`, `style.css`
- **Libraries**: marked.js (markdown rendering)
- **Features**:
  - Chat interface with message history
  - Session management
  - Source attribution with clickable links
  - Real-time typing indicators
  - Responsive design

### API Layer (FastAPI)
- **File**: `backend/app.py`
- **Port**: 8000
- **Features**:
  - CORS enabled for development
  - Static file serving for frontend
  - Pydantic models for validation
  - Startup event for document loading
  - Error handling with HTTP exceptions

### RAG System (Orchestrator)
- **File**: `backend/rag_system.py`
- **Role**: Central coordinator for all RAG operations
- **Responsibilities**:
  - Initialize all components
  - Route queries through pipeline
  - Manage document ingestion
  - Coordinate tool execution

### AI Generator
- **File**: `backend/ai_generator.py`
- **Model**: Claude Sonnet 4 (claude-sonnet-4-20250514)
- **Features**:
  - Tool calling capability
  - Multi-round conversations (up to 2 tool calls)
  - Conversation history management
  - System prompt with instructions

### Vector Store (ChromaDB)
- **File**: `backend/vector_store.py`
- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Collections**:
  1. **course_catalog**: Course metadata for name resolution
  2. **course_content**: Actual lesson chunks
- **Features**:
  - Dual-collection search strategy
  - Semantic course name matching
  - Filtered search by course/lesson
  - Persistent storage

### Document Processor
- **File**: `backend/document_processor.py`
- **Features**:
  - Structured document parsing
  - Metadata extraction (first 3 lines)
  - Lesson detection (regex-based)
  - Smart chunking (800 chars, 100 overlap, sentence-aware)
  - Context prefix addition

### Search Tools
- **File**: `backend/search_tools.py`
- **Tools**:
  1. **CourseSearchTool**: Search course content
  2. **CourseOutlineTool**: Get course structure
- **Features**:
  - Tool interface implementation
  - Anthropic tool definition format
  - Source tracking
  - Result formatting

### Tool Manager
- **File**: `backend/search_tools.py`
- **Responsibilities**:
  - Register tools
  - Execute tool calls
  - Track sources and links
  - Manage tool lifecycle

### Session Manager
- **File**: `backend/session_manager.py`
- **Features**:
  - In-memory session storage
  - UUID-based session IDs
  - Conversation history (2 exchanges max)
  - Session clearing

## Configuration

### Environment Variables (.env)
```
ANTHROPIC_API_KEY=your_key_here
```

### Config Settings (backend/config.py)
```python
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
MAX_RESULTS = 5
MAX_HISTORY = 2  # conversation exchanges
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
CHROMA_PATH = "backend/chroma_db/"
```

## Key Design Patterns

### 1. Tool-Based Search (Non-Deterministic)
- AI decides when to search vs. answer directly
- Flexible, context-aware behavior
- Reduces unnecessary searches for general questions

### 2. Dual-Collection Strategy
- Solves partial name matching problem
- Separates metadata from content
- Enables precise filtering after name resolution

### 3. Context-Aware Chunking
- Adds course/lesson prefix to chunks
- Improves embedding quality
- Preserves context in search results

### 4. Session-Based Conversations
- Maintains conversation flow
- Enables follow-up questions
- Limited history prevents context bloat

### 5. Source Attribution
- Tracks all tool executions
- Returns lesson links to user
- Enables verification and exploration

## Data Flow Summary

1. **Ingestion**: docs/ → DocumentProcessor → VectorStore (2 collections)
2. **Query**: User → FastAPI → RAGSystem → AIGenerator → Anthropic
3. **Search**: Anthropic → ToolManager → SearchTool → VectorStore (2-step)
4. **Response**: Anthropic → AIGenerator → RAGSystem → FastAPI → User
5. **Session**: SessionManager maintains context across queries

## Technology Stack

- **Backend**: FastAPI, Python 3.11+
- **Vector DB**: ChromaDB (persistent)
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **AI**: Anthropic Claude API (Sonnet 4)
- **Frontend**: Vanilla JavaScript, HTML, CSS
- **Markdown**: marked.js
- **Package Manager**: uv (not pip)
- **Testing**: pytest

## Deployment

- **Development**: `./run.sh` or `cd backend && uv run uvicorn app:app --reload`
- **Production**: Should use proper ASGI server (gunicorn + uvicorn worker)
- **Port**: 8000 (configurable)
- **URLs**:
  - Web: http://localhost:8000
  - API Docs: http://localhost:8000/docs
