import logging
import requests
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_RETURNED_URL, CONF_ACCESS_TOKEN, CONF_REFRESH_TOKEN, DEFAULT_REDIRECT_URI

_LOGGER = logging.getLogger(__name__)

class MicrosoftToDoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Microsoft To Do integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step to get client credentials."""
        if user_input is not None:
            # Store client_id and client_secret for later use
            self.client_id = user_input[CONF_CLIENT_ID]
            self.client_secret = user_input[CONF_CLIENT_SECRET]
            return await self.async_step_auth()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_CLIENT_ID): str,
                vol.Required(CONF_CLIENT_SECRET): str
            })
        )

    async def async_step_auth(self, user_input=None):
        """Handle the authentication step and provide the URL for authentication."""
        if user_input is not None:
            returned_url = user_input[CONF_RETURNED_URL]
            auth_code = self.extract_auth_code(returned_url)
            tokens = await self.exchange_code_for_token(auth_code)
            if tokens:
                # Create config entry with tokens and credentials
                return self.async_create_entry(
                    title="Microsoft To Do",
                    data={
                        CONF_CLIENT_ID: self.client_id,
                        CONF_CLIENT_SECRET: self.client_secret,
                        CONF_ACCESS_TOKEN: tokens["access_token"],
                        CONF_REFRESH_TOKEN: tokens["refresh_token"]
                    }
                )

        # Generate authorization URL
        auth_url = (
            f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
            f"?client_id={self.client_id}&response_type=code"
            f"&redirect_uri={DEFAULT_REDIRECT_URI}&response_mode=query"
            f"&scope=Tasks.ReadWrite offline_access"
        )

        # Log the generated authorization URL for debugging purposes
        _LOGGER.info(f"Authorization URL: {auth_url}")

        # Display the link to the user and ask for the returned URL
        return self.async_show_form(
            step_id="auth",
            description_placeholders={"auth_url": auth_url},  # Pass the auth_url to be rendered
            data_schema=vol.Schema({
                vol.Required(CONF_RETURNED_URL): str  # Field where the user pastes the returned URL
            })
        )

    def extract_auth_code(self, returned_url):
        """Extract the authorization code from the returned URL."""
        from urllib.parse import parse_qs, urlparse
        query = parse_qs(urlparse(returned_url).query)
        return query["code"][0]

    async def exchange_code_for_token(self, auth_code):
        """Exchange the authorization code for access and refresh tokens."""
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        data = {
            "client_id": self.client_id,
            "scope": "Tasks.ReadWrite offline_access",
            "code": auth_code,
            "redirect_uri": DEFAULT_REDIRECT_URI,
            "grant_type": "authorization_code",
            "client_secret": self.client_secret
        }

        # Make the request to exchange authorization code for tokens
        response = await self.hass.async_add_executor_job(
            requests.post, token_url, data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            _LOGGER.error(f"Error exchanging code: {response.status_code} - {response.text}")
            return None
