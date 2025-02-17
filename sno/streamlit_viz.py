# streamlit_viz.py

import streamlit as st
from pathlib import Path
from core.vis.interactive_vis import create_interactive_visualization
from core.abn.pareataxonomy.AreaTaxonomy import create_area_taxonomy
from core.abn.pareataxonomy.PAreaTaxonomy import create_parea_taxonomy
from sno.datasource.SCTReleaseInfo import SCTReleaseInfo
from sno.load.RF2ReleaseLoader import RF2ReleaseLoader
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="SNOMED CT Taxonomy Visualizer",
    page_icon="🌲",
    layout="wide"
)

# Sidebar configuration
st.sidebar.title("Configuration")

# SNOMED Path Input
snomed_path = st.sidebar.text_input(
    "SNOMED CT Path",
    value="G:/Ontology/SNO/SnomedCT_InternationalRF2_PRODUCTION_20210731T120000Z/Snapshot/Terminology",
    help="Path to SNOMED CT terminology folder"
)

# Predefined concept choices
CONCEPT_CHOICES = {
    "Clinical Finding": 404684003,
    "Diabetes mellitus": 73211009,
    "Disease": 64572001,
    "Procedure": 71388002
}

selected_concept = st.sidebar.selectbox(
    "Select Root Concept",
    options=list(CONCEPT_CHOICES.keys()),
    help="Choose the root concept for visualization"
)

# Visualization type
viz_type = st.sidebar.radio(
    "Visualization Type",
    ["Area Taxonomy", "Partial Area Taxonomy"]
)

# Depth control
max_depth = st.sidebar.slider(
    "Maximum Depth",
    min_value=1,
    max_value=5,
    value=2,
    help="Maximum depth of hierarchy to display"
)


# Helper function to get concept relationships
def get_concept_rels(concept):
    return {rel.get_type().get_name()
            for rel in concept.get_attribute_relationships()
            if rel.get_characteristic_type() == 1}


# Load SNOMED data
@st.cache_resource
def load_snomed_data(path):
    dir_path = path
    release_name = 'SnomedCT_InternationalRF2_PRODUCTION_20210731T120000Z'

    rf2_importer = RF2ReleaseLoader()
    return rf2_importer.load_local_snomed_release(
        dir_path,
        SCTReleaseInfo(dir_path, release_name)
    )


# Create taxonomy
@st.cache_data
def create_taxonomy(_release, concept_id, viz_type):
    root_concept = _release.get_concept_from_id(concept_id)
    hier = _release.get_stated_hierarchy()
    sub_hier = hier.get_subhierarchy_rooted_at(root_concept)

    if viz_type == "Area Taxonomy":
        return create_area_taxonomy(sub_hier, get_concept_rels)
    else:
        return create_parea_taxonomy(sub_hier, get_concept_rels)


# Main app
def main():
    st.title("SNOMED CT Taxonomy Visualizer")

    try:
        # Load SNOMED data
        with st.spinner("Loading SNOMED CT data..."):
            release = load_snomed_data(snomed_path)

        # Get concept ID
        concept_id = CONCEPT_CHOICES[selected_concept]

        # Create taxonomy
        with st.spinner("Creating taxonomy..."):
            taxonomy = create_taxonomy(release, concept_id, viz_type)

        # Display statistics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Total Areas" if viz_type == "Area Taxonomy" else "Total PAreas",
                len(taxonomy.get_areas()) if viz_type == "Area Taxonomy"
                else len(taxonomy.get_parea_hierarchy().get_nodes())
            )

        with col2:
            root = taxonomy.get_root_area() if viz_type == "Area Taxonomy" \
                else taxonomy.get_root_parea()
            st.metric(
                "Root Concepts",
                len(root.get_concepts())
            )

        with col3:
            st.metric(
                "Relationship Types",
                len(taxonomy.get_relationship_types()) if viz_type == "Area Taxonomy"
                else len(root.get_relationships())
            )

        # Create visualization
        with st.spinner("Generating visualization..."):

            fig = create_interactive_visualization(taxonomy, viz_type, max_depth)

            # Update layout for Streamlit
            fig.update_layout(
                height=800,
                width=None,  # Auto-width
                margin=dict(l=20, r=20, t=60, b=20)
            )

            # Display visualization
            st.plotly_chart(fig, use_container_width=True)

        # Relationship details
        if viz_type == "Area Taxonomy":
            st.subheader("Relationship Types")
            rel_types = sorted(taxonomy.get_relationship_types())
            for rel in rel_types:
                st.write(f"- {rel}")

        # Area/PArea details
        if st.checkbox("Show Detailed Statistics"):
            st.subheader("Detailed Statistics")

            if viz_type == "Area Taxonomy":
                areas = taxonomy.get_areas()
                data = []
                for area in sorted(areas, key=lambda a: len(a.get_concepts()), reverse=True):
                    data.append({
                        "Name": area.get_name(),
                        "Concepts": len(area.get_concepts()),
                        "Partial Areas": len(area.get_pareas()),
                        "Relationships": len(area.get_relationships())
                    })
                st.dataframe(data)
            else:
                parea_hier = taxonomy.get_parea_hierarchy()
                data = []
                for parea in parea_hier.get_nodes():
                    data.append({
                        "Name": parea.get_root().get_name(),
                        "Concepts": len(parea.get_concepts()),
                        "Relationships": len(parea.get_relationships()),
                        "Level": len(parea.get_relationships())
                    })
                st.dataframe(data)

    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.write("Please check the SNOMED CT path and try again.")


if __name__ == "__main__":
    main()
