import logging
from typing import List, Type, Optional

import requests

from ..core.models import Fact, Message
from ..core.realize_slots import SlotRealizerComponent
from .processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: Of the analyzed comments, a total of {value} were identified as containing hate speech.
| value_type = hate_speech:blocked:abs, value > 0

en: Of the analyzed comments, none were identified as containing hate speech.
| value_type = hate_speech:blocked:abs, value = 0

en: This corresponds to {value} % of all comments.
| value_type = hate_speech:blocked:rel

en: For example, the following comment was identified as containing hate speech: <blockquote> {value} </blockquote>
| value_type = hate_speech:blocked:example
"""


def _generate_hate_speech_blocked_abs(labels: List[str]) -> Message:
    return Message(Fact(len([label for label in labels if label != "Non-Blocked"]), "hate_speech:blocked:abs", 9_10))


def _generate_hate_speech_blocked_rel(labels: List[str]) -> Optional[Message]:
    n_blocked = len([label for label in labels if label != "Non-Blocked"])
    if n_blocked == 0:
        return None
    return Message(Fact(n_blocked / len(labels) * 100, "hate_speech:blocked:rel", 9_09))


def _generate_hate_speech_blocked_example(
    labels: List[str], confidences: List[float], comments: List[str]
) -> Optional[Message]:
    combined = zip(labels, confidences, comments)
    combined = [(label, confidence, comment) for (label, confidence, comment) in combined if label != "Non-Blocked"]
    if not combined:
        return None
    return Message(Fact(max(combined, key=lambda x: x[1])[2], "hate_speech:blocked:example", 9_08))


class HateSpeechResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def generate_messages(self, language: str, comments: List[str]) -> List[Message]:
        hate_speech_data = self._query_model(language, comments)
        labels = hate_speech_data["labels"]
        confidences = hate_speech_data["confidences"]
        messages: List[Message] = [
            _generate_hate_speech_blocked_abs(labels),
            _generate_hate_speech_blocked_rel(labels),
            _generate_hate_speech_blocked_example(labels, confidences, comments),
        ]

        return [m for m in messages if m is not None]

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return []

    def _query_model(self, language: str, comments: List[str]):
        log.info(f"comments: {comments}")
        response = requests.post(
            self.read_config_language_value("HATESPEECH", language, allow_none=False), json={"texts": comments}
        )
        log.info(f"{response}, {response.reason}, {response.text}")
        return response.json()
