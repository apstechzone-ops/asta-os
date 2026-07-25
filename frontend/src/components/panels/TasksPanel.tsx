import { FormEvent, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import GlassPanel from "./GlassPanel";
import { tasksApi, TaskOut } from "../../lib/api";

export default function TasksPanel() {
  const [tasks, setTasks] = useState<TaskOut[]>([]);
  const [input, setInput] = useState("");
  const [error, setError] = useState(false);

  async function refresh() {
    try {
      setTasks(await tasksApi.list());
      setError(false);
    } catch {
      setError(true);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleAdd(e: FormEvent) {
    e.preventDefault();
    const title = input.trim();
    if (!title) return;
    setInput("");
    const optimistic: TaskOut = {
      id: `temp-${Date.now()}`,
      title,
      description: "",
      status: "pending",
      priority: "normal",
      due_date: null,
      project_id: null,
      created_at: new Date().toISOString(),
    };
    setTasks((t) => [optimistic, ...t]);
    try {
      const created = await tasksApi.create(title);
      setTasks((t) => t.map((task) => (task.id === optimistic.id ? created : task)));
    } catch {
      setTasks((t) => t.filter((task) => task.id !== optimistic.id));
    }
  }

  async function toggleDone(task: TaskOut) {
    const nextStatus = task.status === "done" ? "pending" : "done";
    setTasks((t) => t.map((x) => (x.id === task.id ? { ...x, status: nextStatus } : x)));
    try {
      await tasksApi.setStatus(task.id, nextStatus);
    } catch {
      refresh();
    }
  }

  return (
    <GlassPanel title="Missions">
      <form onSubmit={handleAdd} className="flex gap-2 mb-3">
        <input
          className="flex-1 bg-white/5 border border-core-border rounded-lg px-2 py-1.5 text-xs font-mono outline-none focus:border-core-cyan"
          placeholder="Add a task..."
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
      {!error && tasks.length === 0 && <p className="text-xs text-core-text/50">No tasks yet.</p>}

      <ul className="space-y-1.5 max-h-48 overflow-y-auto">
        <AnimatePresence initial={false}>
          {tasks.map((task) => (
            <motion.li
              key={task.id}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 8 }}
              className="flex items-center gap-2 text-sm"
            >
              <button
                onClick={() => toggleDone(task)}
                className={`h-3.5 w-3.5 rounded-sm border flex-shrink-0 transition-colors ${
                  task.status === "done"
                    ? "bg-core-cyan border-core-cyan"
                    : "border-core-border hover:border-core-cyan"
                }`}
              />
              <span
                className={`font-mono text-xs truncate ${
                  task.status === "done" ? "line-through text-core-text/40" : "text-core-text/90"
                }`}
              >
                {task.title}
              </span>
            </motion.li>
          ))}
        </AnimatePresence>
      </ul>
    </GlassPanel>
  );
}
