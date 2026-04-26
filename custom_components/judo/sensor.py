"""Sensor entities for JUDO."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfMass,
    UnitOfTime,
    UnitOfVolume,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import JudoCoordinator, JudoData


@dataclass(kw_only=True, frozen=True)
class JudoSensorDescription(SensorEntityDescription):
    value_fn: Callable[[JudoData], Any]
    attrs_fn: Callable[[JudoData], dict[str, Any] | None] | None = None


SENSORS: tuple[JudoSensorDescription, ...] = (
    JudoSensorDescription(
        key="target_hardness",
        translation_key="target_hardness",
        native_unit_of_measurement="°dH",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.target_hardness,
    ),
    JudoSensorDescription(
        key="salt_storage_mass",
        translation_key="salt_storage_mass",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda d: d.salt_storage_mass_kg,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    JudoSensorDescription(
        key="salt_range",
        translation_key="salt_range",
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:calendar-clock",
        value_fn=lambda d: d.salt_range_days,
    ),
    JudoSensorDescription(
        key="salt_warning_threshold",
        translation_key="salt_warning_threshold",
        native_unit_of_measurement=UnitOfTime.DAYS,
        icon="mdi:bell-alert",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.salt_warning_days,
    ),
    JudoSensorDescription(
        key="service_contact",
        translation_key="service_contact",
        icon="mdi:phone",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.service_contact,
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
        # device counter; meaning depends on model (see README)
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


# Sensors that depend on the cloud relay (myjudo.eu). Only added when cloud
# credentials are configured — see async_setup_entry.
CLOUD_SENSORS: tuple[JudoSensorDescription, ...] = (
    JudoSensorDescription(
        key="live_flow",
        translation_key="live_flow",
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        native_unit_of_measurement=UnitOfVolumeFlowRate.LITERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:waves-arrow-right",
        value_fn=lambda d: d.live_flow_l_per_h,
    ),
    JudoSensorDescription(
        key="input_hardness",
        translation_key="input_hardness",
        native_unit_of_measurement="°dH",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:water-plus",
        value_fn=lambda d: d.input_hardness_dh,
    ),
    JudoSensorDescription(
        key="regeneration_count",
        translation_key="regeneration_count",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:water-sync",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.regeneration_count,
    ),
    JudoSensorDescription(
        key="battery_backup",
        translation_key="battery_backup",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.battery_backup_percent,
    ),
    JudoSensorDescription(
        key="days_until_maintenance",
        translation_key="days_until_maintenance",
        native_unit_of_measurement=UnitOfTime.DAYS,
        icon="mdi:account-wrench",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.days_until_maintenance,
    ),
    JudoSensorDescription(
        key="status",
        translation_key="status",
        icon="mdi:information-outline",
        value_fn=lambda d: d.status_text,
        attrs_fn=lambda d: d.cloud_status_attrs,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: JudoCoordinator = hass.data[DOMAIN][entry.entry_id]
    descriptions: list[JudoSensorDescription] = list(SENSORS)
    if coordinator.cloud is not None:
        descriptions.extend(CLOUD_SENSORS)
    async_add_entities(
        JudoSensor(coordinator, entry.entry_id, desc) for desc in descriptions
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

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        fn = self.entity_description.attrs_fn
        if fn is None or self.coordinator.data is None:
            return None
        return fn(self.coordinator.data)
