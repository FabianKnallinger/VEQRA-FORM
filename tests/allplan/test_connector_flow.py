"""Simulierte Ablaeufe des Verbindungswerkzeugs mit gemockter Allplan-Laufzeit."""

from __future__ import annotations


def _cuboid_command() -> dict:
    return {
        "command_id": "cmd-1",
        "action": "create_cuboid",
        "parameters": {"length_mm": 8000, "width_mm": 1200, "height_mm": 4500,
                       "placement_mode": "pick_point"},
        "status": "pending",
        "requires_allplan_confirmation": True,
    }


def test_check_command_reports_awaiting_confirmation(connector_factory) -> None:
    connector, _ = connector_factory(pending=[_cuboid_command()])

    connector._check_command()

    assert connector.client.received == ["cmd-1"]
    assert connector.client.reports[-1][1] == "awaiting_confirmation"
    assert connector.active_command is not None
    assert "Quader" in connector.build_ele.NextCommandText.value
    assert "Bestätigung" in connector.build_ele.StatusText.value


def test_check_command_rejects_unknown_action(connector_factory) -> None:
    bad_command = _cuboid_command()
    bad_command["action"] = "delete_elements"
    connector, _ = connector_factory(pending=[bad_command])

    connector._check_command()

    assert connector.client.reports[-1][1] == "failed"
    assert connector.active_command is None
    assert "unbekannte Aktion" in connector.build_ele.StatusText.value


def test_check_command_rejects_implausible_values(connector_factory) -> None:
    bad_command = _cuboid_command()
    bad_command["parameters"]["length_mm"] = -100
    connector, _ = connector_factory(pending=[bad_command])

    connector._check_command()

    assert connector.client.reports[-1][1] == "failed"
    assert "plausibl" in connector.build_ele.StatusText.value


def test_reject_command(connector_factory) -> None:
    connector, _ = connector_factory(pending=[_cuboid_command()])
    connector._check_command()

    connector._reject_command()

    assert connector.client.reports[-1][1] == "rejected"
    assert connector.active_command is None
    assert connector.build_ele.StatusText.value == "Der Auftrag wurde abgelehnt."


def test_move_without_selection_fails_safely(connector_factory, allplan_stubs) -> None:
    connector, _ = connector_factory(pending=[{
        "command_id": "cmd-2",
        "action": "move_selected_elements",
        "parameters": {"dx_mm": 0, "dy_mm": 0, "dz_mm": 250},
    }])
    connector._check_command()

    connector._execute_command()

    statuses = [status for _, status, _ in connector.client.reports]
    assert statuses[-1] == "failed"
    # Keine Modellaenderung ohne Auswahl
    assert "ModifyElements" not in allplan_stubs.names()
    assert "keine Elemente ausgewählt" in connector.build_ele.StatusText.value


def test_move_with_selection_modifies_and_resyncs(connector_factory, allplan_stubs) -> None:
    summaries = [{"element_uuid": "e-1", "element_type": "Wall"}]
    connector, _ = connector_factory(pending=[{
        "command_id": "cmd-3",
        "action": "move_selected_elements",
        "parameters": {"dx_mm": 0, "dy_mm": 0, "dz_mm": 250},
    }], selection_summaries=summaries)
    connector._check_command()

    # Nachbildung der erneuten Synchronisierung nach der Aenderung
    connector._sync_after_change = lambda adapters: connector.client.sync_elements({
        "source": "after_change", "elements": summaries})

    connector._execute_command()

    names = allplan_stubs.names()
    assert "ElementTransform" in names
    assert "ModifyElements" in names

    statuses = [status for _, status, _ in connector.client.reports]
    assert statuses == ["awaiting_confirmation", "approved", "executing", "completed"]

    # Erneute Synchronisierung nach der Aenderung
    assert connector.client.synced_elements[-1]["source"] == "after_change"


def test_set_attributes_with_selection(connector_factory, allplan_stubs) -> None:
    summaries = [{"element_uuid": "e-1", "element_type": "Wall"}]
    connector, _ = connector_factory(pending=[{
        "command_id": "cmd-4",
        "action": "set_selected_attributes",
        "parameters": {"attributes": [{"attribute_id": 508, "value": "Beton"}]},
    }], selection_summaries=summaries)
    connector._check_command()
    connector._sync_after_change = lambda adapters: None

    connector._execute_command()

    change_calls = [call for call in allplan_stubs.calls
                    if call[0] == "ElementsAttributeService.ChangeAttributes"]
    assert change_calls
    assert change_calls[0][1][0] == [(508, "Beton")]
    assert connector.client.reports[-1][1] == "completed"


def test_execute_cuboid_starts_point_input_not_creation(connector_factory,
                                                        allplan_stubs) -> None:
    connector, _ = connector_factory(pending=[_cuboid_command()])
    connector._check_command()

    connector._execute_command()

    # Die Erstellung erfolgt erst nach der Punkteingabe, nicht sofort
    assert "CreateElements" not in allplan_stubs.names()
    assert connector.input_mode == "cuboid_point"
    statuses = [status for _, status, _ in connector.client.reports]
    assert statuses == ["awaiting_confirmation", "approved", "executing"]


def test_cuboid_creation_after_point_confirmation(connector_factory,
                                                  allplan_stubs) -> None:
    import NemAll_Python_Geometry as fake_geo

    connector, _ = connector_factory(pending=[_cuboid_command()])
    connector._check_command()
    connector._execute_command()
    connector._sync_after_change = lambda adapters: None

    connector._create_cuboid_at(fake_geo.Point3D(1000, 2000, 0))

    names = allplan_stubs.names()
    assert "CreateElements" in names
    assert connector.client.reports[-1][1] == "completed"
    assert connector.active_command is None
    assert "rückgängig" in connector.build_ele.StatusText.value


def test_no_eval_exec_or_shell_in_plugin_scripts() -> None:
    import ast
    from pathlib import Path

    scripts_dir = Path(__file__).resolve().parent.parent.parent / "PythonPartsScripts"
    forbidden_calls = {"eval", "exec"}
    forbidden_modules = {"subprocess", "os.system"}

    for path in scripts_dir.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls, f"{path}: {node.func.id}"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in forbidden_modules, f"{path}: {alias.name}"
            if isinstance(node, ast.ImportFrom):
                assert node.module != "subprocess", f"{path}: subprocess"
