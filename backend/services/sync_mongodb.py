"""
Synchronous MongoDB service for use in Pathway pipeline thread
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pymongo import MongoClient, ASCENDING

logger = logging.getLogger(__name__)


class SyncMongoDBService:
    """Synchronous MongoDB service for Pathway pipeline"""

    def __init__(self):
        self.connection_string = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.database_name = os.getenv("MONGODB_DATABASE", "claims_triage")
        self.client = None
        self.db = None
        self._connect()

    def _connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]

            # Create indexes
            self.db.claims.create_index([("claim_id", ASCENDING)], unique=True)
            self.db.claims.create_index([("status", ASCENDING)])
            self.db.adjusters.create_index([("adjuster_id", ASCENDING)], unique=True)

            logger.info(f"Sync MongoDB connected: {self.database_name}")

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def save_claim(self, claim_data: Dict[str, Any]) -> bool:
        """Save or update claim"""
        try:
            claim_data["updated_at"] = datetime.now()

            self.db.claims.update_one(
                {"claim_id": claim_data["claim_id"]},
                {"$set": claim_data},
                upsert=True
            )
            logger.info(f"Saved claim: {claim_data['claim_id']}")
            return True

        except Exception as e:
            logger.error(f"Failed to save claim: {e}", exc_info=True)
            return False

    def delete_claim(self, claim_id: str) -> bool:
        """Delete a claim"""
        try:
            result = self.db.claims.delete_one({"claim_id": claim_id})
            logger.info(f"Deleted claim: {claim_id}")
            return result.deleted_count > 0

        except Exception as e:
            logger.error(f"Failed to delete claim: {e}")
            return False

    def get_claim_by_filename(self, source_filename: str) -> Optional[Dict[str, Any]]:
        """Get claim by source filename"""
        try:
            claim = self.db.claims.find_one({"source_filename": source_filename}, {"_id": 0})
            return claim

        except Exception as e:
            logger.error(f"Failed to get claim by filename: {e}")
            return None

    def update_claim_status(self, claim_id: str, status: str) -> bool:
        """Update claim status"""
        try:
            self.db.claims.update_one(
                {"claim_id": claim_id},
                {"$set": {"status": status, "updated_at": datetime.now()}}
            )
            logger.info(f"Updated claim {claim_id} status to {status}")
            return True

        except Exception as e:
            logger.error(f"Failed to update claim status: {e}")
            return False

    def update_claim_field(self, claim_id: str, field: str, value: Any) -> bool:
        """Update a specific claim field"""
        try:
            self.db.claims.update_one(
                {"claim_id": claim_id},
                {"$set": {field: value, "updated_at": datetime.now()}}
            )
            logger.info(f"Updated claim {claim_id} field {field}")
            return True

        except Exception as e:
            logger.error(f"Failed to update claim field: {e}")
            return False

    def get_all_adjusters(self, available_only: bool = False):
        """Get all adjusters"""
        try:
            query = {"available": True} if available_only else {}
            adjusters = list(self.db.adjusters.find(query, {"_id": 0}))
            return adjusters

        except Exception as e:
            logger.error(f"Failed to get adjusters: {e}")
            return []

    def update_adjuster_workload(self, adjuster_id: str, increment: int) -> bool:
        """Update adjuster workload"""
        try:
            self.db.adjusters.update_one(
                {"adjuster_id": adjuster_id},
                {"$inc": {"current_workload": increment}}
            )
            logger.info(f"Updated adjuster {adjuster_id} workload by {increment}")
            return True

        except Exception as e:
            logger.error(f"Failed to update adjuster workload: {e}")
            return False

    def close(self):
        """Close connection"""
        if self.client:
            self.client.close()
            logger.info("Sync MongoDB connection closed")


# Singleton for Pathway thread
_sync_mongodb_instance = None


def get_sync_mongodb() -> SyncMongoDBService:
    """Get or create sync MongoDB instance"""
    global _sync_mongodb_instance
    if _sync_mongodb_instance is None:
        _sync_mongodb_instance = SyncMongoDBService()
    return _sync_mongodb_instance
