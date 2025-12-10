"""
Simple SOP (Standard Operating Procedure) system.

SOPs guide the agent on which tools to use in which order,
instead of letting the agent guess.
"""

import json
from typing import List, Dict, Any, Optional


class SOP:
    """
    A Standard Operating Procedure that guides investigation workflow.

    Each SOP defines:
    - When to use it (triggers/scenarios)
    - Step-by-step workflow
    - Which tools to use at each step
    - What to look for in results
    """

    def __init__(self, data: Dict[str, Any]):
        self.id = data["id"]
        self.name = data["name"]
        self.description = data["description"]
        self.triggers = data.get("triggers", [])
        self.steps = data["steps"]
        self.do_not = data.get("do_not", [])

    def matches(self, user_query: str) -> bool:
        """
        Check if this SOP matches the user query.
        Simple keyword-based matching for now.
        """
        query_lower = user_query.lower()

        # Check if any trigger phrase is in the query
        for trigger in self.triggers:
            if trigger.lower() in query_lower:
                return True

        return False

    def get_step(self, step_number: int) -> Optional[Dict[str, Any]]:
        """Get a specific step by number."""
        for step in self.steps:
            if step["step"] == step_number:
                return step
        return None

    def __repr__(self):
        return f"SOP(id={self.id}, name={self.name}, steps={len(self.steps)})"


class SOPManager:
    """Manages SOPs - loading, searching, matching."""

    def __init__(self, sop_file: str = "sops.json"):
        self.sop_file = sop_file
        self.sops: List[SOP] = []
        self.load_sops()

    def load_sops(self):
        """Load SOPs from JSON file."""
        try:
            with open(self.sop_file, 'r') as f:
                data = json.load(f)
                self.sops = [SOP(sop_data) for sop_data in data.get("sops", [])]
            print(f"✓ Loaded {len(self.sops)} SOPs")
        except FileNotFoundError:
            print(f"⚠ SOP file not found: {self.sop_file}")
            self.sops = []
        except Exception as e:
            print(f"✗ Error loading SOPs: {e}")
            self.sops = []

    def find_sop(self, user_query: str) -> Optional[SOP]:
        """
        Find the best matching SOP for a user query.
        Returns the first match for simplicity.
        """
        for sop in self.sops:
            if sop.matches(user_query):
                return sop
        return None

    def list_sops(self):
        """List all available SOPs."""
        print("\nAvailable SOPs:")
        for i, sop in enumerate(self.sops, 1):
            print(f"{i}. {sop.name}")
            print(f"   Triggers: {', '.join(sop.triggers)}")
            print(f"   Steps: {len(sop.steps)}")
