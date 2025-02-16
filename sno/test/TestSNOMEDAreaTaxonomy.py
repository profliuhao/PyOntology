import unittest
from pathlib import Path
from typing import Set

from core.abn.pareataxonomy.PAreaTaxonomy import create_parea_taxonomy
from sno.datasource.SCTReleaseInfo import SCTReleaseInfo
from sno.load.LoadLocalRelease import LoadLocalRelease
from sno.load.RF2ReleaseLoader import RF2ReleaseLoader
from core.abn.pareataxonomy.AreaTaxonomy import create_area_taxonomy


class TestSNOMEDAreaTaxonomy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize SNOMED CT data
        input_directory = Path("G:/Ontology/SNO")
        if not input_directory.is_dir():
            raise unittest.SkipTest("SNOMED CT data directory not found")

        # Find and load SNOMED release
        for file in input_directory.iterdir():
            if file.is_dir():
                dir_list = [
                    'G:/Ontology/SNO/SnomedCT_InternationalRF2_PRODUCTION_20210731T120000Z/Snapshot/Terminology']
                release_names = 'SnomedCT_InternationalRF2_PRODUCTION_20210731T120000Z'

                rf2_importer = RF2ReleaseLoader()
                cls.release = rf2_importer.load_local_snomed_release(
                    dir_list[0],
                    SCTReleaseInfo(dir_list[0], release_names)
                )
                break
        else:
            raise unittest.SkipTest("No SNOMED CT release found")

    def test_clinical_finding_taxonomy(self):
        """Test creating taxonomy from Clinical Finding hierarchy"""
        # Get Clinical Finding concept and hierarchy
        concept_id = 404684003  # Clinical Finding
        root_concept = self.release.get_concept_from_id(concept_id)
        hier = self.release.get_stated_hierarchy()
        sub_hier = hier.get_subhierarchy_rooted_at(root_concept)

        print(f"\nAnalyzing Clinical Finding hierarchy...")
        print(f"Root concept: {root_concept.get_name()} ({root_concept.get_id()})")
        print(f"Total concepts: {len(sub_hier.get_nodes())}")

        # Function to get relationships for a concept
        def get_concept_rels(concept) -> Set[str]:
            return {rel.get_type().get_name()
                    for rel in concept.get_attribute_relationships()
                    if rel.get_characteristic_type() == 1}  # Only defining relationships

        # Create taxonomy
        taxonomy = create_area_taxonomy(sub_hier, get_concept_rels)

        # Analyze results
        areas = taxonomy.get_areas()
        print("\nTaxonomy Statistics:")
        print(f"Number of Areas: {len(areas)}")

        total_pareas = sum(len(area.get_pareas()) for area in areas)
        print(f"Total Partial Areas: {total_pareas}")

        total_concepts = sum(len(area.get_concepts()) for area in areas)
        print(f"Total Concepts: {total_concepts}")

        # Verify structure
        self.assertIsNotNone(taxonomy.get_root_area())
        self.assertEqual(total_concepts, len(sub_hier.get_nodes()))

        # Analyze relationship types
        rel_types = taxonomy.get_relationship_types()
        print(f"\nRelationship types used ({len(rel_types)}):")
        for rel in sorted(rel_types):
            print(f"- {rel}")

        # Analyze largest areas
        print("\nLargest Areas:")
        for area in sorted(areas, key=lambda a: len(a.get_concepts()), reverse=True)[:5]:
            print(f"\nArea: {area.get_name()}")
            print(f"Relationships: {len(area.get_relationships())}")
            print(f"Partial Areas: {len(area.get_pareas())}")
            print(f"Total Concepts: {len(area.get_concepts())}")

            # Sample some concepts from each partial area
            print("Sample concepts by partial area:")
            for parea in list(area.get_pareas())[:2]:
                root = parea.get_root()
                print(f"\nPartial Area root: {root.get_name()}")
                sample_concepts = list(parea.get_concepts())[:3]
                for concept in sample_concepts:
                    print(f"- {concept.get_name()}")

    def test_procedure_taxonomy(self):
        """Test creating taxonomy from Procedure hierarchy"""
        concept_id = 71388002  # Procedure
        root_concept = self.release.get_concept_from_id(concept_id)
        hier = self.release.get_stated_hierarchy()
        sub_hier = hier.get_subhierarchy_rooted_at(root_concept)

        def get_concept_rels(concept):
            return {rel.get_type().get_name()
                    for rel in concept.get_attribute_relationships()
                    if rel.get_characteristic_type() == 1}

        taxonomy = create_area_taxonomy(sub_hier, get_concept_rels)

        areas = taxonomy.get_areas()
        print(f"\nTaxonomy Statistics for Procedure:")
        print(f"Number of Areas: {len(areas)}")
        print(f"Total Partial Areas: {sum(len(area.get_pareas()) for area in areas)}")
        print(f"Total Concepts: {sum(len(area.get_concepts()) for area in areas)}")

        # Verify some structural properties
        self.assertTrue(len(areas) > 0)
        self.assertIsNotNone(taxonomy.get_root_area())
        self.assertTrue(root_concept in taxonomy.get_root_area().get_concepts())

    def test_parea_hierarchy(self):
        """Test the hierarchical relationships between PAreas"""
        # Get Diabetes hierarchy
        diabetes_id = 73211009  # Diabetes mellitus
        diabetes = self.release.get_concept_from_id(diabetes_id)
        hier = self.release.get_stated_hierarchy()
        sub_hier = hier.get_subhierarchy_rooted_at(diabetes)

        def get_concept_rels(concept):
            return {rel.get_type().get_name()
                    for rel in concept.get_attribute_relationships()
                    if rel.get_characteristic_type() == 1}

        # Create both taxonomies
        parea_taxonomy = create_parea_taxonomy(sub_hier, get_concept_rels)

        print(f"\nAnalyzing PArea Taxonomy for Diabetes hierarchy...")
        print(f"Root concept: {diabetes.get_name()}")

        # Get root PArea and its details
        root_parea = parea_taxonomy.get_root_parea()
        root_area = parea_taxonomy.get_area_for(root_parea)

        print(f"\nRoot PArea:")
        print(f"Relationships: {root_parea.get_relationships()}")
        print(f"Concepts: {len(root_parea.get_concepts())}")
        print(f"In Area: {root_area.get_name()}")

        # Analyze PArea hierarchy
        parea_hier = parea_taxonomy.get_parea_hierarchy()
        print(f"\nPArea Hierarchy Statistics:")
        print(f"Total PAreas: {len(parea_hier.get_nodes())}")
        print(f"Leaf PAreas: {len(parea_hier.get_leaves())}")

        # Sample some parent-child PArea relationships
        print("\nSample PArea relationships:")
        for parea in list(parea_hier.get_nodes())[:5]:
            print(f"\nPArea root: {parea.get_root().get_name()}")
            print(f"Relationships: {parea.get_relationships()}")
            print(f"Concepts: {len(parea.get_concepts())}")

            parent_pareas = parea_hier.get_parents(parea)
            if parent_pareas:
                print("Parent PAreas:")
                for parent_parea in parent_pareas:
                    print(f"- Root: {parent_parea.get_root().get_name()}")
                    print(f"  Relationships: {parent_parea.get_relationships()}")

            child_pareas = parea_hier.get_children(parea)
            if child_pareas:
                print("Child PAreas:")
                for child_parea in child_pareas:
                    print(f"- Root: {child_parea.get_root().get_name()}")
                    print(f"  Relationships: {child_parea.get_relationships()}")

        # Verify some structural properties
        self.assertEqual(parea_taxonomy.get_root_parea(), root_parea)
        self.assertTrue(len(parea_hier.get_nodes()) > 0)

        # Verify each PArea's children have more relationships than their parents
        for parea in parea_hier.get_nodes():
            for child_parea in parea_hier.get_children(parea):
                child_rel_set = set(child_parea.get_relationships())
                parent_rel_set = set(parea.get_relationships())
                print('child: {}\n=>parent: {}'.format(child_rel_set, parent_rel_set))
                self.assertTrue(
                    child_rel_set.issuperset(parent_rel_set),
                    f"Child PArea {child_parea.get_root().get_name()} should have more relationships than parent")
                # self.assertTrue(
                #     child_parea.get_relationships().issuperset(parea.get_relationships()),
                #     f"Child PArea {child_parea.get_root().get_name()} should have all parent relationships")

if __name__ == '__main__':
    unittest.main(verbosity=2)

