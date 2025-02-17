# visualization/interactive_taxonomy_visualizer.py

import plotly.graph_objects as go
import networkx as nx
from typing import Dict, Set, List, Optional
import json
from dataclasses import dataclass

from core.vis.hierarchical_visualizer import HierarchicalTaxonomyVisualizer


@dataclass
class NodeState:
    """Track state of nodes in visualization"""
    expanded: bool = False
    visible: bool = True
    parent_id: Optional[str] = None
    level: int = 0


class InteractiveTaxonomyVisualizer:
    """Enhanced interactive visualization for SNOMED CT taxonomies"""

    def __init__(self):
        self.node_states = {}  # Track expansion state of nodes
        self.G = nx.DiGraph()  # Main graph
        self.pos = {}  # Node positions
        self.fig = None  # Plotly figure
        self.taxonomy = None  # Current taxonomy
        self.expanded_nodes = set()  # Track which nodes are expanded

    def create_area_visualization(self, taxonomy, initial_depth: int = 1):
        """
        Create interactive Area taxonomy visualization

        Args:
            taxonomy: The Area taxonomy object
            initial_depth: How many levels to show initially
        """
        self.taxonomy = taxonomy
        self.G = nx.DiGraph()

        # Initialize with root area
        root_area = taxonomy.get_root_area()
        self._add_area_node(root_area, level=0)

        # Add initial visible nodes up to initial_depth
        self._expand_area_node(root_area, max_depth=initial_depth)

        # Calculate initial layout
        self.pos = nx.spring_layout(self.G, k=2, iterations=50)

        # Create initial figure
        self._create_figure()
        self._add_buttons()

        return self.fig

    def _add_area_node(self, area, level: int, parent=None):
        """Add an area node to the graph with metadata"""
        area_name = area.get_name()
        if area_name not in self.G:
            self.G.add_node(area_name,
                            num_concepts=len(area.get_concepts()),
                            num_pareas=len(area.get_pareas()),
                            relationships=list(area.get_relationships()),
                            concepts=[c.get_name() for c in area.get_concepts()],
                            level=level)

            self.node_states[area_name] = NodeState(
                expanded=False,
                visible=level <= 1,
                parent_id=parent,
                level=level
            )

    def _expand_area_node(self, area, max_depth: int):
        """Expand an area node to show its children"""
        if max_depth <= 0:
            return

        area_name = area.get_name()
        area_rels = area.get_relationships()

        # Find child areas (those with superset of relationships)
        for child_area in self.taxonomy.get_areas():
            if (child_area != area and
                    child_area.get_relationships().issuperset(area_rels)):
                # Add child node
                child_name = child_area.get_name()
                self._add_area_node(child_area,
                                    level=self.node_states[area_name].level + 1,
                                    parent=area_name)

                # Add edge
                self.G.add_edge(area_name, child_name)

                # Recursively expand child
                self._expand_area_node(child_area, max_depth - 1)

        self.node_states[area_name].expanded = True

    def _create_figure(self):
        """Create the Plotly figure with current graph state"""
        # Create edge traces for visible edges
        edge_traces = []

        for edge in self.G.edges():
            if (self.node_states[edge[0]].visible and
                    self.node_states[edge[1]].visible):
                x0, y0 = self.pos[edge[0]]
                x1, y1 = self.pos[edge[1]]

                edge_trace = go.Scatter(
                    x=[x0, x1, None],
                    y=[y0, y1, None],
                    line=dict(width=0.5, color='#888'),
                    hoverinfo='none',
                    mode='lines',
                    showlegend=False
                )
                edge_traces.append(edge_trace)

        # Create node trace
        visible_nodes = [n for n in self.G.nodes()
                         if self.node_states[n].visible]

        node_x = []
        node_y = []
        node_text = []
        node_size = []
        node_colors = []

        for node in visible_nodes:
            x, y = self.pos[node]
            node_x.append(x)
            node_y.append(y)

            # Create hover text
            hover_text = (
                f"Area: {node}<br>"
                f"Concepts: {self.G.nodes[node]['num_concepts']}<br>"
                f"Partial Areas: {self.G.nodes[node]['num_pareas']}<br>"
                f"Relationships: {', '.join(self.G.nodes[node]['relationships'])}<br>"
                f"Level: {self.G.nodes[node]['level']}"
            )

            node_text.append(hover_text)
            node_size.append(20 + self.G.nodes[node]['num_concepts'] / 100)
            node_colors.append(self.G.nodes[node]['level'])

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=[n.split()[0] for n in visible_nodes],
            textposition="top center",
            hovertext=node_text,
            marker=dict(
                showscale=True,
                size=node_size,
                colorscale='Viridis',
                reversescale=True,
                color=node_colors,
                colorbar=dict(
                    title='Hierarchy Level',
                    thickness=15,
                    xanchor='left',
                    titleside='right'
                ),
                line_width=2
            ),
            customdata=visible_nodes  # Store full node names for click events
        )

        # Create figure
        self.fig = go.Figure(
            data=[*edge_traces, node_trace],
            layout=self._create_layout()
        )

        # Add click event handler
        self.fig.update_layout(clickmode='event')

        # Add callback for node clicks
        self.fig.update_traces(
            node_trace,
            customdata=visible_nodes,
            selector=dict(type='scatter'),
            overwrite=True
        )

    def _create_layout(self):
        """Create the figure layout"""
        return go.Layout(
            title='Interactive SNOMED CT Area Taxonomy',
            titlefont_size=16,
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=[],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            width=1200,
            height=800,
            uirevision=True  # Preserve state during updates
        )

    def _add_buttons(self):
        """Add control buttons to the visualization"""
        self.fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    direction="right",
                    x=0.1,
                    y=1.1,
                    showactive=True,
                    buttons=[
                        dict(
                            label="Expand All",
                            method="update",
                            args=[{"visible": [True]},
                                  {"title": "Expanded View"}],
                            args2=[{"visible": [False]},
                                   {"title": "Collapsed View"}]
                        ),
                        dict(
                            label="Reset",
                            method="update",
                            args=[{"visible": [True]},
                                  {"title": "Reset View"}]
                        ),
                        dict(
                            label="Center",
                            method="relayout",
                            args=[{"xaxis.range": None,
                                   "yaxis.range": None}]
                        )
                    ]
                )
            ]
        )


# Function to handle node clicks in JavaScript
# NODE_CLICK_HANDLER = """
# function(data) {
#     var pts = data.points[0];
#     var nodeName = pts.customdata;
#
#     // Send node click event
#     console.log('Clicked node:', nodeName);
#
#     // Custom handling can be added here
#     // For example, show/hide child nodes
#
#     return false;  // Prevent default handling
# }
# """

    def create_parea_visualization(self, parea_taxonomy, initial_depth: int = 1):
        """
        Create interactive Partial Area taxonomy visualization

        Args:
            parea_taxonomy: The PArea taxonomy object
            initial_depth: How many levels to show initially
        """
        self.taxonomy = parea_taxonomy
        self.G = nx.DiGraph()

        # Initialize with root PArea
        root_parea = parea_taxonomy.get_root_parea()
        self._add_parea_node(root_parea, level=0)

        # Add initial visible nodes up to initial_depth
        self._expand_parea_node(root_parea, max_depth=initial_depth)

        # Calculate initial layout
        self.pos = nx.spring_layout(self.G, k=2, iterations=50)

        # Create initial figure
        self._create_parea_figure()
        self._add_buttons()

        return self.fig

    def _add_parea_node(self, parea, level: int, parent=None):
        """Add a PArea node to the graph with metadata"""
        parea_name = parea.get_root().get_name()
        if parea_name not in self.G:
            self.G.add_node(parea_name,
                            num_concepts=len(parea.get_concepts()),
                            relationships=list(parea.get_relationships()),
                            concepts=[c.get_name() for c in parea.get_concepts()],
                            level=level)

            self.node_states[parea_name] = NodeState(
                expanded=False,
                visible=level <= 1,
                parent_id=parent,
                level=level
            )

    def _expand_parea_node(self, parea, max_depth: int):
        """Expand a PArea node to show its children"""
        if max_depth <= 0:
            return

        parea_name = parea.get_root().get_name()
        parea_hier = self.taxonomy.get_parea_hierarchy()

        # Add children PAreas
        for child_parea in parea_hier.get_children(parea):
            child_name = child_parea.get_root().get_name()

            # Add child node
            self._add_parea_node(child_parea,
                                 level=self.node_states[parea_name].level + 1,
                                 parent=parea_name)

            # Add edge
            self.G.add_edge(parea_name, child_name)

            # Recursively expand child
            self._expand_parea_node(child_parea, max_depth - 1)

        self.node_states[parea_name].expanded = True

    def _create_parea_figure(self):
        """Create the Plotly figure for PArea visualization"""
        # Create edge traces for visible edges
        edge_traces = []

        for edge in self.G.edges():
            if (self.node_states[edge[0]].visible and
                    self.node_states[edge[1]].visible):
                x0, y0 = self.pos[edge[0]]
                x1, y1 = self.pos[edge[1]]

                edge_trace = go.Scatter(
                    x=[x0, x1, None],
                    y=[y0, y1, None],
                    line=dict(width=0.5, color='#888'),
                    hoverinfo='none',
                    mode='lines',
                    showlegend=False
                )
                edge_traces.append(edge_trace)

        # Create node trace
        visible_nodes = [n for n in self.G.nodes()
                         if self.node_states[n].visible]

        node_x = []
        node_y = []
        node_text = []
        node_size = []
        node_colors = []

        for node in visible_nodes:
            x, y = self.pos[node]
            node_x.append(x)
            node_y.append(y)

            # Create hover text with PArea-specific information
            hover_text = (
                    f"PArea: {node}<br>"
                    f"Concepts: {self.G.nodes[node]['num_concepts']}<br>"
                    f"Relationships: {', '.join(self.G.nodes[node]['relationships'])}<br>"
                    f"Level: {self.G.nodes[node]['level']}<br>"
                    f"Sample Concepts:<br>- " +
                    "<br>- ".join(self.G.nodes[node]['concepts'][:3])  # Show first 3 concepts
            )

            node_text.append(hover_text)
            # Size based on number of concepts
            node_size.append(20 + self.G.nodes[node]['num_concepts'] / 100)
            # Color based on number of relationships
            node_colors.append(len(self.G.nodes[node]['relationships']))

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=[n.split()[0] for n in visible_nodes],  # Show first word of node name
            textposition="top center",
            hovertext=node_text,
            marker=dict(
                showscale=True,
                size=node_size,
                colorscale='Viridis',
                reversescale=True,
                color=node_colors,
                colorbar=dict(
                    title='Number of Relationships',
                    thickness=15,
                    xanchor='left',
                    titleside='right'
                ),
                line_width=2
            ),
            customdata=visible_nodes  # Store full node names for click events
        )

        # Create figure
        self.fig = go.Figure(
            data=[*edge_traces, node_trace],
            layout=self._create_parea_layout()
        )

    def _create_parea_layout(self):
        """Create the figure layout for PArea visualization"""
        return go.Layout(
            title='Interactive SNOMED CT Partial Area Taxonomy',
            titlefont_size=16,
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=[
                dict(
                    text="Node size: Number of concepts<br>"
                         "Node color: Number of relationships",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=1.1, y=0.9,
                    align='left'
                )
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            width=1200,
            height=800,
            uirevision=True  # Preserve state during updates
        )

def create_interactive_visualization(taxonomy, viz_type='Area', max_depth=4):
    """
    Create and display interactive visualization

    Args:
        taxonomy: The taxonomy object to visualize
    """
    # viz = InteractiveTaxonomyVisualizer()
    viz = HierarchicalTaxonomyVisualizer()

    if viz_type == "Area Taxonomy":
        fig = viz.create_area_visualization(taxonomy, initial_depth=max_depth)
    else:  # PArea Taxonomy
        fig = viz.create_parea_visualization(taxonomy, initial_depth=max_depth)

    # fig = viz.create_area_visualization(taxonomy, initial_depth=2)

    # Add JavaScript event handling
    fig.update_layout(
        clickmode='event',
        annotations=[
            dict(
                text='Click nodes to expand/collapse',
                showarrow=False,
                x=0,
                y=1.1,
                xref='paper',
                yref='paper'
            )
        ]
    )

    return fig


# Example usage:
# """
# # Create visualization
# taxonomy = create_area_taxonomy(sub_hier, get_concept_rels)
# fig = create_interactive_visualization(taxonomy)
#
# # Save as interactive HTML
# fig.write_html('interactive_taxonomy.html',
#                include_plotlyjs=True,
#                full_html=True)
# """


# Example usage:
# """
# # Create visualization for PArea taxonomy
# parea_taxonomy = create_parea_taxonomy(sub_hier, get_concept_rels)
# viz = InteractiveTaxonomyVisualizer()
# fig = viz.create_parea_visualization(parea_taxonomy, initial_depth=2)
# fig.show()
# """
