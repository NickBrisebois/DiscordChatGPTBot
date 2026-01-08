import os
import tomllib
from pathlib import Path
from typing import Annotated, Any, Generic, Type, get_args, get_type_hints

from conf_handler.config_types import BaseConfig, ConfigField, ConfigType


class ConfigPropertyRequiredException(Exception):
    def __init__(self, field_name: str):
        self.field_name = field_name
        super().__init__(f"Required value for field '{field_name}' is not set")


class InvalidConfigException(Exception):
    def __init__(self, missing_fields: list[str]):
        self.missing_fields = missing_fields
        super().__init__(f"Missing required fields: {', '.join(missing_fields)}")


class ConfigHandler(Generic[ConfigType]):
    """
    Generic configuration handler that loads from TOML with environment variable overrides
    Heavily influenced by Pydantic
    """

    _config_path: Path
    _config_class: Type[ConfigType]
    _config: ConfigType | None

    def __init__(self, config_file_path: Path, config_class: Type[ConfigType]):
        self._config_path = config_file_path
        self._config_class = config_class
        self._config = None

    def load_config(self) -> ConfigType:
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

        self._config = self._parse_config(self._config_class, raw_toml_config)
        return self._config

    def _parse_config(
        self, container_class_type: Type[ConfigType], data: dict[str, Any]
    ) -> ConfigType:
        if not issubclass(container_class_type, BaseConfig):
            raise TypeError(
                f"Config class {container_class_type} must be a subclass of BaseConfig"
            )

        kwargs: dict[str, Any] = {}
        hints = get_type_hints(container_class_type, include_extras=True)
        missing_fields: list[str] = []

        for field_name, field_hint in hints.items():
            sub_config_type, config_field = self._get_field_meta(field_hint=field_hint)
            try:
                if config_field:
                    kwargs[field_name] = self._parse_field_value(
                        field_type=sub_config_type,
                        field_name=field_name,
                        config_field=config_field,
                        toml_value=data.get(field_name),
                    )
                elif sub_config_type and issubclass(sub_config_type, BaseConfig):
                    kwargs[field_name] = self._parse_config(
                        sub_config_type, data.get(field_name, {})
                    )
                else:
                    kwargs[field_name] = data.get(field_name)
            except InvalidConfigException as e:
                missing_fields.extend(e.missing_fields)
            except ConfigPropertyRequiredException as e:
                missing_fields.append(e.field_name)
            except TypeError:
                # sub_config_type isn't a class so we just use the raw data
                kwargs[field_name] = data.get(field_name)
            except Exception as e:
                print(f"Error parsing field {field_name}, using raw value: {e}")
                kwargs[field_name] = data.get(field_name)

        if missing_fields:
            raise InvalidConfigException(missing_fields)

        return container_class_type(**kwargs)

    def _get_field_meta(
        self, field_hint: Any
    ) -> tuple[type, ConfigField] | tuple[type, None]:
        args = get_args(field_hint)
        if len(args) == 0:
            return field_hint, None
        elif len(args) == 1:
            return args[0], None
        elif len(args) >= 2 and isinstance(args[1], ConfigField):
            return args[0], args[1]

        return args[0], None

    def _parse_field_value(
        self,
        field_type: type | None,
        field_name: str,
        config_field: ConfigField,
        toml_value: Any,
    ) -> Any:
        config_val = toml_value

        if config_field.env_name in os.environ:
            # env vars always take precedence over config file values
            config_val = os.getenv(config_field.env_name)

        if config_val is None:
            if config_field.default is not None:
                return config_field.default
            elif config_field.required:
                raise ConfigPropertyRequiredException(field_name)

        return self._convert_value(config_val, field_type) if field_type else config_val

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
    def config(self) -> ConfigType:
        if not self._config:
            self._config = self.load_config()

        return self._config
