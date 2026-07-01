"""Shared types for the DeepSeek Conversation integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import openai
from homeassistant.config_entries import ConfigEntry  # pyright: ignore[reportMissingImports]

from .usage_metrics import UsageTracker


@dataclass
class DeepSeekRuntimeData:
    """Per-config-entry runtime state (OpenAI client + usage tracking)."""

    client: openai.AsyncClient
    usage: UsageTracker


DeepSeekConfigEntry: TypeAlias = ConfigEntry[DeepSeekRuntimeData]
