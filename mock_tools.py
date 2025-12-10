"""
Mock implementations of observability tools for testing.

This module provides realistic mock data for various observability tools
including metrics, logs, traces, and health checks.
"""

import random
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


# Simulated state for consistent mock data within a session
_SERVICE_STATES = {
    "payment": {"health": "degraded", "error_rate": 0.15, "latency": 850},
    "payment-consumer": {"health": "degraded", "consumer_lag": 15000, "messages_per_sec": 100},
    "payment-processor": {"health": "healthy", "error_rate": 0.02, "latency": 120},
    "order": {"health": "healthy", "error_rate": 0.01, "latency": 95},
    "elasticsearch": {"health": "degraded", "query_latency": 2500, "cpu_usage": 85},
    "logstash": {"health": "degraded", "memory_usage": 92, "events_per_sec": 50},
    "kafka": {"health": "healthy", "messages_per_sec": 5000},
    "msk": {"health": "degraded", "consumer_lag": 12000},
}


def service_health_check(service_name: str) -> Dict[str, Any]:
    """
    Check the health status of a service.

    Args:
        service_name: Name of the service to check

    Returns:
        Dictionary with health status and basic metrics
    """
    state = _SERVICE_STATES.get(service_name, {"health": "healthy"})

    result = {
        "service": service_name,
        "status": state.get("health", "healthy"),
        "timestamp": datetime.utcnow().isoformat(),
        "checks": []
    }

    # Add health check details
    if state.get("health") == "degraded":
        result["checks"].append({
            "name": "availability",
            "status": "warning",
            "message": "Service experiencing issues"
        })
    else:
        result["checks"].append({
            "name": "availability",
            "status": "passing",
            "message": "Service is healthy"
        })

    # Add related services for discovery
    if "consumer" in service_name or "processor" in service_name:
        base_service = service_name.split("-")[0]
        result["related_services"] = [
            f"{base_service}-consumer",
            f"{base_service}-processor"
        ]

    return result


def query_metric(service: str, metric_name: str, time_range_minutes: int = 5) -> Dict[str, Any]:
    """
    Query a specific metric for a service.

    Args:
        service: Service name
        metric_name: Name of the metric
        time_range_minutes: Time range to query

    Returns:
        Dictionary with metric value and metadata
    """
    state = _SERVICE_STATES.get(service, {})

    # Return service-specific metrics if available
    if metric_name in state:
        value = state[metric_name]
    else:
        # Generate reasonable defaults
        value = _generate_metric_value(metric_name)

    return {
        "service": service,
        "metric": metric_name,
        "value": value,
        "timestamp": datetime.utcnow().isoformat(),
        "unit": _get_metric_unit(metric_name),
        "time_range_minutes": time_range_minutes
    }


def query_msk_metrics(cluster_name: str, consumer_group: Optional[str] = None) -> Dict[str, Any]:
    """
    Query MSK/Kafka metrics.

    Args:
        cluster_name: MSK cluster name
        consumer_group: Optional consumer group to filter

    Returns:
        Dictionary with Kafka metrics
    """
    return {
        "cluster": cluster_name,
        "consumer_group": consumer_group,
        "metrics": {
            "sum_offset_lag": 15000,
            "max_offset_lag": 18000,
            "estimated_lag_seconds": 300,
            "messages_consumed_per_sec": 100,
            "bytes_consumed_per_sec": 102400,
            "consumer_rebalances_per_hour": 3,
            "fetch_latency_avg_ms": 50,
            "commit_latency_avg_ms": 25
        },
        "partition_details": [
            {"partition": 0, "offset_lag": 5000, "current_offset": 95000, "log_end_offset": 100000},
            {"partition": 1, "offset_lag": 6000, "current_offset": 94000, "log_end_offset": 100000},
            {"partition": 2, "offset_lag": 4000, "current_offset": 96000, "log_end_offset": 100000}
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


def get_consumer_group_details(consumer_group: str, topic: Optional[str] = None) -> Dict[str, Any]:
    """
    Get Kafka consumer group details.

    Args:
        consumer_group: Consumer group name
        topic: Optional topic to filter

    Returns:
        Dictionary with consumer group information
    """
    return {
        "consumer_group": consumer_group,
        "state": "Stable",
        "members": 3,
        "lag": {
            "total": 15000,
            "by_topic": {
                "payment-events": 12000,
                "payment-dlq": 3000
            }
        },
        "topics": ["payment-events", "payment-dlq"],
        "coordinator": "kafka-broker-2",
        "last_rebalance": (datetime.utcnow() - timedelta(minutes=25)).isoformat(),
        "rebalance_count_last_hour": 3,
        "members_info": [
            {
                "member_id": "consumer-1",
                "host": "10.0.1.23",
                "assigned_partitions": [0, 1],
                "lag": 5000
            },
            {
                "member_id": "consumer-2",
                "host": "10.0.1.24",
                "assigned_partitions": [2, 3],
                "lag": 6000
            },
            {
                "member_id": "consumer-3",
                "host": "10.0.1.25",
                "assigned_partitions": [4],
                "lag": 4000
            }
        ]
    }


def query_logs(service: str, time_range_minutes: int = 5,
               pattern: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    """
    Query logs for a service.

    Args:
        service: Service name
        time_range_minutes: Time range to query
        pattern: Optional pattern to filter logs
        limit: Maximum number of log entries

    Returns:
        Dictionary with log entries
    """
    state = _SERVICE_STATES.get(service, {})
    entries = []

    # Generate relevant log entries based on service health
    if state.get("health") == "degraded":
        if "consumer" in service:
            entries = [
                {
                    "timestamp": (datetime.utcnow() - timedelta(minutes=3)).isoformat(),
                    "level": "ERROR",
                    "message": "ConsumerTimeoutException: Failed to consume messages within timeout period",
                    "thread": "consumer-thread-1"
                },
                {
                    "timestamp": (datetime.utcnow() - timedelta(minutes=2)).isoformat(),
                    "level": "WARN",
                    "message": "Consumer group rebalancing triggered due to member timeout",
                    "thread": "coordinator-thread"
                },
                {
                    "timestamp": (datetime.utcnow() - timedelta(minutes=1)).isoformat(),
                    "level": "WARN",
                    "message": "High lag detected: 15000 messages behind",
                    "thread": "lag-monitor"
                }
            ]
        elif "elasticsearch" in service or "es" in service:
            entries = [
                {
                    "timestamp": (datetime.utcnow() - timedelta(minutes=4)).isoformat(),
                    "level": "WARN",
                    "message": "Slow query detected: SELECT took 2.5s",
                    "query_time_ms": 2500
                },
                {
                    "timestamp": (datetime.utcnow() - timedelta(minutes=2)).isoformat(),
                    "level": "ERROR",
                    "message": "Circuit breaker triggered: field data cache size exceeded",
                    "cache_size_mb": 512
                },
                {
                    "timestamp": (datetime.utcnow() - timedelta(minutes=1)).isoformat(),
                    "level": "WARN",
                    "message": "GC overhead limit exceeded, performance degraded",
                    "gc_time_ms": 5000
                }
            ]
        elif "logstash" in service:
            entries = [
                {
                    "timestamp": (datetime.utcnow() - timedelta(minutes=3)).isoformat(),
                    "level": "ERROR",
                    "message": "Pipeline worker error: Out of memory",
                    "memory_usage_mb": 1800
                },
                {
                    "timestamp": (datetime.utcnow() - timedelta(minutes=2)).isoformat(),
                    "level": "WARN",
                    "message": "Pipeline queue is full, dropping events",
                    "queue_size": 10000
                },
                {
                    "timestamp": (datetime.utcnow() - timedelta(minutes=1)).isoformat(),
                    "level": "ERROR",
                    "message": "Failed to parse JSON: Unexpected end of input",
                    "event_count": 150
                }
            ]
        else:
            entries = [
                {
                    "timestamp": (datetime.utcnow() - timedelta(minutes=2)).isoformat(),
                    "level": "ERROR",
                    "message": f"Request timeout after 30s",
                    "latency_ms": 30000
                },
                {
                    "timestamp": (datetime.utcnow() - timedelta(minutes=1)).isoformat(),
                    "level": "WARN",
                    "message": "High error rate detected: 15% of requests failing",
                    "error_rate": 0.15
                }
            ]
    else:
        entries = [
            {
                "timestamp": (datetime.utcnow() - timedelta(minutes=1)).isoformat(),
                "level": "INFO",
                "message": f"{service} is operating normally"
            }
        ]

    return {
        "service": service,
        "time_range_minutes": time_range_minutes,
        "entry_count": len(entries),
        "entries": entries[:limit]
    }


def query_elasticsearch_slow_log(index: str, time_range_minutes: int = 30) -> Dict[str, Any]:
    """
    Query Elasticsearch slow log.

    Args:
        index: Index name
        time_range_minutes: Time range to query

    Returns:
        Dictionary with slow query information
    """
    return {
        "index": index,
        "time_range_minutes": time_range_minutes,
        "slow_queries": [
            {
                "timestamp": (datetime.utcnow() - timedelta(minutes=10)).isoformat(),
                "query_time_ms": 2500,
                "query": {
                    "type": "aggregation",
                    "aggregation": "terms",
                    "field": "user_id",
                    "size": 10000
                },
                "shard": "[payments][2]",
                "warning": "Large terms aggregation without pagination"
            },
            {
                "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                "query_time_ms": 3200,
                "query": {
                    "type": "wildcard",
                    "pattern": "*payment*",
                    "field": "description"
                },
                "shard": "[payments][0]",
                "warning": "Leading wildcard query is inefficient"
            }
        ],
        "total_slow_queries": 15,
        "avg_query_time_ms": 2800
    }


def get_cluster_health(cluster_type: str, cluster_name: str) -> Dict[str, Any]:
    """
    Get cluster health status.

    Args:
        cluster_type: Type of cluster (elasticsearch, kafka, etc.)
        cluster_name: Cluster name

    Returns:
        Dictionary with cluster health information
    """
    if cluster_type.lower() in ["elasticsearch", "es"]:
        return {
            "cluster_name": cluster_name,
            "status": "yellow",
            "number_of_nodes": 5,
            "active_primary_shards": 150,
            "active_shards": 285,
            "relocating_shards": 0,
            "initializing_shards": 0,
            "unassigned_shards": 15,
            "delayed_unassigned_shards": 0,
            "number_of_pending_tasks": 0,
            "task_max_waiting_in_queue_millis": 0,
            "active_shards_percent_as_number": 95.0,
            "issues": [
                "15 unassigned shards detected",
                "High CPU usage on node-3 (85%)",
                "Heap usage above 80% on 2 nodes"
            ]
        }
    elif cluster_type.lower() in ["kafka", "msk"]:
        return {
            "cluster_name": cluster_name,
            "status": "healthy",
            "broker_count": 3,
            "online_brokers": 3,
            "controller_broker": 2,
            "under_replicated_partitions": 5,
            "offline_partitions": 0,
            "total_topics": 25,
            "total_partitions": 150,
            "issues": [
                "5 under-replicated partitions detected"
            ]
        }
    else:
        return {
            "cluster_name": cluster_name,
            "status": "unknown",
            "message": f"Health check not implemented for {cluster_type}"
        }


def get_distributed_trace(trace_id: str) -> Dict[str, Any]:
    """
    Get distributed trace information.

    Args:
        trace_id: Trace identifier

    Returns:
        Dictionary with trace spans
    """
    return {
        "trace_id": trace_id,
        "duration_ms": 850,
        "spans": [
            {
                "span_id": "span-1",
                "service": "payment-api",
                "operation": "POST /payment",
                "duration_ms": 850,
                "start_time": datetime.utcnow().isoformat(),
                "tags": {"http.status_code": 200}
            },
            {
                "span_id": "span-2",
                "parent_span_id": "span-1",
                "service": "payment-processor",
                "operation": "process_payment",
                "duration_ms": 720,
                "start_time": (datetime.utcnow() + timedelta(milliseconds=50)).isoformat(),
                "tags": {"payment.amount": 99.99}
            },
            {
                "span_id": "span-3",
                "parent_span_id": "span-2",
                "service": "payment-consumer",
                "operation": "consume_kafka_message",
                "duration_ms": 650,
                "start_time": (datetime.utcnow() + timedelta(milliseconds=100)).isoformat(),
                "tags": {"kafka.topic": "payment-events", "kafka.partition": 2}
            }
        ],
        "errors": []
    }


def query_elasticsearch(index: str, query: Dict[str, Any], size: int = 10) -> Dict[str, Any]:
    """
    Query Elasticsearch.

    Args:
        index: Index to query
        query: Elasticsearch query DSL
        size: Number of results

    Returns:
        Dictionary with query results
    """
    return {
        "took": 125,
        "timed_out": False,
        "hits": {
            "total": {"value": 1523, "relation": "eq"},
            "max_score": 1.0,
            "hits": [
                {
                    "_index": index,
                    "_id": f"doc-{i}",
                    "_score": 1.0 - (i * 0.1),
                    "_source": {
                        "timestamp": (datetime.utcnow() - timedelta(minutes=i)).isoformat(),
                        "level": "ERROR" if i < 3 else "INFO",
                        "message": f"Sample log message {i}"
                    }
                }
                for i in range(min(size, 10))
            ]
        }
    }


def check_broker_status(cluster_name: str, broker_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Check Kafka broker status.

    Args:
        cluster_name: Cluster name
        broker_id: Optional specific broker to check

    Returns:
        Dictionary with broker status
    """
    if broker_id is not None:
        return {
            "cluster": cluster_name,
            "broker_id": broker_id,
            "status": "online",
            "host": f"kafka-broker-{broker_id}.internal",
            "port": 9092,
            "is_controller": broker_id == 2,
            "partition_count": 50,
            "leader_count": 45,
            "under_replicated_partitions": 2,
            "metrics": {
                "requests_per_sec": 1500,
                "bytes_in_per_sec": 1048576,
                "bytes_out_per_sec": 2097152,
                "cpu_percent": 45,
                "network_utilization": 0.3
            }
        }
    else:
        return {
            "cluster": cluster_name,
            "brokers": [
                check_broker_status(cluster_name, i)
                for i in range(1, 4)
            ]
        }


def get_alert_history(service: str, hours: int = 24) -> Dict[str, Any]:
    """
    Get alert history for a service.

    Args:
        service: Service name
        hours: Number of hours to look back

    Returns:
        Dictionary with alert history
    """
    state = _SERVICE_STATES.get(service, {})
    alerts = []

    if state.get("health") == "degraded":
        if "consumer" in service:
            alerts.append({
                "name": "HighConsumerLag",
                "severity": "warning",
                "status": "firing",
                "started_at": (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
                "message": "Consumer lag exceeds 10000 messages"
            })
        elif "elasticsearch" in service:
            alerts.append({
                "name": "SlowQueryDetected",
                "severity": "warning",
                "status": "firing",
                "started_at": (datetime.utcnow() - timedelta(minutes=15)).isoformat(),
                "message": "Query latency exceeds 2000ms"
            })

    return {
        "service": service,
        "time_range_hours": hours,
        "alerts": alerts,
        "total_alerts": len(alerts)
    }


def _generate_metric_value(metric_name: str) -> float:
    """Generate a reasonable mock value for a metric."""
    metric_ranges = {
        "error_rate": (0.01, 0.20),
        "latency": (50, 1000),
        "response_time": (50, 1000),
        "p95_latency": (100, 2000),
        "p99_latency": (200, 3000),
        "cpu_usage": (20, 90),
        "memory_usage": (40, 95),
        "requests_per_sec": (10, 5000),
        "messages_per_sec": (50, 10000),
        "consumer_lag": (0, 20000),
        "queue_depth": (0, 5000)
    }

    min_val, max_val = metric_ranges.get(metric_name, (0, 100))
    return round(random.uniform(min_val, max_val), 2)


def _get_metric_unit(metric_name: str) -> str:
    """Get the unit for a metric."""
    if "rate" in metric_name or "percent" in metric_name or "usage" in metric_name:
        return "percent"
    elif "latency" in metric_name or "time" in metric_name:
        return "milliseconds"
    elif "per_sec" in metric_name:
        return "per_second"
    elif "lag" in metric_name or "count" in metric_name or "depth" in metric_name:
        return "count"
    else:
        return "unknown"
