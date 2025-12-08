import { useRouter } from "next/router";
import LatticeShell from "@/components/LatticeShell";

export default function TraceDetailPlaceholder() {
  const router = useRouter();
  const { id } = router.query;

  return (
    <LatticeShell title="Trace Detail" subtitle="Lattice Dev Edition does not persist per-request traces.">
      <div className="rounded-2xl border border-white/40 dark:border-white/10 bg-white/70 dark:bg-white/5 p-6 text-sm text-slate-700 dark:text-slate-200 shadow-[0_0_40px_rgba(15,23,42,0.08)] backdrop-blur-2xl">
        <p className="mb-2">
          Request <strong>{typeof id === "string" ? `#${id}` : ""}</strong> cannot be displayed because Lattice never stores
          raw prompts or responses. Use the metrics views or `/dashboard` to monitor aggregate activity.
        </p>
        <p>
          Need per-request logging? Fork the repo and add your own persistence layer—just keep the privacy guarantees in mind.
        </p>
      </div>
    </LatticeShell>
  );
}
