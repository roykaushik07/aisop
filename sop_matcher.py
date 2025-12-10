"""
SOP matching logic with context-aware weighted scoring.

This module implements the intelligent matching of SOPs to investigation contexts
using keyword matching, service filters, metric patterns, and log patterns.
"""

import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass

from sop_models import (
    SOP,
    SOPMatch,
    InvestigationContext,
    DisambiguationRequest
)

logger = logging.getLogger(__name__)


@dataclass
class MatchWeights:
    """Weights for different matching criteria."""
    service_name: float = 0.30
    metric_pattern: float = 0.25
    log_pattern: float = 0.15
    confidence_booster: float = 0.10
    keyword_baseline: float = 0.20


class SOPMatcher:
    """Matches SOPs to investigation contexts using weighted scoring."""

    def __init__(
        self,
        weights: Optional[MatchWeights] = None,
        min_confidence_threshold: float = 0.3,
        disambiguation_threshold: float = 0.15
    ):
        """
        Initialize SOP matcher.

        Args:
            weights: Weights for different matching criteria
            min_confidence_threshold: Minimum confidence score to consider a match
            disambiguation_threshold: If top matches are within this delta, ask for disambiguation
        """
        self.weights = weights or MatchWeights()
        self.min_confidence_threshold = min_confidence_threshold
        self.disambiguation_threshold = disambiguation_threshold

    def find_matching_sops(
        self,
        context: InvestigationContext,
        available_sops: List[SOP]
    ) -> List[SOPMatch]:
        """
        Find matching SOPs for the given context.

        Args:
            context: Investigation context
            available_sops: List of available SOPs to match against

        Returns:
            List of SOPMatch objects, sorted by confidence score (highest first)
        """
        matches = []

        for sop in available_sops:
            # Calculate match score
            score, reasons = self._calculate_match_score(sop, context)

            # Check exclusion criteria
            if self._should_exclude(sop, context):
                logger.debug(f"SOP {sop.sop_id} excluded based on exclusion criteria")
                continue

            # Only include if above threshold
            if score >= self.min_confidence_threshold:
                match = SOPMatch(
                    sop=sop,
                    confidence_score=round(score, 3),
                    match_reasons=reasons,
                    context_highlights=self._extract_context_highlights(sop, context)
                )
                matches.append(match)

        # Sort by confidence score (highest first)
        matches.sort(key=lambda m: m.confidence_score, reverse=True)

        return matches

    def select_best_sop(
        self,
        matches: List[SOPMatch]
    ) -> Tuple[Optional[SOPMatch], Optional[DisambiguationRequest]]:
        """
        Select the best SOP from matches, or create disambiguation request.

        Args:
            matches: List of SOPMatch objects

        Returns:
            Tuple of (best_match, disambiguation_request). One will be None.
        """
        if not matches:
            return None, None

        if len(matches) == 1:
            return matches[0], None

        # Check if top matches are too close (need disambiguation)
        top_score = matches[0].confidence_score
        second_score = matches[1].confidence_score if len(matches) > 1 else 0.0

        if top_score - second_score <= self.disambiguation_threshold:
            # Need disambiguation
            disambiguation = self._create_disambiguation_request(matches[:3])
            return None, disambiguation
        else:
            # Clear winner
            return matches[0], None

    def _calculate_match_score(
        self,
        sop: SOP,
        context: InvestigationContext
    ) -> Tuple[float, List[str]]:
        """
        Calculate weighted match score for an SOP.

        Args:
            sop: The SOP to score
            context: Investigation context

        Returns:
            Tuple of (score, list of reasons for the match)
        """
        score = 0.0
        reasons = []

        # 1. Keyword matching (20% weight)
        keyword_score, keyword_reasons = self._score_keyword_match(
            sop.trigger_keywords,
            context.user_query
        )
        score += keyword_score * self.weights.keyword_baseline
        reasons.extend(keyword_reasons)

        # 2. Service name matching (30% weight)
        service_score, service_reasons = self._score_service_match(
            sop.applicability.service_filters,
            context.mentioned_services,
            context.affected_services
        )
        score += service_score * self.weights.service_name
        reasons.extend(service_reasons)

        # 3. Metric pattern matching (25% weight)
        metric_score, metric_reasons = self._score_metric_match(
            sop.applicability.metric_patterns,
            context.available_metrics
        )
        score += metric_score * self.weights.metric_pattern
        reasons.extend(metric_reasons)

        # 4. Log pattern matching (15% weight)
        log_score, log_reasons = self._score_log_match(
            sop.applicability.log_patterns,
            context.recent_log_patterns
        )
        score += log_score * self.weights.log_pattern
        reasons.extend(log_reasons)

        # 5. Confidence boosters (10% weight)
        booster_score, booster_reasons = self._score_confidence_boosters(
            sop.confidence_boosters,
            context
        )
        score += booster_score * self.weights.confidence_booster
        reasons.extend(booster_reasons)

        return min(score, 1.0), reasons

    def _score_keyword_match(
        self,
        trigger_keywords: List[str],
        query: str
    ) -> Tuple[float, List[str]]:
        """Score keyword matching."""
        query_lower = query.lower()
        matched_keywords = [
            kw for kw in trigger_keywords
            if kw.lower() in query_lower
        ]

        if not matched_keywords:
            return 0.0, []

        # Score based on percentage of keywords matched
        score = len(matched_keywords) / len(trigger_keywords)
        reasons = [f"Matched keywords: {', '.join(matched_keywords)}"]

        return score, reasons

    def _score_service_match(
        self,
        service_filters: List[str],
        mentioned_services: List[str],
        affected_services: List[str]
    ) -> Tuple[float, List[str]]:
        """Score service name matching."""
        if not service_filters:
            return 0.0, []

        all_services = set(mentioned_services + affected_services)
        matched_services = []

        for service in all_services:
            for filter_pattern in service_filters:
                if filter_pattern.lower() in service.lower() or service.lower() in filter_pattern.lower():
                    matched_services.append(service)
                    break

        if not matched_services:
            return 0.0, []

        # Higher score if multiple services match or if affected services match
        score = min(len(matched_services) / max(len(service_filters), 1), 1.0)

        # Boost score if affected services (not just mentioned) match
        affected_matched = [s for s in matched_services if s in affected_services]
        if affected_matched:
            score = min(score * 1.2, 1.0)

        reasons = [f"Matched services: {', '.join(matched_services)}"]
        if affected_matched:
            reasons.append(f"Affected services confirmed: {', '.join(affected_matched)}")

        return score, reasons

    def _score_metric_match(
        self,
        metric_patterns: List[str],
        available_metrics: dict
    ) -> Tuple[float, List[str]]:
        """Score metric pattern matching."""
        if not metric_patterns or not available_metrics:
            return 0.0, []

        matched_metrics = []

        for metric_key in available_metrics.keys():
            for pattern in metric_patterns:
                if pattern.lower() in metric_key.lower():
                    matched_metrics.append(metric_key)
                    break

        if not matched_metrics:
            return 0.0, []

        score = min(len(matched_metrics) / len(metric_patterns), 1.0)
        reasons = [f"Matched metrics: {', '.join(matched_metrics)}"]

        return score, reasons

    def _score_log_match(
        self,
        log_patterns: List[str],
        recent_log_patterns: List[str]
    ) -> Tuple[float, List[str]]:
        """Score log pattern matching."""
        if not log_patterns or not recent_log_patterns:
            return 0.0, []

        matched_patterns = []

        for log_entry in recent_log_patterns:
            for pattern in log_patterns:
                if pattern.lower() in log_entry.lower():
                    matched_patterns.append(pattern)
                    break

        if not matched_patterns:
            return 0.0, []

        score = min(len(matched_patterns) / len(log_patterns), 1.0)
        reasons = [f"Matched log patterns: {', '.join(matched_patterns)}"]

        return score, reasons

    def _score_confidence_boosters(
        self,
        boosters: list,
        context: InvestigationContext
    ) -> Tuple[float, List[str]]:
        """Score confidence boosters."""
        if not boosters:
            return 0.0, []

        total_boost = 0.0
        reasons = []

        for booster in boosters:
            condition = booster.condition.lower()
            matched = False

            # Check condition against context
            if any(condition in service.lower() for service in context.affected_services):
                matched = True
            elif any(condition in pattern.lower() for pattern in context.recent_log_patterns):
                matched = True
            elif any(condition in alert.lower() for alert in context.active_alerts):
                matched = True

            if matched:
                total_boost += booster.boost_amount
                reasons.append(f"Booster triggered: {booster.condition}")

        return min(total_boost, 1.0), reasons

    def _should_exclude(self, sop: SOP, context: InvestigationContext) -> bool:
        """Check if SOP should be excluded based on exclusion criteria."""
        exclusion = sop.exclusion

        # Check excluded services
        all_services = set(context.mentioned_services + context.affected_services)
        for excluded_service in exclusion.excluded_services:
            if any(excluded_service.lower() in service.lower() for service in all_services):
                return True

        # Check excluded conditions
        query_lower = context.user_query.lower()
        for condition in exclusion.excluded_conditions:
            if condition.lower() in query_lower:
                return True

        # Check conflicting symptoms
        for symptom in exclusion.conflicting_symptoms:
            if symptom.lower() in query_lower:
                return True
            if any(symptom.lower() in pattern.lower() for pattern in context.recent_log_patterns):
                return True

        return False

    def _extract_context_highlights(
        self,
        sop: SOP,
        context: InvestigationContext
    ) -> dict:
        """Extract key context information relevant to this SOP."""
        highlights = {}

        # Relevant services
        matched_services = [
            s for s in (context.mentioned_services + context.affected_services)
            if any(f.lower() in s.lower() for f in sop.applicability.service_filters)
        ]
        if matched_services:
            highlights["services"] = matched_services

        # Relevant metrics
        matched_metrics = {
            k: v for k, v in context.available_metrics.items()
            if any(p.lower() in k.lower() for p in sop.applicability.metric_patterns)
        }
        if matched_metrics:
            highlights["metrics"] = matched_metrics

        # Relevant log patterns
        matched_logs = [
            log for log in context.recent_log_patterns
            if any(p.lower() in log.lower() for p in sop.applicability.log_patterns)
        ]
        if matched_logs:
            highlights["logs"] = matched_logs

        return highlights

    def _create_disambiguation_request(
        self,
        top_matches: List[SOPMatch]
    ) -> DisambiguationRequest:
        """Create a disambiguation request for closely matched SOPs."""
        # Create a question based on the differences between SOPs
        sop_names = [match.sop.name for match in top_matches]
        question = (
            f"Multiple investigation procedures match your query. "
            f"Which scenario best describes your situation?\n"
            + "\n".join([
                f"{i+1}. {match.sop.name} (confidence: {match.confidence_score:.2%})"
                for i, match in enumerate(top_matches)
            ])
        )

        return DisambiguationRequest(
            matching_sops=top_matches,
            disambiguation_question=question,
            suggested_default=top_matches[0].sop.sop_id
        )
