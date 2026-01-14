from typing import Annotated

from pymicroconf import BaseConfig, ConfigField


class AIParametersConfig(BaseConfig):
    temperature: Annotated[float, ConfigField("TEMPERATURE", default=0.75)]
    top_p: Annotated[float, ConfigField("TOP_P", default=0.9)]
    frequency_penalty: Annotated[float, ConfigField("FREQUENCY_PENALTY", default=0.7)]
    presence_penalty: Annotated[float, ConfigField("PRESENCE_PENALTY", default=0.4)]
    max_tokens: Annotated[int, ConfigField("MAX_TOKENS", default=500)]
    max_history_size: Annotated[int, ConfigField("MAX_HISTORY_SIZE", default=50)]


class DiscordConfig(BaseConfig):
    token: Annotated[str, ConfigField("DISCORD_TOKEN")]
    guild_id: Annotated[str, ConfigField("DISCORD_GUILD_ID")]


class OpenAIConfig(BaseConfig):
    api_key: Annotated[str, ConfigField("OPENAI_API_KEY")]
    model_name: Annotated[
        str, ConfigField("OPENAI_MODEL_NAME", default="gpt-3.5-turbo")
    ]
    ai_parameters: AIParametersConfig


class Config(BaseConfig):
    bot_name: Annotated[str, ConfigField("BOT_NAME")]
    debug: Annotated[bool, ConfigField("DEBUG", default=False)]

    discord: DiscordConfig
    openai: OpenAIConfig
