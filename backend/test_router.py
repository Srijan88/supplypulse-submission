import json

from agents.router_agent import RouterAgent


router = RouterAgent()

test_questions = [
    "Hi, what can you do?",
    "What are the schedule risks?",
    "What are the political risks for delayed shipments?",
    "Check tariff and customs risk.",
    "Any port or logistics risk?",
    "Give me complete risk analysis.",
]

for question in test_questions:
    print("\n" + "=" * 80)
    print("QUESTION:", question)

    result = router.classify(question)
    plan = router.get_execution_plan(result)

    compact_result = {
        "first_agent": result.get("first_agent"),
        "intent": result.get("intent"),
        "next_agent_after_scheduler": result.get("next_agent_after_scheduler"),
        "confidence": result.get("confidence"),
        "reason": result.get("reason"),
        "router_source": result.get("router_source"),
        "auditLogCount": len(result.get("auditLogs", [])),
        "auditContext": result.get("auditContext"),
    }

    print("\nROUTER RESULT:")
    print(json.dumps(compact_result, indent=2))

    print("\nEXECUTION PLAN:")
    print(" → ".join(plan))

    print("\nROUTER AUDIT STAGES:")
    print([log["thinking_stage"] for log in result.get("auditLogs", [])])