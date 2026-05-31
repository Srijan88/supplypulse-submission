from typing import Any, Dict, List, Optional


class AuditFlowPlugin:
    """
    SupplyPulse audit flow collector.

    Purpose:
    - Combine audit logs from multiple agents/plugins into one pipeline audit trail.
    - Validate that all agents share the same run_id.
    - Build a clean stage timeline for developer/debug UI.
    - Summarize evidence search activity without exposing secrets.

    Important:
    - This plugin does not call any LLM.
    - This plugin does not change business logic.
    - This plugin only organizes audit logs already produced by agents/plugins.
    """

    def build_pipeline_audit(
        self,
        pipeline_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        audit_context = pipeline_result.get("auditContext", {})

        agent_outputs = self._collect_agent_outputs(pipeline_result)
        all_logs = self._collect_all_logs(agent_outputs)

        return {
            "auditContext": audit_context,
            "sharedContextCheck": self._build_shared_context_check(
                audit_context=audit_context,
                agent_outputs=agent_outputs,
            ),
            "agentAuditCounts": self._build_agent_audit_counts(agent_outputs),
            "stageTimeline": self._build_stage_timeline(all_logs),
            "evidenceSearchSummary": self._build_evidence_search_summary(all_logs),
            "agentOutputSummary": self._build_agent_output_summary(pipeline_result),
            "totalAuditLogs": len(all_logs),
        }

    def _collect_agent_outputs(
        self,
        pipeline_result: Dict[str, Any],
    ) -> Dict[str, Dict[str, Any]]:
        possible_outputs = {
            "router": pipeline_result.get("routerResult"),
            "support": pipeline_result.get("supportResult"),
            "scheduleAnalyzer": pipeline_result.get("scheduleResult"),
            "geoAnalyst": pipeline_result.get("geoResult"),
            "tradeAnalyst": pipeline_result.get("tradeResult"),
            "routeAnalyst": pipeline_result.get("routeResult"),
            "reportBuilder": pipeline_result.get("reportResult"),
        }

        return {
            name: output
            for name, output in possible_outputs.items()
            if isinstance(output, dict)
        }

    def _collect_all_logs(
        self,
        agent_outputs: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        all_logs: List[Dict[str, Any]] = []

        for output_name, output in agent_outputs.items():
            logs = output.get("auditLogs", [])

            if not isinstance(logs, list):
                continue

            for log in logs:
                if not isinstance(log, dict):
                    continue

                enriched_log = {
                    **log,
                    "outputName": output_name,
                }

                all_logs.append(enriched_log)

        return sorted(
            all_logs,
            key=lambda log: (
                str(log.get("created_at", "")),
                int(log.get("sequence_number", 0) or 0),
            ),
        )

    def _build_shared_context_check(
        self,
        audit_context: Dict[str, Any],
        agent_outputs: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        expected_run_id = audit_context.get("run_id")

        checks: List[Dict[str, Any]] = []

        for output_name, output in agent_outputs.items():
            output_context = output.get("auditContext", {})
            output_run_id = output_context.get("run_id")

            checks.append(
                {
                    "outputName": output_name,
                    "runId": output_run_id,
                    "matchesPipelineRun": bool(
                        expected_run_id and output_run_id == expected_run_id
                    ),
                }
            )

        return {
            "expectedRunId": expected_run_id,
            "allOutputsShareRunId": all(item["matchesPipelineRun"] for item in checks)
            if checks
            else False,
            "checks": checks,
        }

    def _build_agent_audit_counts(
        self,
        agent_outputs: Dict[str, Dict[str, Any]],
    ) -> Dict[str, int]:
        counts: Dict[str, int] = {}

        for output_name, output in agent_outputs.items():
            logs = output.get("auditLogs", [])

            if isinstance(logs, list):
                counts[output_name] = len(logs)
            else:
                counts[output_name] = 0

        return counts

    def _build_stage_timeline(
        self,
        all_logs: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        timeline: List[Dict[str, Any]] = []

        for index, log in enumerate(all_logs, start=1):
            timeline.append(
                {
                    "timelineIndex": index,
                    "createdAt": log.get("created_at"),
                    "outputName": log.get("outputName"),
                    "agentName": log.get("agent_name"),
                    "stage": log.get("thinking_stage"),
                    "summary": log.get("thought_content"),
                    "sequenceNumber": log.get("sequence_number"),
                    "modelName": log.get("model_name"),
                    "logId": log.get("log_id"),
                }
            )

        return timeline

    def _build_evidence_search_summary(
        self,
        all_logs: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        evidence_events: List[Dict[str, Any]] = []

        for log in all_logs:
            stage = log.get("thinking_stage")
            stage_output = log.get("thinking_stage_output", {})

            if stage not in {
                "bright_data_search_request",
                "bright_data_search_response",
            }:
                continue

            if not isinstance(stage_output, dict):
                continue

            if stage == "bright_data_search_request":
                evidence_events.append(
                    {
                        "eventType": "search_request",
                        "agentName": log.get("agent_name"),
                        "query": stage_output.get("query"),
                        "targetUrl": stage_output.get("targetUrl"),
                        "searchEngine": stage_output.get("searchEngine"),
                        "glCountry": stage_output.get("gl_country"),
                        "hlLanguage": stage_output.get("hl_language"),
                        "location": stage_output.get("location"),
                        "uuleProvided": stage_output.get("uuleProvided"),
                        "numResultsRequested": stage_output.get("numResultsRequested"),
                        "createdAt": log.get("created_at"),
                    }
                )

            if stage == "bright_data_search_response":
                evidence_events.append(
                    {
                        "eventType": "search_response",
                        "agentName": log.get("agent_name"),
                        "success": stage_output.get("success"),
                        "statusCode": stage_output.get("brightDataStatusCode"),
                        "resultCount": stage_output.get("resultCount"),
                        "topSources": stage_output.get("topSources"),
                        "error": stage_output.get("error"),
                        "createdAt": log.get("created_at"),
                    }
                )

        return evidence_events

    def _build_agent_output_summary(
        self,
        pipeline_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        summary: Dict[str, Any] = {}

        router_result = pipeline_result.get("routerResult")
        if isinstance(router_result, dict):
            summary["router"] = {
                "firstAgent": router_result.get("first_agent"),
                "intent": router_result.get("intent"),
                "nextAgentAfterScheduler": router_result.get(
                    "next_agent_after_scheduler"
                ),
                "confidence": router_result.get("confidence"),
            }

        schedule_result = pipeline_result.get("scheduleResult")
        if isinstance(schedule_result, dict):
            summary["scheduleAnalyzer"] = {
                "summary": schedule_result.get("summary"),
                "searchQuery": schedule_result.get("searchQuery"),
            }

        support_result = pipeline_result.get("supportResult")
        if isinstance(support_result, dict):
            summary["support"] = {
                "hasResponse": bool(support_result.get("response")),
            }

        geo_result = pipeline_result.get("geoResult")
        if isinstance(geo_result, dict):
            summary["geoAnalyst"] = {
                "hasSummary": bool(geo_result.get("geoRiskSummary")),
                "level": geo_result.get("geoRiskLevel"),
            }

        trade_result = pipeline_result.get("tradeResult")
        if isinstance(trade_result, dict):
            summary["tradeAnalyst"] = {
                "hasSummary": bool(trade_result.get("tradeRiskSummary")),
                "level": trade_result.get("tradeRiskLevel"),
            }

        route_result = pipeline_result.get("routeResult")
        if isinstance(route_result, dict):
            summary["routeAnalyst"] = {
                "hasSummary": bool(route_result.get("routeRiskSummary")),
                "level": route_result.get("routeRiskLevel"),
            }

        report_result = pipeline_result.get("reportResult")
        if isinstance(report_result, dict):
            summary["reportBuilder"] = {
                "hasExecutiveSummary": bool(report_result.get("executiveSummary")),
                "hasDeliveryExposureTable": bool(
                    report_result.get("deliveryExposureTable")
                ),
                "hasMarkdownReport": bool(report_result.get("markdownReport")),
            }

        return summary