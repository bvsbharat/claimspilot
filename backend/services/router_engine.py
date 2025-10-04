"""
Routing Engine
Matches claims to appropriate adjusters based on specialization, workload, and complexity
"""

import logging
import os
from typing import Dict, Any, List, Optional
import openai

logger = logging.getLogger(__name__)


class RouterEngine:
    """Route claims to appropriate adjusters"""

    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = openai.OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None

    async def route_claim(
        self,
        claim_data: Dict[str, Any],
        available_adjusters: List[Dict[str, Any]],
        severity_score: float,
        complexity_score: float,
        fraud_flags: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Route claim to best matching adjuster

        Returns:
            Routing decision with assigned adjuster, priority, reason, and checklist
        """
        try:
            # Check for SIU routing first (fraud)
            if self._should_route_to_siu(fraud_flags):
                siu_adjuster = self._find_siu_adjuster(available_adjusters)
                if siu_adjuster:
                    return await self._create_routing_decision(
                        claim_data=claim_data,
                        adjuster=siu_adjuster,
                        priority="urgent",
                        reason="Fraud indicators detected - routing to Special Investigation Unit",
                        fraud_flags=fraud_flags
                    )

            # Determine priority based on scores
            priority = self._calculate_priority(severity_score, complexity_score)

            # Filter adjusters by specialization and capacity
            qualified_adjusters = self._filter_qualified_adjusters(
                available_adjusters,
                claim_data,
                severity_score
            )

            if not qualified_adjusters:
                logger.warning("No qualified adjusters available")
                return {
                    "assigned_to": None,
                    "adjuster_id": None,
                    "priority": priority,
                    "reason": "No qualified adjusters available at this time",
                    "estimated_workload_hours": None,
                    "investigation_checklist": []
                }

            # Score adjusters and select best match
            best_adjuster = self._select_best_adjuster(
                qualified_adjusters,
                claim_data,
                severity_score,
                complexity_score
            )

            # Create routing decision
            routing_decision = await self._create_routing_decision(
                claim_data=claim_data,
                adjuster=best_adjuster,
                priority=priority,
                reason=self._generate_routing_reason(claim_data, best_adjuster, severity_score, complexity_score),
                fraud_flags=fraud_flags
            )

            return routing_decision

        except Exception as e:
            logger.error(f"Routing failed: {e}")
            return {
                "assigned_to": None,
                "adjuster_id": None,
                "priority": "medium",
                "reason": f"Routing error: {str(e)}",
                "estimated_workload_hours": None,
                "investigation_checklist": []
            }

    def _should_route_to_siu(self, fraud_flags: List[Dict[str, Any]]) -> bool:
        """Check if claim should be routed to SIU"""
        # Route to SIU if high-confidence fraud flags or multiple flags
        high_confidence_flags = [f for f in fraud_flags if f.get("confidence", 0) > 0.7]
        return len(high_confidence_flags) > 0 or len(fraud_flags) >= 3

    def _find_siu_adjuster(self, adjusters: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find SIU adjuster"""
        for adjuster in adjusters:
            if "siu" in adjuster.get("specializations", []):
                return adjuster
        return None

    def _calculate_priority(self, severity_score: float, complexity_score: float) -> str:
        """Calculate claim priority"""
        combined_score = (severity_score + complexity_score) / 2

        if combined_score >= 80:
            return "urgent"
        elif combined_score >= 60:
            return "high"
        elif combined_score >= 40:
            return "medium"
        else:
            return "low"

    def _filter_qualified_adjusters(
        self,
        adjusters: List[Dict[str, Any]],
        claim_data: Dict[str, Any],
        severity_score: float
    ) -> List[Dict[str, Any]]:
        """Filter adjusters by qualification"""
        qualified = []

        incident_type = claim_data.get("incident_type", "").lower()
        claim_amount = claim_data.get("claim_amount", 0)

        for adjuster in adjusters:
            # Check availability
            if not adjuster.get("available", False):
                continue

            # Check capacity
            current_workload = adjuster.get("current_workload", 0)
            max_concurrent = adjuster.get("max_concurrent_claims", 15)
            if current_workload >= max_concurrent:
                continue

            # Check specialization match
            specializations = adjuster.get("specializations", [])
            if incident_type in specializations or "liability" in specializations:
                # Check if they can handle the claim amount
                max_amount = adjuster.get("max_claim_amount", float('inf'))
                if claim_amount <= max_amount:
                    qualified.append(adjuster)

        return qualified

    def _select_best_adjuster(
        self,
        qualified_adjusters: List[Dict[str, Any]],
        claim_data: Dict[str, Any],
        severity_score: float,
        complexity_score: float
    ) -> Dict[str, Any]:
        """Select best adjuster from qualified list"""
        incident_type = claim_data.get("incident_type", "").lower()

        # Score each adjuster
        scored_adjusters = []
        for adjuster in qualified_adjusters:
            score = 0.0

            # Specialization match (40 points)
            specializations = adjuster.get("specializations", [])
            if incident_type in specializations:
                score += 40
            elif "liability" in specializations:
                score += 20

            # Experience level (30 points)
            experience_level = adjuster.get("experience_level", "junior")
            combined_score = (severity_score + complexity_score) / 2
            if combined_score >= 70 and experience_level in ["senior", "expert"]:
                score += 30
            elif combined_score >= 50 and experience_level in ["mid", "senior", "expert"]:
                score += 25
            elif combined_score < 50 and experience_level in ["junior", "mid"]:
                score += 20

            # Workload (30 points) - prefer less busy adjusters
            current_workload = adjuster.get("current_workload", 0)
            max_workload = adjuster.get("max_concurrent_claims", 15)
            workload_ratio = current_workload / max_workload
            score += (30 * (1 - workload_ratio))

            scored_adjusters.append((score, adjuster))

        # Return highest scoring adjuster
        scored_adjusters.sort(key=lambda x: x[0], reverse=True)
        return scored_adjusters[0][1]

    def _generate_routing_reason(
        self,
        claim_data: Dict[str, Any],
        adjuster: Dict[str, Any],
        severity_score: float,
        complexity_score: float
    ) -> str:
        """Generate human-readable routing reason"""
        reasons = []

        # Specialization match
        incident_type = claim_data.get("incident_type", "unknown")
        specializations = adjuster.get("specializations", [])
        if incident_type in specializations:
            reasons.append(f"Specialist in {incident_type} claims")

        # Experience match
        experience_level = adjuster.get("experience_level", "junior")
        combined_score = (severity_score + complexity_score) / 2
        if combined_score >= 70:
            reasons.append(f"{experience_level.capitalize()} adjuster for high-complexity case")
        else:
            reasons.append(f"Appropriate experience level ({experience_level})")

        # Workload
        current_workload = adjuster.get("current_workload", 0)
        if current_workload < 5:
            reasons.append("Low current workload")
        elif current_workload < 10:
            reasons.append("Available capacity")

        return " | ".join(reasons)

    async def _create_routing_decision(
        self,
        claim_data: Dict[str, Any],
        adjuster: Dict[str, Any],
        priority: str,
        reason: str,
        fraud_flags: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create routing decision with investigation checklist"""

        # Generate investigation checklist
        checklist = await self._generate_investigation_checklist(claim_data, fraud_flags)

        # Estimate workload hours
        estimated_hours = self._estimate_workload(claim_data, fraud_flags)

        return {
            "assigned_to": adjuster.get("name"),
            "adjuster_id": adjuster.get("adjuster_id"),
            "priority": priority,
            "reason": reason,
            "estimated_workload_hours": estimated_hours,
            "investigation_checklist": checklist
        }

    async def _generate_investigation_checklist(
        self,
        claim_data: Dict[str, Any],
        fraud_flags: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate investigation checklist based on claim details"""
        checklist = []

        # Standard items
        checklist.append("Review all submitted documentation")
        checklist.append("Verify policy coverage and limits")
        checklist.append("Contact insured for statement")

        # Based on incident type
        incident_type = claim_data.get("incident_type", "").lower()
        if incident_type == "auto":
            checklist.append("Obtain police report")
            checklist.append("Inspect vehicle damage")
            checklist.append("Review traffic camera footage if available")
        elif incident_type == "property":
            checklist.append("Schedule property inspection")
            checklist.append("Review photos and damage assessment")
            checklist.append("Verify property ownership")
        elif incident_type == "commercial":
            checklist.append("Review business interruption documentation")
            checklist.append("Analyze financial records")
            checklist.append("Assess subrogation opportunities")

        # Injuries
        injuries = claim_data.get("injuries", [])
        if injuries:
            checklist.append("Request medical records and bills")
            checklist.append("Assess medical treatment necessity")
            if len(injuries) > 1:
                checklist.append("Coordinate with multiple medical providers")

        # Fraud flags
        if fraud_flags:
            checklist.append("Conduct detailed fraud investigation")
            for flag in fraud_flags:
                checklist.append(f"Investigate: {flag.get('evidence', 'fraud indicator')}")

        # Attorney involvement
        if claim_data.get("attorney_involved"):
            checklist.append("Coordinate with legal department")
            checklist.append("Establish attorney communication protocol")

        return checklist

    def _estimate_workload(
        self,
        claim_data: Dict[str, Any],
        fraud_flags: List[Dict[str, Any]]
    ) -> float:
        """Estimate workload hours for claim"""
        base_hours = 5.0

        # Adjust for injuries
        injuries = claim_data.get("injuries", [])
        base_hours += len(injuries) * 2.0

        # Adjust for parties
        parties = claim_data.get("parties", [])
        if len(parties) > 2:
            base_hours += (len(parties) - 2) * 1.5

        # Adjust for fraud investigation
        base_hours += len(fraud_flags) * 3.0

        # Adjust for attorney involvement
        if claim_data.get("attorney_involved"):
            base_hours += 5.0

        return round(base_hours, 1)


# Singleton instance
_router_engine_instance = None


def get_router_engine() -> RouterEngine:
    """Get or create router engine instance"""
    global _router_engine_instance
    if _router_engine_instance is None:
        _router_engine_instance = RouterEngine()
    return _router_engine_instance
