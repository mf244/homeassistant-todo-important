import requests
import logging
from datetime import timedelta
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from .const import DOMAIN, CONF_ACCESS_TOKEN, CONF_REFRESH_TOKEN, CONF_CLIENT_ID, CONF_CLIENT_SECRET

_LOGGER = logging.getLogger(__name__)

# Throttle to ensure the update method is only called once per minute
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=1)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Microsoft To Do sensor platform."""
    client_id = config_entry.data[CONF_CLIENT_ID]
    client_secret = config_entry.data[CONF_CLIENT_SECRET]
    access_token = config_entry.data[CONF_ACCESS_TOKEN]
    refresh_token = config_entry.data[CONF_REFRESH_TOKEN]

    todo_data = MicrosoftToDoData(hass, client_id, client_secret, access_token, refresh_token)
    async_add_entities([MicrosoftToDoSensor(todo_data)], True)

class MicrosoftToDoSensor(Entity):
    """Representation of a Microsoft To Do sensor."""

    def __init__(self, todo_data):
        """Initialize the sensor."""
        self._state = None
        self.todo_data = todo_data

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Microsoft To Do Important Tasks"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    async def async_update(self):
        """Update the sensor state."""
        await self.todo_data.update()
        self._state = self.todo_data.important_tasks

class MicrosoftToDoData:
    """Handle Microsoft To Do API requests."""

    def __init__(self, hass, client_id, client_secret, access_token, refresh_token):
        """Initialize the data handler."""
        self.hass = hass
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.important_tasks = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def update(self):
        """Update important tasks from the API."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = "https://graph.microsoft.com/v1.0/me/todo/lists"

        response = await self.hass.async_add_executor_job(requests.get, url, headers)
        if response.status_code == 200:
            task_lists = response.json().get("value", [])
            important_tasks = []

            for task_list in task_lists:
                list_id = task_list["id"]
                tasks_url = f"https://graph.microsoft.com/v1.0/me/todo/lists/{list_id}/tasks"
                tasks_response = requests.get(tasks_url, headers=headers)

                if tasks_response.status_code == 200:
                    tasks_data = tasks_response.json().get("value", [])
                    for task in tasks_data:
                        if task.get("importance") == "high" and task.get("status") in ["notStarted", "inProgress"]:
                            important_tasks.append(task["title"])

            self.important_tasks = "\n".join(important_tasks) if important_tasks else "No important tasks found"
        else:
            _LOGGER.error(f"Error fetching tasks: {response.status_code} - {response.text}")

    async def refresh_access_token(self):
        """Refresh the access token using the refresh token."""
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "scope": "Tasks.ReadWrite offline_access"
        }

        response = await self.hass.async_add_executor_job(requests.post, token_url, data)
        if response.status_code == 200:
            tokens = response.json()
        
            # Update access and refresh tokens
            self.access_token = tokens["access_token"]
            self.refresh_token = tokens["refresh_token"]

            # Update the tokens in Home Assistant config entry
            self.hass.config_entries.async_update_entry(
                entry=self.hass.config_entries.async_entries(DOMAIN)[0],
                data={
                    CONF_CLIENT_ID: self.client_id,
                    CONF_CLIENT_SECRET: self.client_secret,
                    CONF_ACCESS_TOKEN: self.access_token,
                    CONF_REFRESH_TOKEN: self.refresh_token,
                }
            )
        else:
            _LOGGER.error(f"Error refreshing token: {response.status_code} - {response.text}")
