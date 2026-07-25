export type VoiceState = "waiting" | "listening" | "processing" | "speaking";

const STATE_LABEL: Record<VoiceState, string> = {
  waiting: "WAITING",
  listening: "LISTENING",
  processing: "PROCESSING",
  speaking: "SPEAKING",
};

const STATE_COLOR: Record<VoiceState, string> = {
  waiting: "bg-core-text/20",
  listening: "bg-blue-400/80",
  processing: "bg-core-violet/80",
  speaking: "bg-core-cyan/80",
};

const BAR_HEIGHTS = [4, 14, 8, 20, 6, 16, 10, 22, 5, 12, 9, 18, 7, 15, 11, 20, 6, 14, 8, 17, 5, 12, 9, 16];

interface VoiceVisualizerProps {
  state: VoiceState;
  bars?: number;
}

export default function VoiceVisualizer({ state, bars = 24 }: VoiceVisualizerProps) {
  const active = state !== "waiting";
  const barColor = STATE_COLOR[state];
  const speed = state === "processing" ? 0.35 : state === "speaking" ? 0.45 : 0.6;

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="flex items-end gap-1 h-8">
        {Array.from({ length: bars }).map((_, i) => (
          <span
            key={i}
            className={`w-1 rounded-full transition-all ${barColor}`}
            style={{
              height: active ? `${BAR_HEIGHTS[i % BAR_HEIGHTS.length]}px` : "4px",
              transitionDuration: `${speed + (i % 5) * 0.08}s`,
              animation: active ? `pulse-bar ${speed + (i % 5) * 0.1}s ease-in-out infinite alternate` : "none",
              animationDelay: `${i * 0.03}s`,
            }}
          />
        ))}
      </div>
      <span className="font-mono text-[10px] tracking-[0.2em] text-core-text/40">
        {STATE_LABEL[state]}
      </span>
    </div>
  );
}
