"use client";

export default function SettingsPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Settings / About</h1>
      <div className="space-y-2 text-slate-300">
        <p>Version: v0.3.0-beta</p>
        <p>Pricing Profile: default_public_list_prices_2025Q1</p>
        <p>Enabled Providers: OpenAI, Anthropic, Gemini, Ollama</p>
        <p>Environment: Local (Docker)</p>
      </div>
    </div>
  );
}

