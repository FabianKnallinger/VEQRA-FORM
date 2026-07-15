"""Mocks fuer die Allplan-Laufzeit.

Es werden niemals echte Allplan-Module importiert; stattdessen werden
Stub-Module in sys.modules eingesetzt, damit die Adapter-Schicht des
Plugins ohne Allplan getestet werden kann.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "PythonPartsScripts"))


class _Recorder:
    """Zeichnet Aufrufe der Allplan-Stubs auf."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple, dict]] = []

    def record(self, name: str):
        def _call(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            return None
        return _call

    def names(self) -> list[str]:
        return [name for name, _, _ in self.calls]


RECORDER = _Recorder()


class _FakeVector3D:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        if hasattr(x, "X"):
            self.X, self.Y, self.Z = x.X, x.Y, x.Z
        else:
            self.X, self.Y, self.Z = x, y, z


class _FakeMatrix3D:
    def __init__(self):
        self.translation = None

    def SetTranslation(self, vector):
        self.translation = vector


class _FakePoint3D:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.X, self.Y, self.Z = x, y, z


class _FakePolyhedron3D:
    @staticmethod
    def CreateCuboid(*args):
        RECORDER.calls.append(("Polyhedron3D.CreateCuboid", args, {}))
        return "fake-cuboid"


class _FakeElementsAttributeService:
    @staticmethod
    def ChangeAttributes(attributes, elements):
        RECORDER.calls.append(("ElementsAttributeService.ChangeAttributes",
                               (attributes, elements), {}))


class _FakeAdapterList(list):
    def __init__(self, items=()):
        super().__init__(items)


def _build_module(name: str, **attrs) -> types.ModuleType:
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


@pytest.fixture(scope="session", autouse=True)
def allplan_stubs():
    """Installiert die Allplan-Stub-Module fuer alle Tests dieses Ordners."""

    geometry = _build_module(
        "NemAll_Python_Geometry",
        Vector3D=_FakeVector3D, Matrix3D=_FakeMatrix3D, Point3D=_FakePoint3D,
        Point2D=type("Point2D", (), {}), Polyhedron3D=_FakePolyhedron3D,
        AxisPlacement3D=type("AxisPlacement3D", (), {}))

    base_elements = _build_module(
        "NemAll_Python_BaseElements",
        GetElements=lambda adapters: ["fake-object"] * len(adapters),
        ElementTransform=RECORDER.record("ElementTransform"),
        ModifyElements=RECORDER.record("ModifyElements"),
        CreateElements=RECORDER.record("CreateElements"),
        DrawElementPreview=RECORDER.record("DrawElementPreview"),
        ElementsAttributeService=_FakeElementsAttributeService,
        CommonProperties=type("CommonProperties", (), {
            "GetGlobalProperties": lambda self: None}),
        DrawingFileService=type("DrawingFileService", (), {
            "GetFileState": lambda self: [(1, "Active")],
            "GetActiveFileNumber": staticmethod(lambda: 1)}),
        ProjectAttributeService=type("ProjectAttributeService", (), {
            "GetAttributesFromCurrentProject": staticmethod(lambda: [(405, "T-001")])}),
        AttributeService=type("AttributeService", (), {
            "GetAttributeName": staticmethod(lambda doc, attribute_id: f"Attr{attribute_id}")}),
        LayerService=type("LayerService", (), {
            "GetNameByID": staticmethod(lambda layer_id: f"LAYER{layer_id}")}),
        ElementsSelectService=type("ElementsSelectService", (), {
            "SelectAllElements": staticmethod(lambda doc: _FakeAdapterList())}),
        GetMinMaxBox=lambda elements: None,
        eAttibuteReadState=type("eAttibuteReadState", (), {"ReadAll": 0}),
    )

    basis_elements = _build_module(
        "NemAll_Python_BasisElements",
        ModelElement3D=lambda common, geometry: ("model-element", geometry))

    settings = _build_module(
        "NemAll_Python_AllplanSettings",
        AllplanVersion=type("AllplanVersion", (), {
            "Version": staticmethod(lambda: "2025")}),
        AllplanPaths=type("AllplanPaths", (), {
            "GetCurPrjPath": staticmethod(lambda: "C:\\Daten\\Testprojekt\\")}))

    adapter = _build_module(
        "NemAll_Python_IFW_ElementAdapter",
        DocumentAdapter=type("DocumentAdapter", (), {}),
        BaseElementAdapter=type("BaseElementAdapter", (), {}),
        BaseElementAdapterList=_FakeAdapterList,
        BaseElementAdapterParentElementService=type("P", (), {}),
        BaseElementAdapterChildElementsService=type("C", (), {}))

    ifw_input = _build_module(
        "NemAll_Python_IFW_Input",
        CoordinateInput=type("CoordinateInput", (), {}),
        ElementSelectFilterSetting=type("ElementSelectFilterSetting", (), {}),
        PostElementSelection=type("PostElementSelection", (), {}),
        InputStringConvert=lambda text: text,
        InputFunctionStarter=type("InputFunctionStarter", (), {
            "StartElementSelect": staticmethod(RECORDER.record("StartElementSelect"))}))

    utility = _build_module(
        "NemAll_Python_Utility",
        ShowMessageBox=RECORDER.record("ShowMessageBox"), MB_OK=1)

    framework_modules = {
        "BaseInteractor": _build_module("BaseInteractor",
                                        BaseInteractor=type("BaseInteractor", (), {})),
        "BuildingElement": _build_module("BuildingElement",
                                         BuildingElement=type("BuildingElement", (), {})),
        "BuildingElementComposite": _build_module(
            "BuildingElementComposite",
            BuildingElementComposite=type("BuildingElementComposite", (), {})),
        "BuildingElementControlProperties": _build_module(
            "BuildingElementControlProperties",
            BuildingElementControlProperties=type("BECP", (), {})),
        "BuildingElementListService": _build_module(
            "BuildingElementListService",
            BuildingElementListService=type("BELS", (), {})),
        "BuildingElementPaletteService": _build_module(
            "BuildingElementPaletteService",
            BuildingElementPaletteService=type("BEPS", (), {})),
        "CreateElementResult": _build_module(
            "CreateElementResult",
            CreateElementResult=lambda *args, **kwargs: ("create-result", args)),
        "StringTableService": _build_module(
            "StringTableService",
            StringTableService=type("StringTableService", (), {})),
    }

    stubs = {
        "NemAll_Python_Geometry": geometry,
        "NemAll_Python_BaseElements": base_elements,
        "NemAll_Python_BasisElements": basis_elements,
        "NemAll_Python_AllplanSettings": settings,
        "NemAll_Python_IFW_ElementAdapter": adapter,
        "NemAll_Python_IFW_Input": ifw_input,
        "NemAll_Python_Utility": utility,
        **framework_modules,
    }
    sys.modules.update(stubs)
    yield RECORDER


@pytest.fixture(autouse=True)
def clear_recorder():
    RECORDER.calls.clear()
    yield


class FakeValue:
    def __init__(self, value=""):
        self.value = value


class FakeBuildEle:
    """Nachbildung des BuildingElement mit Palettenparametern und Konstanten."""

    CHECK_CONNECTION = 1001
    SYNC_PROJECT = 1002
    READ_SELECTION = 1003
    SYNC_SELECTION = 1004
    CHECK_COMMAND = 1005
    PREVIEW_COMMAND = 1006
    EXECUTE_COMMAND = 1007
    REJECT_COMMAND = 1008
    OPEN_WEB = 1009

    def __init__(self) -> None:
        for name in ("StatusText", "ConnectionText", "ConnectorIdText",
                     "LastContactText", "PairingToken", "ProjectNameText",
                     "ProjectIdText", "DrawingFilesText", "ElementCountText",
                     "LastSyncText", "SelectionCountText", "SelectionTypesText",
                     "PendingCountText", "NextCommandText", "WebAddressText",
                     "WebHintText"):
            setattr(self, name, FakeValue())
        self.script_name = "VeqraFormConnect.py"
        self.pyp_file_name = "VeqraFormConnect"


class FakeBridgeClient:
    """Nachbildung des BridgeClient; zeichnet alle Meldungen auf."""

    def __init__(self, pending: list[dict] | None = None):
        self.base_url = "http://127.0.0.1:8899"
        self.connector_id = "test-connector"
        self.session_token = "t-sess"  # bewusst kurzer Dummy-Wert
        self.last_contact = "2026-07-14T12:00:00+00:00"
        self.pending_command_count = 0
        self.pending = pending or []
        self.reports: list[tuple[str, str, str | None]] = []
        self.received: list[str] = []
        self.synced_elements: list[dict] = []

    def health(self) -> dict:
        return {"status": "ok"}

    def pending_commands(self, project_id=None) -> list[dict]:
        return self.pending

    def mark_received(self, command_id: str) -> dict:
        self.received.append(command_id)
        return {}

    def report_result(self, command_id: str, status: str, message=None,
                      created_uuids=None, modified_uuids=None) -> dict:
        self.reports.append((command_id, status, message))
        return {}

    def sync_elements(self, payload: dict) -> dict:
        self.synced_elements.append(payload)
        return {"ok": True, "accepted": len(payload.get("elements", [])),
                "truncated": False, "message": "ok"}

    def sync_selection(self, payload: dict) -> dict:
        return self.sync_elements(payload)

    def stop_heartbeat(self) -> None:
        pass


class FakePaletteService:
    def update_palette(self, *args) -> None:
        pass


class FakeCoordInput:
    def GetInputViewDocument(self):
        return object()

    def InitNextPointInput(self, prompt) -> None:
        pass

    def InitFirstElementInput(self, prompt) -> None:
        pass

    def InitFirstPointInput(self, prompt) -> None:
        pass


@pytest.fixture()
def connector_factory(allplan_stubs):
    """Erzeugt eine VeqraFormConnect-Instanz ohne echten Interactor-Start."""

    import VeqraFormConnect as module

    def _create(pending: list[dict] | None = None,
                selection_summaries: list[dict] | None = None):
        instance = module.VeqraFormConnect.__new__(module.VeqraFormConnect)
        instance.build_ele = FakeBuildEle()
        instance.client = FakeBridgeClient(pending)
        instance.coord_input = FakeCoordInput()
        instance.palette_service = FakePaletteService()
        instance.current_project_id = "p" * 32
        instance.selected_elements = (
            _FakeAdapterList(["adapter"] * len(selection_summaries))
            if selection_summaries else None)
        instance.selection_summaries = selection_summaries or []
        instance.active_command = None
        instance.post_element_selection = None
        instance.cuboid_model_ele_list = []
        instance.input_mode = "idle"
        return instance, module

    return _create
