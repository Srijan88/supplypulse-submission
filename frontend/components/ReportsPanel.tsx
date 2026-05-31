"use client";

import {
  AlertTriangle,
  CheckCircle2,
  Database,
  Download,
  FileText,
  Globe2,
  PackageSearch,
  Printer,
  Radar,
  Route,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { useEffect, useMemo } from "react";
import type { ReactNode } from "react";
import type { PipelineResult } from "@/lib/types";

type EquipmentLike = {
  equipmentCode?: string;
  equipmentName?: string;
  baselineDueDate?: string;
  latestExpectedDeliveryDate?: string;
  delayDays?: number;
  scheduleRiskPercentage?: number;
  scheduleRiskLevel?: string;
  originCountry?: string;
  projectCountry?: string;
};

type AffectedItemLike = {
  equipmentCode?: string;
  equipmentName?: string;
  sourceCountry?: string;
  destinationCountry?: string;
  scheduleExposurePercentage?: number;
  statusBand?: string;
  geoExposureReason?: string;
  tradeExposureReason?: string;
  routeExposureReason?: string;
};

type EvidenceLike = {
  rank?: number;
  sourceTitle?: string;
  sourceUrl?: string;
  sourceDomain?: string;
  sourceCategory?: string;
  evidenceSummary?: string;
  relevanceReason?: string;
};

export function ReportsPanel({ result }: { result: PipelineResult }) {
  const report = result.reportResult;
  const scheduleSummary = result.scheduleResult?.summary;
  const items = (result.scheduleResult?.equipmentItems || []) as EquipmentLike[];

  const markdownReport =
    report?.markdownReport ||
    "# SupplyPulse Delivery Exposure Report\n\nRun an analysis to generate the report.";

  const generatedAt = result.lastRunAt
    ? new Date(result.lastRunAt).toLocaleString()
    : new Date().toLocaleString();

  const reportFileName = useMemo(() => {
    const date = new Date().toISOString().slice(0, 10);
    return `SupplyPulse_NorthBridge_Delivery_Exposure_Report_${date}.md`;
  }, []);

  useEffect(() => {
    function cleanupPrintMode() {
      document.body.classList.remove("printing-report");
    }

    window.addEventListener("afterprint", cleanupPrintMode);

    return () => {
      window.removeEventListener("afterprint", cleanupPrintMode);
    };
  }, []);

  function exportPdf() {
    document.body.classList.add("printing-report");

    window.setTimeout(() => {
      window.print();

      window.setTimeout(() => {
        document.body.classList.remove("printing-report");
      }, 800);
    }, 100);
  }

  function downloadMarkdown() {
    const blob = new Blob([markdownReport], {
      type: "text/markdown;charset=utf-8",
    });

    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");

    anchor.href = url;
    anchor.download = reportFileName;
    anchor.click();

    URL.revokeObjectURL(url);
  }

  const totalItems = getNumber(scheduleSummary?.totalItems, items.length);
  const highItems = getNumber(scheduleSummary?.highRiskItems, 0);
  const mediumItems = getNumber(scheduleSummary?.mediumRiskItems, 0);
  const lowItems = getNumber(scheduleSummary?.lowRiskItems, 0);
  const onTrackItems = getNumber(scheduleSummary?.onTrackItems, 0);

  const geoLevel = result.geoResult?.geoExposureLevel || "Not Run";
  const tradeLevel = result.tradeResult?.tradeExposureLevel || "Not Run";
  const routeLevel = result.routeResult?.routeExposureLevel || "Not Run";

  return (
    <div className="space-y-6">
      <section className="no-print rounded-[2rem] border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-violet-50 px-3 py-1 text-xs font-black text-violet-700 ring-1 ring-violet-100">
              <FileText size={14} />
              Executive report publishing
            </div>

            <h2 className="mt-3 text-2xl font-black tracking-tight text-slate-950">
              SupplyPulse Delivery Exposure Report
            </h2>

            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              Publish a clean PDF-ready report for stakeholders, while keeping
              the markdown export available for technical review.
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row">
            <button
              onClick={exportPdf}
              className="inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600 px-5 py-3 text-sm font-black text-white shadow-lg shadow-violet-200 transition hover:from-violet-700 hover:to-indigo-700"
            >
              <Printer size={18} />
              Export PDF
            </button>

            <button
              onClick={downloadMarkdown}
              className="inline-flex items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-black text-slate-700 transition hover:border-violet-200 hover:bg-violet-50"
            >
              <Download size={18} />
              Download Markdown
            </button>
          </div>
        </div>
      </section>

      <article className="pdf-report overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-sm">
        <header className="bg-gradient-to-br from-slate-950 via-violet-950 to-indigo-950 p-8 text-white">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-black text-violet-100 ring-1 ring-white/15">
                <Sparkles size={14} />
                SupplyPulse Executive Report
              </div>

              <h1 className="mt-5 max-w-4xl text-4xl font-black tracking-tight">
                Delivery Exposure Report
              </h1>

              <p className="mt-3 max-w-3xl text-sm leading-6 text-violet-100">
                NorthBridge Energy Infrastructure - Singapore Data Center Phase
                2
              </p>
            </div>

            <div className="rounded-3xl bg-white/10 p-4 text-sm ring-1 ring-white/15">
              <div className="text-xs font-black uppercase tracking-wide text-violet-200">
                Generated
              </div>
              <div className="mt-1 font-bold text-white">{generatedAt}</div>

              <div className="mt-4 text-xs font-black uppercase tracking-wide text-violet-200">
                Run ID
              </div>
              <div className="mt-1 break-all font-mono text-xs text-white">
                {result.auditContext?.run_id || "Not available"}
              </div>
            </div>
          </div>
        </header>

        <section className="border-b border-slate-200 p-6">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <ReportMetric
              label="Tracked Items"
              value={totalItems}
              icon={<PackageSearch size={18} />}
            />
            <ReportMetric
              label="High-Exposure Items"
              value={highItems}
              icon={<AlertTriangle size={18} />}
              tone="danger"
            />
            <ReportMetric
              label="On-Track Items"
              value={onTrackItems}
              icon={<CheckCircle2 size={18} />}
              tone="success"
            />
            <ReportMetric
              label="Audit Logs"
              value={result.pipelineAudit?.totalAuditLogs || 0}
              icon={<ShieldCheck size={18} />}
              tone="violet"
            />
          </div>
        </section>

        <section className="grid gap-6 border-b border-slate-200 p-6 xl:grid-cols-[1fr_360px]">
          <div>
            <SectionLabel>Executive Summary</SectionLabel>
            <p className="mt-3 text-sm leading-7 text-slate-700">
              {report?.executiveSummary ||
                "Run a SupplyPulse analysis to generate an executive summary."}
            </p>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-slate-50 p-5">
            <SectionLabel>External Exposure Levels</SectionLabel>

            <div className="mt-4 space-y-3">
              <ExposureBadge
                label="Geopolitical"
                value={geoLevel}
                icon={<Globe2 size={16} />}
              />
              <ExposureBadge
                label="Trade / Tariff"
                value={tradeLevel}
                icon={<Radar size={16} />}
              />
              <ExposureBadge
                label="Route / Logistics"
                value={routeLevel}
                icon={<Route size={16} />}
              />
            </div>
          </div>
        </section>

        <section className="border-b border-slate-200 p-6">
          <SectionLabel>Exposure Overview</SectionLabel>

          <div className="mt-4 grid gap-3 md:grid-cols-4">
            <SmallSummary label="High" value={highItems} />
            <SmallSummary label="Medium" value={mediumItems} />
            <SmallSummary label="Low" value={lowItems} />
            <SmallSummary label="On Track" value={onTrackItems} />
          </div>

          <div className="mt-5 rounded-3xl bg-violet-50 p-4 text-sm leading-6 text-violet-900 ring-1 ring-violet-100">
            <strong>Note:</strong> Schedule Exposure % is a delay-pressure
            score, not a probability. A higher number means the delivery
            timeline needs more attention.
          </div>
        </section>

        <section className="border-b border-slate-200 p-6">
          <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
            <div>
              <SectionLabel>Delivery Exposure Table</SectionLabel>
              <p className="mt-2 text-xs leading-5 text-slate-500">
                Equipment-level view of planned need date, forecast arrival,
                delay pressure, status band, and country lane.
              </p>
            </div>
          </div>

          <div className="mt-5 overflow-x-auto rounded-3xl border border-slate-200">
            <table className="w-full min-w-[980px] border-collapse text-left text-xs">
              <thead className="bg-slate-50 text-[11px] uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-3 py-3 font-black">Item Code</th>
                  <th className="px-3 py-3 font-black">Asset / Equipment</th>
                  <th className="px-3 py-3 font-black">Planned Need</th>
                  <th className="px-3 py-3 font-black">Forecast Arrival</th>
                  <th className="px-3 py-3 text-right font-black">
                    Delay / Gain
                  </th>
                  <th className="px-3 py-3 text-right font-black">
                    Schedule Exposure
                  </th>
                  <th className="px-3 py-3 font-black">Status Band</th>
                  <th className="px-3 py-3 font-black">Country Lane</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-100">
                {items.map((item) => (
                  <tr key={item.equipmentCode} className="align-top">
                    <td className="px-3 py-3 font-black text-slate-950">
                      {item.equipmentCode || "—"}
                    </td>
                    <td className="px-3 py-3 text-slate-700">
                      {item.equipmentName || "—"}
                    </td>
                    <td className="px-3 py-3 text-slate-600">
                      {item.baselineDueDate || "—"}
                    </td>
                    <td className="px-3 py-3 text-slate-600">
                      {item.latestExpectedDeliveryDate || "—"}
                    </td>
                    <td className="px-3 py-3 text-right font-bold text-slate-700">
                      {formatNumber(item.delayDays)} days
                    </td>
                    <td className="px-3 py-3 text-right font-black text-slate-950">
                      {formatPercent(item.scheduleRiskPercentage)}
                    </td>
                    <td className="px-3 py-3">
                      <StatusPill status={item.scheduleRiskLevel || "Unknown"} />
                    </td>
                    <td className="px-3 py-3 text-slate-600">
                      {item.originCountry || "—"} → {item.projectCountry || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <ExternalAnalysisSection
          title="Geopolitical Exposure"
          level={geoLevel}
          summary={result.geoResult?.geoExposureSummary}
          affectedItems={result.geoResult?.affectedItems as AffectedItemLike[]}
          keyFindings={result.geoResult?.keyFindings}
          recommendedActions={result.geoResult?.recommendedActions}
          limitations={result.geoResult?.limitations}
          evidence={result.geoResult?.evidenceUsed as EvidenceLike[]}
        />

        <ExternalAnalysisSection
          title="Trade / Tariff Exposure"
          level={tradeLevel}
          summary={result.tradeResult?.tradeExposureSummary}
          affectedItems={result.tradeResult?.affectedItems as AffectedItemLike[]}
          keyFindings={result.tradeResult?.keyFindings}
          recommendedActions={result.tradeResult?.recommendedActions}
          limitations={result.tradeResult?.limitations}
          evidence={result.tradeResult?.evidenceUsed as EvidenceLike[]}
        />

        <ExternalAnalysisSection
          title="Route / Logistics Exposure"
          level={routeLevel}
          summary={result.routeResult?.routeExposureSummary}
          affectedItems={result.routeResult?.affectedItems as AffectedItemLike[]}
          keyFindings={result.routeResult?.keyFindings}
          recommendedActions={result.routeResult?.recommendedActions}
          limitations={result.routeResult?.limitations}
          evidence={result.routeResult?.evidenceUsed as EvidenceLike[]}
        />

        <section className="border-b border-slate-200 p-6">
          <SectionLabel>Downstream Intelligence Queries</SectionLabel>

          <div className="mt-4 grid gap-3">
            <QueryRow
              label="Geopolitical"
              value={result.scheduleResult?.searchQuery?.political}
            />
            <QueryRow
              label="Trade / Tariff"
              value={result.scheduleResult?.searchQuery?.tariff}
            />
            <QueryRow
              label="Route / Logistics"
              value={result.scheduleResult?.searchQuery?.logistics}
            />
          </div>
        </section>

        <section className="p-6">
          <SectionLabel>Run Audit Summary</SectionLabel>

          <div className="mt-4 grid gap-4 md:grid-cols-3">
            <AuditBox
              label="Shared Run"
              value={
                result.pipelineAudit?.sharedContextCheck?.allOutputsShareRunId
                  ? "Yes"
                  : "No"
              }
            />
            <AuditBox
              label="Total Audit Logs"
              value={String(result.pipelineAudit?.totalAuditLogs || 0)}
            />
            <AuditBox
              label="Evidence Searches"
              value={String(
                result.pipelineAudit?.evidenceSearchSummary?.filter(
                  (event) => event.eventType === "search_request"
                ).length || 0
              )}
            />
          </div>
        </section>
      </article>

      <section className="no-print rounded-[2rem] border border-slate-200 bg-white p-5 shadow-sm">
        <details>
          <summary className="cursor-pointer text-sm font-black text-slate-950">
            View raw markdown report
          </summary>

          <pre className="mt-4 max-h-[460px] overflow-auto rounded-3xl bg-slate-950 p-5 text-xs leading-6 text-slate-100">
            {markdownReport}
          </pre>
        </details>
      </section>
    </div>
  );
}

function ReportMetric({
  label,
  value,
  icon,
  tone = "default",
}: {
  label: string;
  value: string | number;
  icon: ReactNode;
  tone?: "default" | "danger" | "success" | "violet";
}) {
  const toneClass =
    tone === "danger"
      ? "bg-rose-50 text-rose-700"
      : tone === "success"
        ? "bg-emerald-50 text-emerald-700"
        : tone === "violet"
          ? "bg-violet-50 text-violet-700"
          : "bg-slate-50 text-slate-700";

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className={`mb-3 inline-flex rounded-2xl p-2 ${toneClass}`}>
        {icon}
      </div>
      <div className="text-2xl font-black text-slate-950">{value}</div>
      <div className="mt-1 text-xs font-black uppercase tracking-wide text-slate-500">
        {label}
      </div>
    </div>
  );
}

function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <div className="text-xs font-black uppercase tracking-[0.18em] text-violet-700">
      {children}
    </div>
  );
}

function ExposureBadge({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon: ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-2xl bg-white p-3 ring-1 ring-slate-200">
      <div className="flex items-center gap-2">
        <div className="rounded-xl bg-violet-50 p-2 text-violet-700">
          {icon}
        </div>
        <div className="text-sm font-black text-slate-800">{label}</div>
      </div>

      <StatusPill status={value} />
    </div>
  );
}

function SmallSummary({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl bg-slate-50 p-4 ring-1 ring-slate-100">
      <div className="text-xl font-black text-slate-950">{value}</div>
      <div className="mt-1 text-xs font-bold text-slate-500">{label}</div>
    </div>
  );
}

function ExternalAnalysisSection({
  title,
  level,
  summary,
  affectedItems,
  keyFindings,
  recommendedActions,
  limitations,
  evidence,
}: {
  title: string;
  level: string;
  summary?: string;
  affectedItems?: AffectedItemLike[];
  keyFindings?: string[];
  recommendedActions?: string[];
  limitations?: string;
  evidence?: EvidenceLike[];
}) {
  const hasContent =
    summary ||
    affectedItems?.length ||
    keyFindings?.length ||
    recommendedActions?.length ||
    limitations ||
    evidence?.length;

  if (!hasContent) {
    return (
      <section className="border-b border-slate-200 p-6">
        <div className="flex items-center justify-between gap-3">
          <SectionLabel>{title}</SectionLabel>
          <StatusPill status={level} />
        </div>

        <p className="mt-3 text-sm leading-6 text-slate-500">
          This exposure dimension was not run for the current question.
        </p>
      </section>
    );
  }

  return (
    <section className="pdf-avoid-break border-b border-slate-200 p-6">
      <div className="flex items-center justify-between gap-3">
        <SectionLabel>{title}</SectionLabel>
        <StatusPill status={level} />
      </div>

      {summary && (
        <p className="mt-3 text-sm leading-7 text-slate-700">{summary}</p>
      )}

      {affectedItems && affectedItems.length > 0 && (
        <div className="mt-5">
          <div className="text-sm font-black text-slate-950">
            Affected Items
          </div>

          <div className="mt-3 grid gap-3">
            {affectedItems.map((item) => (
              <div
                key={`${title}-${item.equipmentCode}`}
                className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
              >
                <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                  <div>
                    <div className="text-sm font-black text-slate-950">
                      {item.equipmentCode || "—"} ·{" "}
                      {item.equipmentName || "Equipment item"}
                    </div>
                    <div className="mt-1 text-xs text-slate-500">
                      {item.sourceCountry || "—"} →{" "}
                      {item.destinationCountry || "—"}
                    </div>
                  </div>

                  <StatusPill status={item.statusBand || "Assessed"} />
                </div>

                <p className="mt-3 text-xs leading-5 text-slate-600">
                  {item.geoExposureReason ||
                    item.tradeExposureReason ||
                    item.routeExposureReason ||
                    "Item linked to this exposure dimension."}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {keyFindings && keyFindings.length > 0 && (
        <ReportList title="Key Findings" items={keyFindings} />
      )}

      {recommendedActions && recommendedActions.length > 0 && (
        <ReportList title="Recommended Actions" items={recommendedActions} />
      )}

      {evidence && evidence.length > 0 && (
        <div className="mt-5">
          <div className="flex items-center gap-2 text-sm font-black text-slate-950">
            <Database size={16} className="text-violet-700" />
            Evidence Used
          </div>

          <div className="mt-3 grid gap-3">
            {evidence.slice(0, 5).map((source) => (
              <div
                key={`${title}-${source.rank}-${source.sourceDomain}`}
                className="rounded-2xl border border-slate-200 bg-white p-4"
              >
                <div className="text-sm font-black text-slate-950">
                  {source.sourceTitle || "Source"}
                </div>

                <div className="mt-1 text-xs font-semibold text-violet-700">
                  {source.sourceDomain || "Unknown domain"} ·{" "}
                  {source.sourceCategory || "source"}
                </div>

                <p className="mt-2 text-xs leading-5 text-slate-600">
                  {source.evidenceSummary || source.relevanceReason || "—"}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {limitations && (
        <div className="mt-5 rounded-3xl bg-amber-50 p-4 text-sm leading-6 text-amber-900 ring-1 ring-amber-100">
          <strong>Limitations:</strong> {limitations}
        </div>
      )}
    </section>
  );
}

function ReportList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="mt-5">
      <div className="text-sm font-black text-slate-950">{title}</div>

      <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-700">
        {items.map((item, index) => (
          <li key={`${title}-${index}`} className="flex gap-2">
            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-600" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function QueryRow({ label, value }: { label: string; value?: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <div className="text-xs font-black uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className="mt-2 break-words font-mono text-xs leading-5 text-slate-800">
        {value || "Not available"}
      </div>
    </div>
  );
}

function AuditBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <div className="text-xl font-black text-slate-950">{value}</div>
      <div className="mt-1 text-xs font-bold text-slate-500">{label}</div>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const lowered = status.toLowerCase();

  const className = lowered.includes("high")
    ? "bg-rose-50 text-rose-700 ring-rose-200"
    : lowered.includes("medium")
      ? "bg-amber-50 text-amber-700 ring-amber-200"
      : lowered.includes("low")
        ? "bg-blue-50 text-blue-700 ring-blue-200"
        : lowered.includes("track")
          ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
          : "bg-slate-100 text-slate-600 ring-slate-200";

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-black ring-1 ${className}`}
    >
      {status}
    </span>
  );
}

function getNumber(value: unknown, fallback: number) {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function formatNumber(value?: number) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "0";
  }

  return value.toFixed(0);
}

function formatPercent(value?: number) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "0.00%";
  }

  return `${value.toFixed(2)}%`;
}