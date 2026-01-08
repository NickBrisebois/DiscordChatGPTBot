import os
import tomllib
from dataclasses import Field, fields
from pathlib import Path
from typing import Annotated, Any, Type, get_args, get_type_hints

from conf.config_types import BaseConfig, Config, ConfigField, ConfigType


class ConfigPropertyRequiredException(Exception):
    def __init__(self, field_name: str):
        self.field_name = field_name
        super().__init__(f"Required value for field '{field_name}' is not set")


class InvalidConfigException(Exception):
    def __init__(self, missing_fields: list[str]):
        self.missing_fields = missing_fields
        super().__init__(f"Missing required fields: {', '.join(missing_fields)}")


class ConfigHandler:
    # Load configuration from file and/or environment variables
    # Setup as a sort of lightweight/homemade version of Pydantic's config

    _config_path: Path
    _config: Config

    def __init__(self, config_file_path: Path):
        self._config_path = config_file_path

    def load_config(self) -> Config:
        raw_toml_config: dict[str, Any] = {}

        if self._config_path.exists():
            try:
                with open(self._config_path, "rb") as f:
                    raw_toml_config = tomllib.load(f)
            except Exception as e:
                print(
                    f"Error loading config file, continuing with just environment variables: (error: {e})"
                )
        else:
            print(f"{self._config_path} file not found, loading from environment only")
            raw_toml_config = {}

        self._config = self._parse_config(Config, raw_toml_config)
        return self._config

    def _parse_config(
        self, config_class: Type[ConfigType], data: dict[str, Any]
    ) -> ConfigType:
        if not issubclass(config_class, BaseConfig):
            raise TypeError(
                f"Config class {config_class} must be a subclass of BaseConfig"
            )

        kwargs: dict[str, Any] = {}
        hints = get_type_hints(config_class, include_extras=True)
        missing_fields: list[str] = []

        for field_name, field_hint in hints.items():
            config_field = self._extract_config_field(field_hint=field_hint)
            try:
                if config_field:
                    kwargs[field_name] = self._get_field_value(
                        field_name=field_name,
                        config_field=config_field,
                        toml_value=data.get(field_name),
                    )
                    continue

                if issubclass(field_hint, BaseConfig):
                    kwargs[field_name] = self._parse_config(
                        field_hint, data.get(field_name, {})
                    )
                    continue
            except ConfigPropertyRequiredException as e:
                missing_fields.append(e.field_name)
                continue
            finally:
                kwargs[field_name] = data.get(field_name)

        if missing_fields:
            raise InvalidConfigException(missing_fields)

        return config_class(**kwargs)

    def _extract_config_field(
        self, field_hint: Annotated[Any, ConfigField]
    ) -> ConfigField | None:
        # Grab the value stored in the Annotated type hint
        args = get_args(field_hint)
        if len(args) < 2:
            return None

        for arg in args[1:]:
            if isinstance(arg, ConfigField):
                return arg

        return None

    def _get_field_value(
        self, field_name: str, config_field: ConfigField, toml_value: Any
    ) -> Any:
        env_value = os.getenv(config_field.env_name)
        if env_value is not None:
            return env_value

        config_val = env_value if env_value is not None else toml_value
        if config_val is None:
            if hasattr(config_field, "default") and config_field.default is not None:
                return config_field.default
            elif config_field.required:
                raise ConfigPropertyRequiredException(field_name)

        return config_val

    def _convert_value(self, value: Any, target_type: type) -> Any:
        if isinstance(value, target_type):
            return value

        if isinstance(value, str):
            try:
                if target_type is bool:
                    return value.lower() in ("true", "1", "yes", "y", "on")
                elif target_type in (int, float):
                    return target_type(value)
                else:
                    return value
            except ValueError:
                raise ValueError(f"Invalid value for type {target_type}: {value}")

        return value

    @property
    def config(self) -> Config:
        if not self._config:
            self._config = self.load_config()

        return self._config
