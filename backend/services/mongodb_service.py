"""
MongoDB service for claims storage and retrieval
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)


class MongoDBService:
    """Service for managing claims data in MongoDB"""

    def __init__(self, connection_string: Optional[str] = None, database_name: Optional[str] = None):
        self.connection_string = connection_string or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.database_name = database_name or os.getenv("MONGODB_DATABASE", "claims_triage")
        self.client = None
        self.db = None

    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.connection_string)
            self.db = self.client[self.database_name]

            # Create indexes
            await self.db.claims.create_index("claim_id", unique=True)
            await self.db.claims.create_index("status")
            await self.db.claims.create_index("created_at")

            await self.db.adjusters.create_index("adjuster_id", unique=True)
            await self.db.adjusters.create_index("available")

            await self.db.routing_history.create_index("claim_id")
            await self.db.routing_history.create_index("adjuster_id")

            logger.info(f"Connected to MongoDB: {self.database_name}")

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def close(self):
        """Close MongoDB connection"""
        if self.client is not None:
            self.client.close()
            logger.info("MongoDB connection closed")

    # Claims operations
    async def save_claim(self, claim_data: Dict[str, Any]) -> bool:
        """Save or update claim"""
        try:
            claim_data["updated_at"] = datetime.now()

            await self.db.claims.update_one(
                {"claim_id": claim_data["claim_id"]},
                {"$set": claim_data},
                upsert=True
            )
            logger.info(f"Saved claim: {claim_data['claim_id']}")
            return True

        except Exception as e:
            logger.error(f"Failed to save claim: {e}")
            return False

    async def get_claim(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Get claim by ID"""
        try:
            claim = await self.db.claims.find_one({"claim_id": claim_id}, {"_id": 0})
            return claim

        except Exception as e:
            logger.error(f"Failed to get claim: {e}")
            return None

    async def get_claim_by_filename(self, source_filename: str) -> Optional[Dict[str, Any]]:
        """Get claim by source filename"""
        try:
            claim = await self.db.claims.find_one({"source_filename": source_filename}, {"_id": 0})
            return claim

        except Exception as e:
            logger.error(f"Failed to get claim by filename: {e}")
            return None

    async def get_all_claims(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all claims, optionally filtered by status"""
        try:
            if self.client is None or self.db is None:
                logger.warning("MongoDB not connected, returning empty list")
                return []

            query = {}
            if status:
                query["status"] = status

            claims = await self.db.claims.find(query, {"_id": 0}).sort("created_at", -1).to_list(length=None)
            return claims

        except Exception as e:
            logger.error(f"Failed to get claims: {e}", exc_info=False)
            return []

    async def get_claims_queue(self) -> List[Dict[str, Any]]:
        """Get claims in triage queue (not yet assigned)"""
        try:
            claims = await self.db.claims.find(
                {"status": {"$in": ["uploaded", "extracting", "scoring", "routing"]}},
                {"_id": 0}
            ).sort("created_at", 1).to_list(length=None)

            return claims

        except Exception as e:
            logger.error(f"Failed to get claims queue: {e}")
            return []

    async def delete_claim(self, claim_id: str) -> bool:
        """Delete claim"""
        try:
            await self.db.claims.delete_one({"claim_id": claim_id})
            logger.info(f"Deleted claim: {claim_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete claim: {e}")
            return False

    async def update_claim_status(self, claim_id: str, status: str) -> bool:
        """Update claim status"""
        try:
            result = await self.db.claims.update_one(
                {"claim_id": claim_id},
                {"$set": {"status": status, "updated_at": datetime.now()}}
            )
            logger.info(f"Updated claim {claim_id} status to {status}")
            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Failed to update claim status: {e}")
            return False

    async def update_claim_field(self, claim_id: str, field_name: str, field_value: Any) -> bool:
        """Update a specific claim field"""
        try:
            result = await self.db.claims.update_one(
                {"claim_id": claim_id},
                {"$set": {field_name: field_value, "updated_at": datetime.now()}}
            )
            logger.info(f"Updated claim {claim_id} field {field_name}")
            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Failed to update claim field: {e}")
            return False

    # Adjuster operations
    async def save_adjuster(self, adjuster_data: Dict[str, Any]) -> bool:
        """Save or update adjuster profile"""
        try:
            adjuster_data["updated_at"] = datetime.now()

            await self.db.adjusters.update_one(
                {"adjuster_id": adjuster_data["adjuster_id"]},
                {"$set": adjuster_data},
                upsert=True
            )
            logger.info(f"Saved adjuster: {adjuster_data['adjuster_id']}")
            return True

        except Exception as e:
            logger.error(f"Failed to save adjuster: {e}")
            return False

    async def get_adjuster(self, adjuster_id: str) -> Optional[Dict[str, Any]]:
        """Get adjuster by ID"""
        try:
            adjuster = await self.db.adjusters.find_one({"adjuster_id": adjuster_id}, {"_id": 0})
            return adjuster

        except Exception as e:
            logger.error(f"Failed to get adjuster: {e}")
            return None

    async def get_all_adjusters(self, available_only: bool = False) -> List[Dict[str, Any]]:
        """Get all adjusters"""
        try:
            if self.client is None or self.db is None:
                logger.warning("MongoDB not connected, returning empty list")
                return []

            query = {}
            if available_only:
                query["available"] = True

            adjusters = await self.db.adjusters.find(query, {"_id": 0}).to_list(length=None)
            return adjusters

        except Exception as e:
            logger.error(f"Failed to get adjusters: {e}", exc_info=False)
            return []

    async def update_adjuster_workload(self, adjuster_id: str, workload_delta: int) -> bool:
        """Update adjuster's current workload"""
        try:
            await self.db.adjusters.update_one(
                {"adjuster_id": adjuster_id},
                {"$inc": {"current_workload": workload_delta}}
            )
            return True

        except Exception as e:
            logger.error(f"Failed to update adjuster workload: {e}")
            return False

    # Routing history
    async def save_routing_decision(self, routing_data: Dict[str, Any]) -> bool:
        """Save routing decision to history"""
        try:
            routing_data["timestamp"] = datetime.now()
            await self.db.routing_history.insert_one(routing_data)
            return True

        except Exception as e:
            logger.error(f"Failed to save routing decision: {e}")
            return False

    async def get_routing_history(self, claim_id: Optional[str] = None, adjuster_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get routing history"""
        try:
            query = {}
            if claim_id:
                query["claim_id"] = claim_id
            if adjuster_id:
                query["adjuster_id"] = adjuster_id

            history = await self.db.routing_history.find(query, {"_id": 0}).sort("timestamp", -1).to_list(length=None)
            return history

        except Exception as e:
            logger.error(f"Failed to get routing history: {e}")
            return []

    # Analytics
    async def get_fraud_flags(self) -> List[Dict[str, Any]]:
        """Get all claims with fraud flags"""
        try:
            if self.client is None or self.db is None:
                logger.warning("MongoDB not connected, returning empty list")
                return []

            claims = await self.db.claims.find(
                {"fraud_flags": {"$exists": True, "$ne": []}},
                {"_id": 0, "claim_id": 1, "fraud_flags": 1, "extracted_data": 1, "status": 1}
            ).to_list(length=None)

            return claims

        except Exception as e:
            logger.error(f"Failed to get fraud flags: {e}", exc_info=False)
            return []

    async def get_processing_metrics(self) -> Dict[str, Any]:
        """Get processing metrics"""
        try:
            if self.client is None or self.db is None:
                logger.warning("MongoDB not connected, returning default metrics")
                return {
                    "total_claims": 0,
                    "assigned_claims": 0,
                    "completed_claims": 0,
                    "avg_processing_time_seconds": 0,
                }

            total_claims = await self.db.claims.count_documents({})
            assigned_claims = await self.db.claims.count_documents({"status": "assigned"})
            completed_claims = await self.db.claims.count_documents({"status": "completed"})

            # Average processing time
            pipeline = [
                {"$match": {"processing_time_seconds": {"$exists": True, "$ne": None}}},
                {"$group": {"_id": None, "avg_time": {"$avg": "$processing_time_seconds"}}}
            ]
            result = await self.db.claims.aggregate(pipeline).to_list(length=1)
            avg_processing_time = result[0]["avg_time"] if result else 0

            return {
                "total_claims": total_claims,
                "assigned_claims": assigned_claims,
                "completed_claims": completed_claims,
                "avg_processing_time_seconds": avg_processing_time,
            }

        except Exception as e:
            logger.error(f"Failed to get processing metrics: {e}", exc_info=False)
            return {
                "total_claims": 0,
                "assigned_claims": 0,
                "completed_claims": 0,
                "avg_processing_time_seconds": 0,
            }

    # Gmail token operations
    async def save_gmail_tokens(self, user_email: str, token_data: Dict[str, Any]) -> bool:
        """Save Gmail OAuth tokens"""
        try:
            token_data["user_email"] = user_email
            token_data["created_at"] = datetime.now()
            token_data["updated_at"] = datetime.now()

            await self.db.gmail_tokens.update_one(
                {"user_email": user_email},
                {"$set": token_data},
                upsert=True
            )
            logger.info(f"Saved Gmail tokens for: {user_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to save Gmail tokens: {e}")
            return False

    async def get_gmail_tokens(self, user_email: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get Gmail OAuth tokens"""
        try:
            if user_email:
                tokens = await self.db.gmail_tokens.find_one({"user_email": user_email}, {"_id": 0})
            else:
                # Get the most recently updated tokens
                tokens = await self.db.gmail_tokens.find_one(
                    {},
                    {"_id": 0},
                    sort=[("updated_at", -1)]
                )

            return tokens

        except Exception as e:
            logger.error(f"Failed to get Gmail tokens: {e}")
            return None

    async def delete_gmail_tokens(self, user_email: Optional[str] = None) -> bool:
        """Delete Gmail OAuth tokens"""
        try:
            if user_email:
                result = await self.db.gmail_tokens.delete_one({"user_email": user_email})
            else:
                result = await self.db.gmail_tokens.delete_many({})

            logger.info(f"Deleted Gmail tokens")
            return result.deleted_count > 0

        except Exception as e:
            logger.error(f"Failed to delete Gmail tokens: {e}")
            return False


# Singleton instance
_mongodb_instance = None


async def get_mongodb_service() -> MongoDBService:
    """Get or create MongoDB service instance"""
    global _mongodb_instance
    if _mongodb_instance is None:
        _mongodb_instance = MongoDBService()
        await _mongodb_instance.connect()
    return _mongodb_instance
