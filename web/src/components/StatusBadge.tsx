import type { CommandStatus } from "../types/api";

const STATUS_LABELS: Record<CommandStatus, string> = {
  pending: "Ausstehend",
  received: "Abgerufen",
  awaiting_confirmation: "Wartet auf Bestätigung",
  previewing: "Vorschau läuft",
  approved: "Bestätigt",
  executing: "Wird ausgeführt",
  completed: "Abgeschlossen",
  rejected: "Abgelehnt",
  failed: "Fehlgeschlagen",
  expired: "Abgelaufen",
};

const STATUS_KIND: Record<CommandStatus, string> = {
  pending: "",
  received: "",
  awaiting_confirmation: "warn",
  previewing: "warn",
  approved: "ok",
  executing: "warn",
  completed: "ok",
  rejected: "error",
  failed: "error",
  expired: "error",
};

export function StatusBadge({ status }: { status: CommandStatus }) {
  return <span className={`badge ${STATUS_KIND[status]}`}>{STATUS_LABELS[status]}</span>;
}

export function statusLabel(status: CommandStatus): string {
  return STATUS_LABELS[status];
}
