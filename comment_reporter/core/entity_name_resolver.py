import logging
from abc import abstractmethod
from collections import defaultdict
from typing import DefaultDict, Set, Tuple

from numpy.random import Generator

from .models import DocumentPlanNode, Slot
from .pipeline import NLGPipelineComponent
from .registry import Registry

log = logging.getLogger("root")


class EntityNameResolver(NLGPipelineComponent):
    """
    A NLGPipelineComponent that transforms abstracted entity identifers to names.

    Entity name variants are supplied as the 'ner_table' component in the registry.

    When an entity is first encountered, "full_name" is used. On subsequent uses,
    either "short_name" or "pronoun" is used depending on whether the previously
    encountered entity is the same entity as the one being processed.
    """

    # We want certain entity_types to be "possible confusable" for each other. For example
    # it is possible for a reader to get confused with a pronoun like "they" if the previous
    # sentence discusses both a party and a candidate. At the same time, there are cases where
    # such confusion is not in pratice possible, for example when we refer to "they" in a sentence
    # that has only discussed a single party and some location.
    #
    # Thus, we define a data structure where
    # these "confusion-groups" each map to a key. This allows us to in turn key the previous_entities
    # my by confusion-group, rather than by entity_type.
    #
    # This solution is likely going to turn out to be language-specific. If so, some abstraction is
    # needed or the confusion-groups must be keyed by language as well.
    #
    # In this implementation, it is enough to define the multi-entity_type confusion groups, as we
    # can simply use the default parameter in dict.get() to return the key for other cases-

    def run(
        self, registry: Registry, random: Generator, language: str, document_plan: DocumentPlanNode
    ) -> Tuple[DocumentPlanNode]:
        """
        Run this pipeline component.
        """
        log.info("Running NER")

        if language.endswith("-head"):
            language = language[:-5]
            log.debug("Language had suffix '-head', removing. Result: {}".format(language))

        previous_entities = defaultdict(lambda: None)
        self._recurse(registry, random, language, document_plan, previous_entities, set())

        if log.isEnabledFor(logging.DEBUG):
            document_plan.print_tree()

        return (document_plan,)

    def _recurse(
        self,
        registry: Registry,
        random: Generator,
        language: str,
        this: DocumentPlanNode,
        previous_entities: DefaultDict[str, None],
        encountered: Set[str],
    ) -> Tuple[Set[str], DefaultDict[str, None]]:
        """
        Traverses the DocumentPlan tree recursively in-order and modifies named
        entity to_value functions to return the chosen form of that NE's name.
        """
        if isinstance(this, Slot):
            if not self.is_entity(this.value):
                log.debug("Visited leaf non-NE leaf node {}".format(this.value))
                return encountered, previous_entities

            log.debug("Visiting NE leaf {}".format(this.value))
            entity_type, entity = self.parse_entity(this.value)

            if previous_entities[entity_type] == entity:
                log.debug("Same as previous entity")
                this.attributes["name_type"] = "pronoun"

            elif entity in encountered:
                log.debug("Different entity than previous, but has been previously encountered")
                this.attributes["name_type"] = "short"

            else:
                log.debug("First time encountering this entity")
                this.attributes["name_type"] = "full"
                encountered.add(entity)
                log.debug("Added entity to encountered, all encountered: {}".format(encountered))

            self.resolve_surface_form(registry, random, language, this, entity, entity_type)
            log.debug("Resolved entity name")

            this.attributes["entity_type"] = entity_type
            previous_entities[entity_type] = entity

            return encountered, previous_entities
        elif isinstance(this, DocumentPlanNode):
            log.debug("Visiting non-leaf '{}'".format(this))
            for child in this.children:
                encountered, previous_entities = self._recurse(
                    registry, random, language, child, previous_entities, encountered
                )
            return encountered, previous_entities
        return encountered, previous_entities

    @abstractmethod
    def is_entity(self, maybe_entity: str) -> bool:
        raise NotImplementedError("Not implemented")

    @abstractmethod
    def parse_entity(self, entity: str) -> Tuple[str, str]:
        raise NotImplementedError("Not implemented")

    @abstractmethod
    def resolve_surface_form(
        self, registry: Registry, random: Generator, language: str, slot: Slot, entity: str, entity_type: str
    ) -> None:
        raise NotImplementedError("Not implemented")
