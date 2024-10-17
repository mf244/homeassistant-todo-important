import logging
import requests
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_ACCESS_TOKEN, CONF_REFRESH_TOKEN

_LOGGER = logging.getLogger(__name__)

class MicrosoftToDoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Microsoft To Do integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step to get client credentials and tokens."""
        errors = None
        if user_input is not None:
            self.client_id = user_input[CONF_CLIENT_ID]
            self.client_secret = user_input[CONF_CLIENT_SECRET]
            self.access_token = user_input[CONF_ACCESS_TOKEN]
            self.refresh_token = user_input[CONF_REFRESH_TOKEN]

            return self.async_create_entry(
                title="Microsoft To Do",
                data={
                    CONF_CLIENT_ID: self.client_id,
                    CONF_CLIENT_SECRET: self.client_secret,
                    CONF_ACCESS_TOKEN: self.access_token,
                    CONF_REFRESH_TOKEN: self.refresh_token,
                }
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_CLIENT_ID): str,
                vol.Required(CONF_CLIENT_SECRET): str,
                vol.Required(CONF_ACCESS_TOKEN): str,
                vol.Required(CONF_REFRESH_TOKEN): str,
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return MicrosoftToDoOptionsFlowHandler(config_entry)


class MicrosoftToDoOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for the Microsoft To Do integration."""

    def __init__(self, config_entry):
        """Initialize the options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options for the integration."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("polling_interval", default=5): int,
            }),
        )
