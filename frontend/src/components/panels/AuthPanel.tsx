import { useState } from "react";
import GlassPanel from "./GlassPanel";
import { authApi, setAuthToken } from "../../lib/api";
import { useAstaStore } from "../../lib/store";

export default function AuthPanel() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const login = useAstaStore((s) => s.login);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "register") {
        await authApi.register(email, password, displayName);
      }
      const token = await authApi.login(email, password);
      setAuthToken(token.access_token);
      const user = await authApi.me();
      login(token.access_token, user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center px-4">
      <GlassPanel title={mode === "login" ? "Sign in to Asta" : "Create your Asta account"} className="w-full max-w-96">
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          {mode === "register" && (
            <input
              className="bg-white/5 border border-core-border rounded-lg px-3 py-2 text-sm outline-none focus:border-core-cyan"
              placeholder="Display name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
            />
          )}
          <input
            className="bg-white/5 border border-core-border rounded-lg px-3 py-2 text-sm outline-none focus:border-core-cyan"
            placeholder="Email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <input
            className="bg-white/5 border border-core-border rounded-lg px-3 py-2 text-sm outline-none focus:border-core-cyan"
            placeholder="Password"
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          {error && <p className="text-xs text-red-400">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="mt-1 py-2 rounded-lg bg-gradient-to-r from-core-cyan to-core-violet text-core-bg font-semibold text-sm disabled:opacity-50"
          >
            {loading ? "Please wait..." : mode === "login" ? "Sign in" : "Create account"}
          </button>
        </form>

        <button
          onClick={() => setMode(mode === "login" ? "register" : "login")}
          className="mt-3 text-xs text-core-cyan/70 hover:text-core-cyan"
        >
          {mode === "login" ? "Need an account? Register" : "Already have an account? Sign in"}
        </button>
      </GlassPanel>
    </div>
  );
}
