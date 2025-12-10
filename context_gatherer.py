"""
Context gathering system for fast diagnostic information collection.

This module provides quick context gathering (<30s) to inform SOP matching.
It collects information about services, metrics, logs, and alerts without
performing a full investigation.
"""

import re
import time
from typing import List, Dict, Any, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from sop_models import InvestigationContext
from mock_tools import (
    service_health_check,
    query_metric,
    query_logs,
    get_alert_history
)

logger = logging.getLogger(__name__)


class ContextGatherer:
    """Gathers context quickly for SOP matching."""

    def __init__(self, max_workers: int = 5, timeout_seconds: float = 25.0):
        """
        Initialize context gatherer.

        Args:
            max_workers: Maximum concurrent tasks for context gathering
            timeout_seconds: Maximum time to spend gathering context
        """
        self.max_workers = max_workers
        self.timeout_seconds = timeout_seconds

    def gather_context(self, user_query: str) -> InvestigationContext:
        """
        Gather context from user query and quick checks.

        Args:
            user_query: The user's investigation request

        Returns:
            InvestigationContext with gathered information
        """
        start_time = time.time()

        # Parse query for immediate context
        mentioned_services = self._extract_services_from_query(user_query)
        symptom_keywords = self._extract_symptom_keywords(user_query)

        # Gather context in parallel
        context_data = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._check_service_health, mentioned_services): "health",
                executor.submit(self._gather_relevant_metrics, mentioned_services, user_query): "metrics",
                executor.submit(self._scan_recent_logs, mentioned_services, symptom_keywords): "logs",
                executor.submit(self._check_active_alerts, mentioned_services): "alerts"
            }

            # Collect results with timeout
            remaining_time = self.timeout_seconds - (time.time() - start_time)

            for future in as_completed(futures, timeout=max(remaining_time, 1.0)):
                task_name = futures[future]
                try:
                    context_data[task_name] = future.result(timeout=1.0)
                except Exception as e:
                    logger.warning(f"Context gathering task '{task_name}' failed: {e}")
                    context_data[task_name] = None

        # Build context object
        context = InvestigationContext(
            user_query=user_query,
            mentioned_services=mentioned_services,
            affected_services=context_data.get("health", {}).get("affected", []),
            available_metrics=context_data.get("metrics", {}),
            recent_log_patterns=context_data.get("logs", []),
            active_alerts=context_data.get("alerts", []),
            gathering_duration_seconds=round(time.time() - start_time, 2)
        )

        logger.info(f"Context gathered in {context.gathering_duration_seconds}s")
        return context

    def _extract_services_from_query(self, query: str) -> List[str]:
        """
        Extract service names from user query.

        Args:
            query: User query text

        Returns:
            List of service names found in query
        """
        # Common service name patterns
        service_patterns = [
            r'\b([a-z]+-?[a-z]+)[-\s]+(service|consumer|producer|processor|api|worker)\b',
            r'\b(kafka|elasticsearch|logstash|msk|kinesis|redis|postgres|mysql)\b',
            r'\bservice[:\s]+([a-z-]+)\b'
        ]

        services = set()
        query_lower = query.lower()

        for pattern in service_patterns:
            matches = re.findall(pattern, query_lower)
            for match in matches:
                if isinstance(match, tuple):
                    services.update(m for m in match if m and m not in
                                  ['service', 'consumer', 'producer', 'processor', 'api', 'worker'])
                else:
                    services.add(match)

        # Also check for standalone common service names
        common_services = [
            'payment', 'order', 'user', 'auth', 'notification',
            'kafka', 'elasticsearch', 'logstash', 'msk'
        ]

        for service in common_services:
            if service in query_lower:
                services.add(service)

        return sorted(list(services))

    def _extract_symptom_keywords(self, query: str) -> List[str]:
        """
        Extract symptom keywords from query.

        Args:
            query: User query text

        Returns:
            List of symptom keywords
        """
        symptom_keywords = [
            'lag', 'latency', 'slow', 'high', 'error', 'timeout',
            'failure', 'down', 'degraded', 'spike', 'drop', 'increase',
            'memory', 'cpu', 'disk', 'connection', 'queue'
        ]

        query_lower = query.lower()
        found_symptoms = [kw for kw in symptom_keywords if kw in query_lower]

        return found_symptoms

    def _check_service_health(self, services: List[str]) -> Dict[str, Any]:
        """
        Check health status of services.

        Args:
            services: List of service names to check

        Returns:
            Dictionary with health information
        """
        if not services:
            return {"affected": [], "healthy": []}

        affected = []
        healthy = []

        for service in services:
            try:
                health = service_health_check(service)
                if health.get("status") != "healthy":
                    affected.append(service)
                else:
                    healthy.append(service)

                # Check for related services (e.g., payment -> payment-consumer, payment-processor)
                if "related_services" in health:
                    for related in health["related_services"]:
                        if related not in services:
                            related_health = service_health_check(related)
                            if related_health.get("status") != "healthy":
                                affected.append(related)
            except Exception as e:
                logger.warning(f"Health check failed for {service}: {e}")

        return {
            "affected": list(set(affected)),
            "healthy": healthy
        }

    def _gather_relevant_metrics(self, services: List[str], query: str) -> Dict[str, Any]:
        """
        Gather current metric values for services.

        Args:
            services: List of service names
            query: Original query for context

        Returns:
            Dictionary of metric names to current values
        """
        metrics = {}

        # Determine which metrics to check based on query keywords
        metric_keywords = {
            'lag': ['consumer_lag', 'offset_lag', 'replication_lag'],
            'latency': ['response_time', 'query_latency', 'p95_latency', 'p99_latency'],
            'error': ['error_rate', 'error_count', 'failure_rate'],
            'throughput': ['requests_per_sec', 'messages_per_sec', 'events_per_sec'],
            'memory': ['memory_usage', 'heap_usage', 'jvm_memory'],
            'cpu': ['cpu_usage', 'cpu_percent'],
            'queue': ['queue_depth', 'queue_size', 'pending_messages']
        }

        query_lower = query.lower()
        metrics_to_check = set()

        # Select relevant metrics based on query
        for keyword, metric_names in metric_keywords.items():
            if keyword in query_lower:
                metrics_to_check.update(metric_names)

        # If no specific metrics identified, check common ones
        if not metrics_to_check:
            metrics_to_check = {'error_rate', 'response_time', 'cpu_usage'}

        # Query metrics for each service
        for service in services:
            for metric_name in metrics_to_check:
                try:
                    result = query_metric(service, metric_name)
                    if result.get("value") is not None:
                        key = f"{service}.{metric_name}"
                        metrics[key] = result["value"]
                except Exception as e:
                    logger.debug(f"Metric query failed for {service}.{metric_name}: {e}")

        return metrics

    def _scan_recent_logs(self, services: List[str], symptom_keywords: List[str]) -> List[str]:
        """
        Scan recent logs for patterns.

        Args:
            services: List of service names
            symptom_keywords: Keywords from query

        Returns:
            List of notable log patterns found
        """
        patterns = set()

        # Common error patterns to look for
        error_patterns = [
            'Exception', 'Error', 'Timeout', 'Failed', 'Rejected',
            'OutOfMemory', 'ConnectionRefused', 'Rebalancing'
        ]

        for service in services:
            try:
                # Query recent logs (last 5 minutes)
                logs = query_logs(
                    service=service,
                    time_range_minutes=5,
                    limit=50
                )

                # Analyze log entries for patterns
                for log_entry in logs.get("entries", []):
                    message = log_entry.get("message", "")

                    # Check for error patterns
                    for pattern in error_patterns:
                        if pattern in message:
                            patterns.add(f"{service}: {pattern}")

                    # Check for symptom keywords
                    for keyword in symptom_keywords:
                        if keyword in message.lower():
                            patterns.add(f"{service}: mentions '{keyword}'")

            except Exception as e:
                logger.debug(f"Log scan failed for {service}: {e}")

        return sorted(list(patterns))

    def _check_active_alerts(self, services: List[str]) -> List[str]:
        """
        Check for active alerts on services.

        Args:
            services: List of service names

        Returns:
            List of active alert descriptions
        """
        alerts = []

        for service in services:
            try:
                alert_history = get_alert_history(service, hours=1)

                for alert in alert_history.get("alerts", []):
                    if alert.get("status") == "firing":
                        alert_desc = f"{service}: {alert.get('name', 'Unknown alert')}"
                        alerts.append(alert_desc)

            except Exception as e:
                logger.debug(f"Alert check failed for {service}: {e}")

        return alerts


def quick_context(user_query: str) -> InvestigationContext:
    """
    Convenience function for quick context gathering.

    Args:
        user_query: User's investigation request

    Returns:
        InvestigationContext with gathered information
    """
    gatherer = ContextGatherer()
    return gatherer.gather_context(user_query)
