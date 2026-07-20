# План: Добавление поддержки выбора API Provider (OpenAI / Anthropic)

## Обзор задачи
Добавить возможность выбора провайдера API при настройке интеграции. В текущей версии используется только OpenAI SDK, нужно добавить поддержку Anthropic SDK.

## Важное замечание
**DeepSeek официально поддерживает ТОЛЬКО OpenAI-compatible API**. Anthropic SDK не может напрямую работать с DeepSeek endpoint без использования gateway/proxy.

Возможные варианты реализации:
1. **Gateway подход**: Использовать сторонний proxy который конвертирует запросы между OpenAI и Anthropic форматами
2. **Поддержка другого провайдера**: Позволить пользователю указывать любой OpenAI-compatible API endpoint (уже поддерживается через base_url)
3. **Ограничить выбор до OpenAI**: В UI показывать "API Provider" как information, но только OpenAI реально работает

## Файлы для изменения

### 1. manifest.json ✅
- Добавить `anthropic>=0.49.0` в requirements
- Увеличить version с 1.3.3 до 1.3.4

### 2. const.py ✅
Добавить константы:
```python
CONF_API_PROVIDER = "api_provider"
API_PROVIDER_OPENAI = "openai"
API_PROVIDER_ANTHROPIC = "anthropic"
DEFAULT_API_PROVIDER = API_PROVIDER_OPENAI

def get_api_provider() -> str:
    """Get the current API provider, defaults to OpenAI."""
    return DEFAULT_API_PROVIDER
```

### 3. config_flow.py — Основные изменения:

**A. Импорты (строки 9-10):**
```python
import openai
try:
    import anthropic
except ImportError:
    anthropic = None
```

**B. Новые функции:**

```python
def _api_provider_selector() -> SelectSelector:
    """Return selector for API provider choice."""
    return SelectSelector(
        SelectSelectorConfig(
            options=[
                SelectOptionDict(value=API_PROVIDER_OPENAI, label="OpenAI"),
                SelectOptionDict(value=API_PROVIDER_ANTHROPIC, label="Anthropic (via gateway)"),
            ],
            mode=SelectSelectorMode.Dropdown,  # or SelectSelectorMode.RADIO if side-by-side
        )
    )

def _get_api_provider_selector() -> SelectSelector:
    """Return provider selector with dynamic options based on Anthropic availability."""
    from homeassistant.helpers.selector import SelectSelectorMode
    
    options = [SelectOptionDict(value=API_PROVIDER_OPENAI, label="OpenAI")]
    if anthropic:
        options.append(SelectOptionDict(value=API_PROVIDER_ANTHROPIC, label="Anthropic (via proxy/gateway)"))
    
    return SelectSelector(
        SelectSelectorConfig(
            options=options,
            mode=SelectSelectorMode.Dropdown,
        )
    )
```

**C. Модификация `get_user_step_schema()`:**
Добавить опцию выбора provider на первом шаге:
```python
def get_user_step_schema(api_provider_available: bool = True) -> vol.Schema:
    return vol.Schema({
        vol.Required(CONF_API_KEY): _api_key_selector(),
        vol.Optional(
            CONF_BASE_URL, 
            default=DEEPSEEK_API_BASE_URL
        ): _base_url_selector(),
        vol.Optional(
            CONF_CHAT_MODEL, 
            default=RECOMMENDED_CHAT_MODEL
        ): _chat_model_selector(),
        # NEW: API provider selection (only for initial setup)
        vol.Optional(
            CONF_API_PROVIDER,
            default=DEFAULT_API_PROVIDER
        ): SelectSelector(SelectSelectorConfig(options=["openai", "anthropic"])),
    })
```

**D. Модификация `validate_input()`:**
Создать factory function для создания клиента:
```python
async def get_api_client(data: dict[str, Any], hass: HomeAssistant) -> tuple[BaseClient | None, str]:
    """Create appropriate API client based on selected provider."""
    provider = data.get(CONF_API_PROVIDER, DEFAULT_API_PROVIDER)
    
    if provider == API_PROVIDER_OPENAI:
        return _create_openai_client(data, hass), ""
    elif provider == API_PROVIDER_ANTHROPIC:
        # Anthropic requires gateway/proxy — show warning
        return None, "Anthropic needs a proxy/gateway configured at base_url"
    return None, "Unknown API provider"

async def async_probe_deepseek_client(client):
    """Validate credentials - needs to work for both providers."""
    if isinstance(client, OpenAIClient):
        await _probe_openai_client(client)
    elif isinstance(client, AnthropicClient):
        await _probe_anthropic_client(client)
```

**E. Модификация `DeepSeekConfigFlow.async_step_user()`:**
Сохранять provider в entry.data:
```python
else:
    entry_data = {
        CONF_API_KEY: user_input[CONF_API_KEY],
        CONF_BASE_URL: user_input.get(CONF_BASE_URL, DEEPSEEK_API_BASE_URL),
        CONF_API_PROVIDER: user_input.get(CONF_API_PROVIDER, DEFAULT_API_PROVIDER),
    }
```

### 4. conversation.py — Основные изменения:

**A. Импорты:**
```python
try:
    import anthropic
    from anthropic.types import Message as AnthropicMessage
except ImportError:
    anthropic = None
    AnthropicMessage = None
```

**B. Factory function для клиента:**
```python
async def get_client(entry: DeepSeekConfigEntry, hass: HomeAssistant) -> BaseChatClient:
    """Get chat client based on configured provider."""
    provider = entry.data.get(CONF_API_PROVIDER, DEFAULT_API_PROVIDER)
    base_url = entry.data.get(CONF_BASE_URL, DEEPSEEK_API_BASE_URL)
    api_key = entry.data[CONF_API_KEY]
    
    if provider == API_PROVIDER_OPENAI:
        return OpenAIClient(api_key, base_url, hass)
    elif provider == API_PROVIDER_ANTHROPIC:
        # This won't work directly with DeepSeek — needs gateway
        raise HomeAssistantError(
            "Anthropic provider requires an Anthropic-compatible endpoint. "
            "DeepSeek uses OpenAI-compatible format."
        )
    raise ValueError(f"Unknown API provider: {provider}")
```

**C. Обертка для форматирования сообщений:**
OpenAI и Anthropic используют разные форматы messages — нужна конвертация!

**D. Модификация `build_chat_completion_args()`:**
Нужно определить, какой SDK использовать и адаптировать параметры.

### 5. __init__.py — Инициализация клиента:

Создать отдельный файл `client.py` или модифицировать существующую логику для поддержки разных SDK.

## Технические сложности

1. **Разные форматы сообщений:**
   - OpenAI: `{role, content, ...}` + tools/choice
   - Anthropic: `{role, content, tool_use/tool_result}` — полностью другая структура!

2. **Разные параметры API:**
   - temperature/top_p работают одинаково
   - reasoning/thinking — у DeepSeek это `thinking` в extra_body, у Anthropic — `max_tokens`, `temperature` + special params
   - system prompt: у OpenAI первый message может быть system, у Anthropic только системный уровень

3. **Streaming:** Разные типы событий

4. **Tools/Functions:** У Anthropic это `tool_use`, у OpenAI — `tools/tool_choice`

## Рекомендуемое решение

**Вместо полной поддержки Anthropic**, сделать:

1. **Информационное поле**: В config_flow показать выбор provider, но только "OpenAI" доступен
2. **Гибкая настройка base_url**: Пользователь может указать любой OpenAI-compatible endpoint
3. **Документация**: Указать что DeepSeek требует OpenAI формат

Или альтернативно:

1. Реализовать конвертер между форматами (отдельная задача)
2. Использовать gateway service как middleware

## Следующие шаги

1. ✅ Обновить manifest.json
2. ✅ Добавить константы в const.py  
3. ⏳ Изменить config_flow.py — добавить selector (упрощенно только OpenAI выбор)
4. ⏳ Создать `client.py` с factory pattern для разных SDK
5. ⏳ Обновить conversation.py для использования factory
6. ⏺️ Обновить __init__.py
7. ⏺️ Тестирование

## Примечание
Если пользователь хочет использовать Anthropic, ему нужно:
- Настроить proxy/gateway который принимает Anthropic запросы и преобразует их в OpenAI формат
- Или использовать другой endpoint который поддерживает Anthropic напрямую (например, свой LLM)
