"""
RAG Retrieval Metrics

Evaluates retrieval quality using standard information retrieval metrics:
- Precision@k: Proportion of retrieved docs that are relevant
- Recall@k: Proportion of relevant docs that were retrieved
- Hit Rate@k: Did we get at least one relevant doc in top-k?
- MRR (Mean Reciprocal Rank): Average of 1/rank of first relevant doc
"""
from typing import List, Dict, Set, Any
import logging

logger = logging.getLogger(__name__)


class RAGMetrics:
    """Calculate retrieval metrics for RAG evaluation."""
    
    @staticmethod
    def precision_at_k(retrieved_docs: List[str], relevant_docs: Set[str], k: int) -> float:
        """
        Calculate Precision@k.
        
        Precision@k = (# relevant docs in top-k) / k
        
        Args:
            retrieved_docs: List of retrieved document IDs (ordered by relevance)
            relevant_docs: Set of IDs of truly relevant documents
            k: Number of top results to consider
            
        Returns:
            Precision@k score (0.0 to 1.0)
        """
        if k <= 0 or not retrieved_docs:
            return 0.0
        
        top_k = retrieved_docs[:k]
        relevant_in_top_k = sum(1 for doc in top_k if doc in relevant_docs)
        
        return relevant_in_top_k / k
    
    @staticmethod
    def recall_at_k(retrieved_docs: List[str], relevant_docs: Set[str], k: int) -> float:
        """
        Calculate Recall@k.
        
        Recall@k = (# relevant docs in top-k) / (total # relevant docs)
        
        Args:
            retrieved_docs: List of retrieved document IDs (ordered by relevance)
            relevant_docs: Set of IDs of truly relevant documents
            k: Number of top results to consider
            
        Returns:
            Recall@k score (0.0 to 1.0)
        """
        if not relevant_docs or k <= 0:
            return 0.0
        
        top_k = retrieved_docs[:k]
        relevant_in_top_k = sum(1 for doc in top_k if doc in relevant_docs)
        
        return relevant_in_top_k / len(relevant_docs)
    
    @staticmethod
    def hit_rate_at_k(retrieved_docs: List[str], relevant_docs: Set[str], k: int) -> float:
        """
        Calculate Hit Rate@k.
        
        Hit Rate@k = 1 if at least one relevant doc in top-k, else 0
        
        Args:
            retrieved_docs: List of retrieved document IDs (ordered by relevance)
            relevant_docs: Set of IDs of truly relevant documents
            k: Number of top results to consider
            
        Returns:
            1.0 if hit, 0.0 if miss
        """
        if k <= 0 or not retrieved_docs:
            return 0.0
        
        top_k = retrieved_docs[:k]
        return 1.0 if any(doc in relevant_docs for doc in top_k) else 0.0
    
    @staticmethod
    def mean_reciprocal_rank(retrieved_docs: List[str], relevant_docs: Set[str]) -> float:
        """
        Calculate Mean Reciprocal Rank (MRR).
        
        MRR = 1 / (rank of first relevant doc)
        
        Args:
            retrieved_docs: List of retrieved document IDs (ordered by relevance)
            relevant_docs: Set of IDs of truly relevant documents
            
        Returns:
            MRR score (0.0 to 1.0)
        """
        if not retrieved_docs or not relevant_docs:
            return 0.0
        
        for rank, doc in enumerate(retrieved_docs, start=1):
            if doc in relevant_docs:
                return 1.0 / rank
        
        return 0.0  # No relevant docs found
    
    @staticmethod
    def evaluate_query(
        retrieved_docs: List[str],
        relevant_docs: Set[str],
        k_values: List[int] = [1, 3, 5, 10]
    ) -> Dict[str, Any]:
        """
        Evaluate a single query across multiple metrics and k values.
        
        Args:
            retrieved_docs: List of retrieved document IDs
            relevant_docs: Set of truly relevant document IDs
            k_values: List of k values to evaluate
            
        Returns:
            Dictionary with all metrics
        """
        results = {
            "precision": {},
            "recall": {},
            "hit_rate": {},
            "mrr": RAGMetrics.mean_reciprocal_rank(retrieved_docs, relevant_docs),
            "num_retrieved": len(retrieved_docs),
            "num_relevant": len(relevant_docs)
        }
        
        for k in k_values:
            results["precision"][f"@{k}"] = RAGMetrics.precision_at_k(retrieved_docs, relevant_docs, k)
            results["recall"][f"@{k}"] = RAGMetrics.recall_at_k(retrieved_docs, relevant_docs, k)
            results["hit_rate"][f"@{k}"] = RAGMetrics.hit_rate_at_k(retrieved_docs, relevant_docs, k)
        
        return results
    
    @staticmethod
    def aggregate_results(query_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate results across multiple queries.
        
        Args:
            query_results: List of results from evaluate_query()
            
        Returns:
            Aggregated metrics with means
        """
        if not query_results:
            return {}
        
        # Initialize aggregates
        precision_agg = {}
        recall_agg = {}
        hit_rate_agg = {}
        mrr_scores = []
        
        # Collect metrics
        for result in query_results:
            for k, score in result["precision"].items():
                if k not in precision_agg:
                    precision_agg[k] = []
                precision_agg[k].append(score)
            
            for k, score in result["recall"].items():
                if k not in recall_agg:
                    recall_agg[k] = []
                recall_agg[k].append(score)
            
            for k, score in result["hit_rate"].items():
                if k not in hit_rate_agg:
                    hit_rate_agg[k] = []
                hit_rate_agg[k].append(score)
            
            mrr_scores.append(result["mrr"])
        
        # Calculate means
        aggregated = {
            "num_queries": len(query_results),
            "precision": {k: sum(scores) / len(scores) for k, scores in precision_agg.items()},
            "recall": {k: sum(scores) / len(scores) for k, scores in recall_agg.items()},
            "hit_rate": {k: sum(scores) / len(scores) for k, scores in hit_rate_agg.items()},
            "mrr": sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0
        }
        
        return aggregated


def format_metrics_report(aggregated: Dict[str, Any]) -> str:
    """
    Format aggregated metrics into a readable report.
    
    Args:
        aggregated: Results from aggregate_results()
        
    Returns:
        Formatted string report
    """
    report = []
    report.append("=" * 60)
    report.append("RAG RETRIEVAL METRICS REPORT")
    report.append("=" * 60)
    report.append(f"Queries Evaluated: {aggregated['num_queries']}")
    report.append("")
    
    report.append("PRECISION@k:")
    for k, score in sorted(aggregated['precision'].items()):
        report.append(f"  {k}: {score:.3f}")
    report.append("")
    
    report.append("RECALL@k:")
    for k, score in sorted(aggregated['recall'].items()):
        report.append(f"  {k}: {score:.3f}")
    report.append("")
    
    report.append("HIT RATE@k:")
    for k, score in sorted(aggregated['hit_rate'].items()):
        report.append(f"  {k}: {score:.3f}")
    report.append("")
    
    report.append(f"MRR (Mean Reciprocal Rank): {aggregated['mrr']:.3f}")
    report.append("=" * 60)
    
    return "\n".join(report)
