"use client";

import {
  Activity,
  BarChart3,
  Bot,
  ClipboardList,
  Database,
  FileText,
  Loader2,
  Map as MapIcon,
  Radar,
} from "lucide-react";
import type { ReactNode } from "react";

export type SupplyPulseTab =
  | "ask"
  | "control"
  | "map"
  | "exposure"
  | "evidence"
  | "reports"
  | "audit";

export type SupplyPulseConnectionStatus =
  | "sample"
  | "running"
  | "connected";

type ShellProps = {
  activeTab: SupplyPulseTab;
  connectionStatus: SupplyPulseConnectionStatus;
  onTabChange: (tab: SupplyPulseTab) => void;
  children: ReactNode;
};

const tabs = [
  {
    id: "ask" as const,
    label: "Ask SupplyPulse",
    icon: Bot,
    subtitle: "Chat with the delivery exposure assistant.",
  },
  {
    id: "control" as const,
    label: "Control Tower",
    icon: BarChart3,
    subtitle: "View schedule exposure KPIs and delivery table.",
  },
  {
    id: "map" as const,
    label: "Supply Map",
    icon: MapIcon,
    subtitle: "Explore country routes and item-level exposure.",
  },
  {
    id: "exposure" as const,
    label: "Exposure Workspace",
    icon: Radar,
    subtitle: "Review Geo, Trade, and Route exposure outputs.",
  },
  {
    id: "evidence" as const,
    label: "Evidence",
    icon: Database,
    subtitle: "Inspect evidence and source quality filtering.",
  },
  {
    id: "reports" as const,
    label: "Reports",
    icon: FileText,
    subtitle: "Preview and download generated reports.",
  },
  {
    id: "audit" as const,
    label: "Audit Trail",
    icon: ClipboardList,
    subtitle: "Trace every agent stage and shared run ID.",
  },
];

export function Shell({
  activeTab,
  connectionStatus,
  onTabChange,
  children,
}: ShellProps) {
  const activeMeta = tabs.find((tab) => tab.id === activeTab) || tabs[0];

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,#ede9fe_0,#f8fafc_34%,#f8fafc_100%)]">
      <aside className="fixed left-0 top-0 z-20 hidden h-screen w-72 border-r border-slate-200/80 bg-white/90 p-5 shadow-sm backdrop-blur lg:block">
        <div className="mb-8 flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-3xl bg-gradient-to-br from-violet-600 to-indigo-600 text-white shadow-lg shadow-violet-200">
            <Activity size={23} />
          </div>
          <div>
            <div className="text-lg font-black tracking-tight text-slate-950">
              SupplyPulse
            </div>
            <div className="text-xs text-slate-500">
              Delivery Exposure Control Tower
            </div>
          </div>
        </div>

        <nav className="space-y-2">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const selected = activeTab === tab.id;

            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={[
                  "group flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm font-semibold transition",
                  selected
                    ? "bg-gradient-to-r from-violet-50 to-indigo-50 text-violet-700 ring-1 ring-violet-100"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-950",
                ].join(" ")}
              >
                <span
                  className={[
                    "flex h-8 w-8 items-center justify-center rounded-xl transition",
                    selected
                      ? "bg-white text-violet-700 shadow-sm"
                      : "bg-slate-50 text-slate-500 group-hover:bg-white",
                  ].join(" ")}
                >
                  <Icon size={17} />
                </span>
                {tab.label}
              </button>
            );
          })}
        </nav>

        <div className="absolute bottom-5 left-5 right-5 overflow-hidden rounded-3xl border border-violet-100 bg-gradient-to-br from-violet-50 via-white to-indigo-50 p-4">
          <div className="text-sm font-bold text-slate-950">
            Company Dataset Loaded
          </div>
          <div className="mt-1 text-xs leading-5 text-slate-600">
            NorthBridge Energy Infrastructure · Singapore Data Center Phase 2
          </div>
          <div className="mt-3 flex items-center gap-2 text-xs font-semibold text-violet-700">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            Ready for analysis
          </div>
        </div>
      </aside>

      <div className="lg:pl-72">
        <header className="sticky top-0 z-10 border-b border-slate-200/80 bg-white/80 px-4 py-4 backdrop-blur-xl md:px-8">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="text-xl font-black tracking-tight text-slate-950 md:text-2xl">
                {activeMeta.label}
              </h1>
              <p className="text-sm text-slate-500">{activeMeta.subtitle}</p>
            </div>

            <ConnectionBadge status={connectionStatus} />
          </div>

          <div className="mt-4 flex gap-2 overflow-x-auto lg:hidden">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={[
                  "whitespace-nowrap rounded-full px-4 py-2 text-sm font-semibold",
                  activeTab === tab.id
                    ? "bg-violet-600 text-white"
                    : "bg-white text-slate-600 ring-1 ring-slate-200",
                ].join(" ")}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </header>

        <main className="px-4 py-6 md:px-8">{children}</main>
      </div>
    </div>
  );
}

function ConnectionBadge({
  status,
}: {
  status: SupplyPulseConnectionStatus;
}) {
  if (status === "running") {
    return (
      <div className="inline-flex items-center gap-2 rounded-full bg-amber-50 px-4 py-2 text-sm font-semibold text-amber-700 ring-1 ring-amber-100">
        <Loader2 size={16} className="animate-spin" />
        Running Backend Pipeline
      </div>
    );
  }

  if (status === "connected") {
    return (
      <div className="rounded-full bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-700 ring-1 ring-emerald-100">
        Backend Connected
      </div>
    );
  }

  return (
    <div className="rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-600 shadow-sm ring-1 ring-slate-200">
      Company Dataset Loaded
    </div>
  );
}