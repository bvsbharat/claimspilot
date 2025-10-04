"""
DeepAgent Service
Advanced reasoning and decision-making for complex claims
Based on langchain-ai/deepagents principles: https://github.com/langchain-ai/deepagents

This is a simplified implementation that uses OpenAI for multi-step reasoning.
To use the full DeepAgents framework, install: pip install langchain langchain-openai
"""

import os
import logging
import json
from typing import Dict, Any, List, Optional
import openai

logger = logging.getLogger(__name__)


class DeepAgentService:
    """
    Advanced claim processing with multi-step reasoning

    Features:
    - Multi-step investigation planning
    - Evidence-based decision making
    - Adjuster skill matching with semantic reasoning
    - Complex claim analysis
    """

    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = openai.OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None

    async def analyze_complex_claim(
        self,
        claim_data: Dict[str, Any],
        fraud_flags: List[Dict[str, Any]],
        severity_score: float,
        complexity_score: float
    ) -> Dict[str, Any]:
        """
        Perform deep analysis on complex claims

        Returns:
            Analysis with reasoning chain, recommendations, and investigation plan
        """
        try:
            if not self.client:
                logger.warning("OpenAI client not available for deep analysis")
                return self._fallback_analysis(claim_data, fraud_flags)

            prompt = f"""You are an expert insurance claims analyst. Analyze this claim deeply and provide structured reasoning.

Claim Data:
{json.dumps(claim_data, indent=2)}

Severity Score: {severity_score}/100
Complexity Score: {complexity_score}/100

Fraud Flags: {len(fraud_flags)} flag(s)
{json.dumps(fraud_flags, indent=2) if fraud_flags else "None"}

Provide a comprehensive analysis including:

1. **Reasoning Chain**: Step-by-step thought process
2. **Risk Assessment**: Key risks and concerns
3. **Investigation Priorities**: What to investigate first and why
4. **Recommended Actions**: Specific next steps
5. **Adjuster Requirements**: What skills/experience needed for this claim
6. **Estimated Timeline**: How long investigation will take
7. **Settlement Range**: Likely settlement amount range

Format as JSON with these keys: reasoning_chain (list of steps), risk_assessment, investigation_priorities (list), recommended_actions (list), adjuster_requirements (dict with experience_level, specializations), estimated_timeline_days, settlement_range (dict with min, max, confidence)
"""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            analysis = json.loads(response.choices[0].message.content)
            logger.info(f"Deep analysis completed with {len(analysis.get('reasoning_chain', []))} reasoning steps")

            return {
                "analysis_type": "deep_reasoning",
                "reasoning_chain": analysis.get("reasoning_chain", []),
                "risk_assessment": analysis.get("risk_assessment", ""),
                "investigation_priorities": analysis.get("investigation_priorities", []),
                "recommended_actions": analysis.get("recommended_actions", []),
                "adjuster_requirements": analysis.get("adjuster_requirements", {}),
                "estimated_timeline_days": analysis.get("estimated_timeline_days", 30),
                "settlement_range": analysis.get("settlement_range", {}),
                "confidence": "high"
            }

        except Exception as e:
            logger.error(f"Deep analysis failed: {e}")
            return self._fallback_analysis(claim_data, fraud_flags)

    async def match_adjuster_with_reasoning(
        self,
        claim_data: Dict[str, Any],
        available_adjusters: List[Dict[str, Any]],
        complexity_score: float,
        fraud_flags: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Match adjuster to claim using semantic reasoning

        Returns:
            Best adjuster match with detailed reasoning
        """
        try:
            if not self.client:
                logger.warning("OpenAI client not available for adjuster matching")
                return {"error": "No OpenAI client"}

            adjuster_summaries = [
                {
                    "id": adj.get("adjuster_id"),
                    "name": adj.get("name"),
                    "experience_level": adj.get("experience_level"),
                    "years_experience": adj.get("years_experience"),
                    "specializations": adj.get("specializations", []),
                    "current_workload": adj.get("current_workload", 0),
                    "max_claims": adj.get("max_concurrent_claims", 15)
                }
                for adj in available_adjusters[:10]  # Limit to top 10 for token efficiency
            ]

            prompt = f"""You are an expert at matching insurance claims to adjusters based on skills, experience, and capacity.

Claim Summary:
- Type: {claim_data.get('incident_type', 'unknown')}
- Amount: ${claim_data.get('claim_amount', 0)}
- Complexity Score: {complexity_score}/100
- Has Fraud Flags: {len(fraud_flags) > 0}
- Description: {claim_data.get('description', '')[:200]}

Available Adjusters:
{json.dumps(adjuster_summaries, indent=2)}

Analyze each adjuster and select the best match. Provide reasoning for your choice.

Return JSON with: selected_adjuster_id, selected_adjuster_name, confidence_score (0-1), reasoning (detailed explanation), alternative_adjusters (list of 2 backup options with ids)
"""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            logger.info(f"Adjuster matched with reasoning: {result.get('selected_adjuster_name')}")

            return {
                "adjuster_id": result.get("selected_adjuster_id"),
                "adjuster_name": result.get("selected_adjuster_name"),
                "confidence": result.get("confidence_score", 0.8),
                "reasoning": result.get("reasoning", ""),
                "alternatives": result.get("alternative_adjusters", []),
                "match_type": "deep_semantic"
            }

        except Exception as e:
            logger.error(f"Deep adjuster matching failed: {e}")
            return {"error": str(e)}

    async def generate_investigation_plan(
        self,
        claim_data: Dict[str, Any],
        fraud_flags: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate a step-by-step investigation plan with reasoning

        Returns:
            List of investigation steps with priorities and estimated times
        """
        try:
            if not self.client:
                return self._fallback_investigation_plan(claim_data)

            prompt = f"""Create a detailed investigation plan for this insurance claim.

Claim: {json.dumps(claim_data, indent=2)}
Fraud Flags: {json.dumps(fraud_flags, indent=2) if fraud_flags else "None"}

Create an investigation plan with steps in priority order. Each step should have:
- step_number
- action (what to do)
- reason (why this step is important)
- priority (urgent/high/medium/low)
- estimated_hours
- dependencies (which steps must be completed first)
- success_criteria (how to know this step is done)

Return JSON with key "investigation_steps" containing a list of steps.
"""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            steps = result.get("investigation_steps", [])
            logger.info(f"Generated {len(steps)}-step investigation plan")

            return steps

        except Exception as e:
            logger.error(f"Investigation plan generation failed: {e}")
            return self._fallback_investigation_plan(claim_data)

    def _fallback_analysis(self, claim_data: Dict[str, Any], fraud_flags: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback analysis when OpenAI is not available"""
        return {
            "analysis_type": "rule_based",
            "reasoning_chain": [
                "Basic rule-based analysis performed",
                f"Claim amount: ${claim_data.get('claim_amount', 0)}",
                f"Incident type: {claim_data.get('incident_type', 'unknown')}",
                f"Fraud flags present: {len(fraud_flags) > 0}"
            ],
            "risk_assessment": "Requires manual review - deep analysis unavailable",
            "investigation_priorities": [
                "Review all submitted documentation",
                "Verify policy coverage",
                "Contact insured for statement"
            ],
            "recommended_actions": [
                "Assign to experienced adjuster",
                "Begin standard investigation process"
            ],
            "adjuster_requirements": {
                "experience_level": "mid to senior",
                "specializations": [claim_data.get("incident_type", "general")]
            },
            "estimated_timeline_days": 30,
            "settlement_range": {},
            "confidence": "low"
        }

    def _fallback_investigation_plan(self, claim_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback investigation plan when OpenAI is not available"""
        return [
            {
                "step_number": 1,
                "action": "Review all submitted documentation",
                "reason": "Establish baseline facts",
                "priority": "urgent",
                "estimated_hours": 2,
                "dependencies": [],
                "success_criteria": "All documents catalogued and reviewed"
            },
            {
                "step_number": 2,
                "action": "Verify policy coverage and limits",
                "reason": "Ensure claim is covered",
                "priority": "high",
                "estimated_hours": 1,
                "dependencies": [1],
                "success_criteria": "Coverage confirmed in writing"
            },
            {
                "step_number": 3,
                "action": "Contact insured for detailed statement",
                "reason": "Get firsthand account",
                "priority": "high",
                "estimated_hours": 3,
                "dependencies": [1],
                "success_criteria": "Statement recorded and signed"
            }
        ]


# Singleton instance
_deepagent_instance = None


def get_deepagent_service() -> DeepAgentService:
    """Get or create deep agent service instance"""
    global _deepagent_instance
    if _deepagent_instance is None:
        _deepagent_instance = DeepAgentService()
    return _deepagent_instance
