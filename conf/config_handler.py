import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AIParameters:
    temperature: float = field(default=0.75)
    top_p: float = field(default=0.9)
    frequency_penalty: float = field(default=0.7)
    presence_penalty: float = field(default=0.4)
    max_tokens: int = field(default=500)
    max_history_size: int = field(default=50)


@dataclass
class Config:
    bot_name: str
    debug: bool

    discord_token: str
    guild_id: str

    model_name: str
    ai_parameters: AIParameters


class ConfigHandler:
    _config: Config

    def __init__(self, config_file_path: Path):
        try:
            with open(config_file_path, "rb") as f:
                self.config = tomllib.load(f)
        except FileNotFoundError:
            ...
