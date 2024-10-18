import logging
from homeassistant import config_entries
from homeassistant.helpers import config_entry_oauth2_flow

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
        return await self.async_step_auth()

    async def async_step_auth(self):
        """Handle the authentication step."""
        self.logger.debug("Redirecting user to Microsoft login.")
        return await self.async_oauth_create_entry()

    async def async_step_reauth(self, user_input=None):
        """Handle re-authentication."""
        self.logger.debug("Re-authenticating user.")
        return await self.async_step_auth()

    async def async_oauth_create_entry(self):
        """Create an entry for the OAuth authentication."""
        self.logger.debug("Creating OAuth entry.")
        return await self.async_create_entry(title="Microsoft To Do", data=self.token)
