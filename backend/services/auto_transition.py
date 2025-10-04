"""
Auto-Transition Service
Automatically transitions claims through statuses: in_progress -> review -> completed
"""

import asyncio
import logging
import time
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class AutoTransitionService:
    """Service to automatically transition claims through workflow stages"""

    def __init__(self):
        self.running = False
        self.transition_queue: Dict[str, Dict[str, Any]] = {}
        self.task = None

    async def start(self):
        """Start the auto-transition service"""
        if self.running:
            logger.warning("Auto-transition service already running")
            return

        self.running = True
        self.task = asyncio.create_task(self._process_transitions())
        logger.info("✅ Auto-transition service started")

    async def stop(self):
        """Stop the auto-transition service"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Auto-transition service stopped")

    def schedule_transition(self, claim_id: str, claim_amount: float = 0):
        """
        Schedule a claim for auto-transition

        Args:
            claim_id: The claim identifier
            claim_amount: The claim amount for check ID generation
        """
        self.transition_queue[claim_id] = {
            "claim_id": claim_id,
            "claim_amount": claim_amount,
            "current_status": "in_progress",
            "scheduled_at": time.time(),
            "next_transition_at": time.time() + 10  # 10 seconds from now
        }
        logger.info(f"📅 Scheduled auto-transition for claim {claim_id}")

    async def _process_transitions(self):
        """Main loop to process claim transitions"""
        from .mongodb_service import get_mongodb_service
        from .event_queue import get_event_queue

        logger.info("🔄 Auto-transition processor started")

        while self.running:
            try:
                current_time = time.time()
                claims_to_remove = []

                for claim_id, transition_info in list(self.transition_queue.items()):
                    if current_time >= transition_info["next_transition_at"]:
                        # Time to transition this claim
                        success = await self._transition_claim(claim_id, transition_info)

                        if success:
                            current_status = transition_info["current_status"]

                            if current_status == "in_progress":
                                # Move to review and schedule next transition
                                transition_info["current_status"] = "review"
                                transition_info["next_transition_at"] = current_time + 10
                                logger.info(f"✅ Claim {claim_id} transitioned: in_progress → review")

                            elif current_status == "review":
                                # Move to completed and remove from queue
                                transition_info["current_status"] = "completed"
                                claims_to_remove.append(claim_id)
                                logger.info(f"✅ Claim {claim_id} transitioned: review → completed")
                        else:
                            # Failed to transition, remove from queue
                            claims_to_remove.append(claim_id)
                            logger.error(f"❌ Failed to transition claim {claim_id}, removing from queue")

                # Remove completed or failed claims
                for claim_id in claims_to_remove:
                    del self.transition_queue[claim_id]

                # Sleep for a bit before checking again
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error in auto-transition processor: {e}", exc_info=True)
                await asyncio.sleep(5)

    async def _transition_claim(self, claim_id: str, transition_info: Dict[str, Any]) -> bool:
        """
        Transition a claim to the next status

        Args:
            claim_id: The claim identifier
            transition_info: Information about the current transition state

        Returns:
            True if transition was successful, False otherwise
        """
        try:
            from .mongodb_service import get_mongodb_service
            from .event_queue import get_event_queue

            mongodb = await get_mongodb_service()
            event_queue = get_event_queue()

            current_status = transition_info["current_status"]
            claim_amount = transition_info.get("claim_amount", 0)

            # Get full claim to check complexity
            claim = await mongodb.get_claim(claim_id)
            if not claim:
                logger.warning(f"Claim {claim_id} not found, cannot transition")
                return False

            complexity_score = claim.get("complexity_score", 0)
            severity_score = claim.get("severity_score", 0)

            if current_status == "in_progress":
                # Transition to review and assign check ID
                check_id = f"CHECK-{claim_id}-${claim_amount:.0f}"

                # Update claim status and assign check ID
                await mongodb.update_claim_status(claim_id, "review")
                await mongodb.update_claim_field(claim_id, "review_check_id", check_id)

                # Publish event
                await event_queue.publish({
                    "type": "claim_moved_to_review",
                    "message": f"🔍 Claim {claim_id} moved to review - Check ID: {check_id}",
                    "claim_id": claim_id,
                    "status": "review",
                    "review_check_id": check_id
                })

                logger.info(f"📋 Assigned check ID {check_id} to claim {claim_id}")
                return True

            elif current_status == "review":
                # Only auto-complete simple claims (< $500 and low complexity)
                should_auto_complete = (
                    claim_amount < 500 and
                    complexity_score < 50 and
                    severity_score < 50
                )

                if should_auto_complete:
                    # Transition to completed
                    await mongodb.update_claim_status(claim_id, "completed")

                    # Decrement adjuster workload (skip AUTO_SYSTEM)
                    routing_decision = claim.get("routing_decision", {})
                    adjuster_id = routing_decision.get("adjuster_id")
                    if adjuster_id and adjuster_id != "AUTO_SYSTEM":
                        await mongodb.update_adjuster_workload(adjuster_id, -1)
                        logger.info(f"Decremented workload for adjuster {adjuster_id}")

                    # Publish event
                    await event_queue.publish({
                        "type": "claim_completed",
                        "message": f"✅ Claim {claim_id} auto-completed (low complexity, <$500)",
                        "claim_id": claim_id,
                        "status": "completed"
                    })

                    logger.info(f"✅ Claim {claim_id} auto-completed (${claim_amount:.0f}, complexity: {complexity_score:.0f})")
                    return True
                else:
                    # Keep in review - requires manual handling
                    logger.info(f"⏸️  Claim {claim_id} staying in review (${claim_amount:.0f}, complexity: {complexity_score:.0f}, severity: {severity_score:.0f})")
                    # Return False to remove from auto-transition queue
                    return False

            else:
                logger.warning(f"Unknown status for claim {claim_id}: {current_status}")
                return False

        except Exception as e:
            logger.error(f"Failed to transition claim {claim_id}: {e}", exc_info=True)
            return False


# Singleton instance
_auto_transition_service = None


def get_auto_transition_service() -> AutoTransitionService:
    """Get or create the auto-transition service instance"""
    global _auto_transition_service
    if _auto_transition_service is None:
        _auto_transition_service = AutoTransitionService()
    return _auto_transition_service
