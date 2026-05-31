"use client";

import { useEffect, useState } from "react";
import { AskSupplyPulse } from "@/components/AskSupplyPulse";
import { AuditTrail } from "@/components/AuditTrail";
import { ControlTower } from "@/components/ControlTower";
import { EvidencePanel } from "@/components/EvidencePanel";
import { ExposureWorkspace } from "@/components/ExposureWorkspace";
import { LoginScreen } from "@/components/LoginScreen";
import { ReportsPanel } from "@/components/ReportsPanel";
import { SupplyMap } from "@/components/SupplyMap";
import {
  Shell,
  SupplyPulseConnectionStatus,
  SupplyPulseTab,
} from "@/components/Shell";
import { runSupplyPulsePipeline } from "@/lib/api";
import { createSamplePipelineResult } from "@/lib/sampleData";
import { EquipmentItem, PipelineResult } from "@/lib/types";

export default function Home() {
  const [isAuthChecked, setIsAuthChecked] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const [activeTab, setActiveTab] = useState<SupplyPulseTab>("ask");
  const [connectionStatus, setConnectionStatus] =
    useState<SupplyPulseConnectionStatus>("sample");

  const [result, setResult] = useState<PipelineResult>(() =>
    createSamplePipelineResult(
      "Give me complete external exposure analysis for high schedule exposure items including geopolitical, trade tariff, and route logistics exposure."
    )
  );

  const [isRunning, setIsRunning] = useState(false);
  const [selectedItem, setSelectedItem] = useState<EquipmentItem | null>(null);

  useEffect(() => {
    const savedAuth = localStorage.getItem("supplypulse_demo_auth") === "true";
    setIsAuthenticated(savedAuth);
    setIsAuthChecked(true);

    if (savedAuth) {
      setActiveTab("ask");
    }
  }, []);

  function handleLogin() {
    setIsAuthenticated(true);
    setActiveTab("ask");
  }

  async function handleRun(question: string) {
    setIsRunning(true);
    setConnectionStatus("running");

    try {
      const pipelineResult = await runSupplyPulsePipeline(question);

      setResult(pipelineResult);

      if (pipelineResult.responseSource === "backend") {
        setConnectionStatus("connected");
      } else {
        setConnectionStatus("sample");
      }

      setActiveTab("ask");
    } finally {
      setIsRunning(false);
    }
  }

  if (!isAuthChecked) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="rounded-3xl bg-white px-6 py-4 text-sm font-semibold text-slate-600 shadow-sm ring-1 ring-slate-200">
          Loading SupplyPulse...
        </div>
      </main>
    );
  }

  if (!isAuthenticated) {
    return <LoginScreen onLogin={handleLogin} />;
  }

  return (
    <Shell
      activeTab={activeTab}
      connectionStatus={connectionStatus}
      onTabChange={setActiveTab}
    >
      {activeTab === "ask" && (
        <AskSupplyPulse
          result={result}
          isRunning={isRunning}
          onRun={handleRun}
          onNavigate={setActiveTab}
        />
      )}

      {activeTab === "control" && (
        <ControlTower result={result} onSelectItem={setSelectedItem} />
      )}

      {activeTab === "map" && <SupplyMap result={result} />}

      {activeTab === "exposure" && <ExposureWorkspace result={result} />}

      {activeTab === "evidence" && <EvidencePanel result={result} />}

      {activeTab === "reports" && <ReportsPanel result={result} />}

      {activeTab === "audit" && <AuditTrail result={result} />}

      {selectedItem && (
        <ItemDrawer item={selectedItem} onClose={() => setSelectedItem(null)} />
      )}
    </Shell>
  );
}

function ItemDrawer({
  item,
  onClose,
}: {
  item: EquipmentItem;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-40">
      <button
        className="absolute inset-0 bg-slate-950/30"
        onClick={onClose}
        aria-label="Close item drawer"
      />
      <aside className="absolute right-0 top-0 h-full w-full max-w-xl overflow-auto bg-white p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="text-sm font-semibold text-violet-700">
              {item.equipmentCode}
            </div>
            <h2 className="mt-1 text-2xl font-bold text-slate-950">
              {item.equipmentName}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-full bg-slate-100 px-3 py-1.5 text-sm font-semibold text-slate-600 hover:bg-slate-200"
          >
            Close
          </button>
        </div>

        <div className="mt-6 grid gap-3">
          <Detail label="Planned Need Date" value={item.baselineDueDate} />
          <Detail
            label="Forecast Arrival"
            value={item.latestExpectedDeliveryDate}
          />
          <Detail label="Delay / Gain" value={`${item.delayDays ?? 0} days`} />
          <Detail
            label="Schedule Exposure %"
            value={`${(item.scheduleRiskPercentage ?? 0).toFixed(2)}%`}
          />
          <Detail label="Status Band" value={item.scheduleRiskLevel} />
          <Detail label="Source Country" value={item.originCountry} />
          <Detail label="Destination Country" value={item.projectCountry} />
        </div>

        <div className="mt-6 rounded-2xl bg-violet-50 p-5 text-sm leading-6 text-violet-900">
          Schedule Exposure % is a delay-pressure index, not a probability.
          Values can exceed 100% when the forecast delay is larger than the time
          remaining before the planned need date.
        </div>
      </aside>
    </div>
  );
}

function Detail({
  label,
  value,
}: {
  label: string;
  value?: string | number;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 p-4">
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className="mt-1 font-semibold text-slate-950">
        {value || "Not available"}
      </div>
    </div>
  );
}