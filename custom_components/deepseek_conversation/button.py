"""Button entities for DeepSeek Conversation.

Reset usage: calls UsageTracker.reset_all() in usage_metrics.py (all token/request
sensors on the integration device).
"""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity  # pyright: ignore[reportMissingImports]
from homeassistant.core import HomeAssistant  # pyright: ignore[reportMissingImports]
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback  # pyright: ignore[reportMissingImports]
from homeassistant.helpers import device_registry as dr  # pyright: ignore[reportMissingImports]

from .const import DOMAIN, LOGGER
from .types import DeepSeekConfigEntry


class DeepSeekResetUsageButton(ButtonEntity):
    """Reset all token and API request usage sensors to zero."""

    _attr_has_entity_name = True
    _attr_translation_key = "reset_usage"
    _attr_icon = "mdi:counter"

    def __init__(self, entry: DeepSeekConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_reset_usage"
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
        )

    async def async_press(self) -> None:
        """Reset cumulative and last-request usage sensors."""
        runtime = self._entry.runtime_data
        runtime.usage.reset_all()
        LOGGER.info(
            "[Debug button]: usage counters reset manually for entry %s",
            self._entry.entry_id,
        )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DeepSeekConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up DeepSeek button entities."""
    async_add_entities([DeepSeekResetUsageButton(entry)])
