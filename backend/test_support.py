import json

from agents.support_agent import SupportAgent


agent = SupportAgent()

result = agent.run("Hi, what can you do?")

print("\nSUPPORT RESPONSE:")
print(result["response"])

print("\nAUDIT CONTEXT:")
print(json.dumps(result["auditContext"], indent=2))

print("\nAUDIT LOG COUNT:")
print(len(result["auditLogs"]))

print("\nAUDIT STAGES:")
print([log["thinking_stage"] for log in result["auditLogs"]])