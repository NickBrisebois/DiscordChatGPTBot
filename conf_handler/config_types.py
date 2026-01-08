from dataclasses import dataclass
from typing import Any, TypeVar


class ConfigField:
    env_name: str
    required: bool
    default: Any

    def __init__(self, env_name: str, required: bool = True, default: Any = None):
        self.env_name = env_name
        self.required = required
        self.default = default


class BaseConfig:
    def __init_subclass__(cls, **kwargs):
        # just automatically declare subclasses as dataclasses so we can skip the decorators
        super().__init_subclass__(**kwargs)
        dataclass(cls)


ConfigType = TypeVar("ConfigType", bound=BaseConfig)
