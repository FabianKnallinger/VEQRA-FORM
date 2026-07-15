// Gemeinsame Typen der VEQRA FORM Weboberflaeche.
// Muss zum JSON-Protokoll in shared/schemas passen (Protokollversion 1.0).

export const PROTOCOL_VERSION = "1.0";

export interface Point {
  x: number;
  y: number;
  z: number;
}

export interface BoundingBox {
  min: Point;
  max: Point;
}

export interface ProjectAttribute {
  attribute_id: number;
  name?: string;
  value: string | number | boolean | null;
}

export interface DrawingFileInfo {
  number: number;
  name: string;
  load_state: string;
  synchronized_at?: string;
}

export interface ElementStatistics {
  total_count: number;
  counts_by_type: Record<string, number>;
  counts_by_layer: Record<string, number>;
  model_bounding_box?: BoundingBox | null;
  warnings: string[];
}

export interface Project {
  project_id: string;
  name: string;
  path_hash: string;
  allplan_version: string;
  machine_name: string;
  connector_id: string | null;
  connector_version: string;
  attributes: ProjectAttribute[];
  element_statistics: ElementStatistics;
  snapshot_version: number;
  synchronized_at: string | null;
  connection_status: "connected" | "disconnected";
  drawing_files: DrawingFileInfo[];
}

export interface ElementSummary {
  element_uuid: string;
  model_element_uuid?: string | null;
  element_type: string;
  element_subtype?: string | null;
  display_name?: string | null;
  layer_id?: number | null;
  layer_name?: string | null;
  drawing_file_number?: number | null;
  format_properties?: Record<string, number | boolean | null> | null;
  attributes: ProjectAttribute[];
  geometry_kind?: string | null;
  geometry_summary?: string | null;
  is_3d?: boolean | null;
  bounding_box?: BoundingBox | null;
  center?: Point | null;
  parent_uuid?: string | null;
  child_uuids: string[];
  is_modifiable?: boolean | null;
}

export interface ElementsPage {
  total: number;
  page: number;
  page_size: number;
  elements: ElementSummary[];
}

export type CommandStatus =
  | "pending"
  | "received"
  | "awaiting_confirmation"
  | "previewing"
  | "approved"
  | "executing"
  | "completed"
  | "rejected"
  | "failed"
  | "expired";

export interface Command {
  command_id: string;
  project_id: string | null;
  connector_id: string | null;
  action: string;
  parameters: Record<string, unknown>;
  source: string;
  summary_de: string;
  status: CommandStatus;
  requires_allplan_confirmation: boolean;
  created_at: string;
  expires_at: string;
  updated_at: string;
  results?: CommandResult[];
}

export interface CommandResult {
  status: CommandStatus;
  message: string | null;
  created_element_uuids: string[];
  modified_element_uuids: string[];
  reported_at: string;
}

export interface ActivityEntry {
  id: number;
  event_type: string;
  message: string;
  project_id: string | null;
  connector_id: string | null;
  created_at: string;
}

export interface HealthInfo {
  status: string;
  product: string;
  bridge_version: string;
  protocol_version: string;
  ai_provider: string;
  server_time: string;
  connected_connectors: number;
}

export interface ProposedCommand {
  protocol_version: string;
  action: string;
  parameters: Record<string, unknown>;
  requires_allplan_confirmation: boolean;
}

export interface ChatResponse {
  ok: boolean;
  provider: string;
  reply_text_de: string;
  context_preview: string;
  proposed_commands: ProposedCommand[];
}

export type ContextMode =
  | "current_project"
  | "active_drawing_files"
  | "allplan_selection"
  | "web_selection"
  | "project_attributes_only";
