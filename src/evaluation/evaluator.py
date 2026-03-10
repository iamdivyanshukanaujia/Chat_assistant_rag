"""
RAG System Evaluator.

Orchestrates evaluation of RAG system using test datasets.
"""
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
from datetime import datetime
import numpy as np

from src.evaluation.evaluation_metrics import EvaluationMetrics
from src.system import SystemInitializer
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RAGEvaluator:
    """Comprehensive RAG system evaluator."""
    
    def __init__(
        self,
        system: Optional[SystemInitializer] = None,
        k_values: List[int] = [1, 3, 5, 10]
    ):
        """
        Initialize RAG evaluator.
        
        Args:
            system: SystemInitializer instance (optional)
            k_values: List of k values for retrieval metrics
        """
        self.system = system
        self.metrics = EvaluationMetrics()
        self.k_values = k_values
        logger.info(f"RAG Evaluator initialized with k_values={k_values}")
    
    def load_test_dataset(self, dataset_path: str) -> List[Dict[str, Any]]:
        """
        Load test dataset from JSON file.
        
        Args:
            dataset_path: Path to test dataset JSON file
        
        Returns:
            List of test cases
        """
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
            logger.info(f"Loaded {len(dataset)} test cases from {dataset_path}")
            return dataset
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            raise
    
    def evaluate_query(
        self,
        query: str,
        ground_truth: Dict[str, Any],
        include_generation: bool = True,
        include_retrieval: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluate a single query.
        
        Args:
            query: User query
            ground_truth: Ground truth data with 'answer' and 'relevant_doc_ids'
            include_generation: Whether to compute generation metrics
            include_retrieval: Whether to compute retrieval metrics
        
        Returns:
            Dict containing evaluation results
        """
        if not self.system:
            logger.warning("No system instance - skipping actual RAG evaluation")
            return {}
        
        try:
            # Get RAG system response
            logger.debug(f"Evaluating query: {query[:50]}...")
            response = self.system.rag_engine.answer_question(query, student_context="")
            
            results = {
                'query': query,
                'generated_answer': response.get('answer', ''),
                'retrieved_docs': response.get('citations', [])
            }
            
            # Extract document IDs from retrieved docs
            retrieved_ids = [
                doc.get('source_file', f"doc_{i}")
                for i, doc in enumerate(results['retrieved_docs'])
            ]
            
            # Generation metrics
            if include_generation and 'ground_truth_answer' in ground_truth:
                gen_metrics = self.metrics.compute_all_generation_metrics(
                    reference=ground_truth['ground_truth_answer'],
                    generated=results['generated_answer']
                )
                results['generation_metrics'] = gen_metrics
            
            # Retrieval metrics
            if include_retrieval and 'relevant_doc_ids' in ground_truth:
                ret_metrics = self.metrics.compute_all_retrieval_metrics(
                    retrieved_ids=retrieved_ids,
                    relevant_ids=ground_truth['relevant_doc_ids'],
                    k_values=self.k_values
                )
                results['retrieval_metrics'] = ret_metrics
            
            logger.debug(f"Evaluation complete for query")
            return results
            
        except Exception as e:
            logger.error(f"Query evaluation failed: {e}")
            return {
                'query': query,
                'error': str(e)
            }
    
    def evaluate_dataset(
        self,
        test_dataset: List[Dict[str, Any]],
        include_generation: bool = True,
        include_retrieval: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluate entire test dataset.
        
        Args:
            test_dataset: List of test cases
            include_generation: Whether to compute generation metrics
            include_retrieval: Whether to compute retrieval metrics
        
        Returns:
            Dict containing per-query results and aggregate statistics
        """
        results = {
            'total_queries': len(test_dataset),
            'timestamp': datetime.now().isoformat(),
            'per_query_results': [],
            'aggregate_metrics': {}
        }
        
        logger.info(f"Starting evaluation of {len(test_dataset)} queries...")
        
        for i, test_case in enumerate(test_dataset):
            logger.info(f"Evaluating query {i+1}/{len(test_dataset)}: {test_case['id']}")
            
            query_result = self.evaluate_query(
                query=test_case['query'],
                ground_truth=test_case,
                include_generation=include_generation,
                include_retrieval=include_retrieval
            )
            query_result['test_id'] = test_case['id']
            query_result['category'] = test_case.get('category', 'unknown')
            
            results['per_query_results'].append(query_result)
        
        # Compute aggregate statistics
        results['aggregate_metrics'] = self._compute_aggregate_metrics(
            results['per_query_results'],
            include_generation,
            include_retrieval
        )
        
        logger.info("Evaluation complete")
        return results
    
    def _compute_aggregate_metrics(
        self,
        per_query_results: List[Dict[str, Any]],
        include_generation: bool,
        include_retrieval: bool
    ) -> Dict[str, Any]:
        """
        Compute aggregate statistics across all queries.
        
        Args:
            per_query_results: Results for each query
            include_generation: Whether generation metrics are included
            include_retrieval: Whether retrieval metrics are included
        
        Returns:
            Dict with mean, std, min, max for each metric
        """
        aggregates = {}
        
        # Aggregate generation metrics
        if include_generation:
            bleu_scores = []
            rouge_f1_scores = []
            bert_f1_scores = []
            
            for result in per_query_results:
                if 'generation_metrics' in result:
                    gen = result['generation_metrics']
                    bleu_scores.append(gen.get('bleu', 0))
                    rouge_f1_scores.append(gen['rouge_l'].get('f1', 0))
                    bert_f1_scores.append(gen['bertscore'].get('f1', 0))
            
            if bleu_scores:
                aggregates['generation'] = {
                    'bleu': self._compute_stats(bleu_scores),
                    'rouge_l_f1': self._compute_stats(rouge_f1_scores),
                    'bertscore_f1': self._compute_stats(bert_f1_scores)
                }
        
        # Aggregate retrieval metrics
        if include_retrieval:
            aggregates['retrieval'] = {}
            
            for k in self.k_values:
                precision_scores = []
                recall_scores = []
                hit_rate_scores = []
                
                for result in per_query_results:
                    if 'retrieval_metrics' in result:
                        ret = result['retrieval_metrics']
                        precision_scores.append(ret['precision'].get(k, 0))
                        recall_scores.append(ret['recall'].get(k, 0))
                        hit_rate_scores.append(ret['hit_rate'].get(k, 0))
                
                if precision_scores:
                    aggregates['retrieval'][f'precision@{k}'] = self._compute_stats(precision_scores)
                    aggregates['retrieval'][f'recall@{k}'] = self._compute_stats(recall_scores)
                    aggregates['retrieval'][f'hit_rate@{k}'] = self._compute_stats(hit_rate_scores)
        
        return aggregates
    
    def _compute_stats(self, values: List[float]) -> Dict[str, float]:
        """Compute statistical summary of values."""
        if not values:
            return {'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0}
        
        return {
            'mean': float(np.mean(values)),
            'std': float(np.std(values)),
            'min': float(np.min(values)),
            'max': float(np.max(values))
        }
    
    def save_results(
        self,
        results: Dict[str, Any],
        output_path: str
    ):
        """
        Save evaluation results to JSON file.
        
        Args:
            results: Evaluation results
            output_path: Path to save results
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Results saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            raise
    
    def generate_report(
        self,
        results: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate human-readable markdown report.
        
        Args:
            results: Evaluation results
            output_path: Optional path to save report
        
        Returns:
            Markdown formatted report
        """
        report_lines = [
            "# RAG System Evaluation Report\n",
            f"**Date**: {results['timestamp']}",
            f"**Total Queries**: {results['total_queries']}\n",
            "---\n"
        ]
        
        aggregates = results.get('aggregate_metrics', {})
        
        # Generation metrics
        if 'generation' in aggregates:
            report_lines.append("## Generation Quality Metrics\n")
            gen = aggregates['generation']
            
            report_lines.append("| Metric | Mean | Std | Min | Max |")
            report_lines.append("|--------|------|-----|-----|-----|")
            
            for metric_name, stats in gen.items():
                report_lines.append(
                    f"| {metric_name.upper()} | "
                    f"{stats['mean']:.4f} | "
                    f"{stats['std']:.4f} | "
                    f"{stats['min']:.4f} | "
                    f"{stats['max']:.4f} |"
                )
            
            report_lines.append("")
        
        # Retrieval metrics
        if 'retrieval' in aggregates:
            report_lines.append("## Retrieval Quality Metrics\n")
            ret = aggregates['retrieval']
            
            report_lines.append("| Metric | Mean | Std | Min | Max |")
            report_lines.append("|--------|------|-----|-----|-----|")
            
            for metric_name, stats in ret.items():
                report_lines.append(
                    f"| {metric_name} | "
                    f"{stats['mean']:.4f} | "
                    f"{stats['std']:.4f} | "
                    f"{stats['min']:.4f} | "
                    f"{stats['max']:.4f} |"
                )
            
            report_lines.append("")
        
        # Category breakdown
        report_lines.append("## Performance by Category\n")
        categories = {}
        for result in results.get('per_query_results', []):
            cat = result.get('category', 'unknown')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result)
        
        for category, cat_results in categories.items():
            report_lines.append(f"### {category.replace('_', ' ').title()}")
            report_lines.append(f"- Queries: {len(cat_results)}\n")
        
        report = "\n".join(report_lines)
        
        # Save if path provided
        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(report)
                logger.info(f"Report saved to {output_path}")
            except Exception as e:
                logger.error(f"Failed to save report: {e}")
        
        return report
