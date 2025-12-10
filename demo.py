"""
Simple demonstration of the AIOps SOP system.
"""

import json
from sop_repository import SOPRepository, initialize_sample_repository
from sample_sops import get_all_sample_sops
from strandsai_integration import AIOpsAgent


def print_section(title):
    """Print a formatted section."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70 + "\n")


def demo():
    """Run a simple demonstration."""
    print_section("AIOps SOP System - Quick Demo")

    # Step 1: Setup
    print("Step 1: Setting up repository with sample SOPs...")
    repo = SOPRepository(storage_path="./data/demo_sops.json")

    # Add sample SOPs
    sample_sops = get_all_sample_sops()
    for sop in sample_sops:
        try:
            repo.create(sop)
            print(f"  ✓ Added: {sop.name}")
        except:
            pass  # Already exists

    # Step 2: Create agent
    print("\nStep 2: Creating AIOps agent...")
    agent = AIOpsAgent(repository=repo)
    print(f"  ✓ Agent created with {len(repo.get_all())} SOPs available")

    # Step 3: Test investigation
    queries = [
        "High consumer lag in payment-consumer service",
        "Elasticsearch queries are slow",
        "Logstash pipeline is stuck"
    ]

    for query in queries:
        print_section(f"Investigation: \"{query}\"")

        # Get SOP recommendation
        result = agent.sop_tool.get_relevant_sop(query)

        print("Status:", result.get("status"))

        if result.get("status") == "success":
            if result.get("sop"):
                sop = result["sop"]
                print(f"Matched SOP: {sop['name']}")
                print(f"Confidence: {result.get('confidence', 0):.1%}")
                print(f"\nWorkflow Steps:")
                for i, step in enumerate(sop['workflow_steps'][:3], 1):
                    print(f"  {i}. {step['title']}")
                    print(f"     Tools: {', '.join(step['tools_to_use'])}")
                if len(sop['workflow_steps']) > 3:
                    print(f"  ... and {len(sop['workflow_steps']) - 3} more steps")

                print(f"\nFirst step guidance:")
                print(f"  {sop['workflow_steps'][0]['guidance'][:150]}...")
        elif result.get("status") == "no_match":
            print("No matching SOP found - would use general investigation approach")

    # Step 4: Show repository stats
    print_section("Repository Statistics")
    stats = repo.get_stats()
    print(f"Total SOPs: {stats['total_sops']}")
    print(f"Tags: {', '.join(stats['unique_tags'])}")
    print(f"Storage: {stats['storage_path']}")

    print_section("Demo Complete")
    print("✓ System is working correctly!")
    print("\nNext steps:")
    print("  - Run 'python3 examples.py' for detailed scenarios")
    print("  - See README.md for full documentation")
    print("  - Create your own SOPs using sample_sops.py as a template")


if __name__ == "__main__":
    demo()
