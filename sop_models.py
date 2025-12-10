"""
Pydantic models for the Standard Operating Procedures (SOP) system.

This module defines the data structures for SOPs, including trigger keywords,
applicability checks, workflow steps, and related metadata.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ToolType(str, Enum):
    """Types of observability tools available."""
    MSK_METRICS = "query_msk_metrics"
    CONSUMER_GROUP = "get_consumer_group_details"
    LOGS = "query_logs"
    ES_SLOW_LOG = "query_elasticsearch_slow_log"
    CLUSTER_HEALTH = "get_cluster_health"
    SERVICE_HEALTH = "service_health_check"
    TRACE = "get_distributed_trace"
    ES_QUERY = "query_elasticsearch"
    BROKER_STATUS = "check_broker_status"
    METRIC_QUERY = "query_metric"
    ALERT_HISTORY = "get_alert_history"


class ApplicabilityCriteria(BaseModel):
    """Criteria for determining if an SOP applies to a situation."""
    service_filters: List[str] = Field(
        default_factory=list,
        description="Service name patterns (e.g., 'kafka', 'elasticsearch', 'msk')"
    )
    metric_patterns: List[str] = Field(
        default_factory=list,
        description="Metric patterns to check (e.g., 'consumer_lag', 'query_latency')"
    )
    log_patterns: List[str] = Field(
        default_factory=list,
        description="Log patterns indicating relevance (e.g., 'OutOfMemory', 'timeout')"
    )
    symptom_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords describing symptoms (e.g., 'slow', 'lag', 'high latency')"
    )


class ExclusionCriteria(BaseModel):
    """Criteria that would exclude this SOP from being used."""
    excluded_services: List[str] = Field(
        default_factory=list,
        description="Services where this SOP doesn't apply"
    )
    excluded_conditions: List[str] = Field(
        default_factory=list,
        description="Conditions that make this SOP inappropriate"
    )
    conflicting_symptoms: List[str] = Field(
        default_factory=list,
        description="Symptoms that indicate this SOP is wrong choice"
    )


class ConfidenceBooster(BaseModel):
    """Conditions that increase confidence in SOP selection."""
    condition: str = Field(description="What to check for")
    boost_amount: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="How much to boost confidence (0.0-1.0)"
    )


class WorkflowStep(BaseModel):
    """A single step in the SOP workflow."""
    step_number: int = Field(description="Order of this step")
    title: str = Field(description="Brief title of the step")
    description: str = Field(description="Detailed description of what to do")
    tools_to_use: List[str] = Field(
        description="List of tool names to use in this step"
    )
    guidance: str = Field(
        description="Specific guidance on how to interpret results and what to look for"
    )
    success_criteria: str = Field(
        description="How to know if this step revealed useful information"
    )
    next_step_logic: Optional[str] = Field(
        default=None,
        description="Conditional logic for determining next steps"
    )


class CommonMistake(BaseModel):
    """A common mistake to avoid when following this SOP."""
    mistake: str = Field(description="Description of the mistake")
    why_its_wrong: str = Field(description="Why this approach is problematic")
    correct_approach: str = Field(description="The right way to handle it")


class SOP(BaseModel):
    """Standard Operating Procedure for investigating specific issues."""

    # Identity
    sop_id: str = Field(description="Unique identifier for this SOP")
    name: str = Field(description="Human-readable name")
    description: str = Field(description="What this SOP helps investigate")
    version: str = Field(default="1.0", description="SOP version")

    # Matching criteria
    trigger_keywords: List[str] = Field(
        description="Keywords that trigger consideration of this SOP"
    )
    applicability: ApplicabilityCriteria = Field(
        description="Criteria for when this SOP applies"
    )
    exclusion: ExclusionCriteria = Field(
        default_factory=ExclusionCriteria,
        description="Criteria that exclude this SOP"
    )
    confidence_boosters: List[ConfidenceBooster] = Field(
        default_factory=list,
        description="Conditions that increase confidence in this SOP"
    )

    # Workflow
    workflow_steps: List[WorkflowStep] = Field(
        description="Ordered steps to follow"
    )

    # Guidance
    common_mistakes: List[CommonMistake] = Field(
        default_factory=list,
        description="Common mistakes when following this SOP"
    )

    # Relationships
    related_sops: List[str] = Field(
        default_factory=list,
        description="IDs of related SOPs that might also be relevant"
    )
    escalation_criteria: Optional[str] = Field(
        default=None,
        description="When to escalate beyond this SOP"
    )

    # Metadata
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization"
    )
    estimated_duration_minutes: Optional[int] = Field(
        default=None,
        description="Estimated time to complete this SOP"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "sop_id": "msk-consumer-lag-001",
                "name": "MSK/Kafka Consumer Lag Investigation",
                "description": "Investigates high consumer lag in Kafka/MSK services",
                "trigger_keywords": ["consumer lag", "kafka", "msk", "offset"],
                "applicability": {
                    "service_filters": ["kafka", "msk"],
                    "metric_patterns": ["consumer_lag", "offset_lag"],
                    "symptom_keywords": ["high lag", "behind", "slow consumption"]
                },
                "workflow_steps": [
                    {
                        "step_number": 1,
                        "title": "Check Consumer Group Status",
                        "description": "Get current lag metrics for the consumer group",
                        "tools_to_use": ["get_consumer_group_details", "query_msk_metrics"],
                        "guidance": "Look for lag > 10000 messages or increasing trends",
                        "success_criteria": "Identified which topics/partitions have lag"
                    }
                ]
            }
        }


class SOPMatch(BaseModel):
    """Result of matching an SOP to a context."""
    sop: SOP = Field(description="The matched SOP")
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence that this SOP is appropriate (0.0-1.0)"
    )
    match_reasons: List[str] = Field(
        description="Reasons why this SOP was matched"
    )
    context_highlights: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key context information that led to this match"
    )


class InvestigationContext(BaseModel):
    """Context gathered for SOP matching."""

    # User input
    user_query: str = Field(description="Original user query")
    mentioned_services: List[str] = Field(
        default_factory=list,
        description="Services explicitly mentioned in query"
    )

    # Discovered context
    affected_services: List[str] = Field(
        default_factory=list,
        description="Services found to be affected via health checks"
    )
    available_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Current metric values for relevant services"
    )
    recent_log_patterns: List[str] = Field(
        default_factory=list,
        description="Notable patterns found in recent logs"
    )
    active_alerts: List[str] = Field(
        default_factory=list,
        description="Currently firing alerts"
    )

    # Timing
    gathering_duration_seconds: Optional[float] = Field(
        default=None,
        description="How long context gathering took"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "user_query": "High consumer lag in payment service",
                "mentioned_services": ["payment"],
                "affected_services": ["payment-processor", "payment-consumer"],
                "available_metrics": {
                    "payment-consumer.consumer_lag": 15000,
                    "payment-consumer.messages_per_sec": 100
                },
                "recent_log_patterns": ["ConsumerTimeoutException", "Rebalancing"],
                "gathering_duration_seconds": 12.5
            }
        }


class DisambiguationRequest(BaseModel):
    """Request for user to disambiguate between multiple matching SOPs."""
    matching_sops: List[SOPMatch] = Field(
        description="SOPs that matched with similar confidence"
    )
    disambiguation_question: str = Field(
        description="Question to ask the user to narrow down the choice"
    )
    suggested_default: Optional[str] = Field(
        default=None,
        description="SOP ID to use as default if user doesn't respond"
    )
