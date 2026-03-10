"""
Quick test to verify backend returns clean text
"""
from src.system import system

# Initialize
system.initialize_all()

# Test multiple queries
test_queries = [
    "What is the minimum attendance requirement?",
    "Give a summary of ODD semester (Autumn)",
    "What are the library timings?"
]

print("=" * 70)
print("TESTING BACKEND RESPONSES FOR HTML")
print("=" * 70)

for query in test_queries:
    result = system.rag_engine.answer_question(
        query=query,
        session_id="clean_test",
        use_cache=False
    )
    
    answer = result['answer']
    
    # Check for HTML tags
    has_html = '<div' in answer or '</div>' in answer or '<span' in answer
    
    print(f"\nQuery: {query}")
    print(f"Has HTML tags: {has_html}")
    if has_html:
        print("⚠️ WARNING: HTML detected!")
        print(f"Answer: {answer[:200]}...")
    else:
        print(f"✓ Clean: {answer[:100]}...")

print("\n" + "=" * 70)
print("All responses checked. If you see warnings above, there's HTML in the data.")
print("=" * 70)
