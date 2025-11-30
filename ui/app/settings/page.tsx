"use client";

import { useEffect, useState } from "react";

const API_BASE =
  (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(
    /\/$/,
    "",
  );

const DATA_SENSITIVITY_OPTIONS = ["PUBLIC", "INTERNAL", "PII"];
const AUTONOMY_OPTIONS = ["ANSWER_ONLY", "TOOL_CALL"];

export default function SettingsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const [tenantName, setTenantName] = useState<string>("");
  const [dataSensitivity, setDataSensitivity] =
    useState<string>("PUBLIC");
  const [autonomyLevel, setAutonomyLevel] =
    useState<string>("ANSWER_ONLY");

  useEffect(() => {
    async function loadSettings() {
      try {
        setLoading(true);
        setError(null);
        const res = await fetch(`${API_BASE}/tenant/settings`);
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        const json = await res.json();
        setTenantName(json.name ?? "Default Tenant");
        setDataSensitivity(json.default_data_sensitivity ?? "PUBLIC");
        setAutonomyLevel(json.default_autonomy_level ?? "ANSWER_ONLY");
      } catch (err: any) {
        setError(err.message || "Failed to load tenant settings");
      } finally {
        setLoading(false);
      }
    }
    loadSettings();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const res = await fetch(`${API_BASE}/tenant/settings`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          default_data_sensitivity: dataSensitivity,
          default_autonomy_level: autonomyLevel,
        }),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `HTTP ${res.status}`);
      }
      const json = await res.json();
      setDataSensitivity(json.default_data_sensitivity);
      setAutonomyLevel(json.default_autonomy_level);
      setMessage("Settings saved.");
    } catch (err: any) {
      setError(err.message || "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const disabled = loading || saving;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Tenant Settings</h1>
        <p className="text-sm text-slate-400">
          Configure default governance for routing decisions.
        </p>
      </div>

      {error && (
        <div className="rounded border border-red-500/50 bg-red-950/40 px-4 py-2 text-sm text-red-200">
          {error}
        </div>
      )}

      {message && (
        <div className="rounded border border-emerald-500/40 bg-emerald-950/40 px-4 py-2 text-sm text-emerald-200">
          {message}
        </div>
      )}

      <div className="space-y-4 rounded-2xl border border-slate-800/70 bg-slate-950/60 p-5">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-500">
            Tenant
          </p>
          <p className="text-lg font-semibold text-slate-100">
            {loading ? "Loading…" : tenantName || "Unknown tenant"}
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="flex flex-col gap-2">
            <label className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              Default Data Sensitivity
            </label>
            <select
              className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
              value={dataSensitivity}
              onChange={(e) => setDataSensitivity(e.target.value)}
              disabled={disabled}
            >
              {DATA_SENSITIVITY_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              Default Autonomy Level
            </label>
            <select
              className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
              value={autonomyLevel}
              onChange={(e) => setAutonomyLevel(e.target.value)}
              disabled={disabled}
            >
              {AUTONOMY_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </div>
        </div>

        <button
          type="button"
          onClick={handleSave}
          disabled={disabled}
          className="inline-flex items-center rounded-md border border-emerald-500/50 bg-emerald-500/10 px-4 py-2 text-sm font-semibold text-emerald-200 hover:bg-emerald-500/20 disabled:opacity-50"
        >
          {saving ? "Saving…" : "Save Settings"}
        </button>
      </div>
    </div>
  );
}
