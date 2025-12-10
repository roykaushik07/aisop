"""
AIOps Agent that uses SOPs to guide tool usage.

Instead of guessing which tools to use, the agent follows
SOP workflows step-by-step.
"""

from typing import Dict, Any, List
from sop import SOPManager
from tools import TOOLS


class AIOpsAgent:
    """
    Agent that follows SOPs to investigate issues.

    The key difference: Instead of the agent deciding which tools to use,
    the SOP tells it exactly which tools to use in which order.
    """

    def __init__(self, sop_file: str = "sops.json"):
        self.sop_manager = SOPManager(sop_file)
        self.tools = TOOLS
        self.conversation_history = []

    def investigate(self, user_query: str) -> Dict[str, Any]:
        """
        Investigate an issue using SOP guidance.

        Flow:
        1. Find matching SOP
        2. Follow SOP steps
        3. Execute tools as specified in each step
        4. Return findings
        """
        print(f"\n{'='*70}")
        print(f"User Query: {user_query}")
        print(f"{'='*70}\n")

        # Step 1: Find matching SOP
        sop = self.sop_manager.find_sop(user_query)

        if not sop:
            return {
                "status": "no_sop_found",
                "message": "No matching SOP found. Agent would need to decide tools on its own.",
                "suggestion": "Create an SOP for this scenario to guide future investigations."
            }

        print(f"✓ Matched SOP: {sop.name}")
        print(f"  Description: {sop.description}")
        print(f"  Steps: {len(sop.steps)}\n")

        # Step 2: Execute SOP workflow
        results = self._execute_sop_workflow(sop, user_query)

        return {
            "status": "success",
            "sop_used": sop.name,
            "steps_executed": len(results["steps"]),
            "results": results
        }

    def _execute_sop_workflow(self, sop, user_query: str) -> Dict[str, Any]:
        """
        Execute the SOP workflow step by step.

        Each step specifies:
        - Which tools to use
        - What to look for
        - Conditions for next steps
        """
        workflow_results = {
            "sop": sop.name,
            "steps": []
        }

        for step_data in sop.steps:
            print(f"Step {step_data['step']}: {step_data['action']}")
            print(f"  Tools: {', '.join(step_data['tools'])}")

            # Execute tools for this step
            step_results = []
            for tool_name in step_data["tools"]:
                if tool_name in self.tools:
                    print(f"  → Executing {tool_name}...")

                    # Execute tool
                    tool_func = self.tools[tool_name]
                    try:
                        # Handle tools with different signatures
                        if "service_errors" in tool_name:
                            # Extract service name from query
                            result = tool_func(self._extract_service(user_query))
                        else:
                            result = tool_func()

                        step_results.append(result)
                        print(f"    ✓ {tool_name} completed")
                    except Exception as e:
                        print(f"    ✗ Error executing {tool_name}: {e}")
                        step_results.append({"error": str(e)})
                else:
                    print(f"  ⚠ Tool not found: {tool_name}")

            # Check what was found
            if step_data.get("check_for"):
                print(f"  Looking for: {step_data['check_for']}")

            # Check condition for next step
            if step_data.get("if_found"):
                print(f"  Next: {step_data['if_found']}")

            workflow_results["steps"].append({
                "step": step_data["step"],
                "action": step_data["action"],
                "tools_used": step_data["tools"],
                "results": step_results
            })

            print()

        return workflow_results

    def _extract_service(self, query: str) -> str:
        """
        Extract service name from query.
        Simple keyword extraction for demo.
        """
        common_services = ["payment", "order", "logstash", "elasticsearch", "kafka"]
        query_lower = query.lower()

        for service in common_services:
            if service in query_lower:
                return service

        return "unknown"

    def chat(self):
        """
        Simple chat interface.
        """
        print("\n" + "="*70)
        print(" AIOps Agent with SOP Guidance")
        print("="*70)
        print("\nType 'list' to see available SOPs")
        print("Type 'quit' to exit\n")

        while True:
            user_input = input("You: ").strip()

            if user_input.lower() == 'quit':
                print("Goodbye!")
                break

            if user_input.lower() == 'list':
                self.sop_manager.list_sops()
                continue

            if not user_input:
                continue

            # Investigate using SOPs
            result = self.investigate(user_input)

            if result["status"] == "no_sop_found":
                print(f"\n⚠ {result['message']}")
                print(f"💡 {result['suggestion']}\n")
            else:
                print(f"\n✓ Investigation complete using SOP: {result['sop_used']}")
                print(f"  Executed {result['steps_executed']} steps\n")


if __name__ == "__main__":
    agent = AIOpsAgent()
    agent.chat()
