import logging
from typing import Callable, List, Tuple

from numpy.random import Generator

from .core.message_generator import NoMessagesForSelectionException
from .core.models import Message
from .core.pipeline import NLGPipelineComponent, Registry

log = logging.getLogger("root")


class CommentReportMessageGenerator(NLGPipelineComponent):
    def run(self, registry: Registry, random: Generator, language: str, comments: List[str]) -> Tuple[List[Message]]:
        """
        Run this pipeline component.
        """
        message_parsers: List[Callable[[List[str]], List[Message]]] = registry.get("message-parsers")

        messages: List[Message] = []
        generation_succeeded = False
        for message_parser in message_parsers:
            log.debug(f"Trying parser {message_parser}")
            try:
                new_messages = message_parser(comments)
                for message in new_messages:
                    log.debug("Parsed message {}".format(message))
                if new_messages:
                    generation_succeeded = True
                    messages.extend(new_messages)
            except Exception as ex:
                log.error("Message parser crashed: {}".format(ex), exc_info=True)
                raise

        if not generation_succeeded:
            log.error("Failed to parse any Message from input")

        # Filter out messages that share the same underlying fact. Can't be done with set() because of how the
        # __hash__ and __eq__ are (not) defined.
        facts = set()
        uniq_messages = []
        for m in messages:
            if m.main_fact not in facts:
                facts.add(m.main_fact)
                uniq_messages.append(m)
        messages = uniq_messages

        if not messages:
            raise NoMessagesForSelectionException()

        return (messages,)
