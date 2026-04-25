"""Sensor-Entitäten für Judo."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfMass, UnitOfTime, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import JudoCoordinator, JudoData


@dataclass(kw_only=True, frozen=True)
class JudoSensorDescription(SensorEntityDescription):
    value_fn: Callable[[JudoData], Any]


SENSORS: tuple[JudoSensorDescription, ...] = (
    JudoSensorDescription(
        key="target_hardness",
        translation_key="target_hardness",
        native_unit_of_measurement="°dH",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.target_hardness,
    ),
    JudoSensorDescription(
        key="salt_level",
        translation_key="salt_level",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.GRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.salt_level_g,
    ),
    JudoSensorDescription(
        key="total_water",
        translation_key="total_water",
        device_class=SensorDeviceClass.WATER,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d.total_water_m3,
        suggested_display_precision=2,
    ),
    JudoSensorDescription(
        key="soft_water",
        translation_key="soft_water",
        device_class=SensorDeviceClass.WATER,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d.soft_water_m3,
        suggested_display_precision=2,
    ),
    JudoSensorDescription(
        key="operating_time",
        translation_key="operating_time",
        value_fn=lambda d: d.operating_text,
        # Geräte-Counter, Bedeutung modellabhängig (s. README)
        entity_registry_enabled_default=True,
    ),
    JudoSensorDescription(
        key="daily_water",
        translation_key="daily_water",
        device_class=SensorDeviceClass.WATER,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d.daily_total_l,
    ),
    JudoSensorDescription(
        key="installation_date",
        translation_key="installation_date",
        device_class=SensorDeviceClass.DATE,
        value_fn=lambda d: d.installation_date.date() if d.installation_date else None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: JudoCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        JudoSensor(coordinator, entry.entry_id, desc) for desc in SENSORS
    )


class JudoSensor(CoordinatorEntity[JudoCoordinator], SensorEntity):
    _attr_has_entity_name = True
    entity_description: JudoSensorDescription

    def __init__(
        self,
        coordinator: JudoCoordinator,
        entry_id: str,
        description: JudoSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> Any:
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)
