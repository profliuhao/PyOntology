from typing import Set, Generic, TypeVar
from core.hierarchy.Hierarchy import Hierarchy

T = TypeVar('T')

class SimilarityNode(Generic[T]):
    def __init__(self, internal_nodes: Set[T]):
        self.internal_nodes = internal_nodes

    @staticmethod
    def create_internal_hierarchy(nodes: Set[T]) -> 'Hierarchy[Concept]':
        roots = set(node.get_root() for node in nodes)
        hierarchy = Hierarchy(roots)
        for node in nodes:
            hierarchy.add_all_hierarchical_relationships(node.get_hierarchy())
        return hierarchy
