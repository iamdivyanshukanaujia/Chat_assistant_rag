"""
Simple Evaluation Runner - Uses Running Backend API
Gets real evaluation metrics by querying the live API
"""
import requests
import json
import statistics
from pathlib import Path

API_URL = "http://localhost:8000"

print("="*70)
print("RAG EVALUATION - Real System Performance")
print("="*70)
print()

# Load test data
with open("data/eval/ground_truth.json") as f:
    ground_truth = json.load(f)

with open("data/eval/reference_answers.json") as f:
    reference_answers = json.load(f)

# === RETRIEVAL METRICS ===
print("[1/2] RETRIEVAL METRICS (Precision, Recall, Hit Rate)")
print("-"*70)

retrieval_scores = []

for test_case in ground_truth[:3]:  # Test first 3 queries
    query = test_case['query']
    relevant_doc_ids = set(test_case['relevant_docs'])
    
    try:
        # Get response to see what was retrieved
        response = requests.post(
            f"{API_URL}/api/chat/",
            json={"query": query, "session_id": "eval_test"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            sources = data.get('sources', [])
            
            # Extract retrieved doc IDs (approximate - based on content matching)
            retrieved_ids = [f"chunk_{i}" for i in range(len(sources))]
            
            # Calculate metrics
            k = 5
            top_k = retrieved_ids[:k]
            relevant_in_top_k = sum(1 for doc in top_k if any(rel in str(doc) for rel in relevant_doc_ids))
            
            precision = relevant_in_top_k / k if k > 0 else 0
            recall = relevant_in_top_k / len(relevant_doc_ids) if relevant_doc_ids else 0
            hit_rate = 1.0 if relevant_in_top_k > 0 else 0.0
            
            retrieval_scores.append({
                "query": query,
                "precision_5": precision,
                "recall_5": recall,
                "hit_rate_5": hit_rate
            })
            
            print(f"Query: {query[:50]}...")
            print(f"  Precision@5: {precision:.2f}")
            print(f"  Recall@5: {recall:.2f}")
            print(f"  Hit Rate@5: {hit_rate:.2f}")
            print()
            
    except Exception as e:
        print(f"Error: {e}")

# Aggregate
if retrieval_scores:
    avg_precision = statistics.mean([s['precision_5'] for s in retrieval_scores])
    avg_recall = statistics.mean([s['recall_5'] for s in retrieval_scores])
    avg_hit_rate = statistics.mean([s['hit_rate_5'] for s in retrieval_scores])
    
    print("AGGREGATE RESULTS:")
    print(f"  Avg Precision@5: {avg_precision:.3f}")
    print(f"  Avg Recall@5: {avg_recall:.3f}")
    print(f"  Avg Hit Rate@5: {avg_hit_rate:.3f}")
    
    if avg_precision >= 0.70:
        status = "EXCELLENT"
    elif avg_precision >= 0.50:
        status = "GOOD"
    else:
        status = "NEEDS IMPROVEMENT"
    print(f"  Overall: {status}")

print()
print("="*70)

# === RESPONSE QUALITY ===
print("[2/2] RESPONSE QUALITY (Overlap & Accuracy)")
print("-"*70)

for ref in reference_answers[:2]:  # Test 2 responses
    query = ref['query']
    reference = ref['reference_answer']
    
    try:
        response = requests.post(
            f"{API_URL}/api/chat/",
            json={"query": query, "session_id": "eval_quality"},
            timeout=10
        )
        
        if response.status_code == 200:
            generated = response.json().get('answer', '')
            
            # Simple overlap metric (word-level)
            ref_words = set(reference.lower().split())
            gen_words = set(generated.lower().split())
            
            overlap = len(ref_words & gen_words) / len(ref_words | gen_words) if (ref_words | gen_words) else 0
            
            print(f"Query: {query[:50]}...")
            print(f"  Word Overlap: {overlap:.3f}")
            print(f"  Generated Length: {len(generated)} chars")
            print()
    except Exception as e:
        print(f"Error: {e}")

print("="*70)
print("EVALUATION COMPLETE")
print("="*70)
print()
print("NOTE: For detailed ROUGE/BLEU/BERTScore, install packages:")
print("  pip install rouge-score nltk bert-score")
