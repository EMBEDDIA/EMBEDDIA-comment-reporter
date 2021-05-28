import logging
from typing import List, Type, Optional

import requests

from ..core.models import Fact, Message
from ..core.realize_slots import SlotRealizerComponent
from .processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
en: The mean sentiment of the comments was {value} (higher values indicate more positive sentiment)
| value_type = sentiment:mean

en: Of the analyzed comments, {value} percentage were positive (sentiment >= 0.5).
| value_type = sentiment:perc_positive

en: The most positive comment was <blockquote> {value} </blockquote>
| value_type = sentiment:most_positive
"""


def _generate_sentiment_mean(sentiments: List[float]) -> Optional[Message]:
    if not sentiments:
        return None
    return Message(Fact(sum(sentiments) / len(sentiments), "sentiment:mean", 7_10))


def _generate_sentiment_positive_count(sentiments: List[float]) -> Optional[Message]:
    n_positive = len([f for f in sentiments if f >= 0.5])
    if n_positive == 0:
        return None
    return Message(Fact(n_positive / len(sentiments) * 100, "sentiment:perc_positive", 7_09))


def _generate_sentiment_most_positive(sentiments: List[str], comments: List[str]) -> Optional[Message]:
    combined = zip(sentiments, comments)
    if not combined:
        return None
    return Message(Fact(max(combined, key=lambda x: x[0])[1], "sentiment:most_positive", 7_08))


class SentimentStatsResource(ProcessorResource):
    def templates_string(self) -> str:
        return TEMPLATE

    def generate_messages(self, comments: List[str]) -> List[Message]:
        sentiments = self._query_model(comments)["sentiments"]
        messages: List[Message] = [
            _generate_sentiment_mean(sentiments),
            _generate_sentiment_positive_count(sentiments),
            _generate_sentiment_most_positive(sentiments, comments),
        ]

        return [m for m in messages if m is not None]

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return []

    def _query_model(self, comments: List[str]):
        log.info(f"comments: {comments}")
        response = requests.post(
            self.read_config_value("SENTIMENTANALYSIS", "url", allow_none=False), json={"comments": comments}
        )
        log.info(f"{response}, {response.reason}, {response.text}")
        return response.json()
