import { FormEvent, useState } from "react";
import { motion } from "framer-motion";
import { useAstaStore } from "../../lib/store";

interface CommandBarProps {
  recording: boolean;
  transcribing: boolean;
  onMicToggle: () => void;
}

export default function CommandBar({ recording, transcribing, onMicToggle }: CommandBarProps) {
  const { coreState, sendMessage } = useAstaStore();
  const [input, setInput] = useState("");
  const busy = coreState === "thinking" || coreState === "responding";

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!input.trim() || busy) return;
    const text = input;
    setInput("");
    await sendMessage(text);
  }

  return (
    <motion.form
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      onSubmit={handleSubmit}
      className="glass-panel flex items-center gap-3 px-4 py-3 mx-4 mb-4"
    >
      <motion.button
        type="button"
        whileHover={{ scale: 1.06 }}
        whileTap={{ scale: 0.94 }}
        onClick={onMicToggle}
        disabled={transcribing}
        title={recording ? "Stop and send" : "Start voice input"}
        className={`h-9 w-9 flex-shrink-0 rounded-full flex items-center justify-center border transition-colors disabled:opacity-40 ${
          recording
            ? "border-red-400/60 text-red-400 shadow-[0_0_14px_rgba(248,113,113,0.4)]"
            : "border-core-cyan/40 text-core-cyan hover:border-core-cyan"
        }`}
      >
        {recording ? "■" : "●"}
      </motion.button>

      <input
        className="flex-1 bg-transparent border-none text-sm font-mono outline-none placeholder:text-core-text/30"
        placeholder={transcribing ? "Transcribing audio…" : "Enter command or message…"}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        disabled={busy || transcribing}
      />

      <motion.button
        type="submit"
        whileHover={{ scale: input.trim() ? 1.04 : 1 }}
        whileTap={{ scale: input.trim() ? 0.96 : 1 }}
        disabled={busy || transcribing || !input.trim()}
        className="px-4 py-1.5 rounded-lg bg-gradient-to-r from-core-cyan to-core-violet text-core-bg text-xs font-hud disabled:opacity-30"
      >
        SEND
      </motion.button>
    </motion.form>
  );
}
