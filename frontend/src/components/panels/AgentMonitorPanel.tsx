import { useEffect, useState } from "react";
import GlassPanel from "./GlassPanel";
import { agentsApi } from "../../lib/api";

type AgentState = "online" | "standby" | "offline" | "waiting";

const STATE_STYLE: Record<AgentState, { dot: string; label: string; text: string }> = {
  online: { dot: "bg-emerald-400 animate-pulse", label: "ONLINE", text: "text-emerald-400/90" },
  standby: { dot: "bg-amber-400", label: "STANDBY", text: "text-amber-400/80" },
  offline: { dot: "bg-core-text/25", label: "OFFLINE", text: "text-core-text/40" },
  waiting: { dot: "bg-core-cyan animate-pulse", label: "WAITING", text: "text-core-cyan/80" },
};

// Planned roadmap agents (future modules) — shown so the mission-control
// picture is complete even before each one is implemented.
const PLANNED_AGENTS: { name: string; state: AgentState }[] = [
  { name: "Planner Agent", state: "waiting" },
  { name: "Memory Agent", state: "standby" },
  { name: "Automation Agent", state: "offline" },
  { name: "Learning Agent", state: "offline" },
];

export default function AgentMonitorPanel() {
  const [liveAgents, setLiveAgents] = useState<string[]>([]);
  const [error, setError] = useState(false);

  useEffect(() => {
    agentsApi
      .list()
      .then((res) => setLiveAgents(res.agents))
      .catch(() => setError(true));
  }, []);

  const liveSet = new Set(liveAgents);
  const planned = PLANNED_AGENTS.filter((a) => {
    const slug = a.name.toLowerCase().replace(/ /g, "_");
    return !liveSet.has(slug);
  });

  return (
    <GlassPanel title="Agent Monitor">
      {error && <p className="text-xs text-core-text/50 mb-2">Unable to reach backend.</p>}
      <ul className="space-y-2">
        {liveAgents.map((name) => (
          <li key={name} className="flex items-center justify-between text-sm">
            <span className="font-mono text-xs text-core-text/80">
              {name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
            </span>
            <span className={`flex items-center gap-1.5 font-mono text-[10px] ${STATE_STYLE.online.text}`}>
              <span className={`h-1.5 w-1.5 rounded-full ${STATE_STYLE.online.dot}`} />
              {STATE_STYLE.online.label}
            </span>
          </li>
        ))}
        {planned.map((a) => (
          <li key={a.name} className="flex items-center justify-between text-sm opacity-70">
            <span className="font-mono text-xs text-core-text/60">{a.name}</span>
            <span className={`flex items-center gap-1.5 font-mono text-[10px] ${STATE_STYLE[a.state].text}`}>
              <span className={`h-1.5 w-1.5 rounded-full ${STATE_STYLE[a.state].dot}`} />
              {STATE_STYLE[a.state].label}
            </span>
          </li>
        ))}
      </ul>
    </GlassPanel>
  );
}
