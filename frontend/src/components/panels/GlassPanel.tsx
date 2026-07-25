import { PropsWithChildren } from "react";
import { motion } from "framer-motion";

interface GlassPanelProps {
  title?: string;
  className?: string;
}

export default function GlassPanel({
  title,
  className = "",
  children,
}: PropsWithChildren<GlassPanelProps>) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className={`glass-panel p-4 ${className}`}
    >
      {title && (
        <h3 className="font-hud text-xs text-core-cyan/80 mb-3">{title}</h3>
      )}
      {children}
    </motion.div>
  );
}
