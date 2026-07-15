"""Tests fuer Projekt- und Elementsynchronisierung inkl. Groessenbegrenzungen."""

from __future__ import annotations

from conftest import make_element, make_project_sync


def test_project_sync_creates_snapshot(registered) -> None:
    payload = make_project_sync(registered["connector"]["connector_id"])
    response = registered["client"].post("/api/v1/sync/project", json=payload,
                                         headers=registered["headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["snapshot_version"] == 1

    # Jede Synchronisierung erhaelt eine neue eindeutige Versionsnummer
    response = registered["client"].post("/api/v1/sync/project", json=payload,
                                         headers=registered["headers"])
    assert response.json()["snapshot_version"] == 2

    projects = registered["client"].get("/api/v1/projects").json()["projects"]
    assert len(projects) == 1
    assert projects[0]["name"] == "Testprojekt"
    assert projects[0]["snapshot_version"] == 2
    assert projects[0]["connection_status"] == "connected"


def test_project_sync_rejects_wrong_protocol(registered) -> None:
    payload = make_project_sync(registered["connector"]["connector_id"])
    payload["protocol_version"] = "9.9"
    response = registered["client"].post("/api/v1/sync/project", json=payload,
                                         headers=registered["headers"])
    assert response.status_code == 400


def test_project_sync_rejects_foreign_connector_id(registered) -> None:
    payload = make_project_sync("fremder-connector")
    response = registered["client"].post("/api/v1/sync/project", json=payload,
                                         headers=registered["headers"])
    assert response.status_code == 403


def test_path_hash_required_no_plaintext_path(registered) -> None:
    payload = make_project_sync(registered["connector"]["connector_id"])
    payload["path_hash"] = "C:\\Projekte\\geheim"
    response = registered["client"].post("/api/v1/sync/project", json=payload,
                                         headers=registered["headers"])
    assert response.status_code == 422  # kein Klartextpfad, nur SHA-256 erlaubt


def test_selection_sync_stores_elements(registered) -> None:
    connector_id = registered["connector"]["connector_id"]
    registered["client"].post("/api/v1/sync/project",
                              json=make_project_sync(connector_id),
                              headers=registered["headers"])

    response = registered["client"].post("/api/v1/sync/selection", json={
        "protocol_version": "1.0",
        "connector_id": connector_id,
        "project_id": "p" * 32,
        "source": "selection",
        "elements": [make_element("1"), make_element("2")],
    }, headers=registered["headers"])
    assert response.status_code == 200
    assert response.json()["accepted"] == 2

    elements = registered["client"].get(
        f"/api/v1/projects/{'p' * 32}/elements").json()
    assert elements["total"] == 2
    assert elements["elements"][0]["element_type"] == "Wall"


def test_element_sync_truncates_attributes(registered, monkeypatch) -> None:
    connector_id = registered["connector"]["connector_id"]
    state = registered["state"]

    # Begrenzung klein stellen, um das Verhalten zu testen
    object.__setattr__(state.config, "max_attributes_per_element", 2)

    element = make_element("3")
    element["attributes"] = [
        {"attribute_id": i, "name": f"A{i}", "value": i} for i in range(1, 10)
    ]
    response = registered["client"].post("/api/v1/sync/elements", json={
        "protocol_version": "1.0",
        "connector_id": connector_id,
        "project_id": "p" * 32,
        "source": "project_scan",
        "elements": [element],
    }, headers=registered["headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["truncated"] is True
    assert "begrenzt" in data["message"]


def test_element_sync_truncates_element_count(registered) -> None:
    connector_id = registered["connector"]["connector_id"]
    state = registered["state"]
    object.__setattr__(state.config, "max_elements_per_scan", 3)

    elements = [make_element(str(i)) for i in range(1, 7)]
    for index, element in enumerate(elements):
        element["element_uuid"] = f"00000000-0000-0000-0000-00000000000{index}"

    response = registered["client"].post("/api/v1/sync/elements", json={
        "protocol_version": "1.0",
        "connector_id": connector_id,
        "project_id": "p" * 32,
        "source": "project_scan",
        "elements": elements,
    }, headers=registered["headers"])
    data = response.json()
    assert data["accepted"] == 3
    assert data["truncated"] is True


def test_element_filters_and_pagination(registered) -> None:
    connector_id = registered["connector"]["connector_id"]
    elements = []
    for index in range(5):
        element = make_element(str(index))
        element["element_uuid"] = f"11111111-0000-0000-0000-00000000000{index}"
        element["element_type"] = "Wall" if index < 3 else "Column"
        elements.append(element)

    registered["client"].post("/api/v1/sync/elements", json={
        "protocol_version": "1.0",
        "connector_id": connector_id,
        "project_id": "p" * 32,
        "source": "project_scan",
        "elements": elements,
    }, headers=registered["headers"])

    filtered = registered["client"].get(
        f"/api/v1/projects/{'p' * 32}/elements?element_type=Wall").json()
    assert filtered["total"] == 3

    paged = registered["client"].get(
        f"/api/v1/projects/{'p' * 32}/elements?page=2&page_size=2").json()
    assert paged["total"] == 5
    assert len(paged["elements"]) == 2

    by_attribute = registered["client"].get(
        f"/api/v1/projects/{'p' * 32}/elements?attribute_id=508").json()
    assert by_attribute["total"] == 5
