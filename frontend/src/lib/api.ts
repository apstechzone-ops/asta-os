const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

let authToken: string | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
}

function headers(extra: Record<string, string> = {}): Record<string, string> {
  const h: Record<string, string> = { "Content-Type": "application/json", ...extra };
  if (authToken) h["Authorization"] = `Bearer ${authToken}`;
  return h;
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail ?? `Request failed with ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface UserOut {
  id: string;
  email: string;
  display_name: string;
  is_active: boolean;
}

export const authApi = {
  async register(email: string, password: string, display_name = ""): Promise<UserOut> {
    const res = await fetch(`${BASE_URL}/auth/register`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ email, password, display_name }),
    });
    return handle<UserOut>(res);
  },

  async login(email: string, password: string): Promise<Token> {
    const res = await fetch(`${BASE_URL}/auth/login`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ email, password }),
    });
    return handle<Token>(res);
  },

  async me(): Promise<UserOut> {
    const res = await fetch(`${BASE_URL}/auth/me`, { headers: headers() });
    return handle<UserOut>(res);
  },
};

export interface PlannerAction {
  status: "executing" | "done" | "failed";
  tool: string;
}

export const plannerApi = {
  /** Streams NDJSON events from the backend: token content via onToken,
   * tool-execution status via onAction. Buffers partial lines across
   * chunk boundaries since fetch's stream doesn't guarantee line-aligned reads. */
  async chatStream(
    sessionId: string,
    message: string,
    onToken: (token: string) => void,
    onAction?: (action: PlannerAction) => void,
    signal?: AbortSignal
  ): Promise<void> {
    const res = await fetch(`${BASE_URL}/planner/chat`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ session_id: sessionId, message }),
      signal,
    });

    if (!res.ok || !res.body) {
      const detail = await res.json().catch(() => ({}));
      throw new Error(detail.detail ?? `Chat request failed with ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? ""; // keep the last (possibly incomplete) line for next read

      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const event = JSON.parse(line);
          if (event.type === "token") onToken(event.content);
          else if (event.type === "action") onAction?.({ status: event.status, tool: event.tool });
        } catch {
          // malformed line — surface as raw text rather than silently dropping it
          onToken(line);
        }
      }
    }

    if (buffer.trim()) {
      try {
        const event = JSON.parse(buffer);
        if (event.type === "token") onToken(event.content);
        else if (event.type === "action") onAction?.({ status: event.status, tool: event.tool });
      } catch {
        onToken(buffer);
      }
    }
  },
};

export const memoryApi = {
  async getRecent(sessionId: string, limit = 20) {
    const res = await fetch(`${BASE_URL}/memory/short-term/${sessionId}?limit=${limit}`, {
      headers: headers(),
    });
    return handle<{ role: string; content: string; created_at: string }[]>(res);
  },
};

export interface SystemMetrics {
  cpu_percent: number;
  ram_percent: number;
  gpu_percent: number | null;
  vram_percent: number | null;
  network_mbps: number | null;
}

export const systemApi = {
  async metrics(): Promise<SystemMetrics> {
    const res = await fetch(`${BASE_URL}/system/metrics`, { headers: headers() });
    return handle<SystemMetrics>(res);
  },
};

export const agentsApi = {
  async list(): Promise<{ agents: string[] }> {
    const res = await fetch(`${BASE_URL}/agents`, { headers: headers() });
    return handle<{ agents: string[] }>(res);
  },
};

export const voiceApi = {
  async transcribe(audioBlob: Blob): Promise<string> {
    const form = new FormData();
    form.append("file", audioBlob, "recording.webm");

    const h: Record<string, string> = {};
    if (authToken) h["Authorization"] = `Bearer ${authToken}`;

    const res = await fetch(`${BASE_URL}/voice/transcribe`, {
      method: "POST",
      headers: h,
      body: form,
    });
    const data = await handle<{ text: string }>(res);
    return data.text;
  },
};

export interface TaskOut {
  id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  due_date: string | null;
  project_id: string | null;
  created_at: string;
}

export const tasksApi = {
  async list(): Promise<TaskOut[]> {
    const res = await fetch(`${BASE_URL}/tasks`, { headers: headers() });
    return handle<TaskOut[]>(res);
  },

  async create(title: string): Promise<TaskOut> {
    const res = await fetch(`${BASE_URL}/tasks`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ title }),
    });
    return handle<TaskOut>(res);
  },

  async setStatus(taskId: string, status: string): Promise<TaskOut> {
    const res = await fetch(`${BASE_URL}/tasks/${taskId}`, {
      method: "PATCH",
      headers: headers(),
      body: JSON.stringify({ status }),
    });
    return handle<TaskOut>(res);
  },

  async remove(taskId: string): Promise<void> {
    await fetch(`${BASE_URL}/tasks/${taskId}`, { method: "DELETE", headers: headers() });
  },
};

export interface SessionSummary {
  id: string;
  title: string;
  summary: string;
  last_message: string;
  updated_at: string;
}

export const sessionsApi = {
  async list(): Promise<SessionSummary[]> {
    const res = await fetch(`${BASE_URL}/memory/sessions`, { headers: headers() });
    return handle<SessionSummary[]>(res);
  },
};

export interface ProjectOut {
  id: string;
  name: string;
  description: string;
  status: string;
  created_at: string;
}

export const projectsApi = {
  async list(): Promise<ProjectOut[]> {
    const res = await fetch(`${BASE_URL}/projects`, { headers: headers() });
    return handle<ProjectOut[]>(res);
  },

  async create(name: string): Promise<ProjectOut> {
    const res = await fetch(`${BASE_URL}/projects`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ name }),
    });
    return handle<ProjectOut>(res);
  },
};

export const googleApi = {
  async status(): Promise<{ connected: boolean }> {
    const res = await fetch(`${BASE_URL}/google/status`, { headers: headers() });
    return handle<{ connected: boolean }>(res);
  },

  async authUrl(): Promise<{ url: string }> {
    const res = await fetch(`${BASE_URL}/google/auth-url`, { headers: headers() });
    return handle<{ url: string }>(res);
  },

  async calendarEvents(): Promise<unknown[]> {
    const res = await fetch(`${BASE_URL}/google/calendar/events`, { headers: headers() });
    return handle<unknown[]>(res);
  },
};
