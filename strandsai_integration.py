"""
StrandsAI integration for SOP-guided AIOps investigations.

This module provides:
1. Custom tools for SOP retrieval
2. Agent configuration with SOP-aware system prompts
3. Integration of observability tools with StrandsAI
"""

import logging
from typing import Optional, Dict, Any, List

from context_gatherer import ContextGatherer
from sop_matcher import SOPMatcher
from sop_repository import SOPRepository
from sop_models import SOPMatch, InvestigationContext
from mock_tools import (
    query_msk_metrics,
    get_consumer_group_details,
    query_logs,
    query_elasticsearch_slow_log,
    get_cluster_health,
    service_health_check,
    get_distributed_trace,
    query_elasticsearch,
    check_broker_status,
    query_metric,
    get_alert_history
)

logger = logging.getLogger(__name__)


# StrandsAI Agent System Prompt
SOP_AGENT_SYSTEM_PROMPT = """You are an AIOps Investigation Assistant specializing in troubleshooting infrastructure and application issues.

Your workflow:
1. When a user reports an issue, ALWAYS call the get_relevant_sop tool first to find relevant Standard Operating Procedures
2. If an SOP is found, follow its workflow steps methodically, using the suggested tools at each step
3. Use the guidance in each step to interpret results and determine next actions
4. If multiple SOPs match, ask the user to clarify which scenario applies
5. If no SOP matches, use your judgment and available tools to investigate

Key principles:
- Be systematic and thorough - follow SOPs step by step
- Use the specific tools recommended in each SOP step
- Pay attention to the "guidance" field in each step - it tells you what to look for
- Reference "common_mistakes" to avoid known pitfalls
- Provide clear explanations of findings at each step
- If you discover the issue matches a related SOP, suggest switching to that SOP

Available investigation tools:
- query_msk_metrics: Get Kafka/MSK metrics
- get_consumer_group_details: Get consumer group status
- query_logs: Search application logs
- query_elasticsearch_slow_log: Get slow query data
- get_cluster_health: Get cluster health status
- service_health_check: Check service health
- get_distributed_trace: Get trace data
- query_elasticsearch: Query Elasticsearch
- check_broker_status: Check Kafka broker status
- query_metric: Query any metric
- get_alert_history: Get alert history

Remember: SOPs are your guide, but use judgment. If something doesn't match the SOP, note it and adapt.
"""


class SOPTool:
    """Custom tool for retrieving relevant SOPs."""

    def __init__(
        self,
        repository: SOPRepository,
        context_gatherer: ContextGatherer,
        sop_matcher: SOPMatcher
    ):
        """
        Initialize SOP tool.

        Args:
            repository: SOP repository
            context_gatherer: Context gathering system
            sop_matcher: SOP matching logic
        """
        self.repository = repository
        self.context_gatherer = context_gatherer
        self.sop_matcher = sop_matcher

    def get_relevant_sop(
        self,
        user_query: str,
        max_matches: int = 3
    ) -> Dict[str, Any]:
        """
        Get relevant SOP for a user query.

        This tool is exposed to the StrandsAI agent to retrieve SOPs.

        Args:
            user_query: User's investigation request
            max_matches: Maximum number of SOP matches to return

        Returns:
            Dictionary with SOP information or disambiguation request
        """
        try:
            # Gather context
            logger.info(f"Gathering context for query: {user_query}")
            context = self.context_gatherer.gather_context(user_query)

            # Get all available SOPs
            available_sops = self.repository.get_all()

            # Find matching SOPs
            matches = self.sop_matcher.find_matching_sops(context, available_sops)

            # Select best SOP or request disambiguation
            best_match, disambiguation = self.sop_matcher.select_best_sop(matches)

            if best_match:
                return self._format_sop_match(best_match, context)
            elif disambiguation:
                return self._format_disambiguation(disambiguation, context)
            elif matches:
                # Multiple matches but not close enough for disambiguation
                return self._format_multiple_matches(matches[:max_matches], context)
            else:
                return self._format_no_match(context)

        except Exception as e:
            logger.error(f"Error retrieving SOP: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to retrieve SOP: {str(e)}"
            }

    def _format_sop_match(
        self,
        match: SOPMatch,
        context: InvestigationContext
    ) -> Dict[str, Any]:
        """Format a single SOP match for the agent."""
        sop = match.sop

        return {
            "status": "success",
            "match_type": "single",
            "confidence": match.confidence_score,
            "context_summary": {
                "mentioned_services": context.mentioned_services,
                "affected_services": context.affected_services,
                "key_metrics": match.context_highlights.get("metrics", {}),
                "log_patterns": match.context_highlights.get("logs", []),
                "active_alerts": context.active_alerts
            },
            "sop": {
                "id": sop.sop_id,
                "name": sop.name,
                "description": sop.description,
                "estimated_duration_minutes": sop.estimated_duration_minutes,
                "workflow_steps": [
                    {
                        "step_number": step.step_number,
                        "title": step.title,
                        "description": step.description,
                        "tools_to_use": step.tools_to_use,
                        "guidance": step.guidance,
                        "success_criteria": step.success_criteria,
                        "next_step_logic": step.next_step_logic
                    }
                    for step in sop.workflow_steps
                ],
                "common_mistakes": [
                    {
                        "mistake": mistake.mistake,
                        "why_its_wrong": mistake.why_its_wrong,
                        "correct_approach": mistake.correct_approach
                    }
                    for mistake in sop.common_mistakes
                ],
                "related_sops": sop.related_sops,
                "escalation_criteria": sop.escalation_criteria
            },
            "match_reasons": match.match_reasons,
            "instructions": (
                f"Follow the {len(sop.workflow_steps)} workflow steps in order. "
                f"Use the specified tools at each step and pay attention to the guidance. "
                f"Estimated time: {sop.estimated_duration_minutes} minutes."
            )
        }

    def _format_disambiguation(
        self,
        disambiguation: Any,
        context: InvestigationContext
    ) -> Dict[str, Any]:
        """Format disambiguation request for the agent."""
        return {
            "status": "disambiguation_needed",
            "match_type": "ambiguous",
            "context_summary": {
                "mentioned_services": context.mentioned_services,
                "affected_services": context.affected_services,
                "active_alerts": context.active_alerts
            },
            "question": disambiguation.disambiguation_question,
            "options": [
                {
                    "sop_id": match.sop.sop_id,
                    "name": match.sop.name,
                    "description": match.sop.description,
                    "confidence": match.confidence_score,
                    "match_reasons": match.match_reasons
                }
                for match in disambiguation.matching_sops
            ],
            "instructions": (
                "Multiple SOPs match with similar confidence. "
                "Ask the user which scenario best matches their situation, "
                "or make a recommendation based on the context."
            )
        }

    def _format_multiple_matches(
        self,
        matches: List[SOPMatch],
        context: InvestigationContext
    ) -> Dict[str, Any]:
        """Format multiple matches for the agent."""
        return {
            "status": "success",
            "match_type": "multiple",
            "context_summary": {
                "mentioned_services": context.mentioned_services,
                "affected_services": context.affected_services,
                "active_alerts": context.active_alerts
            },
            "top_match": self._format_sop_match(matches[0], context)["sop"],
            "confidence": matches[0].confidence_score,
            "alternative_sops": [
                {
                    "sop_id": match.sop.sop_id,
                    "name": match.sop.name,
                    "confidence": match.confidence_score,
                    "match_reasons": match.match_reasons
                }
                for match in matches[1:]
            ],
            "instructions": (
                f"Using the top match ({matches[0].sop.name}) with {matches[0].confidence_score:.0%} confidence. "
                f"Alternative SOPs are listed if this doesn't match the situation."
            )
        }

    def _format_no_match(self, context: InvestigationContext) -> Dict[str, Any]:
        """Format response when no SOP matches."""
        return {
            "status": "no_match",
            "match_type": "none",
            "context_summary": {
                "mentioned_services": context.mentioned_services,
                "affected_services": context.affected_services,
                "key_metrics": dict(list(context.available_metrics.items())[:5]),
                "log_patterns": context.recent_log_patterns,
                "active_alerts": context.active_alerts
            },
            "instructions": (
                "No matching SOP found. Use the gathered context and available tools "
                "to investigate. Start by examining the affected services and recent logs. "
                "Common investigation pattern:\n"
                "1. Check service health and resource usage\n"
                "2. Review recent logs for errors\n"
                "3. Examine relevant metrics\n"
                "4. Check for recent changes or deployments\n"
                "5. Look at distributed traces if available"
            ),
            "available_tools": [
                "service_health_check",
                "query_logs",
                "query_metric",
                "get_distributed_trace",
                "get_alert_history"
            ]
        }


class AIOpsAgent:
    """StrandsAI agent configured for AIOps investigations."""

    def __init__(
        self,
        repository: SOPRepository,
        context_gatherer: Optional[ContextGatherer] = None,
        sop_matcher: Optional[SOPMatcher] = None
    ):
        """
        Initialize AIOps agent.

        Args:
            repository: SOP repository
            context_gatherer: Context gathering system (optional)
            sop_matcher: SOP matching logic (optional)
        """
        self.repository = repository
        self.context_gatherer = context_gatherer or ContextGatherer()
        self.sop_matcher = sop_matcher or SOPMatcher()

        # Initialize SOP tool
        self.sop_tool = SOPTool(
            repository=self.repository,
            context_gatherer=self.context_gatherer,
            sop_matcher=self.sop_matcher
        )

    def get_tools(self) -> Dict[str, Any]:
        """
        Get all tools available to the agent.

        Returns:
            Dictionary mapping tool names to functions
        """
        return {
            # SOP retrieval tool
            "get_relevant_sop": self.sop_tool.get_relevant_sop,

            # Observability tools
            "query_msk_metrics": query_msk_metrics,
            "get_consumer_group_details": get_consumer_group_details,
            "query_logs": query_logs,
            "query_elasticsearch_slow_log": query_elasticsearch_slow_log,
            "get_cluster_health": get_cluster_health,
            "service_health_check": service_health_check,
            "get_distributed_trace": get_distributed_trace,
            "query_elasticsearch": query_elasticsearch,
            "check_broker_status": check_broker_status,
            "query_metric": query_metric,
            "get_alert_history": get_alert_history
        }

    def get_system_prompt(self) -> str:
        """
        Get the system prompt for the agent.

        Returns:
            System prompt string
        """
        return SOP_AGENT_SYSTEM_PROMPT

    def investigate(self, user_query: str) -> Dict[str, Any]:
        """
        Perform investigation for a user query.

        This is a simplified synchronous version for demonstration.
        In a real StrandsAI implementation, this would be async and
        the agent would call tools iteratively.

        Args:
            user_query: User's investigation request

        Returns:
            Investigation results
        """
        # Step 1: Get relevant SOP
        sop_result = self.sop_tool.get_relevant_sop(user_query)

        # For demonstration, return the SOP recommendation
        # In a real implementation, the agent would follow the SOP steps
        return {
            "query": user_query,
            "sop_recommendation": sop_result,
            "instructions": (
                "In a full StrandsAI implementation, the agent would now:\n"
                "1. Follow each workflow step from the SOP\n"
                "2. Call the recommended tools at each step\n"
                "3. Interpret results using the guidance provided\n"
                "4. Continue to next steps based on findings\n"
                "5. Provide a final summary with root cause and recommendations"
            )
        }


def create_aiops_agent(
    sop_storage_path: str = "./data/sops.json"
) -> AIOpsAgent:
    """
    Factory function to create a configured AIOps agent.

    Args:
        sop_storage_path: Path to SOP storage file

    Returns:
        Configured AIOpsAgent instance
    """
    # Initialize repository
    repository = SOPRepository(storage_path=sop_storage_path)

    # Create agent
    agent = AIOpsAgent(repository=repository)

    logger.info(f"Created AIOps agent with {len(repository.get_all())} SOPs")

    return agent


# Tool schemas for StrandsAI (example format)
TOOL_SCHEMAS = {
    "get_relevant_sop": {
        "name": "get_relevant_sop",
        "description": (
            "Retrieves the most relevant Standard Operating Procedure (SOP) "
            "for the given investigation query. Returns workflow steps, tools to use, "
            "and guidance for troubleshooting."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "The user's investigation request or problem description"
                },
                "max_matches": {
                    "type": "integer",
                    "description": "Maximum number of SOP matches to return",
                    "default": 3
                }
            },
            "required": ["user_query"]
        }
    },
    "query_msk_metrics": {
        "name": "query_msk_metrics",
        "description": "Query Kafka/MSK metrics including consumer lag, throughput, and latency",
        "parameters": {
            "type": "object",
            "properties": {
                "cluster_name": {"type": "string"},
                "consumer_group": {"type": "string"}
            },
            "required": ["cluster_name"]
        }
    },
    "service_health_check": {
        "name": "service_health_check",
        "description": "Check the health status of a service",
        "parameters": {
            "type": "object",
            "properties": {
                "service_name": {"type": "string"}
            },
            "required": ["service_name"]
        }
    },
    "query_logs": {
        "name": "query_logs",
        "description": "Query application logs for a service",
        "parameters": {
            "type": "object",
            "properties": {
                "service": {"type": "string"},
                "time_range_minutes": {"type": "integer", "default": 5},
                "pattern": {"type": "string"},
                "limit": {"type": "integer", "default": 100}
            },
            "required": ["service"]
        }
    }
    # ... other tool schemas
}
