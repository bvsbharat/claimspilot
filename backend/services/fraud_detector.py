"""
Fraud Detection Service
Identifies potential fraud indicators in claims
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


class FraudDetector:
    """Detect fraud indicators in claims"""

    def __init__(self):
        # Suspicious keywords for pattern matching
        self.suspicious_patterns = [
            r"pre-existing",
            r"previous.*accident",
            r"similar.*claim",
            r"multiple.*injuries",
            r"witness.*unavailable",
        ]

    async def detect_fraud_flags(self, claim_data: Dict[str, Any], document_text: str) -> List[Dict[str, Any]]:
        """
        Detect potential fraud indicators

        Returns:
            List of fraud flags with type, confidence, and evidence
        """
        flags = []

        try:
            # Check late reporting
            late_report_flag = self._check_late_reporting(claim_data)
            if late_report_flag:
                flags.append(late_report_flag)

            # Check inconsistencies in story
            inconsistency_flags = self._check_inconsistencies(claim_data, document_text)
            flags.extend(inconsistency_flags)

            # Check suspicious patterns
            pattern_flags = self._check_suspicious_patterns(document_text)
            flags.extend(pattern_flags)

            # Check injury patterns
            injury_flags = self._check_injury_patterns(claim_data)
            flags.extend(injury_flags)

            # Check geographic anomalies
            geo_flags = self._check_geographic_anomalies(claim_data)
            flags.extend(geo_flags)

            logger.info(f"Detected {len(flags)} fraud flags")

            return flags

        except Exception as e:
            logger.error(f"Fraud detection failed: {e}")
            return []

    def _check_late_reporting(self, claim_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check if claim was reported late (>14 days)"""
        try:
            incident_date = claim_data.get("incident_date")
            report_date = claim_data.get("report_date")

            if not incident_date or not report_date:
                return None

            # Convert to datetime if strings
            if isinstance(incident_date, str):
                incident_date = datetime.fromisoformat(incident_date.replace('Z', '+00:00'))
            if isinstance(report_date, str):
                report_date = datetime.fromisoformat(report_date.replace('Z', '+00:00'))

            days_delayed = (report_date - incident_date).days

            if days_delayed > 14:
                confidence = min(0.3 + (days_delayed - 14) * 0.02, 0.95)
                return {
                    "type": "late_reporting",
                    "confidence": confidence,
                    "evidence": f"Claim reported {days_delayed} days after incident (threshold: 14 days)",
                    "severity": "high" if days_delayed > 30 else "medium"
                }

        except Exception as e:
            logger.error(f"Late reporting check failed: {e}")

        return None

    def _check_inconsistencies(self, claim_data: Dict[str, Any], document_text: str) -> List[Dict[str, Any]]:
        """Check for inconsistencies in the claim story"""
        flags = []

        try:
            description = claim_data.get("description", "").lower()
            doc_text_lower = document_text.lower()

            # Check for contradicting statements
            contradictions = [
                ("stopped", "moving"),
                ("no injuries", "injury"),
                ("clear visibility", "couldn't see"),
                ("sober", "drinking"),
            ]

            for word1, word2 in contradictions:
                if word1 in description and word2 in doc_text_lower:
                    flags.append({
                        "type": "inconsistent_story",
                        "confidence": 0.6,
                        "evidence": f"Contradicting statements found: '{word1}' vs '{word2}'",
                        "severity": "medium"
                    })

        except Exception as e:
            logger.error(f"Inconsistency check failed: {e}")

        return flags

    def _check_suspicious_patterns(self, document_text: str) -> List[Dict[str, Any]]:
        """Check for suspicious patterns in document text"""
        flags = []

        try:
            text_lower = document_text.lower()

            for pattern in self.suspicious_patterns:
                if re.search(pattern, text_lower):
                    flags.append({
                        "type": "suspicious_pattern",
                        "confidence": 0.5,
                        "evidence": f"Suspicious pattern detected: {pattern}",
                        "severity": "low"
                    })

        except Exception as e:
            logger.error(f"Pattern check failed: {e}")

        return flags

    def _check_injury_patterns(self, claim_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for suspicious injury patterns"""
        flags = []

        try:
            injuries = claim_data.get("injuries", [])

            # Soft tissue injuries only (common in fraud)
            soft_tissue_keywords = ["whiplash", "strain", "sprain", "soft tissue"]
            all_soft_tissue = all(
                any(keyword in injury.get("description", "").lower() for keyword in soft_tissue_keywords)
                for injury in injuries
            )

            if injuries and all_soft_tissue:
                flags.append({
                    "type": "soft_tissue_only",
                    "confidence": 0.4,
                    "evidence": "Only soft tissue injuries reported (difficult to verify)",
                    "severity": "low"
                })

            # Excessive number of injuries for incident type
            if len(injuries) > 5:
                flags.append({
                    "type": "excessive_injuries",
                    "confidence": 0.5,
                    "evidence": f"{len(injuries)} injuries reported (unusually high)",
                    "severity": "medium"
                })

        except Exception as e:
            logger.error(f"Injury pattern check failed: {e}")

        return flags

    def _check_geographic_anomalies(self, claim_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for geographic anomalies"""
        flags = []

        try:
            location = claim_data.get("location", {})
            state = location.get("state", "").upper() if location else None

            # Check if incident occurred far from insured's location
            # This would require policy holder location - simplified for demo
            parties = claim_data.get("parties", [])
            insured_addresses = [p.get("address", "") for p in parties if p.get("role") == "insured"]

            # Placeholder logic - in production, would do proper geographic distance calculation
            if state and insured_addresses:
                # Simplified check - would need actual address parsing
                pass

        except Exception as e:
            logger.error(f"Geographic anomaly check failed: {e}")

        return flags


# Singleton instance
_fraud_detector_instance = None


def get_fraud_detector() -> FraudDetector:
    """Get or create fraud detector instance"""
    global _fraud_detector_instance
    if _fraud_detector_instance is None:
        _fraud_detector_instance = FraudDetector()
    return _fraud_detector_instance
