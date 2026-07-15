"""Tests der automatischen Kopplung (Token-Lesen aus der lokalen Ablage)."""

from __future__ import annotations

from pathlib import Path

import pytest
from veqra_protocol import read_local_pairing_token


def test_reads_token_from_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VEQRA_BRIDGE_DATA_DIR", str(tmp_path))
    (tmp_path / "pairing-token.txt").write_text("mein-lokaler-token\n", encoding="utf-8")

    assert read_local_pairing_token() == "mein-lokaler-token"


def test_returns_none_if_file_missing(tmp_path: Path,
                                      monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VEQRA_BRIDGE_DATA_DIR", str(tmp_path))
    assert read_local_pairing_token() is None


def test_returns_none_for_empty_file(tmp_path: Path,
                                     monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VEQRA_BRIDGE_DATA_DIR", str(tmp_path))
    (tmp_path / "pairing-token.txt").write_text("   \n", encoding="utf-8")
    assert read_local_pairing_token() is None


def test_default_location_is_home_veqra_form(tmp_path: Path,
                                             monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VEQRA_BRIDGE_DATA_DIR", raising=False)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    (tmp_path / ".veqra-form").mkdir()
    (tmp_path / ".veqra-form" / "pairing-token.txt").write_text("heim-token",
                                                                encoding="utf-8")
    assert read_local_pairing_token() == "heim-token"
