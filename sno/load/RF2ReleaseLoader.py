import os
from typing import List, Dict, Set

from core.hierarchy.Hierarchy import Hierarchy
from sno.concept.AttributeRelationship import AttributeRelationship

from sno.concept.Description import Description
from sno.concept.SCTStatedConcept import SCTStatedConcept
from sno.datasource.SCTReleaseWithStated import SCTReleaseWithStated
from sno.load.LocalLoadStateMonitor import LocalLoadStateMonitor


class RF2ReleaseLoader:
    def __init__(self):
        self.load_monitor = LocalLoadStateMonitor()

    def load_local_snomed_release(self, directory, release_info):
        release_directory = directory
        concepts_file, desc_file, rel_file, stated_rel_file = self.get_rf2_files(release_directory)

        # Load concepts as SCTStatedConcept from the start
        concepts = self.load_concepts(concepts_file)

        self.load_descriptions(desc_file, concepts)

        # Load both regular and stated relationships
        stated_hierarchy, stated_relationships = self.load_stated_relationships(stated_rel_file, concepts)
        hierarchy, relationships = self.load_relationships(rel_file, concepts)

        # Set relationships on concepts
        for concept_id, rels in stated_relationships.items():
            if concept_id in concepts:
                concepts[concept_id].set_stated_relationships(rels)

        for concept_id, rels in relationships.items():
            if concept_id in concepts:
                concepts[concept_id].set_lateral_relationships(rels)

        # Create release with both hierarchies
        release = SCTReleaseWithStated(release_info, hierarchy, set(concepts.values()), hierarchy)
        return release

    def load_stated_relationships(self, relationships_file, concepts):
        root_concept = concepts[138875005]  # SNOMED CT Concept
        hierarchy = Hierarchy([root_concept])
        stated_attribute_relationships = {}

        with open(relationships_file, 'r') as in_file:
            in_file.readline()  # Skip header
            processed_relationships = 0

            for line in in_file:
                parts = line.split("\t")
                active = int(parts[2])
                if active == 0:
                    continue

                rel_type = int(parts[7])
                source_id = int(parts[4])
                target_id = int(parts[5])

                # IS A relationship
                if rel_type == 116680003:
                    if source_id in concepts and target_id in concepts:
                        child = concepts[source_id]
                        parent = concepts[target_id]
                        hierarchy.add_edge(child, parent)
                else:
                    # Attribute relationship
                    if source_id not in stated_attribute_relationships:
                        stated_attribute_relationships[source_id] = set()

                    relationship_group = int(parts[6])
                    # 900000000000010007 is Stated
                    rel_characteristic_type = 1 if int(parts[8]) == 900000000000010007 else 0

                    if rel_type in concepts and target_id in concepts:
                        rel = AttributeRelationship(
                            concepts[rel_type],
                            concepts[target_id],
                            relationship_group,
                            rel_characteristic_type
                        )
                        stated_attribute_relationships[source_id].add(rel)

                processed_relationships += 1

        print(f"Processed {processed_relationships} stated relationships")
        print(f"Found {len(stated_attribute_relationships)} concepts with stated relationships")

        # Initialize empty relationships for concepts without any
        for concept in concepts.values():
            if concept.get_id() not in stated_attribute_relationships:
                stated_attribute_relationships[concept.get_id()] = set()

        return hierarchy, stated_attribute_relationships

    def load_relationships(self, relationships_file, concepts):
        root_concept = concepts[138875005]  # SNOMED CT Concept
        hierarchy = Hierarchy([root_concept])
        attribute_relationships = {}

        with open(relationships_file, 'r') as in_file:
            in_file.readline()  # Skip header
            processed_relationships = 0

            for line in in_file:
                parts = line.split("\t")
                active = int(parts[2])
                if active == 0:
                    continue

                rel_type = int(parts[7])
                source_id = int(parts[4])
                target_id = int(parts[5])

                # IS A relationship
                if rel_type == 116680003:
                    if source_id in concepts and target_id in concepts:
                        child = concepts[source_id]
                        parent = concepts[target_id]
                        hierarchy.add_edge(child, parent)
                else:
                    # Attribute relationship
                    if source_id not in attribute_relationships:
                        attribute_relationships[source_id] = set()

                    relationship_group = int(parts[6])
                    # 900000000000011006 is Inferred
                    rel_characteristic_type = 1 if int(parts[8]) == 900000000000011006 else 0

                    if rel_type in concepts and target_id in concepts:
                        rel = AttributeRelationship(
                            concepts[rel_type],
                            concepts[target_id],
                            relationship_group,
                            rel_characteristic_type
                        )
                        attribute_relationships[source_id].add(rel)

                processed_relationships += 1

        print(f"Processed {processed_relationships} relationships")
        print(f"Found {len(attribute_relationships)} concepts with relationships")

        return hierarchy, attribute_relationships

    def load_concepts(self, concepts_file):
        concepts = {}
        with open(concepts_file, 'r') as in_file:
            in_file.readline()  # Skip header
            processed_concepts = 0

            for line in in_file:
                parts = line.split("\t")
                _id = int(parts[0])
                active = parts[2] == "1"
                # 900000000000074008 is Primitive
                primitive = parts[4] == "900000000000074008"

                if active:  # Only load active concepts
                    concepts[_id] = SCTStatedConcept(_id, primitive, active)
                    processed_concepts += 1

        print(f"Processed {processed_concepts} active concepts")
        return concepts


    # def load_local_snomed_release(self, directory, release_info):
    #     release_directory = directory
    #     concepts_file, desc_file, rel_file, stated_rel_file = self.get_rf2_files(release_directory)
    #
    #
    #     concepts = self.load_concepts(concepts_file)
    #
    #     self.load_descriptions(desc_file, concepts)
    #
    #     hierarchy = self.load_relationships(rel_file, concepts)
    #
    #     stated_hierarchy = self.load_stated_relationships(stated_rel_file, concepts)
    #
    #     release = SCTReleaseWithStated(release_info, hierarchy, set(concepts.values()), stated_hierarchy)
    #
    #
    #     return release
    #
    # def load_stated_relationships(self, relationships_file, concepts):
    #     hierarchy = Hierarchy([concepts[138875005]])
    #
    #     stated_attribute_relationships = {}
    #
    #     with open(relationships_file, 'r') as in_file:
    #         in_file.readline()
    #
    #         processed_relationships = 0
    #
    #         for line in in_file:
    #             parts = line.split("\t")
    #
    #             active = int(parts[2])
    #
    #             if active == 0:
    #                 continue
    #
    #             rel_type = int(parts[7])
    #             source_id = int(parts[4])
    #             target_id = int(parts[5])
    #
    #             if rel_type == 116680003:
    #                 child = concepts[source_id]
    #                 parent = concepts[target_id]
    #
    #                 hierarchy.add_edge(child, parent)
    #             else:
    #                 if source_id not in stated_attribute_relationships:
    #                     stated_attribute_relationships[source_id] = set()
    #
    #                 relationship_group = int(parts[6])
    #
    #                 rel_characteristic_type = 1 if int(parts[8]) == 900000000000010007 else 0
    #
    #                 stated_attribute_relationships[source_id].add(AttributeRelationship(
    #                     concepts[rel_type],
    #                     concepts[target_id],
    #                     relationship_group,
    #                     rel_characteristic_type
    #                 ))
    #
    #             processed_relationships += 1
    #
    #     for concept in concepts.values():
    #         if concept.get_id() in stated_attribute_relationships:
    #             stated_concept = SCTStatedConcept(concept)  # Assuming SCTStatedConcept is used
    #             stated_concept.set_stated_relationships(stated_attribute_relationships[concept.get_id()])
    #         else:
    #             concept.set_stated_relationships(set())
    #
    #     print("PROCESSED STATED RELS:", processed_relationships)
    #
    #     return hierarchy
    #
    # def load_relationships(self, relationships_file, concepts):
    #     hierarchy = Hierarchy([concepts[138875005]])
    #
    #     attribute_rels = {}
    #
    #     with open(relationships_file, 'r') as in_file:
    #         in_file.readline()
    #
    #         processed_relationships = 0
    #
    #         for line in in_file:
    #             parts = line.split("\t")
    #
    #             active = int(parts[2])
    #
    #             if active == 0:
    #                 continue
    #
    #             rel_type = int(parts[7])
    #             source_id = int(parts[4])
    #             target_id = int(parts[5])
    #
    #             if rel_type == 116680003:
    #                 child = concepts[source_id]
    #                 parent = concepts[target_id]
    #
    #                 hierarchy.add_edge(child, parent)
    #             else:
    #                 if source_id not in attribute_rels:
    #                     attribute_rels[source_id] = set()
    #
    #                 relationship_group = int(parts[6])
    #
    #                 rel_characteristic_type = 1 if int(parts[8]) == 900000000000011006 else 0
    #
    #                 attribute_rels[source_id].add(AttributeRelationship(
    #                     concepts[rel_type],
    #                     concepts[target_id],
    #                     relationship_group,
    #                     rel_characteristic_type
    #                 ))
    #
    #             processed_relationships += 1
    #
    #     for concept in concepts.values():
    #         if concept.get_id() in attribute_rels:
    #             concept.set_lateral_relationships(attribute_rels[concept.get_id()])
    #         else:
    #             concept.set_lateral_relationships(set())
    #
    #     print("PROCESSED RELS:", processed_relationships)
    #
    #     return hierarchy
    #
    # def load_concepts(self, concepts_file):
    #     concepts = {}
    #
    #     with open(concepts_file, 'r') as in_file:
    #         in_file.readline()
    #
    #         processed_concepts = 0
    #
    #         for line in in_file:
    #             parts = line.split("\t")
    #             _id = int(parts[0])
    #             active = parts[2] == "1"
    #             primitive = parts[4] == "900000000000074008"
    #             concepts[_id] = SCTStatedConcept(_id, primitive, active)
    #
    #             processed_concepts += 1
    #
    #
    #     print("PROCESSED CONCEPTS:", processed_concepts)
    #
    #     return concepts

    def load_descriptions(self, descriptions_file, concepts):
        descriptions = {}

        with open(descriptions_file, 'r', encoding='utf-8') as in_file:
            in_file.readline()

            processed_descriptions = 0

            for line in in_file:
                parts = line.split("\t")

                active = int(parts[2])

                if active == 0:
                    continue

                concept_id = int(parts[4])
                desc_type = int(parts[6])

                rf1_desc_type = 3 if desc_type == 900000000000003001 else 0

                d = Description(parts[7], rf1_desc_type)

                if concept_id in descriptions:
                    descriptions[concept_id].add(d)
                else:
                    descriptions[concept_id] = {d}

                processed_descriptions += 1
                load_progress = processed_descriptions / 1200000.0

        print("PROCESSED DESCRIPTIONS:", processed_descriptions)

        for concept in concepts.values():
            if concept.get_id() in descriptions:
                concept.set_descriptions(descriptions[concept.get_id()])
            else:
                concept.set_descriptions(set())

    def get_rf2_files(self, release_directory):
        concepts_file, desc_file, rel_file, stated_rel_file = None, None, None, None

        for child in os.listdir(release_directory):
            if "sct2_concept" in child.lower():
                concepts_file = os.path.join(release_directory, child)
            elif "sct2_description" in child.lower():
                desc_file = os.path.join(release_directory, child)
            elif "sct2_relationship" in child.lower():
                rel_file = os.path.join(release_directory, child)
            elif "sct2_statedrelationship" in child.lower():
                stated_rel_file = os.path.join(release_directory, child)

        return concepts_file, desc_file, rel_file, stated_rel_file
