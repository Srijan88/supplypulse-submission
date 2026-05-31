"use client";

import { useState } from "react";
import { GeoResult, PipelineResult, RouteResult, TradeResult } from "@/lib/types";

type Tab = "geo" | "trade" | "route";

type Props = {
  result: PipelineResult;
};

export function ExposureWorkspace({ result }: Props) {
  const [tab, setTab] = useState<Tab>("geo");

  return (
    <div className="space-y-6">
      <div className="supply-card p-2">
        <div className="grid gap-2 md:grid-cols-3">
          <TabButton
            label="Geopolitical Exposure"
            selected={tab === "geo"}
            onClick={() => setTab("geo")}
          />
          <TabButton
            label="Trade / Tariff Exposure"
            selected={tab === "trade"}
            onClick={() => setTab("trade")}
          />
          <TabButton
            label="Route / Logistics Exposure"
            selected={tab === "route"}
            onClick={() => setTab("route")}
          />
        </div>
      </div>

      {tab === "geo" && <GeoPanel data={result.geoResult} />}
      {tab === "trade" && <TradePanel data={result.tradeResult} />}
      {tab === "route" && <RoutePanel data={result.routeResult} />}
    </div>
  );
}

function TabButton({
  label,
  selected,
  onClick,
}: {
  label: string;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={[
        "rounded-2xl px-4 py-3 text-sm font-semibold transition",
        selected
          ? "bg-violet-600 text-white shadow-sm"
          : "text-slate-600 hover:bg-slate-50",
      ].join(" ")}
    >
      {label}
    </button>
  );
}

function GeoPanel({ data }: { data?: GeoResult }) {
  return (
    <ExposurePanel
      title="Geopolitical Exposure"
      level={data?.geoExposureLevel}
      summary={data?.geoExposureSummary}
      affectedItems={data?.affectedItems || []}
      findings={data?.keyFindings || []}
      actions={data?.recommendedActions || []}
      limitations={data?.limitations}
      reasonKey="geoExposureReason"
    />
  );
}

function TradePanel({ data }: { data?: TradeResult }) {
  return (
    <ExposurePanel
      title="Trade / Tariff Exposure"
      level={data?.tradeExposureLevel}
      summary={data?.tradeExposureSummary}
      affectedItems={data?.affectedItems || []}
      findings={data?.keyFindings || []}
      actions={data?.recommendedActions || []}
      limitations={data?.limitations}
      reasonKey="tradeExposureReason"
    />
  );
}

function RoutePanel({ data }: { data?: RouteResult }) {
  return (
    <ExposurePanel
      title="Route / Logistics Exposure"
      level={data?.routeExposureLevel}
      summary={data?.routeExposureSummary}
      affectedItems={data?.affectedItems || []}
      findings={data?.keyFindings || []}
      actions={data?.recommendedActions || []}
      limitations={data?.limitations}
      reasonKey="routeExposureReason"
    />
  );
}

function ExposurePanel({
  title,
  level,
  summary,
  affectedItems,
  findings,
  actions,
  limitations,
  reasonKey,
}: {
  title: string;
  level?: string;
  summary?: string;
  affectedItems: Array<Record<string, unknown>>;
  findings: string[];
  actions: string[];
  limitations?: string;
  reasonKey: string;
}) {
  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_420px]">
      <section className="supply-card p-5">
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-950">{title}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              {summary || "This analysis has not been run yet."}
            </p>
          </div>
          <span className="rounded-full bg-violet-50 px-4 py-2 text-sm font-semibold text-violet-700 ring-1 ring-violet-100">
            {level || "Not Run"}
          </span>
        </div>

        <div className="mt-6">
          <h3 className="font-bold text-slate-950">Affected Items</h3>
          <div className="mt-3 space-y-3">
            {affectedItems.length === 0 ? (
              <EmptyState text="No affected items available." />
            ) : (
              affectedItems.map((item, index) => (
                <div key={index} className="rounded-2xl border border-slate-200 p-4">
                  <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                    <div>
                      <div className="font-bold text-slate-950">
                        {String(item.equipmentCode || "Unknown Item")}
                      </div>
                      <div className="text-sm text-slate-500">
                        {String(item.equipmentName || "")}
                      </div>
                    </div>
                    <div className="text-sm font-semibold text-slate-700">
                      {Number(item.scheduleExposurePercentage || 0).toFixed(2)}%
                    </div>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-slate-600">
                    {String(item[reasonKey] || "No reason available.")}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      </section>

      <aside className="space-y-4">
        <SideList title="Key Findings" values={findings} />
        <SideList title="Recommended Actions" values={actions} />
        <div className="supply-card p-5">
          <h3 className="font-bold text-slate-950">Limitations</h3>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            {limitations || "No limitations available."}
          </p>
        </div>
      </aside>
    </div>
  );
}

function SideList({ title, values }: { title: string; values: string[] }) {
  return (
    <div className="supply-card p-5">
      <h3 className="font-bold text-slate-950">{title}</h3>
      <div className="mt-3 space-y-3">
        {values.length === 0 ? (
          <EmptyState text="No data available." />
        ) : (
          values.map((value, index) => (
            <div key={index} className="rounded-xl bg-slate-50 p-3 text-sm text-slate-700">
              {value}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">{text}</div>;
}