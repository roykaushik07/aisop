"""
Example showing how SOPs guide the agent to use the right tools.
"""

from agent import AIOpsAgent


def main():
    print("\n" + "="*70)
    print(" AIOps Agent with SOP Guidance - Example")
    print("="*70)
    print()
    print("This demonstrates how SOPs guide the agent to use the right tools")
    print("in the right order, instead of the agent guessing.\n")

    # Create agent
    agent = AIOpsAgent()

    # Example queries
    queries = [
        "Logstash pipeline is running slow",
        "We have high consumer lag in the payment service",
        "Elasticsearch queries are timing out",
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n{'#'*70}")
        print(f"# Example {i}")
        print(f"{'#'*70}\n")

        result = agent.investigate(query)

        if result["status"] == "success":
            print(f"✓ Investigation guided by SOP: {result['sop_used']}")
            print(f"✓ Executed {result['steps_executed']} steps systematically")
        else:
            print(f"⚠ {result['message']}")

        input("\nPress Enter for next example...")

    print("\n" + "="*70)
    print(" Example Complete")
    print("="*70)
    print()
    print("Key Points:")
    print("  • SOPs tell the agent exactly which tools to use")
    print("  • Tools are executed in a specific order")
    print("  • No guessing - clear workflow every time")
    print("  • Easy to add new SOPs for new scenarios")
    print()


if __name__ == "__main__":
    main()
