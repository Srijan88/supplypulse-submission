import json

from agents.schedule_analyzer_agent import ScheduleAnalyzerAgent
from config.settings import settings


agent = ScheduleAnalyzerAgent()
result = agent.run_from_csv(settings.raw_data_path)

print("\nSUMMARY:")
print(json.dumps(result["summary"], indent=2))

print("\nFIRST EQUIPMENT ITEM:")
print(json.dumps(result["equipmentItems"][0], indent=2))

print("\nSEARCH QUERIES:")
print(json.dumps(result["searchQuery"], indent=2))

print("\nAUDIT LOG COUNT:")
print(len(result["auditLogs"]))

print("\nAUDIT LOG PREVIEW:")
print(json.dumps(result["auditLogs"][:2], indent=2))