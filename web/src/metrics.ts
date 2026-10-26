export type CompareSide = "high" | "low" | "neutral";

export type MetricComparison = {
  a: CompareSide;
  b: CompareSide;
  delta: number | null;
};

export function compareMetric(a: number | null | undefined, b: number | null | undefined): MetricComparison {
  if (a == null || b == null || Number.isNaN(a) || Number.isNaN(b) || a === b) {
    return { a: "neutral", b: "neutral", delta: null };
  }
  const delta = Math.abs(a - b);
  if (a > b) return { a: "high", b: "low", delta };
  return { a: "low", b: "high", delta };
}

export function formatPt(value: number, fractionDigits = 0): string {
  return value.toLocaleString("pt-PT", {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });
}

export function secondsFromMs(latencyMs: number | null | undefined): number | null {
  if (latencyMs == null) return null;
  return Math.round(latencyMs / 100) / 10;
}

export function reasoningTokens(
  usage:
    | {
        prompt_tokens?: number | null;
        completion_tokens?: number | null;
        total_tokens?: number | null;
      }
    | null
    | undefined,
): number | null {
  const total = usage?.total_tokens;
  const prompt = usage?.prompt_tokens;
  const completion = usage?.completion_tokens;
  if (total == null || prompt == null || completion == null) return null;
  const value = total - prompt - completion;
  return value > 0 ? value : null;
}

export function parseCitations(visibleText: string | null | undefined): number[] {
  if (!visibleText) return [];
  const found = new Set<number>();
  const blocks = visibleText.matchAll(/\[([0-9]+(?:\s*,\s*[0-9]+)*)\]/g);
  for (const block of blocks) {
    for (const part of block[1].split(",")) {
      const index = Number(part.trim());
      if (Number.isInteger(index) && index > 0) found.add(index);
    }
  }
  return [...found].sort((left, right) => left - right);
}

export function wordCount(visibleText: string | null | undefined): number | null {
  if (visibleText == null || visibleText.trim() === "") return visibleText == null ? null : 0;
  return visibleText.trim().split(/\s+/).length;
}

export function citationLabel(indices: number[]): string {
  if (!indices.length) return "nenhuma";
  return indices.map((index) => `[${index}]`).join(", ");
}

export function buildSummary(input: {
  xaiLatencyS: number | null;
  geminiLatencyS: number | null;
  xaiTokens: number | null;
  geminiTokens: number | null;
  xaiCitations: number;
  geminiCitations: number;
}): string {
  const { xaiLatencyS, geminiLatencyS, xaiTokens, geminiTokens, xaiCitations, geminiCitations } = input;
  let subject: "xAI" | "Gemini" | null = null;
  const parts: string[] = [];

  if (xaiLatencyS != null && geminiLatencyS != null && xaiLatencyS !== geminiLatencyS) {
    subject = geminiLatencyS < xaiLatencyS ? "Gemini" : "xAI";
    parts.push(`${subject}: ${formatPt(Math.abs(geminiLatencyS - xaiLatencyS), 1)} s mais rápido`);
  }

  if (xaiTokens != null && geminiTokens != null && xaiTokens !== geminiTokens) {
    const leaner: "xAI" | "Gemini" = geminiTokens < xaiTokens ? "Gemini" : "xAI";
    const tokenBit = `${formatPt(Math.abs(geminiTokens - xaiTokens))} tokens a menos`;
    if (subject === leaner) {
      parts.push(tokenBit);
    } else {
      parts.push(`${leaner}: ${tokenBit}`);
      subject = subject ?? leaner;
    }
  }

  const citeSubject = subject ?? "Gemini";
  const citeCount = citeSubject === "Gemini" ? geminiCitations : xaiCitations;
  const otherCount = citeSubject === "Gemini" ? xaiCitations : geminiCitations;
  const fonte = citeCount === 1 ? "fonte" : "fontes";
  parts.push(`cita ${citeCount} ${fonte} vs ${otherCount}`);
  return parts.join(" · ");
}
