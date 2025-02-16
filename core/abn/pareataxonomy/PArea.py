from typing import Set
from core.hierarchy.Hierarchy import Hierarchy
from core.ontology import Concept
from core.abn.pareataxonomy import InheritableProperty


class PArea:
    def __init__(self, concept_hierarchy: Hierarchy[Concept], relationships: Set[InheritableProperty]):
        self.concept_hierarchy = concept_hierarchy
        self.relationships = relationships

    def get_root(self) -> Concept:
        return self.concept_hierarchy.get_root()

    def get_concepts(self) -> Set[Concept]:
        return self.concept_hierarchy.get_nodes()

    def get_relationships(self) -> Set[InheritableProperty]:
        return self.relationships
