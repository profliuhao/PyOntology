from typing import Set, Dict, Optional
from abc import ABC, abstractmethod

from core.abn.pareataxonomy.AreaTaxonomy import AreaTaxonomy, create_area_taxonomy
from core.hierarchy.Hierarchy import Hierarchy
from core.ontology import Concept
from core.abn.pareataxonomy.PArea import PArea
from core.abn.pareataxonomy.Area import Area



class PAreaTaxonomy:
    def __init__(self, area_taxonomy: AreaTaxonomy, parea_hierarchy: Hierarchy[PArea]):
        self.area_taxonomy = area_taxonomy
        self.parea_hierarchy = parea_hierarchy

    def get_area_taxonomy(self) -> AreaTaxonomy:
        return self.area_taxonomy

    def get_parea_hierarchy(self) -> Hierarchy[PArea]:
        return self.parea_hierarchy

    def get_area_for(self, parea: PArea) -> Area:
        return next(area for area in self.area_taxonomy.get_areas()
                    if parea in area.get_pareas())

    def get_pareas(self) -> Set[PArea]:
        return self.parea_hierarchy.get_nodes()

    def get_root_parea(self) -> PArea:
        return self.parea_hierarchy.get_root()


# def create_parea_taxonomy(hierarchy: Hierarchy[Concept], get_concept_rels) -> PAreaTaxonomy:
#     """
#     Create a PArea taxonomy from a concept hierarchy, showing hierarchical relationships between PAreas.
#
#     Args:
#         hierarchy: Concept hierarchy to analyze
#         get_concept_rels: Function that takes a concept and returns its set of relationship names
#
#     Returns:
#         PAreaTaxonomy representing the structure with PArea hierarchy
#     """
#     # First create area taxonomy to get areas and their PAreas
#     area_taxonomy = create_area_taxonomy(hierarchy, get_concept_rels)
#
#     # Collect all PAreas
#     all_pareas = set()
#     for area in area_taxonomy.get_areas():
#         all_pareas.update(area.get_pareas())
#
#     # Find root PArea (one containing hierarchy root)
#     root_parea = next(parea for parea in all_pareas
#                       if hierarchy.get_root() in parea.get_concepts())
#
#     # Create PArea hierarchy
#     parea_hierarchy = Hierarchy(root_parea)
#
#     # For each PArea, find its parent PAreas based on concept relationships
#     for parea in all_pareas:
#         if parea == root_parea:
#             continue
#
#         parea_root = parea.get_root()
#         parent_concepts = hierarchy.get_parents(parea_root)
#
#         # Find parent PAreas
#         for parent_concept in parent_concepts:
#             parent_parea = next(p for p in all_pareas
#                                 if parent_concept in p.get_concepts())
#             parea_hierarchy.add_edge(parea, parent_parea)
#
#     return PAreaTaxonomy(area_taxonomy, parea_hierarchy)


def create_parea_taxonomy(hierarchy: Hierarchy[Concept], get_concept_rels) -> PAreaTaxonomy:
    """
    Create a PArea taxonomy showing hierarchical relationships between PAreas.
    Each child PArea must have more relationships than its parents.
    """
    # First create area taxonomy to get areas and their PAreas
    area_taxonomy = create_area_taxonomy(hierarchy, get_concept_rels)

    # Cache relationship information
    concept_rels_cache = {concept: frozenset(get_concept_rels(concept))
                          for concept in hierarchy.get_nodes()}

    # Collect all PAreas and create map of root concepts to PAreas
    root_to_parea = {}
    for area in area_taxonomy.get_areas():
        for parea in area.get_pareas():
            root_concept = parea.get_root()
            root_to_parea[root_concept] = parea

    # Create PArea hierarchy
    root_parea = root_to_parea[hierarchy.get_root()]
    parea_hierarchy = Hierarchy(root_parea)

    # Process each PArea
    for parea in root_to_parea.values():
        if parea == root_parea:
            continue

        parea_root = parea.get_root()
        parea_rels = concept_rels_cache[parea_root]

        # Find immediate parent PAreas
        parent_pareas = set()
        for parent_concept in hierarchy.get_parents(parea_root):
            # Find the PArea containing this parent concept
            parent_root = next(root for root, p in root_to_parea.items()
                               if parent_concept in p.get_concepts())
            parent_parea = root_to_parea[parent_root]

            # Only add as parent if it has strictly fewer relationships
            parent_rels = concept_rels_cache[parent_root]
            if parent_rels.issubset(parea_rels) and parent_rels != parea_rels:
                parent_pareas.add(parent_parea)

        # Remove transitive relationships
        immediate_parents = set()
        for potential_parent in parent_pareas:
            # Check if this is an immediate parent
            is_immediate = True
            potential_parent_rels = concept_rels_cache[potential_parent.get_root()]

            for other_parent in parent_pareas:
                if other_parent != potential_parent:
                    other_parent_rels = concept_rels_cache[other_parent.get_root()]
                    if (potential_parent_rels.issubset(other_parent_rels) and
                            potential_parent_rels != other_parent_rels):
                        is_immediate = False
                        break

            if is_immediate:
                immediate_parents.add(potential_parent)

        # Add edges to immediate parents
        for parent_parea in immediate_parents:
            parea_hierarchy.add_edge(parea, parent_parea)

    return PAreaTaxonomy(area_taxonomy, parea_hierarchy)
