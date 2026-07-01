# Changelog

Alle wesentlichen Änderungen an dieser Integration.

## [1.3.0] - 2026-07-01

- chore: add bump.bat and use CHANGELOG.md for GitHub releases (a8def45)
- feat: add token usage sensors and metrics from API responses (2e9ad03)
- i18n: add missing translations for services, exceptions, and debug notification (cfeef1c)
- perf: reload config entry only for connection changes, not options (9333571)
- fix: skip tools with invalid schema instead of sending empty parameters (475fe93)
- fix: omit DeepSeek extra_body when reasoning is disabled (27f7ec2)
- chore: run CI on dev branch pushes (5ab017b)
- chore: bump integration version to 1.3.0 (1a60a06)
- feat: add DeepSeek brand icons for Home Assistant 2026.3+ (af49224)
- chore: centralize DeepSeekConfigEntry type alias and clean up imports (27f7324)
- refactor: validate API credentials with models.list instead of chat completion (9ec72d9)
- fix: share chat completion args and omit sampling when reasoning is on (ab5ed0e)
- feat: add reauth config flow for expired or invalid API keys (ebedf4b)
