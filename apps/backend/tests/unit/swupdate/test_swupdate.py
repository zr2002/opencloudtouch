"""Unit tests for swupdate firmware index endpoints."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from opencloudtouch.swupdate.routes import _build_index_xml, router

app = FastAPI()
app.include_router(router)


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# _build_index_xml (pure function)
# ---------------------------------------------------------------------------


class TestBuildIndexXml:
    def test_returns_valid_xml_declaration(self):
        xml = _build_index_xml("http://localhost:7777")
        assert xml.startswith('<?xml version="1.0"')

    def test_contains_index_root(self):
        xml = _build_index_xml("http://localhost:7777")
        assert "<INDEX" in xml
        assert "</INDEX>" in xml

    def test_contains_url_header(self):
        xml = _build_index_xml("http://myhost:7777")
        assert 'URL_HEADER="http://myhost:7777/ced/eup/downloads/rel"' in xml

    def test_contains_soundtouch_10(self):
        xml = _build_index_xml("http://x")
        assert 'ID="0x0926"' in xml
        assert "SoundTouch 10" in xml

    def test_contains_soundtouch_20(self):
        xml = _build_index_xml("http://x")
        assert 'ID="0x0923"' in xml

    def test_contains_soundtouch_30(self):
        xml = _build_index_xml("http://x")
        assert 'ID="0x0924"' in xml

    def test_contains_soundtouch_300(self):
        xml = _build_index_xml("http://x")
        assert 'ID="0x073A"' in xml

    def test_contains_all_devices(self):
        xml = _build_index_xml("http://x")
        assert xml.count("<DEVICE") == 6

    def test_each_device_has_release(self):
        xml = _build_index_xml("http://x")
        assert xml.count("<RELEASE ") == 6

    def test_each_device_has_hardware(self):
        xml = _build_index_xml("http://x")
        assert xml.count("<HARDWARE") == 6

    def test_release_has_crc(self):
        xml = _build_index_xml("http://x")
        assert 'CRC="0x00000000"' in xml

    def test_release_has_revision(self):
        xml = _build_index_xml("http://x")
        assert 'REVISION="27.0.6.46330.5043500"' in xml


# ---------------------------------------------------------------------------
# GET /updates/soundtouch
# ---------------------------------------------------------------------------


class TestFirmwareIndex:
    @pytest.mark.asyncio
    async def test_returns_200(self, client):
        resp = await client.get("/updates/soundtouch")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_returns_xml_content_type(self, client):
        resp = await client.get("/updates/soundtouch")
        assert "xml" in resp.headers["content-type"]

    @pytest.mark.asyncio
    async def test_contains_index_element(self, client):
        resp = await client.get("/updates/soundtouch")
        assert "<INDEX" in resp.text
        assert "</INDEX>" in resp.text

    @pytest.mark.asyncio
    async def test_contains_device_entries(self, client):
        resp = await client.get("/updates/soundtouch")
        assert "<DEVICE" in resp.text

    @pytest.mark.asyncio
    async def test_contains_soundtouch_10_device(self, client):
        resp = await client.get("/updates/soundtouch")
        assert 'ID="0x0926"' in resp.text


# ---------------------------------------------------------------------------
# GET /ced/eup/downloads/rel/{filename}
# ---------------------------------------------------------------------------


class TestFirmwareDownload:
    @pytest.mark.asyncio
    async def test_returns_404(self, client):
        resp = await client.get("/ced/eup/downloads/rel/SoundTouch_10.eup")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_xml_error(self, client):
        resp = await client.get("/ced/eup/downloads/rel/anything.eup")
        assert "xml" in resp.headers["content-type"]
        assert "<error>" in resp.text

    @pytest.mark.asyncio
    async def test_blocked_message(self, client):
        resp = await client.get("/ced/eup/downloads/rel/firmware.eup")
        assert "disabled" in resp.text.lower()
