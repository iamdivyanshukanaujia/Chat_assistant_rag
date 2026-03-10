"""
Core RAG engine integrating retrieval, reranking, LLM, and caching.
"""
from typing import Dict, Any, List, Optional, Tuple
import time

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.utils.logger import get_logger
from src.utils.exceptions import RAGError, LLMError
from src.config import settings
from src.chunking import SemanticChunk
from src.retrieval import HybridRetriever, CrossEncoderReranker
from src.caching import CacheManager

# Guardrails disabled for Python 3.14 compatibility
InputGuardrails = None
OutputGuardrails = None

logger = get_logger(__name__)


class RAGEngine:
    """Core RAG engine coordinating all components."""
    
    def __init__(
        self,
        hybrid_retriever: HybridRetriever,
        reranker: CrossEncoderReranker,
        cache_manager: Optional[CacheManager] = None,
        input_guardrails: Optional[Any] = None,
        output_guardrails: Optional[Any] = None,
        memory_manager: Optional[Any] = None
    ):
        """Initialize RAG engine."""
        self.hybrid_retriever = hybrid_retriever
        self.reranker = reranker
        self.cache_manager = cache_manager or CacheManager()
        self.memory_manager = memory_manager
        
        # Guardrails disabled
        self.input_guardrails = None
        self.output_guardrails = None
        
        # Initialize LLM based on provider
        if settings.llm_provider == "azure" and settings.azure_openai_api_key:
            try:
                from langchain_openai import AzureChatOpenAI
                logger.info("Initializing Azure OpenAI...")
                self.llm = AzureChatOpenAI(
                    azure_endpoint=settings.azure_openai_endpoint,
                    api_key=settings.azure_openai_api_key,
                    azure_deployment=settings.azure_openai_deployment,
                    api_version=settings.azure_openai_api_version,
                    temperature=settings.ollama_temperature,
                    max_tokens=2000
                )
                logger.info(f"✅ Using Azure OpenAI: {settings.azure_openai_deployment}")
            except Exception as e:
                logger.warning(f"⚠️ Azure OpenAI failed: {e}. Falling back to Ollama.")
                self.llm = ChatOllama(
                    base_url=settings.ollama_base_url,
                    model=settings.ollama_model,
                    temperature=settings.ollama_temperature
                )
        else:
            # Use Ollama
            logger.info("Using Ollama (local model)")
            self.llm = ChatOllama(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
                temperature=settings.ollama_temperature
            )
        
        # Create RAG prompt template
        self.rag_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful university advisor who knows the policies and procedures.

**CRITICAL: Check Student Profile FIRST!**

Student Profile:
{student_context}

**VALIDATION RULES:**
1. If student asks about "my syllabus/fees/courses", verify the information matches their program (BTech/MTech/PhD/MBA)
2. If retrieved information is for a DIFFERENT program than the student's, DO NOT use it - say "I don't have that information for your program"
3. ALWAYS prioritize information matching the student's program level

**Response Rules:**
1. Answer directly and naturally
2. DO NOT say "according to documents" or mention sources
3. DO NOT give information for wrong programs (e.g., MTech info to BTech student)
4. If unsure or no matching info, say "Check with your academic advisor for details specific to your program"

**Example:**
✅ GOOD: "For BTech CSE Year 3, you'll be taking courses like..." (matches student)
❌ BAD: "According to MTech syllabus..." (wrong program for BTech student)

{conversation_history}

Information retrieved:
{context}"""),
            ("human", "{question}")
        ])
        
        logger.info("Initialized RAG Engine")
    
    def _validate_input(self, query: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate input (disabled)."""
        return True, None, None
    
    def _validate_output(self, output: Dict[str, Any]) -> Tuple[bool, Optional[str], List[str]]:
        """Validate output (disabled)."""
        return True, None, []
    
    def _format_context(self, chunks: List[Tuple[SemanticChunk, float]]) -> Tuple[str, List[Dict]]:
        """Format retrieved chunks into context string and citations."""
        context_parts = []
        citations = []
        
        for i, (chunk, score) in enumerate(chunks, 1):
            context_parts.append(
                f"[Reference {i}] {chunk.section_title}\n"
                f"{chunk.content}\n"
            )
            
            citations.append({
                "source_id": i,
                "source_file": chunk.source_file,
                "section_title": chunk.section_title,
                "subsection": chunk.subsection,
                "program_level": chunk.program_level,
                "category": chunk.category,
                "content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                "relevance_score": float(score)
            })
        
        context_string = "\n".join(context_parts)
        return context_string, citations
    
    def _enrich_query(self, query: str, student_profile: Dict[str, Any]) -> str:
        """Enrich query with student context."""
        program = student_profile.get("program", "")
        department = student_profile.get("department", "")
        year = student_profile.get("year", "")
        
        personal_keywords = ["my", "our", "me", "i", "i'm", "we"]
        is_personal = any(keyword in query.lower().split() for keyword in personal_keywords)
        
        if is_personal and program:
            enriched = f"{query} for {program}"
            if department:
                enriched += f" {department}"
            if year:
                enriched += f" year {year}"
            logger.info(f"Enriched query: '{query}' → '{enriched}'")
            return enriched
        
        return query
    
    def retrieve_and_rerank(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> List[Tuple[SemanticChunk, float]]:
        """Perform hybrid retrieval and reranking."""
        start_time = time.time()
        
        candidates = self.hybrid_retriever.retrieve(query)
        reranked = self.reranker.rerank(query, candidates, top_k=top_k)
        
        duration = time.time() - start_time
        logger.info(f"Retrieval + reranking completed in {duration:.2f}s")
        
        return reranked
    
    def generate_answer(
        self,
        query: str,
        context: str,
        student_context: str = "",
        conversation_history: str = "",
        citations: List[Dict] = None
    ) -> Dict[str, Any]:
        """Generate answer using LLM."""
        try:
            chain = self.rag_prompt | self.llm | StrOutputParser()
            
            answer = chain.invoke({
                "question": query,
                "context": context,
                "student_context": student_context or "No student context available.",
                "conversation_history": conversation_history or ""
            })
            
            confidence = 0.7
            if "I don't have" in answer or "don't know" in answer:
                confidence = 0.3
            elif len(answer) > 100:
                confidence = 0.8
            if citations and len(citations) > 0:
                confidence = min(confidence + 0.1, 1.0)
            
            return {
                "answer": answer,
                "citations": citations or [],
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}", exc_info=True)
            raise LLMError(f"Failed to generate answer: {str(e)}")
    
    def answer_question(
        self,
        query: str,
        session_id: str,
        use_cache: bool = True,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """Main method to answer a question."""
        try:
            start_time = time.time()
            
            # Input validation (disabled)
            is_valid, error_msg, disclaimer = self._validate_input(query)
            if not is_valid:
                return {"answer": error_msg, "citations": [], "confidence": 0.0}
            
            # Get student profile
            student_profile = {}
            student_context = ""
            if self.memory_manager:
                try:
                    entities = self.memory_manager.get_entities(session_id)
                    student_profile = entities.get("profile", {})
                    if student_profile:
                        student_context = f"Program: {student_profile.get('program', 'Unknown')}, Department: {student_profile.get('department', 'Unknown')}, Year: {student_profile.get('year', 'Unknown')}"
                except Exception as e:
                    logger.warning(f"Could not load student profile: {e}")
            
            # Enrich query
            enriched_query = self._enrich_query(query, student_profile)
            
            # Check cache
            if use_cache and self.cache_manager:
                cached = self.cache_manager.get_answer(enriched_query)
                if cached:
                    logger.info(f"Cache hit for query: {enriched_query[:50]}...")
                    return cached
            
            # Retrieve and rerank
            reranked_chunks = self.retrieve_and_rerank(enriched_query, top_k=top_k)
            
            # Format context
            context, citations = self._format_context(reranked_chunks)
            
            # Load conversation history
            conversation_history = ""
            if self.memory_manager:
                try:
                    history_obj = self.memory_manager.get_message_history(session_id)
                    messages = history_obj.messages[-6:] if hasattr(history_obj, 'messages') else []
                    if messages:
                        history_parts = []
                        for msg in messages:
                            role = "Student" if msg.type == "human" else "Advisor"
                            history_parts.append(f"{role}: {msg.content}")
                        conversation_history = "\n".join(history_parts)
                except Exception as e:
                    logger.warning(f"Could not load conversation history: {e}")
            
            # Generate answer
            result = self.generate_answer(
                query=query,
                context=context,
                student_context=student_context,
                conversation_history=conversation_history,
                citations=citations
            )
            
            # Output validation (disabled)
            is_valid_output, output_error, warnings = self._validate_output(result)
            
            # Cache result
            if use_cache and self.cache_manager:
                try:
                    self.cache_manager.set_answer(
                        enriched_query, 
                        result["answer"], 
                        result.get("citations", []),
                        result.get("confidence", 0.7)
                    )
                except Exception as e:
                    logger.warning(f"Failed to cache result: {e}")
            
            # Save to conversation history
            if self.memory_manager:
                try:
                    history_obj = self.memory_manager.get_message_history(session_id)
                    from langchain_core.messages import HumanMessage, AIMessage
                    history_obj.add_message(HumanMessage(content=query))
                    history_obj.add_message(AIMessage(content=result["answer"]))
                    logger.info(f"Saved conversation for session {session_id}")
                except Exception as e:
                    logger.error(f"Failed to save conversation: {e}", exc_info=True)
            
            # Extract entities
            if self.memory_manager and student_profile.get("student_id"):
                try:
                    self.memory_manager.extract_and_save_entities(
                        query,
                        result["answer"],
                        session_id
                    )
                except Exception as e:
                    logger.warning(f"Entity extraction failed: {e}")
            
            duration = time.time() - start_time
            logger.info(f"Total query processing time: {duration:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"RAG pipeline failed: {e}", exc_info=True)
            raise RAGError(f"Failed to process query: {str(e)}")
