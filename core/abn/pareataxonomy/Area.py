from typing import Set
from core.abn.pareataxonomy import PArea
from core.abn.pareataxonomy import InheritableProperty

from core.ontology.Concept import Concept


class Area:
    def __init__(self, pareas: Set[PArea], relationships: Set[InheritableProperty]):
        self.pareas = pareas
        self.relationships = relationships
        self._concepts: Set[Concept] = set()

        for parea in pareas:
            self._concepts.update(parea.get_concepts())

    def get_relationships(self) -> Set[InheritableProperty]:
        return self.relationships

    def get_pareas(self) -> Set[PArea]:
        return self.pareas

    def get_concepts(self) -> Set[Concept]:
        return self._concepts

    def get_name(self, separator: str = ", ") -> str:
        if not self.relationships:
            return "∅"
        return separator.join(sorted(rel for rel in self.relationships))
