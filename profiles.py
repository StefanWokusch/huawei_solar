"""Sensor profile configuration for Huawei Solar."""

from __future__ import annotations

from typing import Any, Mapping

from .const import CONF_SENSOR_GROUPS, CONF_SENSOR_PROFILE

SENSOR_PROFILE_MINIMUM = "minimum"
SENSOR_PROFILE_NORMAL = "normal"
SENSOR_PROFILE_ALL_VALUES = "all_values"
SENSOR_PROFILE_CUSTOM = "custom"

SENSOR_PROFILE_OPTIONS = {
    SENSOR_PROFILE_MINIMUM: "Minimum (stable core values)",
    SENSOR_PROFILE_NORMAL: "Normal (recommended)",
    SENSOR_PROFILE_ALL_VALUES: "All values (full)",
    SENSOR_PROFILE_CUSTOM: "Custom (choose groups)",
}

SENSOR_GROUP_INVERTER_CORE = "inverter_core"
SENSOR_GROUP_INVERTER_DIAGNOSTICS = "inverter_diagnostics"
SENSOR_GROUP_PV_STRINGS = "pv_strings"
SENSOR_GROUP_METER_BASIC = "meter_basic"
SENSOR_GROUP_METER_ADVANCED = "meter_advanced"
SENSOR_GROUP_BATTERY_BASIC = "battery_basic"
SENSOR_GROUP_BATTERY_DETAIL = "battery_detail"
SENSOR_GROUP_OPTIMIZER_SUMMARY = "optimizer_summary"
SENSOR_GROUP_OPTIMIZER_DETAIL = "optimizer_detail"

SENSOR_GROUP_OPTIONS = {
    SENSOR_GROUP_INVERTER_CORE: "Inverter core values",
    SENSOR_GROUP_INVERTER_DIAGNOSTICS: "Inverter diagnostics",
    SENSOR_GROUP_PV_STRINGS: "PV string values",
    SENSOR_GROUP_METER_BASIC: "Power meter basic values",
    SENSOR_GROUP_METER_ADVANCED: "Power meter advanced values",
    SENSOR_GROUP_BATTERY_BASIC: "Battery basic values",
    SENSOR_GROUP_BATTERY_DETAIL: "Battery detail values",
    SENSOR_GROUP_OPTIMIZER_SUMMARY: "Optimizer summary values",
    SENSOR_GROUP_OPTIMIZER_DETAIL: "Optimizer detail values",
}

DEFAULT_MINIMUM_SENSOR_GROUPS: tuple[str, ...] = (
    SENSOR_GROUP_INVERTER_CORE,
    SENSOR_GROUP_METER_BASIC,
    SENSOR_GROUP_BATTERY_BASIC,
)

DEFAULT_NORMAL_SENSOR_GROUPS: tuple[str, ...] = (
    SENSOR_GROUP_INVERTER_CORE,
    SENSOR_GROUP_INVERTER_DIAGNOSTICS,
    SENSOR_GROUP_PV_STRINGS,
    SENSOR_GROUP_METER_BASIC,
    SENSOR_GROUP_METER_ADVANCED,
    SENSOR_GROUP_BATTERY_BASIC,
    SENSOR_GROUP_BATTERY_DETAIL,
)

ALL_SENSOR_GROUPS: tuple[str, ...] = tuple(SENSOR_GROUP_OPTIONS.keys())

SENSOR_GROUP_PRESET_MINIMUM = "minimum"
SENSOR_GROUP_PRESET_NORMAL = "normal"
SENSOR_GROUP_PRESET_ALL_VALUES = "all_values"
SENSOR_GROUP_PRESET_MANUAL = "manual"

SENSOR_GROUP_PRESET_OPTIONS = {
    SENSOR_GROUP_PRESET_MINIMUM: "Minimum",
    SENSOR_GROUP_PRESET_NORMAL: "Normal",
    SENSOR_GROUP_PRESET_ALL_VALUES: "All values",
    SENSOR_GROUP_PRESET_MANUAL: "Manual selection",
}


def sanitize_sensor_groups(
    groups: list[str] | tuple[str, ...] | set[str] | None,
) -> set[str]:
    """Return known groups only."""
    if groups is None:
        return set()
    return {group for group in groups if group in SENSOR_GROUP_OPTIONS}


def get_selected_sensor_groups(config: Mapping[str, Any]) -> set[str]:
    """Resolve selected sensor groups from profile + optional custom selection."""
    profile = config.get(CONF_SENSOR_PROFILE, SENSOR_PROFILE_NORMAL)

    if profile == SENSOR_PROFILE_MINIMUM:
        return set(DEFAULT_MINIMUM_SENSOR_GROUPS)

    if profile == SENSOR_PROFILE_CUSTOM:
        custom_groups = config.get(CONF_SENSOR_GROUPS)
        if isinstance(custom_groups, (list, tuple, set)):
            return sanitize_sensor_groups(custom_groups)
        return set(ALL_SENSOR_GROUPS)

    if profile == SENSOR_PROFILE_ALL_VALUES:
        return set(ALL_SENSOR_GROUPS)

    return set(DEFAULT_NORMAL_SENSOR_GROUPS)


def should_use_minimal_device_init(config: Mapping[str, Any]) -> bool:
    """Use full SUN2000 discovery only when optimizer detail entities are requested."""
    profile = config.get(CONF_SENSOR_PROFILE, SENSOR_PROFILE_NORMAL)
    if profile in (SENSOR_PROFILE_MINIMUM, SENSOR_PROFILE_NORMAL):
        return True
    if profile == SENSOR_PROFILE_ALL_VALUES:
        return False

    custom_groups = get_selected_sensor_groups(config)
    return SENSOR_GROUP_OPTIMIZER_DETAIL not in custom_groups


def get_groups_for_preset(preset: str) -> set[str]:
    """Return sensor groups for a custom preset option."""
    if preset == SENSOR_GROUP_PRESET_MINIMUM:
        return set(DEFAULT_MINIMUM_SENSOR_GROUPS)
    if preset == SENSOR_GROUP_PRESET_NORMAL:
        return set(DEFAULT_NORMAL_SENSOR_GROUPS)
    if preset == SENSOR_GROUP_PRESET_ALL_VALUES:
        return set(ALL_SENSOR_GROUPS)
    return set()


def get_matching_preset_for_groups(groups: set[str]) -> str:
    """Resolve preset name for known group combinations."""
    if groups == set(DEFAULT_MINIMUM_SENSOR_GROUPS):
        return SENSOR_GROUP_PRESET_MINIMUM
    if groups == set(DEFAULT_NORMAL_SENSOR_GROUPS):
        return SENSOR_GROUP_PRESET_NORMAL
    if groups == set(ALL_SENSOR_GROUPS):
        return SENSOR_GROUP_PRESET_ALL_VALUES
    return SENSOR_GROUP_PRESET_MANUAL
