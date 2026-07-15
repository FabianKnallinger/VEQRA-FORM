"""Datenmodelle fuer Connector-Registrierung und Heartbeat."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ConnectorRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pairing_token: str = Field(min_length=8, max_length=256)
    machine_name: str = Field(min_length=1, max_length=255)
    allplan_version: str = Field(default="", max_length=32)
    connector_version: str = Field(default="", max_length=32)


class ConnectorRegisterResponse(BaseModel):
    connector_id: str
    session_token: str
    session_expires_at: str
    protocol_version: str


class HeartbeatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    connector_id: str = Field(min_length=1, max_length=128)
    project_id: str | None = Field(default=None, max_length=128)


class HeartbeatResponse(BaseModel):
    ok: bool
    server_time: str
    pending_commands: int
