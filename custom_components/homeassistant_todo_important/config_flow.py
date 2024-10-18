import logging
from homeassistant import config_entries
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.core import callback
from homeassistant.helpers.network import get_url
import voluptuous as vol

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class MicrosoftToDoOAuth2FlowHandler(config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN):
    """Config flow to handle Microsoft To Do OAuth2 authentication."""

    DOMAIN = DOMAIN

    @property
    def logger(self):
        return _LOGGER

    @property
    def oauth_auth_url(self):
        """Generate the authorization URL."""
        redirect_uri = self.hass.helpers.network.get_url(self.hass, allow_internal=False, prefer_external=True) + "/auth/external/callback"
        base_auth_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
        params = {
            "client_id": self.flow_impl.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": "User.Read Tasks.ReadWrite",
            "response_mode": "query",
        }
        import urllib.parse
        return base_auth_url + "?" + urllib.parse.urlencode(params)

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

    @staticmethod
    @callback
    def _extract_code_from_url(url):
        """Extract the authorization code from the returned URL."""
        import urllib.parse
        parsed_url = urllib.parse.urlparse(url)
        return urllib.parse.parse_qs(parsed_url.query).get("code", [None])[0]
