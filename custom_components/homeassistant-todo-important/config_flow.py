import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_RETURNED_URL, DEFAULT_REDIRECT_URI

_LOGGER = logging.getLogger(__name__)

@callback
def configured_instances(hass):
    """Return a set of configured instances."""
    return set(entry.title for entry in hass.config_entries.async_entries(DOMAIN))

class MicrosoftToDoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Microsoft To Do integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            self.client_id = user_input[CONF_CLIENT_ID]
            self.client_secret = user_input[CONF_CLIENT_SECRET]
            return await self.async_step_auth()

        # Show form to ask for client_id and client_secret
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_CLIENT_ID): str,
                vol.Required(CONF_CLIENT_SECRET): str
            })
        )

    async def async_step_auth(self, user_input=None):
        """Handle the authentication step."""
        if user_input is not None:
            returned_url = user_input[CONF_RETURNED_URL]
            # Process the returned URL and exchange the authorization code for tokens
            # Here you would extract the code from the URL and request access/refresh tokens

            # Once authenticated, complete the config flow
            return self.async_create_entry(title="Microsoft To Do", data={
                CONF_CLIENT_ID: self.client_id,
                CONF_CLIENT_SECRET: self.client_secret,
                CONF_RETURNED_URL: returned_url
            })

        # Show the link to start authentication and ask for the returned URL
        return self.async_show_form(
            step_id="auth",
            description_placeholders={
                "auth_url": f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id={self.client_id}&response_type=code&redirect_uri={DEFAULT_REDIRECT_URI}&response_mode=query&scope=Tasks.ReadWrite offline_access"
            },
            data_schema=vol.Schema({
                vol.Required(CONF_RETURNED_URL): str
            })
        )
