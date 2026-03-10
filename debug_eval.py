"""
Debug script to see what's being compared in the evaluation
"""
import json
from src.system import system

# Initialize system
system.initialize_all()

# Test query
query = "What is the minimum attendance requirement?"

# Get retrieved documents
retrieved_tuples = system.rag_engine.hybrid_retriever.retrieve(query)

print("Query:", query)
print("\nRetrieved Document IDs:")
print("=" * 60)
for i, (chunk, score) in enumerate(retrieved_tuples[:10]):
    doc_id = f"{chunk.source_file}_{chunk.category}"
    print(f"{i+1}. {doc_id} (score: {score:.4f})")
    print(f"   Source: {chunk.source_file}")
    print(f"   Category: {chunk.category}")
    print()

# Load ground truth
with open("data/eval/ground_truth.json") as f:
    ground_truth = json.load(f)

# Find this query in ground truth
for test_case in ground_truth:
    if test_case['query'] == query:
        print("\nExpected Document IDs (from ground truth):")
        print("=" * 60)
        for relevant_doc in test_case['relevant_docs']:
            print(f"- {relevant_doc}")
        
        print("\nComparison:")
        print("=" * 60)
        retrieved_ids = [f"{chunk.source_file}_{chunk.category}" for chunk, score in retrieved_tuples]
        relevant_set = set(test_case['relevant_docs'])
        
        print(f"Retrieved IDs: {retrieved_ids[:5]}")
        print(f"Relevant docs: {list(relevant_set)}")
        print(f"\nIntersection: {set(retrieved_ids) & relevant_set}")
        break
