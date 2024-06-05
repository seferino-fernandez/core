"""Support for an Intergas heater via an InComfort/InTouch Lan2RF gateway."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from incomfortclient import Heater as InComfortHeater

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import UnitOfPressure, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import InComfortConfigEntry
from .const import DOMAIN
from .coordinator import InComfortDataCoordinator
from .entity import IncomfortEntity

INCOMFORT_HEATER_TEMP = "CV Temp"
INCOMFORT_PRESSURE = "CV Pressure"
INCOMFORT_TAP_TEMP = "Tap Temp"


@dataclass(frozen=True, kw_only=True)
class IncomfortSensorEntityDescription(SensorEntityDescription):
    """Describes Incomfort sensor entity."""

    value_key: str
    extra_key: str | None = None
    # IncomfortSensor does not support UNDEFINED or None,
    # restrict the type to str
    name: str = ""


SENSOR_TYPES: tuple[IncomfortSensorEntityDescription, ...] = (
    IncomfortSensorEntityDescription(
        key="cv_pressure",
        name=INCOMFORT_PRESSURE,
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.BAR,
        value_key="pressure",
    ),
    IncomfortSensorEntityDescription(
        key="cv_temp",
        name=INCOMFORT_HEATER_TEMP,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        extra_key="is_pumping",
        value_key="heater_temp",
    ),
    IncomfortSensorEntityDescription(
        key="tap_temp",
        name=INCOMFORT_TAP_TEMP,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        extra_key="is_tapping",
        value_key="tap_temp",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: InComfortConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up InComfort/InTouch sensor entities."""
    incomfort_coordinator = entry.runtime_data
    heaters = incomfort_coordinator.data.heaters
    async_add_entities(
        IncomfortSensor(incomfort_coordinator, heater, description)
        for heater in heaters
        for description in SENSOR_TYPES
    )


class IncomfortSensor(IncomfortEntity, SensorEntity):
    """Representation of an InComfort/InTouch sensor device."""

    entity_description: IncomfortSensorEntityDescription

    def __init__(
        self,
        coordinator: InComfortDataCoordinator,
        heater: InComfortHeater,
        description: IncomfortSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description

        self._heater = heater

        self._attr_unique_id = f"{heater.serial_no}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, heater.serial_no)},
            manufacturer="Intergas",
            name="Boiler",
        )

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self._heater.status[self.entity_description.value_key]

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the device state attributes."""
        if (extra_key := self.entity_description.extra_key) is None:
            return None
        return {extra_key: self._heater.status[extra_key]}
