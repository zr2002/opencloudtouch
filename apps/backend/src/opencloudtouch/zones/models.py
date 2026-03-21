"""Zone domain models for multi-room management."""

from pydantic import BaseModel


class ZoneMemberInfo(BaseModel):
    """A member device within a multi-room zone."""

    device_id: str
    ip_address: str
    role: str  # "master" or "slave"
    name: str | None = None
    model: str | None = None


class ZoneStatus(BaseModel):
    """Status of a multi-room zone."""

    master_id: str
    master_ip: str
    is_master: bool
    members: list[ZoneMemberInfo]
