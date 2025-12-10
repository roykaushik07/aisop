"""
Test scenarios and examples for the AIOps SOP system.

This module demonstrates different matching scenarios:
1. Clear single SOP match
2. Ambiguous query requiring disambiguation
3. Context-driven matching
4. No match scenario
"""

import json
import logging
from typing import Dict, Any

from sop_repository import SOPRepository, initialize_sample_repository
from context_gatherer import ContextGatherer
from sop_matcher import SOPMatcher
from strandsai_integration import create_aiops_agent
from sample_sops import get_all_sample_sops

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80 + "\n")


def print_json(data: Dict[str, Any], title: str = None):
    """Print JSON data in a formatted way."""
    if title:
        print(f"\n{title}:")
        print("-" * 60)
    print(json.dumps(data, indent=2, default=str))
    print()


def setup_repository() -> SOPRepository:
    """Set up repository with sample SOPs."""
    print_section("Setting Up Repository")

    # Create repository
    repo = SOPRepository(storage_path="./data/sample_sops.json")

    # Initialize with sample SOPs
    sample_sops = get_all_sample_sops()
    added = initialize_sample_repository(repo, sample_sops)

    print(f"✓ Initialized repository with {added} SOPs")

    # Print repository stats
    stats = repo.get_stats()
    print(f"✓ Repository location: {stats['storage_path']}")
    print(f"✓ Available SOPs: {', '.join(stats['sop_ids'])}")

    return repo


def scenario_1_clear_match():
    """
    Scenario 1: Clear Single SOP Match
    User query clearly matches MSK consumer lag SOP.
    """
    print_section("Scenario 1: Clear Single SOP Match")

    query = "High consumer lag in payment service"
    print(f"User Query: \"{query}\"\n")

    # Create agent
    agent = create_aiops_agent()

    # Investigate
    result = agent.investigate(query)

    # Print context gathered
    context_summary = result["sop_recommendation"]["context_summary"]
    print("Context Gathered:")
    print(f"  - Mentioned services: {context_summary.get('mentioned_services', [])}")
    print(f"  - Affected services: {context_summary.get('affected_services', [])}")
    print(f"  - Key metrics: {list(context_summary.get('key_metrics', {}).keys())}")
    print(f"  - Active alerts: {context_summary.get('active_alerts', [])}")

    # Print SOP match
    sop_rec = result["sop_recommendation"]
    print(f"\n✓ Match Status: {sop_rec['status']}")
    print(f"✓ Confidence: {sop_rec.get('confidence', 0):.1%}")

    if sop_rec.get("sop"):
        sop = sop_rec["sop"]
        print(f"✓ Selected SOP: {sop['name']}")
        print(f"✓ Description: {sop['description']}")
        print(f"✓ Estimated Duration: {sop['estimated_duration_minutes']} minutes")

        print(f"\nMatch Reasons:")
        for reason in sop_rec.get("match_reasons", []):
            print(f"  • {reason}")

        print(f"\nWorkflow Steps ({len(sop['workflow_steps'])} steps):")
        for step in sop["workflow_steps"]:
            print(f"\n  Step {step['step_number']}: {step['title']}")
            print(f"    Tools: {', '.join(step['tools_to_use'])}")
            print(f"    Guidance: {step['guidance'][:100]}...")

        print(f"\nCommon Mistakes to Avoid:")
        for mistake in sop["common_mistakes"]:
            print(f"  • {mistake['mistake']}")
            print(f"    → {mistake['correct_approach']}")

    return result


def scenario_2_ambiguous_query():
    """
    Scenario 2: Ambiguous Query Requiring Disambiguation
    Generic "high latency" could match multiple SOPs.
    """
    print_section("Scenario 2: Ambiguous Query - Disambiguation Needed")

    query = "We're seeing high latency"
    print(f"User Query: \"{query}\"\n")

    # Create agent
    agent = create_aiops_agent()

    # Investigate
    result = agent.investigate(query)

    # Print context
    sop_rec = result["sop_recommendation"]
    context_summary = sop_rec.get("context_summary", {})
    print("Context Gathered:")
    print(f"  - Mentioned services: {context_summary.get('mentioned_services', [])}")
    print(f"  - Affected services: {context_summary.get('affected_services', [])}")

    # Print match status
    print(f"\n✓ Match Status: {sop_rec['status']}")
    print(f"✓ Match Type: {sop_rec.get('match_type', 'unknown')}")

    if sop_rec.get("status") == "disambiguation_needed":
        print(f"\nDisambiguation Required:")
        print(f"  {sop_rec['question']}\n")

        print("Options:")
        for i, option in enumerate(sop_rec.get("options", []), 1):
            print(f"\n  {i}. {option['name']} (confidence: {option['confidence']:.1%})")
            print(f"     {option['description']}")
            print(f"     Reasons: {', '.join(option['match_reasons'])}")

        print(f"\n{sop_rec.get('instructions', '')}")

    elif sop_rec.get("match_type") == "multiple":
        # Show top match with alternatives
        print(f"\nTop Match: {sop_rec['top_match']['name']}")
        print(f"Confidence: {sop_rec['confidence']:.1%}")

        if sop_rec.get("alternative_sops"):
            print(f"\nAlternative SOPs:")
            for alt in sop_rec["alternative_sops"]:
                print(f"  • {alt['name']} ({alt['confidence']:.1%})")

    return result


def scenario_3_context_driven():
    """
    Scenario 3: Context-Driven Matching
    Multiple SOPs could match, but context selects the best one.
    """
    print_section("Scenario 3: Context-Driven Matching")

    query = "Elasticsearch query performance issue in search service"
    print(f"User Query: \"{query}\"\n")

    # Create agent
    agent = create_aiops_agent()

    # Investigate
    result = agent.investigate(query)

    # Print detailed context
    sop_rec = result["sop_recommendation"]
    context_summary = sop_rec.get("context_summary", {})

    print("Context Gathered:")
    print(f"  - Mentioned services: {context_summary.get('mentioned_services', [])}")
    print(f"  - Affected services: {context_summary.get('affected_services', [])}")
    print(f"  - Key metrics:")
    for metric, value in list(context_summary.get('key_metrics', {}).items())[:3]:
        print(f"      {metric}: {value}")
    print(f"  - Log patterns: {context_summary.get('log_patterns', [])}")

    # Print match decision
    print(f"\n✓ Match Status: {sop_rec['status']}")
    print(f"✓ Confidence: {sop_rec.get('confidence', 0):.1%}")

    if sop_rec.get("sop"):
        sop = sop_rec["sop"]
        print(f"✓ Selected SOP: {sop['name']}")

        print(f"\nWhy this SOP was selected:")
        for reason in sop_rec.get("match_reasons", []):
            print(f"  • {reason}")

        # Show how context influenced the match
        print(f"\nContext Highlights (what triggered this match):")
        if "key_metrics" in context_summary:
            print(f"  Metrics: {', '.join(context_summary['key_metrics'].keys())}")
        if "log_patterns" in context_summary:
            print(f"  Log patterns: {context_summary['log_patterns']}")

        print(f"\nFirst Step to Execute:")
        first_step = sop["workflow_steps"][0]
        print(f"  {first_step['step_number']}. {first_step['title']}")
        print(f"  Description: {first_step['description']}")
        print(f"  Tools to use: {', '.join(first_step['tools_to_use'])}")

    return result


def scenario_4_no_match():
    """
    Scenario 4: No Match - Agent Uses Judgment
    Query doesn't match any SOP, agent provides general guidance.
    """
    print_section("Scenario 4: No Match - Agent Uses Judgment")

    query = "Strange behavior in custom-internal-tool service"
    print(f"User Query: \"{query}\"\n")

    # Create agent
    agent = create_aiops_agent()

    # Investigate
    result = agent.investigate(query)

    # Print context
    sop_rec = result["sop_recommendation"]
    context_summary = sop_rec.get("context_summary", {})

    print("Context Gathered:")
    print(f"  - Mentioned services: {context_summary.get('mentioned_services', [])}")
    print(f"  - Affected services: {context_summary.get('affected_services', [])}")
    print(f"  - Key metrics: {list(context_summary.get('key_metrics', {}).keys())[:5]}")
    print(f"  - Log patterns: {context_summary.get('log_patterns', [])}")

    # Print no match guidance
    print(f"\n✓ Match Status: {sop_rec['status']}")
    print(f"✓ Match Type: {sop_rec.get('match_type', 'unknown')}")

    print(f"\nNo SOP matched this query. General investigation guidance provided:")
    print(f"{sop_rec.get('instructions', '')}")

    if sop_rec.get("available_tools"):
        print(f"\nRecommended tools for investigation:")
        for tool in sop_rec["available_tools"]:
            print(f"  • {tool}")

    return result


def scenario_5_end_to_end():
    """
    Scenario 5: End-to-End Example with Tool Execution
    Demonstrates full workflow with simulated tool execution.
    """
    print_section("Scenario 5: End-to-End Investigation Example")

    query = "Payment consumer has high lag and frequent rebalancing"
    print(f"User Query: \"{query}\"\n")

    # Create components
    agent = create_aiops_agent()
    tools = agent.get_tools()

    # Step 1: Get SOP
    print("Step 1: Retrieving relevant SOP...")
    sop_result = tools["get_relevant_sop"](query)

    if sop_result["status"] != "success":
        print("No SOP found, aborting example")
        return

    sop = sop_result["sop"]
    print(f"✓ Found SOP: {sop['name']}")
    print(f"✓ Confidence: {sop_result['confidence']:.1%}")

    # Step 2: Execute first workflow step
    first_step = sop["workflow_steps"][0]
    print(f"\n\nStep 2: Executing SOP Step {first_step['step_number']}: {first_step['title']}")
    print(f"Description: {first_step['description']}")
    print(f"Tools to use: {', '.join(first_step['tools_to_use'])}\n")

    # Execute tools for first step
    for tool_name in first_step["tools_to_use"]:
        if tool_name in tools:
            print(f"Calling {tool_name}...")

            if tool_name == "get_consumer_group_details":
                result = tools[tool_name]("payment-consumer-group")
            elif tool_name == "query_msk_metrics":
                result = tools[tool_name]("payment-cluster", "payment-consumer-group")
            else:
                continue

            print_json(result, f"Results from {tool_name}")

    # Show guidance
    print("\nGuidance for interpreting results:")
    print(first_step['guidance'])

    print("\nSuccess Criteria:")
    print(first_step['success_criteria'])

    # Step 3: Show second step
    if len(sop["workflow_steps"]) > 1:
        second_step = sop["workflow_steps"][1]
        print(f"\n\nNext Step: {second_step['step_number']}. {second_step['title']}")
        print(f"Description: {second_step['description']}")
        print(f"Tools to use: {', '.join(second_step['tools_to_use'])}")
        print("\n(In full implementation, agent would continue through all steps...)")

    return sop_result


def run_all_scenarios():
    """Run all test scenarios."""
    print_section("AIOps SOP System - Test Scenarios")

    # Setup
    repo = setup_repository()

    # Run scenarios
    scenario_1_clear_match()
    scenario_2_ambiguous_query()
    scenario_3_context_driven()
    scenario_4_no_match()
    scenario_5_end_to_end()

    print_section("All Scenarios Complete")
    print("Summary:")
    print("  ✓ Scenario 1: Clear single match demonstrated")
    print("  ✓ Scenario 2: Disambiguation demonstrated")
    print("  ✓ Scenario 3: Context-driven selection demonstrated")
    print("  ✓ Scenario 4: No match handling demonstrated")
    print("  ✓ Scenario 5: End-to-end workflow demonstrated")


def demo_repository_operations():
    """Demonstrate repository CRUD operations."""
    print_section("Repository Operations Demo")

    repo = SOPRepository(storage_path="./data/demo_sops.json")

    # Create
    from sample_sops import get_msk_consumer_lag_sop
    sop = get_msk_consumer_lag_sop()
    print(f"Creating SOP: {sop.sop_id}")
    success = repo.create(sop)
    print(f"✓ Created: {success}")

    # Read
    print(f"\nReading SOP: {sop.sop_id}")
    retrieved = repo.get_by_id(sop.sop_id)
    print(f"✓ Retrieved: {retrieved.name if retrieved else 'Not found'}")

    # Search
    print(f"\nSearching by keyword: 'kafka'")
    matches = repo.search_by_keywords(["kafka"])
    print(f"✓ Found {len(matches)} matches")

    # Update
    print(f"\nUpdating SOP version")
    sop.version = "1.1"
    success = repo.update(sop)
    print(f"✓ Updated: {success}")

    # Stats
    print(f"\nRepository Statistics:")
    stats = repo.get_stats()
    print_json(stats, "Stats")

    # Export
    print(f"Exporting to file...")
    repo.export_to_file("./data/export_demo.json")
    print(f"✓ Exported")

    # Cleanup
    print(f"\nDeleting SOP: {sop.sop_id}")
    success = repo.delete(sop.sop_id)
    print(f"✓ Deleted: {success}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        scenario = sys.argv[1]

        if scenario == "1":
            setup_repository()
            scenario_1_clear_match()
        elif scenario == "2":
            setup_repository()
            scenario_2_ambiguous_query()
        elif scenario == "3":
            setup_repository()
            scenario_3_context_driven()
        elif scenario == "4":
            setup_repository()
            scenario_4_no_match()
        elif scenario == "5":
            setup_repository()
            scenario_5_end_to_end()
        elif scenario == "repo":
            demo_repository_operations()
        else:
            print(f"Unknown scenario: {scenario}")
            print("Usage: python examples.py [1|2|3|4|5|repo]")
    else:
        # Run all scenarios
        run_all_scenarios()
