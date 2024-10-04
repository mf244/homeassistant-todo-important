from homeassistant.core import HomeAssistant
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry):
    """Set up Microsoft To Do from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Store tokens for further use
    hass.states.async_set(f"{DOMAIN}.status", "Authenticated")
    
    return True
