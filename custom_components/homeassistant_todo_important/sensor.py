import logging
from datetime import timedelta
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from homeassistant.helpers import config_entry_oauth2_flow

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=1)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Microsoft To Do sensor platform."""
    oauth2session = hass.data[DOMAIN][config_entry.entry_id]
    todo_data = MicrosoftToDoData(hass, oauth2session)
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

    def __init__(self, hass, oauth2session):
        """Initialize the data handler."""
        self.hass = hass
        self.oauth2session = oauth2session
        self.important_tasks = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def update(self):
        """Update important tasks from the API."""
        url = "https://graph.microsoft.com/v1.0/me/todo/lists"
        try:
            response = await self.oauth2session.async_request("GET", url)

            if response.status_code == 200:
                task_lists = response.json().get("value", [])
                important_tasks = []

                for task_list in task_lists:
                    list_id = task_list["id"]
                    tasks_url = f"https://graph.microsoft.com/v1.0/me/todo/lists/{list_id}/tasks"
                    tasks_response = await self.oauth2session.async_request("GET", tasks_url)

                    if tasks_response.status_code == 200:
                        tasks_data = tasks_response.json().get("value", [])
                        for task in tasks_data:
                            if task.get("importance") == "high" and task.get("status") in ["notStarted", "inProgress"]:
                                important_tasks.append(task["title"])

                self.important_tasks = "\n".join(important_tasks) if important_tasks else "No important tasks found"
            else:
                _LOGGER.error(f"Error fetching task lists: {response.status_code} - {response.text}")

        except Exception as e:
            _LOGGER.error(f"Exception while fetching tasks: {e}")
