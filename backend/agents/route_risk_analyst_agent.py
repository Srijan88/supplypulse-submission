import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from google import genai
from google.genai import types

from config.settings import settings
from plugins.audit_logging_plugin import AuditLoggingPlugin
from plugins.bright_data_search_plugin import BrightDataSearchPlugin
from plugins.source_quality_filter_plugin import SourceQualityFilterPlugin


ROUTE_RISK_ANALYST_AGENT = "ROUTE_RISK_ANALYST_AGENT"


class RouteRiskAnalystAgent:
    """
    SupplyPulse route / logistics exposure analyst.

    Responsibilities:
    - Read Schedule Analyzer output.
    - Use searchQuery.logistics.
    - Run localized Bright Data SERP search.
    - Filter source quality.
    - Use LLM to assess route, port, carrier, congestion, disruption, and logistics exposure.
    - Treat source freshness relative to current run date, not planned delivery dates.
    - Apply deterministic post-LLM guardrails for freshness wording and SupplyPulse terminology.
    - Produce SupplyPulse audit logs.
    """

    ROUTE_RESPONSE_JSON_SCHEMA = {
        "type": "object",
        "properties": {
            "agent": {"type": "string"},
            "routeExposureLevel": {
                "type": "string",
                "enum": ["High", "Medium", "Low", "Unknown"],
            },
            "routeExposureSummary": {"type": "string"},
            "logisticsSearchQuery": {"type": "string"},
            "searchLocalization": {
                "type": "object",
                "properties": {
                    "country": {"type": "string"},
                    "language": {"type": "string"},
                    "location": {"type": "string"},
                },
                "required": ["country", "language", "location"],
            },
            "evidenceUsed": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "rank": {"type": "number"},
                        "sourceTitle": {"type": "string"},
                        "sourceUrl": {"type": "string"},
                        "sourceDomain": {"type": "string"},
                        "sourceCategory": {"type": "string"},
                        "evidenceSummary": {"type": "string"},
                        "relevanceReason": {"type": "string"},
                    },
                    "required": [
                        "rank",
                        "sourceTitle",
                        "sourceUrl",
                        "sourceDomain",
                        "sourceCategory",
                        "evidenceSummary",
                        "relevanceReason",
                    ],
                },
            },
            "affectedItems": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "equipmentCode": {"type": "string"},
                        "equipmentName": {"type": "string"},
                        "sourceCountry": {"type": "string"},
                        "destinationCountry": {"type": "string"},
                        "sourcePort": {"type": "string"},
                        "destinationPort": {"type": "string"},
                        "scheduleExposurePercentage": {"type": "number"},
                        "statusBand": {"type": "string"},
                        "routeExposureReason": {"type": "string"},
                    },
                    "required": [
                        "equipmentCode",
                        "equipmentName",
                        "sourceCountry",
                        "destinationCountry",
                        "sourcePort",
                        "destinationPort",
                        "scheduleExposurePercentage",
                        "statusBand",
                        "routeExposureReason",
                    ],
                },
            },
            "keyFindings": {
                "type": "array",
                "items": {"type": "string"},
            },
            "recommendedActions": {
                "type": "array",
                "items": {"type": "string"},
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
            },
            "limitations": {"type": "string"},
        },
        "required": [
            "agent",
            "routeExposureLevel",
            "routeExposureSummary",
            "logisticsSearchQuery",
            "searchLocalization",
            "evidenceUsed",
            "affectedItems",
            "keyFindings",
            "recommendedActions",
            "confidence",
            "limitations",
        ],
    }

    COUNTRY_TO_GL = {
        "Australia": "au",
        "Brazil": "br",
        "China": "cn",
        "Denmark": "dk",
        "France": "fr",
        "Germany": "de",
        "India": "in",
        "Italy": "it",
        "Japan": "jp",
        "Malaysia": "my",
        "Netherlands": "nl",
        "Singapore": "sg",
        "South Korea": "kr",
        "Sweden": "se",
        "Switzerland": "ch",
        "Taiwan": "tw",
        "United Arab Emirates": "ae",
        "United States": "us",
    }

    def __init__(self, audit_context: Optional[Dict[str, Any]] = None) -> None:
        self.agent_name = ROUTE_RISK_ANALYST_AGENT

        context = audit_context or AuditLoggingPlugin.create_context(
            model_name=settings.gemini_model
        )

        self.audit_plugin = AuditLoggingPlugin(
            default_agent_name=self.agent_name,
            **context,
        )

        self.bright_data_plugin = BrightDataSearchPlugin()
        self.source_filter_plugin = SourceQualityFilterPlugin()

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
            settings.google_application_credentials
        )

        self.client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )

    def run(self, schedule_result: Dict[str, Any]) -> Dict[str, Any]:
        self.audit_plugin.clear()

        current_run_date = self._current_utc_date()
        logistics_query = self._get_logistics_search_query(schedule_result)
        compact_context = self._build_compact_context(schedule_result)

        localization = self._infer_search_localization(
            compact_context=compact_context,
            logistics_query=logistics_query,
        )

        self.audit_plugin.log(
            stage="analysis_start",
            thought_content="Started route and logistics exposure analysis from Schedule Analyzer output.",
            stage_output={
                "currentRunDateUtc": current_run_date,
                "schedulerSummary": schedule_result.get("summary"),
                "logisticsSearchQuery": logistics_query,
                "searchLocalization": localization,
            },
            metadata={
                "component": "route_risk_analyst_agent",
                "input_agent": schedule_result.get("agent"),
            },
        )

        self.audit_plugin.log(
            stage="schedule_context_extraction",
            thought_content="Prepared high-exposure schedule context for route and logistics exposure review.",
            stage_output={
                "itemsInScope": len(compact_context.get("equipmentItems", [])),
                "originCountries": compact_context.get("originCountries"),
                "projectCountries": compact_context.get("projectCountries"),
                "originPorts": compact_context.get("originPorts"),
                "destinationPorts": compact_context.get("destinationPorts"),
                "logisticsSearchQuery": logistics_query,
            },
            metadata={
                "component": "route_risk_analyst_agent",
                "context_source": "ScheduleAnalyzerAgent",
            },
        )

        bright_data_result = self.bright_data_plugin.search(
            query=logistics_query,
            num_results=10,
            country=localization["country"],
            language=localization["language"],
            location=localization["location"],
            search_engine="google",
            audit_plugin=self.audit_plugin,
            audit_agent_name=self.agent_name,
            audit_metadata={
                "component_owner": self.agent_name,
                "stage_group": "evidence_search",
                "query_source": "searchQuery.logistics",
                "localization_source": localization.get("source"),
                "current_run_date_utc": current_run_date,
            },
        )

        source_filter_result = self.source_filter_plugin.filter_sources(
            bright_data_result=bright_data_result,
            max_trusted=8,
            max_usable=8,
            audit_plugin=self.audit_plugin,
            audit_agent_name=self.agent_name,
            audit_metadata={
                "component_owner": self.agent_name,
                "stage_group": "source_filtering",
                "current_run_date_utc": current_run_date,
            },
        )

        evidence_pack = source_filter_result.get("evidencePack", [])

        self.audit_plugin.log(
            stage="evidence_pack_preparation",
            thought_content="Prepared filtered evidence pack for LLM route and logistics exposure assessment.",
            stage_output={
                "currentRunDateUtc": current_run_date,
                "brightDataSuccess": bright_data_result.get("success"),
                "brightDataResultCount": bright_data_result.get("resultCount"),
                "sourceFilterSummary": source_filter_result.get("summary"),
                "evidencePackCount": len(evidence_pack),
                "freshnessRule": (
                    "Source freshness must be judged relative to the current run date, "
                    "not planned need dates or forecast arrival dates."
                ),
            },
            metadata={
                "component": "route_risk_analyst_agent",
                "evidence_sources": [
                    item.get("sourceDomain") for item in evidence_pack[:8]
                ],
            },
        )

        result = self._call_llm_route_assessment(
            compact_context=compact_context,
            bright_data_result=bright_data_result,
            source_filter_result=source_filter_result,
            localization=localization,
            current_run_date=current_run_date,
        )

        result = self._apply_route_output_guardrails(
            result=result,
            current_run_date=current_run_date,
        )

        if result.get("agent") != self.agent_name:
            result["agent"] = self.agent_name

        self.audit_plugin.log(
            stage="route_exposure_assessment",
            thought_content="LLM completed route and logistics exposure assessment using schedule context and filtered evidence.",
            stage_output={
                "routeExposureLevel": result.get("routeExposureLevel"),
                "evidenceUsedCount": len(result.get("evidenceUsed", [])),
                "affectedItemsCount": len(result.get("affectedItems", [])),
                "keyFindingsCount": len(result.get("keyFindings", [])),
                "recommendedActionsCount": len(result.get("recommendedActions", [])),
                "confidence": result.get("confidence"),
            },
            metadata={
                "component": "route_risk_analyst_agent",
                "uses_filtered_evidence": True,
                "current_run_date_utc": current_run_date,
                "deterministic_guardrail_applied": True,
            },
        )

        self.audit_plugin.log(
            stage="final_output",
            thought_content="Prepared final route and logistics exposure output.",
            stage_output={
                "hasRouteExposureSummary": bool(result.get("routeExposureSummary")),
                "routeExposureLevel": result.get("routeExposureLevel"),
                "limitations": result.get("limitations"),
            },
            agent_output={
                "routeExposureSummary": result.get("routeExposureSummary"),
            },
        )

        result["brightDataSearch"] = {
            "success": bright_data_result.get("success"),
            "query": bright_data_result.get("query"),
            "targetUrl": bright_data_result.get("targetUrl"),
            "country": bright_data_result.get("country"),
            "language": bright_data_result.get("language"),
            "location": bright_data_result.get("location"),
            "localizationSource": localization.get("source"),
            "matchedEquipmentCode": localization.get("matchedEquipmentCode"),
            "resultCount": bright_data_result.get("resultCount"),
            "topSources": BrightDataSearchPlugin.extract_top_sources(
                bright_data_result
            ),
        }

        result["sourceQuality"] = {
            "summary": source_filter_result.get("summary"),
            "trustedSources": source_filter_result.get("trustedSources", []),
            "usableSources": source_filter_result.get("usableSources", []),
            "lowerQualitySources": source_filter_result.get(
                "lowerQualitySources",
                [],
            ),
            "discardedSources": source_filter_result.get("discardedSources", []),
        }

        result["auditLogs"] = self.audit_plugin.get_logs()
        result["auditContext"] = self.audit_plugin.get_context()

        return result

    def _get_logistics_search_query(self, schedule_result: Dict[str, Any]) -> str:
        search_query = schedule_result.get("searchQuery", {})
        logistics_query = search_query.get("logistics")

        if logistics_query:
            return str(logistics_query)

        return "Shipping route logistics port congestion current delays high-exposure supply chain shipments"

    def _build_compact_context(self, schedule_result: Dict[str, Any]) -> Dict[str, Any]:
        equipment_items = schedule_result.get("equipmentItems", [])

        high_exposure_items = [
            self._clean_item_for_route(item)
            for item in equipment_items
            if item.get("scheduleRiskLevel") == "High"
        ]

        return {
            "summary": schedule_result.get("summary"),
            "originCountries": schedule_result.get("originCountries"),
            "projectCountries": schedule_result.get("projectCountries"),
            "originPorts": schedule_result.get("originPorts"),
            "destinationPorts": schedule_result.get("destinationPorts"),
            "logisticsSearchQuery": self._get_logistics_search_query(schedule_result),
            "equipmentItems": high_exposure_items,
            "analysisNote": (
                "Schedule Exposure % is a delay-pressure index, not a probability. "
                "Values can exceed 100% when forecast delay is larger than time "
                "remaining before planned need date."
            ),
        }

    def _clean_item_for_route(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "equipmentCode": item.get("equipmentCode"),
            "equipmentName": item.get("equipmentName"),
            "projectName": item.get("projectName"),
            "sourceCountry": item.get("originCountry"),
            "destinationCountry": item.get("projectCountry"),
            "sourcePort": item.get("originPort"),
            "destinationPort": item.get("destinationPort"),
            "plannedNeedDate": item.get("baselineDueDate"),
            "forecastArrival": item.get("latestExpectedDeliveryDate"),
            "delayDays": item.get("delayDays"),
            "daysUntilDue": item.get("daysUntilDue"),
            "scheduleExposurePercentage": item.get("scheduleRiskPercentage"),
            "statusBand": item.get("scheduleRiskLevel"),
            "currentMilestone": item.get("currentMilestone"),
            "scheduleReason": item.get("riskReason"),
            "recommendedScheduleAction": item.get("recommendedAction"),
        }

    def _infer_search_localization(
        self,
        compact_context: Dict[str, Any],
        logistics_query: str,
    ) -> Dict[str, str]:
        query = str(logistics_query or "").lower()
        items = compact_context.get("equipmentItems", [])

        matched_item, score = self._find_best_query_matched_item(
            query=query,
            items=items,
        )

        if matched_item and score > 0:
            destination_country = matched_item.get("destinationCountry") or ""
            country_code = self.COUNTRY_TO_GL.get(destination_country, "us")

            return {
                "country": country_code,
                "language": settings.brightdata_default_language or "en",
                "location": destination_country,
                "source": "matched_schedule_item_from_search_query",
                "matchedEquipmentCode": str(matched_item.get("equipmentCode") or ""),
            }

        destination_country_from_query = self._extract_destination_country_from_query(
            query
        )

        if destination_country_from_query:
            return self._build_localization_from_country(
                country_name=destination_country_from_query,
                source="destination_country_detected_in_search_query",
                matched_equipment_code="",
            )

        any_country_from_query = self._extract_any_country_from_query(query)

        if any_country_from_query:
            return self._build_localization_from_country(
                country_name=any_country_from_query,
                source="country_detected_in_search_query",
                matched_equipment_code="",
            )

        if items:
            top_item = items[0]
            destination_country = top_item.get("destinationCountry") or ""
            return self._build_localization_from_country(
                country_name=destination_country,
                source="fallback_first_high_exposure_item",
                matched_equipment_code=str(top_item.get("equipmentCode") or ""),
            )

        return {
            "country": settings.brightdata_default_country or "us",
            "language": settings.brightdata_default_language or "en",
            "location": settings.brightdata_default_location or "",
            "source": "settings_default",
            "matchedEquipmentCode": "",
        }

    def _find_best_query_matched_item(
        self,
        query: str,
        items: List[Dict[str, Any]],
    ) -> Tuple[Optional[Dict[str, Any]], int]:
        best_item: Optional[Dict[str, Any]] = None
        best_score = 0

        for item in items:
            score = self._score_item_against_query(query, item)

            if score > best_score:
                best_item = item
                best_score = score

        return best_item, best_score

    def _score_item_against_query(
        self,
        query: str,
        item: Dict[str, Any],
    ) -> int:
        score = 0

        equipment_code = str(item.get("equipmentCode") or "").lower()
        equipment_name = str(item.get("equipmentName") or "").lower()
        source_country = str(item.get("sourceCountry") or "").lower()
        destination_country = str(item.get("destinationCountry") or "").lower()
        source_port = str(item.get("sourcePort") or "").lower()
        destination_port = str(item.get("destinationPort") or "").lower()

        if equipment_code and equipment_code in query:
            score += 8

        for code_part in re.split(r"[-_\s]+", equipment_code):
            if len(code_part) >= 3 and code_part in query:
                score += 3

        for token in self._important_tokens(equipment_name):
            if token in query:
                score += 2

        if source_country and source_country in query:
            score += 4

        if destination_country and destination_country in query:
            score += 5

        if source_port and source_port in query:
            score += 7

        if destination_port and destination_port in query:
            score += 7

        route_country_phrase = f"{source_country} to {destination_country}".strip()
        if source_country and destination_country and route_country_phrase in query:
            score += 5

        route_port_phrase = f"{source_port} to {destination_port}".strip()
        if source_port and destination_port and route_port_phrase in query:
            score += 8

        source_port_simple = source_port.replace("port of ", "").strip()
        destination_port_simple = destination_port.replace("port of ", "").strip()

        if source_port_simple and source_port_simple in query:
            score += 5

        if destination_port_simple and destination_port_simple in query:
            score += 5

        return score

    def _important_tokens(self, text: str) -> List[str]:
        stopwords = {
            "the",
            "and",
            "for",
            "with",
            "system",
            "package",
            "unit",
            "set",
            "rack",
            "cabinet",
            "module",
            "modular",
        }

        tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())

        return [
            token
            for token in tokens
            if len(token) >= 3 and token not in stopwords
        ]

    def _extract_destination_country_from_query(self, query: str) -> str:
        for country_name in self.COUNTRY_TO_GL.keys():
            country_lower = country_name.lower()

            patterns = [
                f" to {country_lower}",
                f" destination {country_lower}",
                f" arriving {country_lower}",
                f" shipments to {country_lower}",
                f" shipping to {country_lower}",
                f" route to {country_lower}",
            ]

            if any(pattern in query for pattern in patterns):
                return country_name

        return ""

    def _extract_any_country_from_query(self, query: str) -> str:
        for country_name in self.COUNTRY_TO_GL.keys():
            if country_name.lower() in query:
                return country_name

        return ""

    def _build_localization_from_country(
        self,
        country_name: str,
        source: str,
        matched_equipment_code: str,
    ) -> Dict[str, str]:
        country_code = self.COUNTRY_TO_GL.get(country_name, "us")

        return {
            "country": country_code,
            "language": settings.brightdata_default_language or "en",
            "location": country_name,
            "source": source,
            "matchedEquipmentCode": matched_equipment_code,
        }

    def _call_llm_route_assessment(
        self,
        compact_context: Dict[str, Any],
        bright_data_result: Dict[str, Any],
        source_filter_result: Dict[str, Any],
        localization: Dict[str, str],
        current_run_date: str,
    ) -> Dict[str, Any]:
        evidence_pack = source_filter_result.get("evidencePack", [])

        prompt = f"""
You are {self.agent_name}, the route and logistics exposure analyst for SupplyPulse V2.

Current run date:
{current_run_date} UTC

Schedule context:
{json.dumps(compact_context, indent=2, default=str)}

Bright Data search metadata:
{json.dumps(bright_data_result.get("requestMetadata", {}), indent=2, default=str)}

Source filter summary:
{json.dumps(source_filter_result.get("summary", {}), indent=2, default=str)}

Filtered evidence pack:
{json.dumps(evidence_pack, indent=2, default=str)}

Search localization:
{json.dumps(localization, indent=2, default=str)}

Your task:
1. Review the high-exposure supply items.
2. Review only the filtered evidence pack as external evidence.
3. Assess route, port, carrier, congestion, maritime disruption, customs-processing delay, weather disruption, and logistics exposure that may affect source ports, destination ports, or route lanes.
4. Connect evidence to affected equipment items where reasonable.
5. Produce practical recommended actions for logistics, procurement, project delivery, and supplier teams.

Important accuracy rules:
- Use only the provided Schedule context and Filtered evidence pack.
- Do not invent port congestion, shipping disruption, route closure, or delay evidence not present in the evidence pack.
- Do not treat lower-quality sources as confirmed evidence unless they are only used as weak signals.
- Do not change equipment codes.
- Do not change schedule exposure numbers.
- Do not change delay/gain days.
- Do not change status bands.
- affectedItems should include only equipment items with direct or reasonably supported route/logistics exposure from the evidence pack.
- Do not include items in affectedItems only because their status band is High.
- If evidence is weak, indirect, stale, historical, or generic, say so in limitations.

Source freshness rules:
- Judge source freshness relative to the Current run date only.
- Do not judge source freshness relative to planned need dates, forecast arrival dates, shipment dates, baseline due dates, or project dates.
- Before writing the final JSON, classify every evidence source into exactly one of these labels:
  1. current/live
  2. recent
  3. historical/stale
  4. future-dated/inconsistent
- Use "future-dated" only when the evidence source date is AFTER the Current run date.
- If the Current run date is 2026 and a source is dated 2024, the source is historical/stale, never future-dated.
- If the Current run date is 2026 and a source is dated July 2024, the source is historical/stale, never future-dated.
- If the evidence says "19 Jul 2024" and the Current run date is May 30, 2026, call it historical/stale, not future-dated.
- Never write the phrase "historical and future-dated reports" unless the evidence pack truly contains at least one historical source AND at least one source dated after the Current run date.
- Never call a 2024 source future-dated when the Current run date is in 2026.
- Never say "future relative to planned need dates."
- Never say "future-dated relative to planned need date."
- Never say "future-dated relative to forecast arrival."
- Never say "source date 2024 is future-dated relative to current run date 2026."
- For live-status pages, port congestion dashboards, or pages described as real-time/current, you may treat the retrieved evidence as current to the run date.
- For older articles, describe them as "historical context", "historical evidence", or "potentially stale context".
- If exact vessel-level wait times are unavailable, say that vessel-specific confirmation is unavailable.

Mandatory source-date examples:
- Current run date = 2026-05-30, source date = 2024-07-19 → historical/stale.
- Current run date = 2026-05-30, source date = Jan/Feb 2026 → recent or historical context depending on wording.
- Current run date = 2026-05-30, source says live/current/real-time → current/live.
- Current run date = 2026-05-30, source date = 2027 → future-dated/inconsistent.

Forbidden wording:
- "Historical and future-dated reports"
- "future-dated reports" unless a source date is after the Current run date
- "2024 is future-dated relative to 2026"
- "19 Jul 2024 is future-dated relative to May 30, 2026"

Required rewrite behavior:
- If you are about to write "future-dated" for a source dated before the Current run date, rewrite it as "historical" or "potentially stale".
- If a source is dated July 2024 and the Current run date is May 2026, write: "This source is historical and should be used only as context, not as confirmed current live evidence."

SupplyPulse terminology rules:
- Use "route / logistics exposure" where natural.
- Use "schedule exposure", not "risk probability".
- Use "status band" when referring to High / Medium / Low / On Track labels.
- Schedule Exposure % is a delay-pressure index, not a probability.
- Values above 100% are valid when delay is larger than remaining time before planned need date.
- Avoid saying "high probability of further delays"; say "high route / logistics exposure" or "elevated delay pressure" instead.
- Avoid saying "risk of weather-related delays"; say "weather-related delay exposure" instead.
- Avoid saying "increasing the likelihood of delays"; say "increasing route / logistics delay exposure" instead.

Output requirements:
- evidenceUsed must only include sources from the filtered evidence pack.
- affectedItems must only include equipment items from Schedule context.
- logisticsSearchQuery must equal the provided logisticsSearchQuery.
- searchLocalization must equal the provided localization.
- Return only valid JSON matching the schema.
- Do not include markdown outside JSON.
- Do not wrap JSON in triple backticks.
"""

        response = self.client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
                response_json_schema=self.ROUTE_RESPONSE_JSON_SCHEMA,
            ),
        )

        return json.loads(response.text.strip())

    def _apply_route_output_guardrails(
        self,
        result: Dict[str, Any],
        current_run_date: str,
    ) -> Dict[str, Any]:
        """
        Deterministic guardrail after LLM output.

        Purpose:
        - Prevent wrong freshness wording such as:
          "future-dated July 2024 relative to May 2026"
        - Keep route wording aligned with SupplyPulse terminology.
        - Clean nested strings in summary, evidence, findings, actions, limitations.
        """
        guarded_result = self._clean_route_guardrail_value(
            value=result,
            current_run_date=current_run_date,
        )

        if not isinstance(guarded_result, dict):
            return result

        return guarded_result

    def _clean_route_guardrail_value(
        self,
        value: Any,
        current_run_date: str,
    ) -> Any:
        if isinstance(value, str):
            return self._clean_route_guardrail_text(
                text=value,
                current_run_date=current_run_date,
            )

        if isinstance(value, list):
            return [
                self._clean_route_guardrail_value(
                    value=item,
                    current_run_date=current_run_date,
                )
                for item in value
            ]

        if isinstance(value, dict):
            return {
                key: self._clean_route_guardrail_value(
                    value=item,
                    current_run_date=current_run_date,
                )
                for key, item in value.items()
            }

        return value

    def _clean_route_guardrail_text(
        self,
        text: str,
        current_run_date: str,
    ) -> str:
        current_year = self._extract_year(current_run_date)

        def replace_future_dated_phrase(match: re.Match) -> str:
            source_date_label = match.group(1)
            source_year = self._extract_year(source_date_label)
            run_date_label = match.group(3)

            if source_year and current_year and source_year < current_year:
                return (
                    f"historical ({source_date_label}) relative to the current "
                    f"run date ({run_date_label})"
                )

            if source_year and current_year and source_year > current_year:
                return (
                    f"future-dated ({source_date_label}) relative to the current "
                    f"run date ({run_date_label})"
                )

            return (
                f"date-sensitive ({source_date_label}) relative to the current "
                f"run date ({run_date_label})"
            )

        cleaned = re.sub(
            pattern=(
                r"future-dated\s*\(([^)]*?(\d{4})[^)]*)\)\s*"
                r"relative to the current run date\s*\(([^)]*)\)"
            ),
            repl=replace_future_dated_phrase,
            string=text,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            pattern=(
                r"future-dated\s+([^.,;]*?\b(20\d{2}|19\d{2})\b[^.,;]*)\s+"
                r"relative to the current run date"
            ),
            repl=lambda match: self._replace_unparenthesized_future_phrase(
                match=match,
                current_year=current_year,
            ),
            string=cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            pattern=r"\bhigh probability of further delays\b",
            repl="high route / logistics exposure",
            string=cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            pattern=r"\bhigh likelihood of further schedule delays\b",
            repl="elevated delay pressure",
            string=cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            pattern=r"\brisk of weather-related delays\b",
            repl="weather-related delay exposure",
            string=cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            pattern=r"\brisk of further delays\b",
            repl="route / logistics delay exposure",
            string=cleaned,
            flags=re.IGNORECASE,
        )

        return cleaned

    def _replace_unparenthesized_future_phrase(
        self,
        match: re.Match,
        current_year: Optional[int],
    ) -> str:
        source_date_label = match.group(1).strip()
        source_year = self._extract_year(source_date_label)

        if source_year and current_year and source_year < current_year:
            return f"historical {source_date_label} relative to the current run date"

        if source_year and current_year and source_year > current_year:
            return f"future-dated {source_date_label} relative to the current run date"

        return f"date-sensitive {source_date_label} relative to the current run date"

    @staticmethod
    def _extract_year(value: Any) -> Optional[int]:
        match = re.search(r"\b(20\d{2}|19\d{2})\b", str(value or ""))

        if not match:
            return None

        return int(match.group(1))

    @staticmethod
    def _current_utc_date() -> str:
        return datetime.now(timezone.utc).date().isoformat()