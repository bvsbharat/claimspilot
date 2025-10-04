"""
Pinecone Vector Database Service
Handles vector storage for claims and adjusters
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec

logger = logging.getLogger(__name__)


class PineconeService:
    """Service for managing vectors in Pinecone"""

    def __init__(self, api_key: Optional[str] = None, index_name: Optional[str] = None):
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.index_name = index_name or os.getenv("PINECONE_INDEX_NAME", "claims-triage")
        self.pc = None
        self.index = None

        if self.api_key:
            self._initialize()
        else:
            logger.warning("Pinecone API key not found")

    def _initialize(self):
        """Initialize Pinecone client and index"""
        try:
            # Initialize Pinecone
            self.pc = Pinecone(api_key=self.api_key)

            # Check if index exists, create if not
            existing_indexes = [index.name for index in self.pc.list_indexes()]

            if self.index_name not in existing_indexes:
                logger.info(f"Creating Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=1536,  # text-embedding-3-small dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                logger.info(f"Pinecone index created: {self.index_name}")

            # Connect to index
            self.index = self.pc.Index(self.index_name)
            logger.info(f"Connected to Pinecone index: {self.index_name}")

        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            raise

    async def upsert_claim_embedding(
        self,
        claim_id: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Upsert claim embedding to Pinecone

        Args:
            claim_id: Unique claim identifier
            embedding: Vector embedding
            metadata: Claim metadata

        Returns:
            Success status
        """
        try:
            if not self.index:
                logger.error("Pinecone index not initialized")
                return False

            self.index.upsert(vectors=[{
                "id": f"claim_{claim_id}",
                "values": embedding,
                "metadata": {
                    "type": "claim",
                    "claim_id": claim_id,
                    **metadata
                }
            }])

            logger.info(f"Upserted claim embedding: {claim_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to upsert claim embedding: {e}")
            return False

    async def upsert_adjuster_embedding(
        self,
        adjuster_id: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Upsert adjuster profile embedding to Pinecone

        Args:
            adjuster_id: Unique adjuster identifier
            embedding: Vector embedding
            metadata: Adjuster metadata

        Returns:
            Success status
        """
        try:
            if not self.index:
                logger.error("Pinecone index not initialized")
                return False

            self.index.upsert(vectors=[{
                "id": f"adjuster_{adjuster_id}",
                "values": embedding,
                "metadata": {
                    "type": "adjuster",
                    "adjuster_id": adjuster_id,
                    **metadata
                }
            }])

            logger.info(f"Upserted adjuster embedding: {adjuster_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to upsert adjuster embedding: {e}")
            return False

    async def find_similar_adjusters(
        self,
        claim_embedding: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find adjusters similar to claim

        Args:
            claim_embedding: Claim vector embedding
            top_k: Number of results to return
            filter_dict: Optional metadata filters

        Returns:
            List of similar adjusters with metadata and scores
        """
        try:
            if not self.index:
                logger.error("Pinecone index not initialized")
                return []

            # Build filter
            query_filter = {"type": "adjuster"}
            if filter_dict:
                query_filter.update(filter_dict)

            # Query Pinecone
            results = self.index.query(
                vector=claim_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=query_filter
            )

            # Format results
            adjusters = []
            for match in results.matches:
                adjusters.append({
                    "adjuster_id": match.metadata.get("adjuster_id", ""),
                    "score": match.score,
                    "metadata": match.metadata
                })

            logger.info(f"Found {len(adjusters)} similar adjusters")
            return adjusters

        except Exception as e:
            logger.error(f"Failed to find similar adjusters: {e}")
            return []

    async def delete_vector(self, vector_id: str) -> bool:
        """
        Delete vector from Pinecone

        Args:
            vector_id: Vector identifier (claim_id or adjuster_id)

        Returns:
            Success status
        """
        try:
            if not self.index:
                logger.error("Pinecone index not initialized")
                return False

            self.index.delete(ids=[vector_id])
            logger.info(f"Deleted vector: {vector_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete vector: {e}")
            return False

    async def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the Pinecone index"""
        try:
            if not self.index:
                return {"error": "Index not initialized"}

            stats = self.index.describe_index_stats()
            return {
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness
            }
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {"error": str(e)}


# Singleton instance
_pinecone_instance = None


def get_pinecone_service() -> PineconeService:
    """Get or create Pinecone service instance"""
    global _pinecone_instance
    if _pinecone_instance is None:
        _pinecone_instance = PineconeService()
    return _pinecone_instance
