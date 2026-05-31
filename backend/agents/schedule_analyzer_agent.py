import json
import os
from datetime import date
from typing import Any, Dict, List, Optional

import pandas as pd
from google import genai
from google.genai import types

from config.settings import settings
from plugins.audit_logging_plugin import AuditLoggingPlugin
from plugins.schedule_data_plugin import ScheduleDataPlugin


SCHEDULE_ANALYZER_AGENT = "SCHEDULE_ANALYZER_AGENT"


class ScheduleAnalyzerAgent:
    """
    LLM-first Schedule Analyzer Agent.

    Responsibilities:
    - Load and validate schedule data using ScheduleDataPlugin.
    - Ask the LLM to calculate schedule exposure.
    - Ask the LLM to assign status bands.
    - Ask the LLM to create reasons and recommendations.
    - Ask the LLM to create downstream intelligence queries.
    - Log all major steps using AuditLoggingPlugin.
    """

    SCHEDULER_RESPONSE_JSON_SCHEMA = {
        "type": "object",
        "properties": {
            "agent": {"type": "string"},
            "summary": {
                "type": "object",
                "properties": {
                    "totalItems": {"type": "integer"},
                    "highRiskItems": {"type": "integer"},
                    "mediumRiskItems": {"type": "integer"},
                    "lowRiskItems": {"type": "integer"},
                    "onTrackItems": {"type": "integer"},
                },
                "required": [
                    "totalItems",
                    "highRiskItems",
                    "mediumRiskItems",
                    "lowRiskItems",
                    "onTrackItems",
                ],
            },
            "projectInfo": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "projectName": {"type": "string"},
                        "projectCountry": {"type": "string"},
                    },
                    "required": ["projectName", "projectCountry"],
                },
            },
            "originCountries": {
                "type": "array",
                "items": {"type": "string"},
            },
            "projectCountries": {
                "type": "array",
                "items": {"type": "string"},
            },
            "originPorts": {
                "type": "array",
                "items": {"type": "string"},
            },
            "destinationPorts": {
                "type": "array",
                "items": {"type": "string"},
            },
            "equipmentItems": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "itemId": {"type": "string"},
                        "projectId": {"type": "string"},
                        "projectName": {"type": "string"},
                        "projectCountry": {"type": "string"},
                        "equipmentCode": {"type": "string"},
                        "equipmentName": {"type": "string"},
                        "equipmentCategory": {"type": "string"},
                        "supplierName": {"type": "string"},
                        "originCountry": {"type": "string"},
                        "originPort": {"type": "string"},
                        "destinationPort": {"type": "string"},
                        "baselineDueDate": {"type": "string"},
                        "latestExpectedDeliveryDate": {"type": "string"},
                        "delayDays": {"type": "integer"},
                        "daysUntilDue": {"type": "integer"},
                        "scheduleRiskPercentage": {"type": "number"},
                        "scheduleRiskLevel": {
                            "type": "string",
                            "enum": ["High", "Medium", "Low", "On Track"],
                        },
                        "scheduleRiskReason": {"type": "string"},
                        "scheduleRecommendation": {"type": "string"},
                    },
                    "required": [
                        "itemId",
                        "projectId",
                        "projectName",
                        "projectCountry",
                        "equipmentCode",
                        "equipmentName",
                        "equipmentCategory",
                        "supplierName",
                        "originCountry",
                        "originPort",
                        "destinationPort",
                        "baselineDueDate",
                        "latestExpectedDeliveryDate",
                        "delayDays",
                        "daysUntilDue",
                        "scheduleRiskPercentage",
                        "scheduleRiskLevel",
                        "scheduleRiskReason",
                        "scheduleRecommendation",
                    ],
                },
            },
            "searchQuery": {
                "type": "object",
                "properties": {
                    "political": {"type": "string"},
                    "tariff": {"type": "string"},
                    "logistics": {"type": "string"},
                },
                "required": ["political", "tariff", "logistics"],
            },
        },
        "required": [
            "agent",
            "summary",
            "projectInfo",
            "originCountries",
            "projectCountries",
            "originPorts",
            "destinationPorts",
            "equipmentItems",
            "searchQuery",
        ],
    }

    def __init__(self, audit_context: Optional[Dict[str, Any]] = None) -> None:
        self.agent_name = SCHEDULE_ANALYZER_AGENT
        self.data_plugin = ScheduleDataPlugin()

        context = audit_context or AuditLoggingPlugin.create_context(
            model_name=settings.gemini_model
        )

        self.audit_plugin = AuditLoggingPlugin(
            default_agent_name=self.agent_name,
            **context,
        )

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials

        self.client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )

    def run_from_csv(self, csv_path: str) -> Dict[str, Any]:
        raw_df = self.data_plugin.load_csv(csv_path)
        return self.run(raw_df)

    def run(self, raw_df: pd.DataFrame) -> Dict[str, Any]:
        self.audit_plugin.clear()

        self.audit_plugin.log(
            stage="analysis_start",
            thought_content="Started LLM-first schedule exposure analysis.",
            stage_output={
                "input_rows": int(len(raw_df)),
                "input_columns": list(raw_df.columns),
            },
            metadata={
                "component": "schedule_analyzer",
                "input_type": "dataframe",
            },
        )

        prepared_df = self.data_plugin.validate_and_prepare_data(raw_df)
        data_profile = self.data_plugin.get_data_profile(prepared_df)

        self.audit_plugin.log(
            stage="data_review",
            thought_content="Schedule data was validated before LLM analysis.",
            stage_output=data_profile,
            metadata={
                "plugin_used": "ScheduleDataPlugin",
            },
        )

        llm_rows = self._prepare_rows_for_llm(prepared_df)

        self.audit_plugin.log(
            stage="llm_schedule_analysis_request",
            thought_content="Sending schedule rows to the LLM for schedule exposure calculation and status band assignment.",
            stage_output={
                "rows_sent_to_llm": len(llm_rows),
                "today": date.today().isoformat(),
            },
            metadata={
                "model": settings.gemini_model,
                "temperature": 0,
            },
        )

        result = self._call_llm_scheduler(llm_rows)

        equipment_items = result.get("equipmentItems", [])
        summary = result.get("summary", {})
        search_query = result.get("searchQuery", {})

        calculation_sample = [
            {
                "itemId": item.get("itemId"),
                "equipmentCode": item.get("equipmentCode"),
                "delayDays": item.get("delayDays"),
                "daysUntilDue": item.get("daysUntilDue"),
                "scheduleRiskPercentage": item.get("scheduleRiskPercentage"),
                "scheduleRiskLevel": item.get("scheduleRiskLevel"),
            }
            for item in equipment_items[:5]
        ]

        self.audit_plugin.log(
            stage="risk_calculation",
            thought_content="LLM calculated delivery delay, days until planned need date, and schedule exposure percentage.",
            stage_output={
                "formula": "scheduleRiskPercentage = delayDays / daysUntilDue * 100, with special handling for on-track and overdue items",
                "sample_calculations": calculation_sample,
            },
            metadata={
                "calculation_owner": "LLM",
                "rows_calculated": len(equipment_items),
            },
        )

        self.audit_plugin.log(
            stage="categorization",
            thought_content="LLM assigned each item to a schedule exposure status band.",
            stage_output={
                "summary": summary,
                "status_bands": ["High", "Medium", "Low", "On Track"],
            },
            metadata={
                "high_items": summary.get("highRiskItems"),
                "medium_items": summary.get("mediumRiskItems"),
                "low_items": summary.get("lowRiskItems"),
                "on_track_items": summary.get("onTrackItems"),
            },
        )

        self.audit_plugin.log(
            stage="recommendations",
            thought_content="LLM generated item-level recommendations and downstream intelligence queries.",
            stage_output={
                "searchQuery": search_query,
                "sample_recommendations": [
                    {
                        "itemId": item.get("itemId"),
                        "recommendation": item.get("scheduleRecommendation"),
                    }
                    for item in equipment_items[:3]
                ],
            },
            metadata={
                "downstream_query_keys": list(search_query.keys()),
            },
        )

        self.audit_plugin.log(
            stage="final_output",
            thought_content="Schedule exposure analysis output is ready for report builder and downstream risk agents.",
            stage_output={
                "has_summary": True,
                "has_equipment_items": True,
                "has_search_queries": True,
            },
            agent_output={
                "summary": summary,
                "searchQuery": search_query,
            },
        )

        result["auditLogs"] = self.audit_plugin.get_logs()
        result["auditContext"] = self.audit_plugin.get_context()

        return result

    def _prepare_rows_for_llm(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        safe_df = df.copy()

        date_columns = [
            "baseline_due_date",
            "latest_expected_delivery_date",
            "actual_delivery_date",
        ]

        for col in date_columns:
            if col in safe_df.columns:
                safe_df[col] = safe_df[col].apply(
                    lambda value: None if pd.isna(value) else str(value.date())
                )

        safe_df = safe_df.where(pd.notnull(safe_df), None)

        return safe_df.to_dict("records")

    def _call_llm_scheduler(self, schedule_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        today = date.today().isoformat()

        prompt = f"""
You are {self.agent_name}, a Schedule Analyzer Agent for SupplyPulse V2.

Your task:
1. Read the schedule/equipment rows.
2. Calculate delivery delay for each item.
3. Calculate schedule exposure percentage for each item.
4. Assign status band for each item.
5. Create clear exposure reasons.
6. Create practical recommendations.
7. Create downstream search queries for political, tariff, and logistics risk agents.

Today's date:
{today}

Raw schedule rows:
{json.dumps(schedule_rows, indent=2, default=str)}

Use this exact calculation logic:

1. delayDays:
delayDays = latest_expected_delivery_date - baseline_due_date

2. daysUntilDue:
daysUntilDue = baseline_due_date - today's date

3. scheduleRiskPercentage:
If delayDays <= 0:
    scheduleRiskPercentage = 0

If delayDays > 0 and daysUntilDue <= 0:
    scheduleRiskPercentage = 100

If delayDays > 0 and daysUntilDue > 0:
    scheduleRiskPercentage = delayDays / daysUntilDue * 100

Round scheduleRiskPercentage to 2 decimals.

4. scheduleRiskLevel:
If delayDays <= 0:
    scheduleRiskLevel = "On Track"
Else if scheduleRiskPercentage < 5:
    scheduleRiskLevel = "Low"
Else if scheduleRiskPercentage < 15:
    scheduleRiskLevel = "Medium"
Else:
    scheduleRiskLevel = "High"

5. summary:
Count total, High, Medium, Low, and On Track items.

6. searchQuery:
Create three downstream search queries using this exact structure:

"searchQuery": {{
  "political": "Political risks manufacturing exports [MANUFACTURING_COUNTRY] to [PROJECT_COUNTRY] [EQUIPMENT_TYPE] current issues",
  "tariff": "[MANUFACTURING_COUNTRY] [PROJECT_COUNTRY] tariffs [EQUIPMENT_TYPE] trade agreements customs duties",
  "logistics": "[SHIPPING_PORT] to [RECEIVING_PORT] shipping route issues logistics current delays"
}}

Rules for searchQuery:
- Replace [MANUFACTURING_COUNTRY] with the most relevant origin_country from the schedule rows.
- Replace [PROJECT_COUNTRY] with the most relevant project_country from the schedule rows.
- Replace [EQUIPMENT_TYPE] with the most relevant equipment_category or equipment_name.
- Replace [SHIPPING_PORT] with the most relevant origin_port.
- Replace [RECEIVING_PORT] with the most relevant destination_port.
- Prefer the highest-risk item when choosing the countries, equipment type, and ports.
- Do not return only country lists.
- Do not return only port lists.
- Each searchQuery value must be a complete search-ready sentence.

Return only valid JSON matching the schema.
Do not include markdown.
Do not include explanation outside JSON.
"""

        response = self.client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
                response_json_schema=self.SCHEDULER_RESPONSE_JSON_SCHEMA,
            ),
        )

        parsed = json.loads(response.text.strip())

        if parsed.get("agent") != self.agent_name:
            parsed["agent"] = self.agent_name

        return parsed