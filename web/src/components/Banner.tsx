import type { ReactNode } from "react";

interface BannerProps {
  kind: "info" | "warn" | "error";
  children: ReactNode;
}

export function Banner({ kind, children }: BannerProps) {
  return <div className={`banner ${kind}`}>{children}</div>;
}
