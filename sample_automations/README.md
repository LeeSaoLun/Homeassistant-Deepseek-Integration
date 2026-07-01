# Sample automations

Copy a YAML file into **Automations → Create automation → Edit in YAML**, save, then trigger.

**Requirement:** one loaded `deepseek_conversation` config entry (no IDs to edit; entry and agent are resolved automatically).

Vision demo: place any image at `/config/www/deepseek_demo.jpg` and allow `/config/www` in `allowlist_external_dirs` if needed.

| Event | File |
|-------|------|
| `deepseek_integration_demo` | `deepseek_integration_demo.yaml` |
| `deepseek_vision_demo` | `deepseek_vision_demo.yaml` (place any image at `/config/www/deepseek_demo.jpg` first) |

Results: **persistent notification** + logbook. Token sensors update after each API call.

`run_debug`: see `examples/run_deepseek_debug_script.yaml`.
