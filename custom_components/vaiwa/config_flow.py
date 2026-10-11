"""UI login flow for VAIWA Cloud."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from .api import VaiwaAuthError, VaiwaConnectionError, async_sign_in
from .const import DOMAIN, FIREBASE_UID, PUBLIC_FIREBASE_WEB_API_KEY, REFRESH_TOKEN

_LOGGER = logging.getLogger(__name__)


class VaiwaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Connect one VAIWA account to Home Assistant."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if PUBLIC_FIREBASE_WEB_API_KEY == "PASTE_VAIWA_FIREBASE_WEB_API_KEY_HERE":
                return self.async_show_form(
                    step_id="user",
                    data_schema=_login_schema(),
                    errors={"base": "not_configured"},
                )
            try:
                result = await async_sign_in(
                    async_get_clientsession(self.hass),
                    PUBLIC_FIREBASE_WEB_API_KEY,
                    user_input[CONF_EMAIL].strip(),
                    user_input[CONF_PASSWORD],
                )
            except VaiwaAuthError:
                errors["base"] = "invalid_auth"
            except VaiwaConnectionError:
                errors["base"] = "cannot_connect"
            else:
                uid = result["localId"]
                await self.async_set_unique_id(uid)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"VAIWA ({user_input[CONF_EMAIL].strip()})",
                    data={
                        CONF_EMAIL: user_input[CONF_EMAIL].strip(),
                        FIREBASE_UID: uid,
                        REFRESH_TOKEN: result["refreshToken"],
                    },
                )

        return self.async_show_form(step_id="user", data_schema=_login_schema(), errors=errors)


def _login_schema() -> vol.Schema:
    """Only user-facing credentials; no Firebase developer settings."""
    return vol.Schema(
        {
            vol.Required(CONF_EMAIL): str,
            vol.Required(CONF_PASSWORD): TextSelector(
                TextSelectorConfig(type=TextSelectorType.PASSWORD)
            ),
        }
    )
