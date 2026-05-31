import json

from agents.schedule_analyzer_agent import ScheduleAnalyzerAgent
from agents.risk_report_builder_agent import RiskReportBuilderAgent
from config.settings import settings
from plugins.audit_logging_plugin import AuditLoggingPlugin


audit_context = AuditLoggingPlugin.create_context(model_name=settings.gemini_model)

schedule_agent = ScheduleAnalyzerAgent(audit_context=audit_context)
schedule_result = schedule_agent.run_from_csv(settings.raw_data_path)

report_agent = RiskReportBuilderAgent(audit_context=audit_context)
report_result = report_agent.run(
    user_question="What are the schedule risks?",
    schedule_result=schedule_result,
)

print("\nEXECUTIVE SUMMARY:")
print(report_result["executiveSummary"])

print("\nDELIVERY EXPOSURE TABLE:")
print(report_result["deliveryExposureTable"])

print("\nREPORT AUDIT CONTEXT:")
print(json.dumps(report_result["auditContext"], indent=2))

print("\nSCHEDULE AUDIT LOG COUNT:")
print(len(schedule_result["auditLogs"]))

print("\nREPORT AUDIT LOG COUNT:")
print(len(report_result["auditLogs"]))

print("\nREPORT AUDIT STAGES:")
print([log["thinking_stage"] for log in report_result["auditLogs"]])

print("\nSHARED CONTEXT CHECK:")
print("schedule run_id:", schedule_result["auditContext"]["run_id"])
print("report run_id:  ", report_result["auditContext"]["run_id"])