import logging
from homeassistant.helpers import discovery
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    """Set up the Microsoft To Do integration from YAML configuration."""
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]
    hass.data[DOMAIN] = conf

    # Set up the sensor platform using discovery
    hass.async_create_task(
        discovery.async_load_platform(hass, 'sensor', DOMAIN, {}, conf)
    )

    return True
