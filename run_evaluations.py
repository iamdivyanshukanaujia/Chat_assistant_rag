"""
Comprehensive RAG Evaluation Runner

Executes all evaluation modules and generates reports:
- RAG Retrieval Metrics (Precision@k, Recall@k, Hit Rate, MRR)
- Response Quality (ROUGE-L, BLEU, BERTScore)
- Advising Quality (LLM-as-judge scoring)
- Latency Benchmarks

Usage:
    python run_evaluations.py --all
    python run_evaluations.py --retrieval
    python run_evaluations.py --latency
"""
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List

# Import evaluation modules
from src.evaluation.rag_metrics import RAGMetrics, format_metrics_report
from src.evaluation.latency_benchmark import LatencyBenchmark, format_latency_report
from src.evaluation.response_quality import ResponseQualityEvaluator, format_quality_report
from src.evaluation.quality_scorer import AdvisingQualityScorer, format_advising_report

# Import system components
from src.rag_engine import RAGEngine
from src.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EvaluationRunner:
    """Main evaluation orchestrator."""
    
    def __init__(self):
        self.data_dir = Path("data/eval")
        self.results_dir = Path("results/evaluation")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Load test data
        self.ground_truth = self._load_json(self.data_dir / "ground_truth.json")
        self.reference_answers = self._load_json(self.data_dir / "reference_answers.json")
        
        # Initialize evaluators
        self.rag_metrics = RAGMetrics()
        self.latency_benchmark = LatencyBenchmark()
        self.response_quality = ResponseQualityEvaluator()
        self.quality_scorer = AdvisingQualityScorer()
        
        # Use existing system RAG engine
        try:
            from src.system import system
            if system.rag_engine is None:
                logger.info("RAG engine not initialized, initializing system...")
                system.initialize_all(load_initial_data=True)
            self.rag_engine = system.rag_engine
            logger.info("RAG engine loaded from system successfully")
        except Exception as e:
            logger.error(f"Failed to load RAG engine from system: {e}")
            self.rag_engine = None
    
    def _load_json(self, path: Path) -> List[Dict]:
        """Load JSON file."""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {path}: {e}")
            return []
    
    def _save_report(self, name: str, content: str):
        """Save report to file."""
        report_path = self.results_dir / f"{name}_report.txt"
        with open(report_path, 'w') as f:
            f.write(content)
        logger.info(f"Report saved to: {report_path}")
    
    def run_retrieval_evaluation(self) -> Dict[str, Any]:
        """Evaluate retrieval metrics."""
        logger.info("Running retrieval evaluation...")
        
        if not self.rag_engine:
            logger.error("RAG engine not available")
            return {}
        
        query_results = []
        
        for test_case in self.ground_truth:
            query = test_case['query']
            relevant_docs = set(test_case['relevant_docs'])
            
            # Get retrieved documents
            try:
                # HybridRetriever.retrieve returns List[Tuple[SemanticChunk, float]]
                retrieved_tuples = self.rag_engine.hybrid_retriever.retrieve(query)
                # Use source_file and category as the doc identifier
                retrieved_ids = [f"{chunk.source_file}_{chunk.category}" 
                               for chunk, score in retrieved_tuples]
                
                # Evaluate
                result = self.rag_metrics.evaluate_query(retrieved_ids, relevant_docs)
                result['query'] = query
                query_results.append(result)
                
                logger.info(f"Evaluated: {query[:50]}...")
            except Exception as e:
                logger.error(f"Error evaluating query '{query}': {e}")
        
        # Aggregate results
        aggregated = self.rag_metrics.aggregate_results(query_results)
        
        # Generate report
        report = format_metrics_report(aggregated)
        print("\n" + report)
        self._save_report("retrieval_metrics", report)
        
        return aggregated
    
    def run_latency_evaluation(self) -> Dict[str, Any]:
        """Evaluate latency benchmarks."""
        logger.info("Running latency evaluation...")
        
        if not self.rag_engine:
            logger.error("RAG engine not available")
            return {}
        
        test_query = "What is the minimum attendance requirement?"
        student_profile = {
            "student_id": "test123",
            "name": "Test Student",
            "program": "BTech",
            "year": 3
        }
        
        results = {}
        
        # Benchmark full RAG pipeline
        try:
            logger.info("Benchmarking full RAG pipeline...")
            results["full_pipeline"] = self.latency_benchmark.benchmark_rag_pipeline(
                self.rag_engine,
                test_query,
                student_profile,
                "test_session",
                iterations=20  # Reduced for speed
            )
        except Exception as e:
            logger.error(f"Failed to benchmark full pipeline: {e}")
        
        # Benchmark retrieval only
        try:
            logger.info("Benchmarking retrieval only...")
            results["retrieval"] = self.latency_benchmark.benchmark_retrieval_only(
                self.rag_engine.hybrid_retriever,
                test_query,
                iterations=50
            )
        except Exception as e:
            logger.error(f"Failed to benchmark retrieval: {e}")
        
        # Benchmark LLM generation
        try:
            logger.info("Benchmarking LLM generation...")
            test_prompt = "What is 2+2?"
            results["llm_generation"] = self.latency_benchmark.benchmark_llm_generation(
                self.rag_engine.llm,
                test_prompt,
                iterations=20
            )
        except Exception as e:
            logger.error(f"Failed to benchmark LLM: {e}")
        
        # Generate report
        report = format_latency_report(results)
        print("\n" + report)
        self._save_report("latency_benchmark", report)
        
        return results
    
    def run_response_quality_evaluation(self) -> Dict[str, Any]:
        """Evaluate response quality."""
        logger.info("Running response quality evaluation...")
        
        if not self.rag_engine:
            logger.error("RAG engine not available")
            return {}
        
        generated_responses = []
        reference_responses = []
        
        for test_case in self.reference_answers:
            query = test_case['query']
            reference = test_case['reference_answer']
            
            try:
                # Generate response
                result = self.rag_engine.answer_question(
                    query=query,
                    session_id="eval_session",
                    use_cache=False
                )
                
                generated = result.get('answer', '')
                generated_responses.append(generated)
                reference_responses.append(reference)
                
                logger.info(f"Generated response for: {query[:50]}...")
            except Exception as e:
                logger.error(f"Error generating response for '{query}': {e}")
        
        # Evaluate
        if generated_responses and reference_responses:
            results = self.response_quality.evaluate_batch(
                generated_responses,
                reference_responses,
                include_bert=False  # Set to True for BERTScore (slower)
            )
            
            # Generate report
            report = format_quality_report(results)
            print("\n" + report)
            self._save_report("response_quality", report)
            
            return results
        
        return {}
    
    def run_advising_quality_evaluation(self) -> Dict[str, Any]:
        """Evaluate advising quality using LLM-as-judge."""
        logger.info("Running advising quality evaluation...")
        
        if not self.rag_engine:
            logger.error("RAG engine not available")
            return {}
        
        evaluations = []
        
        # Test on first 3 queries (LLM-as-judge is expensive)
        for test_case in self.reference_answers[:3]:
            query = test_case['query']
            
            try:
                # Generate response
                result = self.rag_engine.answer_question(
                    query=query,
                    session_id="eval_session",
                    use_cache=False
                )
                
                evaluations.append({
                    "query": query,
                    "response": result.get('answer', ''),
                    "student_context": student_profile,
                    "sources": result.get('sources', [])
                })
                
                logger.info(f"Prepared for scoring: {query[:50]}...")
            except Exception as e:
                logger.error(f"Error preparing evaluation for '{query}': {e}")
        
        # Score
        if evaluations:
            results = self.quality_scorer.score_batch(evaluations)
            
            # Generate report
            report = format_advising_report(results)
            print("\n" + report)
            self._save_report("advising_quality", report)
            
            return results
        
        return {}
    
    def run_all(self):
        """Run all evaluations."""
        logger.info("=" * 70)
        logger.info("RUNNING COMPREHENSIVE RAG EVALUATION")
        logger.info("=" * 70)
        
        results = {
            "retrieval_metrics": self.run_retrieval_evaluation(),
            "latency_benchmark": self.run_latency_evaluation(),
            "response_quality": self.run_response_quality_evaluation(),
            "advising_quality": self.run_advising_quality_evaluation()
        }
        
        # Save combined results
        results_path = self.results_dir / "all_results.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"All results saved to: {results_path}")
        
        logger.info("=" * 70)
        logger.info("EVALUATION COMPLETE!")
        logger.info("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Run RAG system evaluations")
    parser.add_argument("--all", action="store_true", help="Run all evaluations")
    parser.add_argument("--retrieval", action="store_true", help="Run retrieval metrics only")
    parser.add_argument("--latency", action="store_true", help="Run latency benchmarks only")
    parser.add_argument("--response", action="store_true", help="Run response quality only")
    parser.add_argument("--advising", action="store_true", help="Run advising quality only")
    
    args = parser.parse_args()
    
    runner = EvaluationRunner()
    
    if args.all or not any([args.retrieval, args.latency, args.response, args.advising]):
        runner.run_all()
    else:
        if args.retrieval:
            runner.run_retrieval_evaluation()
        if args.latency:
            runner.run_latency_evaluation()
        if args.response:
            runner.run_response_quality_evaluation()
        if args.advising:
            runner.run_advising_quality_evaluation()


if __name__ == "__main__":
    main()
