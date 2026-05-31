"use client";

import { PipelineResult } from "@/lib/types";

type Props = {
  result: PipelineResult;
};

export function AuditTrail({ result }: Props) {
  const audit = result.pipelineAudit;
  const counts = audit?.agentAuditCounts || {};
  const timeline = audit?.stageTimeline || [];

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-3">
        <AuditCard
          label="Total Audit Logs"
          value={audit?.totalAuditLogs ?? 0}
        />
        <AuditCard
          label="Shared Run ID"
          value={audit?.sharedContextCheck?.allOutputsShareRunId ? "Passed" : "Unknown"}
        />
        <AuditCard
          label="Run ID"
          value={audit?.sharedContextCheck?.expectedRunId || "Not available"}
        />
      </section>

      <section className="supply-card p-5">
        <h2 className="text-xl font-bold text-slate-950">Agent Audit Counts</h2>
        <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {Object.entries(counts).map(([agent, count]) => (
            <div key={agent} className="rounded-2xl bg-slate-50 p-4">
              <div className="text-sm font-semibold text-slate-950">{agent}</div>
              <div className="mt-2 text-2xl font-bold text-violet-700">
                {count}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="supply-card p-5">
        <h2 className="text-xl font-bold text-slate-950">Stage Timeline</h2>
        <div className="mt-5 space-y-3">
          {timeline.length === 0 ? (
            <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">
              No stage timeline available yet.
            </div>
          ) : (
            timeline.map((item, index) => (
              <div
                key={`${item.agentName}-${item.stage}-${index}`}
                className="flex gap-4 rounded-2xl border border-slate-200 p-4"
              >
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-violet-600 text-sm font-bold text-white">
                  {index + 1}
                </div>
                <div>
                  <div className="font-semibold text-slate-950">
                    {item.agentName}
                  </div>
                  <div className="text-sm text-slate-500">
                    {item.sourceName} / {item.stage}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </section>

      <section className="supply-card p-5">
        <h2 className="text-xl font-bold text-slate-950">
          Evidence Search Summary
        </h2>
        <div className="mt-5 space-y-3">
          {(audit?.evidenceSearchSummary || []).map((event, index) => (
            <pre
              key={index}
              className="overflow-auto rounded-2xl bg-slate-950 p-4 text-xs leading-6 text-slate-100"
            >
              {JSON.stringify(event, null, 2)}
            </pre>
          ))}
        </div>
      </section>
    </div>
  );
}

function AuditCard({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="supply-card p-5">
      <div className="text-2xl font-bold text-slate-950">{value}</div>
      <div className="mt-1 text-sm text-slate-500">{label}</div>
    </div>
  );
}