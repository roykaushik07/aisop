"""
Elasticsearch query tools for AIOps investigations.
Each tool queries ES for specific information.
"""

def search_logstash_errors(time_range_minutes=30):
    """Search for Logstash pipeline errors."""
    return {
        "tool": "search_logstash_errors",
        "query": "index:logstash-* AND level:ERROR",
        "results": [
            {"timestamp": "2024-12-10T10:30:00", "message": "Pipeline worker error: Out of memory"},
            {"timestamp": "2024-12-10T10:28:00", "message": "Failed to process event"},
        ]
    }

def search_logstash_throughput(time_range_minutes=60):
    """Get Logstash event throughput metrics."""
    return {
        "tool": "search_logstash_throughput",
        "query": "index:metrics-* AND service:logstash AND metric:events_per_sec",
        "results": {
            "current": 50,
            "average": 500,
            "trend": "decreasing"
        }
    }

def search_kafka_consumer_lag():
    """Check Kafka consumer lag."""
    return {
        "tool": "search_kafka_consumer_lag",
        "query": "index:kafka-metrics-* AND metric:consumer_lag",
        "results": {
            "payment-consumer": {"lag": 15000, "status": "high"},
            "order-consumer": {"lag": 200, "status": "normal"}
        }
    }

def search_elasticsearch_slow_queries(time_range_minutes=30):
    """Find slow Elasticsearch queries."""
    return {
        "tool": "search_elasticsearch_slow_queries",
        "query": "index:.elasticsearch-slowlog AND took_ms:>1000",
        "results": [
            {"query": "wildcard search on large field", "took_ms": 2500},
            {"query": "aggregation without limit", "took_ms": 3200}
        ]
    }

def search_service_errors(service_name, time_range_minutes=30):
    """Search for errors in a specific service."""
    return {
        "tool": "search_service_errors",
        "query": f"index:app-logs-* AND service:{service_name} AND level:ERROR",
        "results": [
            {"timestamp": "2024-12-10T10:25:00", "message": f"{service_name}: Connection timeout"},
            {"timestamp": "2024-12-10T10:20:00", "message": f"{service_name}: NullPointerException"}
        ]
    }

def search_high_cpu_services():
    """Find services with high CPU usage."""
    return {
        "tool": "search_high_cpu_services",
        "query": "index:system-metrics-* AND metric:cpu_percent AND value:>80",
        "results": [
            {"service": "payment-processor", "cpu": 95},
            {"service": "elasticsearch-node-3", "cpu": 87}
        ]
    }

def search_high_memory_services():
    """Find services with high memory usage."""
    return {
        "tool": "search_high_memory_services",
        "query": "index:system-metrics-* AND metric:memory_percent AND value:>85",
        "results": [
            {"service": "logstash", "memory": 92},
            {"service": "elasticsearch-node-2", "memory": 88}
        ]
    }

def search_recent_deployments(hours=24):
    """Find recent deployments."""
    return {
        "tool": "search_recent_deployments",
        "query": "index:deployment-logs-* AND event:deploy",
        "results": [
            {"service": "payment-service", "version": "v2.3.1", "time": "2024-12-10T09:00:00"},
            {"service": "order-service", "version": "v1.8.2", "time": "2024-12-10T08:30:00"}
        ]
    }

def search_alert_history(service_name=None, hours=24):
    """Search alert history."""
    query = "index:alerts-* AND status:firing"
    if service_name:
        query += f" AND service:{service_name}"

    return {
        "tool": "search_alert_history",
        "query": query,
        "results": [
            {"alert": "HighCPU", "service": "payment-processor", "since": "30m ago"},
            {"alert": "HighMemory", "service": "logstash", "since": "45m ago"}
        ]
    }

def search_network_errors():
    """Search for network-related errors."""
    return {
        "tool": "search_network_errors",
        "query": "index:app-logs-* AND (message:*timeout* OR message:*connection*refused*)",
        "results": [
            {"service": "payment-service", "error": "Connection timeout to database", "count": 45},
            {"service": "order-service", "error": "Connection refused", "count": 12}
        ]
    }


# Tool registry for agent
TOOLS = {
    "search_logstash_errors": search_logstash_errors,
    "search_logstash_throughput": search_logstash_throughput,
    "search_kafka_consumer_lag": search_kafka_consumer_lag,
    "search_elasticsearch_slow_queries": search_elasticsearch_slow_queries,
    "search_service_errors": search_service_errors,
    "search_high_cpu_services": search_high_cpu_services,
    "search_high_memory_services": search_high_memory_services,
    "search_recent_deployments": search_recent_deployments,
    "search_alert_history": search_alert_history,
    "search_network_errors": search_network_errors,
}
