"""Token usage sensors for DeepSeek Conversation."""

from __future__ import annotations

from homeassistant.components.sensor import (  # pyright: ignore[reportMissingImports]
    RestoreSensor,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant  # pyright: ignore[reportMissingImports]
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback  # pyright: ignore[reportMissingImports]
from homeassistant.helpers import device_registry as dr  # pyright: ignore[reportMissingImports]

from .const import DOMAIN
from .types import DeepSeekConfigEntry
from .usage_metrics import CompletionUsage, UsageTracker


class DeepSeekUsageCounterSensor(RestoreSensor, SensorEntity):
    """Cumulative token counter (persists across restarts)."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "tokens"
    _attr_icon = "mdi:counter"

    def __init__(
        self,
        entry: DeepSeekConfigEntry,
        translation_key: str,
        unique_suffix: str,
    ) -> None:
        self._entry = entry
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{entry.entry_id}_{unique_suffix}"
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                self._attr_native_value = int(float(last_state.state))
            except (TypeError, ValueError):
                self._attr_native_value = 0
        elif self.native_value is None:
            self._attr_native_value = 0

    def increment(self, amount: int) -> None:
        if amount <= 0:
            return
        self._attr_native_value = int(self.native_value or 0) + amount
        self.async_write_ha_state()


class DeepSeekLastRequestSensor(SensorEntity):
    """Tokens used by the most recent API call."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "tokens"
    _attr_icon = "mdi:history"
    _attr_translation_key = "last_request_tokens"

    def __init__(self, entry: DeepSeekConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_last_request_tokens"
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
        )
        self._attr_native_value = 0

    def set_usage(
        self, usage: CompletionUsage, *, source: str, request_count: int
    ) -> None:
        total = usage.total_tokens or usage.prompt_tokens + usage.completion_tokens
        self._attr_native_value = total
        self._attr_extra_state_attributes = {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "reasoning_tokens": usage.reasoning_tokens,
            "source": source,
            "request_count": request_count,
        }
        self.async_write_ha_state()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DeepSeekConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up token usage sensors."""
    runtime = entry.runtime_data
    tracker: UsageTracker = runtime.usage

    prompt = DeepSeekUsageCounterSensor(entry, "prompt_tokens", "prompt_tokens")
    completion = DeepSeekUsageCounterSensor(
        entry, "completion_tokens", "completion_tokens"
    )
    total = DeepSeekUsageCounterSensor(entry, "total_tokens", "total_tokens")
    last_request = DeepSeekLastRequestSensor(entry)

    tracker.bind_sensors(
        prompt=prompt,
        completion=completion,
        total=total,
        last_request=last_request,
    )
    async_add_entities([prompt, completion, total, last_request])
