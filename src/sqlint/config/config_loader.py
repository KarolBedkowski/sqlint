import logging
import os
import warnings
from configparser import ConfigParser, NoOptionError, NoSectionError
from typing import Any, Dict, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INI = os.path.join(BASE_DIR, "default.ini")

# section name in ini file
SECTION = "sqlint"

# type of each config values
NAME_TYPES = {
    "max-line-length": int,  # max line length
    "comma-position": str,  # Comma position in breaking a line
    "keyword-style": str,  # Reserved keyword style
    "indent-steps": int,  # indent steps in breaking a line
}


logger = logging.getLogger(__name__)


class ConfigLoader:
    def __init__(self, config_file: Optional[str] = DEFAULT_INI):
        if config_file is None:
            config_file = DEFAULT_INI

        self.values: Dict[str, Any] = {}
        if not os.path.exists(DEFAULT_INI):
            raise FileNotFoundError(
                f"default setting file is not found: {DEFAULT_INI}"
            )

        # load default configs
        default_config = ConfigParser()
        default_config.read(DEFAULT_INI)
        self._load(default_config)

        # load user config
        self.user_config_file: Optional[str]
        if config_file != DEFAULT_INI:
            self.user_config_file = config_file

            if not os.path.exists(self.user_config_file):
                logger.warning(
                    "[Warning] config file is not found: %s", config_file
                )
            else:
                user_config = ConfigParser()
                user_config.read(self.user_config_file)

                # load user configs
                self._load(user_config)

    @staticmethod
    def _get_with_type(config_parser: ConfigParser, name: str, _type: type):
        """

        Args:
            config_parser:
            name:
            _type:

        Returns:

        """
        if _type == int:
            return config_parser.getint(SECTION, name)
        if _type == float:
            return config_parser.getfloat(SECTION, name)
        if _type == bool:
            return config_parser.getboolean(SECTION, name)

        # type is str or others
        return config_parser.get(SECTION, name)

    def _load(self, config_parser: ConfigParser):
        """Loads config values"""

        for name, _type in NAME_TYPES.items():
            try:
                self.values[name] = self._get_with_type(
                    config_parser, name, _type
                )
            except NoSectionError as err:
                raise err
            except NoOptionError as err:
                # raise Error
                raise err
            except ValueError as err:
                # TODO: raise config Error
                raise err

    def get(self, name, default=None):
        """Returns value by name"""
        if name in self.values:
            return self.values[name]

        return default


class Config:
    def __init__(self, config_file: Optional[str] = DEFAULT_INI):
        if config_file is None:
            config_file = DEFAULT_INI

        self.loader: ConfigLoader = ConfigLoader(config_file)

    @property
    def max_line_length(self) -> int:
        result = self.loader.get("max-line-length")
        if result < 32:
            warnings.warn(
                f"max-line-length value must be more 32, but {result}"
                f" So defualt value(128) was used."
            )
            return 128

        return result

    @property
    def comma_position(self) -> str:
        result = self.loader.get("comma-position")
        if result not in ["head", "end"]:
            warnings.warn(
                f'comma-position value must be "head" or "end", but {result}'
                f" So defualt value(before) was used."
            )
            return "head"

        return result

    @property
    def keyword_style(self) -> str:
        result = self.loader.get("keyword-style")
        if result not in ["upper-all", "lower", "upper-head"]:
            warnings.warn(
                'keyword-style value must be "upper-all", "lower" or '
                f'"upper-head", but {result}. So default value(lower) was used.'
            )
            return "lower"

        return result

    @property
    def indent_steps(self) -> int:
        result = self.loader.get("indent-steps")
        if result < 0:
            warnings.warn(
                f"indent-steps value must be more 0, but {result}"
                f" So defualt value(4) was used."
            )
            return 4

        return self.loader.get("indent-steps")
