"""Device creation helpers with resilient SUN2000 fallback initialization."""

from __future__ import annotations

import logging
from typing import Any

from huawei_solar import (
    HuaweiSolarException,
    ReadException,
    register_names as rn,
    register_values as rv,
)
from huawei_solar.device import (
    create_device_instance,
    create_sub_device_instance,
)
from huawei_solar.device.base import HuaweiSolarDevice
from huawei_solar.device.sun2000 import SUN2000Device

_LOGGER = logging.getLogger(__name__)


def _is_sun2000_model(model_name: str) -> bool:
    return model_name.startswith(("SUN", "EDF ESS", "Powershifter", "SWI300"))


def _compute_pv_registers(pv_string_count: int) -> list[str]:
    if not 1 <= pv_string_count <= 24:
        return []
    return [
        register_name
        for idx in range(1, pv_string_count + 1)
        for register_name in (
            getattr(rn, f"PV_{idx:02}_VOLTAGE"),
            getattr(rn, f"PV_{idx:02}_CURRENT"),
        )
    ]


async def _safe_get(device: HuaweiSolarDevice, register: rn.RegisterName, default: Any) -> Any:
    try:
        return (await device.get(register)).value
    except (HuaweiSolarException, TimeoutError, ReadException):
        return default


async def _populate_sun2000_minimal(device: SUN2000Device) -> None:
    """Populate the minimum required SUN2000 fields without optimizer probing."""
    serial_number = await _safe_get(device, rn.SERIAL_NUMBER, None)
    product_number = await _safe_get(device, rn.PN, "")
    firmware_version = await _safe_get(device, rn.FIRMWARE_VERSION, "")
    software_version = await _safe_get(device, rn.SOFTWARE_VERSION, "")

    if serial_number in (None, ""):
        serial_number = f"{device.model_name}_{device.client.unit_id}"

    device.serial_number = str(serial_number)
    device.product_number = str(product_number)
    device.firmware_version = str(firmware_version)
    device.software_version = str(software_version)

    pv_string_count = await _safe_get(device, rn.NB_PV_STRINGS, 1)
    if not isinstance(pv_string_count, int):
        pv_string_count = 1
    if pv_string_count < 1:
        pv_string_count = 1
    device.pv_string_count = pv_string_count
    device._pv_registers = _compute_pv_registers(pv_string_count)

    # Explicitly skip optimizer probing in fallback mode.
    device.has_optimizers = False

    device.battery_1_type = await _safe_get(
        device,
        rn.STORAGE_UNIT_1_PRODUCT_MODEL,
        rv.StorageProductModel.NONE,
    )
    device.battery_2_type = await _safe_get(
        device,
        rn.STORAGE_UNIT_2_PRODUCT_MODEL,
        rv.StorageProductModel.NONE,
    )
    device.supports_capacity_control = False

    meter_status = await _safe_get(device, rn.METER_STATUS, None)
    device.power_meter_online = meter_status == rv.MeterStatus.NORMAL
    if device.power_meter_online:
        device.power_meter_type = await _safe_get(device, rn.METER_TYPE, None)
    else:
        device.power_meter_type = None

    device._dst = await _safe_get(device, rn.DAYLIGHT_SAVING_TIME, None)
    device._time_zone = await _safe_get(device, rn.TIME_ZONE, None)


async def _create_sun2000_minimal(
    client: Any,
    model_name: str,
    primary_device: HuaweiSolarDevice | None,
) -> SUN2000Device:
    device = SUN2000Device(
        client,
        model_name=model_name,
        primary_device=primary_device,
    )
    await _populate_sun2000_minimal(device)
    return device


async def create_device_instance_resilient(
    client: Any,
    *,
    prefer_minimal: bool,
) -> HuaweiSolarDevice:
    """Create device instance with minimal SUN2000 fallback when needed."""
    model_name = (await client.get(rn.MODEL_NAME)).value
    if isinstance(model_name, str) and _is_sun2000_model(model_name):
        if prefer_minimal:
            _LOGGER.info(
                "Using minimal SUN2000 initialization path for unit %s",
                client.unit_id,
            )
            return await _create_sun2000_minimal(client, model_name, None)

        try:
            return await create_device_instance(client)
        except (TimeoutError, HuaweiSolarException) as err:
            _LOGGER.warning(
                "Falling back to minimal SUN2000 initialization for unit %s: %s",
                client.unit_id,
                err,
            )
            return await _create_sun2000_minimal(client, model_name, None)

    return await create_device_instance(client)


async def create_sub_device_instance_resilient(
    primary_device: HuaweiSolarDevice,
    unit_id: int,
    *,
    prefer_minimal: bool,
) -> HuaweiSolarDevice:
    """Create sub-device instance with minimal SUN2000 fallback when needed."""
    sub_client = primary_device.client.for_unit_id(unit_id)
    model_name = (await sub_client.get(rn.MODEL_NAME)).value

    if isinstance(model_name, str) and _is_sun2000_model(model_name):
        if prefer_minimal:
            _LOGGER.info(
                "Using minimal SUN2000 initialization path for sub-device unit %s",
                unit_id,
            )
            return await _create_sun2000_minimal(sub_client, model_name, primary_device)

        try:
            return await create_sub_device_instance(primary_device, unit_id)
        except (TimeoutError, HuaweiSolarException) as err:
            _LOGGER.warning(
                "Falling back to minimal SUN2000 sub-device initialization for unit %s: %s",
                unit_id,
                err,
            )
            return await _create_sun2000_minimal(sub_client, model_name, primary_device)

    return await create_sub_device_instance(primary_device, unit_id)
