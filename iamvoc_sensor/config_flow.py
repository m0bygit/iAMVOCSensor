"""Config flow for iAM VOC Sensor integration."""
from __future__ import annotations

import logging
from typing import Any

import usb.core
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)

DOMAIN = "iamvoc_sensor"


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # Check if the USB device is present
    def check_device():
        dev = usb.core.find(idVendor=0x03eb, idProduct=0x2013)
        if dev is None:
            raise CannotConnect
        return True

    try:
        await hass.async_add_executor_job(check_device)
    except Exception as err:
        _LOGGER.exception("Unexpected exception")
        raise CannotConnect from err

    # Return info that you want to store in the config entry.
    return {"title": "iAM VOC Sensor"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for iAM VOC Sensor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check if already configured
                await self.async_set_unique_id("iamvoc_sensor_usb")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data={})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
