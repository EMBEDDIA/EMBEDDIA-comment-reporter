import configparser
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Type, Optional

from ..core.models import Message
from ..core.realize_slots import SlotRealizerComponent


class ProcessorResource(ABC):

    EPSILON = 0.00000001

    @abstractmethod
    def templates_string(self) -> str:
        pass

    @abstractmethod
    def generate_messages(self, language: str, comments: List[str]) -> List[Message]:
        pass

    @abstractmethod
    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        pass

    def read_config_language_value(self, group: str, key: str, allow_none: bool = False) -> Optional[str]:
        value = self.read_config_value(group, key, True)
        if not value:
            value = self.read_config_value(group, "all", True)
        if (not value) and (not allow_none):
            raise Exception(f"config.ini missing mandatory value '{key}' for group '{group}'")
        return value

    @staticmethod
    def read_config_value(group: str, key: str, allow_none: bool = False) -> Optional[str]:
        config_path = Path(__file__).parent / ".." / ".." / "config.ini"
        try:
            config = configparser.ConfigParser()
            config.read(str(config_path))
            return config[group][key]
        except Exception:
            if allow_none:
                return None
            raise Exception(f"config.ini missing mandatory value '{key}' for group '{group}'")
