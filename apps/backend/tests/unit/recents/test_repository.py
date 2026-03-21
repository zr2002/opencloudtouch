"""Tests for recents repository."""

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from opencloudtouch.recents.models import RecentPlay
from opencloudtouch.recents.repository import MAX_RECENTS_PER_DEVICE, RecentsRepository


@pytest.fixture
async def recents_repo():
    """Create a temporary recents repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_recents.db"
        repo = RecentsRepository(str(db_path))
        await repo.initialize()
        yield repo
        await repo.close()


@pytest.fixture
def sample_recent():
    """Sample recent play data."""
    return RecentPlay(
        device_id="689E194F7D2F",
        source="TUNEIN",
        location="/v1/playback/station/s33828",
        name="WDR 2",
        image_url="https://cdn-radiotime-logos.tunein.com/s33828q.png",
    )


class TestRecentsRepository:
    """Tests for RecentsRepository."""

    @pytest.mark.asyncio
    async def test_initialize_creates_table(self, recents_repo):
        """Test that initialize creates the recents table."""
        cursor = await recents_repo._db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='recents'"
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row[0] == "recents"

    @pytest.mark.asyncio
    async def test_add_recent(self, recents_repo, sample_recent):
        """Test adding a recent item."""
        result = await recents_repo.add_recent(sample_recent)

        assert result.id is not None
        assert result.device_id == "689E194F7D2F"
        assert result.name == "WDR 2"
        assert result.source == "TUNEIN"

    @pytest.mark.asyncio
    async def test_get_recents_empty(self, recents_repo):
        """Test getting recents for device with no history."""
        result = await recents_repo.get_recents("nonexistent")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_recents_ordered_by_played_at(self, recents_repo):
        """Test recents are returned newest first."""
        now = datetime.now(UTC)
        for i in range(3):
            recent = RecentPlay(
                device_id="device1",
                source="TUNEIN",
                location=f"/station/{i}",
                name=f"Station {i}",
                played_at=now - timedelta(hours=2 - i),
            )
            await recents_repo.add_recent(recent)

        result = await recents_repo.get_recents("device1")

        assert len(result) == 3
        assert result[0].name == "Station 2"  # newest
        assert result[1].name == "Station 1"
        assert result[2].name == "Station 0"  # oldest

    @pytest.mark.asyncio
    async def test_add_recent_deduplicates_by_location(self, recents_repo):
        """Test that re-playing same station updates timestamp."""
        recent1 = RecentPlay(
            device_id="device1",
            source="TUNEIN",
            location="/station/s1",
            name="Station 1",
            played_at=datetime(2024, 1, 1, tzinfo=UTC),
        )
        await recents_repo.add_recent(recent1)

        recent2 = RecentPlay(
            device_id="device1",
            source="TUNEIN",
            location="/station/s1",
            name="Station 1 Updated",
            played_at=datetime(2024, 6, 1, tzinfo=UTC),
        )
        await recents_repo.add_recent(recent2)

        result = await recents_repo.get_recents("device1")
        assert len(result) == 1
        assert result[0].name == "Station 1 Updated"

    @pytest.mark.asyncio
    async def test_recents_per_device_isolation(self, recents_repo):
        """Test that recents are isolated per device."""
        await recents_repo.add_recent(
            RecentPlay(device_id="dev1", source="TUNEIN", location="/s1", name="S1")
        )
        await recents_repo.add_recent(
            RecentPlay(device_id="dev2", source="TUNEIN", location="/s2", name="S2")
        )

        dev1_recents = await recents_repo.get_recents("dev1")
        dev2_recents = await recents_repo.get_recents("dev2")

        assert len(dev1_recents) == 1
        assert dev1_recents[0].name == "S1"
        assert len(dev2_recents) == 1
        assert dev2_recents[0].name == "S2"

    @pytest.mark.asyncio
    async def test_max_recents_limit_enforced(self, recents_repo):
        """Test that oldest items are pruned beyond MAX_RECENTS_PER_DEVICE."""
        now = datetime.now(UTC)
        for i in range(MAX_RECENTS_PER_DEVICE + 5):
            await recents_repo.add_recent(
                RecentPlay(
                    device_id="device1",
                    source="TUNEIN",
                    location=f"/station/{i}",
                    name=f"Station {i}",
                    played_at=now + timedelta(seconds=i),
                )
            )

        result = await recents_repo.get_recents("device1")
        assert len(result) == MAX_RECENTS_PER_DEVICE

        # Oldest 5 should be pruned
        names = [r.name for r in result]
        for i in range(5):
            assert f"Station {i}" not in names

    @pytest.mark.asyncio
    async def test_get_recents_with_limit(self, recents_repo):
        """Test limiting returned recents."""
        now = datetime.now(UTC)
        for i in range(10):
            await recents_repo.add_recent(
                RecentPlay(
                    device_id="device1",
                    source="TUNEIN",
                    location=f"/station/{i}",
                    name=f"Station {i}",
                    played_at=now + timedelta(seconds=i),
                )
            )

        result = await recents_repo.get_recents("device1", limit=3)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_clear_recents(self, recents_repo):
        """Test clearing all recents for a device."""
        for i in range(5):
            await recents_repo.add_recent(
                RecentPlay(
                    device_id="device1",
                    source="TUNEIN",
                    location=f"/station/{i}",
                    name=f"Station {i}",
                )
            )

        deleted = await recents_repo.clear_recents("device1")
        assert deleted == 5

        result = await recents_repo.get_recents("device1")
        assert result == []

    @pytest.mark.asyncio
    async def test_clear_recents_empty(self, recents_repo):
        """Test clearing recents for device with no history."""
        deleted = await recents_repo.clear_recents("nonexistent")
        assert deleted == 0

    @pytest.mark.asyncio
    async def test_not_initialized_raises(self):
        """Test accessing repo without initialize raises RuntimeError."""
        repo = RecentsRepository("/tmp/unused.db")
        with pytest.raises(RuntimeError, match="not initialized"):
            await repo.get_recents("device1")


class TestRecentPlayModel:
    """Tests for RecentPlay model."""

    def test_defaults(self):
        """Test default values."""
        recent = RecentPlay(
            device_id="dev1",
            source="TUNEIN",
            location="/s1",
            name="Station 1",
        )
        assert recent.id is None
        assert recent.image_url is None
        assert recent.played_at is not None

    def test_all_fields(self):
        """Test setting all fields."""
        now = datetime.now(UTC)
        recent = RecentPlay(
            id=42,
            device_id="dev1",
            source="LOCAL_INTERNET_RADIO",
            location="http://stream.example.com/live",
            name="Example FM",
            image_url="https://example.com/logo.png",
            played_at=now,
        )
        assert recent.id == 42
        assert recent.source == "LOCAL_INTERNET_RADIO"
        assert recent.played_at == now
