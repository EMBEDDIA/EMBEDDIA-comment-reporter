import logging
from typing import List, Tuple

from numpy.random import Generator

from .core.models import Message
from .core.pipeline import NLGPipelineComponent, Registry

log = logging.getLogger("root")


class CommentReportImportanceSelector(NLGPipelineComponent):
    def run(
        self, registry: Registry, random: Generator, language: str, messages: List[Message]
    ) -> Tuple[List[Message]]:
        """
        Runs this pipeline component.
        """
        for msg in messages:
            msg.score = msg.main_fact.outlierness
        sorted_scored_messages = sorted(messages, key=lambda x: float(x.score), reverse=True)
        return (sorted_scored_messages,)
