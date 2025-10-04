"""
Auto-Processing Service
Handles automatic processing and routing of minor claims
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class AutoProcessor:
    """Automatically process and approve minor claims"""

    def __init__(self):
        # Define auto-processing rules
        self.auto_approve_threshold = 500  # Claims under $500
        self.glass_damage_types = ["glass", "windshield", "window", "chip", "crack"]
        self.minor_damage_keywords = [
            "scratch", "dent", "paint", "bumper", "small", "minor",
            "cosmetic", "chip", "ding"
        ]

    def should_auto_process(self, claim_data: Dict[str, Any], severity_score: float, complexity_score: float) -> Dict[str, Any]:
        """
        Determine if claim should be auto-processed

        Returns:
            Dict with should_auto_process (bool), reason (str), and auto_decision (Dict)
        """
        try:
            claim_amount = claim_data.get("claim_amount")
            if claim_amount is None:
                claim_amount = 0

            incident_type = claim_data.get("incident_type", "").lower()
            description = claim_data.get("description", "").lower()
            injuries = claim_data.get("injuries", [])
            if injuries is None:
                injuries = []

            # Rule 1: No injuries, low amount, AND low complexity
            if not injuries and claim_amount > 0 and claim_amount <= self.auto_approve_threshold:
                # IMPORTANT: Only auto-approve if BOTH severity and complexity are low
                # This ensures complex claims go to real adjusters
                is_simple_enough = severity_score <= 15 and complexity_score <= 30

                if not is_simple_enough:
                    # Too complex for auto-approval, needs human adjuster
                    logger.info(f"Claim too complex for auto-approval: severity={severity_score}, complexity={complexity_score}")
                    return {
                        "should_auto_process": False,
                        "reason": "Requires adjuster review due to complexity",
                        "auto_decision": None
                    }

                # Check if it's glass damage
                is_glass_damage = any(keyword in description for keyword in self.glass_damage_types)

                if is_glass_damage:
                    return {
                        "should_auto_process": True,
                        "reason": "Auto-approved: Simple glass damage under $500 with no injuries",
                        "auto_decision": {
                            "status": "auto_approved",
                            "priority": "low",
                            "action": "approve",
                            "estimated_payout": claim_amount,
                            "processing_type": "glass_replacement"
                        }
                    }

                # Check if it's other minor damage
                is_minor_damage = any(keyword in description for keyword in self.minor_damage_keywords)

                if is_minor_damage:
                    return {
                        "should_auto_process": True,
                        "reason": f"Auto-approved: Simple minor damage (${claim_amount}) with no injuries",
                        "auto_decision": {
                            "status": "auto_approved",
                            "priority": "low",
                            "action": "approve",
                            "estimated_payout": claim_amount,
                            "processing_type": "minor_repair"
                        }
                    }

            # Rule 2: Very low severity and complexity scores
            if severity_score <= 15 and complexity_score <= 25 and not injuries:
                return {
                    "should_auto_process": True,
                    "reason": "Auto-approved: Very low severity and complexity with no injuries",
                    "auto_decision": {
                        "status": "auto_approved",
                        "priority": "low",
                        "action": "approve",
                        "estimated_payout": claim_amount if claim_amount > 0 else 500,
                        "processing_type": "simple_claim"
                    }
                }

            # Rule 3: Route to junior adjuster for simple claims under $2000
            if not injuries and claim_amount > self.auto_approve_threshold and claim_amount <= 2000:
                is_simple = severity_score <= 25 and complexity_score <= 30

                if is_simple:
                    return {
                        "should_auto_process": True,
                        "reason": "Auto-routed to junior adjuster: Simple claim under $2000",
                        "auto_decision": {
                            "status": "auto_routed",
                            "priority": "low",
                            "action": "route_to_junior",
                            "estimated_payout": claim_amount,
                            "processing_type": "junior_review"
                        }
                    }

            # No auto-processing rules apply
            return {
                "should_auto_process": False,
                "reason": "Requires full adjuster review",
                "auto_decision": None
            }

        except Exception as e:
            logger.error(f"Auto-processing check failed: {e}")
            return {
                "should_auto_process": False,
                "reason": f"Error in auto-processing: {str(e)}",
                "auto_decision": None
            }

    async def process_auto_approved_claim(
        self,
        claim_id: str,
        claim_data: Dict[str, Any],
        auto_decision: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process an auto-approved claim

        Returns:
            Routing decision for auto-approved claim
        """
        try:
            processing_type = auto_decision.get("processing_type", "auto_approved")
            estimated_payout = auto_decision.get("estimated_payout", 0)

            # Generate checklist based on processing type
            if processing_type == "glass_replacement":
                checklist = [
                    "Verify glass damage photos",
                    "Confirm no additional damage",
                    "Approve glass shop estimate",
                    "Schedule repair appointment"
                ]
            elif processing_type == "minor_repair":
                checklist = [
                    "Review damage photos",
                    "Verify repair estimate",
                    "Approve payment under $500",
                    "Confirm no hidden damage"
                ]
            else:
                checklist = [
                    "Quick review of documentation",
                    "Verify claim amount",
                    "Approve payment"
                ]

            return {
                "assigned_to": "Auto-Processor System",
                "adjuster_id": "AUTO_SYSTEM",
                "priority": "low",
                "reason": auto_decision.get("reason", "Auto-approved based on rules"),
                "estimated_workload_hours": 0.5,
                "investigation_checklist": checklist,
                "auto_processed": True,
                "estimated_payout": estimated_payout
            }

        except Exception as e:
            logger.error(f"Auto-processing failed: {e}")
            return {
                "assigned_to": None,
                "adjuster_id": None,
                "priority": "medium",
                "reason": f"Auto-processing error: {str(e)}",
                "estimated_workload_hours": None,
                "investigation_checklist": [],
                "auto_processed": False
            }

    async def route_to_junior_adjuster(
        self,
        claim_data: Dict[str, Any],
        available_adjusters: list,
        auto_decision: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Route to a junior adjuster for simple claims

        Returns:
            Selected junior adjuster or None
        """
        try:
            # Find available junior adjusters
            junior_adjusters = [
                adj for adj in available_adjusters
                if adj.get("experience_level", "").lower() in ["junior", "entry"]
                and adj.get("available", False)
                and adj.get("current_workload", 0) < adj.get("max_concurrent_claims", 15)
            ]

            if not junior_adjusters:
                logger.warning("No junior adjusters available for auto-routing")
                return None

            # Select adjuster with lowest workload
            best_adjuster = min(junior_adjusters, key=lambda x: x.get("current_workload", 0))

            return {
                "assigned_to": best_adjuster.get("name"),
                "adjuster_id": best_adjuster.get("adjuster_id"),
                "priority": "low",
                "reason": "Auto-routed to junior adjuster for simple claim review",
                "estimated_workload_hours": 2.0,
                "investigation_checklist": [
                    "Review claim documentation",
                    "Verify damage and estimate",
                    "Contact insured if needed",
                    "Approve or escalate to senior adjuster"
                ],
                "auto_routed": True
            }

        except Exception as e:
            logger.error(f"Junior adjuster routing failed: {e}")
            return None


# Singleton instance
_auto_processor_instance = None


def get_auto_processor() -> AutoProcessor:
    """Get or create auto processor instance"""
    global _auto_processor_instance
    if _auto_processor_instance is None:
        _auto_processor_instance = AutoProcessor()
    return _auto_processor_instance
