import json

from config.settings import settings
from plugins.audit_logging_plugin import AuditLoggingPlugin
from plugins.bright_data_search_plugin import BrightDataSearchPlugin
from plugins.source_quality_filter_plugin import SourceQualityFilterPlugin


audit_context = AuditLoggingPlugin.create_context(model_name=settings.gemini_model)

audit_plugin = AuditLoggingPlugin(
    default_agent_name="SOURCE_QUALITY_TEST",
    **audit_context,
)

bright_data_plugin = BrightDataSearchPlugin()
source_filter = SourceQualityFilterPlugin()

query = "Political risks manufacturing exports Taiwan to Singapore UPS current issues"

bright_data_result = bright_data_plugin.search(
    query=query,
    num_results=10,
    country="sg",
    language="en",
    location="Singapore",
    search_engine="google",
    audit_plugin=audit_plugin,
    audit_agent_name="SOURCE_QUALITY_TEST",
    audit_metadata={
        "test_file": "test_source_quality_filter.py",
        "stage_group": "evidence_search",
    },
)

filter_result = source_filter.filter_sources(
    bright_data_result=bright_data_result,
    max_trusted=8,
    max_usable=8,
    audit_plugin=audit_plugin,
    audit_agent_name="SOURCE_QUALITY_TEST",
    audit_metadata={
        "test_file": "test_source_quality_filter.py",
        "stage_group": "source_filtering",
    },
)

print("\nBRIGHT DATA SUCCESS:")
print(bright_data_result["success"])

print("\nBRIGHT DATA RESULT COUNT:")
print(bright_data_result.get("resultCount"))

print("\nSOURCE FILTER SUMMARY:")
print(json.dumps(filter_result["summary"], indent=2, ensure_ascii=False))

print("\nTRUSTED SOURCES:")
print(json.dumps(filter_result["trustedSources"], indent=2, ensure_ascii=False))

print("\nUSABLE SOURCES:")
print(json.dumps(filter_result["usableSources"], indent=2, ensure_ascii=False))

print("\nLOWER QUALITY SOURCES:")
print(json.dumps(filter_result["lowerQualitySources"], indent=2, ensure_ascii=False))

print("\nDISCARDED SOURCES:")
print(json.dumps(filter_result["discardedSources"], indent=2, ensure_ascii=False))

print("\nEVIDENCE PACK:")
print(json.dumps(filter_result["evidencePack"], indent=2, ensure_ascii=False))

print("\nAUDIT CONTEXT:")
print(json.dumps(audit_plugin.get_context(), indent=2, ensure_ascii=False))

print("\nAUDIT LOG COUNT:")
print(len(audit_plugin.get_logs()))

print("\nAUDIT STAGES:")
print([log["thinking_stage"] for log in audit_plugin.get_logs()])

print("\nAUDIT LOG PREVIEW:")
print(json.dumps(audit_plugin.get_logs(), indent=2, ensure_ascii=False))