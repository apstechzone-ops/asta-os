import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAstaStore } from "../../lib/store";

const STATE_LABEL: Record<string, string> = {
  idle: "STANDBY",
  listening: "RECEIVING AUDIO",
  thinking: "PROCESSING",
  responding: "TRANSMITTING",
};

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export default function ConversationPanel() {
  const { messages, coreState, currentAction } = useAstaStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="glass-panel flex flex-col h-full overflow-hidden"
    >
      <div className="flex items-center justify-between px-4 py-3 border-b border-core-border/60">
        <span className="font-hud text-xs text-core-cyan/80">Conversation Log</span>
        <span
          className={`font-mono text-[10px] tracking-[0.2em] ${
            coreState === "idle" ? "text-core-text/40" : "text-core-cyan animate-pulse"
          }`}
        >
          {STATE_LABEL[coreState]}
        </span>
      </div>

      {currentAction && (
        <div className="px-4 py-1.5 border-b border-core-border/40 bg-core-violet/5">
          <span className="font-mono text-[10px] tracking-wider text-core-violet/80 animate-pulse">
            ⚙ {currentAction}
          </span>
        </div>
      )}

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
        {messages.length === 0 && (
          <p className="text-sm text-core-text/40 font-mono">// no transmissions logged — say something to Asta</p>
        )}
        <AnimatePresence initial={false}>
          {messages.map((m, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25 }}
              className={m.role === "user" ? "text-right" : ""}
            >
              <div
                className={`flex items-center gap-2 mb-1 text-[10px] font-mono tracking-wider ${
                  m.role === "user" ? "justify-end text-core-violet/60" : "text-core-cyan/60"
                }`}
              >
                <span>{m.role === "user" ? "USER" : "ASTA"}</span>
                <span className="text-core-text/30">{formatTime(m.timestamp)}</span>
              </div>
              <div
                className={`inline-block text-sm font-mono rounded-lg px-3 py-2 max-w-[85%] leading-relaxed text-left ${
                  m.role === "user"
                    ? "bg-core-violet/15 border border-core-violet/30 text-core-text/90"
                    : "bg-core-cyan/5 border border-core-cyan/20 text-core-cyan/90"
                }`}
              >
                {m.content}
                {m.role === "assistant" && i === messages.length - 1 && coreState === "responding" && (
                  <span className="inline-block w-1.5 h-3.5 bg-core-cyan/80 ml-0.5 animate-pulse align-middle" />
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
