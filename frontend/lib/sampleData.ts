import { PipelineResult } from "./types";

export function createSamplePipelineResult(question = "Demo run"): PipelineResult {
  return {
    userQuestion: question,
    executedRiskAgents: [
      "GEO_RISK_ANALYST_AGENT",
      "TRADE_RISK_ANALYST_AGENT",
      "ROUTE_RISK_ANALYST_AGENT",
    ],
    scheduleResult: {
      summary: {
        totalItems: 20,
        highRiskItems: 12,
        mediumRiskItems: 0,
        lowRiskItems: 0,
        onTrackItems: 8,
      },
      searchQuery: {
        political:
          "Political risks manufacturing exports Taiwan to Singapore UPS current issues",
        tariff: "Taiwan Singapore tariffs UPS trade agreements customs duties",
        logistics:
          "Kaohsiung to Singapore shipping route issues logistics current delays",
      },
      equipmentItems: [
        {
          equipmentCode: "UPS-2MW-02",
          equipmentName: "2 MW Modular UPS System",
          baselineDueDate: "2026-06-05",
          latestExpectedDeliveryDate: "2026-06-20",
          delayDays: 15,
          scheduleRiskPercentage: 250,
          scheduleRiskLevel: "High",
          originCountry: "Taiwan",
          projectCountry: "Singapore",
        },
        {
          equipmentCode: "PCS-3MW-05",
          equipmentName: "3 MW Power Conversion System",
          baselineDueDate: "2026-06-08",
          latestExpectedDeliveryDate: "2026-06-24",
          delayDays: 16,
          scheduleRiskPercentage: 160,
          scheduleRiskLevel: "High",
          originCountry: "Switzerland",
          projectCountry: "United States",
        },
        {
          equipmentCode: "CMP-H2-06",
          equipmentName: "Hydrogen Compressor Package",
          baselineDueDate: "2026-06-10",
          latestExpectedDeliveryDate: "2026-06-28",
          delayDays: 18,
          scheduleRiskPercentage: 150,
          scheduleRiskLevel: "High",
          originCountry: "Japan",
          projectCountry: "Netherlands",
        },
        {
          equipmentCode: "BAT-LFP-01",
          equipmentName: "LFP Battery Rack",
          baselineDueDate: "2026-06-28",
          latestExpectedDeliveryDate: "2026-07-04",
          delayDays: 6,
          scheduleRiskPercentage: 20.69,
          scheduleRiskLevel: "High",
          originCountry: "China",
          projectCountry: "Singapore",
        },
        {
          equipmentCode: "CRAC-80-07",
          equipmentName: "Precision Cooling CRAC Unit",
          baselineDueDate: "2026-07-20",
          latestExpectedDeliveryDate: "2026-07-20",
          delayDays: 0,
          scheduleRiskPercentage: 0,
          scheduleRiskLevel: "On Track",
          originCountry: "Japan",
          projectCountry: "Singapore",
        },
      ],
    },
    geoResult: {
      geoExposureLevel: "High",
      geoExposureSummary:
        "Geopolitical tensions in the Taiwan Strait present significant exposure to Taiwan-to-Singapore electronics supply chains.",
      affectedItems: [
        {
          equipmentCode: "UPS-2MW-02",
          equipmentName: "2 MW Modular UPS System",
          sourceCountry: "Taiwan",
          destinationCountry: "Singapore",
          scheduleExposurePercentage: 250,
          statusBand: "High",
          geoExposureReason:
            "Taiwan Strait exposure may affect Taiwan-to-Singapore electronics shipments.",
        },
      ],
      keyFindings: [
        "Taiwan is a critical electronics manufacturing hub.",
        "Taiwan Strait disruption could affect trade flows into Singapore.",
      ],
      recommendedActions: [
        "Monitor Taiwan Strait developments.",
        "Review supplier contingency plans.",
      ],
      limitations:
        "Analysis is focused on the matched Taiwan-to-Singapore item.",
      evidenceUsed: [
        {
          rank: 1,
          sourceTitle: "Situation in the Taiwan Strait and Implications for Singapore",
          sourceUrl: "https://rsis.edu.sg/",
          sourceDomain: "rsis.edu.sg",
          sourceCategory: "trusted",
          evidenceSummary:
            "Taiwan Strait disruption could affect Singapore supply chains.",
          relevanceReason:
            "Directly relevant to Taiwan-to-Singapore trade exposure.",
        },
      ],
      brightDataSearch: {
        success: true,
        query:
          "Political risks manufacturing exports Taiwan to Singapore UPS current issues",
        country: "sg",
        language: "en",
        location: "Singapore",
        matchedEquipmentCode: "UPS-2MW-02",
        resultCount: 15,
        topSources: ["rsis.edu.sg", "csis.org", "asianews.network"],
      },
      sourceQuality: {
        summary: {
          rawResultCount: 10,
          trustedCount: 3,
          usableCount: 4,
          lowerQualityCount: 2,
          discardedCount: 0,
          evidenceReadyCount: 7,
        },
      },
    },
    tradeResult: {
      tradeExposureLevel: "Low",
      tradeExposureSummary:
        "ASTEP indicates Singapore has eliminated customs duties on products imported from Taiwan, so direct tariff exposure is low.",
      affectedItems: [
        {
          equipmentCode: "UPS-2MW-02",
          equipmentName: "2 MW Modular UPS System",
          sourceCountry: "Taiwan",
          destinationCountry: "Singapore",
          scheduleExposurePercentage: 250,
          statusBand: "High",
          tradeExposureReason:
            "ASTEP supports low direct customs duty exposure for Taiwan-to-Singapore imports.",
        },
      ],
      keyFindings: [
        "ASTEP is active between Singapore and Taiwan.",
        "Direct customs duty exposure is low.",
      ],
      recommendedActions: [
        "Verify HS code.",
        "Prepare Certificate of Origin documentation.",
      ],
      limitations:
        "Specific HS code was not available in the evidence pack.",
      evidenceUsed: [
        {
          rank: 5,
          sourceTitle: "ASTEP",
          sourceUrl: "https://www.enterprisesg.gov.sg/",
          sourceDomain: "enterprisesg.gov.sg",
          sourceCategory: "trusted",
          evidenceSummary:
            "Enterprise Singapore confirms the ASTEP agreement.",
          relevanceReason:
            "Directly relevant to Taiwan-to-Singapore tariff exposure.",
        },
      ],
      brightDataSearch: {
        success: true,
        query: "Taiwan Singapore tariffs UPS trade agreements customs duties",
        country: "sg",
        language: "en",
        location: "Singapore",
        matchedEquipmentCode: "UPS-2MW-02",
        resultCount: 16,
        topSources: ["enterprisesg.gov.sg", "italaw.com", "rikvin.com"],
      },
      sourceQuality: {
        summary: {
          rawResultCount: 10,
          trustedCount: 1,
          usableCount: 8,
          lowerQualityCount: 1,
          discardedCount: 0,
          evidenceReadyCount: 9,
        },
      },
    },
    routeResult: {
      routeExposureLevel: "High",
      routeExposureSummary:
        "The Kaohsiung-to-Singapore route faces high route and logistics exposure from port congestion and typhoon-season delay pressure.",
      affectedItems: [
        {
          equipmentCode: "UPS-2MW-02",
          equipmentName: "2 MW Modular UPS System",
          sourceCountry: "Taiwan",
          destinationCountry: "Singapore",
          sourcePort: "Kaohsiung",
          destinationPort: "Singapore",
          scheduleExposurePercentage: 250,
          statusBand: "High",
          routeExposureReason:
            "Live port congestion monitoring and typhoon-season exposure affect the Kaohsiung-to-Singapore route.",
        },
      ],
      keyFindings: [
        "Live congestion monitoring exists for Singapore and Taiwan ports.",
        "The South China Sea route is entering typhoon season.",
      ],
      recommendedActions: [
        "Monitor port congestion daily.",
        "Request vessel-level ETA and wait-time updates.",
      ],
      limitations:
        "Vessel-specific wait-time evidence is not available.",
      evidenceUsed: [
        {
          rank: 1,
          sourceTitle: "Singapore Port Congestion / Delay Status Data",
          sourceUrl: "https://www.gocomet.com/real-time-port-congestion/singapore",
          sourceDomain: "gocomet.com",
          sourceCategory: "usable",
          evidenceSummary:
            "Provides live status of port delays in Singapore.",
          relevanceReason:
            "Directly relevant to the destination port Singapore.",
        },
        {
          rank: 8,
          sourceTitle:
            "Kaohsiung the latest victim of Asia's container congestion",
          sourceUrl: "https://theloadstar.com/",
          sourceDomain: "theloadstar.com",
          sourceCategory: "historical/stale",
          evidenceSummary:
            "Historical context from July 2024 about Kaohsiung congestion.",
          relevanceReason:
            "Provides historical context, not current live confirmation.",
        },
      ],
      brightDataSearch: {
        success: true,
        query:
          "Kaohsiung to Singapore shipping route issues logistics current delays",
        country: "sg",
        language: "en",
        location: "Singapore",
        matchedEquipmentCode: "UPS-2MW-02",
        resultCount: 16,
        topSources: ["gocomet.com", "gocubic.io", "portcast.io"],
      },
      sourceQuality: {
        summary: {
          rawResultCount: 10,
          trustedCount: 0,
          usableCount: 8,
          lowerQualityCount: 1,
          discardedCount: 0,
          evidenceReadyCount: 8,
        },
      },
    },
    reportResult: {
      executiveSummary:
        "SupplyPulse identifies UPS-2MW-02 as the highest-exposure item, with 250% Schedule Exposure. Geo exposure is High, trade exposure is Low, and route / logistics exposure is High.",
      markdownReport:
        "# SupplyPulse Delivery Exposure Report\n\n## 1. Executive Summary\n\nUPS-2MW-02 is the highest-exposure item.\n\n## 2. Exposure Overview\n\n12 high-exposure items were identified.\n\n## 3. Geopolitical Exposure\n\nHigh.\n\n## 4. Trade / Tariff Exposure\n\nLow.\n\n## 5. Route / Logistics Exposure\n\nHigh.",
      recommendedActions: [
        "Monitor Taiwan Strait developments.",
        "Confirm ASTEP documentation.",
        "Monitor Kaohsiung and Singapore port congestion.",
      ],
      reportLimitations:
        "This demo report uses sample frontend fallback data.",
    },
    pipelineAudit: {
      agentAuditCounts: {
        router: 4,
        scheduleAnalyzer: 7,
        geoAnalyst: 9,
        tradeAnalyst: 9,
        routeAnalyst: 9,
        reportBuilder: 6,
      },
      totalAuditLogs: 44,
      sharedContextCheck: {
        expectedRunId: "run_demo_44_logs",
        allOutputsShareRunId: true,
      },
      evidenceSearchSummary: [
        {
          eventType: "search_request",
          agentName: "GEO_RISK_ANALYST_AGENT",
          query:
            "Political risks manufacturing exports Taiwan to Singapore UPS current issues",
          glCountry: "sg",
          hlLanguage: "en",
          location: "Singapore",
        },
        {
          eventType: "search_request",
          agentName: "TRADE_RISK_ANALYST_AGENT",
          query: "Taiwan Singapore tariffs UPS trade agreements customs duties",
          glCountry: "sg",
          hlLanguage: "en",
          location: "Singapore",
        },
        {
          eventType: "search_request",
          agentName: "ROUTE_RISK_ANALYST_AGENT",
          query:
            "Kaohsiung to Singapore shipping route issues logistics current delays",
          glCountry: "sg",
          hlLanguage: "en",
          location: "Singapore",
        },
      ],
      stageTimeline: [
        {
          sourceName: "router",
          agentName: "ROUTER_AGENT",
          stage: "classification_request",
        },
        {
          sourceName: "scheduleAnalyzer",
          agentName: "SCHEDULE_ANALYZER_AGENT",
          stage: "risk_calculation",
        },
        {
          sourceName: "geoAnalyst",
          agentName: "GEO_RISK_ANALYST_AGENT",
          stage: "geo_exposure_assessment",
        },
        {
          sourceName: "tradeAnalyst",
          agentName: "TRADE_RISK_ANALYST_AGENT",
          stage: "trade_exposure_assessment",
        },
        {
          sourceName: "routeAnalyst",
          agentName: "ROUTE_RISK_ANALYST_AGENT",
          stage: "route_exposure_assessment",
        },
        {
          sourceName: "reportBuilder",
          agentName: "RISK_REPORT_BUILDER_AGENT",
          stage: "final_output",
        },
      ],
    },
  };
}