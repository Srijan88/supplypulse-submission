import json

from agents.schedule_analyzer_agent import ScheduleAnalyzerAgent
from agents.geo_risk_analyst_agent import GeoRiskAnalystAgent
from config.settings import settings
from plugins.audit_logging_plugin import AuditLoggingPlugin


audit_context = AuditLoggingPlugin.create_context(model_name=settings.gemini_model)

schedule_agent = ScheduleAnalyzerAgent(audit_context=audit_context)
schedule_result = schedule_agent.run_from_csv(settings.raw_data_path)

geo_agent = GeoRiskAnalystAgent(audit_context=audit_context)
geo_result = geo_agent.run(schedule_result)

print("\nGEO EXPOSURE LEVEL:")
print(geo_result["geoExposureLevel"])

print("\nPOLITICAL SEARCH QUERY:")
print(geo_result["politicalSearchQuery"])

print("\nSEARCH LOCALIZATION:")
print(json.dumps(geo_result["searchLocalization"], indent=2, ensure_ascii=False))

print("\nGEO EXPOSURE SUMMARY:")
print(geo_result["geoExposureSummary"])

print("\nEVIDENCE USED:")
print(json.dumps(geo_result["evidenceUsed"], indent=2, ensure_ascii=False))

print("\nAFFECTED ITEMS:")
print(json.dumps(geo_result["affectedItems"], indent=2, ensure_ascii=False))

print("\nKEY FINDINGS:")
print(json.dumps(geo_result["keyFindings"], indent=2, ensure_ascii=False))

print("\nRECOMMENDED ACTIONS:")
print(json.dumps(geo_result["recommendedActions"], indent=2, ensure_ascii=False))

print("\nLIMITATIONS:")
print(geo_result["limitations"])

print("\nBRIGHT DATA SEARCH SUMMARY:")
print(json.dumps(geo_result["brightDataSearch"], indent=2, ensure_ascii=False))

print("\nSOURCE QUALITY SUMMARY:")
print(json.dumps(geo_result["sourceQuality"]["summary"], indent=2, ensure_ascii=False))

print("\nAUDIT CONTEXT:")
print(json.dumps(geo_result["auditContext"], indent=2, ensure_ascii=False))

print("\nSCHEDULE AUDIT LOG COUNT:")
print(len(schedule_result["auditLogs"]))

print("\nGEO AUDIT LOG COUNT:")
print(len(geo_result["auditLogs"]))

print("\nGEO AUDIT STAGES:")
print([log["thinking_stage"] for log in geo_result["auditLogs"]])

print("\nSHARED RUN CHECK:")
print("schedule run_id:", schedule_result["auditContext"]["run_id"])
print("geo run_id:     ", geo_result["auditContext"]["run_id"])