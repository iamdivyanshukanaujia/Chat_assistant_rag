"""
Latency Benchmark Module

Measures performance of different RAG pipeline components:
- Full RAG query (end-to-end)
- Retrieval only (FAISS + BM25)
- LLM generation only
- Component-level timings

Provides percentile analysis (mean, median, p95, p99)
"""
import time
import statistics
from typing import Dict, List, Callable, Any
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class LatencyBenchmark:
    """Benchmark latency of RAG components."""
    
    def __init__(self):
        self.results = {}
    
    @staticmethod
    def measure_execution_time(func: Callable, *args, **kwargs) -> tuple:
        """
        Measure execution time of a function.
        
        Args:
            func: Function to measure
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Tuple of (result, execution_time_ms)
        """
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        
        execution_time_ms = (end - start) * 1000  # Convert to ms
        return result, execution_time_ms
    
    @staticmethod
    def run_benchmark(
        func: Callable,
        iterations: int = 100,
        warmup: int = 5,
        *args,
        **kwargs
    ) -> Dict[str, float]:
        """
        Run benchmark with multiple iterations.
        
        Args:
            func: Function to benchmark
            iterations: Number of test iterations
            warmup: Number of warmup runs (not counted)
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Dictionary with timing statistics
        """
        timings = []
        
        # Warmup runs
        for _ in range(warmup):
            try:
                func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Warmup run failed: {e}")
        
        # Actual benchmark runs
        for i in range(iterations):
            try:
                start = time.perf_counter()
                func(*args, **kwargs)
                end = time.perf_counter()
                
                execution_time_ms = (end - start) * 1000
                timings.append(execution_time_ms)
            except Exception as e:
                logger.error(f"Benchmark iteration {i} failed: {e}")
        
        if not timings:
            return {
                "mean": 0.0,
                "median": 0.0,
                "min": 0.0,
                "max": 0.0,
                "p95": 0.0,
                "p99": 0.0,
                "std_dev": 0.0,
                "iterations": 0
            }
        
        # Calculate statistics
        sorted_timings = sorted(timings)
        n = len(sorted_timings)
        
        return {
            "mean": statistics.mean(timings),
            "median": statistics.median(timings),
            "min": min(timings),
            "max": max(timings),
            "p95": sorted_timings[int(n * 0.95)] if n > 0 else 0.0,
            "p99": sorted_timings[int(n * 0.99)] if n > 0 else 0.0,
            "std_dev": statistics.stdev(timings) if n > 1 else 0.0,
            "iterations": n
        }
    
    def benchmark_rag_pipeline(
        self,
        rag_engine,
        query: str,
        student_profile: Dict,
        session_id: str,
        iterations: int = 50
    ) -> Dict[str, Any]:
        """
        Benchmark full RAG pipeline.
        
        Args:
            rag_engine: RAG engine instance
            query: Test query
            student_profile: Student profile dict
            session_id: Session ID
            iterations: Number of test runs
            
        Returns:
            Timing statistics
        """
        logger.info(f"Benchmarking full RAG pipeline: '{query}'")
        
        def run_query():
            return rag_engine.answer_question(
                query=query,
                student_profile=student_profile,
                session_id=session_id,
                use_cache=False  # Disable cache for fair timing
            )
        
        results = self.run_benchmark(run_query, iterations=iterations)
        results["query"] = query
        results["component"] = "full_rag_pipeline"
        
        self.results["full_pipeline"] = results
        return results
    
    def benchmark_retrieval_only(
        self,
        retriever,
        query: str,
        iterations: int = 100
    ) -> Dict[str, Any]:
        """
        Benchmark retrieval component only.
        
        Args:
            retriever: Retriever instance
            query: Test query
            iterations: Number of test runs
            
        Returns:
            Timing statistics
        """
        logger.info(f"Benchmarking retrieval: '{query}'")
        
        def run_retrieval():
            return retriever.retrieve(query)
        
        results = self.run_benchmark(run_retrieval, iterations=iterations)
        results["query"] = query
        results["component"] = "retrieval_only"
        
        self.results["retrieval"] = results
        return results
    
    def benchmark_llm_generation(
        self,
        llm,
        prompt: str,
        iterations: int = 50
    ) -> Dict[str, Any]:
        """
        Benchmark LLM generation only.
        
        Args:
            llm: LLM instance
            prompt: Test prompt
            iterations: Number of test runs
            
        Returns:
            Timing statistics
        """
        logger.info("Benchmarking LLM generation")
        
        def run_generation():
            return llm.invoke(prompt)
        
        results = self.run_benchmark(run_generation, iterations=iterations)
        results["component"] = "llm_generation"
        
        self.results["llm_generation"] = results
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all benchmarks."""
        return self.results


def format_latency_report(results: Dict[str, Dict[str, Any]]) -> str:
    """
    Format latency benchmark results into a readable report.
    
    Args:
        results: Dictionary of benchmark results
        
    Returns:
        Formatted string report
    """
    report = []
    report.append("=" * 70)
    report.append("LATENCY BENCHMARK REPORT")
    report.append("=" * 70)
    
    for component, stats in results.items():
        report.append(f"\n{component.upper().replace('_', ' ')}:")
        report.append("-" * 70)
        
        if "query" in stats:
            report.append(f"Query: {stats['query']}")
        
        report.append(f"Iterations: {stats['iterations']}")
        report.append(f"Mean:       {stats['mean']:.2f} ms")
        report.append(f"Median:     {stats['median']:.2f} ms")
        report.append(f"Min:        {stats['min']:.2f} ms")
        report.append(f"Max:        {stats['max']:.2f} ms")
        report.append(f"P95:        {stats['p95']:.2f} ms")
        report.append(f"P99:        {stats['p99']:.2f} ms")
        report.append(f"Std Dev:    {stats['std_dev']:.2f} ms")
        
        # Performance assessment
        mean_sec = stats['mean'] / 1000
        if component == "full_pipeline":
            status = "EXCELLENT" if mean_sec < 2 else "ACCEPTABLE" if mean_sec < 5 else "SLOW"
        elif component == "retrieval":
            status = "EXCELLENT" if mean_sec < 0.2 else "ACCEPTABLE" if mean_sec < 0.5 else "SLOW"
        elif component == "llm_generation":
            status = "EXCELLENT" if mean_sec < 1.5 else "ACCEPTABLE" if mean_sec < 3 else "SLOW"
        else:
            status = ""
        
        if status:
            report.append(f"Status:     {status}")
    
    report.append("=" * 70)
    
    return "\n".join(report)


def timing_decorator(name: str = None):
    """
    Decorator to automatically measure function execution time.
    
    Usage:
        @timing_decorator("my_function")
        def my_function():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = name or func.__name__
            start = time.perf_counter()
            result = func(*args, **kwargs)
            end = time.perf_counter()
            
            execution_time_ms = (end - start) * 1000
            logger.info(f"{func_name} executed in {execution_time_ms:.2f}ms")
            
            return result
        return wrapper
    return decorator
