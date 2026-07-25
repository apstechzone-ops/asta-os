import { useEffect, useState } from "react";
import GlassPanel from "./GlassPanel";
import { systemApi } from "../../lib/api";

interface Metric {
  label: string;
  value: number | null;
  unit: string;
}

export default function SystemStatusPanel() {
  const [metrics, setMetrics] = useState<Metric[]>([
    { label: "CPU", value: null, unit: "%" },
    { label: "GPU", value: null, unit: "%" },
    { label: "MEMORY", value: null, unit: "%" },
    { label: "NETWORK", value: null, unit: " Mbps" },
  ]);
  const [online, setOnline] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const m = await systemApi.metrics();
        if (cancelled) return;
        setOnline(true);
        setMetrics([
          { label: "CPU", value: m.cpu_percent, unit: "%" },
          { label: "GPU", value: m.gpu_percent, unit: "%" },
          { label: "MEMORY", value: m.ram_percent, unit: "%" },
          { label: "NETWORK", value: m.network_mbps, unit: " Mbps" },
        ]);
      } catch {
        if (!cancelled) setOnline(false);
      }
    }

    poll();
    const interval = setInterval(poll, 4000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <GlassPanel title="System Status">
      <div className="flex items-center gap-2 mb-3">
        <span className={`h-1.5 w-1.5 rounded-full ${online ? "bg-emerald-400" : "bg-red-400"}`} />
        <span className="font-mono text-[10px] tracking-wider text-core-text/50">
          {online ? "SYSTEM ONLINE" : "BACKEND UNREACHABLE"}
        </span>
      </div>

      <div className="space-y-3">
        {metrics.map((m) => (
          <div key={m.label}>
            <div className="flex justify-between text-xs font-mono text-core-text/60 mb-1">
              <span>{m.label}</span>
              <span>{m.value ?? "—"}{m.value !== null ? m.unit : ""}</span>
            </div>
            <div className="h-1 rounded-full bg-white/5 overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-core-cyan to-core-violet transition-all duration-700"
                style={{ width: `${m.label === "NETWORK" ? Math.min(100, (m.value ?? 0) * 10) : m.value ?? 0}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </GlassPanel>
  );
}
