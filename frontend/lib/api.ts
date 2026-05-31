import { createSamplePipelineResult } from "./sampleData";
import { PipelineResult } from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_SUPPLYPULSE_API_BASE || "http://127.0.0.1:8000";

export async function runSupplyPulsePipeline(
  question: string
): Promise<PipelineResult> {
  try {
    const response = await fetch(`${API_BASE}/api/pipeline/run`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }

    const data = await response.json();
    const normalized = normalizePipelineResult(data, question);

    return {
      ...normalized,
      responseSource: "backend",
      lastRunAt: new Date().toISOString(),
    };
  } catch (error) {
    console.warn(
      "Using sample SupplyPulse data because backend is unavailable.",
      error
    );

    return {
      ...createSamplePipelineResult(question),
      responseSource: "sample",
      lastRunAt: new Date().toISOString(),
    };
  }
}

function normalizePipelineResult(
  data: unknown,
  question: string
): PipelineResult {
  const value = data as Record<string, unknown>;

  if (value.pipelineResult && typeof value.pipelineResult === "object") {
    const pipelineResult = value.pipelineResult as PipelineResult;

    return {
      ...pipelineResult,
      userQuestion: pipelineResult.userQuestion || question,
    };
  }

  if (value.result && typeof value.result === "object") {
    const result = value.result as PipelineResult;

    return {
      ...result,
      userQuestion: result.userQuestion || question,
    };
  }

  return {
    ...(value as PipelineResult),
    userQuestion: (value.userQuestion as string) || question,
  };
}