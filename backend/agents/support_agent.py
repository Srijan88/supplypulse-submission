import os
from typing import Any, Dict, Optional

from google import genai
from google.genai import types

from config.settings import settings
from plugins.audit_logging_plugin import AuditLoggingPlugin


SUPPORT_AGENT = "SUPPORT_AGENT"


class SupportAgent:
    """
    Support Agent for general help, greetings, and product explanation.

    Responsibilities:
    - Answer casual/help/product questions.
    - Explain what SupplyPulse V2 can do.
    - Produce upgraded audit logs.
    """

    def __init__(self, audit_context: Optional[Dict[str, Any]] = None) -> None:
        self.agent_name = SUPPORT_AGENT

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

    def run(self, user_question: str) -> Dict[str, Any]:
        self.audit_plugin.clear()

        self.audit_plugin.log(
            stage="analysis_start",
            thought_content="Started support response flow for a general user query.",
            stage_output={
                "user_question": user_question,
            },
            metadata={
                "component": "support_agent",
                "query_type": "general_support",
            },
        )

        self.audit_plugin.log(
            stage="query_understanding",
            thought_content="Classified the query as suitable for support response rather than risk analysis.",
            stage_output={
                "handled_by": self.agent_name,
                "requires_schedule_data": False,
                "requires_external_risk_agents": False,
            },
        )

        prompt = f"""
You are {self.agent_name} for SupplyPulse V2.

SupplyPulse V2 is a supply-chain risk intelligence system.

Answer the user briefly and clearly.

The system can help with:
- schedule exposure analysis
- delivery delay analysis
- geopolitical risk analysis through GEO_RISK_ANALYST_AGENT
- tariff/customs/trade risk analysis through TRADE_RISK_ANALYST_AGENT
- logistics/port/route risk analysis through ROUTE_RISK_ANALYST_AGENT
- full delivery exposure reporting through RISK_REPORT_BUILDER_AGENT

User question:
{user_question}

Rules:
- Keep the answer short and practical.
- Use SupplyPulse V2 terminology.
- Do not mention internal code unless useful.
"""

        self.audit_plugin.log(
            stage="response_generation_request",
            thought_content="Sending support prompt to the LLM.",
            stage_output={
                "prompt_type": "support_response",
                "model": settings.gemini_model,
            },
            metadata={
                "temperature": 0.3,
            },
        )

        response = self.client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
            ),
        )

        answer = response.text.strip()

        self.audit_plugin.log(
            stage="final_output",
            thought_content="Prepared final support response.",
            stage_output={
                "response_length_chars": len(answer),
            },
            agent_output={
                "response": answer,
            },
        )

        return {
            "agent": self.agent_name,
            "response": answer,
            "auditLogs": self.audit_plugin.get_logs(),
            "auditContext": self.audit_plugin.get_context(),
        }