# Quick Start Guide

## Prerequisites Checklist

Before running the system, ensure:

- [ ] **Python 3.10+** installed
- [ ] **Redis** running on localhost:6379
- [ ] **Ollama** running with Mistral model
- [ ] **Virtual environment** created
- [ ] **Dependencies** installed
- [ ] **`.env` file** configured
- [ ] **semantic_chunks.jsonl** present in `/data/`

## Step-by-Step Setup

### 1. Start Redis

**Windows (using Memurai or Redis for Windows)**:
```bash
# Start Redis service
redis-server
```

**Verify**:
```bash
redis-cli ping
# Should return: PONG
```

### 2. Start Ollama

```bash
# Start Ollama service (if not already running)
ollama serve

# In another terminal, verify model is available
ollama list
# Should show 'mistral' in the list
```

### 3. Install Dependencies

```bash
cd c:\Users\User\Desktop\pro

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example env file
copy .env.example .env

# Edit .env and verify these settings:
# - REDIS_HOST=localhost
# - REDIS_PORT=6379
# - OLLAMA_BASE_URL=http://localhost:11434
# - SEMANTIC_CHUNKS_FILE=./data/semantic_chunks.jsonl
```

### 5. Start Backend

**Option A: Using start script**
```bash
.\start.bat
```

**Option B: Manual**
```bash
python -m backend.main
```

**Expected Output**:
```
INFO - Initializing University Student Information Assistant
INFO - Loading embedding model: sentence-transformers/all-MiniLM-L6-v2
INFO - Loaded FAISS index with X vectors
INFO - System initialization completed successfully!
INFO - Application startup complete
INFO - Uvicorn running on http://0.0.0.0:8000
```

### 6. Start Frontend (New Terminal)

```bash
# Activate venv
.\venv\Scripts\activate

# Run Streamlit
streamlit run frontend/app.py
```

**Browser Opens**: http://localhost:8501

## Quick Test

Once both services are running:

1. **Open Streamlit UI** at http://localhost:8501
2. **Update Profile** (sidebar):
   - Name: Test Student
   - Program: MTech
   - Department: CSE
3. **Ask a Question**: "What are the core courses?"
4. **Check Response**: Should show answer with citations

## Troubleshooting Quick Fixes

### Backend Error: "Failed to connect to Redis"
```bash
# Start Redis
redis-server

# Or check if already running
redis-cli ping
```

### Backend Error: "Failed to connect to Ollama"
```bash
# Check Ollama
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve
```

### Frontend Error: "Cannot connect to backend"
```bash
# Verify backend is running
curl http://localhost:8000/api/health

# Should return JSON with "status": "healthy"
```

### No Chunks Loaded
```bash
# Check if file exists
dir data\semantic_chunks.jsonl

# If missing, you need to add your university documents
# or manually trigger ingestion via API
```

## Next Steps

Once setup is complete:

1. **Test RAG queries** in the Streamlit UI
2. **Monitor system** via http://localhost:8000/api/health
3. **View metrics** in UI footer (cache, knowledge base size)
4. **Add documents** by placing them in `/data/` folder
5. **View ingestion logs** via API: http://localhost:8000/api/ingest/logs

## Common Commands

```bash
# Check system status
curl http://localhost:8000/api/health

# View cache stats
curl http://localhost:8000/api/metrics/cache

# View retrieval stats
curl http://localhost:8000/api/metrics/retrieval

# Manually trigger ingestion
curl -X POST http://localhost:8000/api/ingest/trigger \
  -H "Content-Type: application/json" \
  -d '{"directory_path": "./data"}'
```
