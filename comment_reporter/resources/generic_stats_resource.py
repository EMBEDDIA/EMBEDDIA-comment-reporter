import logging
from typing import List, Type

from ..core.models import Fact, Message
from ..core.realize_slots import SlotRealizerComponent
from .processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: This report describes an automated analysis conducted on {value} comments
| value_type = stats:count

en: The report has been generated automatically, in parts using machine learning methods, and no guarantee is made with regard to the accuracy of its contents
| value_type = stats:disclaimer
"""  # noqa: E501


def _parse_count_msg(comments: List[str]) -> Message:
    return Message(Fact(len(comments), "stats:count", 10_10))


def _generate_disclaimer() -> Message:
    return Message(Fact(None, "stats:disclaimer", 10_09))


class GenericStatsResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def generate_messages(self, comments: List[str]) -> List[Message]:
        messages: List[Message] = [
            _parse_count_msg(comments),
            _generate_disclaimer(),
        ]

        return messages

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return []
