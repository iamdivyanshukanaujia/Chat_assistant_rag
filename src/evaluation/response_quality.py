"""
Response Quality Evaluation

Measures quality of generated responses using:
- ROUGE-L: Longest common subsequence similarity  
- BLEU: N-gram overlap (1-4 grams)
- BERTScore: Semantic similarity using embeddings

Requires reference answers for comparison.
"""
from typing  import Dict, List, Any
import logging

try:
    from rouge_score import rouge_scorer
    ROUGE_AVAILABLE = True
except ImportError:
    ROUGE_AVAILABLE = False
    logging.warning("rouge-score not installed. Install with: pip install rouge-score")

try:
    import nltk
    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logging.warning("nltk not installed. Install with: pip install nltk")

try:
    from bert_score import score as bert_score
    BERT_AVAILABLE = True
except ImportError:
    BERT_AVAILABLE = False
    logging.warning("bert-score not installed. Install with: pip install bert-score")

logger = logging.getLogger(__name__)


class ResponseQualityEvaluator:
    """Evaluate response quality against reference answers."""
    
    def __init__(self):
        if ROUGE_AVAILABLE:
            self.rouge_scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
        else:
            self.rouge_scorer = None
        
        if NLTK_AVAILABLE:
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                logger.info("Downloading NLTK punkt tokenizer...")
                nltk.download('punkt', quiet=True)
        
        self.smoothing = SmoothingFunction().method1 if NLTK_AVAILABLE else None
    
    def calculate_rouge_l(self, generated: str, reference: str) -> float:
        """
        Calculate ROUGE-L score.
        
        Args:
            generated: Generated response
            reference: Reference answer
            
        Returns:
            ROUGE-L F1 score (0.0 to 1.0)
        """
        if not ROUGE_AVAILABLE or not self.rouge_scorer:
            logger.warning("ROUGE not available")
            return 0.0
        
        scores = self.rouge_scorer.score(reference, generated)
        return scores['rougeL'].fmeasure
    
    def calculate_bleu(self, generated: str, reference: str) -> float:
        """
        Calculate BLEU score.
        
        Args:
            generated: Generated response
            reference: Reference answer
            
        Returns:
            BLEU score (0.0 to 1.0)
        """
        if not NLTK_AVAILABLE:
            logger.warning("NLTK not available")
            return 0.0
        
        # Tokenize
        reference_tokens = nltk.word_tokenize(reference.lower())
        generated_tokens = nltk.word_tokenize(generated.lower())
        
        # Calculate BLEU with smoothing
        score = sentence_bleu(
            [reference_tokens],
            generated_tokens,
            smoothing_function=self.smoothing
        )
        
        return score
    
    def calculate_bert_score(
        self,
        generated: List[str],
        references: List[str],
        model_type: str = "microsoft/deberta-xlarge-mnli"
    ) -> Dict[str, Any]:
        """
        Calculate BERTScore.
        
        Args:
            generated: List of generated responses
            references: List of reference answers
            model_type: BERT model to use
            
        Returns:
            Dictionary with P, R, F1 scores
        """
        if not BERT_AVAILABLE:
            logger.warning("BERTScore not available")
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
        
        try:
            P, R, F1 = bert_score(generated, references, model_type=model_type, verbose=False)
            
            return {
                "precision": float(P.mean()),
                "recall": float(R.mean()),
                "f1": float(F1.mean())
            }
        except Exception as e:
            logger.error(f"BERTScore calculation failed: {e}")
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    
    def evaluate_response(
        self,
        generated: str,
        reference: str,
        include_bert: bool = False
    ) -> Dict[str, float]:
        """
        Evaluate a single response against reference.
        
        Args:
            generated: Generated response
            reference: Reference answer
            include_bert: Whether to calculate BERTScore (slower)
            
        Returns:
            Dictionary with all scores
        """
        results = {
            "rouge_l": self.calculate_rouge_l(generated, reference),
            "bleu": self.calculate_bleu(generated, reference)
        }
        
        if include_bert:
            bert_scores = self.calculate_bert_score([generated], [reference])
            results["bert_f1"] = bert_scores["f1"]
            results["bert_precision"] = bert_scores["precision"]
            results["bert_recall"] = bert_scores["recall"]
        
        return results
    
    def evaluate_batch(
        self,
        generated_responses: List[str],
        reference_answers: List[str],
        include_bert: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluate multiple responses.
        
        Args:
            generated_responses: List of generated responses
            reference_answers: List of reference answers
            include_bert: Whether to calculate BERTScore
            
        Returns:
            Aggregated scores
        """
        if len(generated_responses) != len(reference_answers):
            raise ValueError("Generated and reference lists must be same length")
        
        rouge_scores = []
        bleu_scores = []
        
        for gen, ref in zip(generated_responses, reference_answers):
            result = self.evaluate_response(gen, ref, include_bert=False)
            rouge_scores.append(result["rouge_l"])
            bleu_scores.append(result["bleu"])
        
        aggregated = {
            "num_responses": len(generated_responses),
            "rouge_l_mean": sum(rouge_scores) / len(rouge_scores) if rouge_scores else 0.0,
            "bleu_mean": sum(bleu_scores) / len(bleu_scores) if bleu_scores else 0.0
        }
        
        # Calculate BERTScore in batch (more efficient)
        if include_bert:
            bert_scores = self.calculate_bert_score(generated_responses, reference_answers)
            aggregated.update({
                "bert_f1_mean": bert_scores["f1"],
                "bert_precision_mean": bert_scores["precision"],
                "bert_recall_mean": bert_scores["recall"]
            })
        
        return aggregated


def format_quality_report(results: Dict[str, Any]) -> str:
    """
    Format response quality results into a report.
    
    Args:
        results: Results from evaluate_batch()
        
    Returns:
        Formatted string report
    """
    report = []
    report.append("=" * 60)
    report.append("RESPONSE QUALITY REPORT")
    report.append("=" * 60)
    report.append(f"Responses Evaluated: {results['num_responses']}")
    report.append("")
    
    report.append("ROUGE-L (Longest Common Subsequence):")
    report.append(f"  Mean F1: {results['rouge_l_mean']:.3f}")
    report.append("")
    
    report.append("BLEU (N-gram Overlap):")
    report.append(f"  Mean Score: {results['bleu_mean']:.3f}")
    report.append("")
    
    if 'bert_f1_mean' in results:
        report.append("BERTScore (Semantic Similarity):")
        report.append(f"  Mean F1:        {results['bert_f1_mean']:.3f}")
        report.append(f"  Mean Precision: {results['bert_precision_mean']:.3f}")
        report.append(f"  Mean Recall:    {results['bert_recall_mean']:.3f}")
        report.append("")
    
    # Overall quality assessment
    avg_score = (results['rouge_l_mean'] + results['bleu_mean']) / 2
    if avg_score >= 0.7:
        status = "EXCELLENT"
    elif avg_score >= 0.5:
        status = "GOOD"
    elif avg_score >= 0.3:
        status = "ACCEPTABLE"
    else:
        status = "POOR"
    
    report.append(f"Overall Quality: {status} (avg: {avg_score:.3f})")
    report.append("=" * 60)
    
    return "\n".join(report)
