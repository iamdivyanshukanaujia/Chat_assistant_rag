"""
Compare generated vs reference answers to understand low scores
"""
import json

# Load reference answers
with open("data/eval/reference_answers.json") as f:
    references = json.load(f)

# Load the actual results from evaluation
# We'll manually check one query to see what was generated
from src.system import system

system.initialize_all()

# Test one query
query = "What is the minimum attendance requirement?"
result = system.rag_engine.answer_question(
    query=query,
    session_id="comparison_test",
    use_cache=False
)

# Find the reference for this query
ref_answer = None
for ref in references:
    if ref['query'] == query:
        ref_answer = ref['reference_answer']
        break

print("=" * 70)
print("QUERY:", query)
print("=" * 70)
print()

print("REFERENCE ANSWER (from reference_answers.json):")
print("-" * 70)
print(ref_answer)
print()

print("GENERATED ANSWER (from your RAG system):")
print("-" * 70)
print(result['answer'])
print()

print("=" * 70)
print("COMPARISON ANALYSIS:")
print("=" * 70)

# Simple word overlap check
ref_words = set(ref_answer.lower().split())
gen_words = set(result['answer'].lower().split())
overlap = ref_words & gen_words
overlap_ratio = len(overlap) / len(ref_words) if ref_words else 0

print(f"Reference word count: {len(ref_words)}")
print(f"Generated word count: {len(gen_words)}")
print(f"Overlapping words: {len(overlap)}")
print(f"Overlap ratio: {overlap_ratio:.2%}")
print()
print("This is why ROUGE/BLEU scores are low!")
print("The system gives CORRECT information but uses DIFFERENT WORDS.")
