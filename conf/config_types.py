from dataclasses import dataclass
from typing import Annotated, Any, TypeVar


class ConfigField:
    parse_to: type
    env_name: str
    required: bool
    default: Any

    def __init__(
        self, parse_to: type, env_name: str, required: bool = True, default: Any = None
    ):
        self.parse_to = parse_to
        self.env_name = env_name
        self.required = required
        self.default = default


@dataclass
class BaseConfig:
    pass


@dataclass
class AIParametersConfig(BaseConfig):
    temperature: Annotated[float, ConfigField(float, "TEMPERATURE", default=0.75)]
    top_p: Annotated[float, ConfigField(float, "TOP_P", default=0.9)]
    frequency_penalty: Annotated[
        float, ConfigField(float, "FREQUENCY_PENALTY", default=0.7)
    ]
    presence_penalty: Annotated[
        float, ConfigField(float, "PRESENCE_PENALTY", default=0.4)
    ]
    max_tokens: Annotated[int, ConfigField(int, "MAX_TOKENS", default=500)]
    max_history_size: Annotated[int, ConfigField(int, "MAX_HISTORY_SIZE", default=50)]


@dataclass
class DiscordConfig(BaseConfig):
    token: Annotated[str, ConfigField(str, "DISCORD_TOKEN")]
    guild_id: Annotated[str, ConfigField(str, "DISCORD_GUILD_ID")]


@dataclass
class OpenAIConfig(BaseConfig):
    api_key: Annotated[str, ConfigField(str, "OPENAI_API_KEY")]
    ai_parameters: AIParametersConfig


@dataclass
class Config(BaseConfig):
    bot_name: Annotated[str, ConfigField(str, "BOT_NAME")]
    debug: Annotated[bool, ConfigField(bool, "DEBUG", default=False)]

    discord: DiscordConfig
    openai: OpenAIConfig


ConfigType = TypeVar("ConfigType", bound=BaseConfig)
