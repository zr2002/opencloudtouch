"""Unit tests for BMX RadioBrowser playback endpoint.

Tests the /bmx/radiobrowser/v1/playback/station/{uuid} endpoint
that resolves RadioBrowser station UUIDs to stream URLs.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from opencloudtouch.bmx.radiobrowser_routes import radiobrowser_router
from opencloudtouch.radio.models import RadioStation


@pytest.fixture
def app():
    """Create FastAPI app with radiobrowser router."""
    app = FastAPI()
    app.include_router(radiobrowser_router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


MOCK_STATION = RadioStation(
    station_id="960e8d30-4e3c-47d8-bf93-a4ce84f5a023",
    name="1LIVE",
    url="https://wdr-1live-live.icecastssl.wdr.de/wdr/1live/live/mp3/128/stream.mp3",
    country="Germany",
    codec="MP3",
    bitrate=128,
    tags=["pop", "rock", "alternative"],
    favicon="https://www.einslive.de/favicon.ico",
    homepage="https://www1.wdr.de/radio/1live/",
    provider="radiobrowser",
)


class TestRadioBrowserPlayback:
    """Tests for /bmx/radiobrowser/v1/playback/station/{uuid}."""

    @patch("opencloudtouch.bmx.radiobrowser_routes.get_radio_adapter")
    def test_valid_uuid_returns_playback_response(self, mock_factory, client):
        """Test successful station resolution returns BmxPlaybackResponse."""
        mock_adapter = AsyncMock()
        mock_adapter.get_station_by_uuid.return_value = MOCK_STATION
        mock_factory.return_value = mock_adapter

        response = client.get(
            "/bmx/radiobrowser/v1/playback/station/960e8d30-4e3c-47d8-bf93-a4ce84f5a023"
        )

        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "1LIVE"
        assert body["streamType"] == "liveRadio"
        assert body["audio"]["streamUrl"].startswith("http://")  # HTTPS→HTTP
        assert len(body["audio"]["streams"]) == 1

    @patch("opencloudtouch.bmx.radiobrowser_routes.get_radio_adapter")
    def test_stream_url_converted_https_to_http(self, mock_factory, client):
        """Test HTTPS stream URLs are converted to HTTP for Bose compatibility."""
        mock_adapter = AsyncMock()
        mock_adapter.get_station_by_uuid.return_value = MOCK_STATION
        mock_factory.return_value = mock_adapter

        response = client.get(
            "/bmx/radiobrowser/v1/playback/station/960e8d30-4e3c-47d8-bf93-a4ce84f5a023"
        )

        body = response.json()
        stream_url = body["audio"]["streams"][0]["streamUrl"]
        assert stream_url.startswith("http://")
        assert "https://" not in stream_url

    @patch("opencloudtouch.bmx.radiobrowser_routes.get_radio_adapter")
    def test_response_contains_image_url(self, mock_factory, client):
        """Test response includes station favicon as imageUrl."""
        mock_adapter = AsyncMock()
        mock_adapter.get_station_by_uuid.return_value = MOCK_STATION
        mock_factory.return_value = mock_adapter

        response = client.get(
            "/bmx/radiobrowser/v1/playback/station/960e8d30-4e3c-47d8-bf93-a4ce84f5a023"
        )

        body = response.json()
        assert body["imageUrl"] == "https://www.einslive.de/favicon.ico"

    @patch("opencloudtouch.bmx.radiobrowser_routes.get_radio_adapter")
    def test_response_contains_nowplaying_links(self, mock_factory, client):
        """Test response contains bmx_nowplaying and bmx_reporting links."""
        mock_adapter = AsyncMock()
        mock_adapter.get_station_by_uuid.return_value = MOCK_STATION
        mock_factory.return_value = mock_adapter

        response = client.get(
            "/bmx/radiobrowser/v1/playback/station/960e8d30-4e3c-47d8-bf93-a4ce84f5a023"
        )

        body = response.json()
        assert "bmx_nowplaying" in body.get("_links", body.get("links", {}))
        assert "bmx_reporting" in body.get("_links", body.get("links", {}))

    @patch("opencloudtouch.bmx.radiobrowser_routes.get_radio_adapter")
    def test_station_not_found_returns_404(self, mock_factory, client):
        """Test unknown UUID returns 404."""
        from opencloudtouch.radio.providers.radiobrowser import RadioBrowserError

        mock_adapter = AsyncMock()
        mock_adapter.get_station_by_uuid.side_effect = RadioBrowserError(
            "Station not-a-real-uuid not found"
        )
        mock_factory.return_value = mock_adapter

        response = client.get("/bmx/radiobrowser/v1/playback/station/not-a-real-uuid")

        assert response.status_code == 404

    @patch("opencloudtouch.bmx.radiobrowser_routes.get_radio_adapter")
    def test_radiobrowser_timeout_returns_504(self, mock_factory, client):
        """Test RadioBrowser API timeout returns 504."""
        from opencloudtouch.radio.providers.radiobrowser import (
            RadioBrowserTimeoutError,
        )

        mock_adapter = AsyncMock()
        mock_adapter.get_station_by_uuid.side_effect = RadioBrowserTimeoutError(
            "Request timed out"
        )
        mock_factory.return_value = mock_adapter

        response = client.get(
            "/bmx/radiobrowser/v1/playback/station/960e8d30-4e3c-47d8-bf93-a4ce84f5a023"
        )

        assert response.status_code == 504

    @patch("opencloudtouch.bmx.radiobrowser_routes.get_radio_adapter")
    def test_radiobrowser_connection_error_returns_503(self, mock_factory, client):
        """Test RadioBrowser connection error returns 503."""
        from opencloudtouch.radio.providers.radiobrowser import (
            RadioBrowserConnectionError,
        )

        mock_adapter = AsyncMock()
        mock_adapter.get_station_by_uuid.side_effect = RadioBrowserConnectionError(
            "Connection failed"
        )
        mock_factory.return_value = mock_adapter

        response = client.get(
            "/bmx/radiobrowser/v1/playback/station/960e8d30-4e3c-47d8-bf93-a4ce84f5a023"
        )

        assert response.status_code == 503

    @patch("opencloudtouch.bmx.radiobrowser_routes.get_radio_adapter")
    def test_station_without_favicon_uses_empty_image(self, mock_factory, client):
        """Test station with no favicon returns empty imageUrl."""
        station = RadioStation(
            station_id="abc-123",
            name="No Logo Radio",
            url="http://stream.example.com/radio.mp3",
            country="Unknown",
            provider="radiobrowser",
        )
        mock_adapter = AsyncMock()
        mock_adapter.get_station_by_uuid.return_value = station
        mock_factory.return_value = mock_adapter

        response = client.get("/bmx/radiobrowser/v1/playback/station/abc-123")

        body = response.json()
        assert body["imageUrl"] == ""
        assert body["name"] == "No Logo Radio"

    @patch("opencloudtouch.bmx.radiobrowser_routes.get_radio_adapter")
    def test_adapter_called_with_correct_uuid(self, mock_factory, client):
        """Test adapter is called with the UUID from the URL path."""
        mock_adapter = AsyncMock()
        mock_adapter.get_station_by_uuid.return_value = MOCK_STATION
        mock_factory.return_value = mock_adapter

        client.get(
            "/bmx/radiobrowser/v1/playback/station/960e8d30-4e3c-47d8-bf93-a4ce84f5a023"
        )

        mock_adapter.get_station_by_uuid.assert_called_once_with(
            "960e8d30-4e3c-47d8-bf93-a4ce84f5a023"
        )
