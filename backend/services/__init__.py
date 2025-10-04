"""
Services initialization
"""

from .mongodb_service import get_mongodb_service
from .pinecone_service import get_pinecone_service
from .document_processor import get_document_processor
from .claim_scorer import ClaimScorer, get_claim_scorer
from .fraud_detector import FraudDetector, get_fraud_detector
from .router_engine import RouterEngine, get_router_engine
from .pathway_pipeline import PathwayPipeline, get_pathway_pipeline
from .event_queue import EventQueue, get_event_queue
from .auto_processor import AutoProcessor, get_auto_processor
from .rag_service import RAGService, get_rag_service
from .document_context import DocumentContextManager, get_document_context_manager
from .gmail_service import GmailService, get_gmail_service
from .pdf_generator import PDFGenerator, get_pdf_generator
from .gmail_auto_fetch import GmailAutoFetchService, get_gmail_auto_fetch_service

__all__ = [
    "get_mongodb_service",
    "get_pinecone_service",
    "get_document_processor",
    "ClaimScorer",
    "get_claim_scorer",
    "FraudDetector",
    "get_fraud_detector",
    "RouterEngine",
    "get_router_engine",
    "PathwayPipeline",
    "get_pathway_pipeline",
    "EventQueue",
    "get_event_queue",
    "AutoProcessor",
    "get_auto_processor",
    "RAGService",
    "get_rag_service",
    "DocumentContextManager",
    "get_document_context_manager",
    "GmailService",
    "get_gmail_service",
    "PDFGenerator",
    "get_pdf_generator",
    "GmailAutoFetchService",
    "get_gmail_auto_fetch_service",
]
