# AIOps Investigation System with Standard Operating Procedures

A Python-based AIOps chatbot system that combines AI agents with Standard Operating Procedures (SOPs) for intelligent infrastructure troubleshooting.

## Overview

This system provides:

- **SOP Management**: Define, store, and retrieve Standard Operating Procedures for common issues
- **Context-Aware Matching**: Intelligent SOP selection based on services, metrics, logs, and alerts
- **Fast Context Gathering**: Quick diagnostic information collection (<30 seconds)
- **StrandsAI Integration**: Ready-to-use agent tools and prompts
- **Mock Tools**: Realistic observability tool implementations for testing

## Architecture

```
User Query
    ↓
┌─────────────────────────────────────┐
│  Context Gatherer (Fast)            │
│  • Extract services from query      │
│  • Check service health             │
│  • Gather metrics                   │
│  • Scan logs                        │
│  • Check alerts                     │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  SOP Matcher (Weighted Scoring)     │
│  • Keyword match (20%)              │
│  • Service match (30%)              │
│  • Metric patterns (25%)            │
│  • Log patterns (15%)               │
│  • Confidence boosters (10%)        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  SOP Selection                      │
│  • Single clear match               │
│  • Disambiguation needed            │
│  • Multiple options                 │
│  • No match (use judgment)          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Agent Follows SOP Workflow         │
│  • Step-by-step investigation       │
│  • Use recommended tools            │
│  • Follow guidance                  │
│  • Check success criteria           │
└─────────────────────────────────────┘
```

## Project Structure

```
aisop/
├── sop_models.py              # Pydantic models for SOPs
├── context_gatherer.py        # Fast context gathering
├── sop_matcher.py             # Weighted matching logic
├── sop_repository.py          # JSON-based storage
├── mock_tools.py              # Mock observability tools
├── sample_sops.py             # 4 sample SOPs
├── strandsai_integration.py   # StrandsAI agent setup
├── examples.py                # Test scenarios
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── data/
    └── sample_sops.json       # SOP storage (auto-created)
```

## Installation

1. **Clone or download this project**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Verify installation**:
```bash
python -c "from sop_models import SOP; print('✓ Installation successful')"
```

## Quick Start

### Running Examples

Run all test scenarios:
```bash
python examples.py
```

Run specific scenarios:
```bash
python examples.py 1  # Clear single match
python examples.py 2  # Disambiguation
python examples.py 3  # Context-driven
python examples.py 4  # No match
python examples.py 5  # End-to-end
python examples.py repo  # Repository operations
```

### Basic Usage

```python
from strandsai_integration import create_aiops_agent

# Create agent
agent = create_aiops_agent()

# Investigate an issue
result = agent.investigate("High consumer lag in payment service")

# Print SOP recommendation
print(result["sop_recommendation"])
```

## Core Components

### 1. SOP Models (`sop_models.py`)

Pydantic models defining SOP structure:

```python
from sop_models import SOP, WorkflowStep, ApplicabilityCriteria

sop = SOP(
    sop_id="my-sop-001",
    name="My Investigation SOP",
    trigger_keywords=["error", "failure"],
    applicability=ApplicabilityCriteria(
        service_filters=["payment"],
        metric_patterns=["error_rate"],
        log_patterns=["Exception"]
    ),
    workflow_steps=[
        WorkflowStep(
            step_number=1,
            title="Check Service Health",
            tools_to_use=["service_health_check"],
            guidance="Look for degraded status...",
            success_criteria="Identified service status"
        )
    ]
)
```

### 2. Context Gathering (`context_gatherer.py`)

Fast context collection (<30 seconds):

```python
from context_gatherer import quick_context

# Gather context from user query
context = quick_context("High latency in search service")

print(f"Services: {context.mentioned_services}")
print(f"Metrics: {context.available_metrics}")
print(f"Logs: {context.recent_log_patterns}")
print(f"Duration: {context.gathering_duration_seconds}s")
```

### 3. SOP Matching (`sop_matcher.py`)

Weighted scoring algorithm:

```python
from sop_matcher import SOPMatcher, MatchWeights

# Configure weights
weights = MatchWeights(
    service_name=0.30,      # 30%
    metric_pattern=0.25,    # 25%
    log_pattern=0.15,       # 15%
    confidence_booster=0.10, # 10%
    keyword_baseline=0.20   # 20%
)

matcher = SOPMatcher(weights=weights)

# Find matching SOPs
matches = matcher.find_matching_sops(context, available_sops)

# Select best match or disambiguate
best_match, disambiguation = matcher.select_best_sop(matches)
```

### 4. SOP Repository (`sop_repository.py`)

JSON-based storage with caching:

```python
from sop_repository import SOPRepository

# Create repository
repo = SOPRepository(storage_path="./data/sops.json")

# CRUD operations
repo.create(sop)
sop = repo.get_by_id("my-sop-001")
repo.update(sop)
repo.delete("my-sop-001")

# Search
matches = repo.search_by_keywords(["kafka", "lag"])
matches = repo.search_by_tags(["messaging"])

# Import/Export
repo.export_to_file("backup.json")
repo.import_from_file("backup.json", overwrite_existing=True)

# Statistics
stats = repo.get_stats()
```

### 5. Mock Tools (`mock_tools.py`)

Realistic observability tools for testing:

```python
from mock_tools import (
    service_health_check,
    query_msk_metrics,
    query_logs,
    get_cluster_health
)

# Check service health
health = service_health_check("payment-consumer")

# Get Kafka metrics
metrics = query_msk_metrics("payment-cluster", "payment-consumer-group")

# Query logs
logs = query_logs("payment-service", time_range_minutes=5)

# Check cluster health
cluster = get_cluster_health("elasticsearch", "prod-es-cluster")
```

### 6. StrandsAI Integration (`strandsai_integration.py`)

Agent setup with SOP tool:

```python
from strandsai_integration import AIOpsAgent

# Create agent
agent = AIOpsAgent(repository=repo)

# Get system prompt
system_prompt = agent.get_system_prompt()

# Get available tools
tools = agent.get_tools()

# Tools include:
# - get_relevant_sop: Retrieve matching SOP
# - query_msk_metrics: Kafka/MSK metrics
# - get_consumer_group_details: Consumer group info
# - query_logs: Application logs
# - service_health_check: Service health
# ... and more
```

## Sample SOPs

The system includes 4 sample SOPs covering common scenarios:

### 1. MSK/Kafka Consumer Lag Investigation (`msk-consumer-lag-001`)

**Triggers**: consumer lag, kafka lag, slow consumption

**Workflow**:
1. Verify consumer lag metrics
2. Check consumer group health
3. Analyze consumer application logs
4. Check Kafka broker health
5. Assess consumer processing performance

**Key Tools**: `query_msk_metrics`, `get_consumer_group_details`, `check_broker_status`

### 2. Elasticsearch Query Performance (`elasticsearch-perf-001`)

**Triggers**: elasticsearch slow, query latency, search performance

**Workflow**:
1. Verify query latency metrics
2. Check cluster health and resources
3. Analyze slow query patterns
4. Check index health and shard distribution
5. Review recent changes and GC activity

**Key Tools**: `query_elasticsearch_slow_log`, `get_cluster_health`, `query_elasticsearch`

### 3. High Latency Triage (`high-latency-triage-001`)

**Triggers**: high latency, slow response, timeout

**Purpose**: Disambiguation SOP that classifies latency type and routes to specific SOPs

**Workflow**:
1. Identify affected services and components
2. Classify latency type
3. Check for recent changes
4. Assess immediate mitigation options

**Routes to**: Other specialized SOPs based on classification

### 4. Logstash Pipeline Issues (`logstash-pipeline-001`)

**Triggers**: logstash, pipeline, log ingestion

**Workflow**:
1. Check pipeline status and throughput
2. Analyze pipeline worker logs
3. Check resource utilization
4. Verify input and output health
5. Review pipeline configuration

**Key Tools**: `query_logs`, `query_metric`, `service_health_check`

## Test Scenarios

### Scenario 1: Clear Single Match

```python
query = "High consumer lag in payment service"
# → Matches MSK Consumer Lag SOP with high confidence
```

**Expected Output**:
- Context: payment service identified, consumer_lag metric found
- Confidence: ~85%
- Selected SOP: MSK/Kafka Consumer Lag Investigation
- Workflow: 5 steps with specific tools

### Scenario 2: Disambiguation

```python
query = "We're seeing high latency"
# → Multiple SOPs match, requires disambiguation
```

**Expected Output**:
- Status: disambiguation_needed
- Options: High Latency Triage, Elasticsearch Performance
- Question: "Which scenario best describes your situation?"

### Scenario 3: Context-Driven Selection

```python
query = "Elasticsearch query performance issue in search service"
# → Context (service name + keywords) selects Elasticsearch SOP
```

**Expected Output**:
- Context: elasticsearch service, query_latency metrics, slow query logs
- Confidence: ~75%
- Selected SOP: Elasticsearch Query Performance Investigation

### Scenario 4: No Match

```python
query = "Strange behavior in custom-internal-tool service"
# → No SOP matches, provides general guidance
```

**Expected Output**:
- Status: no_match
- Guidance: General investigation pattern
- Tools: service_health_check, query_logs, query_metric

## Creating Custom SOPs

### Step 1: Define the SOP

```python
from sop_models import (
    SOP, WorkflowStep, ApplicabilityCriteria,
    ExclusionCriteria, ConfidenceBooster, CommonMistake
)

custom_sop = SOP(
    sop_id="custom-database-slow-001",
    name="Database Slow Query Investigation",
    description="Investigate slow database queries",
    trigger_keywords=["database slow", "query slow", "db performance"],

    applicability=ApplicabilityCriteria(
        service_filters=["postgres", "mysql", "database"],
        metric_patterns=["query_time", "connection_pool"],
        log_patterns=["slow query", "timeout"],
        symptom_keywords=["slow", "timeout"]
    ),

    exclusion=ExclusionCriteria(
        excluded_services=["elasticsearch", "mongodb"],
        excluded_conditions=["database down"],
        conflicting_symptoms=["connection refused"]
    ),

    confidence_boosters=[
        ConfidenceBooster(
            condition="connection pool",
            boost_amount=0.15
        )
    ],

    workflow_steps=[
        WorkflowStep(
            step_number=1,
            title="Check Query Performance Metrics",
            description="Gather current query performance metrics",
            tools_to_use=["query_metric", "query_logs"],
            guidance=(
                "Look for:\n"
                "- Query execution time > 1s\n"
                "- Connection pool exhaustion\n"
                "- Lock contention"
            ),
            success_criteria="Identified slow queries and their patterns"
        ),
        # ... more steps
    ],

    common_mistakes=[
        CommonMistake(
            mistake="Adding indexes without analyzing query plans",
            why_its_wrong="Wrong indexes can make performance worse",
            correct_approach="First get query plans, then add targeted indexes"
        )
    ],

    related_sops=["database-connection-001"],
    tags=["database", "performance"],
    estimated_duration_minutes=20
)
```

### Step 2: Add to Repository

```python
from sop_repository import SOPRepository

repo = SOPRepository()
repo.create(custom_sop)

# Verify
sop = repo.get_by_id("custom-database-slow-001")
print(f"Added: {sop.name}")
```

### Step 3: Test Matching

```python
from context_gatherer import quick_context
from sop_matcher import SOPMatcher

# Test query
context = quick_context("Database queries are slow in user service")

# Match SOPs
matcher = SOPMatcher()
matches = matcher.find_matching_sops(context, repo.get_all())

print(f"Found {len(matches)} matches")
for match in matches:
    print(f"  - {match.sop.name}: {match.confidence_score:.1%}")
```

## Customization

### Adjust Matching Weights

```python
from sop_matcher import SOPMatcher, MatchWeights

# Prioritize service matching over keywords
custom_weights = MatchWeights(
    service_name=0.40,      # Increased from 0.30
    metric_pattern=0.25,
    log_pattern=0.15,
    confidence_booster=0.10,
    keyword_baseline=0.10   # Decreased from 0.20
)

matcher = SOPMatcher(weights=custom_weights)
```

### Configure Context Gathering

```python
from context_gatherer import ContextGatherer

# Faster gathering with fewer workers
gatherer = ContextGatherer(
    max_workers=3,           # Default: 5
    timeout_seconds=15.0     # Default: 25.0
)

context = gatherer.gather_context("High CPU usage")
```

### Customize Tool Behavior

```python
# Override mock tools with real implementations
from mock_tools import service_health_check as mock_health

def real_service_health_check(service_name: str):
    # Call real monitoring API
    response = requests.get(f"https://monitoring/api/health/{service_name}")
    return response.json()

# Use in agent
tools["service_health_check"] = real_service_health_check
```

## Integration with StrandsAI

### Basic Integration

```python
from strandsai_integration import create_aiops_agent

# Create agent with SOP support
agent = create_aiops_agent(sop_storage_path="./data/sops.json")

# Get tools for StrandsAI
tools = agent.get_tools()

# Get system prompt
system_prompt = agent.get_system_prompt()

# In StrandsAI, configure agent with:
# - System prompt: system_prompt
# - Tools: tools
# - Model: claude-3-sonnet or similar
```

### Agent Workflow

1. User: "High consumer lag in payment service"
2. Agent calls: `get_relevant_sop("High consumer lag in payment service")`
3. System returns: MSK Consumer Lag SOP with workflow steps
4. Agent follows step 1: Call `query_msk_metrics` and `get_consumer_group_details`
5. Agent interprets results using guidance
6. Agent continues to step 2: Call `query_logs`
7. Agent continues through remaining steps
8. Agent provides summary with findings and recommendations

## Best Practices

### SOP Design

1. **Clear Trigger Keywords**: Use specific, searchable terms
2. **Realistic Applicability Criteria**: Match actual service names and metrics
3. **Step-by-Step Workflows**: Each step should have clear tools and guidance
4. **Actionable Guidance**: Tell the agent what to look for and why
5. **Common Mistakes**: Help agents avoid known pitfalls

### Context Gathering

1. **Keep It Fast**: Target <30 seconds for context gathering
2. **Parallel Execution**: Gather context concurrently
3. **Fail Gracefully**: Context gathering failures shouldn't block matching

### Matching Logic

1. **Tune Weights**: Adjust based on your environment
2. **Use Exclusions**: Prevent wrong SOP matches
3. **Leverage Boosters**: Reward strong indicators
4. **Test Thoroughly**: Verify matching with real queries

## Troubleshooting

### SOP Not Matching

**Problem**: Expected SOP doesn't match query

**Solutions**:
1. Check trigger keywords include query terms
2. Verify applicability criteria match context
3. Review exclusion criteria (might be blocking)
4. Lower `min_confidence_threshold` in matcher
5. Add confidence boosters for strong signals

### Context Gathering Slow

**Problem**: Context gathering takes >30 seconds

**Solutions**:
1. Reduce `timeout_seconds` in ContextGatherer
2. Decrease `max_workers` to reduce overhead
3. Optimize mock tools or real tool implementations
4. Skip expensive checks in context gathering

### Disambiguation Too Frequent

**Problem**: Too many queries need disambiguation

**Solutions**:
1. Increase `disambiguation_threshold` in matcher
2. Add more specific trigger keywords to SOPs
3. Add confidence boosters to differentiate SOPs
4. Create more specific SOPs for common scenarios

## Performance Considerations

- **Context Gathering**: ~10-25 seconds with 5 workers
- **SOP Matching**: <1 second for 10-20 SOPs
- **Repository Cache**: Reduces disk reads to every 5 minutes
- **Memory Usage**: ~10MB per 100 SOPs (cached)

## Future Enhancements

Potential improvements:

1. **Machine Learning**: Learn from past investigations to improve matching
2. **Feedback Loop**: Track SOP effectiveness and user satisfaction
3. **Dynamic Workflows**: Adjust steps based on intermediate findings
4. **Multi-Language**: Support SOPs in multiple languages
5. **Real-Time Updates**: Live SOP updates without restart
6. **SOP Analytics**: Track which SOPs are used most, success rates
7. **Integration Templates**: Pre-built integrations for common tools

## License

This is a sample/demo project. Adapt and use as needed for your infrastructure.

## Support

For issues or questions:
1. Check the examples in `examples.py`
2. Review the inline documentation in each module
3. Examine the sample SOPs in `sample_sops.py`

## Contributing

To add new SOPs:
1. Create SOP using models in `sop_models.py`
2. Add to `sample_sops.py` or create new file
3. Test with various queries
4. Update documentation

---

**Built for AIOps teams who want structured, repeatable investigation workflows powered by AI.**
