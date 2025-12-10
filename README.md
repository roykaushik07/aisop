# AIOps Agent with SOP Guidance

## The Problem

You have an AIOps agent with ~10 Elasticsearch query tools. When users ask questions, the agent tries to **guess** which tools to use. This causes:

- ❌ Agent fails to use the right tools
- ❌ Agent uses unnecessary tools
- ❌ Inconsistent investigation approach
- ❌ Keywords alone don't help (e.g., "logstash" appears in many contexts)

## The Solution

**SOPs (Standard Operating Procedures)** guide the agent step-by-step:

✅ Tell the agent exactly which tools to use
✅ In what order to use them
✅ What to look for in results
✅ When to proceed to next steps

**No more guessing - just follow the SOP.**

## How It Works

```
User: "Logstash pipeline is slow"
    ↓
Agent finds matching SOP: "Logstash Pipeline Degradation"
    ↓
SOP Step 1: Check throughput
  → Use tool: search_logstash_throughput
    ↓
SOP Step 2: Search for errors
  → Use tool: search_logstash_errors
    ↓
SOP Step 3: Check resources
  → Use tools: search_high_memory_services, search_high_cpu_services
    ↓
SOP Step 4: Check recent changes
  → Use tool: search_recent_deployments
    ↓
Done - systematic investigation every time
```

## Files

- **`sop.py`** - SOP loader and matcher
- **`agent.py`** - Agent that follows SOPs
- **`tools.py`** - 10 Elasticsearch query tools (mock)
- **`sops.json`** - SOP definitions (5 examples)
- **`example.py`** - Demo script

## Quick Start

```bash
# Run example
python3 example.py

# Or use interactive mode
python3 agent.py
```

## Example SOPs

The system includes 5 SOPs:

1. **Logstash Pipeline Degradation** - When throughput drops
2. **Kafka Consumer Lag** - When lag is high
3. **Elasticsearch Slow Queries** - When queries timeout
4. **Service Error Spike** - When errors increase
5. **High Resource Usage** - When CPU/memory is high

## SOP Structure

Each SOP uses **RFC 2119-style requirement levels**:

- **MUST** 🔴 - Required, cannot be skipped
- **SHOULD** 🟡 - Recommended, skip only with good reason
- **MAY** 🟢 - Optional, context-dependent
- **MUST NOT** - Actions that must be avoided
- **SHOULD NOT** - Actions generally to avoid

```json
{
  "id": "logstash-pipeline-degraded",
  "name": "Logstash Pipeline Degradation Investigation",
  "triggers": ["logstash slow", "logstash pipeline"],
  "steps": [
    {
      "step": 1,
      "requirement": "MUST",
      "action": "Check current throughput",
      "tools": ["search_logstash_throughput"],
      "check_for": "Current vs average throughput",
      "if_found": "If low, proceed to check errors"
    },
    {
      "step": 2,
      "requirement": "SHOULD",
      "action": "Check resource usage",
      "tools": ["search_high_memory_services"],
      "check_for": "Memory/CPU on Logstash nodes"
    }
  ],
  "do_not": [
    {
      "requirement": "MUST NOT",
      "action": "Restart Logstash without checking errors first",
      "reason": "May lose diagnostic information"
    },
    {
      "requirement": "SHOULD NOT",
      "action": "Increase heap without confirming memory issue",
      "reason": "May waste resources if problem is elsewhere"
    }
  ]
}
```

## Creating New SOPs

1. Open `sops.json`
2. Add a new SOP with:
   - Clear triggers (phrases that match this scenario)
   - Step-by-step workflow
   - Specific tools for each step
   - What to check in results

3. The agent will automatically use it

## Key Benefits

- 🎯 **Consistent** - Same investigation every time
- 🚀 **Fast** - No trial and error
- 📝 **Documented** - SOP is the documentation
- 🔧 **Easy to update** - Just edit JSON
- 🤖 **No AI guessing** - Clear instructions
- ⚠️ **Prevents mistakes** - "Do not" guidance avoids common errors
- 📊 **Prioritized** - MUST/SHOULD/MAY levels show what's critical

## Integration with Your Agent

Replace the mock tools in `tools.py` with your actual Elasticsearch queries:

```python
def search_logstash_errors(time_range_minutes=30):
    """Your actual ES query here."""
    from elasticsearch import Elasticsearch
    es = Elasticsearch(['localhost:9200'])

    result = es.search(
        index="logstash-*",
        body={
            "query": {
                "bool": {
                    "must": [
                        {"match": {"level": "ERROR"}},
                        {"range": {"@timestamp": {"gte": f"now-{time_range_minutes}m"}}}
                    ]
                }
            }
        }
    )

    return result
```

Then your agent will use real data!

## StrandsAI Integration

To use with StrandsAI:

```python
from agent import AIOpsAgent

agent = AIOpsAgent()

# When user asks a question
result = agent.investigate(user_query)

# Agent follows SOP automatically
# Returns structured results from each step
```

The agent can be wrapped as a StrandsAI tool or used directly in your conversation flow.

## Why This Works

**Without SOPs:**
- Agent sees "logstash" → tries random tools
- Might miss critical checks
- Different results each time

**With SOPs:**
- Agent sees "logstash slow" → loads SOP
- Follows exact steps
- Consistent, complete investigation
- No guessing

---

**Simple. Focused. Solves your problem.**
