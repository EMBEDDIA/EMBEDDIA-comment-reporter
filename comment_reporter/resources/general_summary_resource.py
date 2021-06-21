import logging
from itertools import chain
from typing import List, Type

from nltk import sent_tokenize
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

    def generate_messages(self, language: str, comments: List[str]) -> List[Message]:
        summary = " ".join(self._query_model(language, comments)["summary"])
        return [Message(Fact(summary, "summary", 8_10))]

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return []

    def _query_model(self, language: str, comments: List[str]):
        sentences = list(chain(*[sent_tokenize(comment) for comment in comments]))
        log.info(f"comments as sentenced: {sentences}")
        response = requests.post(
            self.read_config_language_value("SUMMARIZATION", language, allow_none=False),
            json={"comments": sentences, "count": 5},
        )
        return response.json()
