"""SWUpdate routes for SoundTouch firmware index emulation.

Emulates the firmware update endpoints normally served by worldwide.bose.com.
The device's OverrideSdkPrivateCfg.xml redirects firmware checks to OCT via:
  <swUpdateUrl>http://content.api.bose.io:7777/updates/soundtouch</swUpdateUrl>

Endpoints:
  GET /updates/soundtouch          → Firmware INDEX.XML
  GET /ced/eup/downloads/rel/{file} → Redirect to archive.org firmware download
"""

import logging
from xml.sax.saxutils import escape as xml_escape

from fastapi import APIRouter, Response

logger = logging.getLogger(__name__)

router = APIRouter(tags=["swupdate"])

# Known SoundTouch device IDs (from BoseApp-rhino.xml analysis)
_DEVICES: list[dict] = [
    {
        "id": "0x0923",
        "name": "SoundTouch 20",
        "revision": "27.0.6.46330.5043500",
        "filename": "SoundTouch_20_27.0.6.46330.5043500.eup",
    },
    {
        "id": "0x0924",
        "name": "SoundTouch 30",
        "revision": "27.0.6.46330.5043500",
        "filename": "SoundTouch_30_27.0.6.46330.5043500.eup",
    },
    {
        "id": "0x0925",
        "name": "SoundTouch Portable",
        "revision": "27.0.6.46330.5043500",
        "filename": "SoundTouch_Portable_27.0.6.46330.5043500.eup",
    },
    {
        "id": "0x0926",
        "name": "SoundTouch 10",
        "revision": "27.0.6.46330.5043500",
        "filename": "SoundTouch_10_27.0.6.46330.5043500.eup",
    },
    {
        "id": "0x073A",
        "name": "SoundTouch 300",
        "revision": "27.0.6.46330.5043500",
        "filename": "SoundTouch_300_27.0.6.46330.5043500.eup",
    },
    {
        "id": "0x0939",
        "name": "SoundTouch 10 (Gen2)",
        "revision": "27.0.6.46330.5043500",
        "filename": "SoundTouch_10_Gen2_27.0.6.46330.5043500.eup",
    },
]


def _build_index_xml(base_url: str) -> str:
    """Build firmware INDEX.XML from known device list.

    Args:
        base_url: Base URL for firmware downloads (protocol://host:port)
    """
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    url_header = f"{base_url}/ced/eup/downloads/rel"
    lines.append(f'<INDEX REVISION="02.11.00" URL_HEADER="{xml_escape(url_header)}">')

    for dev in _DEVICES:
        lines.append(
            f'  <DEVICE ID="{dev["id"]}" PRODUCTNAME="{xml_escape(dev["name"])}">'
        )
        lines.append('    <HARDWARE REVISION="00.01.00">')
        lines.append(
            f'      <RELEASE HTTPURL="{xml_escape(dev["filename"])}"'
            f' REVISION="{dev["revision"]}"'
            f' CRC="0x00000000">'
        )
        lines.append(
            "        <RELEASE_NOTES><![CDATA[Latest firmware.]]></RELEASE_NOTES>"
        )
        lines.append('        <IMAGE ID="FS" CRC="0x00000000" />')
        lines.append('        <IMAGE ID="MR" CRC="0x00000000" />')
        lines.append("      </RELEASE>")
        lines.append("    </HARDWARE>")
        lines.append("  </DEVICE>")

    lines.append("</INDEX>")
    return "\n".join(lines)


@router.get("/updates/soundtouch")
async def firmware_index():
    """Return firmware INDEX.XML for SoundTouch devices.

    The device checks this endpoint at boot and periodically
    to determine if a firmware update is available.
    """
    logger.info("[swupdate] Firmware index requested")
    # Use empty base URL — device uses URL_HEADER from INDEX
    xml = _build_index_xml("http://content.api.bose.io:7777")
    return Response(content=xml, media_type="application/xml")


@router.get("/ced/eup/downloads/rel/{filename:path}")
async def firmware_download(filename: str):
    """Redirect firmware download to device.

    Firmware files are large (100+ MB). Instead of hosting them,
    we return a 404 — OCT intentionally does NOT serve firmware
    updates to prevent devices from updating to versions that
    might break OCT compatibility.

    In the future, this could proxy to archive.org for
    specific firmware versions needed for downgrading.
    """
    logger.warning(f"[swupdate] Firmware download requested: {filename} — blocked")
    return Response(
        content="<error>Firmware downloads disabled by OCT</error>",
        media_type="application/xml",
        status_code=404,
    )
