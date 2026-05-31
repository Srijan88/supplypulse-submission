import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from google import genai
from google.genai import types

from config.settings import settings
from plugins.audit_logging_plugin import AuditLoggingPlugin
from plugins.bright_data_search_plugin import BrightDataSearchPlugin
from plugins.source_quality_filter_plugin import SourceQualityFilterPlugin


GEO_RISK_ANALYST_AGENT = "GEO_RISK_ANALYST_AGENT"


class GeoRiskAnalystAgent:
    """
    SupplyPulse geopolitical exposure analyst.

    Responsibilities:
    - Read Schedule Analyzer output.
    - Use searchQuery.political.
    - Run localized Bright Data SERP search.
    - Filter source quality.
    - Use LLM to assess geopolitical exposure from schedule context + evidence pack.
    - Produce SupplyPulse audit logs.
    """

    GEO_RESPONSE_JSON_SCHEMA = {
        "type": "object",
        "properties": {
            "agent": {"type": "string"},
            "geoExposureLevel": {
                "type": "string",
                "enum": ["High", "Medium", "Low", "Unknown"],
            },
            "geoExposureSummary": {"type": "string"},
            "politicalSearchQuery": {"type": "string"},
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
                        "scheduleExposurePercentage": {"type": "number"},
                        "statusBand": {"type": "string"},
                        "geoExposureReason": {"type": "string"},
                    },
                    "required": [
                        "equipmentCode",
                        "equipmentName",
                        "sourceCountry",
                        "destinationCountry",
                        "scheduleExposurePercentage",
                        "statusBand",
                        "geoExposureReason",
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
            "geoExposureLevel",
            "geoExposureSummary",
            "politicalSearchQuery",
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
        self.agent_name = GEO_RISK_ANALYST_AGENT

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

        political_query = self._get_political_search_query(schedule_result)
        compact_context = self._build_compact_context(schedule_result)

        localization = self._infer_search_localization(
            compact_context=compact_context,
            political_query=political_query,
        )

        self.audit_plugin.log(
            stage="analysis_start",
            thought_content="Started geopolitical exposure analysis from Schedule Analyzer output.",
            stage_output={
                "schedulerSummary": schedule_result.get("summary"),
                "politicalSearchQuery": political_query,
                "searchLocalization": localization,
            },
            metadata={
                "component": "geo_risk_analyst_agent",
                "input_agent": schedule_result.get("agent"),
            },
        )

        self.audit_plugin.log(
            stage="schedule_context_extraction",
            thought_content="Prepared high-exposure schedule context for geopolitical exposure review.",
            stage_output={
                "itemsInScope": len(compact_context.get("equipmentItems", [])),
                "originCountries": compact_context.get("originCountries"),
                "projectCountries": compact_context.get("projectCountries"),
                "politicalSearchQuery": political_query,
            },
            metadata={
                "component": "geo_risk_analyst_agent",
                "context_source": "ScheduleAnalyzerAgent",
            },
        )

        bright_data_result = self.bright_data_plugin.search(
            query=political_query,
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
                "query_source": "searchQuery.political",
                "localization_source": localization.get("source"),
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
            },
        )

        evidence_pack = source_filter_result.get("evidencePack", [])

        self.audit_plugin.log(
            stage="evidence_pack_preparation",
            thought_content="Prepared filtered evidence pack for LLM geopolitical exposure assessment.",
            stage_output={
                "brightDataSuccess": bright_data_result.get("success"),
                "brightDataResultCount": bright_data_result.get("resultCount"),
                "sourceFilterSummary": source_filter_result.get("summary"),
                "evidencePackCount": len(evidence_pack),
            },
            metadata={
                "component": "geo_risk_analyst_agent",
                "evidence_sources": [
                    item.get("sourceDomain") for item in evidence_pack[:8]
                ],
            },
        )

        result = self._call_llm_geo_assessment(
            compact_context=compact_context,
            bright_data_result=bright_data_result,
            source_filter_result=source_filter_result,
            localization=localization,
        )

        if result.get("agent") != self.agent_name:
            result["agent"] = self.agent_name

        self.audit_plugin.log(
            stage="geo_exposure_assessment",
            thought_content="LLM completed geopolitical exposure assessment using schedule context and filtered evidence.",
            stage_output={
                "geoExposureLevel": result.get("geoExposureLevel"),
                "evidenceUsedCount": len(result.get("evidenceUsed", [])),
                "affectedItemsCount": len(result.get("affectedItems", [])),
                "keyFindingsCount": len(result.get("keyFindings", [])),
                "recommendedActionsCount": len(result.get("recommendedActions", [])),
                "confidence": result.get("confidence"),
            },
            metadata={
                "component": "geo_risk_analyst_agent",
                "uses_filtered_evidence": True,
            },
        )

        self.audit_plugin.log(
            stage="final_output",
            thought_content="Prepared final geopolitical exposure output.",
            stage_output={
                "hasGeoExposureSummary": bool(result.get("geoExposureSummary")),
                "geoExposureLevel": result.get("geoExposureLevel"),
                "limitations": result.get("limitations"),
            },
            agent_output={
                "geoExposureSummary": result.get("geoExposureSummary"),
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
                "lowerQualitySources", []
            ),
            "discardedSources": source_filter_result.get("discardedSources", []),
        }

        result["auditLogs"] = self.audit_plugin.get_logs()
        result["auditContext"] = self.audit_plugin.get_context()

        return result

    def _get_political_search_query(self, schedule_result: Dict[str, Any]) -> str:
        search_query = schedule_result.get("searchQuery", {})
        political_query = search_query.get("political")

        if political_query:
            return str(political_query)

        return "Political and geopolitical exposure affecting high-exposure supply chain shipments"

    def _build_compact_context(self, schedule_result: Dict[str, Any]) -> Dict[str, Any]:
        equipment_items = schedule_result.get("equipmentItems", [])

        high_exposure_items = [
            self._clean_item_for_geo(item)
            for item in equipment_items
            if item.get("scheduleRiskLevel") == "High"
        ]

        return {
            "summary": schedule_result.get("summary"),
            "originCountries": schedule_result.get("originCountries"),
            "projectCountries": schedule_result.get("projectCountries"),
            "originPorts": schedule_result.get("originPorts"),
            "destinationPorts": schedule_result.get("destinationPorts"),
            "politicalSearchQuery": self._get_political_search_query(schedule_result),
            "equipmentItems": high_exposure_items,
            "analysisNote": (
                "Schedule Exposure % is a delay-pressure index, not a probability. "
                "Values can exceed 100% when forecast delay is larger than time "
                "remaining before planned need date."
            ),
        }

    def _clean_item_for_geo(self, item: Dict[str, Any]) -> Dict[str, Any]:
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
        political_query: str,
    ) -> Dict[str, str]:
        """
        Localization priority:
        1. Match searchQuery.political to the most relevant equipment item.
        2. If no item match, detect destination country from query wording.
        3. If no destination country, detect any known country in query.
        4. Fallback to first high-exposure item.
        5. Fallback to settings defaults.

        This prevents Taiwan → Singapore queries from accidentally using the first
        high-exposure row if that row belongs to a different destination.
        """

        query = str(political_query or "").lower()
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

        project_countries = compact_context.get("projectCountries", [])

        if project_countries:
            destination_country = str(project_countries[0])
            return self._build_localization_from_country(
                country_name=destination_country,
                source="fallback_first_project_country",
                matched_equipment_code="",
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

        route_phrase = f"{source_country} to {destination_country}".strip()
        if source_country and destination_country and route_phrase in query:
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
                f" destined for {country_lower}",
                f" destination {country_lower}",
                f" exports to {country_lower}",
                f" shipments to {country_lower}",
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

    def _call_llm_geo_assessment(
        self,
        compact_context: Dict[str, Any],
        bright_data_result: Dict[str, Any],
        source_filter_result: Dict[str, Any],
        localization: Dict[str, str],
    ) -> Dict[str, Any]:
        evidence_pack = source_filter_result.get("evidencePack", [])

        prompt = f"""
You are {self.agent_name}, the geopolitical exposure analyst for SupplyPulse V2.

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
3. Assess geopolitical exposure that may affect source countries, destination countries, or relevant trade lanes.
4. Connect evidence to affected equipment items where reasonable.
5. Produce practical recommended actions for supply-chain operators.

Important accuracy rules:
- Use only the provided Schedule context and Filtered evidence pack.
- Do not invent news or facts not present in the evidence pack.
- Do not treat lower-quality sources as confirmed evidence unless they are only used as weak signals.
- Do not change equipment codes.
- Do not change schedule exposure numbers.
- Do not change delay/gain days.
- Do not change status bands.
- affectedItems should include only equipment items with direct or reasonably supported geopolitical exposure from the evidence pack.
- Do not include items in affectedItems only because their schedule status band is High.
- If other high-exposure items lack specific geopolitical evidence, mention that in limitations.

SupplyPulse terminology rules:
- Use "geopolitical exposure" instead of "political risk" where natural.
- Use "schedule exposure", not "risk probability".
- Use "status band" when referring to High / Medium / Low / On Track labels.
- Schedule Exposure % is a delay-pressure index, not a probability.
- Values above 100% are valid when delay is larger than remaining time before planned need date.

Output requirements:
- evidenceUsed must only include sources from the filtered evidence pack.
- affectedItems must only include equipment items from Schedule context.
- politicalSearchQuery must equal the provided politicalSearchQuery.
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
                response_json_schema=self.GEO_RESPONSE_JSON_SCHEMA,
            ),
        )

        return json.loads(response.text.strip())