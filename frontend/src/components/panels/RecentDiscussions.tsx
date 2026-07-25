import { useEffect, useState } from "react";
import GlassPanel from "./GlassPanel";
import { sessionsApi, SessionSummary } from "../../lib/api";
import { useAstaStore } from "../../lib/store";

function timeAgo(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function RecentDiscussions() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [error, setError] = useState(false);
  const { sessionId, switchSession, startNewSession } = useAstaStore();

  useEffect(() => {
    sessionsApi
      .list()
      .then(setSessions)
      .catch(() => setError(true));
  }, [sessionId]);

  return (
    <GlassPanel title="Recent Discussions">
      <button
        onClick={startNewSession}
        className="w-full mb-2 text-xs font-hud text-core-cyan/80 border border-core-border rounded-lg py-1.5 hover:border-core-cyan hover:text-core-cyan transition-colors"
      >
        + New conversation
      </button>

      {error && <p className="text-xs text-core-text/50">Unable to reach backend.</p>}
      {!error && sessions.length === 0 && (
        <p className="text-xs text-core-text/50">No past conversations yet.</p>
      )}

      <ul className="space-y-1 max-h-48 overflow-y-auto">
        {sessions.map((s) => (
          <li key={s.id}>
            <button
              onClick={() => switchSession(s.id)}
              className={`w-full text-left px-2 py-1.5 rounded-lg text-xs transition-colors ${
                s.id === sessionId ? "bg-core-cyan/10 text-core-cyan" : "hover:bg-white/5 text-core-text/70"
              }`}
            >
              <div className="truncate font-medium">{s.last_message || s.title}</div>
              <div className="text-[10px] text-core-text/40 font-mono">{timeAgo(s.updated_at)}</div>
            </button>
          </li>
        ))}
      </ul>
    </GlassPanel>
  );
}
