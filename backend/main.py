import json
from typing import Any, Dict, List, Optional, Set

from config.settings import settings

from plugins.audit_logging_plugin import AuditLoggingPlugin
from plugins.audit_flow_plugin import AuditFlowPlugin

from agents.router_agent import (
    RouterAgent,
    SUPPORT_AGENT,
    GEO_RISK_ANALYST_AGENT,
    TRADE_RISK_ANALYST_AGENT,
    ROUTE_RISK_ANALYST_AGENT,
    ALL_RISK_AGENTS,
)

from agents.support_agent import SupportAgent
from agents.schedule_analyzer_agent import ScheduleAnalyzerAgent
from agents.geo_risk_analyst_agent import GeoRiskAnalystAgent
from agents.trade_risk_analyst_agent import TradeRiskAnalystAgent
from agents.route_risk_analyst_agent import RouteRiskAnalystAgent
from agents.risk_report_builder_agent import RiskReportBuilderAgent


def should_run_geo_agent(next_agent_after_scheduler: Optional[str]) -> bool:
    return next_agent_after_scheduler in {
        GEO_RISK_ANALYST_AGENT,
        ALL_RISK_AGENTS,
    }


def should_run_trade_agent(next_agent_after_scheduler: Optional[str]) -> bool:
    return next_agent_after_scheduler in {
        TRADE_RISK_ANALYST_AGENT,
        ALL_RISK_AGENTS,
    }


def should_run_route_agent(next_agent_after_scheduler: Optional[str]) -> bool:
    return next_agent_after_scheduler in {
        ROUTE_RISK_ANALYST_AGENT,
        ALL_RISK_AGENTS,
    }


def build_pending_risk_agents(
    next_agent_after_scheduler: str,
    schedule_result: Dict[str, Any],
    executed_agents: Optional[Set[str]] = None,
) -> List[Dict[str, Any]]:
    search_query = schedule_result.get("searchQuery", {})
    executed_agents = executed_agents or set()

    pending_agents: List[Dict[str, Any]] = []

    def add_pending_agent(
        agent_name: str,
        uses: str,
        prepared_search_query: Optional[str],
    ) -> None:
        if agent_name in executed_agents:
            return

        pending_agents.append(
            {
                "agent": agent_name,
                "status": "not_implemented_yet",
                "uses": uses,
                "preparedSearchQuery": prepared_search_query,
            }
        )

    if next_agent_after_scheduler == GEO_RISK_ANALYST_AGENT:
        add_pending_agent(
            agent_name=GEO_RISK_ANALYST_AGENT,
            uses="searchQuery.political",
            prepared_search_query=search_query.get("political"),
        )

    elif next_agent_after_scheduler == TRADE_RISK_ANALYST_AGENT:
        add_pending_agent(
            agent_name=TRADE_RISK_ANALYST_AGENT,
            uses="searchQuery.tariff",
            prepared_search_query=search_query.get("tariff"),
        )

    elif next_agent_after_scheduler == ROUTE_RISK_ANALYST_AGENT:
        add_pending_agent(
            agent_name=ROUTE_RISK_ANALYST_AGENT,
            uses="searchQuery.logistics",
            prepared_search_query=search_query.get("logistics"),
        )

    elif next_agent_after_scheduler == ALL_RISK_AGENTS:
        add_pending_agent(
            agent_name=GEO_RISK_ANALYST_AGENT,
            uses="searchQuery.political",
            prepared_search_query=search_query.get("political"),
        )

        add_pending_agent(
            agent_name=TRADE_RISK_ANALYST_AGENT,
            uses="searchQuery.tariff",
            prepared_search_query=search_query.get("tariff"),
        )

        add_pending_agent(
            agent_name=ROUTE_RISK_ANALYST_AGENT,
            uses="searchQuery.logistics",
            prepared_search_query=search_query.get("logistics"),
        )

    return pending_agents


def build_compact_router_result(router_result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "first_agent": router_result.get("first_agent"),
        "intent": router_result.get("intent"),
        "next_agent_after_scheduler": router_result.get("next_agent_after_scheduler"),
        "confidence": router_result.get("confidence"),
        "reason": router_result.get("reason"),
        "router_source": router_result.get("router_source"),
        "auditLogCount": len(router_result.get("auditLogs", [])),
        "auditContext": router_result.get("auditContext"),
    }


def run_supplypulse_pipeline(user_question: str) -> Dict[str, Any]:
    audit_context = AuditLoggingPlugin.create_context(
        model_name=settings.gemini_model
    )

    router = RouterAgent(audit_context=audit_context)
    router_result = router.classify(user_question)
    execution_plan = router.get_execution_plan(router_result)

    pipeline_result: Dict[str, Any] = {
        "userQuestion": user_question,
        "auditContext": audit_context,
        "routerResult": router_result,
        "executionPlan": execution_plan,
    }

    if router_result["first_agent"] == SUPPORT_AGENT:
        support_result = SupportAgent(audit_context=audit_context).run(user_question)
        pipeline_result["supportResult"] = support_result

        pipeline_result["pipelineAudit"] = AuditFlowPlugin().build_pipeline_audit(
            pipeline_result
        )

        return pipeline_result

    schedule_result = ScheduleAnalyzerAgent(
        audit_context=audit_context
    ).run_from_csv(settings.raw_data_path)

    pipeline_result["scheduleResult"] = schedule_result

    next_agent_after_scheduler = router_result.get("next_agent_after_scheduler")

    executed_agents: Set[str] = set()

    if should_run_geo_agent(next_agent_after_scheduler):
        geo_result = GeoRiskAnalystAgent(
            audit_context=audit_context
        ).run(schedule_result)

        pipeline_result["geoResult"] = geo_result
        executed_agents.add(GEO_RISK_ANALYST_AGENT)

    if should_run_trade_agent(next_agent_after_scheduler):
        trade_result = TradeRiskAnalystAgent(
            audit_context=audit_context
        ).run(schedule_result)

        pipeline_result["tradeResult"] = trade_result
        executed_agents.add(TRADE_RISK_ANALYST_AGENT)

    if should_run_route_agent(next_agent_after_scheduler):
        route_result = RouteRiskAnalystAgent(
            audit_context=audit_context
        ).run(schedule_result)

        pipeline_result["routeResult"] = route_result
        executed_agents.add(ROUTE_RISK_ANALYST_AGENT)

    pending_risk_agents = build_pending_risk_agents(
        next_agent_after_scheduler=next_agent_after_scheduler,
        schedule_result=schedule_result,
        executed_agents=executed_agents,
    )

    pipeline_result["executedRiskAgents"] = sorted(list(executed_agents))
    pipeline_result["pendingRiskAgents"] = pending_risk_agents

    report_result = RiskReportBuilderAgent(
        audit_context=audit_context
    ).run(
        user_question=user_question,
        schedule_result=schedule_result,
        geo_result=pipeline_result.get("geoResult"),
        trade_result=pipeline_result.get("tradeResult"),
        route_result=pipeline_result.get("routeResult"),
    )

    pipeline_result["reportResult"] = report_result

    pipeline_result["pipelineAudit"] = AuditFlowPlugin().build_pipeline_audit(
        pipeline_result
    )

    return pipeline_result


def print_pipeline_audit_summary(result: Dict[str, Any]) -> None:
    pipeline_audit = result.get("pipelineAudit")

    if not pipeline_audit:
        return

    print("\nPIPELINE AUDIT SUMMARY:")
    print(
        json.dumps(
            {
                "sharedContextCheck": pipeline_audit.get("sharedContextCheck"),
                "agentAuditCounts": pipeline_audit.get("agentAuditCounts"),
                "totalAuditLogs": pipeline_audit.get("totalAuditLogs"),
                "evidenceSearchSummary": pipeline_audit.get("evidenceSearchSummary"),
            },
            indent=2,
        )
    )

    print("\nPIPELINE AUDIT STAGE TIMELINE:")

    for item in pipeline_audit.get("stageTimeline", []):
        print(
            f"{item.get('timelineIndex')}. "
            f"{item.get('outputName')} / "
            f"{item.get('agentName')} / "
            f"{item.get('stage')}"
        )


def print_geo_result(result: Dict[str, Any]) -> None:
    geo_result = result.get("geoResult")

    if not geo_result:
        return

    print("\nGEO EXPOSURE LEVEL:")
    print(geo_result.get("geoExposureLevel"))

    print("\nGEO EXPOSURE SUMMARY:")
    print(geo_result.get("geoExposureSummary"))

    print("\nGEO SEARCH LOCALIZATION:")
    print(json.dumps(geo_result.get("searchLocalization"), indent=2))

    print("\nGEO BRIGHT DATA SEARCH SUMMARY:")
    print(json.dumps(geo_result.get("brightDataSearch"), indent=2))

    print("\nGEO SOURCE QUALITY SUMMARY:")
    print(json.dumps(geo_result.get("sourceQuality", {}).get("summary"), indent=2))

    print("\nGEO AFFECTED ITEMS:")
    print(json.dumps(geo_result.get("affectedItems"), indent=2))

    print("\nGEO KEY FINDINGS:")
    print(json.dumps(geo_result.get("keyFindings"), indent=2))

    print("\nGEO RECOMMENDED ACTIONS:")
    print(json.dumps(geo_result.get("recommendedActions"), indent=2))

    print("\nGEO LIMITATIONS:")
    print(geo_result.get("limitations"))


def print_trade_result(result: Dict[str, Any]) -> None:
    trade_result = result.get("tradeResult")

    if not trade_result:
        return

    print("\nTRADE / TARIFF EXPOSURE LEVEL:")
    print(trade_result.get("tradeExposureLevel"))

    print("\nTRADE / TARIFF EXPOSURE SUMMARY:")
    print(trade_result.get("tradeExposureSummary"))

    print("\nTRADE SEARCH LOCALIZATION:")
    print(json.dumps(trade_result.get("searchLocalization"), indent=2))

    print("\nTRADE BRIGHT DATA SEARCH SUMMARY:")
    print(json.dumps(trade_result.get("brightDataSearch"), indent=2))

    print("\nTRADE SOURCE QUALITY SUMMARY:")
    print(json.dumps(trade_result.get("sourceQuality", {}).get("summary"), indent=2))

    print("\nTRADE AFFECTED ITEMS:")
    print(json.dumps(trade_result.get("affectedItems"), indent=2))

    print("\nTRADE KEY FINDINGS:")
    print(json.dumps(trade_result.get("keyFindings"), indent=2))

    print("\nTRADE RECOMMENDED ACTIONS:")
    print(json.dumps(trade_result.get("recommendedActions"), indent=2))

    print("\nTRADE LIMITATIONS:")
    print(trade_result.get("limitations"))


def print_route_result(result: Dict[str, Any]) -> None:
    route_result = result.get("routeResult")

    if not route_result:
        return

    print("\nROUTE / LOGISTICS EXPOSURE LEVEL:")
    print(route_result.get("routeExposureLevel"))

    print("\nROUTE / LOGISTICS EXPOSURE SUMMARY:")
    print(route_result.get("routeExposureSummary"))

    print("\nROUTE SEARCH LOCALIZATION:")
    print(json.dumps(route_result.get("searchLocalization"), indent=2))

    print("\nROUTE BRIGHT DATA SEARCH SUMMARY:")
    print(json.dumps(route_result.get("brightDataSearch"), indent=2))

    print("\nROUTE SOURCE QUALITY SUMMARY:")
    print(json.dumps(route_result.get("sourceQuality", {}).get("summary"), indent=2))

    print("\nROUTE AFFECTED ITEMS:")
    print(json.dumps(route_result.get("affectedItems"), indent=2))

    print("\nROUTE KEY FINDINGS:")
    print(json.dumps(route_result.get("keyFindings"), indent=2))

    print("\nROUTE RECOMMENDED ACTIONS:")
    print(json.dumps(route_result.get("recommendedActions"), indent=2))

    print("\nROUTE LIMITATIONS:")
    print(route_result.get("limitations"))


def print_pipeline_result(result: Dict[str, Any]) -> None:
    print("\n" + "=" * 90)
    print("SUPPLYPULSE V2 PIPELINE RESULT")
    print("=" * 90)

    print("\nUSER QUESTION:")
    print(result["userQuestion"])

    print("\nSHARED AUDIT CONTEXT:")
    print(json.dumps(result["auditContext"], indent=2))

    print("\nROUTER RESULT:")
    print(json.dumps(build_compact_router_result(result["routerResult"]), indent=2))

    print("\nEXECUTION PLAN:")
    print(" → ".join(result["executionPlan"]))

    if "supportResult" in result:
        print("\nSUPPORT RESPONSE:")
        print(result["supportResult"]["response"])

        print("\nAUDIT LOG COUNTS:")
        print(
            json.dumps(
                {
                    "routerAuditLogs": len(result["routerResult"]["auditLogs"]),
                    "supportAuditLogs": len(result["supportResult"]["auditLogs"]),
                },
                indent=2,
            )
        )

        print("\nSHARED RUN CHECK:")
        print("router run_id: ", result["routerResult"]["auditContext"]["run_id"])
        print("support run_id:", result["supportResult"]["auditContext"]["run_id"])

        print_pipeline_audit_summary(result)
        return

    print("\nSCHEDULE SUMMARY:")
    print(json.dumps(result["scheduleResult"]["summary"], indent=2))

    print("\nDOWNSTREAM SEARCH QUERIES:")
    print(json.dumps(result["scheduleResult"]["searchQuery"], indent=2))

    if result.get("executedRiskAgents"):
        print("\nEXECUTED RISK AGENTS:")
        print(json.dumps(result["executedRiskAgents"], indent=2))

    if result.get("pendingRiskAgents"):
        print("\nPENDING RISK AGENTS:")
        print(json.dumps(result["pendingRiskAgents"], indent=2))

    print_geo_result(result)
    print_trade_result(result)
    print_route_result(result)

    print("\nREPORT EXECUTIVE SUMMARY:")
    print(result["reportResult"]["executiveSummary"])

    print("\nDELIVERY EXPOSURE TABLE:")
    print(result["reportResult"]["deliveryExposureTable"])

    if result["reportResult"].get("geoExposureSection"):
        print("\nGEO EXPOSURE SECTION:")
        print(result["reportResult"]["geoExposureSection"])

    if result["reportResult"].get("tradeExposureSection"):
        print("\nTRADE / TARIFF EXPOSURE SECTION:")
        print(result["reportResult"]["tradeExposureSection"])

    if result["reportResult"].get("routeExposureSection"):
        print("\nROUTE / LOGISTICS EXPOSURE SECTION:")
        print(result["reportResult"]["routeExposureSection"])

    if result["reportResult"].get("inputSummary"):
        print("\nREPORT INPUT SUMMARY:")
        print(json.dumps(result["reportResult"]["inputSummary"], indent=2))

    print("\nFULL MARKDOWN REPORT:")
    print(result["reportResult"]["markdownReport"])

    audit_log_counts = {
        "routerAuditLogs": len(result["routerResult"]["auditLogs"]),
        "scheduleAnalyzerAuditLogs": len(result["scheduleResult"]["auditLogs"]),
        "reportBuilderAuditLogs": len(result["reportResult"]["auditLogs"]),
    }

    if result.get("geoResult"):
        audit_log_counts["geoRiskAnalystAuditLogs"] = len(
            result["geoResult"]["auditLogs"]
        )

    if result.get("tradeResult"):
        audit_log_counts["tradeRiskAnalystAuditLogs"] = len(
            result["tradeResult"]["auditLogs"]
        )

    if result.get("routeResult"):
        audit_log_counts["routeRiskAnalystAuditLogs"] = len(
            result["routeResult"]["auditLogs"]
        )

    print("\nAUDIT LOG COUNTS:")
    print(json.dumps(audit_log_counts, indent=2))

    print("\nSHARED RUN CHECK:")
    print("router run_id:  ", result["routerResult"]["auditContext"]["run_id"])
    print("schedule run_id:", result["scheduleResult"]["auditContext"]["run_id"])

    if result.get("geoResult"):
        print("geo run_id:     ", result["geoResult"]["auditContext"]["run_id"])

    if result.get("tradeResult"):
        print("trade run_id:   ", result["tradeResult"]["auditContext"]["run_id"])

    if result.get("routeResult"):
        print("route run_id:   ", result["routeResult"]["auditContext"]["run_id"])

    print("report run_id:  ", result["reportResult"]["auditContext"]["run_id"])

    print_pipeline_audit_summary(result)


if __name__ == "__main__":
    question = input("Ask SupplyPulse V2: ").strip()
    output = run_supplypulse_pipeline(question)
    print_pipeline_result(output)