from typing import Dict, Set

from core.abn.pareataxonomy.Area import Area
from core.abn.pareataxonomy.PArea import PArea
from core.hierarchy.Hierarchy import Hierarchy
from core.ontology import Concept
from tqdm import tqdm
import time

class AreaTaxonomy:
    def __init__(self, areas: Set[Area], root_area: Area):
        """
        Initialize an area taxonomy with areas and designate the root area
        """
        self.areas = areas
        self.root_area = root_area

        # Build concept to area mapping
        self._concept_areas = {}
        for area in areas:
            for concept in area.get_concepts():
                self._concept_areas[concept] = area

    def get_areas(self) -> Set[Area]:
        return self.areas

    def get_root_area(self) -> Area:
        return self.root_area

    def get_concept_area(self, concept: Concept) -> Area:
        return self._concept_areas.get(concept)

    def get_relationship_types(self) -> Set[str]:
        """Get all relationship types used in this taxonomy"""
        all_rels = set()
        for area in self.areas:
            all_rels.update(area.get_relationships())
        return all_rels


def create_area_taxonomy(hierarchy: Hierarchy[Concept], get_concept_rels) -> AreaTaxonomy:
    """
    Create an area taxonomy from a concept hierarchy with optimized performance.
    """

    start_time = time.time()

    # Cache concept relationships to avoid repeated computation
    print("Caching concept relationships...")
    concept_rels_cache = {concept: frozenset(get_concept_rels(concept))
                          for concept in hierarchy.get_nodes()}

    # Step 1: Identify partial area roots
    print("Identifying partial area roots...")
    parea_roots = set()
    for concept in tqdm(hierarchy.get_nodes()):
        parents = hierarchy.get_parents(concept)
        concept_rels = concept_rels_cache[concept]
        if not parents or not any(concept_rels == concept_rels_cache[p] for p in parents):
            parea_roots.add(concept)

    print(f"Found {len(parea_roots)} partial area roots")

    # Create a map of concepts to their potential PArea root
    print("Building concept to root mapping...")
    concept_to_root = {}
    processed = set()

    # Process roots in parallel using topological order to ensure parents are processed first
    for root in tqdm(hierarchy.get_topological_ordering()):
        if root in parea_roots:
            root_rels = concept_rels_cache[root]
            concept_to_root[root] = root
            stack = [(root, None)]

            while stack:
                concept, parent = stack.pop()
                if concept in processed:
                    continue

                processed.add(concept)
                children = hierarchy.get_children(concept)

                for child in children:
                    if (child not in processed and
                            child not in parea_roots and
                            concept_rels_cache[child] == root_rels):

                        # Quick check if child's other parents have same relationships
                        child_parents = hierarchy.get_parents(child)
                        if not any(p != parent and
                                   p not in processed and
                                   concept_rels_cache[p] == root_rels
                                   for p in child_parents):
                            concept_to_root[child] = root
                            stack.append((child, concept))

    # Step 2: Build PAreas using the concept_to_root mapping
    print("Building partial areas...")
    root_to_parea = {}
    for root in tqdm(parea_roots):
        # Get all concepts belonging to this root
        parea_concepts = {concept for concept, r in concept_to_root.items()
                          if r == root}

        parea_hier = Hierarchy(root)

        # Add edges for concepts in this PArea
        for concept in parea_concepts:
            for parent in hierarchy.get_parents(concept):
                if parent in parea_concepts:
                    parea_hier.add_edge(concept, parent)

        root_to_parea[root] = PArea(parea_hier, concept_rels_cache[root])

    # Step 3: Group PAreas into Areas
    print("Grouping into areas...")
    areas_by_rels = {}
    for parea in tqdm(root_to_parea.values()):
        rel_key = frozenset(parea.get_relationships())
        if rel_key not in areas_by_rels:
            areas_by_rels[rel_key] = set()
        areas_by_rels[rel_key].add(parea)

    areas = {Area(pareas, set(rels))
             for rels, pareas in areas_by_rels.items()}

    # Find root area (one containing hierarchy root)
    root_area = next(area for area in areas
                     if hierarchy.get_root() in area.get_concepts())

    end_time = time.time()
    print(f"Created taxonomy in {end_time - start_time:.2f} seconds")
    print(f"Total areas: {len(areas)}")
    print(f"Total PAreas: {len(root_to_parea)}")

    return AreaTaxonomy(areas, root_area)


# def create_area_taxonomy(hierarchy: Hierarchy[Concept], get_concept_rels) -> AreaTaxonomy:
#     """
#     Create an area taxonomy from a concept hierarchy.
#     """
#     start_time = time.time()
#
#     # Step 1: Identify partial area roots
#     def has_same_rels(c1: Concept, c2: Concept) -> bool:
#         return get_concept_rels(c1) == get_concept_rels(c2)
#
#     parea_roots = set()
#     for concept in tqdm(hierarchy.get_nodes(), desc="Identifying partial area roots"):
#         parents = hierarchy.get_parents(concept)
#         # Check if all parents have different relationship types
#         if not parents or not any(has_same_rels(concept, p) for p in parents):
#             parea_roots.add(concept)
#
#     # Step 2: Build partial areas by following descendants
#     pareas = set()
#     processed_concepts = set()
#
#     for root in tqdm(parea_roots, desc="Building partial areas"):
#         if root in processed_concepts:
#             continue
#
#         root_rels = get_concept_rels(root)
#         parea_hier = Hierarchy(root)
#         stack = [(root, None)]  # (concept, parent) pairs
#
#         while stack:
#             concept, parent = stack.pop()
#             if parent is not None:
#                 parea_hier.add_edge(concept, parent)
#             processed_concepts.add(concept)
#
#             # Check each child
#             for child in hierarchy.get_children(concept):
#                 # Only include child if it has same relationships and isn't a root
#                 if (child not in parea_roots and
#                         child not in processed_concepts and
#                         get_concept_rels(child) == root_rels):
#                     # Additional check: ensure no parent outside has same relationships
#                     parents_outside = [p for p in hierarchy.get_parents(child)
#                                      if p not in parea_hier.get_nodes()]
#                     if not any(get_concept_rels(p) == root_rels for p in parents_outside):
#                         stack.append((child, concept))
#
#         # Only add PArea if it contains more than one concept
#         if len(parea_hier.get_nodes()) > 1:
#             pareas.add(PArea(parea_hier, root_rels))
#
#     # Step 3: Group partial areas into areas
#     areas_by_rels = {}
#     for parea in tqdm(pareas, desc="Grouping partial areas"):
#         rel_key = frozenset(parea.get_relationships())
#         if rel_key not in areas_by_rels:
#             areas_by_rels[rel_key] = set()
#         areas_by_rels[rel_key].add(parea)
#
#     # Create Area objects
#     areas = set()
#     for rels, pareas_in_area in areas_by_rels.items():
#         areas.add(Area(pareas_in_area, rels))
#
#     end_time = time.time()
#     print(f"create_area_taxonomy executed in {end_time - start_time:.2f} seconds")
#
#     return AreaTaxonomy(areas)
