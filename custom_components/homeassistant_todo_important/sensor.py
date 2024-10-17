import logging
import requests
from datetime import timedelta
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from .const import DOMAIN, CONF_ACCESS_TOKEN, CONF_REFRESH_TOKEN, CONF_CLIENT_ID, CONF_CLIENT_SECRET

_LOGGER = logging.getLogger(__name__)

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

        # Correct the async_add_executor_job call to pass arguments directly
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
