import logging
from typing import List, Type

import requests

from ..core.models import Fact, Message
from ..core.realize_slots import SlotRealizerComponent
from .processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: In general, the analyzed comments are best summarized by this comment: <blockquote> {value} </blockquote>
| value_type = summary
"""


class GeneralSummaryResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def generate_messages(self, comments: List[str]) -> List[Message]:
        summary = self._query_model(comments)["summary"][0]
        return [Message(Fact(summary, "summary", 8_10))]

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return []

    def _query_model(self, comments: List[str]):
        log.info(f"comments as sentenced: {comments}")
        response = requests.post(
            self.read_config_value("SUMMARIZATION", "url", allow_none=False), json={"comments": comments, "count": 1}
        )
        log.info(f"{response}, {response.reason}, {response.text}")
        return response.json()
