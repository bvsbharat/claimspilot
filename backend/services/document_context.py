"""
Document Context Manager
Stores and manages document processing history and extracted data for RAG
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DocumentContextManager:
    """Manages document context for claims"""

    def __init__(self):
        self.contexts: Dict[str, Dict[str, Any]] = {}

    def add_context(
        self,
        claim_id: str,
        raw_text: str,
        structured_data: Dict[str, Any],
        document_type: str = "unknown",
        file_path: Optional[str] = None,
        tables: Optional[List[Dict]] = None
    ):
        """
        Add or update document context for a claim

        Args:
            claim_id: Claim identifier
            raw_text: Raw extracted text from LandingAI
            structured_data: Structured claim data
            document_type: Type of document (acord, police_report, etc.)
            file_path: Path to original document
            tables: Extracted tables if any
        """
        try:
            self.contexts[claim_id] = {
                "claim_id": claim_id,
                "raw_text": raw_text,
                "structured_data": structured_data,
                "document_type": document_type,
                "file_path": file_path,
                "tables": tables or [],
                "added_at": datetime.now().isoformat(),
                "char_count": len(raw_text),
                "has_tables": bool(tables)
            }
            logger.info(f"Added context for claim {claim_id} ({len(raw_text)} chars, {len(tables or [])} tables)")
        except Exception as e:
            logger.error(f"Failed to add context for {claim_id}: {e}")

    def get_context(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Get document context for a specific claim"""
        return self.contexts.get(claim_id)

    def get_raw_text(self, claim_id: str) -> Optional[str]:
        """Get just the raw extracted text"""
        context = self.contexts.get(claim_id)
        return context.get("raw_text") if context else None

    def get_structured_data(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Get just the structured data"""
        context = self.contexts.get(claim_id)
        return context.get("structured_data") if context else None

    def get_all_claim_ids(self) -> List[str]:
        """Get list of all claim IDs with context"""
        return list(self.contexts.keys())

    def get_stats(self) -> Dict[str, Any]:
        """Get context manager statistics"""
        return {
            "total_contexts": len(self.contexts),
            "claim_ids": list(self.contexts.keys()),
            "total_chars": sum(ctx.get("char_count", 0) for ctx in self.contexts.values()),
            "with_tables": sum(1 for ctx in self.contexts.values() if ctx.get("has_tables"))
        }

    def search_contexts(self, query: str) -> List[Dict[str, Any]]:
        """Simple search through contexts by keyword"""
        query_lower = query.lower()
        results = []

        for claim_id, context in self.contexts.items():
            raw_text = context.get("raw_text", "").lower()
            if query_lower in raw_text:
                results.append({
                    "claim_id": claim_id,
                    "document_type": context.get("document_type"),
                    "preview": context.get("raw_text", "")[:200] + "..."
                })

        return results


# Singleton instance
_document_context_manager = None


def get_document_context_manager() -> DocumentContextManager:
    """Get or create document context manager instance"""
    global _document_context_manager
    if _document_context_manager is None:
        _document_context_manager = DocumentContextManager()
    return _document_context_manager
