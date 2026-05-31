"use client";

import {
  ArrowRight,
  BarChart3,
  Bot,
  CheckCircle2,
  Clock3,
  Database,
  FileText,
  Loader2,
  MapPinned,
  Radar,
  Send,
  ShieldCheck,
  Sparkles,
  User,
  Zap,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import type { PipelineResult } from "@/lib/types";
import type { SupplyPulseTab } from "@/components/Shell";

type Props = {
  result: PipelineResult;
  isRunning: boolean;
  onRun: (question: string) => Promise<void>;
  onNavigate: (tab: SupplyPulseTab) => void;
};

type AgentStep = {
  id: string;
  label: string;
  helper: string;
};

const quickPrompts = [
  "Analyze schedule exposure for all tracked delivery items.",
  "What geopolitical exposure affects high schedule exposure items?",
  "What trade tariff exposure affects high schedule exposure items?",
  "What route logistics exposure affects high schedule exposure items?",
  "Give me complete external exposure analysis for high schedule exposure items including geopolitical, trade tariff, and route logistics exposure.",
];

const company = {
  name: "NorthBridge Energy Infrastructure",
  program: "Singapore Data Center Phase 2",
  scope:
    "Equipment delivery records, planned need dates, forecast arrivals, source and destination countries, and external exposure queries are available for analysis.",
};

export function AskSupplyPulse({
  result,
  isRunning,
  onRun,
  onNavigate,
}: Props) {
  const [question, setQuestion] = useState(quickPrompts[4]);
  const [submittedQuestion, setSubmittedQuestion] = useState<string>("");
  const [progress, setProgress] = useState(0);
  const [startedAt, setStartedAt] = useState<Date | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  const activeQuestion =
    submittedQuestion || result.userQuestion || question || quickPrompts[4];

  const plannedSteps = useMemo(
    () => buildPlannedSteps(activeQuestion, result),
    [activeQuestion, result]
  );

  useEffect(() => {
    if (!isRunning) {
      setProgress((current) => {
        if (current > 0 && current < 100) {
          return 100;
        }

        return current;
      });

      return;
    }

    setProgress(6);
    setElapsedSeconds(0);

    const progressTimer = window.setInterval(() => {
      setProgress((current) => {
        if (current >= 92) {
          return current;
        }

        if (current < 25) {
          return current + 8;
        }

        if (current < 55) {
          return current + 6;
        }

        return current + 3;
      });
    }, 1300);

    const elapsedTimer = window.setInterval(() => {
      setElapsedSeconds((current) => current + 1);
    }, 1000);

    return () => {
      window.clearInterval(progressTimer);
      window.clearInterval(elapsedTimer);
    };
  }, [isRunning]);

  async function handleRun() {
    if (!question.trim() || isRunning) {
      return;
    }

    setSubmittedQuestion(question.trim());
    setStartedAt(new Date());
    setElapsedSeconds(0);
    setProgress(4);

    await onRun(question.trim());
  }

  const elapsedText = startedAt ? formatElapsed(elapsedSeconds) : "Not started";
  const hasCompletedRun = Boolean(result.lastRunAt && !isRunning);

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
      <section className="space-y-5">
        <div className="supply-card overflow-hidden border-violet-100">
          <div className="border-b border-slate-200 bg-gradient-to-r from-white via-violet-50/70 to-indigo-50/70 p-5">
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div className="flex items-start gap-3">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-3xl bg-gradient-to-br from-violet-600 to-indigo-600 text-white shadow-lg shadow-violet-200">
                  <Bot size={22} />
                </div>

                <div>
                  <div className="inline-flex items-center gap-2 rounded-full bg-white px-3 py-1 text-xs font-black text-violet-700 ring-1 ring-violet-100">
                    <Sparkles size={13} />
                    Workspace dataset connected
                  </div>

                  <h2 className="mt-3 text-2xl font-black tracking-tight text-slate-950">
                    Ask SupplyPulse
                  </h2>

                  <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
                    Ask about schedule exposure, geopolitical exposure, trade /
                    tariff exposure, route / logistics exposure, evidence,
                    reports, or audit trail. Full external analysis usually
                    takes <strong>1–2 minutes</strong>.
                  </p>
                </div>
              </div>

              <div className="rounded-3xl border border-violet-100 bg-white/80 p-4 shadow-sm md:w-80">
                <div className="text-xs font-black uppercase tracking-wide text-slate-400">
                  Active workspace
                </div>
                <div className="mt-2 text-sm font-black text-slate-950">
                  {company.name}
                </div>
                <div className="mt-1 text-xs leading-5 text-slate-500">
                  {company.program}
                </div>
              </div>
            </div>
          </div>

          <div className="max-h-[620px] space-y-5 overflow-auto bg-gradient-to-b from-slate-50 to-white p-5">
            <AssistantMessage>
              <div className="flex items-center gap-2 font-black text-slate-950">
                <Zap size={17} className="text-violet-600" />
                Welcome to SupplyPulse
              </div>

              <p className="mt-2 text-sm leading-6 text-slate-600">
                SupplyPulse is connected to the{" "}
                <strong>{company.name}</strong> workspace for the{" "}
                <strong>{company.program}</strong> program. {company.scope}
              </p>

              <div className="mt-4 grid gap-3 md:grid-cols-3">
                <InfoChip label="Tracked Items" value="20" />
                <InfoChip label="Program" value="Singapore DC Phase 2" />
                <InfoChip label="Mode" value="Evidence-backed" />
              </div>
            </AssistantMessage>

            {submittedQuestion && (
              <UserMessage>{submittedQuestion}</UserMessage>
            )}

            {isRunning && (
              <AssistantMessage>
                <RunningPipeline
                  progress={progress}
                  elapsedText={elapsedText}
                  steps={plannedSteps}
                />
              </AssistantMessage>
            )}

            {hasCompletedRun && (
              <AssistantMessage>
                <CompletedResponse result={result} onNavigate={onNavigate} />
              </AssistantMessage>
            )}
          </div>

          <div className="border-t border-slate-200 bg-white p-5">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <div className="text-sm font-black text-slate-950">
                  Suggested questions
                </div>
                <div className="text-xs text-slate-500">
                  Choose one or write your own question.
                </div>
              </div>
            </div>

            <div className="grid gap-2">
              {quickPrompts.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => setQuestion(prompt)}
                  disabled={isRunning}
                  className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-left text-sm text-slate-700 transition hover:border-violet-200 hover:bg-violet-50 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {prompt}
                </button>
              ))}
            </div>

            <div className="mt-4 flex flex-col gap-3 rounded-3xl border border-slate-200 bg-slate-50 p-3 md:flex-row md:items-end">
              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                rows={4}
                disabled={isRunning}
                className="min-h-28 flex-1 resize-none rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none ring-violet-200 focus:ring-4 disabled:cursor-not-allowed disabled:bg-slate-50"
                placeholder="Ask about schedule, geo, trade, route, evidence, reports, or audit trail..."
              />

              <button
                disabled={isRunning || !question.trim()}
                onClick={handleRun}
                className="inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-violet-600 to-indigo-600 px-5 py-3 text-sm font-black text-white shadow-lg shadow-violet-200 transition hover:from-violet-700 hover:to-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isRunning ? (
                  <Loader2 className="animate-spin" size={18} />
                ) : (
                  <Send size={18} />
                )}
                {isRunning ? "Running..." : "Run Analysis"}
              </button>
            </div>
          </div>
        </div>
      </section>

      <aside className="space-y-5">
        <LatestRunCard result={result} isRunning={isRunning} />
        <AgentPlanCard steps={plannedSteps} progress={progress} />
      </aside>
    </div>
  );
}

function InfoChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-slate-50 p-3 ring-1 ring-slate-100">
      <div className="text-xs font-bold uppercase tracking-wide text-slate-400">
        {label}
      </div>
      <div className="mt-1 text-sm font-black text-slate-950">{value}</div>
    </div>
  );
}

function AssistantMessage({ children }: { children: ReactNode }) {
  return (
    <div className="flex items-start gap-3">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-600 to-indigo-600 text-white shadow-md shadow-violet-100">
        <Bot size={18} />
      </div>
      <div className="max-w-5xl rounded-3xl rounded-tl-md bg-white p-5 shadow-sm ring-1 ring-slate-200">
        {children}
      </div>
    </div>
  );
}

function UserMessage({ children }: { children: ReactNode }) {
  return (
    <div className="flex justify-end">
      <div className="flex max-w-3xl items-start gap-3">
        <div className="rounded-3xl rounded-tr-md bg-gradient-to-r from-violet-600 to-indigo-600 p-5 text-sm leading-6 text-white shadow-lg shadow-violet-100">
          {children}
        </div>
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-slate-900 text-white">
          <User size={17} />
        </div>
      </div>
    </div>
  );
}

function RunningPipeline({
  progress,
  elapsedText,
  steps,
}: {
  progress: number;
  elapsedText: string;
  steps: AgentStep[];
}) {
  const activeIndex = Math.min(
    steps.length - 1,
    Math.floor((progress / 100) * steps.length)
  );

  return (
    <div>
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="text-lg font-black text-slate-950">
            Running backend pipeline
          </div>
          <p className="mt-1 text-sm leading-6 text-slate-500">
            This usually takes 1–2 minutes. SupplyPulse is routing the question,
            checking delivery exposure, searching evidence, filtering sources,
            and preparing a traceable report.
          </p>
        </div>

        <div className="inline-flex items-center gap-2 rounded-full bg-amber-50 px-3 py-1.5 text-xs font-black text-amber-700 ring-1 ring-amber-100">
          <Clock3 size={14} />
          {elapsedText}
        </div>
      </div>

      <div className="mt-5">
        <div className="mb-2 flex items-center justify-between text-xs font-black text-slate-500">
          <span>Agent progress</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="h-3 overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-gradient-to-r from-violet-600 to-indigo-600 transition-all duration-700"
            style={{ width: `${Math.min(progress, 100)}%` }}
          />
        </div>
      </div>

      <div className="mt-5 grid gap-3">
        {steps.map((step, index) => {
          const isDone = progress >= ((index + 1) / steps.length) * 100;
          const isActive = index === activeIndex && !isDone;

          return (
            <div
              key={step.id}
              className={[
                "flex gap-3 rounded-2xl border p-4 transition",
                isDone
                  ? "border-emerald-200 bg-emerald-50"
                  : isActive
                    ? "border-violet-200 bg-violet-50"
                    : "border-slate-200 bg-white",
              ].join(" ")}
            >
              <div
                className={[
                  "mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-black",
                  isDone
                    ? "bg-emerald-600 text-white"
                    : isActive
                      ? "bg-violet-600 text-white"
                      : "bg-slate-100 text-slate-400",
                ].join(" ")}
              >
                {isDone ? (
                  <CheckCircle2 size={16} />
                ) : isActive ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  index + 1
                )}
              </div>

              <div>
                <div className="text-sm font-black text-slate-950">
                  {step.label}
                </div>
                <div className="mt-1 text-xs leading-5 text-slate-500">
                  {step.helper}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function CompletedResponse({
  result,
  onNavigate,
}: {
  result: PipelineResult;
  onNavigate: (tab: SupplyPulseTab) => void;
}) {
  const sourceText =
    result.responseSource === "backend"
      ? "Backend run completed successfully."
      : "Local preview response shown because backend was unavailable.";

  const totalLogs = result.pipelineAudit?.totalAuditLogs ?? 0;
  const geoLevel = result.geoResult?.geoExposureLevel || "Not Run";
  const tradeLevel = result.tradeResult?.tradeExposureLevel || "Not Run";
  const routeLevel = result.routeResult?.routeExposureLevel || "Not Run";

  return (
    <div>
      <div className="flex items-center gap-2 text-lg font-black text-slate-950">
        <ShieldCheck size={20} className="text-emerald-600" />
        Analysis ready
      </div>

      <p className="mt-2 text-sm leading-6 text-slate-600">{sourceText}</p>

      <div className="mt-4 grid gap-3 md:grid-cols-4">
        <MiniResult label="Audit Logs" value={String(totalLogs)} />
        <MiniResult label="Geo" value={geoLevel} />
        <MiniResult label="Trade" value={tradeLevel} />
        <MiniResult label="Route" value={routeLevel} />
      </div>

      <div className="mt-5 rounded-3xl bg-gradient-to-br from-slate-50 to-violet-50/50 p-5 ring-1 ring-slate-100">
        <div className="text-xs font-black uppercase tracking-wide text-slate-500">
          Executive Summary
        </div>
        <p className="mt-2 text-sm leading-6 text-slate-700">
          {result.reportResult?.executiveSummary ||
            "The pipeline completed. Open the linked workspaces below to review schedule exposure, external evidence, report output, and audit trail."}
        </p>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-2">
        <NavigationCard
          title="Open Control Tower"
          helper="View the Delivery Exposure Table and KPI cards."
          icon={<BarChart3 size={18} />}
          onClick={() => onNavigate("control")}
        />
        <NavigationCard
          title="Open Supply Map"
          helper="Explore source countries, destination countries, and route exposure."
          icon={<MapPinned size={18} />}
          onClick={() => onNavigate("map")}
        />
        <NavigationCard
          title="Open Exposure Workspace"
          helper="Review Geo, Trade, and Route exposure tabs."
          icon={<Radar size={18} />}
          onClick={() => onNavigate("exposure")}
        />
        <NavigationCard
          title="Open Evidence"
          helper="Inspect Bright Data evidence and source quality."
          icon={<Database size={18} />}
          onClick={() => onNavigate("evidence")}
        />
        <NavigationCard
          title="Open Reports"
          helper="Preview or download the report."
          icon={<FileText size={18} />}
          onClick={() => onNavigate("reports")}
        />
        <NavigationCard
          title="Open Audit Trail"
          helper="Trace every agent stage and shared run ID."
          icon={<ShieldCheck size={18} />}
          onClick={() => onNavigate("audit")}
        />
      </div>
    </div>
  );
}

function MiniResult({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-slate-50 p-4 ring-1 ring-slate-100">
      <div className="text-lg font-black text-slate-950">{value}</div>
      <div className="text-xs text-slate-500">{label}</div>
    </div>
  );
}

function NavigationCard({
  title,
  helper,
  icon,
  onClick,
}: {
  title: string;
  helper: string;
  icon: ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="group flex items-start justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-4 text-left transition hover:border-violet-200 hover:bg-violet-50"
    >
      <div className="flex gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-violet-50 text-violet-700">
          {icon}
        </div>
        <div>
          <div className="text-sm font-black text-slate-950">{title}</div>
          <div className="mt-1 text-xs leading-5 text-slate-500">{helper}</div>
        </div>
      </div>
      <ArrowRight
        size={17}
        className="mt-1 text-slate-400 transition group-hover:translate-x-0.5 group-hover:text-violet-700"
      />
    </button>
  );
}

function LatestRunCard({
  result,
  isRunning,
}: {
  result: PipelineResult;
  isRunning: boolean;
}) {
  const agents = result.executedRiskAgents || [];
  const totalLogs = result.pipelineAudit?.totalAuditLogs ?? 0;
  const sharedRun = result.pipelineAudit?.sharedContextCheck?.allOutputsShareRunId;

  return (
    <div className="supply-card p-5">
      <div className="flex items-center justify-between gap-3">
        <h3 className="font-black text-slate-950">Latest Run</h3>
        {isRunning && (
          <Loader2 size={18} className="animate-spin text-amber-600" />
        )}
      </div>

      <div className="mt-4 rounded-3xl bg-slate-50 p-4 ring-1 ring-slate-100">
        <div className="text-xs font-black uppercase tracking-wide text-slate-500">
          User Question
        </div>
        <div className="mt-2 text-sm leading-6 text-slate-800">
          {result.userQuestion || "No backend run completed yet."}
        </div>
      </div>

      <div className="mt-4">
        <div className="text-xs font-black uppercase tracking-wide text-slate-500">
          Executed Risk Agents
        </div>
        <div className="mt-3 space-y-2">
          {agents.length === 0 ? (
            <div className="rounded-xl bg-slate-50 px-3 py-2 text-xs text-slate-500">
              Agents will appear after the run completes.
            </div>
          ) : (
            agents.map((agent) => (
              <div
                key={agent}
                className="rounded-xl bg-violet-50 px-3 py-2 text-xs font-black text-violet-700"
              >
                {agent}
              </div>
            ))
          )}
        </div>
      </div>

      <div className="mt-5">
        <div className="text-xs font-black uppercase tracking-wide text-slate-500">
          Pipeline Audit
        </div>
        <div className="mt-3 grid grid-cols-2 gap-3">
          <Metric label="Total Logs" value={totalLogs} />
          <Metric label="Shared Run" value={sharedRun ? "Yes" : "No"} />
        </div>
      </div>
    </div>
  );
}

function AgentPlanCard({
  steps,
  progress,
}: {
  steps: AgentStep[];
  progress: number;
}) {
  return (
    <div className="supply-card p-5">
      <h3 className="font-black text-slate-950">Agent Plan</h3>
      <p className="mt-1 text-sm leading-6 text-slate-500">
        SupplyPulse shows the expected pipeline before the backend response
        returns.
      </p>

      <div className="mt-4 space-y-3">
        {steps.map((step, index) => {
          const isDone = progress >= ((index + 1) / steps.length) * 100;

          return (
            <div key={step.id} className="flex gap-3">
              <div
                className={[
                  "flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-black",
                  isDone
                    ? "bg-emerald-600 text-white"
                    : "bg-slate-100 text-slate-500",
                ].join(" ")}
              >
                {index + 1}
              </div>
              <div>
                <div className="text-sm font-black text-slate-950">
                  {step.label}
                </div>
                <div className="text-xs leading-5 text-slate-500">
                  {step.helper}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-2xl bg-slate-50 p-4 ring-1 ring-slate-100">
      <div className="text-2xl font-black text-slate-950">{value}</div>
      <div className="text-xs text-slate-500">{label}</div>
    </div>
  );
}

function buildPlannedSteps(
  question: string,
  result: PipelineResult
): AgentStep[] {
  const lowered = question.toLowerCase();

  const steps: AgentStep[] = [
    {
      id: "router",
      label: "Router Agent",
      helper: "Classifies the question and chooses the downstream agents.",
    },
    {
      id: "schedule",
      label: "Schedule Analyzer Agent",
      helper:
        "Reads loaded delivery data, calculates Schedule Exposure %, and identifies High status band items.",
    },
  ];

  const executedAgents = result.executedRiskAgents || [];

  const asksAll =
    lowered.includes("complete") ||
    lowered.includes("all external") ||
    lowered.includes("geopolitical, trade") ||
    lowered.includes("geo, trade") ||
    executedAgents.length >= 3;

  const asksGeo =
    asksAll ||
    lowered.includes("geo") ||
    lowered.includes("political") ||
    executedAgents.includes("GEO_RISK_ANALYST_AGENT");

  const asksTrade =
    asksAll ||
    lowered.includes("trade") ||
    lowered.includes("tariff") ||
    lowered.includes("customs") ||
    executedAgents.includes("TRADE_RISK_ANALYST_AGENT");

  const asksRoute =
    asksAll ||
    lowered.includes("route") ||
    lowered.includes("logistics") ||
    lowered.includes("port") ||
    executedAgents.includes("ROUTE_RISK_ANALYST_AGENT");

  if (asksGeo) {
    steps.push({
      id: "geo",
      label: "Geo Risk Analyst Agent",
      helper:
        "Runs Bright Data search, filters sources, and assesses geopolitical exposure.",
    });
  }

  if (asksTrade) {
    steps.push({
      id: "trade",
      label: "Trade Risk Analyst Agent",
      helper:
        "Searches tariff and customs evidence, checks trade agreements, and assesses trade exposure.",
    });
  }

  if (asksRoute) {
    steps.push({
      id: "route",
      label: "Route Risk Analyst Agent",
      helper:
        "Searches route, port, congestion, and logistics evidence for affected items.",
    });
  }

  steps.push({
    id: "report",
    label: "Report Builder Agent",
    helper:
      "Combines schedule, external exposure, evidence, recommendations, limitations, and audit context.",
  });

  return steps;
}

function formatElapsed(seconds: number) {
  if (seconds < 60) {
    return `${seconds}s elapsed`;
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  return `${minutes}m ${remainingSeconds}s elapsed`;
}