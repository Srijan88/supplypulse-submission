import json
import os
import re
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from config.settings import settings
from plugins.audit_logging_plugin import AuditLoggingPlugin


RISK_REPORT_BUILDER_AGENT = "RISK_REPORT_BUILDER_AGENT"


class RiskReportBuilderAgent:
    """
    SupplyPulse report builder.

    Responsibilities:
    - Combine Schedule Analyzer output with available intelligence agent outputs.
    - Keep the Delivery Exposure Table deterministic.
    - Include grounded geopolitical exposure only when geo_result is available.
    - Include grounded trade / tariff exposure only when trade_result is available.
    - Include grounded route / logistics exposure only when route_result is available.
    - Keep detailed delivery analysis schedule-focused to avoid duplicate intelligence sections.
    - Preserve SupplyPulse audit logs.
    """

    REPORT_RESPONSE_JSON_SCHEMA = {
        "type": "object",
        "properties": {
            "executiveSummary": {"type": "string"},
            "detailedAnalysisMarkdown": {"type": "string"},
            "recommendedActions": {
                "type": "array",
                "items": {"type": "string"},
            },
            "reportLimitations": {"type": "string"},
        },
        "required": [
            "executiveSummary",
            "detailedAnalysisMarkdown",
            "recommendedActions",
            "reportLimitations",
        ],
    }

    def __init__(self, audit_context: Optional[Dict[str, Any]] = None) -> None:
        self.agent_name = RISK_REPORT_BUILDER_AGENT

        context = audit_context or AuditLoggingPlugin.create_context(
            model_name=settings.gemini_model
        )

        self.audit_plugin = AuditLoggingPlugin(
            default_agent_name=self.agent_name,
            **context,
        )

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
            settings.google_application_credentials
        )

        self.client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )

    def run(
        self,
        user_question: str,
        schedule_result: Dict[str, Any],
        geo_result: Optional[Dict[str, Any]] = None,
        trade_result: Optional[Dict[str, Any]] = None,
        route_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        self.audit_plugin.clear()

        delivery_exposure_table = self._build_delivery_exposure_table(schedule_result)

        intelligence_section_number = 3

        geo_section = ""
        if geo_result:
            geo_section = self._build_geo_exposure_section(
                geo_result=geo_result,
                section_number=intelligence_section_number,
            )
            intelligence_section_number += 1

        trade_section = ""
        if trade_result:
            trade_section = self._build_trade_exposure_section(
                trade_result=trade_result,
                section_number=intelligence_section_number,
            )
            intelligence_section_number += 1

        route_section = ""
        if route_result:
            route_section = self._build_route_exposure_section(
                route_result=route_result,
                section_number=intelligence_section_number,
            )
            intelligence_section_number += 1

        detailed_analysis_section_number = intelligence_section_number

        intelligence_summary = self._build_intelligence_summary(
            geo_result=geo_result,
            trade_result=trade_result,
            route_result=route_result,
        )

        self.audit_plugin.log(
            stage="analysis_start",
            thought_content="Started SupplyPulse report building from schedule and available intelligence outputs.",
            stage_output={
                "userQuestion": user_question,
                "hasScheduleResult": bool(schedule_result),
                "hasGeoResult": bool(geo_result),
                "hasTradeResult": bool(trade_result),
                "hasRouteResult": bool(route_result),
            },
            metadata={
                "component": "risk_report_builder_agent",
            },
        )

        self.audit_plugin.log(
            stage="data_collection",
            thought_content="Collected schedule data and available downstream intelligence outputs.",
            stage_output={
                "scheduleSummary": schedule_result.get("summary"),
                "searchQuery": schedule_result.get("searchQuery"),
                "geoExposureLevel": self._safe_get(geo_result, "geoExposureLevel"),
                "geoAffectedItemsCount": len(
                    self._safe_get(geo_result, "affectedItems", [])
                ),
                "geoEvidenceUsedCount": len(
                    self._safe_get(geo_result, "evidenceUsed", [])
                ),
                "tradeExposureLevel": self._safe_get(
                    trade_result,
                    "tradeExposureLevel",
                ),
                "tradeAffectedItemsCount": len(
                    self._safe_get(trade_result, "affectedItems", [])
                ),
                "tradeEvidenceUsedCount": len(
                    self._safe_get(trade_result, "evidenceUsed", [])
                ),
                "routeExposureLevel": self._safe_get(
                    route_result,
                    "routeExposureLevel",
                ),
                "routeAffectedItemsCount": len(
                    self._safe_get(route_result, "affectedItems", [])
                ),
                "routeEvidenceUsedCount": len(
                    self._safe_get(route_result, "evidenceUsed", [])
                ),
            },
            metadata={
                "component": "risk_report_builder_agent",
                "data_sources": self._available_data_sources(
                    geo_result=geo_result,
                    trade_result=trade_result,
                    route_result=route_result,
                ),
            },
        )

        self.audit_plugin.log(
            stage="exposure_consolidation",
            thought_content="Consolidated schedule exposure with available downstream intelligence insights.",
            stage_output={
                "deliveryExposureTableRows": len(
                    schedule_result.get("equipmentItems", [])
                ),
                "highestExposureItems": self._get_top_schedule_items(
                    schedule_result,
                    limit=5,
                ),
                "geoAffectedItems": self._safe_get(geo_result, "affectedItems", []),
                "geoSourceQualitySummary": self._safe_get(
                    self._safe_get(geo_result, "sourceQuality", {}),
                    "summary",
                    {},
                ),
                "tradeAffectedItems": self._safe_get(
                    trade_result,
                    "affectedItems",
                    [],
                ),
                "tradeSourceQualitySummary": self._safe_get(
                    self._safe_get(trade_result, "sourceQuality", {}),
                    "summary",
                    {},
                ),
                "routeAffectedItems": self._safe_get(
                    route_result,
                    "affectedItems",
                    [],
                ),
                "routeSourceQualitySummary": self._safe_get(
                    self._safe_get(route_result, "sourceQuality", {}),
                    "summary",
                    {},
                ),
            },
            metadata={
                "component": "risk_report_builder_agent",
                "geo_result_used": bool(geo_result),
                "trade_result_used": bool(trade_result),
                "route_result_used": bool(route_result),
            },
        )

        planned_sections = [
            "Executive Summary",
            "Exposure Overview",
            "Delivery Exposure Table",
        ]

        if geo_section:
            planned_sections.append("Geopolitical Exposure")

        if trade_section:
            planned_sections.append("Trade / Tariff Exposure")

        if route_section:
            planned_sections.append("Route / Logistics Exposure")

        planned_sections.extend(
            [
                "Detailed Delivery Exposure Analysis",
                "Downstream Intelligence Queries",
                "Recommended Actions",
                "Limitations",
            ]
        )

        self.audit_plugin.log(
            stage="report_structure",
            thought_content="Prepared report structure with deterministic delivery table and optional intelligence sections.",
            stage_output={
                "sections": planned_sections,
                "deliveryTableGeneratedDeterministically": True,
                "geoSectionIncluded": bool(geo_section),
                "tradeSectionIncluded": bool(trade_section),
                "routeSectionIncluded": bool(route_section),
                "detailedAnalysisMustStayScheduleFocused": True,
            },
            metadata={
                "component": "risk_report_builder_agent",
            },
        )

        llm_result = self._call_llm_report_builder(
            user_question=user_question,
            schedule_result=schedule_result,
            geo_result=geo_result,
            trade_result=trade_result,
            route_result=route_result,
            delivery_exposure_table=delivery_exposure_table,
            geo_section=geo_section,
            trade_section=trade_section,
            route_section=route_section,
            intelligence_summary=intelligence_summary,
        )

        llm_result = self._apply_report_output_guardrails(llm_result)

        recommended_actions = llm_result.get("recommendedActions", [])

        detailed_analysis_markdown = self._sanitize_detailed_analysis_markdown(
            llm_result.get("detailedAnalysisMarkdown", ""),
            schedule_result=schedule_result,
        )

        self.audit_plugin.log(
            stage="recommendations",
            thought_content="Prepared prioritized report recommendations from schedule and available intelligence context.",
            stage_output={
                "recommendationCount": len(recommended_actions),
                "recommendations": recommended_actions,
            },
            metadata={
                "component": "risk_report_builder_agent",
            },
        )

        markdown_report = self._assemble_markdown_report(
            executive_summary=llm_result.get("executiveSummary", ""),
            schedule_result=schedule_result,
            delivery_exposure_table=delivery_exposure_table,
            geo_section=geo_section,
            trade_section=trade_section,
            route_section=route_section,
            detailed_analysis_markdown=detailed_analysis_markdown,
            recommended_actions=recommended_actions,
            report_limitations=llm_result.get("reportLimitations", ""),
            detailed_analysis_section_number=detailed_analysis_section_number,
        )

        result = {
            "agent": self.agent_name,
            "executiveSummary": llm_result.get("executiveSummary", ""),
            "deliveryExposureTable": delivery_exposure_table,
            "geoExposureSection": geo_section,
            "tradeExposureSection": trade_section,
            "routeExposureSection": route_section,
            "markdownReport": markdown_report,
            "recommendedActions": recommended_actions,
            "reportLimitations": llm_result.get("reportLimitations", ""),
            "inputSummary": {
                "hasGeoResult": bool(geo_result),
                "hasTradeResult": bool(trade_result),
                "hasRouteResult": bool(route_result),
                "geoExposureLevel": self._safe_get(geo_result, "geoExposureLevel"),
                "geoAffectedItemsCount": len(
                    self._safe_get(geo_result, "affectedItems", [])
                ),
                "tradeExposureLevel": self._safe_get(
                    trade_result,
                    "tradeExposureLevel",
                ),
                "tradeAffectedItemsCount": len(
                    self._safe_get(trade_result, "affectedItems", [])
                ),
                "routeExposureLevel": self._safe_get(
                    route_result,
                    "routeExposureLevel",
                ),
                "routeAffectedItemsCount": len(
                    self._safe_get(route_result, "affectedItems", [])
                ),
            },
        }

        self.audit_plugin.log(
            stage="final_output",
            thought_content="Prepared final SupplyPulse markdown report.",
            stage_output={
                "hasExecutiveSummary": bool(result.get("executiveSummary")),
                "hasDeliveryExposureTable": bool(result.get("deliveryExposureTable")),
                "hasGeoExposureSection": bool(result.get("geoExposureSection")),
                "hasTradeExposureSection": bool(result.get("tradeExposureSection")),
                "hasRouteExposureSection": bool(result.get("routeExposureSection")),
                "hasMarkdownReport": bool(result.get("markdownReport")),
                "detailedAnalysisSanitized": True,
            },
            agent_output={
                "executiveSummary": result.get("executiveSummary"),
            },
            metadata={
                "component": "risk_report_builder_agent",
            },
        )

        result["auditLogs"] = self.audit_plugin.get_logs()
        result["auditContext"] = self.audit_plugin.get_context()

        return result

    def _call_llm_report_builder(
        self,
        user_question: str,
        schedule_result: Dict[str, Any],
        geo_result: Optional[Dict[str, Any]],
        trade_result: Optional[Dict[str, Any]],
        route_result: Optional[Dict[str, Any]],
        delivery_exposure_table: str,
        geo_section: str,
        trade_section: str,
        route_section: str,
        intelligence_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        compact_schedule = self._compact_schedule_for_prompt(schedule_result)

        prompt = f"""
You are {self.agent_name}, the final report builder for SupplyPulse V2.

User question:
{user_question}

Schedule Analyzer context:
{json.dumps(compact_schedule, indent=2, default=str)}

Available intelligence summary:
{json.dumps(intelligence_summary, indent=2, default=str)}

Geo result:
{json.dumps(self._compact_geo_for_prompt(geo_result), indent=2, default=str)}

Trade result:
{json.dumps(self._compact_trade_for_prompt(trade_result), indent=2, default=str)}

Route result:
{json.dumps(self._compact_route_for_prompt(route_result), indent=2, default=str)}

Deterministic Delivery Exposure Table:
{delivery_exposure_table}

Deterministic Geopolitical Exposure Section:
{geo_section}

Deterministic Trade / Tariff Exposure Section:
{trade_section}

Deterministic Route / Logistics Exposure Section:
{route_section}

Task:
Create only the narrative JSON fields for the final SupplyPulse delivery exposure report.

Important rules:
- Use SupplyPulse terminology.
- Use "status band", not "risk category".
- Use "schedule exposure", not "risk probability".
- Do not use "risk probability" for Schedule Exposure %.
- Schedule Exposure % is a delay-pressure index, not a probability.
- Values above 100% are valid.
- Do not change equipment codes.
- Do not change dates.
- Do not change delay/gain days.
- Do not change Schedule Exposure % values.
- Do not invent source URLs or source titles.
- If geo_result is available, use it in the executive summary and recommendations only where relevant.
- If trade_result is available, use it in the executive summary and recommendations only where relevant.
- If route_result is available, use it in the executive summary and recommendations only where relevant.
- Do not recreate the Geopolitical Exposure section inside detailedAnalysisMarkdown.
- Do not recreate the Trade / Tariff Exposure section inside detailedAnalysisMarkdown.
- Do not recreate the Route / Logistics Exposure section inside detailedAnalysisMarkdown.
- Do not recreate Evidence Used, Source Quality Summary, Downstream Intelligence Queries, Recommended Actions, or Limitations inside detailedAnalysisMarkdown.
- detailedAnalysisMarkdown must focus only on delivery/schedule exposure details.
- detailedAnalysisMarkdown must not contain markdown headings starting with #, ##, or ###.
- detailedAnalysisMarkdown must not discuss ASTEP, customs duties, tariff rates, trade agreements, geopolitical exposure, route exposure, logistics exposure, port congestion, vessel delays, typhoon season, live port dashboards, evidence sources, or source quality.
- If a source is older than the current run date, describe it as historical or potentially stale, not future-dated.
- The word "future-dated" may only be used if the source date is later than the current run date.
- Do not recreate the Delivery Exposure Table. It is already provided deterministically.
- Do not include raw JSON.
- Keep recommendations practical for procurement, logistics, project delivery, trade compliance, and supplier management.

Output JSON only.
"""

        response = self.client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
                response_json_schema=self.REPORT_RESPONSE_JSON_SCHEMA,
            ),
        )

        try:
            return json.loads(response.text.strip())
        except Exception:
            return self._fallback_llm_result(
                schedule_result=schedule_result,
                geo_result=geo_result,
                trade_result=trade_result,
                route_result=route_result,
            )

    def _assemble_markdown_report(
        self,
        executive_summary: str,
        schedule_result: Dict[str, Any],
        delivery_exposure_table: str,
        geo_section: str,
        trade_section: str,
        route_section: str,
        detailed_analysis_markdown: str,
        recommended_actions: List[str],
        report_limitations: str,
        detailed_analysis_section_number: int,
    ) -> str:
        summary = schedule_result.get("summary", {})
        search_query = schedule_result.get("searchQuery", {})

        actions_markdown = self._build_recommended_actions_markdown(
            recommended_actions
        )

        report = f"""# SupplyPulse Delivery Exposure Report

## 1. Executive Summary

{executive_summary}

## 2. Exposure Overview

### 2.1 Status Breakdown

- **Total Items Tracked:** {summary.get("totalItems", 0)}
- **High-Exposure Items:** {summary.get("highRiskItems", 0)}
- **Medium-Exposure Items:** {summary.get("mediumRiskItems", 0)}
- **Low-Exposure Items:** {summary.get("lowRiskItems", 0)}
- **On-Track Items:** {summary.get("onTrackItems", 0)}

### 2.2 SupplyPulse Delivery Exposure Table

{delivery_exposure_table}

_Note: Schedule Exposure % is a delay-pressure index, not a probability. Values can exceed 100% when the forecast delay is larger than the time remaining before the planned need date._
"""

        if geo_section:
            report += f"\n\n{geo_section}"

        if trade_section:
            report += f"\n\n{trade_section}"

        if route_section:
            report += f"\n\n{route_section}"

        downstream_section_number = detailed_analysis_section_number + 1
        recommendations_section_number = detailed_analysis_section_number + 2
        limitations_section_number = detailed_analysis_section_number + 3

        report += f"""

## {detailed_analysis_section_number}. Detailed Delivery Exposure Analysis

{detailed_analysis_markdown}

## {downstream_section_number}. Downstream Intelligence Queries

- **Geopolitical Exposure Query:** {search_query.get("political", "Not available")}
- **Trade / Tariff Exposure Query:** {search_query.get("tariff", "Not available")}
- **Route / Logistics Exposure Query:** {search_query.get("logistics", "Not available")}

## {recommendations_section_number}. Recommended Actions

{actions_markdown}

## {limitations_section_number}. Limitations

{report_limitations}
"""

        return report.strip()

    def _sanitize_detailed_analysis_markdown(
        self,
        detailed_analysis_markdown: str,
        schedule_result: Dict[str, Any],
    ) -> str:
        text = str(detailed_analysis_markdown or "").strip()

        if not text:
            return self._fallback_detailed_schedule_analysis(schedule_result)

        forbidden_heading_keywords = {
            "geopolitical",
            "geo",
            "trade",
            "tariff",
            "customs",
            "astep",
            "agreement",
            "route",
            "logistics",
            "port",
            "evidence",
            "source",
            "source quality",
            "intelligence sourcing",
            "downstream",
            "query",
            "recommended",
            "recommendation",
            "limitation",
            "introduction",
        }

        cleaned_lines: List[str] = []
        skip_section = False

        for raw_line in text.splitlines():
            line = raw_line.rstrip()
            stripped = line.strip()

            if not stripped:
                if cleaned_lines and cleaned_lines[-1] != "":
                    cleaned_lines.append("")
                continue

            is_heading = stripped.startswith("#")
            heading_text = self._normalize_heading_text(stripped)

            if is_heading:
                should_skip = any(
                    keyword in heading_text
                    for keyword in forbidden_heading_keywords
                )

                if should_skip:
                    skip_section = True
                    continue

                skip_section = False

                if heading_text:
                    cleaned_lines.append(f"**{heading_text}:**")
                continue

            if skip_section:
                continue

            if self._line_looks_like_duplicate_section_title(stripped):
                continue

            cleaned_lines.append(line)

        cleaned = "\n".join(cleaned_lines).strip()

        if not cleaned:
            return self._fallback_detailed_schedule_analysis(schedule_result)

        if self._contains_out_of_scope_intelligence_terms(cleaned):
            return self._fallback_detailed_schedule_analysis(schedule_result)

        return cleaned

    def _line_looks_like_duplicate_section_title(self, line: str) -> bool:
        lowered = line.lower().strip("*: ")

        duplicate_titles = [
            "geopolitical exposure analysis",
            "geopolitical risks",
            "trade tariff exposure",
            "trade / tariff exposure",
            "tariff exposure",
            "route logistics exposure",
            "route / logistics exposure",
            "logistics exposure",
            "evidence used",
            "source quality summary",
            "downstream intelligence queries",
            "recommended actions",
            "limitations",
        ]

        return any(title in lowered for title in duplicate_titles)

    def _contains_out_of_scope_intelligence_terms(self, text: str) -> bool:
        lowered = text.lower()

        blocked_terms = [
            "geopolitical",
            "geo exposure",
            "taiwan strait",
            "trade tariff",
            "tariff exposure",
            "customs duties",
            "customs duty",
            "astep",
            "trade agreement",
            "free trade agreement",
            "preferential tariff",
            "certificate of origin",
            "route / logistics exposure",
            "route exposure",
            "logistics exposure",
            "port congestion",
            "vessel-level",
            "vessel wait",
            "typhoon season",
            "shipping route",
            "kaohsiung to singapore",
            "live port congestion",
            "source quality",
            "evidence used",
            "filtered evidence",
        ]

        return any(term in lowered for term in blocked_terms)

    def _normalize_heading_text(self, heading: str) -> str:
        cleaned = re.sub(r"^#+", "", heading).strip()
        cleaned = re.sub(r"^\d+(\.\d+)*\s*", "", cleaned).strip()
        cleaned = cleaned.strip("*: ")
        return cleaned.lower()

    def _fallback_detailed_schedule_analysis(
        self,
        schedule_result: Dict[str, Any],
    ) -> str:
        summary = schedule_result.get("summary", {})
        top_items = self._get_top_schedule_items(schedule_result, limit=8)

        top_items_markdown = "\n".join(
            [
                (
                    f"- **{item.get('equipmentCode')}** "
                    f"({item.get('equipmentName')}): "
                    f"{self._safe_float(item.get('scheduleExposurePercentage')):.2f}% "
                    f"Schedule Exposure, {item.get('delayDays')} delay/gain days, "
                    f"{item.get('sourceCountry')} → {item.get('destinationCountry')}."
                )
                for item in top_items
            ]
        )

        return f"""The schedule review covers {summary.get("totalItems", 0)} tracked delivery items. {summary.get("highRiskItems", 0)} items are currently in the High status band, while {summary.get("onTrackItems", 0)} items are on track or ahead of schedule.

The highest-exposure items should be prioritized because their forecast delay is large relative to the time remaining before the planned need date.

{top_items_markdown}

Items with Schedule Exposure above 100% require urgent follow-up because the forecast delay is larger than the remaining time before the planned need date. Items below 100% may still require monitoring when they are critical-path components or have limited recovery options."""

    def _build_delivery_exposure_table(self, schedule_result: Dict[str, Any]) -> str:
        items = schedule_result.get("equipmentItems", [])

        sorted_items = sorted(
            items,
            key=lambda item: (
                self._status_sort_value(item.get("scheduleRiskLevel")),
                -self._safe_float(item.get("scheduleRiskPercentage")),
                item.get("equipmentCode") or "",
            ),
        )

        lines = [
            "| Item Code | Asset / Equipment | Planned Need Date | Forecast Arrival | Delay / Gain (days) | Schedule Exposure % | Status Band | Source Country | Destination Country |",
            "|---|---|---|---|---:|---:|---|---|---|",
        ]

        for item in sorted_items:
            equipment_code = self._clean_cell(item.get("equipmentCode"))
            equipment_name = self._clean_cell(item.get("equipmentName"))
            planned_need_date = self._clean_cell(item.get("baselineDueDate"))
            forecast_arrival = self._clean_cell(item.get("latestExpectedDeliveryDate"))
            delay_days = self._safe_int(item.get("delayDays"))
            schedule_exposure = self._safe_float(item.get("scheduleRiskPercentage"))
            status_band = self._clean_cell(item.get("scheduleRiskLevel"))
            source_country = self._clean_cell(item.get("originCountry"))
            destination_country = self._clean_cell(item.get("projectCountry"))

            lines.append(
                f"| {equipment_code} | {equipment_name} | {planned_need_date} | "
                f"{forecast_arrival} | {delay_days} | {schedule_exposure:.2f}% | "
                f"{status_band} | {source_country} | {destination_country} |"
            )

        return "\n".join(lines)

    def _build_geo_exposure_section(
        self,
        geo_result: Dict[str, Any],
        section_number: int,
    ) -> str:
        geo_level = geo_result.get("geoExposureLevel", "Unknown")
        geo_summary = geo_result.get("geoExposureSummary", "")
        affected_items = geo_result.get("affectedItems", [])
        key_findings = geo_result.get("keyFindings", [])
        recommended_actions = geo_result.get("recommendedActions", [])
        limitations = geo_result.get("limitations", "")
        evidence_used = geo_result.get("evidenceUsed", [])
        source_quality_summary = geo_result.get("sourceQuality", {}).get("summary", {})
        bright_data_search = geo_result.get("brightDataSearch", {})

        affected_items_markdown = self._build_geo_affected_items_markdown(
            affected_items
        )
        findings_markdown = self._build_bullets(key_findings)
        actions_markdown = self._build_bullets(recommended_actions)
        evidence_markdown = self._build_evidence_markdown(evidence_used)

        return f"""## {section_number}. Geopolitical Exposure

### {section_number}.1 Exposure Level

**{geo_level}**

### {section_number}.2 Summary

{geo_summary}

### {section_number}.3 Affected Items

{affected_items_markdown}

### {section_number}.4 Evidence Used

{evidence_markdown}

### {section_number}.5 Source Quality Summary

- **Raw Results Reviewed:** {source_quality_summary.get("rawResultCount", 0)}
- **Trusted Sources:** {source_quality_summary.get("trustedCount", 0)}
- **Usable Sources:** {source_quality_summary.get("usableCount", 0)}
- **Lower-Quality Sources:** {source_quality_summary.get("lowerQualityCount", 0)}
- **Evidence-Ready Sources:** {source_quality_summary.get("evidenceReadyCount", 0)}
- **Search Localization:** {bright_data_search.get("location", "Not available")} ({bright_data_search.get("country", "n/a")})
- **Matched Item:** {bright_data_search.get("matchedEquipmentCode", "Not available")}

### {section_number}.6 Key Findings

{findings_markdown}

### {section_number}.7 Geo-Specific Recommended Actions

{actions_markdown}

### {section_number}.8 Geo Analysis Limitations

{limitations}"""

    def _build_trade_exposure_section(
        self,
        trade_result: Dict[str, Any],
        section_number: int,
    ) -> str:
        trade_level = trade_result.get("tradeExposureLevel", "Unknown")
        trade_summary = trade_result.get("tradeExposureSummary", "")
        affected_items = trade_result.get("affectedItems", [])
        key_findings = trade_result.get("keyFindings", [])
        recommended_actions = trade_result.get("recommendedActions", [])
        limitations = trade_result.get("limitations", "")
        evidence_used = trade_result.get("evidenceUsed", [])
        source_quality_summary = trade_result.get("sourceQuality", {}).get(
            "summary",
            {},
        )
        bright_data_search = trade_result.get("brightDataSearch", {})

        affected_items_markdown = self._build_trade_affected_items_markdown(
            affected_items
        )
        findings_markdown = self._build_bullets(key_findings)
        actions_markdown = self._build_bullets(recommended_actions)
        evidence_markdown = self._build_evidence_markdown(evidence_used)

        return f"""## {section_number}. Trade / Tariff Exposure

### {section_number}.1 Exposure Level

**{trade_level}**

### {section_number}.2 Summary

{trade_summary}

### {section_number}.3 Affected Items

{affected_items_markdown}

### {section_number}.4 Evidence Used

{evidence_markdown}

### {section_number}.5 Source Quality Summary

- **Raw Results Reviewed:** {source_quality_summary.get("rawResultCount", 0)}
- **Trusted Sources:** {source_quality_summary.get("trustedCount", 0)}
- **Usable Sources:** {source_quality_summary.get("usableCount", 0)}
- **Lower-Quality Sources:** {source_quality_summary.get("lowerQualityCount", 0)}
- **Evidence-Ready Sources:** {source_quality_summary.get("evidenceReadyCount", 0)}
- **Search Localization:** {bright_data_search.get("location", "Not available")} ({bright_data_search.get("country", "n/a")})
- **Matched Item:** {bright_data_search.get("matchedEquipmentCode", "Not available")}

### {section_number}.6 Key Findings

{findings_markdown}

### {section_number}.7 Trade-Specific Recommended Actions

{actions_markdown}

### {section_number}.8 Trade Analysis Limitations

{limitations}"""

    def _build_route_exposure_section(
        self,
        route_result: Dict[str, Any],
        section_number: int,
    ) -> str:
        route_level = route_result.get("routeExposureLevel", "Unknown")
        route_summary = route_result.get("routeExposureSummary", "")
        affected_items = route_result.get("affectedItems", [])
        key_findings = route_result.get("keyFindings", [])
        recommended_actions = route_result.get("recommendedActions", [])
        limitations = route_result.get("limitations", "")
        evidence_used = route_result.get("evidenceUsed", [])
        source_quality_summary = route_result.get("sourceQuality", {}).get(
            "summary",
            {},
        )
        bright_data_search = route_result.get("brightDataSearch", {})

        affected_items_markdown = self._build_route_affected_items_markdown(
            affected_items
        )
        findings_markdown = self._build_bullets(key_findings)
        actions_markdown = self._build_bullets(recommended_actions)
        evidence_markdown = self._build_evidence_markdown(evidence_used)

        return f"""## {section_number}. Route / Logistics Exposure

### {section_number}.1 Exposure Level

**{route_level}**

### {section_number}.2 Summary

{route_summary}

### {section_number}.3 Affected Items

{affected_items_markdown}

### {section_number}.4 Evidence Used

{evidence_markdown}

### {section_number}.5 Source Quality Summary

- **Raw Results Reviewed:** {source_quality_summary.get("rawResultCount", 0)}
- **Trusted Sources:** {source_quality_summary.get("trustedCount", 0)}
- **Usable Sources:** {source_quality_summary.get("usableCount", 0)}
- **Lower-Quality Sources:** {source_quality_summary.get("lowerQualityCount", 0)}
- **Evidence-Ready Sources:** {source_quality_summary.get("evidenceReadyCount", 0)}
- **Search Localization:** {bright_data_search.get("location", "Not available")} ({bright_data_search.get("country", "n/a")})
- **Matched Item:** {bright_data_search.get("matchedEquipmentCode", "Not available")}

### {section_number}.6 Key Findings

{findings_markdown}

### {section_number}.7 Route-Specific Recommended Actions

{actions_markdown}

### {section_number}.8 Route Analysis Limitations

{limitations}"""

    def _build_geo_affected_items_markdown(
        self,
        affected_items: List[Dict[str, Any]],
    ) -> str:
        if not affected_items:
            return "No equipment item was directly linked to geopolitical exposure from the available evidence."

        lines = [
            "| Item Code | Asset / Equipment | Source Country | Destination Country | Schedule Exposure % | Status Band | Geo Exposure Reason |",
            "|---|---|---|---|---:|---|---|",
        ]

        for item in affected_items:
            lines.append(
                f"| {self._clean_cell(item.get('equipmentCode'))} | "
                f"{self._clean_cell(item.get('equipmentName'))} | "
                f"{self._clean_cell(item.get('sourceCountry'))} | "
                f"{self._clean_cell(item.get('destinationCountry'))} | "
                f"{self._safe_float(item.get('scheduleExposurePercentage')):.2f}% | "
                f"{self._clean_cell(item.get('statusBand'))} | "
                f"{self._clean_cell(item.get('geoExposureReason'))} |"
            )

        return "\n".join(lines)

    def _build_trade_affected_items_markdown(
        self,
        affected_items: List[Dict[str, Any]],
    ) -> str:
        if not affected_items:
            return "No equipment item was directly linked to trade / tariff exposure from the available evidence."

        lines = [
            "| Item Code | Asset / Equipment | Source Country | Destination Country | Schedule Exposure % | Status Band | Trade / Tariff Exposure Reason |",
            "|---|---|---|---|---:|---|---|",
        ]

        for item in affected_items:
            lines.append(
                f"| {self._clean_cell(item.get('equipmentCode'))} | "
                f"{self._clean_cell(item.get('equipmentName'))} | "
                f"{self._clean_cell(item.get('sourceCountry'))} | "
                f"{self._clean_cell(item.get('destinationCountry'))} | "
                f"{self._safe_float(item.get('scheduleExposurePercentage')):.2f}% | "
                f"{self._clean_cell(item.get('statusBand'))} | "
                f"{self._clean_cell(item.get('tradeExposureReason'))} |"
            )

        return "\n".join(lines)

    def _build_route_affected_items_markdown(
        self,
        affected_items: List[Dict[str, Any]],
    ) -> str:
        if not affected_items:
            return "No equipment item was directly linked to route / logistics exposure from the available evidence."

        lines = [
            "| Item Code | Asset / Equipment | Source Country | Destination Country | Source Port | Destination Port | Schedule Exposure % | Status Band | Route / Logistics Exposure Reason |",
            "|---|---|---|---|---|---|---:|---|---|",
        ]

        for item in affected_items:
            lines.append(
                f"| {self._clean_cell(item.get('equipmentCode'))} | "
                f"{self._clean_cell(item.get('equipmentName'))} | "
                f"{self._clean_cell(item.get('sourceCountry'))} | "
                f"{self._clean_cell(item.get('destinationCountry'))} | "
                f"{self._clean_cell(item.get('sourcePort'))} | "
                f"{self._clean_cell(item.get('destinationPort'))} | "
                f"{self._safe_float(item.get('scheduleExposurePercentage')):.2f}% | "
                f"{self._clean_cell(item.get('statusBand'))} | "
                f"{self._clean_cell(item.get('routeExposureReason'))} |"
            )

        return "\n".join(lines)

    def _build_evidence_markdown(
        self,
        evidence_used: List[Dict[str, Any]],
    ) -> str:
        if not evidence_used:
            return "No filtered external evidence was used."

        lines = [
            "| Source | Category | Evidence Summary | Relevance |",
            "|---|---|---|---|",
        ]

        for source in evidence_used:
            rank = source.get("rank")
            title = self._clean_cell(source.get("sourceTitle"))
            url = self._clean_cell(source.get("sourceUrl"))
            domain = self._clean_cell(source.get("sourceDomain"))
            category = self._clean_cell(source.get("sourceCategory"))
            evidence_summary = self._clean_cell(source.get("evidenceSummary"))
            relevance_reason = self._clean_cell(source.get("relevanceReason"))

            display_title = title or domain or "Unknown source"

            if rank is not None:
                display_title = f"{display_title} — Rank {rank}"

            if url:
                source_label = f"[{display_title}]({url})"
            else:
                source_label = display_title

            lines.append(
                f"| {source_label} | {category} | {evidence_summary} | {relevance_reason} |"
            )

        return "\n".join(lines)

    def _build_recommended_actions_markdown(self, actions: List[str]) -> str:
        if not actions:
            return "- Continue monitoring high-exposure items and refresh external evidence before major procurement decisions."

        return "\n".join(
            f"{index}. {action}"
            for index, action in enumerate(actions, start=1)
        )

    def _build_bullets(self, values: List[str]) -> str:
        if not values:
            return "- Not available."

        return "\n".join(f"- {value}" for value in values)

    def _compact_schedule_for_prompt(
        self,
        schedule_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "summary": schedule_result.get("summary"),
            "searchQuery": schedule_result.get("searchQuery"),
            "topScheduleItems": self._get_top_schedule_items(
                schedule_result,
                limit=8,
            ),
            "analysisNote": (
                "Schedule Exposure % is a delay-pressure index, not a probability. "
                "Values above 100% are valid."
            ),
        }

    def _compact_geo_for_prompt(
        self,
        geo_result: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not geo_result:
            return {}

        return {
            "geoExposureLevel": geo_result.get("geoExposureLevel"),
            "geoExposureSummary": geo_result.get("geoExposureSummary"),
            "affectedItems": geo_result.get("affectedItems", []),
            "keyFindings": geo_result.get("keyFindings", []),
            "recommendedActions": geo_result.get("recommendedActions", []),
            "limitations": geo_result.get("limitations"),
            "brightDataSearch": geo_result.get("brightDataSearch"),
            "sourceQualitySummary": geo_result.get("sourceQuality", {}).get("summary"),
            "evidenceUsed": geo_result.get("evidenceUsed", []),
        }

    def _compact_trade_for_prompt(
        self,
        trade_result: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not trade_result:
            return {}

        return {
            "tradeExposureLevel": trade_result.get("tradeExposureLevel"),
            "tradeExposureSummary": trade_result.get("tradeExposureSummary"),
            "affectedItems": trade_result.get("affectedItems", []),
            "keyFindings": trade_result.get("keyFindings", []),
            "recommendedActions": trade_result.get("recommendedActions", []),
            "limitations": trade_result.get("limitations"),
            "brightDataSearch": trade_result.get("brightDataSearch"),
            "sourceQualitySummary": trade_result.get("sourceQuality", {}).get(
                "summary"
            ),
            "evidenceUsed": trade_result.get("evidenceUsed", []),
        }

    def _compact_route_for_prompt(
        self,
        route_result: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not route_result:
            return {}

        return {
            "routeExposureLevel": route_result.get("routeExposureLevel"),
            "routeExposureSummary": route_result.get("routeExposureSummary"),
            "affectedItems": route_result.get("affectedItems", []),
            "keyFindings": route_result.get("keyFindings", []),
            "recommendedActions": route_result.get("recommendedActions", []),
            "limitations": route_result.get("limitations"),
            "brightDataSearch": route_result.get("brightDataSearch"),
            "sourceQualitySummary": route_result.get("sourceQuality", {}).get(
                "summary"
            ),
            "evidenceUsed": route_result.get("evidenceUsed", []),
        }

    def _build_intelligence_summary(
        self,
        geo_result: Optional[Dict[str, Any]],
        trade_result: Optional[Dict[str, Any]],
        route_result: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return {
            "geo": {
                "available": bool(geo_result),
                "level": self._safe_get(geo_result, "geoExposureLevel"),
                "affectedItems": self._safe_get(geo_result, "affectedItems", []),
                "evidenceUsedCount": len(
                    self._safe_get(geo_result, "evidenceUsed", [])
                ),
            },
            "trade": {
                "available": bool(trade_result),
                "level": self._safe_get(trade_result, "tradeExposureLevel"),
                "affectedItems": self._safe_get(trade_result, "affectedItems", []),
                "evidenceUsedCount": len(
                    self._safe_get(trade_result, "evidenceUsed", [])
                ),
            },
            "route": {
                "available": bool(route_result),
                "level": self._safe_get(route_result, "routeExposureLevel"),
                "affectedItems": self._safe_get(route_result, "affectedItems", []),
                "evidenceUsedCount": len(
                    self._safe_get(route_result, "evidenceUsed", [])
                ),
            },
        }

    def _available_data_sources(
        self,
        geo_result: Optional[Dict[str, Any]],
        trade_result: Optional[Dict[str, Any]],
        route_result: Optional[Dict[str, Any]],
    ) -> List[str]:
        sources = ["scheduleAnalyzer"]

        if geo_result:
            sources.append("geoAnalyst")

        if trade_result:
            sources.append("tradeAnalyst")

        if route_result:
            sources.append("routeAnalyst")

        return sources

    def _get_top_schedule_items(
        self,
        schedule_result: Dict[str, Any],
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        items = schedule_result.get("equipmentItems", [])

        high_items = [
            item for item in items if item.get("scheduleRiskLevel") == "High"
        ]

        sorted_items = sorted(
            high_items,
            key=lambda item: -self._safe_float(item.get("scheduleRiskPercentage")),
        )

        return [
            {
                "equipmentCode": item.get("equipmentCode"),
                "equipmentName": item.get("equipmentName"),
                "sourceCountry": item.get("originCountry"),
                "destinationCountry": item.get("projectCountry"),
                "delayDays": item.get("delayDays"),
                "scheduleExposurePercentage": item.get("scheduleRiskPercentage"),
                "statusBand": item.get("scheduleRiskLevel"),
            }
            for item in sorted_items[:limit]
        ]

    def _fallback_llm_result(
        self,
        schedule_result: Dict[str, Any],
        geo_result: Optional[Dict[str, Any]],
        trade_result: Optional[Dict[str, Any]],
        route_result: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        summary = schedule_result.get("summary", {})
        intelligence_sentences = []

        if geo_result:
            intelligence_sentences.append(
                f"Geopolitical exposure was assessed as "
                f"{geo_result.get('geoExposureLevel', 'Unknown')}, with "
                f"{len(geo_result.get('affectedItems', []))} item(s) directly linked "
                f"to external geopolitical evidence."
            )

        if trade_result:
            intelligence_sentences.append(
                f"Trade / tariff exposure was assessed as "
                f"{trade_result.get('tradeExposureLevel', 'Unknown')}, with "
                f"{len(trade_result.get('affectedItems', []))} item(s) directly linked "
                f"to external trade evidence."
            )

        if route_result:
            intelligence_sentences.append(
                f"Route / logistics exposure was assessed as "
                f"{route_result.get('routeExposureLevel', 'Unknown')}, with "
                f"{len(route_result.get('affectedItems', []))} item(s) directly linked "
                f"to external route evidence."
            )

        intelligence_summary = " ".join(intelligence_sentences)

        return {
            "executiveSummary": (
                f"SupplyPulse reviewed {summary.get('totalItems', 0)} tracked items. "
                f"{summary.get('highRiskItems', 0)} items are in the High status band, "
                f"while {summary.get('onTrackItems', 0)} items are on track. "
                f"{intelligence_summary}"
            ).strip(),
            "detailedAnalysisMarkdown": self._fallback_detailed_schedule_analysis(
                schedule_result
            ),
            "recommendedActions": [
                "Prioritize high-exposure items with the highest Schedule Exposure %.",
                "Engage suppliers for revised delivery commitments and acceleration options.",
                "Review external intelligence findings for directly affected items.",
                "Prepare contingency plans for items with limited time remaining before planned need date.",
            ],
            "reportLimitations": (
                "This fallback report was generated because the LLM report response could not be parsed. "
                "The delivery table and intelligence sections remain deterministic from available agent outputs."
            ),
        }

    def _apply_report_output_guardrails(
        self,
        value: Any,
    ) -> Any:
        if isinstance(value, str):
            return self._clean_report_guardrail_text(value)

        if isinstance(value, list):
            return [self._apply_report_output_guardrails(item) for item in value]

        if isinstance(value, dict):
            return {
                key: self._apply_report_output_guardrails(item)
                for key, item in value.items()
            }

        return value

    def _clean_report_guardrail_text(self, text: str) -> str:
        cleaned = str(text or "")

        cleaned = re.sub(
            pattern=(
                r"future-dated\s*\(([^)]*?20(?:1|2)\d[^)]*)\)\s*"
                r"relative to the current run date\s*\(([^)]*)\)"
            ),
            repl=lambda match: self._clean_future_dated_report_phrase(match),
            string=cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            pattern=r"\brisk probability\b",
            repl="schedule exposure",
            string=cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            pattern=r"\brisk category\b",
            repl="status band",
            string=cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            pattern=r"\brisk categories\b",
            repl="status bands",
            string=cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            pattern=r"\bhigh probability of further delays\b",
            repl="high route / logistics exposure",
            string=cleaned,
            flags=re.IGNORECASE,
        )

        return cleaned

    def _clean_future_dated_report_phrase(self, match: re.Match) -> str:
        source_date_label = match.group(1)
        run_date_label = match.group(2)

        source_year = self._extract_year(source_date_label)
        run_year = self._extract_year(run_date_label)

        if source_year and run_year and source_year < run_year:
            return (
                f"historical ({source_date_label}) relative to the current "
                f"run date ({run_date_label})"
            )

        if source_year and run_year and source_year > run_year:
            return (
                f"future-dated ({source_date_label}) relative to the current "
                f"run date ({run_date_label})"
            )

        return (
            f"date-sensitive ({source_date_label}) relative to the current "
            f"run date ({run_date_label})"
        )

    @staticmethod
    def _extract_year(value: Any) -> Optional[int]:
        match = re.search(r"\b(20\d{2}|19\d{2})\b", str(value or ""))

        if not match:
            return None

        return int(match.group(1))

    @staticmethod
    def _safe_get(
        value: Optional[Dict[str, Any]],
        key: str,
        default: Any = None,
    ) -> Any:
        if not isinstance(value, dict):
            return default

        return value.get(key, default)

    @staticmethod
    def _clean_cell(value: Any) -> str:
        text = str(value if value is not None else "").strip()
        return text.replace("|", "/").replace("\n", " ")

    @staticmethod
    def _safe_float(value: Any) -> float:
        try:
            return float(value)
        except Exception:
            return 0.0

    @staticmethod
    def _safe_int(value: Any) -> int:
        try:
            return int(float(value))
        except Exception:
            return 0

    @staticmethod
    def _status_sort_value(status: Any) -> int:
        status_text = str(status or "").lower()

        if status_text == "high":
            return 0

        if status_text == "medium":
            return 1

        if status_text == "low":
            return 2

        return 3