"""Unit tests for radio adapter factory function.

Covers the get_radio_adapter() factory and its OCT_MOCK_MODE env var branching.
"""

import pytest

from opencloudtouch.radio.adapter import get_radio_adapter, reset_radio_adapter


@pytest.fixture(autouse=True)
def _reset_singleton():
    """Reset adapter singleton before each test."""
    reset_radio_adapter()
    yield
    reset_radio_adapter()


class TestGetRadioAdapterFactory:
    """Tests for get_radio_adapter() factory function."""

    def test_default_mode_returns_radiobrowser_adapter(self):
        """Default mode (OCT_MOCK_MODE unset) returns RadioBrowserAdapter."""
        import os

        os.environ.pop("OCT_MOCK_MODE", None)

        from opencloudtouch.radio.providers.radiobrowser import RadioBrowserAdapter

        adapter = get_radio_adapter()
        assert isinstance(adapter, RadioBrowserAdapter)

    def test_mock_mode_true_returns_mock_adapter(self, monkeypatch):
        """OCT_MOCK_MODE=true returns MockRadioAdapter (lines 44-47)."""
        monkeypatch.setenv("OCT_MOCK_MODE", "true")

        from opencloudtouch.radio.providers.mock import MockRadioAdapter

        adapter = get_radio_adapter()
        assert isinstance(adapter, MockRadioAdapter)

    def test_mock_mode_uppercase_returns_mock_adapter(self, monkeypatch):
        """OCT_MOCK_MODE=TRUE (uppercase) is normalised to lowercase correctly."""
        monkeypatch.setenv("OCT_MOCK_MODE", "TRUE")

        from opencloudtouch.radio.providers.mock import MockRadioAdapter

        adapter = get_radio_adapter()
        assert isinstance(adapter, MockRadioAdapter)

    def test_mock_mode_false_returns_radiobrowser_adapter(self, monkeypatch):
        """OCT_MOCK_MODE=false explicitly returns RadioBrowserAdapter."""
        monkeypatch.setenv("OCT_MOCK_MODE", "false")

        from opencloudtouch.radio.providers.radiobrowser import RadioBrowserAdapter

        adapter = get_radio_adapter()
        assert isinstance(adapter, RadioBrowserAdapter)

    def test_singleton_returns_same_instance(self):
        """Production mode returns same adapter instance (singleton)."""
        import os

        os.environ.pop("OCT_MOCK_MODE", None)

        adapter1 = get_radio_adapter()
        adapter2 = get_radio_adapter()
        assert adapter1 is adapter2

    def test_mock_mode_returns_new_instance_each_time(self, monkeypatch):
        """Mock mode creates fresh instance each call (not singleton)."""
        monkeypatch.setenv("OCT_MOCK_MODE", "true")

        adapter1 = get_radio_adapter()
        adapter2 = get_radio_adapter()
        assert adapter1 is not adapter2
