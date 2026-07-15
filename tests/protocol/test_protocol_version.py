"""Zentrale Versionsnummern muessen ueberall uebereinstimmen."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _shared_version() -> dict:
    return json.loads((REPO_ROOT / "shared" / "VERSION.json").read_text(encoding="utf-8"))


def test_shared_version_file() -> None:
    version = _shared_version()
    assert version["protocol_version"] == "1.0"
    assert version["product_version"] == "0.2.0"


def test_bridge_matches_shared_version() -> None:
    import veqra_bridge

    version = _shared_version()
    assert veqra_bridge.PROTOCOL_VERSION == version["protocol_version"]
    assert veqra_bridge.BRIDGE_VERSION == version["product_version"]


def test_plugin_matches_shared_version() -> None:
    import veqra_protocol

    version = _shared_version()
    assert veqra_protocol.PROTOCOL_VERSION == version["protocol_version"]
    assert veqra_protocol.CONNECTOR_VERSION == version["product_version"]


def test_web_matches_shared_version() -> None:
    version = _shared_version()

    package = json.loads((REPO_ROOT / "web" / "package.json").read_text(encoding="utf-8"))
    assert package["version"] == version["product_version"]

    api_ts = (REPO_ROOT / "web" / "src" / "types" / "api.ts").read_text(encoding="utf-8")
    match = re.search(r'PROTOCOL_VERSION = "([^"]+)"', api_ts)
    assert match is not None
    assert match.group(1) == version["protocol_version"]


def test_install_config_matches_shared_version() -> None:
    import yaml

    config = yaml.safe_load((REPO_ROOT / "install-config.yml").read_text(encoding="utf-8"))
    assert config["plugin"]["version"] == _shared_version()["product_version"]


def test_schema_files_are_valid_json_with_expected_version() -> None:
    schema_dir = REPO_ROOT / "shared" / "schemas"
    expected = {"protocol.schema.json", "project.schema.json", "element.schema.json",
                "command.schema.json", "result.schema.json"}
    found = {path.name for path in schema_dir.glob("*.schema.json")}
    assert expected <= found

    protocol = json.loads((schema_dir / "protocol.schema.json").read_text(encoding="utf-8"))
    assert protocol["properties"]["protocol_version"]["const"] == "1.0"

    command = json.loads((schema_dir / "command.schema.json").read_text(encoding="utf-8"))
    actions = command["properties"]["action"]["enum"]
    assert "create_cuboid" in actions
    assert "delete_elements" not in actions


def test_envelope_matches_protocol_schema() -> None:
    import veqra_protocol

    envelope = veqra_protocol.make_envelope("command", "c-1", "p-1", {"a": 1})
    schema = json.loads((REPO_ROOT / "shared" / "schemas" / "protocol.schema.json")
                        .read_text(encoding="utf-8"))

    required = set(schema["required"])
    assert required <= set(envelope.keys())
    assert envelope["protocol_version"] == "1.0"
    assert envelope["message_type"] in schema["properties"]["message_type"]["enum"]


def test_bridge_and_plugin_share_action_list() -> None:
    import veqra_protocol
    from veqra_bridge.models.command import ALLOWED_ACTIONS as BRIDGE_ACTIONS

    assert tuple(veqra_protocol.ALLOWED_ACTIONS) == tuple(BRIDGE_ACTIONS)
