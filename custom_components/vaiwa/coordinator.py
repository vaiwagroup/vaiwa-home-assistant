"""Single poller for all VAIWA sensors in the logged-in account."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import VaiwaAuthError, VaiwaCloudClient, VaiwaConnectionError
from .const import SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class VaiwaCoordinator(DataUpdateCoordinator[dict]):
    """Poll Firebase once per cycle for all entities."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: VaiwaCloudClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="VAIWA Cloud",
            config_entry=entry,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.client = client

    async def _async_update_data(self) -> dict:
        try:
            return await self.client.async_get_sensors()
        except VaiwaAuthError as exc:
            raise ConfigEntryAuthFailed("VAIWA authentication needs renewal") from exc
        except VaiwaConnectionError as exc:
            raise UpdateFailed(str(exc)) from exc
