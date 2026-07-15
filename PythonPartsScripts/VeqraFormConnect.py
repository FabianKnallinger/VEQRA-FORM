"""VEQRA FORM - Verbindungswerkzeug (Interactor PythonPart, Adapter-Schicht).

Aufbau nach den offiziellen Allplan 2025 Beispielen:
- InteractorExamples/GeneralModification/CopyElements.py
  (Interactor mit Palette, Elementauswahl, Punkteingabe)
- InteractorExamples/Elements3DInteractor.py
  (Vorschau mit DrawElementPreview, Erstellung mit CreateElements)
- InteractorExamples/GeneralModification/ChangeAttributes.py
  (ElementsAttributeService.ChangeAttributes)
- BasisExamples/PythonParts/MovePythonPart.py
  (GetElements, ModifyElements, Translationsmatrix)
- ModelObjectExamples/General/ShowObjectInformation.py
  (Elementinformationen)

Sicherheitsregeln dieses Werkzeugs:
- Beim Start erfolgt keine Modellaenderung.
- Modellaendernde Auftraege werden erst nach aktiver Bestaetigung
  (Schaltflaeche "Ausführen") ausgefuehrt.
- Kein eval, kein exec, keine Shell-Aufrufe, kein Loeschen von Elementen.
"""

from __future__ import annotations

import platform
import webbrowser
from typing import Any, cast

# Importe wie im offiziellen Beispiel CopyElements.py
import NemAll_Python_AllplanSettings as AllplanSettings  # noqa: F401 (Projektpfad via Reader)
import NemAll_Python_BaseElements as AllplanBaseEle
import NemAll_Python_BasisElements as AllplanBasisEle
import NemAll_Python_Geometry as AllplanGeo
import NemAll_Python_IFW_ElementAdapter as AllplanEleAdapter
import NemAll_Python_IFW_Input as AllplanIFW
import NemAll_Python_Utility as AllplanUtil
from BaseInteractor import BaseInteractor
from BuildingElement import BuildingElement
from BuildingElementComposite import BuildingElementComposite
from BuildingElementControlProperties import BuildingElementControlProperties
from BuildingElementListService import BuildingElementListService
from BuildingElementPaletteService import BuildingElementPaletteService
from CreateElementResult import CreateElementResult
from StringTableService import StringTableService

try:
    from . import veqra_bridge_client, veqra_model_reader, veqra_protocol
except ImportError:
    import veqra_bridge_client
    import veqra_model_reader
    import veqra_protocol

print("Load VeqraFormConnect.py")

# Der Client bleibt fuer die Dauer der Allplan-Sitzung bestehen,
# damit die Kopplung nicht bei jedem Werkzeugstart wiederholt werden muss.
_CLIENT: veqra_bridge_client.BridgeClient | None = None


def _client() -> veqra_bridge_client.BridgeClient:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = veqra_bridge_client.BridgeClient()
    return _CLIENT


def check_allplan_version(_build_ele: BuildingElement, _version: str) -> bool:
    """Einstiegspunkt wie im offiziellen Beispiel CopyElements.py."""

    return True


def create_interactor(coord_input              : AllplanIFW.CoordinateInput,
                      _pyp_path                : str,
                      _global_str_table_service: StringTableService,
                      build_ele_list           : list[BuildingElement],
                      build_ele_composite      : BuildingElementComposite,
                      control_props_list       : list[BuildingElementControlProperties],
                      _modify_uuid_list        : list) -> object:
    """Einstiegspunkt wie im offiziellen Beispiel CopyElements.py."""

    return VeqraFormConnect(coord_input, build_ele_list, build_ele_composite,
                            control_props_list)


class VeqraFormConnect(BaseInteractor):
    """Verbindung zwischen Allplan und der lokalen VEQRA Bridge."""

    def __init__(self,
                 coord_input        : AllplanIFW.CoordinateInput,
                 build_ele_list     : list[BuildingElement],
                 build_ele_composite: BuildingElementComposite,
                 control_props_list : list[BuildingElementControlProperties]):
        self.coord_input = coord_input
        self.build_ele_list = build_ele_list
        self.build_ele = cast(BuildingElement, build_ele_list[0])

        self.client = _client()
        self.current_project_id: str | None = None
        self.selected_elements: AllplanEleAdapter.BaseElementAdapterList | None = None
        self.selection_summaries: list[dict] = []
        self.active_command: dict | None = None
        self.post_element_selection: AllplanIFW.PostElementSelection | None = None
        self.cuboid_model_ele_list: list = []
        self.input_mode = "idle"  # idle | element_selection | cuboid_point

        # Palette wie im offiziellen Beispiel CopyElements.py
        self.palette_service = BuildingElementPaletteService(
            build_ele_list, build_ele_composite, self.build_ele.script_name,
            control_props_list, self.build_ele.pyp_file_name)
        self.palette_service.show_palette(self.build_ele.pyp_file_name)

        # Leerlauf-Eingabe wie im offiziellen Beispiel
        # DrawingFileDataInteractor.py ("Execute by button click")
        self._start_idle_input()

        # Beim Start: nur lesende Statusanzeige, keine Modellaenderung.
        # Ein Fehler hier darf den Werkzeugstart niemals verhindern.
        try:
            self._refresh_connection_status(register_if_needed=False)
        except Exception as error:  # Details nur im Trace, nie in der Palette
            print("VeqraFormConnect: Statusabfrage beim Start fehlgeschlagen:", error)
            self._set_status(veqra_protocol.MSG_BRIDGE_UNREACHABLE)
        self.palette_service.update_palette(-1, True)

    # ------------------------------------------------------------------
    # Eingabesteuerung
    # ------------------------------------------------------------------

    def _start_idle_input(self) -> None:
        """Neutraler Leerlauf; Klicks im Leerlauf aendern nichts am Modell.

        InitFirstElementInput wie in den offiziellen button-gesteuerten
        Interactor-Beispielen (z. B. DrawingFileDataInteractor.py:
        "Execute by button click").
        """

        self.coord_input.InitFirstElementInput(
            AllplanIFW.InputStringConvert("VEQRA FORM: Aktionen über die Palette wählen"))
        self.input_mode = "idle"

    def _start_element_selection(self) -> None:
        """Elementauswahl wie im offiziellen Beispiel CopyElements.py."""

        sel_setting = AllplanIFW.ElementSelectFilterSetting()
        self.post_element_selection = AllplanIFW.PostElementSelection()
        AllplanIFW.InputFunctionStarter.StartElementSelect(
            "Elemente für den Auswahl-Scan wählen",
            sel_setting, self.post_element_selection, True)
        self.input_mode = "element_selection"

    def _start_cuboid_point_input(self) -> None:
        self.coord_input.InitNextPointInput(
            AllplanIFW.InputStringConvert("Einfügepunkt für den Quader wählen"))
        self.input_mode = "cuboid_point"

    # ------------------------------------------------------------------
    # Palette
    # ------------------------------------------------------------------

    def _set_status(self, message: str) -> None:
        self.build_ele.StatusText.value = message

    def _show_error(self, message: str) -> None:
        """Fehler sichtbar machen: Dialogbox + Statuszeile (Details im Trace).

        Die Statuszeile der Palette schneidet lange Texte ab; wichtige
        Meldungen erscheinen deshalb zusaetzlich als Nachrichtenbox
        (ShowMessageBox wie in offiziellen Beispielen, z. B. MWSPlacement.py).
        """

        self._set_status(message)
        print("VEQRA FORM:", message)
        AllplanUtil.ShowMessageBox(message, AllplanUtil.MB_OK)

    def _update_palette(self) -> None:
        self.palette_service.update_palette(-1, True)

    def _refresh_connection_status(self, register_if_needed: bool) -> None:
        client = self.client
        try:
            health = client.health()
            bridge_ok = health.get("status") == "ok"
        except (veqra_bridge_client.BridgeUnreachableError,
                veqra_bridge_client.BridgeRequestError):
            bridge_ok = False

        if bridge_ok and register_if_needed and client.session_token is None:
            token = str(self.build_ele.PairingToken.value).strip()
            if not token:
                # Auto-Kopplung: Token direkt aus der lokalen Bridge-Ablage
                # lesen (gleicher Rechner, gleicher Benutzer)
                token = veqra_protocol.read_local_pairing_token() or ""
                if token:
                    self.build_ele.PairingToken.value = token
            if not token:
                self._set_status(veqra_protocol.MSG_NOT_PAIRED)
                self.build_ele.ConnectionText.value = "Getrennt"
                return
            try:
                client.register(token, platform.node(),
                                veqra_model_reader.get_allplan_version())
                client.start_heartbeat(lambda: self.current_project_id)
                self._set_status("Die Kopplung mit der VEQRA Bridge war erfolgreich.")
            except veqra_bridge_client.BridgeRequestError as error:
                self._set_status(error.message_de)
            except veqra_bridge_client.BridgeUnreachableError:
                bridge_ok = False

        if not bridge_ok:
            self.build_ele.ConnectionText.value = "Getrennt"
            self.build_ele.WebHintText.value = veqra_protocol.MSG_BRIDGE_UNREACHABLE
            if register_if_needed:
                self._set_status(veqra_protocol.MSG_BRIDGE_UNREACHABLE)
            return

        connected = client.session_token is not None
        self.build_ele.ConnectionText.value = (
            "Verbunden" if connected else "Bridge erreichbar, nicht gekoppelt")
        self.build_ele.ConnectorIdText.value = client.connector_id or "–"
        self.build_ele.LastContactText.value = client.last_contact or "–"
        self.build_ele.WebAddressText.value = client.base_url
        self.build_ele.WebHintText.value = ""
        if connected:
            self.build_ele.PendingCountText.value = str(client.pending_command_count)

    # ------------------------------------------------------------------
    # Schaltflaechen (EventIds aus der PYP-Datei)
    # ------------------------------------------------------------------

    def on_control_event(self, event_id: int) -> None:
        build_ele = self.build_ele
        try:
            if event_id == build_ele.CHECK_CONNECTION:
                self._refresh_connection_status(register_if_needed=True)
            elif event_id == build_ele.SYNC_PROJECT:
                self._sync_project()
            elif event_id == build_ele.READ_SELECTION:
                self._start_element_selection()
                self._set_status("Bitte Elemente im Zeichenbereich wählen und bestätigen.")
            elif event_id == build_ele.SYNC_SELECTION:
                self._sync_selection()
            elif event_id == build_ele.CHECK_COMMAND:
                self._check_command()
            elif event_id == build_ele.PREVIEW_COMMAND:
                self._preview_command()
            elif event_id == build_ele.EXECUTE_COMMAND:
                self._execute_command()
            elif event_id == build_ele.REJECT_COMMAND:
                self._reject_command()
            elif event_id == build_ele.OPEN_WEB:
                self._open_web()
            elif event_id == build_ele.SEND_AI:
                self._send_ai_prompt()
        except veqra_bridge_client.BridgeUnreachableError:
            self._show_error(veqra_protocol.MSG_BRIDGE_UNREACHABLE
                             + " Bitte VeqraBridge starten und erneut versuchen.")
        except veqra_bridge_client.BridgeRequestError as error:
            self._show_error(error.message_de)
        except veqra_protocol.CommandValidationError as error:
            self._show_error(error.message_de)
        except Exception as error:  # niemals ein roher Traceback in der Palette
            import traceback
            print("VEQRA FORM: unerwarteter Fehler bei Ereignis", event_id)
            traceback.print_exc()
            self._show_error("Die Aktion ist fehlgeschlagen. "
                             f"({type(error).__name__}) "
                             "Details stehen im Allplan-Trace-Fenster.")

        self._update_palette()

    # ------------------------------------------------------------------
    # Synchronisierung
    # ------------------------------------------------------------------

    def _require_session(self) -> bool:
        if self.client.session_token is None:
            self._set_status(veqra_protocol.MSG_NOT_PAIRED)
            return False
        return True

    def _document(self) -> AllplanEleAdapter.DocumentAdapter:
        # GetInputViewDocument wie im offiziellen Beispiel CopyElements.py
        return self.coord_input.GetInputViewDocument()

    def _sync_project(self) -> None:
        """Projektsynchronisierung; jeder Teilschritt ist einzeln abgesichert."""

        if not self._require_session():
            return

        doc = self._document()
        if doc is None:
            self._show_error("Kein aktives Dokument (DocumentAdapter fehlt). "
                             "Bitte ein Teilbild öffnen.")
            return

        self._set_status("Synchronisierung läuft…")

        path = veqra_model_reader.get_project_path()
        project_id = veqra_protocol.project_id_from_path(path)
        self.current_project_id = project_id
        print("VEQRA FORM: Projektscan startet, Projekt-ID", project_id)

        statistics = veqra_model_reader.project_scan(doc)
        print("VEQRA FORM: Projektscan fertig,",
              statistics.get("total_count", 0), "Elemente")

        try:
            drawing_files = veqra_model_reader.get_drawing_files()
        except Exception as error:
            print("VEQRA FORM: Teilbilder nicht lesbar:", error)
            drawing_files = []

        try:
            allplan_version = veqra_model_reader.get_allplan_version()
        except Exception:
            allplan_version = ""

        payload = {
            "protocol_version": veqra_protocol.PROTOCOL_VERSION,
            "connector_id": self.client.connector_id,
            "project_id": project_id,
            "name": veqra_model_reader.get_project_name(),
            "path_hash": veqra_protocol.hash_project_path(path),
            "allplan_version": allplan_version,
            "machine_name": platform.node(),
            "connector_version": veqra_protocol.CONNECTOR_VERSION,
            "attributes": veqra_model_reader.get_project_attributes(doc),
            "drawing_files": drawing_files,
            "element_statistics": statistics,
        }
        result = self.client.sync_project(payload)

        build_ele = self.build_ele
        build_ele.ProjectNameText.value = payload["name"]
        build_ele.ProjectIdText.value = project_id
        build_ele.DrawingFilesText.value = ", ".join(
            (f["name"] or str(f["number"])) for f in drawing_files) or "–"
        build_ele.ElementCountText.value = str(statistics["total_count"])
        build_ele.LastSyncText.value = result.get("synchronized_at", "–")
        self._set_status(veqra_protocol.MSG_PROJECT_SYNCED
                         + f" ({statistics['total_count']} Elemente)")

    def _read_selection_result(self) -> None:
        """Uebernimmt die abgeschlossene Elementauswahl (wie CopyElements.py)."""

        if self.post_element_selection is None:
            return
        doc = self._document()
        self.selected_elements = self.post_element_selection.GetSelectedElements(doc)
        self.post_element_selection = None

        summaries, warnings = veqra_model_reader.summarize_elements(
            self.selected_elements, doc, "Auswahl")
        self.selection_summaries = summaries

        types: dict[str, int] = {}
        for summary in summaries:
            types[summary["element_type"]] = types.get(summary["element_type"], 0) + 1

        build_ele = self.build_ele
        build_ele.SelectionCountText.value = str(len(summaries))
        build_ele.SelectionTypesText.value = ", ".join(
            f"{name} ({count})" for name, count in sorted(types.items())) or "–"

        message = f"{len(summaries)} Element(e) gelesen."
        if warnings:
            message += " " + warnings[0]
        self._set_status(message)

    def _sync_selection(self) -> None:
        if not self._require_session():
            return
        if not self.selection_summaries:
            self._set_status(veqra_protocol.MSG_NO_SELECTION
                             + " Bitte zuerst „Auswahl lesen“ verwenden.")
            return
        if self.current_project_id is None:
            self._set_status("Bitte zuerst „Projekt synchronisieren“ ausführen.")
            return

        result = self.client.sync_selection({
            "protocol_version": veqra_protocol.PROTOCOL_VERSION,
            "connector_id": self.client.connector_id,
            "project_id": self.current_project_id,
            "source": "selection",
            "elements": self.selection_summaries,
        })
        if result.get("truncated"):
            self._set_status(veqra_protocol.MSG_SYNC_TRUNCATED)
        else:
            self._set_status(veqra_protocol.MSG_SELECTION_SYNCED)

    def _sync_after_change(self, adapters) -> None:
        """Synchronisiert betroffene Elemente nach einer Aenderung."""

        if self.current_project_id is None or not adapters:
            return
        doc = self._document()
        summaries, _ = veqra_model_reader.summarize_elements(adapters, doc, "Änderung")
        if summaries:
            self.client.sync_elements({
                "protocol_version": veqra_protocol.PROTOCOL_VERSION,
                "connector_id": self.client.connector_id,
                "project_id": self.current_project_id,
                "source": "after_change",
                "elements": summaries,
            })

    # ------------------------------------------------------------------
    # Auftraege
    # ------------------------------------------------------------------

    def _check_command(self) -> None:
        if not self._require_session():
            return

        commands = self.client.pending_commands(self.current_project_id)
        self.build_ele.PendingCountText.value = str(len(commands))

        if not commands:
            self.active_command = None
            self.build_ele.NextCommandText.value = "–"
            self._set_status(veqra_protocol.MSG_NO_PENDING_COMMAND)
            return

        command = commands[0]

        # Zweite, unabhaengige Validierung im Plugin
        try:
            checked = veqra_protocol.validate_command({
                "protocol_version": veqra_protocol.PROTOCOL_VERSION,
                "action": command.get("action"),
                "parameters": command.get("parameters", {}),
            })
        except veqra_protocol.CommandValidationError as error:
            self.client.mark_received(command["command_id"])
            self.client.report_result(command["command_id"], "failed",
                                      error.message_de)
            self._set_status(error.message_de)
            return

        command["parameters"] = checked
        self.active_command = command
        self.client.mark_received(command["command_id"])
        self.client.report_result(command["command_id"], "awaiting_confirmation",
                                  veqra_protocol.MSG_COMMAND_WAITING)

        summary = veqra_protocol.summarize_command_de(command["action"], checked)
        self.build_ele.NextCommandText.value = summary
        self._set_status(f"{veqra_protocol.MSG_COMMAND_WAITING} ({summary})")

    def _preview_command(self) -> None:
        command = self.active_command
        if command is None:
            self._set_status(veqra_protocol.MSG_NO_PENDING_COMMAND)
            return

        self.client.report_result(command["command_id"], "previewing",
                                  "Vorschau in Allplan gestartet.")
        action = command["action"]
        parameters = command["parameters"]

        if action == "create_cuboid":
            self._build_cuboid_model_elements(parameters)
            # Vorschau im Ursprung; die eigentliche Vorschau folgt dem
            # Fadenkreuz waehrend der Punkteingabe nach "Ausführen"
            AllplanBaseEle.DrawElementPreview(
                self._document(), AllplanGeo.Matrix3D(),
                self.cuboid_model_ele_list, False, None)
            self._set_status("Vorschau: Quader im Ursprung. „Ausführen“ startet die "
                             "Punkteingabe mit Vorschau am Fadenkreuz.")
        elif action == "move_selected_elements":
            if not self._selection_available():
                return
            # Vorschau der verschobenen Elemente: GetElements + ElementTransform
            # + DrawElementPreview (Muster aus MovePythonPart.py und
            # Elements3DInteractor.py)
            objects = AllplanBaseEle.GetElements(self.selected_elements)
            matrix = self._translation_matrix(parameters)
            AllplanBaseEle.ElementTransform(matrix, objects)
            AllplanBaseEle.DrawElementPreview(
                self._document(), AllplanGeo.Matrix3D(), objects, False, None)
            self._set_status("Vorschau: verschobene Auswahl wird angezeigt.")
        elif action == "set_selected_attributes":
            if not self._selection_available():
                return
            names = ", ".join(str(a["attribute_id"]) for a in parameters["attributes"])
            self._set_status(f"Vorschau: Attribute {names} würden auf "
                             f"{len(self.selection_summaries)} Element(e) gesetzt.")
        else:
            self._set_status("Dieser Auftrag ist nur lesend; keine Vorschau nötig.")

    def _execute_command(self) -> None:
        command = self.active_command
        if command is None:
            self._set_status(veqra_protocol.MSG_NO_PENDING_COMMAND)
            return
        if not self._require_session():
            return

        command_id = command["command_id"]
        action = command["action"]
        parameters = command["parameters"]

        self.client.report_result(command_id, "approved",
                                  "In Allplan bestätigt.")

        if action == "create_cuboid":
            # Erst die Punkteingabe; die Erstellung erfolgt nach dem Klick
            self._build_cuboid_model_elements(parameters)
            self.client.report_result(command_id, "executing",
                                      "Punkteingabe in Allplan läuft.")
            self._start_cuboid_point_input()
            self._set_status("Bitte den Einfügepunkt im Zeichenbereich anklicken "
                             "(ESC bricht ab).")
            return

        self.client.report_result(command_id, "executing", "Wird ausgeführt.")

        if action == "move_selected_elements":
            self._execute_move(command_id, parameters)
        elif action == "set_selected_attributes":
            self._execute_set_attributes(command_id, parameters)
        elif action in ("inspect_project", "synchronize_project"):
            self._sync_project()
            self.client.report_result(command_id, "completed",
                                      veqra_protocol.MSG_PROJECT_SYNCED)
            self.active_command = None
        elif action in ("inspect_selection", "synchronize_selection"):
            if self.selection_summaries:
                self._sync_selection()
                self.client.report_result(command_id, "completed",
                                          veqra_protocol.MSG_SELECTION_SYNCED)
            else:
                self.client.report_result(command_id, "failed",
                                          veqra_protocol.MSG_NO_SELECTION)
                self._set_status(veqra_protocol.MSG_NO_SELECTION)
            self.active_command = None

    def _selection_available(self) -> bool:
        if not self.selected_elements or not self.selection_summaries:
            self._set_status(veqra_protocol.MSG_NO_SELECTION
                             + " Bitte zuerst „Auswahl lesen“ verwenden.")
            return False
        return True

    @staticmethod
    def _translation_matrix(parameters: dict) -> AllplanGeo.Matrix3D:
        # Translationsmatrix wie im offiziellen Beispiel MovePythonPart.py
        # (Matrix3D().SetTranslation(Vector3D(...)))
        matrix = AllplanGeo.Matrix3D()
        matrix.SetTranslation(AllplanGeo.Vector3D(
            float(parameters["dx_mm"]), float(parameters["dy_mm"]),
            float(parameters["dz_mm"])))
        return matrix

    def _execute_move(self, command_id: str, parameters: dict) -> None:
        if not self._selection_available():
            self.client.report_result(command_id, "failed",
                                      veqra_protocol.MSG_NO_SELECTION)
            return

        doc = self._document()
        # Dokumentierter Ablauf "Specific modification":
        # GetElements -> Aenderung -> ModifyElements
        # (Handbuch "Model access/Modification" und Beispiel MovePythonPart.py);
        # ElementTransform gemaess offizieller API-Referenz
        # NemAll_Python_BaseElements.ElementTransform(Matrix3D, list)
        objects = AllplanBaseEle.GetElements(self.selected_elements)
        if not objects:
            self.client.report_result(command_id, "failed",
                                      veqra_protocol.MSG_ELEMENTS_NOT_MODIFIABLE)
            self._set_status(veqra_protocol.MSG_ELEMENTS_NOT_MODIFIABLE)
            return

        AllplanBaseEle.ElementTransform(self._translation_matrix(parameters), objects)
        AllplanBaseEle.ModifyElements(doc, objects)

        modified_uuids = [summary["element_uuid"] for summary in self.selection_summaries]
        self.client.report_result(command_id, "completed",
                                  veqra_protocol.MSG_COMMAND_DONE,
                                  modified_uuids=modified_uuids)
        self._sync_after_change(self.selected_elements)
        self.active_command = None
        self._set_status("Die Auswahl wurde verschoben und erneut synchronisiert. "
                         "Hinweis: Elementtypen ohne dokumentierte "
                         "Änderungsfunktion bleiben unverändert.")

    def _execute_set_attributes(self, command_id: str, parameters: dict) -> None:
        if not self._selection_available():
            self.client.report_result(command_id, "failed",
                                      veqra_protocol.MSG_NO_SELECTION)
            return

        # ElementsAttributeService.ChangeAttributes(Attributliste, Elemente)
        # wie im offiziellen Beispiel ChangeAttributes.py
        attribute_tuples = [(entry["attribute_id"], entry["value"])
                            for entry in parameters["attributes"]]
        AllplanBaseEle.ElementsAttributeService.ChangeAttributes(
            attribute_tuples, self.selected_elements)

        modified_uuids = [summary["element_uuid"] for summary in self.selection_summaries]
        self.client.report_result(command_id, "completed",
                                  veqra_protocol.MSG_COMMAND_DONE,
                                  modified_uuids=modified_uuids)
        self._sync_after_change(self.selected_elements)
        self.active_command = None
        self._set_status("Die Attribute wurden gesetzt und die Elemente erneut "
                         "synchronisiert.")

    def _reject_command(self) -> None:
        command = self.active_command
        if command is None:
            self._set_status(veqra_protocol.MSG_NO_PENDING_COMMAND)
            return
        self.client.report_result(command["command_id"], "rejected",
                                  veqra_protocol.MSG_COMMAND_REJECTED)
        self.active_command = None
        self.build_ele.NextCommandText.value = "–"
        self._set_status(veqra_protocol.MSG_COMMAND_REJECTED)

    def _send_ai_prompt(self) -> None:
        """KI-Assistent in der Palette: Kontext waehlen, Prompt senden.

        Die KI laeuft ausschliesslich in der Bridge und darf nur die fest
        definierten Werkzeuge vorschlagen. Vorgeschlagene Auftraege werden
        eingereiht und erst nach „Auftrag prüfen“/„Ausführen“ ausgefuehrt.
        """

        build_ele = self.build_ele
        prompt = str(build_ele.AiPrompt.value).strip()
        if not prompt:
            self._show_error("Bitte zuerst eine Anweisung in das Feld "
                             "„Anweisung“ eintragen, z. B.: "
                             "Erstelle einen Quader 8000 x 1200 x 4500.")
            return

        # Kontextwahl: 0 = aktuelles Projekt, 1 = aktuelle Auswahl (Bereich)
        use_selection = int(build_ele.AiContext.value) == 1
        context_mode = "allplan_selection" if use_selection else "current_project"

        # Der gewaehlte Bereich muss synchronisiert sein, damit die KI ihn kennt
        if self.current_project_id is None:
            self._sync_project()
        if use_selection:
            if not self.selection_summaries:
                self._show_error(veqra_protocol.MSG_NO_SELECTION
                                 + " Bitte zuerst „Auswahl lesen“ verwenden, "
                                 "um den Bereich festzulegen.")
                return
            self._sync_selection()

        self._set_status("Anfrage an die KI läuft…")
        result = self.client.ai_chat(prompt, self.current_project_id, context_mode)

        reply = str(result.get("reply_text_de", ""))
        proposed = result.get("proposed_commands", [])

        queued_summaries = []
        for command in proposed:
            created = self.client.create_command(command, self.current_project_id)
            queued_summaries.append(created.get("summary_de", command.get("action", "")))

        build_ele.AiReplyText.value = reply[:250] if reply else "–"
        if queued_summaries:
            build_ele.PendingCountText.value = str(len(queued_summaries))
            build_ele.NextCommandText.value = queued_summaries[0]
            message = (f"KI ({result.get('provider', '')}): {reply}\n\n"
                       f"{len(queued_summaries)} Auftrag/Aufträge eingereiht:\n- "
                       + "\n- ".join(queued_summaries)
                       + "\n\nWeiter mit „Auftrag prüfen“, „Vorschau“ und „Ausführen“.")
            self._set_status("Auftrag eingereiht – bitte unter „Aufträge“ prüfen.")
        else:
            message = f"KI ({result.get('provider', '')}): {reply}"
            self._set_status("Die KI hat keinen ausführbaren Auftrag vorgeschlagen.")

        # Antwort vollstaendig anzeigen (die Statuszeile schneidet Text ab)
        AllplanUtil.ShowMessageBox(message, AllplanUtil.MB_OK)

    def _open_web(self) -> None:
        try:
            self.client.health()
        except veqra_bridge_client.BridgeUnreachableError:
            self._set_status(veqra_protocol.MSG_BRIDGE_UNREACHABLE
                             + " Bitte zuerst VeqraBridge starten.")
            return
        webbrowser.open(self.client.base_url)
        self._set_status("Die Weboberfläche wurde im Browser geöffnet.")

    # ------------------------------------------------------------------
    # Quader-Erstellung (wiederverwendete Logik des Quader-Werkzeugs)
    # ------------------------------------------------------------------

    def _build_cuboid_model_elements(self, parameters: dict) -> None:
        """Erzeugt die Quader-Modellelemente (noch ohne Modellaenderung).

        Geometrie wie im offiziellen Beispiel Elements3DInteractor.py
        (Polyhedron3D.CreateCuboid, ModelElement3D, CommonProperties).
        """

        common_properties = AllplanBaseEle.CommonProperties()
        common_properties.GetGlobalProperties()

        cuboid = AllplanGeo.Polyhedron3D.CreateCuboid(
            float(parameters["length_mm"]), float(parameters["width_mm"]),
            float(parameters["height_mm"]))

        self.cuboid_model_ele_list = [
            AllplanBasisEle.ModelElement3D(common_properties, cuboid)]

    def _draw_cuboid_preview(self, input_pnt: AllplanGeo.Point3D) -> None:
        """Vorschau am Fadenkreuz wie im offiziellen Beispiel Elements3DInteractor.py."""

        command = self.active_command
        if command is None:
            return
        self._build_cuboid_model_elements(command["parameters"])
        AllplanBaseEle.ElementTransform(AllplanGeo.Vector3D(input_pnt), 0, 0, 0,
                                        self.cuboid_model_ele_list)
        AllplanBaseEle.DrawElementPreview(self._document(), AllplanGeo.Matrix3D(),
                                          self.cuboid_model_ele_list, False, None)

    def _create_cuboid_at(self, input_pnt: AllplanGeo.Point3D) -> None:
        """Erstellt den Quader nach bestaetigter Punkteingabe.

        CreateElements wie im offiziellen Beispiel Elements3DInteractor.py;
        die Rueckgaengig-Funktion ist durch createUndoStep=True gegeben
        (offizielle API-Referenz NemAll_Python_BaseElements.CreateElements).
        """

        command = self.active_command
        if command is None:
            return

        self._build_cuboid_model_elements(command["parameters"])
        AllplanBaseEle.ElementTransform(AllplanGeo.Vector3D(input_pnt), 0, 0, 0,
                                        self.cuboid_model_ele_list)
        created = AllplanBaseEle.CreateElements(
            self._document(), AllplanGeo.Matrix3D(), self.cuboid_model_ele_list, [], None)

        created_uuids: list[str] = []
        created_list = None
        try:
            created_list = list(created) if created is not None else []
            created_uuids = [str(adapter.GetElementUUID()) for adapter in created_list]
        except Exception:
            created_uuids = []

        try:
            self.client.report_result(command["command_id"], "completed",
                                      veqra_protocol.MSG_COMMAND_DONE,
                                      created_uuids=created_uuids)
            if created_list:
                self._sync_after_change(
                    AllplanEleAdapter.BaseElementAdapterList(created_list))
        except (veqra_bridge_client.BridgeUnreachableError,
                veqra_bridge_client.BridgeRequestError) as error:
            message = getattr(error, "message_de", veqra_protocol.MSG_BRIDGE_UNREACHABLE)
            self._set_status(f"Der Quader wurde erstellt, aber die Rückmeldung "
                             f"schlug fehl: {message}")
            self.active_command = None
            self.build_ele.NextCommandText.value = "–"
            self._start_idle_input()
            self._update_palette()
            return

        self.active_command = None
        self.build_ele.NextCommandText.value = "–"
        self._set_status("Der Quader wurde erstellt und synchronisiert. "
                         "Strg+Z macht die Erstellung rückgängig.")
        self._start_idle_input()
        self._update_palette()

    # ------------------------------------------------------------------
    # Interactor-Ereignisse (Signaturen wie im Beispiel CopyElements.py)
    # ------------------------------------------------------------------

    def modify_element_property(self, page: int, name: str, value: str) -> None:
        if self.palette_service.modify_element_property(page, name, value):
            self.palette_service.update_palette(-1, False)

    def on_cancel_function(self) -> bool:
        """ESC: Auftrag ggf. als abgelehnt melden, niemals Modellaenderung."""

        if self.active_command is not None:
            try:
                self.client.report_result(self.active_command["command_id"], "rejected",
                                          "In Allplan mit ESC abgebrochen.")
            except (veqra_bridge_client.BridgeUnreachableError,
                    veqra_bridge_client.BridgeRequestError):
                pass
            self.active_command = None

        self.client.stop_heartbeat()
        self.palette_service.close_palette()
        return True

    def on_preview_draw(self) -> None:
        pass

    def on_mouse_leave(self) -> None:
        self.on_preview_draw()

    def on_value_input_control_enter(self) -> bool:
        return True

    def process_mouse_msg(self, mouse_msg: int, pnt: AllplanGeo.Point2D,
                          msg_info: Any) -> bool:
        if self.input_mode == "element_selection" and self.post_element_selection:
            self._read_selection_result()
            self._start_idle_input()
            self._update_palette()
            return True

        if self.input_mode == "cuboid_point":
            # Punkteingabe wie im offiziellen Beispiel Elements3DInteractor.py
            input_pnt = self.coord_input.GetInputPoint(mouse_msg, pnt, msg_info).GetPoint()
            self._draw_cuboid_preview(input_pnt)
            if self.coord_input.IsMouseMove(mouse_msg):
                return True
            self._create_cuboid_at(input_pnt)
            return True

        return True

    def reset_param_values(self, _build_ele_list) -> None:
        BuildingElementListService.reset_param_values(self.build_ele_list)
        self.palette_service.update_palette(-1, True)

    def execute_save_favorite(self, file_name: str) -> None:
        BuildingElementListService.write_to_file(file_name, self.build_ele_list)

    def execute_load_favorite(self, file_name: str) -> None:
        BuildingElementListService.read_from_file(file_name, self.build_ele_list)
        self.palette_service.update_palette(-1, True)

    def __del__(self):
        try:
            self.client.stop_heartbeat()
        except Exception:
            pass


def create_element(build_ele: BuildingElement,
                   _doc: AllplanEleAdapter.DocumentAdapter) -> CreateElementResult:
    """Interactor-PythonParts erzeugen beim Start keine Elemente."""

    return CreateElementResult()


# Nachrichtenbox-Hilfe fuer manuelle Diagnose (ShowMessageBox wie in
# offiziellen Beispielen, z. B. MWSPlacement.py)
def show_message(message: str) -> None:
    AllplanUtil.ShowMessageBox(message, AllplanUtil.MB_OK)
