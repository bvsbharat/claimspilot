"""
Pathway Real-time RAG Server with LLM xpack
Provides automatic file watching, vector embedding, and question answering
"""

import os
import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import pathway as pw
    from pathway.xpacks.llm import embedders, parsers, splitters
    from pathway.xpacks.llm.vector_store import VectorStoreServer
    from pathway.xpacks.llm.llms import OpenAIChat
    from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer
    PATHWAY_LLM_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Pathway LLM xpack not available: {e}")
    logger.warning("Install with: pip install 'pathway[xpack-llm]' --upgrade")
    PATHWAY_LLM_AVAILABLE = False


class PathwayRAGServer:
    """
    Real-time RAG server using Pathway LLM xpack

    Features:
    - Automatic file watching and indexing
    - Vector embeddings with OpenAI
    - Semantic search over documents
    - REST API endpoints for Q&A
    """

    def __init__(
        self,
        data_dir: str = "./uploads",
        host: str = "127.0.0.1",
        port: int = 8765,
        embedder_model: str = "text-embedding-3-small",
        llm_model: str = "gpt-4o"
    ):
        if not PATHWAY_LLM_AVAILABLE:
            raise ImportError(
                "Pathway LLM xpack is required. "
                "Install with: pip install 'pathway[xpack-llm]' --upgrade"
            )

        self.data_dir = data_dir
        self.host = host
        self.port = port
        self.embedder_model = embedder_model
        self.llm_model = llm_model
        self.running = False

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.api_key = api_key

        logger.info(f"🔧 Initializing Pathway RAG Server")
        logger.info(f"📁 Data directory: {data_dir}")
        logger.info(f"🌐 Server: {host}:{port}")
        logger.info(f"🤖 LLM: {llm_model}")
        logger.info(f"📊 Embedder: {embedder_model}")

    def _build_pipeline(self):
        """Build the Pathway RAG pipeline"""
        logger.info("🏗️  Building Pathway RAG pipeline...")

        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        abs_data_dir = os.path.abspath(self.data_dir)
        logger.info(f"👀 Watching directory: {abs_data_dir}")

        # Step 1: Read files from directory (streaming mode)
        try:
            files = pw.io.fs.read(
                abs_data_dir,
                format="binary",
                mode="streaming",
                autocommit_duration_ms=1500  # Check for new files every 1.5 seconds
            )
            logger.info("✅ File watcher created")
        except TypeError as e:
            # Fallback for older Pathway versions without autocommit_duration_ms
            logger.warning(f"Using fallback file reading (autocommit_duration_ms not supported): {e}")
            files = pw.io.fs.read(
                abs_data_dir,
                format="binary",
                mode="streaming"
            )
            logger.info("✅ File watcher created (fallback mode)")

        # Step 2: Parse documents
        # Use ParseUnstructured for multi-format support (PDF, DOCX, images, etc.)
        logger.info("📄 Setting up document parser...")
        parser = parsers.ParseUnstructured()

        documents = files.select(
            text=pw.apply(
                lambda data: parser(data) if data else "",
                pw.this.data
            )
        )
        logger.info("✅ Document parser configured")

        # Step 3: Split into chunks
        logger.info("✂️  Setting up text splitter...")
        splitter = splitters.TokenCountSplitter(max_tokens=400)

        chunks = documents.select(
            chunks=pw.apply(
                lambda text: splitter(text) if text else [],
                pw.this.text
            )
        ).flatten(pw.this.chunks)
        logger.info("✅ Text splitter configured")

        # Step 4: Create embeddings
        logger.info(f"🧠 Setting up embedder ({self.embedder_model})...")
        embedder = embedders.OpenAIEmbedder(
            api_key=self.api_key,
            model=self.embedder_model,
            retry_strategy=pw.asynchronous.FixedDelayRetryStrategy(max_retries=3)
        )

        embedded_chunks = chunks.select(
            vector=pw.apply_async(embedder, pw.this.chunks)
        )
        logger.info("✅ Embedder configured")

        # Step 5: Create LLM for question answering
        logger.info(f"💬 Setting up LLM ({self.llm_model})...")
        llm = OpenAIChat(
            api_key=self.api_key,
            model=self.llm_model,
            retry_strategy=pw.asynchronous.FixedDelayRetryStrategy(max_retries=3),
            temperature=0.0
        )
        logger.info("✅ LLM configured")

        # Step 6: Create question answerer
        logger.info("🎯 Setting up RAG question answerer...")
        self.question_answerer = BaseRAGQuestionAnswerer(
            llm=llm,
            indexer=embedded_chunks,
            search_topk=3,  # Retrieve top 3 most relevant chunks
            short_prompt_template="""
You are a helpful insurance claims assistant. Answer the question based on the provided context.

Context:
{context}

Question: {query}

Answer:"""
        )
        logger.info("✅ RAG question answerer configured")

        # Step 7: Create REST server
        logger.info(f"🌐 Setting up REST server on {self.host}:{self.port}...")
        self.server = VectorStoreServer(
            host=self.host,
            port=self.port
        )

        # Expose Q&A endpoint
        self.server.add_route(
            "/v2/answer",
            self.question_answerer,
            method="POST"
        )

        logger.info("✅ REST server configured")
        logger.info("🎉 Pathway RAG pipeline built successfully!")

    def run(self):
        """
        Run the Pathway RAG server (blocking call)
        This should be called in a background thread
        """
        try:
            self._build_pipeline()

            logger.info("▶️  Starting Pathway RAG server...")
            logger.info(f"🔗 Endpoints available at http://{self.host}:{self.port}")
            logger.info(f"   📬 POST /v2/answer - Ask questions")
            logger.info(f"   📊 GET  /v1/statistics - Get indexer stats")

            self.running = True

            # Run Pathway (blocking)
            pw.run(
                monitoring_level=pw.MonitoringLevel.NONE,
                with_http_server=True,
                http_server_host=self.host,
                http_server_port=self.port
            )

        except KeyboardInterrupt:
            logger.info("⏹️  Pathway RAG server stopped by user")
            self.running = False
        except Exception as e:
            logger.error(f"❌ Pathway RAG server error: {e}", exc_info=True)
            self.running = False
            raise

    async def query(self, question: str) -> dict:
        """
        Query the RAG system (for internal use)

        Args:
            question: Question to ask

        Returns:
            Answer dictionary with response and sources
        """
        if not self.running:
            return {
                "error": "RAG server is not running",
                "answer": "The RAG service is currently unavailable."
            }

        try:
            import requests

            response = requests.post(
                f"http://{self.host}:{self.port}/v2/answer",
                json={"prompt": question},
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"RAG server returned status {response.status_code}",
                    "answer": "Failed to get response from RAG service."
                }

        except Exception as e:
            logger.error(f"Failed to query RAG server: {e}")
            return {
                "error": str(e),
                "answer": "Failed to connect to RAG service."
            }


# Singleton instance
_pathway_rag_server: Optional[PathwayRAGServer] = None
_pathway_rag_lock = threading.Lock()


def get_pathway_rag_server(
    data_dir: str = "./uploads",
    host: str = "127.0.0.1",
    port: int = 8765
) -> Optional[PathwayRAGServer]:
    """
    Get or create Pathway RAG server instance (thread-safe singleton)

    Returns None if Pathway LLM xpack is not available
    """
    global _pathway_rag_server

    if not PATHWAY_LLM_AVAILABLE:
        return None

    if _pathway_rag_server is None:
        with _pathway_rag_lock:
            if _pathway_rag_server is None:
                try:
                    _pathway_rag_server = PathwayRAGServer(
                        data_dir=data_dir,
                        host=host,
                        port=port
                    )
                    logger.info("✅ Pathway RAG server singleton created")
                except Exception as e:
                    logger.error(f"Failed to create Pathway RAG server: {e}")
                    return None

    return _pathway_rag_server
