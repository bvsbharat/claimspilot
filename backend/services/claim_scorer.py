"""
Claim Scoring Service
Calculates severity and complexity scores for claims
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ClaimScorer:
    """Score claims based on severity and complexity"""

    def __init__(self):
        pass

    async def score_claim(self, claim_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Score a claim on severity and complexity

        Returns:
            Dict with severity_score, complexity_score (0-100)
        """
        try:
            severity_score = await self._calculate_severity(claim_data)
            complexity_score = await self._calculate_complexity(claim_data)

            logger.info(f"Claim scored - Severity: {severity_score:.1f}, Complexity: {complexity_score:.1f}")

            return {
                "severity_score": severity_score,
                "complexity_score": complexity_score
            }

        except Exception as e:
            logger.error(f"Failed to score claim: {e}")
            return {
                "severity_score": 50.0,
                "complexity_score": 50.0
            }

    async def _calculate_severity(self, claim_data: Dict[str, Any]) -> float:
        """
        Calculate severity score (0-100)

        Factors:
        - Financial exposure (claim amount)
        - Injury severity
        - Property damage extent
        """
        score = 0.0

        # Financial exposure (40 points)
        claim_amount = claim_data.get("claim_amount") or 0
        if claim_amount == 0:
            # Try to infer from description
            description = claim_data.get("description", "").lower()
            if any(word in description for word in ["glass", "windshield", "window"]):
                claim_amount = 300  # Typical glass claim
            elif any(word in description for word in ["minor", "scratch", "dent"]):
                claim_amount = 1500  # Minor damage
            elif any(word in description for word in ["major", "total loss"]):
                claim_amount = 15000  # Major damage
            else:
                claim_amount = 5000  # Default moderate claim

        if claim_amount < 500:
            score += 5  # Very minor
        elif claim_amount < 2000:
            score += 10  # Minor
        elif claim_amount < 10000:
            score += 20  # Moderate
        elif claim_amount < 50000:
            score += 30  # Significant
        elif claim_amount < 100000:
            score += 35
        else:
            score += 40  # Major

        # Injury severity (40 points)
        injuries = claim_data.get("injuries", [])
        if not injuries:
            # Check description for injury keywords
            description = claim_data.get("description", "").lower()
            if any(word in description for word in ["injury", "injured", "hurt", "pain", "medical"]):
                score += 15  # Possible injury mentioned
            else:
                score += 0  # Property only
        else:
            max_severity = self._get_max_injury_severity(injuries)
            if max_severity == "minor":
                score += 10
            elif max_severity == "moderate":
                score += 20
            elif max_severity == "serious":
                score += 30
            elif max_severity in ["critical", "fatal"]:
                score += 40

        # Property damage (20 points)
        description = claim_data.get("description", "").lower()
        if any(word in description for word in ["total loss", "destroyed", "catastrophic", "totaled"]):
            score += 20
        elif any(word in description for word in ["major", "significant", "extensive", "severe"]):
            score += 15
        elif any(word in description for word in ["moderate", "substantial"]):
            score += 10
        elif any(word in description for word in ["minor", "small", "light"]):
            score += 5
        elif any(word in description for word in ["glass", "windshield", "scratch", "dent"]):
            score += 3
        else:
            score += 8  # Default moderate

        return min(score, 100.0)

    async def _calculate_complexity(self, claim_data: Dict[str, Any]) -> float:
        """
        Calculate complexity score (0-100)

        Factors:
        - Number of parties involved
        - Fault determination clarity
        - Attorney involvement
        - Documentation completeness
        - Commercial vs personal lines
        """
        score = 0.0
        description = claim_data.get("description", "").lower()

        # Number of parties (20 points)
        parties = claim_data.get("parties", [])
        if len(parties) == 0:
            # Infer from description
            if any(word in description for word in ["multi", "multiple", "several"]):
                score += 15
            else:
                score += 5  # Simple single party
        elif len(parties) <= 2:
            score += 5
        elif len(parties) <= 4:
            score += 10
        else:
            score += 20

        # Fault determination (25 points)
        fault = claim_data.get("fault_determination", "").lower()
        if not fault:
            # Infer from description
            if any(word in description for word in ["disputed", "unclear", "contested", "disagreement"]):
                score += 20
            elif any(word in description for word in ["clear", "obvious", "straightforward"]):
                score += 5
            else:
                score += 10  # Default moderate
        elif fault in ["clear", "obvious", "no dispute"]:
            score += 5
        elif fault in ["disputed", "unclear", "contested"]:
            score += 15
        elif fault in ["multi-party", "shared liability"]:
            score += 25

        # Attorney involvement (20 points)
        attorney_involved = claim_data.get("attorney_involved", False)
        if not attorney_involved:
            # Check description for attorney mentions
            if any(word in description for word in ["attorney", "lawyer", "legal counsel", "representation"]):
                score += 20
        else:
            score += 20

        # Incident type complexity (20 points)
        incident_type = claim_data.get("incident_type", "").lower()
        if incident_type in ["commercial", "business interruption", "liability"]:
            score += 20
        elif incident_type in ["multi-vehicle", "property damage", "property"]:
            score += 15
        elif incident_type in ["auto", "vehicle"]:
            score += 10
        elif incident_type in ["glass", "windshield"]:
            score += 3  # Very simple
        else:
            # Infer from description
            if any(word in description for word in ["glass", "windshield"]):
                score += 3
            elif any(word in description for word in ["commercial", "business"]):
                score += 20
            else:
                score += 8

        # Documentation completeness (15 points)
        # Inverse scoring - less complete = more complex
        completeness = self._assess_documentation_completeness(claim_data)
        score += (15 * (1 - completeness))

        return min(score, 100.0)

    def _get_max_injury_severity(self, injuries: list) -> str:
        """Get the most severe injury from list"""
        severity_order = ["minor", "moderate", "serious", "critical", "fatal"]
        severities = [injury.get("severity", "minor").lower() for injury in injuries]

        for severity in reversed(severity_order):
            if severity in severities:
                return severity

        return "minor"

    def _assess_documentation_completeness(self, claim_data: Dict[str, Any]) -> float:
        """
        Assess documentation completeness (0-1)

        Returns higher score for more complete documentation
        """
        required_fields = [
            "claim_amount",
            "incident_date",
            "parties",
            "location",
            "description",
            "policy_number"
        ]

        present_fields = sum(1 for field in required_fields if claim_data.get(field))
        completeness = present_fields / len(required_fields)

        return completeness


# Singleton instance
_scorer_instance = None


def get_claim_scorer() -> ClaimScorer:
    """Get or create claim scorer instance"""
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = ClaimScorer()
    return _scorer_instance
