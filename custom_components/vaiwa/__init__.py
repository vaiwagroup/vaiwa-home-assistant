"""VAIWA Cloud Home Assistant integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import entity_registry as er

from .api import VaiwaCloudClient
from .const import DOMAIN, FIREBASE_API_KEY, FIREBASE_UID, PUBLIC_FIREBASE_WEB_API_KEY, REFRESH_TOKEN
from .coordinator import VaiwaCoordinator

PLATFORMS = ["sensor", "binary_sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Initialize one logged-in Vaiwa account."""

    def save_refresh_token(token: str) -> None:
        if entry.data.get(REFRESH_TOKEN) != token:
            hass.config_entries.async_update_entry(
                entry, data={**entry.data, REFRESH_TOKEN: token}
            )

    client = VaiwaCloudClient(
        session=async_get_clientsession(hass),
        api_key=entry.data.get(FIREBASE_API_KEY) or PUBLIC_FIREBASE_WEB_API_KEY,
        uid=entry.data[FIREBASE_UID],
        refresh_token=entry.data[REFRESH_TOKEN],
        save_refresh_token=save_refresh_token,
    )
    coordinator = VaiwaCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    # Pri aktualizacii z V1 odstranime stare PM1.0/PM4.0 entity
    # z registru, aby nezostali ako nedostupne alebo skryte polozky.
    registry = er.async_get(hass)
    uid_prefix = f"{entry.data[FIREBASE_UID]}_"
    for item in er.async_entries_for_config_entry(registry, entry.entry_id):
        if (
            item.platform == DOMAIN
            and item.domain == "sensor"
            and item.unique_id.startswith(uid_prefix)
            and item.unique_id.endswith(("_pm1", "_pm4"))
        ):
            registry.async_remove(item.entity_id)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload entities and remove references."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded
