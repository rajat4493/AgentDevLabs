type RoutingFlowProps = {
  provider?: string | null;
  model?: string | null;
  source?: string | null;
};

const PROVIDER_LABELS: Record<string, string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  ollama: "Ollama",
};

function formatProvider(provider?: string | null): string {
  const value = provider?.trim() ?? "";
  const key = value.toLowerCase();
  if (PROVIDER_LABELS[key]) return PROVIDER_LABELS[key];
  return value ? value.charAt(0).toUpperCase() + value.slice(1) : "Unknown";
}

function Step({ label, className }: { label: string; className: string }) {
  return (
    <div className={`rounded-md border px-4 py-2 text-sm font-medium shadow-sm ${className}`}>
      {label}
    </div>
  );
}

function Arrow() {
  return (
    <div className="text-2xl text-gray-500">
      <span className="hidden md:inline">→</span>
      <span className="md:hidden">↓</span>
    </div>
  );
}

export default function RoutingFlow({ provider, model, source }: RoutingFlowProps) {
  const providerLabel = formatProvider(provider);
  const modelLabel = model?.trim() || "Unknown";

  const midLabel =
    source === "sdk" ? "SDK" : source === "router" ? "Lattice Router" : "System";

  const steps = [
    { label: "User Prompt", className: "bg-blue-50 border-blue-200 text-blue-900" },
    { label: midLabel, className: "bg-purple-50 border-purple-200 text-purple-900" },
    { label: `Provider: ${providerLabel}`, className: "bg-green-50 border-green-200 text-green-900" },
    { label: `Model: ${modelLabel}`, className: "bg-orange-50 border-orange-200 text-orange-900" },
  ];

  return (
    <div className="flex flex-col items-center gap-4 md:flex-row">
      {steps.map((step, index) => (
        <div key={step.label} className="flex flex-col items-center gap-2 md:flex-row">
          <Step label={step.label} className={step.className} />
          {index < steps.length - 1 && <Arrow />}
        </div>
      ))}
    </div>
  );
}
