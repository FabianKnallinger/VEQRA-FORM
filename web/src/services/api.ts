// API-Client der Weboberflaeche. Kommuniziert ausschliesslich mit der
// lokalen VEQRA Bridge (gleiche Herkunft oder Vite-Proxy auf 127.0.0.1).

import type {
  ActivityEntry,
  ChatResponse,
  Command,
  ContextMode,
  ElementsPage,
  HealthInfo,
  Project,
  ProposedCommand,
} from "../types/api";
import {
  demoActivity,
  demoChat,
  demoCommands,
  demoElements,
  demoHealth,
  demoProjects,
} from "./demo";

const DEMO_KEY = "veqra_demo_mode";

export function isDemoMode(): boolean {
  return localStorage.getItem(DEMO_KEY) === "1";
}

export function setDemoMode(enabled: boolean): void {
  localStorage.setItem(DEMO_KEY, enabled ? "1" : "0");
}

export class BridgeError extends Error {
  constructor(message: string, readonly status?: number) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    throw new BridgeError("VEQRA Bridge ist nicht erreichbar.");
  }
  if (!response.ok) {
    let detail = `Fehler ${response.status}`;
    try {
      const body = await response.json();
      if (body.detail) detail = String(body.detail);
    } catch {
      // Antwort ohne JSON-Körper
    }
    throw new BridgeError(detail, response.status);
  }
  return (await response.json()) as T;
}

export async function fetchHealth(): Promise<HealthInfo> {
  if (isDemoMode()) return demoHealth;
  return request<HealthInfo>("/api/v1/health");
}

export async function fetchProjects(): Promise<Project[]> {
  if (isDemoMode()) return demoProjects;
  const data = await request<{ projects: Project[] }>("/api/v1/projects");
  return data.projects;
}

export async function fetchProject(projectId: string): Promise<Project> {
  if (isDemoMode()) {
    const project = demoProjects.find((p) => p.project_id === projectId);
    if (project) return project;
    throw new BridgeError("Das Projekt wurde nicht gefunden.", 404);
  }
  return request<Project>(`/api/v1/projects/${encodeURIComponent(projectId)}`);
}

export interface ElementFilter {
  page?: number;
  element_type?: string;
  layer_id?: number;
  drawing_file_number?: number;
  attribute_id?: number;
  search?: string;
}

export async function fetchElements(
  projectId: string,
  filter: ElementFilter,
): Promise<ElementsPage> {
  if (isDemoMode()) return demoElements;
  const params = new URLSearchParams();
  if (filter.page) params.set("page", String(filter.page));
  if (filter.element_type) params.set("element_type", filter.element_type);
  if (filter.layer_id !== undefined) params.set("layer_id", String(filter.layer_id));
  if (filter.drawing_file_number !== undefined)
    params.set("drawing_file_number", String(filter.drawing_file_number));
  if (filter.attribute_id !== undefined)
    params.set("attribute_id", String(filter.attribute_id));
  if (filter.search) params.set("search", filter.search);
  return request<ElementsPage>(
    `/api/v1/projects/${encodeURIComponent(projectId)}/elements?${params.toString()}`,
  );
}

export async function fetchCommands(): Promise<Command[]> {
  if (isDemoMode()) return demoCommands;
  const data = await request<{ commands: Command[] }>("/api/v1/commands");
  return data.commands;
}

export async function fetchActivity(): Promise<ActivityEntry[]> {
  if (isDemoMode()) return demoActivity;
  const data = await request<{ activity: ActivityEntry[] }>("/api/v1/activity");
  return data.activity;
}

export async function createCommand(
  command: ProposedCommand,
  projectId: string | null,
  source: "web" | "ai",
): Promise<Command> {
  if (isDemoMode()) {
    throw new BridgeError("Im Demo-Modus werden keine Aufträge angelegt.");
  }
  return request<Command>("/api/v1/commands", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId, command, source }),
  });
}

export async function sendChat(
  message: string,
  projectId: string | null,
  contextMode: ContextMode,
  webSelectionUuids: string[],
): Promise<ChatResponse> {
  if (isDemoMode()) return demoChat(message);
  return request<ChatResponse>("/api/v1/ai/chat", {
    method: "POST",
    body: JSON.stringify({
      message,
      project_id: projectId,
      context_mode: contextMode,
      web_selection_uuids: webSelectionUuids,
    }),
  });
}

export async function fetchAiContext(
  projectId: string | null,
  contextMode: ContextMode,
): Promise<{ provider: string; context_preview: string }> {
  if (isDemoMode())
    return { provider: "demo (Beispieldaten)", context_preview: "Demo-Kontext." };
  const params = new URLSearchParams();
  if (projectId) params.set("project_id", projectId);
  params.set("context_mode", contextMode);
  return request(`/api/v1/ai/context?${params.toString()}`);
}

export function openWebSocket(onMessage: (data: unknown) => void): WebSocket | null {
  if (isDemoMode()) return null;
  try {
    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    const socket = new WebSocket(`${protocol}//${location.host}/ws/web`);
    socket.onmessage = (event) => {
      try {
        onMessage(JSON.parse(event.data));
      } catch {
        // Nachricht ignorieren
      }
    };
    return socket;
  } catch {
    return null;
  }
}
