export type StatusBand = "High" | "Medium" | "Low" | "On Track" | string;

export type EquipmentItem = {
  equipmentCode?: string;
  equipmentName?: string;
  baselineDueDate?: string;
  latestExpectedDeliveryDate?: string;
  delayDays?: number;
  scheduleRiskPercentage?: number;
  scheduleRiskLevel?: StatusBand;
  originCountry?: string;
  projectCountry?: string;
};

export type ScheduleSummary = {
  totalItems?: number;
  highRiskItems?: number;
  mediumRiskItems?: number;
  lowRiskItems?: number;
  onTrackItems?: number;
};

export type ScheduleResult = {
  summary?: ScheduleSummary;
  equipmentItems?: EquipmentItem[];
  searchQuery?: {
    political?: string;
    tariff?: string;
    logistics?: string;
  };
};

export type EvidenceSource = {
  rank?: number;
  sourceTitle?: string;
  sourceUrl?: string;
  sourceDomain?: string;
  sourceCategory?: string;
  evidenceSummary?: string;
  relevanceReason?: string;
};

export type SourceQualitySummary = {
  rawResultCount?: number;
  trustedCount?: number;
  usableCount?: number;
  lowerQualityCount?: number;
  discardedCount?: number;
  evidenceReadyCount?: number;
};

export type BrightDataSearch = {
  success?: boolean;
  query?: string;
  targetUrl?: string;
  country?: string;
  language?: string;
  location?: string;
  localizationSource?: string;
  matchedEquipmentCode?: string;
  resultCount?: number;
  topSources?: string[];
};

export type GeoAffectedItem = {
  equipmentCode?: string;
  equipmentName?: string;
  sourceCountry?: string;
  destinationCountry?: string;
  scheduleExposurePercentage?: number;
  statusBand?: string;
  geoExposureReason?: string;
};

export type TradeAffectedItem = {
  equipmentCode?: string;
  equipmentName?: string;
  sourceCountry?: string;
  destinationCountry?: string;
  scheduleExposurePercentage?: number;
  statusBand?: string;
  tradeExposureReason?: string;
};

export type RouteAffectedItem = {
  equipmentCode?: string;
  equipmentName?: string;
  sourceCountry?: string;
  destinationCountry?: string;
  sourcePort?: string;
  destinationPort?: string;
  scheduleExposurePercentage?: number;
  statusBand?: string;
  routeExposureReason?: string;
};

export type GeoResult = {
  geoExposureLevel?: string;
  geoExposureSummary?: string;
  affectedItems?: GeoAffectedItem[];
  keyFindings?: string[];
  recommendedActions?: string[];
  limitations?: string;
  evidenceUsed?: EvidenceSource[];
  brightDataSearch?: BrightDataSearch;
  sourceQuality?: {
    summary?: SourceQualitySummary;
  };
};

export type TradeResult = {
  tradeExposureLevel?: string;
  tradeExposureSummary?: string;
  affectedItems?: TradeAffectedItem[];
  keyFindings?: string[];
  recommendedActions?: string[];
  limitations?: string;
  evidenceUsed?: EvidenceSource[];
  brightDataSearch?: BrightDataSearch;
  sourceQuality?: {
    summary?: SourceQualitySummary;
  };
};

export type RouteResult = {
  routeExposureLevel?: string;
  routeExposureSummary?: string;
  affectedItems?: RouteAffectedItem[];
  keyFindings?: string[];
  recommendedActions?: string[];
  limitations?: string;
  evidenceUsed?: EvidenceSource[];
  brightDataSearch?: BrightDataSearch;
  sourceQuality?: {
    summary?: SourceQualitySummary;
  };
};

export type ReportResult = {
  executiveSummary?: string;
  deliveryExposureTable?: string;
  geoExposureSection?: string;
  tradeExposureSection?: string;
  routeExposureSection?: string;
  markdownReport?: string;
  recommendedActions?: string[];
  reportLimitations?: string;
  inputSummary?: Record<string, unknown>;
};

export type AuditTimelineItem = {
  sourceName?: string;
  agentName?: string;
  stage?: string;
  createdAt?: string;
};

export type PipelineAudit = {
  sharedContextCheck?: {
    expectedRunId?: string;
    allOutputsShareRunId?: boolean;
    checks?: Array<{
      outputName?: string;
      runId?: string;
      matchesPipelineRun?: boolean;
    }>;
  };
  agentAuditCounts?: Record<string, number>;
  totalAuditLogs?: number;
  evidenceSearchSummary?: Array<Record<string, unknown>>;
  stageTimeline?: AuditTimelineItem[];
};

export type PipelineResult = {
  responseSource?: "backend" | "sample";
  lastRunAt?: string;
  userQuestion?: string;
  routerResult?: Record<string, unknown>;
  scheduleResult?: ScheduleResult;
  geoResult?: GeoResult;
  tradeResult?: TradeResult;
  routeResult?: RouteResult;
  reportResult?: ReportResult;
  executedRiskAgents?: string[];
  pipelineAudit?: PipelineAudit;
};