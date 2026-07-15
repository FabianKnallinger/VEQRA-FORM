"""VEQRA FORM - HTTP-Client zur lokalen VEQRA Bridge.

Dieses Modul importiert bewusst KEINE Allplan-Module (testbar ohne Allplan).
Es verwendet ausschliesslich die Python-Standardbibliothek (urllib) und
spricht nur den lokalen Dienst auf 127.0.0.1 an.

- Kopplung ueber einmaligen Pairing-Token
- kurzlebiges Sitzungs-Token fuer alle weiteren Anfragen
- Heartbeat alle fuenf Sekunden in einem Hintergrund-Thread
  (der Thread fuehrt ausschliesslich HTTP-Aufrufe aus, niemals Allplan-API)
- Wiederholungslogik und lokale Warteschlange bei Verbindungsfehlern
"""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from collections import deque
from collections.abc import Callable

try:
    # Installiertes Plugin: Paketkontext wie im offiziellen Allplan 2025
    # PythonPart SDK (dort: "from . import GithubUtil")
    from .veqra_protocol import CONNECTOR_VERSION, MSG_BRIDGE_UNREACHABLE, utc_now_iso
except ImportError:
    # Codespace-Tests laden die Module ohne Paketkontext
    from veqra_protocol import CONNECTOR_VERSION, MSG_BRIDGE_UNREACHABLE, utc_now_iso

DEFAULT_BASE_URL = "http://127.0.0.1:8899"
HEARTBEAT_INTERVAL_SECONDS = 5.0
REQUEST_TIMEOUT_SECONDS = 10.0
MAX_QUEUED_SYNCS = 20


class BridgeUnreachableError(Exception):
    """Strukturierte Fehlerklasse: Bridge nicht erreichbar."""

    def __init__(self, message_de: str = MSG_BRIDGE_UNREACHABLE):
        super().__init__(message_de)
        self.message_de = message_de


class BridgeRequestError(Exception):
    """Strukturierte Fehlerklasse: Bridge hat die Anfrage abgelehnt."""

    def __init__(self, status_code: int, message_de: str):
        super().__init__(message_de)
        self.status_code = status_code
        self.message_de = message_de


class BridgeClient:
    """Client fuer die REST-API der VEQRA Bridge."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL,
                 opener: Callable | None = None):
        self.base_url = base_url.rstrip("/")
        self.connector_id: str | None = None
        self.session_token: str | None = None
        self.last_contact: str | None = None
        self.connected: bool = False

        self._opener = opener or urllib.request.urlopen
        self._offline_queue: deque[tuple[str, dict]] = deque(maxlen=MAX_QUEUED_SYNCS)
        self._heartbeat_timer: threading.Timer | None = None
        self._heartbeat_lock = threading.Lock()
        self._current_project_id: str | None = None
        self.pending_command_count: int = 0

    # ---- Basis-HTTP ----

    def _request(self, method: str, path: str, body: dict | None = None,
                 authenticated: bool = True) -> dict:
        url = self.base_url + path
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Content-Type": "application/json"}
        if authenticated:
            if not self.session_token or not self.connector_id:
                raise BridgeRequestError(401, "Keine gültige Sitzung. Bitte neu koppeln.")
            headers["Authorization"] = f"Bearer {self.session_token}"
            headers["X-Connector-Id"] = self.connector_id

        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with self._opener(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                payload = response.read()
                self.last_contact = utc_now_iso()
                self.connected = True
                return json.loads(payload.decode("utf-8")) if payload else {}
        except urllib.error.HTTPError as error:
            detail = "Die Anfrage wurde abgelehnt."
            try:
                detail = json.loads(error.read().decode("utf-8")).get("detail", detail)
            except (ValueError, AttributeError):
                pass
            raise BridgeRequestError(error.code, str(detail)) from error
        except (urllib.error.URLError, OSError, TimeoutError) as error:
            self.connected = False
            raise BridgeUnreachableError() from error

    # ---- Kopplung und Heartbeat ----

    def health(self) -> dict:
        return self._request("GET", "/api/v1/health", authenticated=False)

    def register(self, pairing_token: str, machine_name: str,
                 allplan_version: str) -> dict:
        result = self._request("POST", "/api/v1/connectors/register", {
            "pairing_token": pairing_token,
            "machine_name": machine_name,
            "allplan_version": allplan_version,
            "connector_version": CONNECTOR_VERSION,
        }, authenticated=False)
        self.connector_id = result["connector_id"]
        self.session_token = result["session_token"]
        return result

    def heartbeat(self, project_id: str | None = None) -> dict:
        result = self._request("POST", "/api/v1/connectors/heartbeat", {
            "connector_id": self.connector_id,
            "project_id": project_id,
        })
        self.pending_command_count = int(result.get("pending_commands", 0))
        self._flush_offline_queue()
        return result

    def start_heartbeat(self, project_id_getter: Callable[[], str | None]) -> None:
        """Startet den 5-Sekunden-Heartbeat im Hintergrund.

        Der Timer-Thread ruft ausschliesslich HTTP-Funktionen auf und
        beruehrt niemals die Allplan-API.
        """

        self.stop_heartbeat()

        def tick() -> None:
            try:
                self._current_project_id = project_id_getter()
                self.heartbeat(self._current_project_id)
            except (BridgeUnreachableError, BridgeRequestError):
                pass
            with self._heartbeat_lock:
                if self._heartbeat_timer is not None:
                    timer = threading.Timer(HEARTBEAT_INTERVAL_SECONDS, tick)
                    timer.daemon = True
                    self._heartbeat_timer = timer
                    timer.start()

        with self._heartbeat_lock:
            timer = threading.Timer(HEARTBEAT_INTERVAL_SECONDS, tick)
            timer.daemon = True
            self._heartbeat_timer = timer
            timer.start()

    def stop_heartbeat(self) -> None:
        with self._heartbeat_lock:
            if self._heartbeat_timer is not None:
                self._heartbeat_timer.cancel()
                self._heartbeat_timer = None

    # ---- Synchronisierung mit Warteschlange ----

    def sync_project(self, payload: dict) -> dict:
        return self._sync("/api/v1/sync/project", payload)

    def sync_selection(self, payload: dict) -> dict:
        return self._sync("/api/v1/sync/selection", payload)

    def sync_elements(self, payload: dict) -> dict:
        return self._sync("/api/v1/sync/elements", payload)

    def _sync(self, path: str, payload: dict) -> dict:
        try:
            return self._request("POST", path, payload)
        except BridgeUnreachableError:
            # Lokale Warteschlange: wird beim naechsten erfolgreichen
            # Heartbeat erneut gesendet
            self._offline_queue.append((path, payload))
            raise

    def _flush_offline_queue(self) -> None:
        while self._offline_queue:
            path, payload = self._offline_queue[0]
            try:
                self._request("POST", path, payload)
                self._offline_queue.popleft()
            except (BridgeUnreachableError, BridgeRequestError):
                break

    # ---- Auftraege ----

    def pending_commands(self, project_id: str | None = None) -> list[dict]:
        path = "/api/v1/commands/pending"
        if project_id:
            path += f"?project_id={project_id}"
        return self._request("GET", path).get("commands", [])

    def mark_received(self, command_id: str) -> dict:
        return self._request("POST", f"/api/v1/commands/{command_id}/received")

    def report_result(self, command_id: str, status: str, message: str | None = None,
                      created_uuids: list[str] | None = None,
                      modified_uuids: list[str] | None = None) -> dict:
        return self._request("POST", f"/api/v1/commands/{command_id}/result", {
            "connector_id": self.connector_id,
            "status": status,
            "message": message,
            "created_element_uuids": created_uuids or [],
            "modified_element_uuids": modified_uuids or [],
        })

    @property
    def queued_sync_count(self) -> int:
        return len(self._offline_queue)
