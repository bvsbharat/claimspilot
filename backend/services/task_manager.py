"""
Task Management Service
Integrates with vibe_kanban to create and manage tasks for claims
"""

import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Project configuration
KANBAN_PROJECT_ID = os.getenv("KANBAN_PROJECT_ID", "cc962745-3326-4ab2-a807-790deac92d1a")


async def create_claim_task(
    claim_id: str,
    adjuster_id: str,
    adjuster_name: str,
    claim_amount: Optional[float],
    incident_type: Optional[str],
    priority: str,
    is_auto_approved: bool = False
) -> Optional[str]:
    """
    Create a task in the kanban board for a claim

    Args:
        claim_id: The claim identifier
        adjuster_id: ID of assigned adjuster
        adjuster_name: Name of assigned adjuster
        claim_amount: Claim amount
        incident_type: Type of incident
        priority: Task priority
        is_auto_approved: Whether claim was auto-approved

    Returns:
        Task ID if successful, None otherwise
    """
    try:
        # For now, we'll store task info in the claim document
        # In production, this would integrate with MCP vibe_kanban

        task_title = f"Process Claim: {claim_id}"

        # Build task description
        description_parts = [
            f"**Assigned to:** {adjuster_name} ({adjuster_id})",
            f"**Priority:** {priority.upper()}",
        ]

        if claim_amount:
            description_parts.append(f"**Amount:** ${claim_amount:,.2f}")

        if incident_type:
            description_parts.append(f"**Type:** {incident_type}")

        if is_auto_approved:
            description_parts.append(f"**Status:** Auto-approved - Requires verification")
            description_parts.append("\n**Tasks:**")
            description_parts.append("- [ ] Verify claim details")
            description_parts.append("- [ ] Review auto-approval decision")
            description_parts.append("- [ ] Confirm payout amount")
            description_parts.append("- [ ] Move to review for final check")
        else:
            description_parts.append("\n**Tasks:**")
            description_parts.append("- [ ] Review claim documentation")
            description_parts.append("- [ ] Assess damage and liability")
            description_parts.append("- [ ] Determine payout amount")
            description_parts.append("- [ ] Contact claimant if needed")
            description_parts.append("- [ ] Move to review for approval")

        task_description = "\n".join(description_parts)

        logger.info(f"📋 Task created for claim {claim_id}: {task_title}")

        # Return a mock task ID for now
        # In production, this would call the MCP service:
        # task_id = await mcp_create_task(KANBAN_PROJECT_ID, task_title, task_description)
        return f"TASK-{claim_id}"

    except Exception as e:
        logger.error(f"Failed to create task for claim {claim_id}: {e}", exc_info=True)
        return None


async def update_task_status(claim_id: str, new_status: str) -> bool:
    """
    Update task status based on claim status

    Status mapping:
    - in_progress -> Task created
    - review -> Add review checklist
    - completed -> Mark task as done
    """
    try:
        task_id = f"TASK-{claim_id}"

        logger.info(f"📋 Updated task {task_id} status to: {new_status}")

        # In production, this would update the MCP task status
        return True

    except Exception as e:
        logger.error(f"Failed to update task for claim {claim_id}: {e}")
        return False


# Singleton instance
_task_manager_instance = None


def get_task_manager():
    """Get or create task manager instance"""
    global _task_manager_instance
    if _task_manager_instance is None:
        _task_manager_instance = {
            "create_task": create_claim_task,
            "update_task": update_task_status
        }
    return _task_manager_instance
