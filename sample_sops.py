"""
Sample Standard Operating Procedures for common AIOps scenarios.

This module defines realistic SOPs for:
1. MSK/Kafka Consumer Lag Investigation
2. Elasticsearch Query Performance Issues
3. High Latency Triage (disambiguation SOP)
4. Logstash Pipeline Issues
"""

from sop_models import (
    SOP,
    ApplicabilityCriteria,
    ExclusionCriteria,
    ConfidenceBooster,
    WorkflowStep,
    CommonMistake
)


def get_msk_consumer_lag_sop() -> SOP:
    """SOP for investigating MSK/Kafka consumer lag issues."""
    return SOP(
        sop_id="msk-consumer-lag-001",
        name="MSK/Kafka Consumer Lag Investigation",
        description="Investigates high consumer lag in Kafka/MSK services",
        version="1.0",

        trigger_keywords=[
            "consumer lag",
            "kafka lag",
            "msk lag",
            "offset lag",
            "behind",
            "slow consumption"
        ],

        applicability=ApplicabilityCriteria(
            service_filters=["kafka", "msk", "consumer"],
            metric_patterns=["consumer_lag", "offset_lag", "messages_per_sec"],
            log_patterns=["ConsumerTimeout", "Rebalancing", "CommitFailed"],
            symptom_keywords=["high lag", "behind", "slow", "not consuming"]
        ),

        exclusion=ExclusionCriteria(
            excluded_services=["elasticsearch", "logstash"],
            excluded_conditions=["producer", "broker down"],
            conflicting_symptoms=["no messages in topic", "topic deleted"]
        ),

        confidence_boosters=[
            ConfidenceBooster(
                condition="rebalancing",
                boost_amount=0.15
            ),
            ConfidenceBooster(
                condition="timeout",
                boost_amount=0.10
            ),
            ConfidenceBooster(
                condition="partition",
                boost_amount=0.05
            )
        ],

        workflow_steps=[
            WorkflowStep(
                step_number=1,
                title="Verify Consumer Lag Metrics",
                description=(
                    "Check current lag metrics to confirm the issue and identify severity. "
                    "Determine which consumer groups, topics, and partitions are affected."
                ),
                tools_to_use=["get_consumer_group_details", "query_msk_metrics"],
                guidance=(
                    "Look for:\n"
                    "- Total lag > 10,000 messages indicates significant issue\n"
                    "- Lag increasing over time suggests consumer can't keep up\n"
                    "- Lag stable but high might indicate consumer is down\n"
                    "- Check lag per partition to identify hotspots"
                ),
                success_criteria=(
                    "Confirmed lag exists and identified specific consumer groups and topics affected"
                )
            ),
            WorkflowStep(
                step_number=2,
                title="Check Consumer Group Health",
                description=(
                    "Examine consumer group status, member count, and recent rebalancing activity. "
                    "Verify all expected consumers are active and processing."
                ),
                tools_to_use=["get_consumer_group_details", "service_health_check"],
                guidance=(
                    "Investigate:\n"
                    "- Is consumer group in 'Stable' state?\n"
                    "- Are all expected members present and active?\n"
                    "- Have there been recent rebalances? (> 3/hour is concerning)\n"
                    "- Are partitions evenly distributed across consumers?\n"
                    "- Check if any consumer members are stuck or not committing offsets"
                ),
                success_criteria=(
                    "Identified consumer group state and any issues with members or rebalancing"
                )
            ),
            WorkflowStep(
                step_number=3,
                title="Analyze Consumer Application Logs",
                description=(
                    "Review recent logs from consumer applications to identify errors, "
                    "timeouts, or performance issues that could cause slow consumption."
                ),
                tools_to_use=["query_logs"],
                guidance=(
                    "Look for:\n"
                    "- ConsumerTimeoutException: Indicates slow message processing\n"
                    "- CommitFailedException: Consumer taking too long to process\n"
                    "- Rebalancing messages: Too frequent rebalancing disrupts consumption\n"
                    "- OutOfMemoryError or GC pressure: Resource constraints\n"
                    "- Application-specific errors during message processing"
                ),
                success_criteria=(
                    "Identified specific errors or patterns in consumer logs that explain lag"
                )
            ),
            WorkflowStep(
                step_number=4,
                title="Check Kafka Broker Health",
                description=(
                    "Verify Kafka/MSK broker health to ensure lag is not caused by "
                    "broker-side issues like under-replication or broker failures."
                ),
                tools_to_use=["check_broker_status", "get_cluster_health"],
                guidance=(
                    "Check:\n"
                    "- Are all brokers online and healthy?\n"
                    "- Any under-replicated partitions? (Should be 0)\n"
                    "- Broker resource utilization (CPU, network, disk I/O)\n"
                    "- Fetch latency from brokers (should be < 100ms)\n"
                    "If brokers are degraded, consumer lag may be a symptom, not the root cause"
                ),
                success_criteria=(
                    "Confirmed broker health status and ruled out broker-side causes"
                )
            ),
            WorkflowStep(
                step_number=5,
                title="Assess Consumer Processing Performance",
                description=(
                    "Evaluate consumer application performance metrics to determine if "
                    "slow processing is causing the lag."
                ),
                tools_to_use=["query_metric", "get_distributed_trace"],
                guidance=(
                    "Analyze:\n"
                    "- Message processing time per record (should be < 100ms for most use cases)\n"
                    "- Consumer CPU and memory usage\n"
                    "- Downstream service latencies (databases, APIs)\n"
                    "- Thread pool utilization and queue depths\n"
                    "If processing time is high, investigate what's slowing down each message"
                ),
                success_criteria=(
                    "Identified performance bottleneck in consumer processing logic"
                )
            )
        ],

        common_mistakes=[
            CommonMistake(
                mistake="Immediately scaling up consumers without investigation",
                why_its_wrong=(
                    "If consumers are already struggling due to bugs or downstream issues, "
                    "adding more consumers will worsen the problem (more rebalancing, "
                    "more load on downstream services)"
                ),
                correct_approach=(
                    "First identify why existing consumers are slow, then scale if needed"
                )
            ),
            CommonMistake(
                mistake="Focusing only on lag numbers without checking consumer health",
                why_its_wrong=(
                    "High lag with stable consumer group might mean consumers are actually down, "
                    "not just slow. Need to verify consumers are running."
                ),
                correct_approach=(
                    "Always check consumer group status and member health before investigating lag"
                )
            ),
            CommonMistake(
                mistake="Ignoring frequent rebalancing",
                why_its_wrong=(
                    "Rebalancing stops all consumption temporarily. Frequent rebalancing "
                    "(caused by timeouts or unstable consumers) is often the root cause of lag"
                ),
                correct_approach=(
                    "Check rebalancing frequency first and investigate what's triggering it"
                )
            )
        ],

        related_sops=["kafka-broker-issues-001", "performance-degradation-001"],
        escalation_criteria=(
            "Escalate if: lag continues growing despite healthy consumers, "
            "broker-side issues detected, or data loss risk exists"
        ),

        tags=["kafka", "msk", "consumer", "lag", "messaging"],
        estimated_duration_minutes=20
    )


def get_elasticsearch_performance_sop() -> SOP:
    """SOP for investigating Elasticsearch query performance issues."""
    return SOP(
        sop_id="elasticsearch-perf-001",
        name="Elasticsearch Query Performance Investigation",
        description="Investigates slow query and performance issues in Elasticsearch",
        version="1.0",

        trigger_keywords=[
            "elasticsearch slow",
            "es slow query",
            "query latency",
            "search performance",
            "elasticsearch timeout"
        ],

        applicability=ApplicabilityCriteria(
            service_filters=["elasticsearch", "es"],
            metric_patterns=["query_latency", "search_latency", "p95_latency", "p99_latency"],
            log_patterns=["slow query", "timeout", "circuit breaker"],
            symptom_keywords=["slow", "timeout", "performance", "latency"]
        ),

        exclusion=ExclusionCriteria(
            excluded_services=["kafka", "msk", "logstash"],
            excluded_conditions=["cluster down", "no connection"],
            conflicting_symptoms=["indexing", "writing", "ingestion"]
        ),

        confidence_boosters=[
            ConfidenceBooster(
                condition="circuit breaker",
                boost_amount=0.20
            ),
            ConfidenceBooster(
                condition="heap",
                boost_amount=0.15
            ),
            ConfidenceBooster(
                condition="shard",
                boost_amount=0.10
            )
        ],

        workflow_steps=[
            WorkflowStep(
                step_number=1,
                title="Verify Query Latency Metrics",
                description=(
                    "Confirm slow query issue and establish baseline of query performance. "
                    "Identify which queries or query types are slow."
                ),
                tools_to_use=["query_metric", "query_elasticsearch_slow_log"],
                guidance=(
                    "Check:\n"
                    "- P95/P99 query latency (should be < 500ms for most use cases)\n"
                    "- Compare current latency to historical baseline\n"
                    "- Review slow query log for specific slow queries\n"
                    "- Identify if all queries are slow or just specific patterns"
                ),
                success_criteria=(
                    "Confirmed latency issue and identified slow query patterns"
                )
            ),
            WorkflowStep(
                step_number=2,
                title="Check Cluster Health and Resources",
                description=(
                    "Examine Elasticsearch cluster health, node status, and resource utilization "
                    "to identify infrastructure issues affecting performance."
                ),
                tools_to_use=["get_cluster_health", "query_metric"],
                guidance=(
                    "Investigate:\n"
                    "- Cluster status (should be 'green', 'yellow' indicates issues)\n"
                    "- Unassigned shards (should be 0)\n"
                    "- Node CPU usage (> 80% indicates resource constraint)\n"
                    "- Heap memory usage (> 75% is concerning, > 85% critical)\n"
                    "- Disk I/O and disk space\n"
                    "- Circuit breaker status (field data, request, parent breakers)"
                ),
                success_criteria=(
                    "Identified cluster health status and resource bottlenecks"
                )
            ),
            WorkflowStep(
                step_number=3,
                title="Analyze Slow Query Patterns",
                description=(
                    "Deep dive into slow queries to identify anti-patterns, inefficient queries, "
                    "or problematic query structures."
                ),
                tools_to_use=["query_elasticsearch_slow_log", "query_logs"],
                guidance=(
                    "Look for:\n"
                    "- Wildcard queries (especially leading wildcards like '*term')\n"
                    "- Large aggregations without pagination (size > 1000)\n"
                    "- Queries without proper filtering or too broad\n"
                    "- Script queries (can be very slow)\n"
                    "- Deep pagination (from + size > 10,000)\n"
                    "- Queries against non-indexed fields"
                ),
                success_criteria=(
                    "Identified specific query patterns causing slow performance"
                )
            ),
            WorkflowStep(
                step_number=4,
                title="Check Index Health and Shard Distribution",
                description=(
                    "Examine index configuration, shard distribution, and segment health "
                    "as these can significantly impact query performance."
                ),
                tools_to_use=["query_elasticsearch", "get_cluster_health"],
                guidance=(
                    "Analyze:\n"
                    "- Number of shards per index (too many small shards hurts performance)\n"
                    "- Shard size distribution (should be balanced)\n"
                    "- Number of segments per shard (force merge if too many)\n"
                    "- Index mapping and field data cache usage\n"
                    "- Whether indices need to be reindexed with better settings"
                ),
                success_criteria=(
                    "Identified index or shard configuration issues affecting performance"
                )
            ),
            WorkflowStep(
                step_number=5,
                title="Review Recent Changes and GC Activity",
                description=(
                    "Check for recent changes (reindexing, config changes) and examine "
                    "garbage collection activity that might explain performance degradation."
                ),
                tools_to_use=["query_logs", "query_metric"],
                guidance=(
                    "Investigate:\n"
                    "- Recent deployments or configuration changes\n"
                    "- Index template or mapping updates\n"
                    "- GC frequency and duration (long GC pauses cause timeouts)\n"
                    "- Query pattern changes (new application features)\n"
                    "- Data volume growth (indices growing too large)"
                ),
                success_criteria=(
                    "Identified recent changes or GC issues contributing to slow queries"
                )
            )
        ],

        common_mistakes=[
            CommonMistake(
                mistake="Immediately increasing cluster size without identifying the issue",
                why_its_wrong=(
                    "If the problem is inefficient queries or bad mappings, "
                    "adding nodes won't help and wastes resources"
                ),
                correct_approach=(
                    "First identify if issue is resource-based or query-based, "
                    "then scale or optimize accordingly"
                )
            ),
            CommonMistake(
                mistake="Ignoring the slow query log",
                why_its_wrong=(
                    "Slow query log directly shows problematic queries, "
                    "ignoring it means missing the most obvious clues"
                ),
                correct_approach=(
                    "Always check slow query log first to see actual slow queries"
                )
            ),
            CommonMistake(
                mistake="Focusing only on average latency instead of P95/P99",
                why_its_wrong=(
                    "Average can be misleading if only some queries are slow. "
                    "P95/P99 show tail latency which affects user experience"
                ),
                correct_approach=(
                    "Use P95/P99 metrics to understand worst-case performance"
                )
            )
        ],

        related_sops=["elasticsearch-indexing-001", "high-latency-triage-001"],
        escalation_criteria=(
            "Escalate if: cluster health is red, data loss risk, "
            "performance requires major architecture changes"
        ),

        tags=["elasticsearch", "performance", "query", "latency"],
        estimated_duration_minutes=25
    )


def get_high_latency_triage_sop() -> SOP:
    """SOP for triaging generic high latency issues (disambiguation)."""
    return SOP(
        sop_id="high-latency-triage-001",
        name="High Latency Triage and Classification",
        description=(
            "Triage procedure for high latency issues to determine the specific "
            "component or service causing latency and route to appropriate detailed SOP"
        ),
        version="1.0",

        trigger_keywords=[
            "high latency",
            "slow response",
            "timeout",
            "performance issue",
            "slow"
        ],

        applicability=ApplicabilityCriteria(
            service_filters=[],  # Applies to any service
            metric_patterns=["latency", "response_time", "duration"],
            log_patterns=["timeout", "slow"],
            symptom_keywords=["latency", "slow", "timeout", "performance"]
        ),

        exclusion=ExclusionCriteria(
            excluded_services=[],
            excluded_conditions=["down", "offline", "unreachable"],
            conflicting_symptoms=["error 5xx", "crash"]
        ),

        confidence_boosters=[
            ConfidenceBooster(
                condition="p95",
                boost_amount=0.05
            ),
            ConfidenceBooster(
                condition="p99",
                boost_amount=0.05
            )
        ],

        workflow_steps=[
            WorkflowStep(
                step_number=1,
                title="Identify Affected Services and Components",
                description=(
                    "Determine which services or components are experiencing high latency. "
                    "Use distributed tracing and service mesh data to map the request flow."
                ),
                tools_to_use=["service_health_check", "get_distributed_trace", "query_metric"],
                guidance=(
                    "Questions to answer:\n"
                    "- Which service(s) are affected?\n"
                    "- Is latency at the API gateway, service layer, or data layer?\n"
                    "- Are all endpoints slow or specific ones?\n"
                    "- Look at trace data to see where time is spent\n"
                    "- Check service health to narrow down suspects"
                ),
                success_criteria=(
                    "Identified specific service(s) or layer(s) contributing most to latency"
                )
            ),
            WorkflowStep(
                step_number=2,
                title="Classify Latency Type",
                description=(
                    "Determine the type of latency issue to route to the appropriate detailed SOP."
                ),
                tools_to_use=["query_logs", "query_metric"],
                guidance=(
                    "Classify as:\n"
                    "- Database latency: Slow queries, connection pool exhaustion\n"
                    "- Message queue latency: Consumer lag, high queue depth\n"
                    "- External API latency: Third-party service delays\n"
                    "- Network latency: High network RTT, packet loss\n"
                    "- Application latency: CPU/memory pressure, inefficient code\n"
                    "- Cache miss: Cache unavailable or cold cache"
                ),
                success_criteria=(
                    "Classified latency type and identified appropriate next steps"
                ),
                next_step_logic=(
                    "Route to specific SOP based on classification:\n"
                    "- Kafka/MSK consumer lag → msk-consumer-lag-001\n"
                    "- Elasticsearch slow queries → elasticsearch-perf-001\n"
                    "- Database issues → database-perf-001\n"
                    "- General application → application-perf-001"
                )
            ),
            WorkflowStep(
                step_number=3,
                title="Check for Recent Changes",
                description=(
                    "Identify any recent deployments, configuration changes, or traffic "
                    "pattern changes that correlate with latency increase."
                ),
                tools_to_use=["query_logs", "query_metric"],
                guidance=(
                    "Look for:\n"
                    "- Deployments in the last 24 hours\n"
                    "- Configuration changes (scaling, feature flags)\n"
                    "- Traffic increases or pattern changes\n"
                    "- Upstream service changes\n"
                    "Recent changes are often the root cause"
                ),
                success_criteria=(
                    "Identified or ruled out recent changes as cause"
                )
            ),
            WorkflowStep(
                step_number=4,
                title="Assess Immediate Mitigation Options",
                description=(
                    "While root cause investigation continues, identify quick mitigations "
                    "to reduce user impact."
                ),
                tools_to_use=["service_health_check"],
                guidance=(
                    "Consider:\n"
                    "- Rollback recent deployment if correlation exists\n"
                    "- Scale up resources if resource-constrained\n"
                    "- Enable additional caching\n"
                    "- Rate limit or shed load if overloaded\n"
                    "- Failover to backup region/cluster"
                ),
                success_criteria=(
                    "Identified mitigation options with clear trade-offs"
                )
            )
        ],

        common_mistakes=[
            CommonMistake(
                mistake="Jumping to solutions without proper triage",
                why_its_wrong=(
                    "Without understanding where latency originates, "
                    "you might optimize the wrong component"
                ),
                correct_approach=(
                    "Always trace the request flow to identify bottleneck first"
                )
            ),
            CommonMistake(
                mistake="Looking only at average latency",
                why_its_wrong=(
                    "Latency issues often affect only a percentage of requests. "
                    "Averages hide these tail latency problems"
                ),
                correct_approach=(
                    "Check P95, P99 latency and look at latency distribution"
                )
            )
        ],

        related_sops=[
            "msk-consumer-lag-001",
            "elasticsearch-perf-001",
            "database-perf-001",
            "application-perf-001"
        ],
        escalation_criteria=(
            "Escalate if: unable to identify root cause within 30 minutes, "
            "requires architecture changes, or affecting critical services"
        ),

        tags=["latency", "performance", "triage", "disambiguation"],
        estimated_duration_minutes=15
    )


def get_logstash_pipeline_sop() -> SOP:
    """SOP for investigating Logstash pipeline issues."""
    return SOP(
        sop_id="logstash-pipeline-001",
        name="Logstash Pipeline Issues Investigation",
        description="Investigates Logstash pipeline failures, backpressure, and performance issues",
        version="1.0",

        trigger_keywords=[
            "logstash",
            "pipeline",
            "log ingestion",
            "logstash error",
            "pipeline stuck"
        ],

        applicability=ApplicabilityCriteria(
            service_filters=["logstash"],
            metric_patterns=["events_per_sec", "pipeline_queue", "memory_usage"],
            log_patterns=["pipeline", "OutOfMemory", "parsing error"],
            symptom_keywords=["stuck", "slow", "failing", "memory", "queue"]
        ),

        exclusion=ExclusionCriteria(
            excluded_services=["kafka", "elasticsearch"],
            excluded_conditions=["elasticsearch down", "input source unavailable"],
            conflicting_symptoms=[]
        ),

        confidence_boosters=[
            ConfidenceBooster(
                condition="queue full",
                boost_amount=0.15
            ),
            ConfidenceBooster(
                condition="memory",
                boost_amount=0.15
            ),
            ConfidenceBooster(
                condition="parsing",
                boost_amount=0.10
            )
        ],

        workflow_steps=[
            WorkflowStep(
                step_number=1,
                title="Check Pipeline Status and Throughput",
                description=(
                    "Verify pipeline is running and check current event processing throughput. "
                    "Identify if pipeline is stuck, slow, or failing."
                ),
                tools_to_use=["service_health_check", "query_metric"],
                guidance=(
                    "Check:\n"
                    "- Is Logstash process running and healthy?\n"
                    "- Current events per second (should match expected rate)\n"
                    "- Pipeline queue depth (high queue indicates backpressure)\n"
                    "- Compare throughput to historical baseline\n"
                    "- Check if events are being processed at all (0 eps = stuck)"
                ),
                success_criteria=(
                    "Confirmed pipeline status and identified throughput issue"
                )
            ),
            WorkflowStep(
                step_number=2,
                title="Analyze Pipeline Worker Logs",
                description=(
                    "Review Logstash logs for errors, warnings, and pipeline worker status. "
                    "Identify specific errors causing pipeline issues."
                ),
                tools_to_use=["query_logs"],
                guidance=(
                    "Look for:\n"
                    "- Parsing errors: Grok failures, JSON parse errors\n"
                    "- Output errors: Elasticsearch connection issues, bulk write failures\n"
                    "- Memory errors: OutOfMemoryError, heap exhaustion\n"
                    "- Worker thread errors: Deadlocks, stuck workers\n"
                    "- Input plugin errors: Connection issues with source"
                ),
                success_criteria=(
                    "Identified specific errors in pipeline processing"
                )
            ),
            WorkflowStep(
                step_number=3,
                title="Check Resource Utilization",
                description=(
                    "Examine Logstash process resource usage including memory, CPU, and file descriptors. "
                    "Resource exhaustion often causes pipeline issues."
                ),
                tools_to_use=["query_metric", "query_logs"],
                guidance=(
                    "Investigate:\n"
                    "- JVM heap usage (should stay below 75%)\n"
                    "- GC frequency and duration (frequent GC indicates memory pressure)\n"
                    "- CPU usage per worker thread\n"
                    "- File descriptor usage (exhaustion causes connection failures)\n"
                    "- Disk I/O if using persistent queue"
                ),
                success_criteria=(
                    "Identified resource constraints affecting pipeline"
                )
            ),
            WorkflowStep(
                step_number=4,
                title="Verify Input and Output Health",
                description=(
                    "Check health of input sources (Kafka, Beats, etc.) and output "
                    "destinations (Elasticsearch, etc.) to ensure pipeline can read and write."
                ),
                tools_to_use=["service_health_check", "get_cluster_health", "query_logs"],
                guidance=(
                    "Verify:\n"
                    "- Input source is available and reachable\n"
                    "- Elasticsearch cluster is healthy (if using ES output)\n"
                    "- Network connectivity to inputs and outputs\n"
                    "- Authentication/authorization for accessing sources and destinations\n"
                    "- Backpressure from output (Elasticsearch bulk queue full)"
                ),
                success_criteria=(
                    "Confirmed input/output health or identified connectivity issues"
                )
            ),
            WorkflowStep(
                step_number=5,
                title="Review Pipeline Configuration",
                description=(
                    "Examine pipeline configuration for issues like inefficient filters, "
                    "blocking operations, or misconfigured plugins."
                ),
                tools_to_use=["query_logs"],
                guidance=(
                    "Check for:\n"
                    "- Complex Grok patterns (can be slow)\n"
                    "- Ruby filter with heavy operations\n"
                    "- External lookups (DNS, database) that might be slow\n"
                    "- Incorrect worker count (workers vs pipeline.workers)\n"
                    "- Queue size configuration (too small causes backpressure)\n"
                    "- Batch size for outputs (too small = inefficient)"
                ),
                success_criteria=(
                    "Identified configuration issues impacting pipeline performance"
                )
            )
        ],

        common_mistakes=[
            CommonMistake(
                mistake="Increasing worker count without checking resource limits",
                why_its_wrong=(
                    "If already constrained by CPU or memory, adding workers makes it worse. "
                    "Need to identify bottleneck first"
                ),
                correct_approach=(
                    "Check resource utilization first, then adjust workers if resources available"
                )
            ),
            CommonMistake(
                mistake="Ignoring GC logs and heap dumps",
                why_its_wrong=(
                    "Memory issues are common in Logstash. GC logs show if memory is the problem"
                ),
                correct_approach=(
                    "Always check JVM heap usage and GC activity for Java-based services"
                )
            ),
            CommonMistake(
                mistake="Not checking Elasticsearch cluster health when output fails",
                why_its_wrong=(
                    "If Elasticsearch is degraded, Logstash output will slow down or fail, "
                    "but root cause is downstream"
                ),
                correct_approach=(
                    "Always verify health of output destinations, not just Logstash itself"
                )
            )
        ],

        related_sops=["elasticsearch-perf-001", "kafka-broker-issues-001"],
        escalation_criteria=(
            "Escalate if: persistent memory leaks, need pipeline redesign, "
            "or data loss occurring"
        ),

        tags=["logstash", "pipeline", "ingestion", "logging"],
        estimated_duration_minutes=20
    )


def get_all_sample_sops() -> list[SOP]:
    """Get all sample SOPs."""
    return [
        get_msk_consumer_lag_sop(),
        get_elasticsearch_performance_sop(),
        get_high_latency_triage_sop(),
        get_logstash_pipeline_sop()
    ]
