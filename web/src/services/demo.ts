// Klar gekennzeichneter Demo-Modus mit Beispieldaten fuer die Entwicklung.
// Wird nur verwendet, wenn er in den Einstellungen ausdruecklich aktiviert ist.

import type {
  ActivityEntry,
  ChatResponse,
  Command,
  ElementsPage,
  HealthInfo,
  Project,
} from "../types/api";

const now = new Date().toISOString();

export const demoProjects: Project[] = [
  {
    project_id: "demo-projekt-1",
    name: "Demo: Bürogebäude Nord",
    path_hash: "d".repeat(64),
    allplan_version: "2026",
    machine_name: "DEMO-RECHNER",
    connector_id: "demo-connector",
    connector_version: "0.2.0",
    attributes: [
      { attribute_id: 405, name: "Projektnummer", value: "DEMO-001" },
      { attribute_id: 407, name: "Bauherr", value: "Beispiel GmbH" },
    ],
    element_statistics: {
      total_count: 1284,
      counts_by_type: { Wall: 320, Column: 96, Slab: 48, PythonPart: 12, Line3D: 808 },
      counts_by_layer: { STANDARD: 900, AR_WAND: 320, IN_STUETZE: 64 },
      warnings: ["Demo-Daten: kein echtes Projekt."],
    },
    snapshot_version: 3,
    synchronized_at: now,
    connection_status: "connected",
    drawing_files: [
      { number: 1, name: "Erdgeschoss", load_state: "active" },
      { number: 2, name: "Obergeschoss", load_state: "active_background" },
    ],
  },
  {
    project_id: "demo-projekt-2",
    name: "Demo: Halle Süd (Schnappschuss)",
    path_hash: "e".repeat(64),
    allplan_version: "2026",
    machine_name: "DEMO-RECHNER",
    connector_id: null,
    connector_version: "0.2.0",
    attributes: [],
    element_statistics: {
      total_count: 342,
      counts_by_type: { Wall: 80, Beam: 40, Slab: 12, Line3D: 210 },
      counts_by_layer: { STANDARD: 342 },
      warnings: [],
    },
    snapshot_version: 1,
    synchronized_at: "2026-07-10T09:00:00+00:00",
    connection_status: "disconnected",
    drawing_files: [{ number: 1, name: "Halle", load_state: "loaded" }],
  },
];

export const demoElements: ElementsPage = {
  total: 3,
  page: 1,
  page_size: 100,
  elements: [
    {
      element_uuid: "11111111-1111-1111-1111-111111111111",
      model_element_uuid: "21111111-1111-1111-1111-111111111111",
      element_type: "Wall",
      display_name: "Wand",
      layer_id: 3700,
      layer_name: "AR_WAND",
      drawing_file_number: 1,
      attributes: [{ attribute_id: 508, name: "Material", value: "Beton" }],
      geometry_kind: "Polyhedron3D",
      is_3d: true,
      bounding_box: { min: { x: 0, y: 0, z: 0 }, max: { x: 5000, y: 240, z: 2750 } },
      center: { x: 2500, y: 120, z: 1375 },
      child_uuids: [],
    },
    {
      element_uuid: "22222222-2222-2222-2222-222222222222",
      element_type: "Column",
      display_name: "Stütze",
      layer_id: 3800,
      layer_name: "IN_STUETZE",
      drawing_file_number: 1,
      attributes: [],
      geometry_kind: "Polyhedron3D",
      is_3d: true,
      bounding_box: { min: { x: 900, y: 900, z: 0 }, max: { x: 1200, y: 1200, z: 2750 } },
      center: { x: 1050, y: 1050, z: 1375 },
      child_uuids: [],
    },
    {
      element_uuid: "33333333-3333-3333-3333-333333333333",
      element_type: "PythonPart",
      display_name: "VEQRA Quader",
      layer_id: 1,
      layer_name: "STANDARD",
      drawing_file_number: 1,
      attributes: [],
      geometry_kind: "Polyhedron3D",
      is_3d: true,
      bounding_box: { min: { x: 0, y: 0, z: 0 }, max: { x: 8000, y: 1200, z: 4500 } },
      center: { x: 4000, y: 600, z: 2250 },
      child_uuids: [],
    },
  ],
};

export const demoCommands: Command[] = [
  {
    command_id: "demo-cmd-1",
    project_id: "demo-projekt-1",
    connector_id: "demo-connector",
    action: "create_cuboid",
    parameters: { length_mm: 8000, width_mm: 1200, height_mm: 4500, placement_mode: "pick_point" },
    source: "ai",
    summary_de: "Quader erstellen: Länge 8000 mm, Breite 1200 mm, Höhe 4500 mm.",
    status: "awaiting_confirmation",
    requires_allplan_confirmation: true,
    created_at: now,
    expires_at: now,
    updated_at: now,
  },
];

export const demoActivity: ActivityEntry[] = [
  { id: 3, event_type: "command_created", message: "Demo: Auftrag angelegt.", project_id: "demo-projekt-1", connector_id: null, created_at: now },
  { id: 2, event_type: "project_synced", message: "Demo: Projekt synchronisiert (Version 3).", project_id: "demo-projekt-1", connector_id: "demo-connector", created_at: now },
  { id: 1, event_type: "connector_registered", message: "Demo: Connector gekoppelt.", project_id: null, connector_id: "demo-connector", created_at: now },
];

export const demoHealth: HealthInfo = {
  status: "ok",
  product: "VEQRA FORM",
  bridge_version: "0.2.0",
  protocol_version: "1.0",
  ai_provider: "demo",
  server_time: now,
  connected_connectors: 1,
};

export function demoChat(message: string): ChatResponse {
  return {
    ok: true,
    provider: "demo (Beispieldaten)",
    reply_text_de:
      "Demo-Modus: Ich habe deine Nachricht erhalten: „" +
      message +
      "“. Im echten Betrieb würde hier die KI antworten.",
    context_preview: "Demo-Kontext: Bürogebäude Nord, 1284 Elemente.",
    proposed_commands: [],
  };
}
