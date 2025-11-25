export type ProviderKey =
  | "openai"
  | "anthropic"
  | "gemini"
  | "ollama"
  | "stub"
  | string;

export const PROVIDER_STYLES: Record<
  ProviderKey,
  {
    label: string;
    badgeClass: string;
  }
> = {
  openai: {
    label: "OpenAI",
    badgeClass:
      "inline-flex items-center rounded-full border border-emerald-500/40 bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-200",
  },
  anthropic: {
    label: "Anthropic",
    badgeClass:
      "inline-flex items-center rounded-full border border-amber-500/40 bg-amber-500/10 px-2 py-0.5 text-[11px] font-medium text-amber-200",
  },
  gemini: {
    label: "Gemini",
    badgeClass:
      "inline-flex items-center rounded-full border border-indigo-500/40 bg-indigo-500/10 px-2 py-0.5 text-[11px] font-medium text-indigo-200",
  },
  ollama: {
    label: "Ollama",
    badgeClass:
      "inline-flex items-center rounded-full border border-slate-500/60 bg-slate-900/80 px-2 py-0.5 text-[11px] font-medium text-slate-200",
  },
  stub: {
    label: "Stub",
    badgeClass:
      "inline-flex items-center rounded-full border border-zinc-500/40 bg-zinc-500/10 px-2 py-0.5 text-[11px] font-medium text-zinc-200",
  },
};

