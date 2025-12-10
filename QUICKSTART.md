# Quick Start Guide

## Installation

1. Install dependencies:
```bash
pip install pydantic
```

2. Test the installation:
```bash
python3 test_basic.py
```

Expected output: "✓ All tests passed! System is working correctly."

## Run the Demo

```bash
python3 demo.py
```

This will show:
- SOP matching for different queries
- Workflow steps for each matched SOP
- Repository statistics

## File Overview

| File | Purpose |
|------|---------|
| `sop_models.py` | Pydantic models for SOPs and contexts |
| `context_gatherer.py` | Fast context collection (<30s) |
| `sop_matcher.py` | Weighted SOP matching algorithm |
| `sop_repository.py` | JSON-based storage with caching |
| `mock_tools.py` | Mock observability tools |
| `sample_sops.py` | 4 pre-built SOPs |
| `strandsai_integration.py` | Agent setup and tools |
| `examples.py` | Detailed test scenarios |
| `demo.py` | Quick demonstration |
| `test_basic.py` | Validation tests |

## Sample SOPs Included

1. **MSK/Kafka Consumer Lag Investigation** (`msk-consumer-lag-001`)
   - Triggers: "consumer lag", "kafka lag", "slow consumption"
   - 5-step workflow for diagnosing consumer lag issues

2. **Elasticsearch Query Performance** (`elasticsearch-perf-001`)
   - Triggers: "elasticsearch slow", "query latency", "search performance"
   - 5-step workflow for slow query investigation

3. **High Latency Triage** (`high-latency-triage-001`)
   - Triggers: "high latency", "slow response", "timeout"
   - Disambiguation SOP that routes to specific SOPs

4. **Logstash Pipeline Issues** (`logstash-pipeline-001`)
   - Triggers: "logstash", "pipeline", "log ingestion"
   - 5-step workflow for pipeline troubleshooting

## Example Usage

### Basic Investigation

```python
from strandsai_integration import create_aiops_agent
from sop_repository import SOPRepository, initialize_sample_repository
from sample_sops import get_all_sample_sops

# Setup
repo = SOPRepository()
initialize_sample_repository(repo, get_all_sample_sops())

# Create agent
from strandsai_integration import AIOpsAgent
agent = AIOpsAgent(repository=repo)

# Get SOP for a query
result = agent.sop_tool.get_relevant_sop(
    "High consumer lag in payment-consumer service"
)

# Print recommendation
if result["status"] == "success":
    sop = result["sop"]
    print(f"Use SOP: {sop['name']}")
    print(f"Confidence: {result['confidence']:.1%}")
    print(f"Steps: {len(sop['workflow_steps'])}")
```

### Access Individual Tools

```python
# Get all available tools
tools = agent.get_tools()

# Use specific tools
health = tools["service_health_check"]("payment-service")
metrics = tools["query_msk_metrics"]("my-cluster", "my-consumer-group")
logs = tools["query_logs"]("payment-service", time_range_minutes=5)
```

### Context Gathering

```python
from context_gatherer import quick_context

# Gather context (fast, <30s)
context = quick_context("High latency in search service")

print(f"Services: {context.mentioned_services}")
print(f"Affected: {context.affected_services}")
print(f"Metrics: {context.available_metrics}")
print(f"Log patterns: {context.recent_log_patterns}")
print(f"Duration: {context.gathering_duration_seconds}s")
```

### Create Custom SOP

```python
from sop_models import SOP, WorkflowStep, ApplicabilityCriteria

my_sop = SOP(
    sop_id="custom-001",
    name="My Custom Investigation",
    description="Custom investigation procedure",
    trigger_keywords=["custom", "issue"],
    applicability=ApplicabilityCriteria(
        service_filters=["my-service"],
        metric_patterns=["my_metric"],
        log_patterns=["MyError"]
    ),
    workflow_steps=[
        WorkflowStep(
            step_number=1,
            title="Check Metrics",
            description="Gather current metrics",
            tools_to_use=["query_metric"],
            guidance="Look for anomalies",
            success_criteria="Found relevant metrics"
        )
    ],
    tags=["custom"]
)

# Add to repository
repo.create(my_sop)
```

## Running Test Scenarios

Run specific scenarios:

```bash
python3 examples.py 1  # Clear single match
python3 examples.py 2  # Disambiguation needed
python3 examples.py 3  # Context-driven matching
python3 examples.py 4  # No match handling
python3 examples.py 5  # End-to-end example
```

## Configuration

### Adjust Matching Weights

```python
from sop_matcher import SOPMatcher, MatchWeights

weights = MatchWeights(
    service_name=0.40,      # Prioritize service matching
    metric_pattern=0.25,
    log_pattern=0.15,
    confidence_booster=0.10,
    keyword_baseline=0.10
)

matcher = SOPMatcher(weights=weights)
```

### Configure Context Gathering

```python
from context_gatherer import ContextGatherer

gatherer = ContextGatherer(
    max_workers=3,          # Fewer concurrent tasks
    timeout_seconds=15.0    # Faster timeout
)
```

## Integration with StrandsAI

```python
# Get system prompt
system_prompt = agent.get_system_prompt()

# Get tools with schemas
from strandsai_integration import TOOL_SCHEMAS

# Configure StrandsAI agent with:
# - System prompt: system_prompt
# - Tools: agent.get_tools()
# - Tool schemas: TOOL_SCHEMAS
```

## Architecture Flow

```
User Query
    ↓
Context Gathering (parallel)
  • Extract services
  • Check health
  • Query metrics
  • Scan logs
  • Check alerts
    ↓
SOP Matching (weighted)
  • Keyword: 20%
  • Service: 30%
  • Metrics: 25%
  • Logs: 15%
  • Boosters: 10%
    ↓
SOP Selection
  • Single match → Return SOP
  • Close matches → Disambiguate
  • Multiple → Return top + alternatives
  • No match → General guidance
    ↓
Agent Follows Workflow
  • Execute step 1 tools
  • Interpret with guidance
  • Check success criteria
  • Continue to next step
  • Repeat until complete
```

## Key Features

✓ **Fast Context Gathering**: <30 seconds
✓ **Weighted Matching**: Configurable scoring
✓ **JSON Storage**: Simple file-based persistence
✓ **Caching**: Automatic performance optimization
✓ **Mock Tools**: Ready for testing
✓ **Extensible**: Easy to add new SOPs and tools
✓ **StrandsAI Ready**: Pre-configured integration

## Next Steps

1. ✅ Run `python3 test_basic.py` - Verify installation
2. ✅ Run `python3 demo.py` - See it in action
3. 📖 Read `README.md` - Full documentation
4. 🔧 Customize SOPs in `sample_sops.py`
5. 🚀 Integrate with your StrandsAI agent

## Troubleshooting

**SOP not matching?**
- Check trigger keywords
- Verify applicability criteria
- Lower min_confidence_threshold
- Add confidence boosters

**Context gathering slow?**
- Reduce timeout_seconds
- Decrease max_workers
- Optimize tool implementations

**Import errors?**
- Install pydantic: `pip install pydantic`
- Verify Python 3.7+

## Support

See full documentation in `README.md` for:
- Detailed API reference
- Advanced customization
- Best practices
- Performance tuning
- Integration examples
