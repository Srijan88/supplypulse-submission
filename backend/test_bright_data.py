import json

from plugins.audit_logging_plugin import AuditLoggingPlugin
from plugins.bright_data_search_plugin import BrightDataSearchPlugin
from config.settings import settings


audit_context = AuditLoggingPlugin.create_context(model_name=settings.gemini_model)

audit_plugin = AuditLoggingPlugin(
    default_agent_name="BRIGHT_DATA_TEST",
    **audit_context,
)

plugin = BrightDataSearchPlugin()

query = "Political risks manufacturing exports Taiwan to Singapore UPS current issues"

result = plugin.search(
    query=query,
    num_results=5,
    country="sg",
    language="en",
    location="Singapore",
    search_engine="google",
    audit_plugin=audit_plugin,
    audit_agent_name="BRIGHT_DATA_TEST",
    audit_metadata={
        "test_file": "test_bright_data.py",
        "purpose": "Validate Bright Data SERP localization and audit logging",
    },
)

print("\nBRIGHT DATA SEARCH SUCCESS:")
print(result["success"])

print("\nQUERY:")
print(result["query"])

print("\nTARGET URL:")
print(result.get("targetUrl"))

print("\nREQUEST METADATA:")
print(json.dumps(result.get("requestMetadata"), indent=2, ensure_ascii=False))

print("\nBRIGHT DATA STATUS CODE:")
print(result.get("brightDataStatusCode"))

print("\nRESULT COUNT:")
print(result.get("resultCount"))

if not result["success"]:
    print("\nERROR:")
    print(result.get("error"))
else:
    print("\nRESULTS:")
    print(json.dumps(result["results"], indent=2, ensure_ascii=False))

    print("\nTOP SOURCES:")
    print(json.dumps(plugin.extract_top_sources(result), indent=2, ensure_ascii=False))

print("\nAUDIT CONTEXT:")
print(json.dumps(audit_plugin.get_context(), indent=2, ensure_ascii=False))

print("\nAUDIT LOG COUNT:")
print(len(audit_plugin.get_logs()))

print("\nAUDIT STAGES:")
print([log["thinking_stage"] for log in audit_plugin.get_logs()])

print("\nAUDIT LOG PREVIEW:")
print(json.dumps(audit_plugin.get_logs(), indent=2, ensure_ascii=False))