import json

from agents.schedule_analyzer_agent import ScheduleAnalyzerAgent
from agents.trade_risk_analyst_agent import TradeRiskAnalystAgent
from config.settings import settings
from plugins.audit_logging_plugin import AuditLoggingPlugin


audit_context = AuditLoggingPlugin.create_context(model_name=settings.gemini_model)

schedule_agent = ScheduleAnalyzerAgent(audit_context=audit_context)
schedule_result = schedule_agent.run_from_csv(settings.raw_data_path)

trade_agent = TradeRiskAnalystAgent(audit_context=audit_context)
trade_result = trade_agent.run(schedule_result)

print("\nTRADE EXPOSURE LEVEL:")
print(trade_result["tradeExposureLevel"])

print("\nTARIFF SEARCH QUERY:")
print(trade_result["tariffSearchQuery"])

print("\nSEARCH LOCALIZATION:")
print(json.dumps(trade_result["searchLocalization"], indent=2, ensure_ascii=False))

print("\nTRADE EXPOSURE SUMMARY:")
print(trade_result["tradeExposureSummary"])

print("\nEVIDENCE USED:")
print(json.dumps(trade_result["evidenceUsed"], indent=2, ensure_ascii=False))

print("\nAFFECTED ITEMS:")
print(json.dumps(trade_result["affectedItems"], indent=2, ensure_ascii=False))

print("\nKEY FINDINGS:")
print(json.dumps(trade_result["keyFindings"], indent=2, ensure_ascii=False))

print("\nRECOMMENDED ACTIONS:")
print(json.dumps(trade_result["recommendedActions"], indent=2, ensure_ascii=False))

print("\nLIMITATIONS:")
print(trade_result["limitations"])

print("\nBRIGHT DATA SEARCH SUMMARY:")
print(json.dumps(trade_result["brightDataSearch"], indent=2, ensure_ascii=False))

print("\nSOURCE QUALITY SUMMARY:")
print(json.dumps(trade_result["sourceQuality"]["summary"], indent=2, ensure_ascii=False))

print("\nAUDIT CONTEXT:")
print(json.dumps(trade_result["auditContext"], indent=2, ensure_ascii=False))

print("\nSCHEDULE AUDIT LOG COUNT:")
print(len(schedule_result["auditLogs"]))

print("\nTRADE AUDIT LOG COUNT:")
print(len(trade_result["auditLogs"]))

print("\nTRADE AUDIT STAGES:")
print([log["thinking_stage"] for log in trade_result["auditLogs"]])

print("\nSHARED RUN CHECK:")
print("schedule run_id:", schedule_result["auditContext"]["run_id"])
print("trade run_id:   ", trade_result["auditContext"]["run_id"])