import json
import logging
from collections import defaultdict
from itertools import chain
from typing import List, Type, Optional

import requests

from ..core.models import Fact, Message
from ..core.realize_slots import SlotRealizerComponent
from .processor_resource import ProcessorResource

log = logging.getLogger("root")


TEMPLATE = """
${prevalence}: most_common_topic:prevalence, second_most_common_topic:prevalence
${example}: most_common_topic:example, second_most_common_topic:example

en: The most common topic present in the comments was {value}.
| value_type = most_common_topic:name

en: The second most common topic present in the comments was {value}.
| value_type = second_most_common_topic:name

en: It was present in {value} % of the comments.
| value_type in {prevalence}

en: The topic is exemplified by this snippet: <blockquote> {value} </blockquote>
| value_type in {example}
"""


class GeneralTopicModelingResource(ProcessorResource):
    @staticmethod
    def _nth_most_common_label(labels: List[List[str]], n: int) -> Optional[str]:
        # Input looks like [["label1", "label2"], ["label1", "label3"]]

        weighted_labels = [list(enumerate(label_list)) for label_list in labels]
        # [[(0, "label1"), (1, "label2")], [(0, "label3"), (1, "label1")]]

        weighted_labels = [[(label, 1 / (idx + 1)) for (idx, label) in label_list] for label_list in weighted_labels]
        # [[("label1", 1), ("label2", 0.5)], [("label3", 1), ("label1", 0.5)]]

        counts = defaultdict(int)
        for (label, weight) in chain(*weighted_labels):
            if label.lower() == "stopwords":
                continue
            counts[label] += weight
        # {"label1": 1.5, "label2": 0.5, "label3": 1}

        ordered_labels = sorted(list(counts.items()), key=lambda x: x[1], reverse=True)
        # [("label1", 1.5), ("label3", 1), ("label2", 0.5)]

        if n < len(ordered_labels):
            return ordered_labels[n][0]
        return None

    def _gen_messages_most_common_topic(
        self, language: str, comments: List[str], labels: List[List[str]]
    ) -> List[Message]:
        label = self._nth_most_common_label(labels, 0)
        if label is None:
            return []

        name_msg = Message(Fact(label, "most_common_topic:name", 6_09))

        prevalence = len([label_list for label_list in labels if label in label_list]) / len(labels) * 100
        prevalence_msg = Message(Fact(prevalence, "most_common_topic:prevalence", 6_08))

        comments_with_labels = [
            comment for (comment, comment_labels) in zip(comments, labels) if label in comment_labels
        ]
        summary = self._query_summarizer(language, comments_with_labels)
        if summary is not None:
            summary_msg = Message(Fact(summary[0], "most_common_topic:example", 6_07))
        else:
            summary_msg = None

        return [name_msg, prevalence_msg, summary_msg]

    def _gen_messages_second_most_common_topic(
        self, language: str, comments: List[str], labels: List[List[str]]
    ) -> List[Message]:
        label = self._nth_most_common_label(labels, 1)
        if label is None:
            return []

        name_msg = Message(Fact(label, "second_most_common_topic:name", 5_09))

        prevalence = len([label_list for label_list in labels if label in label_list]) / len(labels) * 100
        prevalence_msg = Message(Fact(prevalence, "second_most_common_topic:prevalence", 5_08))

        comments_with_labels = [
            comment for (comment, comment_labels) in zip(comments, labels) if label in comment_labels
        ]
        summary = self._query_summarizer(language, comments_with_labels)
        if summary is not None:
            summary_msg = Message(Fact(summary[0], "second_most_common_topic:example", 5_07))
        else:
            summary_msg = None

        return [name_msg, prevalence_msg, summary_msg]

    def templates_string(self) -> str:
        return TEMPLATE

    def generate_messages(self, language: str, comments: List[str]) -> List[Message]:

        # TM data is a list of python string representations, where each python string representation represents a list
        # of strings. So we first turn the python string representations into a format that we can parse as JSON
        # (see replacing single-quote with double-quote), and *then* parse as JSON into a list. This list, however,
        # still does a thing where each label is in the form of "label_top<idx> : <label name>" so we have to remove
        # that first part as extraneous. Optimally, the API would be changed, but I don't have time to arrange for
        # that, so instead we'll stick with this weird stuff.
        topic_data = self._query_topic_model(language, comments)
        if topic_data is None:
            return []
        labels = [
            [label.split(" : ")[1] for label in json.loads(label_list.replace("'", '"'))]
            for label_list in topic_data["suggested_label"]
        ]
        # labels now looks like [["label1", "label2"], ["label1", "label3"]]

        messages: List[Message] = []
        messages.extend(self._gen_messages_most_common_topic(language, comments, labels))
        messages.extend(self._gen_messages_second_most_common_topic(language, comments, labels))
        return [m for m in messages if m is not None]

    def slot_realizer_components(self) -> List[Type[SlotRealizerComponent]]:
        return []

    def _query_topic_model(self, language: str, comments: List[str]):
        log.info(f"comments: {comments}")
        url = self.read_config_language_value("TOPIC_MODEL", language, allow_none=True)
        if url is None:
            return None
        response = requests.post(url, json={"texts": comments})
        log.info(f"{response}, {response.reason}, {response.text}")
        return response.json()

    def _query_summarizer(self, language: str, comments: List[str]) -> Optional[List[str]]:
        url = self.read_config_language_value("SUMMARIZATION", language, allow_none=True)
        if url is None:
            return None
        response = requests.post(url, json={"comments": comments, "count": 1})
        log.info(f"{response}, {response.reason}, {response.text}")
        return response.json()["summary"]
