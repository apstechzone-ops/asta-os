import { FormEvent, useEffect, useState } from "react";
import GlassPanel from "./GlassPanel";
import { projectsApi, ProjectOut } from "../../lib/api";

export default function ProjectsPanel() {
  const [projects, setProjects] = useState<ProjectOut[]>([]);
  const [input, setInput] = useState("");
  const [error, setError] = useState(false);

  useEffect(() => {
    projectsApi
      .list()
      .then(setProjects)
      .catch(() => setError(true));
  }, []);

  async function handleAdd(e: FormEvent) {
    e.preventDefault();
    const name = input.trim();
    if (!name) return;
    setInput("");
    try {
      const created = await projectsApi.create(name);
      setProjects((p) => [created, ...p]);
    } catch {
      setError(true);
    }
  }

  return (
    <GlassPanel title="Projects">
      <form onSubmit={handleAdd} className="flex gap-2 mb-3">
        <input
          className="flex-1 bg-white/5 border border-core-border rounded-lg px-2 py-1.5 text-xs font-mono outline-none focus:border-core-cyan"
          placeholder="New project..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button
          type="submit"
          className="px-3 rounded-lg bg-core-cyan/20 border border-core-cyan/40 text-core-cyan text-xs font-hud"
        >
          +
        </button>
      </form>

      {error && <p className="text-xs text-core-text/50">Unable to reach backend.</p>}
      {!error && projects.length === 0 && <p className="text-xs text-core-text/50">No projects yet.</p>}

      <ul className="space-y-1.5 max-h-32 overflow-y-auto">
        {projects.map((p) => (
          <li key={p.id} className="flex items-center justify-between text-xs font-mono">
            <span className="truncate text-core-text/80">{p.name}</span>
            <span className="text-core-cyan/50 text-[10px] uppercase">{p.status}</span>
          </li>
        ))}
      </ul>
    </GlassPanel>
  );
}
