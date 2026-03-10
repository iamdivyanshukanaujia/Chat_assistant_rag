"""
Advising Quality Scorer

Uses LLM-as-Judge to evaluate advising quality on 5 dimensions:
1. Relevance: Does answer address the question?
2. Correctness: Is information accurate?
3. Personalization: Uses student context appropriately?
4. Non-hallucination: Only uses retrieved information?
5. Policy Consistency: Matches university policies?

Each dimension scored 1-5.
"""
from typing import Dict, Any, List
import logging
from langchain_openai import AzureChatOpenAI
from langchain_ollama import ChatOllama
from src.config import settings

logger = logging.getLogger(__name__)


class AdvisingQualityScorer:
    """LLM-as-judge scoring for advising quality."""
    
    EVALUATION_PROMPT_TEMPLATE = """You are an expert evaluator of university AI assistant responses.

Evaluate the following response on 5 dimensions (score 1-5 for each):

**Query:** {query}

**Student Context:** {student_context}

**Generated Response:** {response}

**Retrieved Sources:** {sources}

**Evaluation Criteria:**

1. **Relevance (1-5)**: Does the response directly address the student's question?
   - 5: Perfectly answers the question
   - 3: Partially answers
   - 1: Completely off-topic

2. **Correctness (1-5)**: Is the information factually accurate based on the sources?
   - 5: Fully accurate
   - 3: Mostly accurate with minor errors
   - 1: Significant inaccuracies

3. **Personalization (1-5)**: Does it use student context appropriately?
   - 5: Perfectly tailored to student (program/year/etc)
   - 3: Some personalization
   - 1: Generic, no personalization

4. **Non-hallucination (1-5)**: Does it only use information from sources?
   - 5: All info from sources, no made-up content
   - 3: Mostly from sources, minor speculation
   - 1: Significant hallucinated content

5. **Policy Consistency (1-5)**: Does it match university policies?
   - 5: Fully consistent with policy
   - 3: Mostly consistent
    - 1: Contradicts policy

Provide your evaluation in this EXACT format:
RELEVANCE: [score]
CORRECTNESS: [score]
PERSONALIZATION: [score]
NON_HALLUCINATION: [score]
POLICY_CONSISTENCY: [score]
REASONING: [brief explanation]
"""
    
    def __init__(self):
        """Initialize LLM for evaluation."""
        if settings.llm_provider == "azure" and settings.azure_openai_api_key:
            self.llm = AzureChatOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                azure_deployment=settings.azure_openai_deployment,
                api_version=settings.azure_openai_api_version,
                temperature=0.0  # Deterministic scoring
            )
            logger.info("Using Azure GPT-4o for quality scoring")
        else:
            self.llm = ChatOllama(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
                temperature=0.0
            )
            logger.info("Using Ollama for quality scoring")
    
    def score_response(
        self,
        query: str,
        response: str,
        student_context: Dict[str, Any],
        sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Score a single response.
        
        Args:
            query: User's question
            response: Generated answer
            student_context: Student profile
            sources: Retrieved source documents
            
        Returns:
            Dictionary with scores for each dimension
        """
        # Format sources for prompt
        sources_text = "\n".join([
            f"- {src.get('content', '')}[:100]..."
            for src in sources[:3]  # Top 3 sources
        ])
        
        # Format student context
        context_text = f"Program: {student_context.get('program', 'N/A')}, Year: {student_context.get('year', 'N/A')}"
        
        # Build evaluation prompt
        prompt = self.EVALUATION_PROMPT_TEMPLATE.format(
            query=query,
            student_context=context_text,
            response=response,
            sources=sources_text
        )
        
        try:
            # Get LLM evaluation
            result = self.llm.invoke(prompt)
            evaluation_text = result.content
            
            # Parse scores
            scores = self._parse_evaluation(evaluation_text)
            
            # Calculate aggregate score
            scores['aggregate'] = sum([
                scores['relevance'],
                scores['correctness'],
                scores['personalization'],
                scores['non_hallucination'],
                scores['policy_consistency']
            ]) / 5.0
            
            return scores
            
        except Exception as e:
            logger.error(f"Error scoring response: {e}")
            return {
                "relevance": 0,
                "correctness": 0,
                "personalization": 0,
                "non_hallucination": 0,
                "policy_consistency": 0,
                "aggregate": 0.0,
                "reasoning": f"Error: {str(e)}"
            }
    
    def _parse_evaluation(self, evaluation_text: str) -> Dict[str, Any]:
        """Parse LLM evaluation output."""
        scores = {
            "relevance": 0,
            "correctness": 0,
            "personalization": 0,
            "non_hallucination": 0,
            "policy_consistency": 0,
            "reasoning": ""
        }
        
        lines = evaluation_text.split('\n')
        for line in lines:
            line = line.strip()
            
            if line.startswith("RELEVANCE:"):
                try:
                    scores["relevance"] = int(line.split(':')[1].strip())
                except:
                    pass
            elif line.startswith("CORRECTNESS:"):
                try:
                    scores["correctness"] = int(line.split(':')[1].strip())
                except:
                    pass
            elif line.startswith("PERSONALIZATION:"):
                try:
                    scores["personalization"] = int(line.split(':')[1].strip())
                except:
                    pass
            elif line.startswith("NON_HALLUCINATION:"):
                try:
                    scores["non_hallucination"] = int(line.split(':')[1].strip())
                except:
                    pass
            elif line.startswith("POLICY_CONSISTENCY:"):
                try:
                    scores["policy_consistency"] = int(line.split(':')[1].strip())
                except:
                    pass
            elif line.startswith("REASONING:"):
                scores["reasoning"] = line.split(':', 1)[1].strip()
        
        return scores
    
    def score_batch(
        self,
        evaluations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Score multiple responses and aggregate.
        
        Args:
            evaluations: List of dicts with query, response, context, sources
            
        Returns:
            Aggregated scores
        """
        all_scores = []
        
        for eval_data in evaluations:
            scores = self.score_response(
                query=eval_data['query'],
                response=eval_data['response'],
                student_context=eval_data.get('student_context', {}),
                sources=eval_data.get('sources', [])
            )
            all_scores.append(scores)
        
        # Aggregate
        if not all_scores:
            return {}
        
        aggregated = {
            "num_responses": len(all_scores),
            "relevance_mean": sum(s['relevance'] for s in all_scores) / len(all_scores),
            "correctness_mean": sum(s['correctness'] for s in all_scores) / len(all_scores),
            "personalization_mean": sum(s['personalization'] for s in all_scores) / len(all_scores),
            "non_hallucination_mean": sum(s['non_hallucination'] for s in all_scores) / len(all_scores),
            "policy_consistency_mean": sum(s['policy_consistency'] for s in all_scores) / len(all_scores),
            "aggregate_mean": sum(s['aggregate'] for s in all_scores) / len(all_scores)
        }
        
        return aggregated


def format_advising_report(results: Dict[str, Any]) -> str:
    """Format advising quality results into a report."""
    report = []
    report.append("=" * 60)
    report.append("ADVISING QUALITY REPORT")
    report.append("=" * 60)
    report.append(f"Responses Evaluated: {results['num_responses']}")
    report.append("")
    
    report.append("QUALITY DIMENSIONS (1-5 scale):")
    report.append(f"  Relevance:          {results['relevance_mean']:.2f}")
    report.append(f"  Correctness:        {results['correctness_mean']:.2f}")
    report.append(f"  Personalization:    {results['personalization_mean']:.2f}")
    report.append(f"  Non-hallucination:  {results['non_hallucination_mean']:.2f}")
    report.append(f"  Policy Consistency: {results['policy_consistency_mean']:.2f}")
    report.append("")
    report.append(f"AGGREGATE SCORE: {results['aggregate_mean']:.2f} / 5.0")
    
    # Quality assessment
    avg = results['aggregate_mean']
    if avg >= 4.5:
        status = "✅ EXCELLENT"
    elif avg >= 3.5:
        status = "⚠️ GOOD"
    elif avg >= 2.5:
        status = "⚠️ ACCEPTABLE"
    else:
        status = "❌ POOR"
    
    report.append(f"Overall: {status}")
    report.append("=" * 60)
    
    return "\n".join(report)
