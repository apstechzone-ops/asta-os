import { create } from "zustand";
import { plannerApi, setAuthToken, UserOut, memoryApi } from "./api";
import type { CoreState } from "../components/core/AICore3D";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

interface AstaState {
  token: string | null;
  user: UserOut | null;
  sessionId: string;
  messages: ChatMessage[];
  coreState: CoreState;
  currentAction: string | null;

  login: (token: string, user: UserOut) => void;
  logout: () => void;
  addMessage: (msg: Omit<ChatMessage, "timestamp">) => void;
  appendToLastAssistantMessage: (chunk: string) => void;
  setCoreState: (state: CoreState) => void;
  sendMessage: (text: string) => Promise<void>;
  startNewSession: () => void;
  switchSession: (sessionId: string) => Promise<void>;
}

function newSessionId(): string {
  return crypto.randomUUID();
}

export const useAstaStore = create<AstaState>((set, get) => ({
  token: null,
  user: null,
  sessionId: newSessionId(),
  messages: [],
  coreState: "idle",
  currentAction: null,

  login: (token, user) => {
    setAuthToken(token);
    set({ token, user });
  },

  logout: () => {
    setAuthToken(null);
    set({ token: null, user: null, messages: [], sessionId: newSessionId(), coreState: "idle" });
  },

  addMessage: (msg) => set({ messages: [...get().messages, { ...msg, timestamp: Date.now() }] }),

  appendToLastAssistantMessage: (chunk) => {
    const messages = [...get().messages];
    const last = messages[messages.length - 1];
    if (last && last.role === "assistant") {
      last.content += chunk;
    } else {
      messages.push({ role: "assistant", content: chunk, timestamp: Date.now() });
    }
    set({ messages });
  },

  setCoreState: (coreState) => set({ coreState }),

  sendMessage: async (text: string) => {
    const message = text.trim();
    if (!message || get().coreState === "thinking" || get().coreState === "responding") return;

    const { sessionId, addMessage, appendToLastAssistantMessage, setCoreState } = get();
    addMessage({ role: "user", content: message });
    setCoreState("thinking");

    try {
      let firstToken = true;
      await plannerApi.chatStream(
        sessionId,
        message,
        (token) => {
          if (firstToken) {
            addMessage({ role: "assistant", content: "" });
            setCoreState("responding");
            firstToken = false;
          }
          appendToLastAssistantMessage(token);
        },
        (action) => {
          if (action.status === "executing") {
            set({ currentAction: `Executing ${action.tool}…` });
          } else {
            set({ currentAction: null });
          }
        }
      );
    } catch (err) {
      appendToLastAssistantMessage(`\n[error: ${err instanceof Error ? err.message : "chat failed"}]`);
    } finally {
      setCoreState("idle");
      set({ currentAction: null });
    }
  },

  startNewSession: () => set({ sessionId: newSessionId(), messages: [] }),

  switchSession: async (sessionId: string) => {
    set({ sessionId, messages: [] });
    try {
      const history = await memoryApi.getRecent(sessionId, 50);
      set({
        messages: history.map((m) => ({
          role: m.role === "assistant" ? "assistant" : "user",
          content: m.content,
          timestamp: new Date(m.created_at).getTime(),
        })),
      });
    } catch {
      // leave empty on failure
    }
  },
}));
