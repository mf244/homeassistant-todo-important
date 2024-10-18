import logging
import functools as ft
from homeassistant import config_entries
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import callback
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.network import get_url
import voluptuous as vol

from .const import DOMAIN, CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_URL, AUTH_CALLBACK_PATH, AUTH_CALLBACK_NAME

_LOGGER = logging.getLogger(__name__)

class MicrosoftToDoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Microsoft To Do integration."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._client_id = None
        self._client_secret = None
        self._state = None
        self._callback_url = None
        self._auth_url = None

    async def async_step_user(self, user_input=None):
        """Handle the initial step for user setup."""
        errors = {}

        if user_input is not None:
            self._client_id = user_input[CONF_CLIENT_ID]
            self._client_secret = user_input[CONF_CLIENT_SECRET]
            
            # Prepare OAuth2 authorization flow
            credentials = (self._client_id, self._client_secret)
            redirect_uri = get_callback_url(self.hass)
            token_backend = FileSystemTokenBackend(token_path=self.hass.config.path(), token_filename="ms_todo_token.txt")
            
            # Initialize the account and generate the authorization URL
            from O365 import Account
            self._account = Account(credentials, token_backend=token_backend)
            self._auth_url, self._state = self._account.con.get_authorization_url(
                requested_scopes=["Tasks.ReadWrite"],
                redirect_uri=redirect_uri
            )

            # Proceed to the authorization step
            return await self.async_step_request()

        data_schema = vol.Schema({
            vol.Required(CONF_CLIENT_ID): str,
            vol.Required(CONF_CLIENT_SECRET): str,
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def async_step_request(self, user_input=None):
        """Handle the OAuth2 authorization step."""
        errors = {}

        if user_input is not None:
            # Validate the callback URL from user input
            url = user_input.get(CONF_URL, "")
            if "code" not in url or self._state not in url:
                errors[CONF_URL] = "invalid_url"
                return self.async_show_form(
                    step_id="request", errors=errors
                )

            # Exchange the authorization code for a token
            try:
                result = await self.hass.async_add_executor_job(
                    ft.partial(
                        self._account.con.request_token,
                        url,
                        state=self._state,
                        redirect_uri=self._callback_url
                    )
                )

                if result is True:
                    # Create the entry once authentication is successful
                    return self.async_create_entry(title="Microsoft To Do", data={
                        CONF_CLIENT_ID: self._client_id,
                        CONF_CLIENT_SECRET: self._client_secret,
                    })
                else:
                    errors[CONF_URL] = "token_error"

            except Exception as e:
                _LOGGER.error(f"Error requesting token: {e}")
                errors[CONF_URL] = "token_error"

        # Display authorization URL to the user
        return self.async_show_form(
            step_id="request",
            data_schema=vol.Schema({vol.Required(CONF_URL): str}),
            description_placeholders={"auth_url": self._auth_url},
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

def get_callback_url(hass):
    """Generate the OAuth2 callback URL."""
    return f"{get_url(hass, prefer_external=True)}{AUTH_CALLBACK_PATH}"

class MicrosoftToDoAuthCallbackView(HomeAssistantView):
    """Handle the OAuth2 callback for Microsoft To Do."""

    requires_auth = False
    url = AUTH_CALLBACK_PATH
    name = AUTH_CALLBACK_NAME

    def __init__(self):
        """Initialize the callback view."""
        self.token_url = None

    @callback
    async def get(self, request):
        """Handle the OAuth2 callback request."""
        self.token_url = str(request.url)

        return web_response.Response(
            headers={"content-type": "text/html"},
            text="<script>window.close()</script>This window can be closed",
        )
