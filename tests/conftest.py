"""Shared fixtures."""
from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import AsyncMock, patch

import pycares
import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def _no_slot_fetch() -> Iterator[None]:
    """Don't hit the network for slot metadata during tests by default.

    Tests that exercise the slot select override this with their own patch.
    """
    with patch(
        "custom_components.gbs_control.coordinator.GBSControlApiClient.get_slots",
        new=AsyncMock(return_value=[]),
    ):
        yield


@pytest.fixture(scope="session", autouse=True)
def _prespawn_aiodns_thread() -> Iterator[None]:
    """Pre-spawn the pycares/aiodns daemon DNS thread.

    aiohttp's default resolver (aiodns/pycares) lazily starts a daemon thread
    named ``_run_safe_shutdown_loop`` the first time a ClientSession is created.
    When that happens inside a test body, pytest-homeassistant-custom-component's
    ``verify_cleanup`` fixture sees a thread that was absent from its pre-test
    snapshot and fails the test at teardown. Spawning (and holding) the channel
    once at session scope keeps the thread present in every test's snapshot.
    """
    channel = pycares.Channel()
    yield
    del channel


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading of the custom integration in every test."""
    yield
