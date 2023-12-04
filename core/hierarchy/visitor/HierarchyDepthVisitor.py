# HierarchyDepthVisitor.py

from collections import defaultdict

class HierarchyDepthVisitor:
    def __init__(self, hierarchy):
        self.hierarchy = hierarchy
        self.depth = defaultdict(int)
        self.result = []

    def visit(self, node):
        max_parent_depth = max([self.depth[parent] for parent in self.hierarchy.get_parents(node)] or [-1])
        self.depth[node] = max_parent_depth + 1
        self.result.append(AncestorDepthResult(node, self.depth[node]))

    def get_result(self):
        return self.result

    def get_all_depths(self):
        return self.depth
