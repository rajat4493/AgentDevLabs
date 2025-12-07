import { useCallback, useEffect, useMemo, useState } from "react";
import { Layout } from "@/components/Layout";
import { TraceList } from "@/components/TraceList";
import type { TraceListItem } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_RAJOS_API_BASE || "http://localhost:8000";

type TraceListResponse = {
  items: TraceListItem[];
  total: number;
};

export default function TracesPage() {
  const [traces, setTraces] = useState<TraceListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [providerFilter, setProviderFilter] = useState("all");
  const [frameworkFilter, setFrameworkFilter] = useState("all");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [sortBy, setSortBy] = useState("newest");

  const loadTraces = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${API_BASE}/api/traces?limit=50`);
      if (!resp.ok) throw new Error(`Backend error (${resp.status})`);
      const data: TraceListResponse = await resp.json();
      setTraces(data.items);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadTraces();
  }, [loadTraces]);

  useEffect(() => {
    const handle = setTimeout(() => {
      setSearch(searchInput);
    }, 300);
    return () => clearTimeout(handle);
  }, [searchInput]);

  const filteredTraces = useMemo(() => {
    const searchTerm = search.trim().toLowerCase();
    return traces
      .filter((trace) => {
        const prompt = (trace.input || "").toLowerCase();
        return searchTerm ? prompt.includes(searchTerm) : true;
      })
      .filter((trace) => (providerFilter === "all" ? true : trace.provider?.toLowerCase() === providerFilter))
      .filter((trace) =>
        frameworkFilter === "all" ? true : (trace.framework || "").toLowerCase() === frameworkFilter,
      )
      .filter((trace) => (sourceFilter === "all" ? true : (trace.source || "").toLowerCase() === sourceFilter))
      .sort((a, b) => {
        const aTime = new Date(a.created_at).getTime();
        const bTime = new Date(b.created_at).getTime();
        return sortBy === "newest" ? bTime - aTime : aTime - bTime;
      });
  }, [traces, search, providerFilter, frameworkFilter, sourceFilter, sortBy]);

  const renderContent = () => {
    if (loading) {
      return (
        <div className="rounded-xl border border-slate-900/60 bg-slate-900/40 py-16 text-center text-slate-200">
          Loading traces...
        </div>
      );
    }

    if (error) {
      return (
        <div className="rounded-xl border border-rose-500/30 bg-rose-950/40 py-16 text-center text-rose-100">
          Failed to load traces. Check backend connection.
        </div>
      );
    }

    return (
      <>
        <div className="mb-6 flex flex-col gap-3 lg:flex-row lg:flex-wrap">
        <input
          type="search"
          placeholder="Search prompt..."
          value={searchInput}
          onChange={(event) => setSearchInput(event.target.value)}
          className="w-full rounded-md border border-slate-700/60 bg-slate-900/70 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-amber-400 focus:outline-none focus:ring-0 lg:flex-1"
        />
        <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap lg:flex-none">
          <Select
            label="Provider"
            value={providerFilter}
            onChange={setProviderFilter}
            options={["all", "openai", "anthropic", "ollama", "fake-llm"]}
          />
          <Select
            label="Framework"
            value={frameworkFilter}
            onChange={setFrameworkFilter}
            options={["all", "raw", "langchain", "crewai", "smolagents"]}
          />
          <Select
            label="Source"
            value={sourceFilter}
            onChange={setSourceFilter}
            options={["all", "sdk", "router", "ui", "curl"]}
          />
          <Select label="Sort" value={sortBy} onChange={setSortBy} options={["newest", "oldest"]} />
        </div>
        </div>
        {filteredTraces.length === 0 ? (
          <div className="rounded-xl border border-slate-900/60 bg-slate-900/40 py-16 text-center text-slate-400">
            No traces match your filters.
          </div>
        ) : (
          <TraceList traces={filteredTraces} loading={loading} onRefresh={loadTraces} />
        )}
      </>
    );
  };

  return (
    <Layout
      title="Trace Explorer"
      subtitle="Inspect every routed request from the last mile of your devkit."
      actions={
        <button
          type="button"
          onClick={loadTraces}
          className="rounded-lg border border-slate-700 px-4 py-2 text-xs font-semibold uppercase tracking-[0.3em] text-slate-200 transition hover:border-amber-400"
        >
          Refresh
        </button>
      }
    >
      {renderContent()}
    </Layout>
  );
}

type SelectProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
};

function Select({ label, value, onChange, options }: SelectProps) {
  return (
    <label className="flex flex-col text-xs uppercase tracking-[0.3em] text-slate-300">
      <span className="mb-1">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="min-w-[150px] rounded-xl border border-white/20 bg-white/10 px-4 py-2 text-sm text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.1)] backdrop-blur focus:border-amber-300 focus:outline-none focus:ring-2 focus:ring-amber-400/30"
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option.charAt(0).toUpperCase() + option.slice(1)}
          </option>
        ))}
      </select>
    </label>
  );
}
