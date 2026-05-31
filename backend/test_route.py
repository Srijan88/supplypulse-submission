import json

from agents.schedule_analyzer_agent import ScheduleAnalyzerAgent
from agents.route_risk_analyst_agent import RouteRiskAnalystAgent
from config.settings import settings
from plugins.audit_logging_plugin import AuditLoggingPlugin


audit_context = AuditLoggingPlugin.create_context(model_name=settings.gemini_model)

schedule_agent = ScheduleAnalyzerAgent(audit_context=audit_context)
schedule_result = schedule_agent.run_from_csv(settings.raw_data_path)

route_agent = RouteRiskAnalystAgent(audit_context=audit_context)
route_result = route_agent.run(schedule_result)

print("\nROUTE / LOGISTICS EXPOSURE LEVEL:")
print(route_result["routeExposureLevel"])

print("\nLOGISTICS SEARCH QUERY:")
print(route_result["logisticsSearchQuery"])

print("\nSEARCH LOCALIZATION:")
print(json.dumps(route_result["searchLocalization"], indent=2, ensure_ascii=False))

print("\nROUTE / LOGISTICS EXPOSURE SUMMARY:")
print(route_result["routeExposureSummary"])

print("\nEVIDENCE USED:")
print(json.dumps(route_result["evidenceUsed"], indent=2, ensure_ascii=False))

print("\nAFFECTED ITEMS:")
print(json.dumps(route_result["affectedItems"], indent=2, ensure_ascii=False))

print("\nKEY FINDINGS:")
print(json.dumps(route_result["keyFindings"], indent=2, ensure_ascii=False))

print("\nRECOMMENDED ACTIONS:")
print(json.dumps(route_result["recommendedActions"], indent=2, ensure_ascii=False))

print("\nLIMITATIONS:")
print(route_result["limitations"])

print("\nBRIGHT DATA SEARCH SUMMARY:")
print(json.dumps(route_result["brightDataSearch"], indent=2, ensure_ascii=False))

print("\nSOURCE QUALITY SUMMARY:")
print(json.dumps(route_result["sourceQuality"]["summary"], indent=2, ensure_ascii=False))

print("\nAUDIT CONTEXT:")
print(json.dumps(route_result["auditContext"], indent=2, ensure_ascii=False))

print("\nSCHEDULE AUDIT LOG COUNT:")
print(len(schedule_result["auditLogs"]))

print("\nROUTE AUDIT LOG COUNT:")
print(len(route_result["auditLogs"]))

print("\nROUTE AUDIT STAGES:")
print([log["thinking_stage"] for log in route_result["auditLogs"]])

print("\nSHARED RUN CHECK:")
print("schedule run_id:", schedule_result["auditContext"]["run_id"])
print("route run_id:   ", route_result["auditContext"]["run_id"])