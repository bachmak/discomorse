import type { ReactNode } from "react";

interface PanelProps {
  title: string;
  hint: string;
  children: ReactNode;
  className?: string;
}

export function Panel({ title, hint, children, className }: PanelProps) {
  return (
    <section className={className ? `panel ${className}` : "panel"}>
      <h2>{title}</h2>
      <p className="hint">{hint}</p>
      {children}
    </section>
  );
}
