import logging
from homeassistant import config_entries
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.core import callback
import voluptuous as vol

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class MicrosoftToDoOAuth2FlowHandler(config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN):
    """Config flow to handle Microsoft To Do OAuth2 authentication."""

    DOMAIN = DOMAIN

    @property
    def logger(self):
        return _LOGGER

    async def async_step_user(self, user_input=None):
        """Initial step to start OAuth2 login."""
        self.logger.debug("Starting OAuth2 login for Microsoft To Do.")
        return await self.async_step_auth()

    async def async_step_auth(self, user_input=None):
        """Handle the OAuth2 authentication step."""
        if user_input is None:
            return self.async_show_form(
                step_id="auth",
                description_placeholders={"auth_url": self.oauth_auth_url},
                data_schema=vol.Schema({vol.Required("returned_url"): str})
            )

        # Extract authorization code from the provided URL
        try:
            authorization_code = self._extract_code_from_url(user_input["returned_url"])
            token = await self._exchange_code(authorization_code)
            if token:
                return self.async_create_entry(title="Microsoft To Do", data=token)
            else:
                return self.async_show_form(
                    step_id="auth",
                    errors={"base": "auth_failed"}
                )
        except Exception as e:
            self.logger.error(f"Error during OAuth2 authentication: {e}")
            return self.async_show_form(
                step_id="auth",
                errors={"base": "auth_failed"}
            )

    async def async_step_reauth(self, user_input=None):
        """Handle re-authentication."""
        self.logger.debug("Re-authenticating user.")
        return await self.async_step_auth()

    async def async_step_repair(self, user_input=None):
        """Handle the repair flow for re-authentication."""
        self.logger.debug("Starting repair flow for re-authentication.")
        if user_input is None:
            return self.async_show_form(
                step_id="repair",
                description_placeholders={"auth_url": self.oauth_auth_url},
                data_schema=vol.Schema({vol.Required("returned_url"): str})
            )

        # Attempt to re-authenticate
        try:
            authorization_code = self._extract_code_from_url(user_input["returned_url"])
            token = await self._exchange_code(authorization_code)
            if token:
                self.hass.config_entries.async_update_entry(
                    self._async_current_entry, data=token
                )
                return self.async_create_entry(title="Microsoft To Do", data=token)
            else:
                return self.async_show_form(
                    step_id="repair",
                    errors={"base": "auth_failed"}
                )
        except Exception as e:
            self.logger.error(f"Error during repair flow: {e}")
            return self.async_show_form(
                step_id="repair",
                errors={"base": "auth_failed"}
            )

    @staticmethod
    @callback
    def _extract_code_from_url(url):
        """Extract the authorization code from the returned URL."""
        import urllib.parse
        parsed_url = urllib.parse.urlparse(url)
        return urllib.parse.parse_qs(parsed_url.query).get("code", [None])[0]
