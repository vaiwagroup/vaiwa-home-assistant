"""Sensor online/offline entity."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, FIREBASE_UID
from .coordinator import VaiwaCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator: VaiwaCoordinator = hass.data[DOMAIN][entry.entry_id]
    known: set[str] = set()

    def add_new_sensors() -> None:
        new_ids = set(coordinator.data or {}) - known
        if not new_ids:
            return
        known.update(new_ids)
        async_add_entities(
            VaiwaOnline(coordinator, entry.data[FIREBASE_UID], sensor_id)
            for sensor_id in sorted(new_ids)
        )

    add_new_sensors()
    entry.async_on_unload(coordinator.async_add_listener(add_new_sensors))


class VaiwaOnline(CoordinatorEntity[VaiwaCoordinator], BinarySensorEntity):
    """Online status of one VAIWA device."""

    _attr_has_entity_name = True
    _attr_name = "Online"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: VaiwaCoordinator, uid: str, sensor_id: str) -> None:
        super().__init__(coordinator)
        self.sensor_id = sensor_id
        self._attr_unique_id = f"{uid}_{sensor_id}_online"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{uid}_{sensor_id}")},
            name=f"VAIWA {coordinator.data[sensor_id]['name']}",
            manufacturer="VAIWA",
            model="SEN66",
        )

    @property
    def available(self) -> bool:
        return super().available and self.sensor_id in (self.coordinator.data or {})

    @property
    def is_on(self) -> bool | None:
        sensor = (self.coordinator.data or {}).get(self.sensor_id, {})
        online = sensor.get("data", {}).get("online")
        return online if isinstance(online, bool) else None
