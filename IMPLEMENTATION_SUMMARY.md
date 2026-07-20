# Реализация выбора API Provider

## Изменения внесены в файлы:

### ✅ 1. `manifest.json`
```json
{
  "version": "1.3.4",
  "requirements": [
    "openai>=1.68.2,<3",
    "voluptuous-openapi>=0.2.0,<0.5",
    "anthropic>=0.49.0"  // ← Добавлено
  ]
}
```

### ✅ 2. `const.py` — Новые константы:
```python
CONF_API_PROVIDER = "api_provider"
API_PROVIDER_OPENAI = "openai"
API_PROVIDER_ANTHROPIC = "anthropic"
DEFAULT_API_PROVIDER = API_PROVIDER_OPENAI
```

### ✅ 3. `config_flow.py` — Добавлен выбор provider:

**Новые импорты:**
```python
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
```

**Новая функция `_api_provider_selector()`:**
```python
def _api_provider_selector() -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=[
                SelectOptionDict(value=API_PROVIDER_OPENAI, label="OpenAI"),
                # + Anthropic если библиотека установлена
            ],
            mode=SelectSelectorMode.Dropdown,
        )
    )
```

**Модифицировано `get_user_step_schema()`:**
- Добавлено поле `CONF_API_PROVIDER` с выбором провайдера

**Модифицирована `DeepSeekConfigFlow.async_step_user()`:**
- Сохраняет `CONF_API_PROVIDER` в entry.data

### ✅ 4. `__init__.py` — Инициализация клиента:

```python
# Проверяет provider при создании клиента
provider = entry.data.get(CONF_API_PROVIDER, API_PROVIDER_OPENAI)

if provider == API_PROVIDER_ANTHROPIC and not HAS_ANTHROPIC:
    raise ConfigEntryNotReady("Anthropic library required")

# Warn если Anthropic выбран но DeepSeek требует OpenAI формат
if provider == API_PROVIDER_ANTHROPIC:
    LOGGER.warning(
        "Anthropic provider selected. Note: Direct Anthropic SDK cannot communicate with "
        "DeepSeek's OpenAI-compatible endpoint."
    )

# Создаёт OpenAI client (так как DeepSeek использует OpenAI формат)
client = openai.AsyncOpenAI(
    api_key=entry.data[CONF_API_KEY],
    base_url=base_url,
    http_client=get_async_client(hass),
)
```

### ✅ 5. `conversation.py` — Поддержка provider в диалогах:

```python
# Добавлена проверка compatibility
provider = self.entry.data.get(CONF_API_PROVIDER, API_PROVIDER_OPENAI)

if provider == API_PROVIDER_ANTHROPIC:
    LOGGER.warning(
        "Anthropic provider selected but DeepSeek uses OpenAI-compatible format. "
        "For Anthropic models, configure an Anthropic-compatible endpoint in base_url."
    )
```

## Важное замечание ⚠️

**DeepSeek официально поддерживает ТОЛЬКО OpenAI-compatible API формат.**

### Текущее поведение:
1. Пользователь выбирает провайдер в настройках (OpenAI или Anthropic)
2. Интеграция **всегда использует OpenAI SDK** так как DeepSeek endpoint требует этот формат
3. Если выбран Anthropic — выводится предупреждение о необходимости использовать proxy/gateway

### Для полноценной поддержки Anthropic потребуется:

1. **Gateway подход**: Настроить сервис который преобразует запросы между форматами
2. **Альтернативный endpoint**: Использовать другой LLM API который поддерживает Anthropic SDK
3. **Конвертер сообщений**: Реализовать конвертацию между OpenAI и Anthropic форматами (полностью разные структуры!)

### Рекомендуемое использование:

**Для DeepSeek:**
- Выбирайте **OpenAI** в выборе provider
- Укажите `https://api.deepseek.com/v1` в base_url

**Для других моделей:**
- Выберите соответствующий API endpoint в base_url
- Provider выбор — информационный (для будущих расширений)
