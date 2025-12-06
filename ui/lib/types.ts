export type TraceListItem = {
  id: string;
  created_at: string;
  provider: string;
  model: string;
  latency_ms?: number | null;
  framework?: string | null;
  source?: string | null;
};

export type Trace = TraceListItem & {
  input: string;
  output?: string | null;
  tokens?: number | null;
  extra?: Record<string, unknown> | null;
};
