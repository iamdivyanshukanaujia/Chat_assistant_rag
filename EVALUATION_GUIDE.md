# RAG Evaluation Suite - Quick Start

## Running Evaluations

### Run All Evaluations:
```bash
python run_evaluations.py --all
```

### Run Individual Modules:
```bash
# Retrieval metrics only
python run_evaluations.py --retrieval

# Latency benchmarks only
python run_evaluations.py --latency

# Response quality only
python run_evaluations.py --response

# Advising quality only (uses Azure GPT-4o)
python run_evaluations.py --advising
```

## What Gets Evaluated

### 1. RAG Retrieval Metrics
- **Precision@k**: Accuracy of retrieved documents
- **Recall@k**: Coverage of relevant documents  
- **Hit Rate@k**: Success rate (at least 1 relevant doc)
- **MRR**: Mean Reciprocal Rank

**Test Queries:**
- "What are prerequisites for DS201?"
- "When does registration close?"
- "What is the minimum attendance requirement?"
- "How do I apply for hostel accommodation?"
- "What are the library timings?"

### 2. Latency Benchmarks
- Full RAG pipeline (retrieval + LLM)
- Retrieval only
- LLM generation only

**Targets:**
- Full pipeline: < 3 seconds
- Retrieval: < 200ms
- LLM generation: < 2 seconds

### 3. Response Quality
- **ROUGE-L**: Longest common subsequence
- **BLEU**: N-gram overlap
- **BERTScore**: Semantic similarity (optional, slower)

### 4. Advising Quality (LLM-as-Judge)
5-point scoring on:
- Relevance
- Correctness
- Personalization
- Non-hallucination
- Policy consistency

## Output Reports

All reports saved to: `results/evaluation/`

- `retrieval_metrics_report.txt`
- `latency_benchmark_report.txt`
- `response_quality_report.txt`
- `advising_quality_report.txt`
- `all_results.json` (combined data)

## Adding New Test Cases

### Ground Truth (Retrieval):
Edit `data/eval/ground_truth.json`:
```json
{
  "query": "Your question",
  "relevant_docs": ["chunk_id_1", "chunk_id_2"],
  "description": "What this query tests"
}
```

### Reference Answers (Quality):
Edit `data/eval/reference_answers.json`:
```json
{
  "query": "Your question",
  "reference_answer": "Expected answer text"
}
```

## Notes

- Make sure backend is running before evaluations
- Advising quality uses Azure GPT-4o (costs $)
- BERTScore is slow - disabled by default
- Results are deterministic (temperature=0 for scoring)
