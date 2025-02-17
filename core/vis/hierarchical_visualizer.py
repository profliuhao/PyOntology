# visualization/hierarchical_visualizer.py

import plotly.graph_objects as go
import networkx as nx
from typing import Dict, Set, List, Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class NodeState:
    expanded: bool = False
    visible: bool = True
    parent_id: Optional[str] = None
    level: int = 0


class HierarchicalTaxonomyVisualizer:
    def __init__(self):
        self.node_states = {}
        self.G = nx.DiGraph()
        self.pos = {}
        self.fig = None
        self.taxonomy = None
        self.expanded_nodes = set()

    def _hierarchical_layout(self, G, root_node, width=1.0, height=1.0):
        """
        Create a hierarchical layout for the graph

        Args:
            G: NetworkX graph
            root_node: Root node of the hierarchy
            width: Width of the layout
            height: Height of the layout

        Returns:
            Dict of node positions {node: (x, y)}
        """
        pos = {}
        level_nodes = {}

        # Get nodes by level using BFS
        level = 0
        current_level = [root_node]
        visited = {root_node}

        while current_level:
            level_nodes[level] = current_level
            next_level = []
            for node in current_level:
                # Get children that are visible
                children = [child for child in G.successors(node)
                            if self.node_states[child].visible]
                for child in children:
                    if child not in visited:
                        next_level.append(child)
                        visited.add(child)
            current_level = next_level
            level += 1

        max_level = level

        # Position nodes
        for level, nodes in level_nodes.items():
            y = 1.0 - (level * height / max_level)
            nodes_count = len(nodes)
            for i, node in enumerate(nodes):
                x = width * (i + 1) / (nodes_count + 1)
                pos[node] = np.array([x, y])

        return pos

    def _expand_area_node(self, area, max_depth: int):
        """Expand an area node to show its children"""
        if max_depth <= 0:
            return

        area_name = area.get_name()
        area_rels = area.get_relationships()

        # Get all areas and their relationship sets
        all_areas = [(a, a.get_relationships()) for a in self.taxonomy.get_areas()]

        # Find direct children (those with exactly one more relationship)
        for child_area, child_rels in all_areas:
            if child_area != area and child_rels.issuperset(area_rels):
                # Check if it's a direct child (one level down)
                # It should have exactly one more relationship than the parent
                if len(child_rels) == len(area_rels) + 1:
                    # Add child node
                    child_name = child_area.get_name()
                    self._add_area_node(child_area,
                                        level=self.node_states[area_name].level + 1,
                                        parent=area_name)

                    # Add edge
                    self.G.add_edge(area_name, child_name)

                    # Make child visible up to max_depth
                    self.node_states[child_name].visible = True

                    # Recursively expand child
                    self._expand_area_node(child_area, max_depth - 1)

        self.node_states[area_name].expanded = True

    def _expand_parea_node(self, parea, max_depth: int):
        """Expand a PArea node to show its children"""
        if max_depth <= 0:
            return

        parea_name = parea.get_root().get_name()
        parea_hier = self.taxonomy.get_parea_hierarchy()

        # Get direct children from hierarchy
        children = parea_hier.get_children(parea)
        for child_parea in children:
            child_name = child_parea.get_root().get_name()

            # Add child node
            self._add_parea_node(child_parea,
                                 level=self.node_states[parea_name].level + 1,
                                 parent=parea_name)

            # Add edge
            self.G.add_edge(parea_name, child_name)

            # Make child visible up to max_depth
            self.node_states[child_name].visible = True

            # Recursively expand child
            self._expand_parea_node(child_parea, max_depth - 1)

        self.node_states[parea_name].expanded = True

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
                visible=True,  # Changed to True by default
                parent_id=parent,
                level=level
            )

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
                visible=True,  # Changed to True by default
                parent_id=parent,
                level=level
            )
    # def _add_area_node(self, area, level: int, parent=None):
    #     """Add an area node to the graph with metadata"""
    #     area_name = area.get_name()
    #     if area_name not in self.G:
    #         self.G.add_node(area_name,
    #                         num_concepts=len(area.get_concepts()),
    #                         num_pareas=len(area.get_pareas()),
    #                         relationships=list(area.get_relationships()),
    #                         concepts=[c.get_name() for c in area.get_concepts()],
    #                         level=level)
    #
    #         self.node_states[area_name] = NodeState(
    #             expanded=False,
    #             visible=level <= 1,
    #             parent_id=parent,
    #             level=level
    #         )
    #
    # def _expand_area_node(self, area, max_depth: int):
    #     """Expand an area node to show its children"""
    #     if max_depth <= 0:
    #         return
    #
    #     area_name = area.get_name()
    #     area_rels = area.get_relationships()
    #
    #     # Find child areas (those with superset of relationships)
    #     for child_area in self.taxonomy.get_areas():
    #         if (child_area != area and
    #                 child_area.get_relationships().issuperset(area_rels)):
    #             # Add child node
    #             child_name = child_area.get_name()
    #             self._add_area_node(child_area,
    #                                 level=self.node_states[area_name].level + 1,
    #                                 parent=area_name)
    #
    #             # Add edge
    #             self.G.add_edge(area_name, child_name)
    #
    #             # Recursively expand child
    #             self._expand_area_node(child_area, max_depth - 1)
    #
    #     self.node_states[area_name].expanded = True
    #
    # def _add_parea_node(self, parea, level: int, parent=None):
    #     """Add a PArea node to the graph with metadata"""
    #     parea_name = parea.get_root().get_name()
    #     if parea_name not in self.G:
    #         self.G.add_node(parea_name,
    #                         num_concepts=len(parea.get_concepts()),
    #                         relationships=list(parea.get_relationships()),
    #                         concepts=[c.get_name() for c in parea.get_concepts()],
    #                         level=level)
    #
    #         self.node_states[parea_name] = NodeState(
    #             expanded=False,
    #             visible=level <= 1,
    #             parent_id=parent,
    #             level=level
    #         )
    #
    # def _expand_parea_node(self, parea, max_depth: int):
    #     """Expand a PArea node to show its children"""
    #     if max_depth <= 0:
    #         return
    #
    #     parea_name = parea.get_root().get_name()
    #     parea_hier = self.taxonomy.get_parea_hierarchy()
    #
    #     # Add children PAreas
    #     for child_parea in parea_hier.get_children(parea):
    #         child_name = child_parea.get_root().get_name()
    #
    #         # Add child node
    #         self._add_parea_node(child_parea,
    #                              level=self.node_states[parea_name].level + 1,
    #                              parent=parea_name)
    #
    #         # Add edge
    #         self.G.add_edge(parea_name, child_name)
    #
    #         # Recursively expand child
    #         self._expand_parea_node(child_parea, max_depth - 1)
    #
    #     self.node_states[parea_name].expanded = True

    def create_area_visualization(self, taxonomy, initial_depth: int = 1):
        """Create hierarchical Area taxonomy visualization"""
        self.taxonomy = taxonomy
        self.G = nx.DiGraph()

        # Initialize with root area
        root_area = taxonomy.get_root_area()
        root_name = root_area.get_name()
        self._add_area_node(root_area, level=0)

        # Add initial visible nodes
        self._expand_area_node(root_area, max_depth=initial_depth)

        # Calculate hierarchical layout
        self.pos = self._hierarchical_layout(self.G, root_name)

        # Create figure
        self._create_hierarchical_figure()
        self._add_buttons()

        return self.fig

    def create_parea_visualization(self, parea_taxonomy, initial_depth: int = 1):
        """Create hierarchical PArea taxonomy visualization"""
        self.taxonomy = parea_taxonomy
        self.G = nx.DiGraph()

        # Initialize with root PArea
        root_parea = parea_taxonomy.get_root_parea()
        root_name = root_parea.get_root().get_name()
        self._add_parea_node(root_parea, level=0)

        # Add initial visible nodes
        self._expand_parea_node(root_parea, max_depth=initial_depth)

        # Calculate hierarchical layout
        self.pos = self._hierarchical_layout(self.G, root_name)

        # Create figure
        self._create_hierarchical_figure(is_parea=True)
        self._add_buttons()

        return self.fig

    def _create_hierarchical_figure(self, is_parea=False):
        """Create hierarchical visualization"""
        # Create edge traces for visible edges
        edge_traces = []

        # Create curved edges
        for edge in self.G.edges():
            if (self.node_states[edge[0]].visible and
                    self.node_states[edge[1]].visible):
                x0, y0 = self.pos[edge[0]]
                x1, y1 = self.pos[edge[1]]

                # Create curved path
                path_x = [x0, (x0 + x1) / 2, x1]
                path_y = [y0, (y0 + y1) / 2, y1]

                edge_trace = go.Scatter(
                    x=path_x,
                    y=path_y,
                    line=dict(width=1, color='#888'),
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
            if is_parea:
                hover_text = (
                    f"PArea: {node}<br>"
                    f"Concepts: {self.G.nodes[node]['num_concepts']}<br>"
                    f"Relationships: {', '.join(self.G.nodes[node]['relationships'])}<br>"
                    f"Level: {self.G.nodes[node]['level']}"
                )
            else:
                hover_text = (
                    f"Area: {node}<br>"
                    f"Concepts: {self.G.nodes[node]['num_concepts']}<br>"
                    f"Partial Areas: {self.G.nodes[node].get('num_pareas', 0)}<br>"
                    f"Relationships: {', '.join(self.G.nodes[node]['relationships'])}"
                )

            node_text.append(hover_text)
            node_size.append(20 + self.G.nodes[node]['num_concepts'] / 100)
            node_colors.append(self.G.nodes[node]['level'])

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=[n.split()[0] for n in visible_nodes],
            textposition="bottom center",
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
            customdata=visible_nodes
        )

        # Create figure with improved layout
        self.fig = go.Figure(
            data=[*edge_traces, node_trace],
            layout=go.Layout(
                title=f'Hierarchical SNOMED CT {"PArea" if is_parea else "Area"} Taxonomy',
                titlefont_size=16,
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20, l=5, r=5, t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                           scaleanchor="x", scaleratio=1),  # Keep aspect ratio
                width=1200,
                height=800,
                plot_bgcolor='white'
            )
        )

        # Add legend
        self.fig.add_annotation(
            text="• Node size: Number of concepts<br>"
                 "• Node color: Hierarchy level<br>"
                 "• Click nodes to expand/collapse",
            align='left',
            showarrow=False,
            xref='paper',
            yref='paper',
            x=1.1,
            y=1,
            bordercolor='black',
            borderwidth=1,
            borderpad=4,
            bgcolor='white'
        )

    def _add_buttons(self):
        """Add control buttons"""
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
                            label="Fit View",
                            method="relayout",
                            args=[{"xaxis.range": None,
                                   "yaxis.range": None}]
                        )
                    ]
                )
            ]
        )


# Example usage:
# """
# viz = HierarchicalTaxonomyVisualizer()
#
# # For Area Taxonomy
# fig = viz.create_area_visualization(taxonomy, initial_depth=2)
#
# # For PArea Taxonomy
# fig = viz.create_parea_visualization(parea_taxonomy, initial_depth=2)
#
# # Save or display
# fig.write_html('hierarchical_taxonomy.html')
# """
