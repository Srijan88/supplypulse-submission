import json
import os
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from config.settings import settings
from plugins.audit_logging_plugin import AuditLoggingPlugin


SCHEDULE_ANALYZER_AGENT = "SCHEDULE_ANALYZER_AGENT"
SUPPORT_AGENT = "SUPPORT_AGENT"
GEO_RISK_ANALYST_AGENT = "GEO_RISK_ANALYST_AGENT"
TRADE_RISK_ANALYST_AGENT = "TRADE_RISK_ANALYST_AGENT"
ROUTE_RISK_ANALYST_AGENT = "ROUTE_RISK_ANALYST_AGENT"
RISK_REPORT_BUILDER_AGENT = "RISK_REPORT_BUILDER_AGENT"
ALL_RISK_AGENTS = "ALL_RISK_AGENTS"


class RouterAgent:
    """
    LLM Router Agent.

    Responsibilities:
    - Read the user question.
    - Decide the first agent.
    - Decide the user intent.
    - Decide which agent should run after Scheduler.
    - Produce audit logs for routing decisions.
    """

    ROUTER_RESPONSE_JSON_SCHEMA = {
        "type": "object",
        "properties": {
            "first_agent": {
                "type": "string",
                "enum": [SCHEDULE_ANALYZER_AGENT, SUPPORT_AGENT],
            },
            "intent": {
                "type": "string",
                "enum": [
                    "schedule_risk",
                    "geo_risk",
                    "trade_risk",
                    "route_risk",
                    "comprehensive_risk",
                    "general_help",
                    "casual_chat",
                    "unclear",
                ],
            },
            "next_agent_after_scheduler": {
                "anyOf": [
                    {
                        "type": "string",
                        "enum": [
                            RISK_REPORT_BUILDER_AGENT,
                            GEO_RISK_ANALYST_AGENT,
                            TRADE_RISK_ANALYST_AGENT,
                            ROUTE_RISK_ANALYST_AGENT,
                            ALL_RISK_AGENTS,
                        ],
                    },
                    {"type": "null"},
                ],
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
            },
            "reason": {
                "type": "string",
            },
        },
        "required": [
            "first_agent",
            "intent",
            "next_agent_after_scheduler",
            "confidence",
            "reason",
        ],
    }

    ROUTER_SYSTEM_PROMPT = """
You are a Router Agent for SupplyPulse V2, a supply-chain risk intelligence system.

Your task is to classify the user's message and decide which FIRST agent should run.

Available first agents:

1. SCHEDULE_ANALYZER_AGENT
Use this when the user asks about:
- schedule risk
- delay
- delivery status
- shipment status
- equipment status
- variance
- supplier risk
- project risk
- political risk
- geopolitical risk
- tariff risk
- customs risk
- trade risk
- duties
- sanctions
- logistics risk
- shipping risk
- port risk
- route risk
- transportation risk
- complete risk analysis
- all risks
- overall risk

Reason:
All real supply-chain risk analysis must first read schedule/equipment data.

2. SUPPORT_AGENT
Use this when the user asks:
- greeting
- casual chat
- product explanation
- what can you do
- general help
- unclear non-risk question

Routing rules:
- Schedule/delay/delivery/equipment questions:
  first_agent = SCHEDULE_ANALYZER_AGENT
  intent = schedule_risk
  next_agent_after_scheduler = RISK_REPORT_BUILDER_AGENT

- Political/geopolitical/country instability questions:
  first_agent = SCHEDULE_ANALYZER_AGENT
  intent = geo_risk
  next_agent_after_scheduler = GEO_RISK_ANALYST_AGENT

- Tariff/trade/customs/duties/sanctions questions:
  first_agent = SCHEDULE_ANALYZER_AGENT
  intent = trade_risk
  next_agent_after_scheduler = TRADE_RISK_ANALYST_AGENT

- Logistics/shipping/port/route/transport questions:
  first_agent = SCHEDULE_ANALYZER_AGENT
  intent = route_risk
  next_agent_after_scheduler = ROUTE_RISK_ANALYST_AGENT

- Complete/all/overall risk analysis:
  first_agent = SCHEDULE_ANALYZER_AGENT
  intent = comprehensive_risk
  next_agent_after_scheduler = ALL_RISK_AGENTS

- Greeting/general help/casual chat:
  first_agent = SUPPORT_AGENT
  intent = general_help or casual_chat
  next_agent_after_scheduler = null

Important:
- If the message contains supply-chain/risk words, prefer SCHEDULE_ANALYZER_AGENT.
- If the message is only casual or product help, choose SUPPORT_AGENT.
- Return only valid JSON matching the schema.
- Do not include markdown.
"""

    def __init__(self, audit_context: Optional[Dict[str, Any]] = None) -> None:
        self.agent_name = "ROUTER_AGENT"

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

    def classify(self, user_message: str) -> Dict[str, Any]:
        self.audit_plugin.clear()

        self.audit_plugin.log(
            stage="analysis_start",
            thought_content="Started routing analysis for the user question.",
            stage_output={
                "user_message": user_message,
            },
            metadata={
                "component": "router",
                "model": settings.gemini_model,
            },
        )

        prompt = f"""
{self.ROUTER_SYSTEM_PROMPT}

User message:
{user_message}
"""

        self.audit_plugin.log(
            stage="classification_request",
            thought_content="Sending user question to LLM for routing classification.",
            stage_output={
                "prompt_type": "router_classification",
                "response_format": "json_schema",
            },
            metadata={
                "temperature": 0,
            },
        )

        response = self.client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
                response_json_schema=self.ROUTER_RESPONSE_JSON_SCHEMA,
            ),
        )

        parsed = json.loads(response.text.strip())

        self.audit_plugin.log(
            stage="classification_response",
            thought_content="LLM returned routing classification.",
            stage_output=parsed,
            metadata={
                "raw_response_received": True,
            },
        )

        validated = self._validate(parsed)
        execution_plan = self.get_execution_plan(validated)

        # Clean snapshot avoids circular reference after auditLogs are attached.
        validated_snapshot = {
            "first_agent": validated.get("first_agent"),
            "intent": validated.get("intent"),
            "next_agent_after_scheduler": validated.get("next_agent_after_scheduler"),
            "confidence": validated.get("confidence"),
            "reason": validated.get("reason"),
            "router_source": validated.get("router_source"),
        }

        self.audit_plugin.log(
            stage="final_output",
            thought_content="Final routing decision and execution plan are ready.",
            stage_output={
                "validated_router_result": validated_snapshot,
                "execution_plan": execution_plan,
            },
            agent_output={
                "first_agent": validated_snapshot.get("first_agent"),
                "intent": validated_snapshot.get("intent"),
                "next_agent_after_scheduler": validated_snapshot.get(
                    "next_agent_after_scheduler"
                ),
            },
        )

        validated["auditLogs"] = self.audit_plugin.get_logs()
        validated["auditContext"] = self.audit_plugin.get_context()

        return validated

    def _validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        valid_first_agents = {
            SCHEDULE_ANALYZER_AGENT,
            SUPPORT_AGENT,
        }

        valid_intents = {
            "schedule_risk",
            "geo_risk",
            "trade_risk",
            "route_risk",
            "comprehensive_risk",
            "general_help",
            "casual_chat",
            "unclear",
        }

        valid_next_agents = {
            RISK_REPORT_BUILDER_AGENT,
            GEO_RISK_ANALYST_AGENT,
            TRADE_RISK_ANALYST_AGENT,
            ROUTE_RISK_ANALYST_AGENT,
            ALL_RISK_AGENTS,
            None,
        }

        first_agent = result.get("first_agent")
        intent = result.get("intent")
        next_agent = result.get("next_agent_after_scheduler")
        confidence = result.get("confidence", 0)
        reason = result.get("reason", "")

        if first_agent not in valid_first_agents:
            first_agent = SUPPORT_AGENT

        if intent not in valid_intents:
            intent = "unclear"

        if next_agent not in valid_next_agents:
            next_agent = None

        try:
            confidence = float(confidence)
            confidence = max(0.0, min(confidence, 1.0))
        except Exception:
            confidence = 0.0

        return {
            "first_agent": first_agent,
            "intent": intent,
            "next_agent_after_scheduler": next_agent,
            "confidence": confidence,
            "reason": str(reason)[:160],
            "router_source": "llm",
        }

    def get_execution_plan(self, router_result: Dict[str, Any]) -> List[str]:
        first_agent = router_result.get("first_agent")
        next_agent = router_result.get("next_agent_after_scheduler")

        if first_agent == SUPPORT_AGENT:
            return [SUPPORT_AGENT]

        if next_agent == ALL_RISK_AGENTS:
            return [
                SCHEDULE_ANALYZER_AGENT,
                GEO_RISK_ANALYST_AGENT,
                TRADE_RISK_ANALYST_AGENT,
                ROUTE_RISK_ANALYST_AGENT,
                RISK_REPORT_BUILDER_AGENT,
            ]

        if next_agent in {
            GEO_RISK_ANALYST_AGENT,
            TRADE_RISK_ANALYST_AGENT,
            ROUTE_RISK_ANALYST_AGENT,
        }:
            return [
                SCHEDULE_ANALYZER_AGENT,
                next_agent,
                RISK_REPORT_BUILDER_AGENT,
            ]

        return [
            SCHEDULE_ANALYZER_AGENT,
            RISK_REPORT_BUILDER_AGENT,
        ]