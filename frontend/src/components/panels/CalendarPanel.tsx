import { useEffect, useState } from "react";
import GlassPanel from "./GlassPanel";
import { googleApi } from "../../lib/api";

export default function CalendarPanel() {
  const [connected, setConnected] = useState<boolean | null>(null);

  useEffect(() => {
    googleApi
      .status()
      .then((s) => setConnected(s.connected))
      .catch(() => setConnected(null));
  }, []);

  async function handleConnect() {
    try {
      const { url } = await googleApi.authUrl();
      window.open(url, "_blank", "noopener,noreferrer");
    } catch {
      // silently ignore — button just won't do anything if backend unreachable
    }
  }

  return (
    <GlassPanel title="Calendar">
      {connected === null && <p className="text-xs text-core-text/50">Checking connection…</p>}

      {connected === false && (
        <div className="text-xs text-core-text/60 space-y-2">
          <p>Google Calendar not connected.</p>
          <button
            onClick={handleConnect}
            className="w-full font-hud text-[10px] tracking-widest text-core-cyan/80 border border-core-border rounded-lg py-1.5 hover:border-core-cyan hover:text-core-cyan transition-colors"
          >
            CONNECT GOOGLE CALENDAR
          </button>
        </div>
      )}

      {connected === true && (
        <p className="text-xs text-core-text/60">
          Connected. Upcoming events sync via <span className="font-mono">/google/calendar/events</span>.
        </p>
      )}
    </GlassPanel>
  );
}
