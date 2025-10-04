"""
Pathway Real-time RAG Service
Provides question-answering capabilities over claim documents using real-time vector indexing
"""

import os
import logging
import threading
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import pathway as pw
    from pathway.xpacks.llm import embedders, prompts
    from pathway.xpacks.llm.llms import OpenAIChat
    from pathway.xpacks.llm.vector_store import VectorStoreServer
    PATHWAY_AVAILABLE = True
except ImportError:
    logger.warning("Pathway LLM xpack not available")
    PATHWAY_AVAILABLE = False


class RAGService:
    """Real-time RAG service using Pathway for always up-to-date knowledge"""

    def __init__(self, data_dir: str = "./uploads", host: str = "127.0.0.1", port: int = 8765):
        self.data_dir = data_dir
        self.host = host
        self.port = port
        self.documents_cache: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self._cache_lock = threading.Lock()  # Thread-safe cache access

        # Initialize OpenAI client for Q&A
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set - RAG service will not function")

    def add_document(self, claim_id: str, document_text: str, metadata: Dict[str, Any]):
        """Add a document to the RAG cache for querying (thread-safe)"""
        try:
            with self._cache_lock:
                self.documents_cache[claim_id] = {
                    "text": document_text,
                    "metadata": metadata,
                    "chunks": self._chunk_text(document_text)
                }
                total_docs = len(self.documents_cache)

            logger.info(f"✅ [RAG] Added document for claim {claim_id} to RAG cache ({len(document_text)} chars). Total docs: {total_docs}")
            logger.debug(f"[RAG] Current cache keys: {list(self.documents_cache.keys())}")
        except Exception as e:
            logger.error(f"❌ [RAG] Failed to add document to RAG: {e}")

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Simple text chunking with overlap"""
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += (chunk_size - overlap)

        return chunks

    async def query(
        self,
        question: str,
        claim_id: Optional[str] = None,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Query the RAG system with a question (thread-safe)

        Args:
            question: User's question
            claim_id: Optional claim ID to scope the query
            top_k: Number of relevant chunks to retrieve

        Returns:
            Answer with sources and context
        """
        try:
            # Get relevant documents with thread-safe access
            with self._cache_lock:
                total_docs = len(self.documents_cache)
                cache_keys = list(self.documents_cache.keys())

                if claim_id and claim_id in self.documents_cache:
                    relevant_docs = [self.documents_cache[claim_id]]
                else:
                    relevant_docs = list(self.documents_cache.values())

            logger.info(f"🔍 [RAG] Query received: '{question[:50]}...' | Claim ID: {claim_id} | Total docs in cache: {total_docs}")
            logger.debug(f"[RAG] Available cache keys: {cache_keys}")

            if not relevant_docs:
                logger.warning(f"⚠️ [RAG] No documents in cache to query!")
                return {
                    "answer": "No documents available yet. Please upload and process claims first.",
                    "sources": [],
                    "context": []
                }

            # Simple retrieval: get all chunks and use OpenAI for Q&A
            all_chunks = []
            for doc in relevant_docs[:5]:  # Limit to 5 most recent docs
                chunks = doc.get("chunks", [])
                for i, chunk in enumerate(chunks[:top_k]):
                    all_chunks.append({
                        "text": chunk,
                        "claim_id": doc.get("metadata", {}).get("claim_id"),
                        "index": i
                    })

            # Build context for LLM
            context_text = "\n\n---\n\n".join([
                f"Document {i+1} (Claim: {chunk['claim_id']}):\n{chunk['text'][:800]}"
                for i, chunk in enumerate(all_chunks[:top_k])
            ])

            # Query OpenAI
            import openai
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            system_prompt = """You are a helpful insurance claims assistant. Answer questions about insurance claims based on the provided context.
If the context doesn't contain relevant information, say so clearly. Always cite which document or claim you're referring to."""

            user_prompt = f"""Context from claim documents:

{context_text}

Question: {question}

Please provide a detailed answer based on the context above."""

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            answer = response.choices[0].message.content

            # Extract sources
            sources = [
                {
                    "claim_id": chunk["claim_id"],
                    "text_preview": chunk["text"][:200] + "..."
                }
                for chunk in all_chunks[:top_k]
            ]

            return {
                "answer": answer,
                "sources": sources,
                "context": all_chunks[:top_k],
                "model": "gpt-4o"
            }

        except Exception as e:
            logger.error(f"RAG query failed: {e}", exc_info=True)
            return {
                "answer": f"Sorry, I encountered an error: {str(e)}",
                "sources": [],
                "context": [],
                "error": str(e)
            }

    async def get_claim_context(self, claim_id: str) -> Dict[str, Any]:
        """Get all context for a specific claim (thread-safe)"""
        with self._cache_lock:
            if claim_id not in self.documents_cache:
                logger.warning(f"⚠️ [RAG] Claim {claim_id} not found in RAG cache")
                return {"error": "Claim not found in RAG cache"}

            doc = self.documents_cache[claim_id]
            result = {
                "claim_id": claim_id,
                "text": doc["text"],
                "metadata": doc["metadata"],
                "chunks_count": len(doc.get("chunks", [])),
                "char_count": len(doc["text"])
            }

        logger.debug(f"[RAG] Retrieved context for claim {claim_id}")
        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get RAG service statistics (thread-safe)"""
        with self._cache_lock:
            stats = {
                "documents_cached": len(self.documents_cache),
                "total_claims": list(self.documents_cache.keys()),
                "running": self.running
            }
        return stats


# Singleton instance with thread-safe creation
_rag_service = None
_rag_service_lock = threading.Lock()


def get_rag_service() -> RAGService:
    """Get or create RAG service instance (thread-safe singleton)"""
    global _rag_service
    if _rag_service is None:
        with _rag_service_lock:
            # Double-check locking pattern
            if _rag_service is None:
                logger.info("🔧 [RAG] Initializing RAG service singleton")
                _rag_service = RAGService()
                logger.info("✅ [RAG] RAG service singleton created")
    return _rag_service
