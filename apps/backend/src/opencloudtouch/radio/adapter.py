"""
Radio Provider Factory.

Factory pattern for Mock vs Real RadioBrowser provider selection.
Based on OCT_MOCK_MODE environment variable.
Uses singleton pattern for real adapter to enable connection pooling.
"""

import logging
import os

from opencloudtouch.radio.provider import RadioProvider

logger = logging.getLogger(__name__)

# Singleton instance for connection pooling and DNS caching
_radio_adapter_instance: RadioProvider | None = None


def get_radio_adapter() -> RadioProvider:
    """
    Factory function: Select Mock or Real radio provider.

    Returns a singleton RadioBrowserAdapter in production mode to reuse
    httpx connections and DNS cache across requests.

    Returns:
        RadioProvider: MockRadioAdapter if OCT_MOCK_MODE=true, else RadioBrowserAdapter
    """
    global _radio_adapter_instance

    mock_mode = os.getenv("OCT_MOCK_MODE", "false").lower() == "true"

    if mock_mode:
        logger.debug("[FACTORY] Creating MockRadioAdapter (OCT_MOCK_MODE=true)")
        from opencloudtouch.radio.providers.mock import MockRadioAdapter

        return MockRadioAdapter()

    if _radio_adapter_instance is None:
        logger.info("[FACTORY] Creating RadioBrowserAdapter singleton")
        from opencloudtouch.radio.providers.radiobrowser import RadioBrowserAdapter

        _radio_adapter_instance = RadioBrowserAdapter()

    return _radio_adapter_instance


def reset_radio_adapter() -> None:
    """Reset the singleton (for testing)."""
    global _radio_adapter_instance
    _radio_adapter_instance = None
