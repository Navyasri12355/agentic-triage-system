"""
Audit & Safety Agent
- Logs decisions
- Ensures policy compliance
"""

def log_decision(agent: str, decision: dict):
    """
    Log agent decision
    """
    # TODO: Save logs to DB
    print(f"[LOG] Agent={agent} | Decision={decision}")

def check_policy_constraints(decision: dict):
    """
    Placeholder policy checks
    """
    if decision.get("severity") == "Critical":
        return True  # allowed
    return True
