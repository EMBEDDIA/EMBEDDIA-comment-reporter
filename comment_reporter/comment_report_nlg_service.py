import logging
import random
from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Tuple

from .resources.general_topic_modeling_resource import GeneralTopicModelingResource
from .resources.sentiment_stats_resource import SentimentStatsResource
from .resources.general_summary_resource import GeneralSummaryResource
from .resources.hate_speech_stats_resource import HateSpeechResource
from .resources.generic_stats_resource import GenericStatsResource
from .constants import CONJUNCTIONS, get_error_message
from .core.aggregator import Aggregator
from .core.document_planner import NoInterestingMessagesException
from .core.models import Template
from .core.morphological_realizer import MorphologicalRealizer
from .core.pipeline import NLGPipeline, NLGPipelineComponent
from .core.realize_slots import SlotRealizer
from .core.registry import Registry
from .core.surface_realizer import BodyHTMLSurfaceRealizer, HeadlineHTMLSurfaceRealizer
from .core.template_reader import read_templates
from .core.template_selector import TemplateSelector
from .comment_report_document_planner import CommentReportBodyDocumentPlanner, CommentReportHeadlineDocumentPlanner
from .comment_report_importance_allocator import CommentReportImportanceSelector
from .comment_report_message_generator import CommentReportMessageGenerator, NoMessagesForSelectionException
from .english_uralicNLP_morphological_realizer import EnglishUralicNLPMorphologicalRealizer
from .finnish_uralicNLP_morphological_realizer import FinnishUralicNLPMorphologicalRealizer
from .resources.processor_resource import ProcessorResource

log = logging.getLogger("root")


class CommentReportNlgService(object):

    processor_resources: List[ProcessorResource] = []

    # These are (re)initialized every time run_pipeline is called
    body_pipeline = None
    headline_pipeline = None

    def __init__(self, random_seed: int = None) -> None:
        """
        :param random_seed: seed for random number generation, for repeatability
        """

        # New registry and result importer
        self.registry = Registry()

        # Per-processor resources
        self.processor_resources = [
            GenericStatsResource(),
            HateSpeechResource(),
            GeneralSummaryResource(),
            SentimentStatsResource(),
            GeneralTopicModelingResource(),
        ]

        # Templates
        self.registry.register("templates", self._load_templates())

        # Misc language data
        self.registry.register("CONJUNCTIONS", CONJUNCTIONS)

        # PRNG seed
        self._set_seed(seed_val=random_seed)

        # Message Parsers
        self.registry.register("message-parsers", [])
        for processor_resource in self.processor_resources:
            self.registry.get("message-parsers").append(processor_resource.generate_messages)

        # Slot Realizers Components
        self.registry.register("slot-realizers", [])
        for processor_resource in self.processor_resources:
            components = [component(self.registry) for component in processor_resource.slot_realizer_components()]
            self.registry.get("slot-realizers").extend(components)

    def _load_templates(self) -> Dict[str, List[Template]]:
        log.info("Loading templates")
        templates: Dict[str, List[Template]] = defaultdict(list)
        for resource in self.processor_resources:
            for language, new_templates in read_templates(resource.templates_string())[0].items():
                templates[language].extend(new_templates)
        return templates

    @staticmethod
    def _get_components(type: str) -> Iterable[NLGPipelineComponent]:
        yield CommentReportMessageGenerator()
        yield CommentReportImportanceSelector()

        if type == "headline":
            yield CommentReportHeadlineDocumentPlanner()
        else:
            yield CommentReportBodyDocumentPlanner()

        yield TemplateSelector()
        yield Aggregator()
        yield SlotRealizer()

        yield MorphologicalRealizer(
            {"fi": FinnishUralicNLPMorphologicalRealizer(), "en": EnglishUralicNLPMorphologicalRealizer()}
        )

        if type == "headline":
            yield HeadlineHTMLSurfaceRealizer()
        else:
            yield BodyHTMLSurfaceRealizer()

    def run_pipeline(
        self, output_language: str, comments: List[str], comment_language: Optional[str]
    ) -> Tuple[str, List[str]]:
        log.info("Configuring Body NLG Pipeline")
        self.body_pipeline = NLGPipeline(self.registry, *self._get_components("body"))
        self.headline_pipeline = NLGPipeline(self.registry, *self._get_components("headline"))

        errors: List[str] = []

        log.info("Running Body NLG pipeline: language={}".format(output_language))
        try:
            body = self.body_pipeline.run((comments,), output_language, prng_seed=self.registry.get("seed"))
            log.info("Body pipeline complete")
        except NoMessagesForSelectionException as ex:
            log.error("%s", ex)
            body = get_error_message(output_language, "no-messages-for-selection")
            errors.append("NoMessagesForSelectionException")
        except NoInterestingMessagesException as ex:
            log.info("%s", ex)
            body = get_error_message(output_language, "no-interesting-messages-for-selection")
            errors.append("NoInterestingMessagesException")
        except Exception as ex:
            log.exception("%s", ex)
            body = get_error_message(output_language, "general-error")
            errors.append("{}: {}".format(ex.__class__.__name__, str(ex)))

        return body, errors

    def _set_seed(self, seed_val: Optional[int] = None) -> None:
        log.info("Selecting seed for NLG pipeline")
        if not seed_val:
            seed_val = random.randint(1, 10000000)
            log.info("No preset seed, using random seed {}".format(seed_val))
        else:
            log.info("Using preset seed {}".format(seed_val))
        self.registry.register("seed", seed_val)

    def get_languages(self) -> List[str]:
        return list(self.registry.get("templates").keys())
