"use client";

import { AlertTriangle, CheckCircle2, Clock3, DatabaseZap } from "lucide-react";
import { EquipmentItem, PipelineResult } from "@/lib/types";

type Props = {
  result: PipelineResult;
  onSelectItem: (item: EquipmentItem) => void;
};

export function ControlTower({ result, onSelectItem }: Props) {
  const summary = result.scheduleResult?.summary || {};
  const items = result.scheduleResult?.equipmentItems || [];

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Total Items"
          value={summary.totalItems ?? items.length}
          helper="Tracked delivery items"
          icon={<DatabaseZap size={20} />}
        />
        <KpiCard
          label="High-Exposure Items"
          value={summary.highRiskItems ?? 0}
          helper="Items in High status band"
          icon={<AlertTriangle size={20} />}
          tone="danger"
        />
        <KpiCard
          label="On-Track Items"
          value={summary.onTrackItems ?? 0}
          helper="No schedule delay pressure"
          icon={<CheckCircle2 size={20} />}
          tone="success"
        />
        <KpiCard
          label="Audit Logs"
          value={result.pipelineAudit?.totalAuditLogs ?? 0}
          helper="Traceable agent events"
          icon={<Clock3 size={20} />}
          tone="violet"
        />
      </section>

      <section className="supply-card overflow-hidden">
        <div className="border-b border-slate-200 p-5">
          <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
            <div>
              <h2 className="text-lg font-bold text-slate-950">
                Delivery Exposure Table
              </h2>
              <p className="text-sm text-slate-500">
                Schedule Exposure % is a delay-pressure index, not a probability.
              </p>
            </div>
            <div className="text-sm text-slate-500">
              Click any item to inspect external exposure.
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <TableHead>Item Code</TableHead>
                <TableHead>Asset / Equipment</TableHead>
                <TableHead>Planned Need Date</TableHead>
                <TableHead>Forecast Arrival</TableHead>
                <TableHead align="right">Delay / Gain</TableHead>
                <TableHead align="right">Schedule Exposure %</TableHead>
                <TableHead>Status Band</TableHead>
                <TableHead>Source Country</TableHead>
                <TableHead>Destination Country</TableHead>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {items.map((item) => (
                <tr
                  key={`${item.equipmentCode}-${item.originCountry}`}
                  onClick={() => onSelectItem(item)}
                  className="cursor-pointer hover:bg-violet-50/50"
                >
                  <TableCell strong>{item.equipmentCode}</TableCell>
                  <TableCell>{item.equipmentName}</TableCell>
                  <TableCell>{item.baselineDueDate}</TableCell>
                  <TableCell>{item.latestExpectedDeliveryDate}</TableCell>
                  <TableCell align="right">{item.delayDays ?? 0}</TableCell>
                  <TableCell align="right">
                    {(item.scheduleRiskPercentage ?? 0).toFixed(2)}%
                  </TableCell>
                  <TableCell>
                    <StatusPill value={item.scheduleRiskLevel || "Unknown"} />
                  </TableCell>
                  <TableCell>{item.originCountry}</TableCell>
                  <TableCell>{item.projectCountry}</TableCell>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-3">
        <ExposureMiniCard
          title="Geopolitical Exposure"
          level={result.geoResult?.geoExposureLevel || "Not Run"}
          summary={result.geoResult?.geoExposureSummary || "No geo analysis yet."}
        />
        <ExposureMiniCard
          title="Trade / Tariff Exposure"
          level={result.tradeResult?.tradeExposureLevel || "Not Run"}
          summary={
            result.tradeResult?.tradeExposureSummary || "No trade analysis yet."
          }
        />
        <ExposureMiniCard
          title="Route / Logistics Exposure"
          level={result.routeResult?.routeExposureLevel || "Not Run"}
          summary={
            result.routeResult?.routeExposureSummary || "No route analysis yet."
          }
        />
      </section>
    </div>
  );
}

function KpiCard({
  label,
  value,
  helper,
  icon,
  tone = "default",
}: {
  label: string;
  value: number | string;
  helper: string;
  icon: React.ReactNode;
  tone?: "default" | "danger" | "success" | "violet";
}) {
  const toneClass =
    tone === "danger"
      ? "bg-rose-50 text-rose-700"
      : tone === "success"
      ? "bg-emerald-50 text-emerald-700"
      : tone === "violet"
      ? "bg-violet-50 text-violet-700"
      : "bg-slate-100 text-slate-700";

  return (
    <div className="supply-card p-5">
      <div className="flex items-center justify-between">
        <div className={`rounded-2xl p-3 ${toneClass}`}>{icon}</div>
      </div>
      <div className="mt-4 text-3xl font-bold text-slate-950">{value}</div>
      <div className="mt-1 text-sm font-medium text-slate-700">{label}</div>
      <div className="mt-1 text-xs text-slate-500">{helper}</div>
    </div>
  );
}

function TableHead({
  children,
  align = "left",
}: {
  children: React.ReactNode;
  align?: "left" | "right";
}) {
  return (
    <th
      className={[
        "px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500",
        align === "right" ? "text-right" : "text-left",
      ].join(" ")}
    >
      {children}
    </th>
  );
}

function TableCell({
  children,
  strong,
  align = "left",
}: {
  children: React.ReactNode;
  strong?: boolean;
  align?: "left" | "right";
}) {
  return (
    <td
      className={[
        "whitespace-nowrap px-4 py-4 text-slate-700",
        strong ? "font-semibold text-slate-950" : "",
        align === "right" ? "text-right" : "text-left",
      ].join(" ")}
    >
      {children}
    </td>
  );
}

function StatusPill({ value }: { value: string }) {
  const lowered = value.toLowerCase();

  const className = lowered.includes("high")
    ? "status-high"
    : lowered.includes("medium")
    ? "status-medium"
    : lowered.includes("low")
    ? "status-low"
    : lowered.includes("track")
    ? "status-on-track"
    : "bg-slate-100 text-slate-700 ring-1 ring-slate-200";

  return <span className={`supply-pill ${className}`}>{value}</span>;
}

function ExposureMiniCard({
  title,
  level,
  summary,
}: {
  title: string;
  level: string;
  summary: string;
}) {
  return (
    <div className="supply-card p-5">
      <div className="flex items-center justify-between gap-3">
        <h3 className="font-bold text-slate-950">{title}</h3>
        <StatusPill value={level} />
      </div>
      <p className="mt-3 line-clamp-4 text-sm leading-6 text-slate-600">
        {summary}
      </p>
    </div>
  );
}