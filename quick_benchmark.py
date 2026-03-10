"""
Quick Performance Benchmark
Measures latency of backend API endpoints
"""
import requests
import time
import statistics

API_URL = "http://localhost:8000"

def benchmark_endpoint(endpoint, data, iterations=20):
    """Benchmark an API endpoint"""
    timings = []
    
    for i in range(iterations):
        start = time.perf_counter()
        try:
            response = requests.post(f"{API_URL}{endpoint}", json=data, timeout=30)
            end = time.perf_counter()
            
            if response.status_code == 200:
                timings.append((end - start) * 1000)  # Convert to ms
        except Exception as e:
            print(f"Request {i} failed: {e}")
    
    if not timings:
        return None
    
    sorted_timings = sorted(timings)
    n = len(sorted_timings)
    
    return {
        "mean": statistics.mean(timings),
        "median": statistics.median(timings),
        "min": min(timings),
        "max": max(timings),
        "p95": sorted_timings[int(n * 0.95)] if n > 0 else 0,
        "p99": sorted_timings[int(n * 0.99)] if n > 0 else 0,
        "iterations": n
    }

print("=" * 70)
print("PERFORMANCE BENCHMARK - University AI Assistant")
print("=" * 70)
print()

# Test 1: Chat endpoint (Full RAG pipeline)
print("[1/2] Benchmarking: Full RAG Pipeline (Chat Endpoint)")
print("-" * 70)

chat_data = {
    "query": "What is the minimum attendance requirement?",
    "session_id": "perf_test_123"
}

results = benchmark_endpoint("/api/chat/", chat_data, iterations=10)

if results:
    print(f"Iterations:  {results['iterations']}")
    print(f"Mean:        {results['mean']:.2f} ms")
    print(f"Median:      {results['median']:.2f} ms")
    print(f"Min:         {results['min']:.2f} ms")
    print(f"Max:         {results['max']:.2f} ms")
    print(f"P95:         {results['p95']:.2f} ms")
    print(f"P99:         {results['p99']:.2f} ms")
    
    # Performance assessment
    mean_sec = results['mean'] / 1000
    if mean_sec < 2:
        status = "✅ EXCELLENT"
    elif mean_sec < 5:
        status = "⚠️ ACCEPTABLE"
    else:
        status = "❌ SLOW"
    
    print(f"Status:      {status}")
else:
    print("❌ Benchmark failed - check if backend is running")

print()
print("=" * 70)

# Test 2: Profile endpoint (Lightweight)
print("[2/2] Benchmarking: Profile Endpoint (CSV Lookup)")
print("-" * 70)

results2 = benchmark_endpoint("/api/profile/10843168", {}, iterations=50)

if results2:
    print(f"Iterations:  {results2['iterations']}")
    print(f"Mean:        {results2['mean']:.2f} ms")
    print(f"Median:      {results2['median']:.2f} ms")
    print(f"P95:         {results2['p95']:.2f} ms")
    
    if results2['mean'] < 100:
        status = "✅ EXCELLENT"
    elif results2['mean'] < 200:
        status = "⚠️ ACCEPTABLE"
    else:
        status = "❌ SLOW"
    
    print(f"Status:      {status}")
else:
    print("❌ Benchmark failed")

print()
print("=" * 70)
print("BENCHMARK COMPLETE")
print("=" * 70)
