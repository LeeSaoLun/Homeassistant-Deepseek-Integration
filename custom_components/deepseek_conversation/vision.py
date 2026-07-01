"""Shared vision/image encoding for Assist and generate_content.

Used by conversation.py (UserContent.attachments from Assist / AI Task) and
__init__.py (generate_content filenames). DeepSeek V4 expects OpenAI-style
image_url content parts.
"""

from __future__ import annotations

import base64
from mimetypes import guess_file_type
from pathlib import Path
from typing import Any

from homeassistant.components import conversation  # pyright: ignore[reportMissingImports]
from homeassistant.core import HomeAssistant  # pyright: ignore[reportMissingImports]
from homeassistant.exceptions import HomeAssistantError  # pyright: ignore[reportMissingImports]

from .const import LOGGER


def encode_file_path(file_path: str | Path) -> tuple[str, str]:
    """Return ``(mime_type, base64_data)`` for a local file."""
    path = Path(file_path)
    mime_type, _ = guess_file_type(str(path))
    if mime_type is None:
        mime_type = "application/octet-stream"
    with path.open("rb") as image_file:
        return mime_type, base64.b64encode(image_file.read()).decode("utf-8")


def image_url_content_part(mime_type: str, base64_data: str) -> dict[str, Any]:
    """Build one DeepSeek/OpenAI ``image_url`` content part."""
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{mime_type};base64,{base64_data}"},
    }


def model_supports_vision(model: str) -> bool:
    """Whether the configured model id is expected to accept image inputs."""
    m = (model or "").strip().lower()
    if not m:
        return True
    # Legacy deepseek-reasoner and similar ids do not support vision.
    return "reasoner" not in m


def content_list_has_attachments(
    content_list: list[conversation.Content],
) -> bool:
    """True when any user turn in the chat log carries attachments."""
    return any(
        isinstance(content, conversation.UserContent) and content.attachments
        for content in content_list
    )


def _normalize_mime_type(file_path: Path, mime_type: str | None) -> str:
    if mime_type:
        return mime_type
    guessed, _ = guess_file_type(str(file_path))
    return guessed or "application/octet-stream"


def _image_part_from_path(file_path: Path, mime_type: str | None) -> dict[str, Any]:
    resolved_mime = _normalize_mime_type(file_path, mime_type)
    if not resolved_mime.startswith("image/"):
        raise HomeAssistantError(
            f"Only image attachments are supported, got {resolved_mime} for `{file_path}`"
        )
    encoded_mime, base64_data = encode_file_path(file_path)
    return image_url_content_part(encoded_mime, base64_data)


async def async_image_parts_from_paths(
    hass: HomeAssistant,
    files: list[tuple[Path, str | None]],
    *,
    strict: bool,
) -> list[dict[str, Any]]:
    """Encode local files to DeepSeek image content parts.

    ``strict=True`` (Assist): raise on missing or non-image files.
    ``strict=False`` (generate_content service): log and skip disallowed files.
    """

    def _read_all() -> list[dict[str, Any]]:
        parts: list[dict[str, Any]] = []
        for file_path, mime_type in files:
            if not file_path.exists():
                message = f"`{file_path}` does not exist"
                if strict:
                    raise HomeAssistantError(message)
                LOGGER.warning("[Debug vision]: %s", message)
                continue
            resolved_mime = _normalize_mime_type(file_path, mime_type)
            if not resolved_mime.startswith("image/"):
                message = (
                    f"Skipping `{file_path}`: unsupported type {resolved_mime} "
                    "(only image/* is supported)"
                )
                if strict:
                    raise HomeAssistantError(
                        f"Only image attachments are supported, got {resolved_mime}"
                    )
                LOGGER.warning("[Debug vision]: %s", message)
                continue
            parts.append(_image_part_from_path(file_path, mime_type))
        return parts

    parts = await hass.async_add_executor_job(_read_all)
    if parts:
        LOGGER.debug(
            "[Debug vision]: encoded %d image part(s) from %d file(s)",
            len(parts),
            len(files),
        )
    return parts


async def async_image_parts_from_attachments(
    hass: HomeAssistant,
    attachments: list[conversation.Attachment],
) -> list[dict[str, Any]]:
    """Encode HA ``Attachment`` objects from Assist / AI Task chat logs."""
    files = [(attachment.path, attachment.mime_type) for attachment in attachments]
    return await async_image_parts_from_paths(hass, files, strict=True)


async def async_image_parts_from_filenames(
    hass: HomeAssistant,
    filenames: list[str],
) -> list[dict[str, Any]]:
    """Encode ``generate_content`` ``filenames`` paths (non-strict skip)."""
    files: list[tuple[Path, str | None]] = []
    for filename in filenames:
        if not hass.config.is_allowed_path(filename):
            LOGGER.warning(
                "[Debug vision]: cannot read %s, path not allowed; "
                "adjust allowlist_external_dirs in configuration.yaml",
                filename,
            )
            continue
        files.append((Path(filename), None))
    return await async_image_parts_from_paths(hass, files, strict=False)


async def async_user_message_content(
    hass: HomeAssistant,
    text: str,
    attachments: list[conversation.Attachment] | None,
) -> str | list[dict[str, Any]]:
    """Build ``content`` for a DeepSeek user message (plain text or parts array)."""
    if not attachments:
        return text

    parts: list[dict[str, Any]] = []
    if text.strip():
        parts.append({"type": "text", "text": text})
    parts.extend(await async_image_parts_from_attachments(hass, attachments))
    if not parts:
        raise HomeAssistantError("Image attachment could not be read")
    LOGGER.debug(
        "[Debug vision]: user message with %d part(s) (%d attachment(s))",
        len(parts),
        len(attachments),
    )
    return parts
