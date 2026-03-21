"""Domain model for recently played items."""

from datetime import UTC, datetime
from typing import Optional


class RecentPlay:
    """A recently played item for a device.

    Attributes:
        device_id: Device MAC address
        source: Source type (TUNEIN, LOCAL_INTERNET_RADIO, etc.)
        location: Stream location path
        name: Display name
        image_url: Optional artwork URL
        played_at: When the item was played
        id: Database primary key
    """

    def __init__(
        self,
        device_id: str,
        source: str,
        location: str,
        name: str,
        image_url: Optional[str] = None,
        played_at: Optional[datetime] = None,
        id: Optional[int] = None,
    ):
        self.id = id
        self.device_id = device_id
        self.source = source
        self.location = location
        self.name = name
        self.image_url = image_url
        self.played_at = played_at or datetime.now(UTC)
