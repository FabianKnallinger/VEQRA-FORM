interface StatusDotProps {
  kind: "ok" | "warn" | "error" | "muted";
  label?: string;
}

export function StatusDot({ kind, label }: StatusDotProps) {
  return (
    <span>
      <span className={`dot ${kind}`} />
      {label}
    </span>
  );
}
