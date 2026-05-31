"use client";

import { PipelineResult } from "@/lib/types";

type Props = {
  result: PipelineResult;
};

export function EvidencePanel({ result }: Props) {
  const evidenceGroups = [
    {
      title: "Geopolitical Evidence",
      result: result.geoResult,
    },
    {
      title: "Trade / Tariff Evidence",
      result: result.tradeResult,
    },
    {
      title: "Route / Logistics Evidence",
      result: result.routeResult,
    },
  ];

  return (
    <div className="space-y-6">
      <section className="supply-card p-5">
        <h2 className="text-xl font-bold text-slate-950">
          Evidence & Source Quality
        </h2>
        <p className="mt-2 text-sm text-slate-500">
          Bright Data search results are filtered into evidence packs before LLM assessment.
        </p>

        <div className="mt-5 grid gap-4 md:grid-cols-3">
          {evidenceGroups.map((group) => {
            const summary = group.result?.sourceQuality?.summary;
            return (
              <div key={group.title} className="rounded-2xl bg-slate-50 p-4">
                <div className="font-semibold text-slate-950">{group.title}</div>
                <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                  <Metric label="Raw" value={summary?.rawResultCount ?? 0} />
                  <Metric label="Trusted" value={summary?.trustedCount ?? 0} />
                  <Metric label="Usable" value={summary?.usableCount ?? 0} />
                  <Metric label="Ready" value={summary?.evidenceReadyCount ?? 0} />
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {evidenceGroups.map((group) => (
        <section key={group.title} className="supply-card overflow-hidden">
          <div className="border-b border-slate-200 p-5">
            <h3 className="font-bold text-slate-950">{group.title}</h3>
            <p className="mt-1 text-sm text-slate-500">
              Query: {group.result?.brightDataSearch?.query || "Not available"}
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500">
                    Rank
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500">
                    Source
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500">
                    Category
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500">
                    Evidence Summary
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500">
                    Relevance
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {(group.result?.evidenceUsed || []).map((source, index) => (
                  <tr key={`${group.title}-${index}`}>
                    <td className="px-4 py-4 text-slate-700">{source.rank}</td>
                    <td className="px-4 py-4">
                      <a
                        href={source.sourceUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="font-semibold text-violet-700 hover:underline"
                      >
                        {source.sourceTitle || source.sourceDomain}
                      </a>
                      <div className="text-xs text-slate-500">
                        {source.sourceDomain}
                      </div>
                    </td>
                    <td className="px-4 py-4 text-slate-700">
                      {source.sourceCategory}
                    </td>
                    <td className="max-w-md px-4 py-4 text-slate-700">
                      {source.evidenceSummary}
                    </td>
                    <td className="max-w-md px-4 py-4 text-slate-700">
                      {source.relevanceReason}
                    </td>
                  </tr>
                ))}

                {(group.result?.evidenceUsed || []).length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                      No evidence available yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      ))}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="text-xl font-bold text-slate-950">{value}</div>
      <div className="text-xs text-slate-500">{label}</div>
    </div>
  );
}