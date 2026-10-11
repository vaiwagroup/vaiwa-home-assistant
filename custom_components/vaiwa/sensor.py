"""Native CO2, temperature, humidity, PM and index entities."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature

# Home Assistant compatibility: older Core releases use the legacy constant.
# Core versions that provide UnitOfDensity use the new enum.
try:
    from homeassistant.const import UnitOfDensity
except ImportError:
    from homeassistant.const import CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
    PM_MASS_UNIT = CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
else:
    PM_MASS_UNIT = UnitOfDensity.MICROGRAMS_PER_CUBIC_METER
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, FIREBASE_UID
from .coordinator import VaiwaCoordinator

SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="co2", name="CO₂", device_class=SensorDeviceClass.CO2,
        native_unit_of_measurement="ppm", state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="temperature", name="Temperature", device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="humidity", name="Humidity", device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="pm25", name="PM2.5", device_class=SensorDeviceClass.PM25,
        native_unit_of_measurement=PM_MASS_UNIT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="pm10", name="PM10", device_class=SensorDeviceClass.PM10,
        native_unit_of_measurement=PM_MASS_UNIT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="voc", name="VOC index", state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="nox", name="NOx index", state_class=SensorStateClass.MEASUREMENT,
    ),
)


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
            VaiwaSensor(coordinator, entry.data[FIREBASE_UID], sensor_id, description)
            for sensor_id in sorted(new_ids)
            for description in SENSORS
        )

    add_new_sensors()
    entry.async_on_unload(coordinator.async_add_listener(add_new_sensors))


class VaiwaSensor(CoordinatorEntity[VaiwaCoordinator], SensorEntity):
    """One read-only entity of a physical VAIWA device."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: VaiwaCoordinator, uid: str, sensor_id: str,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self.sensor_id = sensor_id
        self._attr_unique_id = f"{uid}_{sensor_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{uid}_{sensor_id}")},
            name=f"VAIWA {coordinator.data[sensor_id]['name']}",
            manufacturer="VAIWA",
            model="SEN66",
        )

    @property
    def available(self) -> bool:
        if not super().available or self.sensor_id not in (self.coordinator.data or {}):
            return False
        return self.coordinator.data[self.sensor_id]["data"].get("online") is not False

    @property
    def native_value(self) -> float | int | None:
        sensor = (self.coordinator.data or {}).get(self.sensor_id, {})
        value = sensor.get("data", {}).get(self.entity_description.key)
        if isinstance(value, (float, int)) and not isinstance(value, bool):
            return value
        return None
