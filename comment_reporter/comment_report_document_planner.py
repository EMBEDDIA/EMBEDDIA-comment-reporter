import logging
from typing import List, Optional, Tuple

from .core.document_planner import BodyDocumentPlanner, HeadlineDocumentPlanner
from .core.models import Message

log = logging.getLogger("root")

MAX_PARAGRAPHS = 5

MAX_SATELLITES_PER_NUCLEUS = 10
MIN_SATELLITES_PER_NUCLEUS = 4

NEW_PARAGRAPH_ABSOLUTE_THRESHOLD = 0.5

SATELLITE_RELATIVE_THRESHOLD = 0.5
SATELLITE_ABSOLUTE_THRESHOLD = 0.2


class CommentReportBodyDocumentPlanner(BodyDocumentPlanner):
    def __init__(self) -> None:
        super().__init__(new_paragraph_absolute_threshold=NEW_PARAGRAPH_ABSOLUTE_THRESHOLD)

    def select_next_nucleus(
        self, available_message: List[Message], selected_nuclei: List[Message]
    ) -> Tuple[Message, float]:
        return _select_next_nucleus(available_message, selected_nuclei)

    def new_paragraph_relative_threshold(self, selected_nuclei: List[Message]) -> float:
        return _new_paragraph_relative_threshold(selected_nuclei)

    def select_satellites_for_nucleus(self, nucleus: Message, available_messages: List[Message]) -> List[Message]:
        return _select_satellites_for_nucleus(nucleus, available_messages)


class CommentReportHeadlineDocumentPlanner(HeadlineDocumentPlanner):
    def select_next_nucleus(
        self, available_message: List[Message], selected_nuclei: List[Message]
    ) -> Tuple[Message, float]:
        return _select_next_nucleus(available_message, selected_nuclei)


def _select_next_nucleus(
    available_messages: List[Message], selected_nuclei: List[Message]
) -> Tuple[Optional[Message], float]:

    log.debug("Starting a new paragraph")

    available_messages.sort(key=lambda message: message.score, reverse=True)

    if not available_messages:
        return None, 0

    next_nucleus = available_messages[0]
    log.debug(
        "Most interesting thing is {} (int={}), selecting it as a nucleus".format(next_nucleus, next_nucleus.score)
    )

    return next_nucleus, next_nucleus.score


def _new_paragraph_relative_threshold(selected_nuclei: List[Message]) -> float:
    return float("-inf")


def _select_satellites_for_nucleus(nucleus: Message, available_messages: List[Message]) -> List[Message]:
    log.debug("Selecting satellites for {} from among {} options".format(nucleus, len(available_messages)))
    satellites: List[Message] = []
    available_messages = available_messages[:]  # Copy, s.t. we can modify in place

    while True:
        scored_available = [
            (message.score, message)
            for message in available_messages
            if message.score > 0
            and message.main_fact.value_type.split(":")[0] == nucleus.main_fact.value_type.split(":")[0]
        ]
        scored_available.sort(key=lambda pair: pair[0], reverse=True)

        if not scored_available:
            return satellites

        score, selected_satellite = scored_available[0]
        satellites.append(selected_satellite)
        log.debug("Added satellite {} (temp_score={})".format(selected_satellite, score))
        available_messages = [message for message in available_messages if message != selected_satellite]
