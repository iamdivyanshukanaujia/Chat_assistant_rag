"""
Complete Evaluation with All Metrics
Uses live API to get real ROUGE/BLEU scores
"""
import requests
import json
import statistics
from pathlib import Path

# Import scoring libraries
try:
    from rouge_score import rouge_scorer
    ROUGE_AVAILABLE = True
except:
    ROUGE_AVAILABLE = False

try:
    import nltk
    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
    NLTK_AVAILABLE = True
except:
    NLTK_AVAILABLE = False

API_URL = "http://localhost:8000"

print("="*70)
print("COMPLETE RAG EVALUATION - All Metrics")
print("="*70)
print()

# Load test data
with open("data/eval/reference_answers.json") as f:
    reference_answers = json.load(f)

# Initialize scorers
if ROUGE_AVAILABLE:
    rouge = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    print("[OK] ROUGE scorer ready")
else:
    print("[X] ROUGE not available")

if NLTK_AVAILABLE:
    smoothing = SmoothingFunction().method1
    print("[OK] BLEU scorer ready")
else:
    print("[X] BLEU not available")

print()
print("="*70)
print("RESPONSE QUALITY METRICS")
print("="*70)
print()

rouge_scores = []
bleu_scores = []
word_overlaps = []

for ref in reference_answers:
    query = ref['query']
    reference = ref['reference_answer']
    
    try:
        response = requests.post(
            f"{API_URL}/api/chat/",
            json={"query": query, "session_id": "eval_complete"},
            timeout=15
        )
        
        if response.status_code == 200:
            generated = response.json().get('answer', '')
            
            print(f"Query: {query}")
            print(f"Generated: {generated[:100]}...")
            print()
            
            # ROUGE-L
            if ROUGE_AVAILABLE:
                scores = rouge.score(reference, generated)
                rouge_l = scores['rougeL'].fmeasure
                rouge_scores.append(rouge_l)
                print(f"  ROUGE-L F1: {rouge_l:.3f}")
            
            # BLEU
            if NLTK_AVAILABLE:
                ref_tokens = nltk.word_tokenize(reference.lower())
                gen_tokens = nltk.word_tokenize(generated.lower())
                bleu = sentence_bleu([ref_tokens], gen_tokens, smoothing_function=smoothing)
                bleu_scores.append(bleu)
                print(f"  BLEU Score: {bleu:.3f}")
            
            # Word overlap
            ref_words = set(reference.lower().split())
            gen_words = set(generated.lower().split())
            overlap = len(ref_words & gen_words) / len(ref_words | gen_words) if (ref_words | gen_words) else 0
            word_overlaps.append(overlap)
            print(f"  Word Overlap: {overlap:.3f}")
            print()
            
    except Exception as e:
        print(f"Error on '{query}': {e}")
        print()

print("="*70)
print("AGGREGATE RESULTS")
print("="*70)
print()

if rouge_scores:
    print(f"ROUGE-L (Semantic Overlap):")
    print(f"  Mean: {statistics.mean(rouge_scores):.3f}")
    print(f"  Min:  {min(rouge_scores):.3f}")
    print(f"  Max:  {max(rouge_scores):.3f}")
    print()

if bleu_scores:
    print(f"BLEU (N-gram Match):")
    print(f"  Mean: {statistics.mean(bleu_scores):.3f}")
    print(f"  Min:  {min(bleu_scores):.3f}")
    print(f"  Max:  {max(bleu_scores):.3f}")
    print()

if word_overlaps:
    print(f"Word-Level Overlap:")
    print(f"  Mean: {statistics.mean(word_overlaps):.3f}")
    print()

# Overall quality assessment
if rouge_scores and bleu_scores:
    avg_quality = (statistics.mean(rouge_scores) + statistics.mean(bleu_scores)) / 2
    
    if avg_quality >= 0.60:
        status = "EXCELLENT"
    elif avg_quality >= 0.45:
        status = "GOOD"
    elif avg_quality >= 0.30:
        status = "ACCEPTABLE"
    else:
        status = "NEEDS IMPROVEMENT"
    
    print(f"Overall Response Quality: {status} (avg: {avg_quality:.3f})")

print()
print("="*70)
print("EVALUATION COMPLETE!")
print("="*70)

# Save results
results = {
    "rouge_l_scores": rouge_scores,
    "bleu_scores": bleu_scores,
    "word_overlaps": word_overlaps,
    "rouge_l_mean": statistics.mean(rouge_scores) if rouge_scores else 0,
    "bleu_mean": statistics.mean(bleu_scores) if bleu_scores else 0,
    "num_queries": len(reference_answers)
}

Path("results/evaluation").mkdir(parents=True, exist_ok=True)
with open("results/evaluation/response_quality_results.json", "w") as f:
    json.dump(results, f, indent=2)

print()
print("Results saved to: results/evaluation/response_quality_results.json")
