# 🎓 University Student Information & Guidance Assistant

A production-ready **RAG (Retrieval-Augmented Generation) system** designed specifically for university student queries. Features hybrid retrieval (BM25 + FAISS), semantic caching, multi-turn conversations with memory, and automatic document ingestion.

## 🌟 Key Features

### Core Capabilities
- **Hybrid Retrieval**: Combines BM25 keyword search + FAISS semantic search
- **Cross-Encoder Reranking**: Ensures most relevant results using `cross-encoder/ms-marco-MiniLM-L6-v2`
- **Two-Tier Caching**:
  - Traditional Redis caching (24hr TTL)
  - Semantic caching with embedding similarity (>0.85 threshold)
- **Conversation Memory**: Persistent chat history with Redis backend
- **Entity Memory**: Tracks student profiles (program, year, courses, topics)
- **Auto-Ingestion**: Watchdog monitors `/data/` for new PDF/DOCX/TXT/MD files
- **Safety Guardrails**: Input validation, output structure enforcement, citation verification
- **Section-Based Chunking**: Preserves document hierarchy (300-800 token chunks)

### Tech Stack
- **LangChain** (latest) with Ollama + Mistral
- **FAISS** for vector search
- **BM25** for keyword retrieval
- **Redis** for caching + memory
- **FastAPI** backend
- **Streamlit** frontend
- **Watchdog** for file monitoring

---

## 📋 Prerequisites

Before starting, ensure you have:

1. **Python 3.10+**
2. **Redis Server** running locally:
   ```bash
   # Windows (using Memurai or Redis for Windows)
   # Download from: https://github.com/tporadowski/redis/releases
   ```

3. **Ollama with Mistral model**:
   ```bash
   # Install Ollama from: https://ollama.ai/
   
   # Pull Mistral model
   ollama pull mistral
   
   # Verify Ollama is running
   curl http://localhost:11434/api/tags
   ```

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
cd c:\Users\User\Desktop\pro

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Download NLTK data (for BLEU evaluation)
python -c "import nltk; nltk.download('punkt')"
```

### 2. Configuration

Create `.env` file from template:

```bash
cp .env.example .env
```

**Important**: Update these settings in `.env`:

```env
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# Redis Configuration  
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=          # Leave empty for local Redis

# Data Path
SEMANTIC_CHUNKS_FILE=./data/semantic_chunks.jsonl
```

### 3. Prepare Data

Ensure your `semantic_chunks.jsonl` exists:

```bash
# Check if data file exists
ls data/semantic_chunks.jsonl

# If not present, create sample or add your university documents
```

### 4. Start the Backend

```bash
# From project root
python -m backend.main
```

Expected output:
```
INFO - Initializing University Student Information Assistant
INFO - Loading embedding model: sentence-transformers/all-MiniLM-L6-v2
INFO - Loaded FAISS index with 1234 vectors
INFO - Connected to Redis for caching
INFO - System initialization completed successfully!
INFO - Uvicorn running on http://0.0.0.0:8000
```

### 5. Start the Frontend

In a **new terminal**:

```bash
.\venv\Scripts\activate  # Activate venv

streamlit run frontend/app.py
```

The UI will open at `http://localhost:8501`

---

## 💡 Usage Examples

### Via Streamlit UI

1. **Update Student Profile** (sidebar):
   - Name: John Doe
   - Program: MTech
   - Department: Computer Science
   - Year: 1

2. **Ask Questions**:
   - _"What are the core courses for CSE MTech?"_
   - _"When does semester registration close?"_
   - _"What is the hostel room allocation process?"_
   - _"Tell me about the placement eligibility criteria"_

3. **View Citations**: Click "📚 Sources" under each answer

### Via API (cURL)

```bash
# Health Check
curl http://localhost:8000/api/health

# Chat Query
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-123",
    "query": "What are the MTech programs offered?",
    "use_cache": true
  }'

# Update Student Profile
curl -X PUT http://localhost:8000/api/memory/profile/test-session-123 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "program": "BTech",
    "department": "ECE",
    "year": 3
  }'

# Trigger Manual Ingestion
curl -X POST http://localhost:8000/api/ingest/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "./data/new_document.pdf"
  }'

# Get Cache Statistics
curl http://localhost:8000/api/metrics/cache
```

---

## 📁 Project Structure

```
pro/
├── backend/               # FastAPI application
│   ├── main.py           # Entry point
│   ├── models.py         # Pydantic models
│   └── routes/
│       ├── chat_routes.py
│       ├── memory_routes.py
│       ├── ingestion_routes.py
│       └── monitoring_routes.py
├── frontend/
│   └── app.py            # Streamlit UI
├── src/
│   ├── config.py         # Configuration management
│   ├── system.py         # System initializer
│   ├── rag_engine.py     # Core RAG pipeline
│   ├── ingestion_manager.py
│   ├── chunking/         # Semantic chunking
│   ├── retrieval/        # FAISS, BM25, hybrid, reranker
│   ├── caching/          # Redis + semantic cache
│   ├── memory/           # Conversation + entity memory
│   ├── ingestion/        # Document processing, Watchdog
│   ├── guardrails/       # Input/output validation
│   └── utils/
├── data/
│   └── semantic_chunks.jsonl
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔧 Advanced Configuration

### Semantic Cache Tuning

```env
# Adjust similarity threshold (default: 0.85)
SEMANTIC_CACHE_SIMILARITY_THRESHOLD=0.90  # Stricter matching
```

### Retrieval Weights

```env
# Default: BM25=0.3, FAISS=0.7
BM25_WEIGHT=0.4
FAISS_WEIGHT=0.6
```

### Chunk Sizes

```env
CHUNK_MIN_SIZE=200
CHUNK_MAX_SIZE=1000
CHUNK_OVERLAP=75
```

---

## 📊 Monitoring

### Cache Performance

```bash
# Get cache statistics
curl http://localhost:8000/api/metrics/cache

# Sample Response:
{
  "traditional": {
    "total_keys": 45,
    "ttl_seconds": 86400
  },
  "semantic": {
    "total_entries": 23,
    "similarity_threshold": 0.85
  }
}
```

### Retrieval Metrics

```bash
curl http://localhost:8000/api/metrics/retrieval

# Sample Response:
{
  "vector_store": {
    "total_vectors": 2456,
    "dimension": 384,
    "model": "sentence-transformers/all-MiniLM-L6-v2"
  },
  "bm25": {
    "total_documents": 2456
  }
}
```

### Ingestion Logs

```bash
curl http://localhost:8000/api/ingest/logs?lines=20
```

---

## 🛡️ Guardrails in Action

### Input Validation
- **Length checks**: 3-2000 characters
- **Harmful content detection**: Blocks queries with risky keywords
- **Medical disclaimer**: Auto-added for health-related queries
- **Mental health referral**: Provides counseling resources

### Output Validation
- **Structure enforcement**: Ensures `answer`, `citations`, `confidence` fields
- **Citation verification**: Checks that sources are provided
- **Grounding score**: Detects potential hallucinations (overlap < 30%)
- **Confidence thresholding**: Warns if confidence < 0.6

---

## 🧪 Testing

### Manual Testing

```python
# Test RAG pipeline directly
from src.system import system

system.initialize_all()

result = system.rag_engine.answer_question(
    query="What are the PhD admission requirements?",
    student_context="Program: PhD\nDepartment: Physics"
)

print(result["answer"])
print(f"Confidence: {result['confidence']:.2%}")
print(f"Sources: {len(result['citations'])}")
```

### Sample Test Queries

Included in implementation plan - see test queries for:
- Academic calendar
- Program offerings
- Exam rules  
- International student processes
- Department information

---

## 🔄 Auto-Ingestion Workflow

The system automatically monitors `./data/` for new files:

```
User adds file → Watchdog detects → Document Processor extracts text
  ↓
Semantic Chunker creates chunks (300-800 tokens)
  ↓
Updates FAISS + BM25 indexes
  ↓
Appends to semantic_chunks.jsonl
  ↓
Invalidates RAG cache
```

**Supported formats**: PDF, DOCX, TXT, Markdown

---

## 🤝 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat/` | POST | Send query, get answer |
| `/api/chat/history/{session_id}` | GET | Retrieve conversation history |
| `/api/memory/profile/{session_id}` | GET/PUT | Get/update student profile |
| `/api/ingest/trigger` | POST | Manually trigger ingestion |
| `/api/ingest/status` | GET | Check file watcher status |
| `/api/health` | GET | System health check |
| `/api/metrics/cache` | GET | Cache statistics |
| `/api/metrics/retrieval` | GET | Vector store stats |

---

## 🐛 Troubleshooting

### Backend won't start

**Error**: `Failed to connect to Redis`
```bash
# Start Redis server
redis-server  # Linux/Mac
# Or start Redis/Memurai service on Windows
```

**Error**: `Failed to connect to Ollama`
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# If not, start Ollama service
ollama serve
```

### Frontend can't reach backend

**Error in Streamlit**: `Cannot connect to backend`
```bash
# Verify backend is running
curl http://localhost:8000/api/health

# Check CORS settings in .env
ALLOWED_ORIGINS=http://localhost:8501
```

### No chunks found

**Error**: `Loaded 0 chunks from initial file`
```bash
# Verify semantic_chunks.jsonl exists and has content
cat data/semantic_chunks.jsonl | wc -l

# If empty, manually ingest documents
curl -X POST http://localhost:8000/api/ingest/trigger \
  -H "Content-Type: application/json" \
  -d '{"directory_path": "./data"}'
```

---

## 📝 License

This project is provided as-is for educational and research purposes.

---

## 🙏 Acknowledgments

Built with:
- [LangChain](https://github.com/langchain-ai/langchain)
- [Ollama](https://ollama.ai/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [Sentence Transformers](https://www.sbert.net/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Streamlit](https://streamlit.io/)

---

**Questions or Issues?** Check logs in `./logs/` for detailed error information.
