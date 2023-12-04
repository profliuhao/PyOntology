import os
from pathlib import Path


from sno.datasource.SCTReleaseInfo import SCTReleaseInfo
from sno.load.LoadLocalRelease import LoadLocalRelease
from sno.load.RF2ReleaseLoader import RF2ReleaseLoader


def main():
    input_directory = Path("D:/Ontology/SNO")
    print("Loading")
    default_cat = False

    if input_directory.is_dir():
        subfiles = input_directory.iterdir()

        for file in subfiles:
            if file.is_dir():
                print("Find file:", file.absolute())
                # dir_list = LoadLocalRelease.find_release_folders(file)
                dir_list = ['D:\Ontology\SNO\SnomedCT_InternationalRF2_PRODUCTION_20210731T120000Z\Snapshot\Terminology']
                for t in dir_list:
                    print("dir", t)

                release_names = LoadLocalRelease.get_release_file_names(dir_list)
                for t in release_names:
                    print("release", t)

                release_name = release_names[0]
                try:
                    rf2_importer = RF2ReleaseLoader()

                    dir_file = dir_list[0]
                    release = rf2_importer.load_local_snomed_release(
                        dir_file,
                        SCTReleaseInfo(dir_file, release_name),
                    )

                    valid_roots = sorted(release.get_hierarchies_with_attribute_relationships(),
                                         key=lambda x: x.get_name())

                    for root in valid_roots:
                        root_concept = release.get_concept_from_id(root.get_id())
                        print("root_concept.getName() =", root_concept.get_name())

                    concept_id = 49601007
                    opt_concept = release.get_concept_from_id(concept_id)
                    print("opt_concept.getName() =", opt_concept.get_name())


                    concept_id = 404684003
                    opt_concept = release.get_concept_from_id(concept_id)
                    print("opt_concept.getName() =", opt_concept.get_name())

                    concept_id = 301095005
                    opt_concept = release.get_concept_from_id(concept_id)
                    hier = release.get_concept_hierarchy()
                    # anc_hier= hier.get_ancestor_hierarchy([opt_concept])
                    for node in hier.get_ancestors([opt_concept]):
                        print(node.get_name())

                    # for node in hier.get([opt_concept]):
                    #     print(node.get_name())

                    print('show paths')
                    paths = hier.get_all_paths_to(opt_concept)
                    for path in paths:
                        print('->'.join([x.get_name() for x in path]))


                except IOError as e:
                    # TODO: write error...
                    pass


if __name__ == "__main__":
    main()
