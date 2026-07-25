import { Suspense, lazy, useState } from "react";
import VoiceVisualizer, { VoiceState } from "./components/core/VoiceVisualizer";
import AgentMonitorPanel from "./components/panels/AgentMonitorPanel";
import AuthPanel from "./components/panels/AuthPanel";
import CalendarPanel from "./components/panels/CalendarPanel";
import CommandBar from "./components/panels/CommandBar";
import ConversationPanel from "./components/panels/ConversationPanel";
import ProjectsPanel from "./components/panels/ProjectsPanel";
import RecentDiscussions from "./components/panels/RecentDiscussions";
import SystemStatusPanel from "./components/panels/SystemStatusPanel";
import TasksPanel from "./components/panels/TasksPanel";
import { voiceApi } from "./lib/api";
import { useMicrophone } from "./lib/useMicrophone";
import { useAstaStore } from "./lib/store";

const AICore3D = lazy(() => import("./components/core/AICore3D"));

function deriveVoiceState(recording: boolean, transcribing: boolean, coreState: string): VoiceState {
  if (recording) return "listening";
  if (transcribing || coreState === "thinking") return "processing";
  if (coreState === "responding") return "speaking";
  return "waiting";
}

export default function App() {
  const { user, logout, coreState, setCoreState, sendMessage } = useAstaStore();
  const { recording, start, stop } = useMicrophone();
  const [micError, setMicError] = useState<string | null>(null);
  const [transcribing, setTranscribing] = useState(false);

  if (!user) {
    return <AuthPanel />;
  }

  async function handleMicToggle() {
    setMicError(null);
    if (recording) {
      setTranscribing(true);
      try {
        const blob = await stop();
        setCoreState("thinking");
        if (blob) {
          const text = await voiceApi.transcribe(blob);
          if (text.trim()) {
            await sendMessage(text);
          } else {
            setCoreState("idle");
          }
        } else {
          setCoreState("idle");
        }
      } catch (err) {
        setMicError(err instanceof Error ? err.message : "Transcription failed");
        setCoreState("idle");
      } finally {
        setTranscribing(false);
      }
    } else {
      try {
        await start();
        setCoreState("listening");
      } catch {
        setMicError("Microphone access denied");
      }
    }
  }

  const voiceState = deriveVoiceState(recording, transcribing, coreState);

  return (
    <div className="h-screen w-full flex flex-col overflow-hidden">
      {/* TOP: ASTA CORE + AI status / voice visualization */}
      <header className="flex flex-col items-center gap-2 py-4 border-b border-core-border/40">
        <span className="font-hud text-[10px] tracking-[0.4em] text-core-cyan/50">ASTA CORE</span>
        <Suspense
          fallback={<div className="h-28 w-28 rounded-full border border-core-cyan/20 animate-pulse" />}
        >
          <AICore3D state={coreState} />
        </Suspense>
        <VoiceVisualizer state={voiceState} />
        {micError && <p className="text-xs text-red-400">{micError}</p>}
      </header>

      {/* MIDDLE: left / center / right mission-control columns */}
      <div className="flex-1 min-h-0 flex flex-col lg:grid lg:grid-cols-[280px_1fr_320px] xl:grid-cols-[300px_1fr_340px] gap-4 p-4 overflow-y-auto lg:overflow-hidden">
        <aside className="flex flex-col gap-4 lg:overflow-y-auto lg:pr-1 order-2 lg:order-1">
          <div className="flex items-center justify-between text-sm font-mono px-1">
            <span className="text-glow text-core-cyan truncate">{user.display_name || user.email}</span>
            <button onClick={logout} className="text-core-cyan/60 hover:text-core-cyan text-[10px] font-hud">
              SIGN OUT
            </button>
          </div>
          <SystemStatusPanel />
          <RecentDiscussions />
        </aside>

        <main className="min-h-[420px] lg:min-h-0 order-1 lg:order-2">
          <ConversationPanel />
        </main>

        <aside className="flex flex-col gap-4 lg:overflow-y-auto lg:pl-1 order-3">
          <TasksPanel />
          <ProjectsPanel />
          <AgentMonitorPanel />
          <CalendarPanel />
        </aside>
      </div>

      {/* BOTTOM: command interface */}
      <CommandBar recording={recording} transcribing={transcribing} onMicToggle={handleMicToggle} />
    </div>
  );
}
