# Changelog

All notable changes to this integration.

## [1.3.0] - 2026-07-01

### Added

- **Reauthentication** when your API key expires or is rejected — fix credentials in Home Assistant settings without removing and re-adding the integration.
- **Token usage sensors** per config entry: cumulative prompt, completion, and total tokens, plus a “last request” sensor (with reasoning tokens as an attribute when the API reports them). Useful for cost tracking and troubleshooting.
- **DeepSeek brand icons** in the integrations list and config flow (Home Assistant 2026.3+).
- **More translations** for the `generate_content` service, invalid config entry errors, reasoning effort labels, and the debug notification (EN, DE, FR, ZH).

### Improved

- **Faster option changes**: updates to prompt, model, temperature, thinking, and similar options apply immediately in Assist without reloading the whole integration. Reload only runs for connection settings (base URL, API key).
- **Quicker setup and reauth**: credentials are verified via `models.list` instead of a chat completion, so setup does not consume tokens.
- **`generate_content` with reasoning**: temperature and top_p are no longer sent when reasoning is enabled (consistent with Assist).
- **More reliable device control**: Home Assistant tools with invalid schemas are skipped instead of being sent with empty parameters, which previously caused opaque API errors.

### Fixed

- **Reasoning off**: DeepSeek-specific `extra_body` is only sent when reasoning is enabled, improving compatibility if you later point the integration at other OpenAI-compatible endpoints.
