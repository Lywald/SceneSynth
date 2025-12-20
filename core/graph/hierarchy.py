"""HierarchyManager for managing nested scene graphs."""
from typing import Dict, List, Optional, Tuple, Any
import json

from .scene_graph import SceneGraph
from .node import SceneNode


class HierarchyManager:
    """
    Manages the tree of nested SceneGraphs.

    Handles navigation between hierarchy levels and maintains
    parent-child relationships between graphs.
    """

    def __init__(self):
        self._graphs: Dict[str, SceneGraph] = {}
        self._root_graph_id: Optional[str] = None
        self._current_graph_id: Optional[str] = None
        self._navigation_stack: List[str] = []  # Breadcrumb trail

    # ==================== Graph Management ====================

    def add_graph(self, graph: SceneGraph) -> None:
        """Add a graph to the hierarchy."""
        self._graphs[graph.id] = graph

    def remove_graph(self, graph_id: str) -> bool:
        """Remove a graph from the hierarchy."""
        if graph_id not in self._graphs:
            return False

        # Remove from navigation stack if present
        self._navigation_stack = [gid for gid in self._navigation_stack if gid != graph_id]

        # Update current if needed
        if self._current_graph_id == graph_id:
            self._current_graph_id = self._root_graph_id

        # Remove child graph references in parent
        graph = self._graphs[graph_id]
        if graph.parent_graph_id and graph.parent_node_id:
            parent = self._graphs.get(graph.parent_graph_id)
            if parent:
                parent_node = parent.get_node(graph.parent_node_id)
                if parent_node:
                    parent_node.child_graph_id = None

        del self._graphs[graph_id]
        return True

    def get_graph(self, graph_id: str) -> Optional[SceneGraph]:
        """Get a graph by ID."""
        return self._graphs.get(graph_id)

    # ==================== Hierarchy Operations ====================

    def set_root(self, graph: SceneGraph) -> None:
        """Set the root graph of the hierarchy."""
        graph.depth_level = 0
        graph.parent_graph_id = None
        graph.parent_node_id = None

        self.add_graph(graph)
        self._root_graph_id = graph.id
        self._current_graph_id = graph.id
        self._navigation_stack = [graph.id]

    def create_child_graph(self, parent_node: SceneNode, child_graph: SceneGraph) -> None:
        """
        Create a child graph linked to a parent node.

        Args:
            parent_node: The node being expanded
            child_graph: The new child graph
        """
        parent_graph = self._graphs.get(parent_node.parent_graph_id)
        if not parent_graph:
            raise ValueError("Parent node's graph not found in hierarchy")

        # Set up relationships
        child_graph.parent_graph_id = parent_graph.id
        child_graph.parent_node_id = parent_node.id
        child_graph.depth_level = parent_graph.depth_level + 1

        # Link parent node to child graph
        parent_node.child_graph_id = child_graph.id

        self.add_graph(child_graph)

    def get_parent_graph(self, graph_id: str) -> Optional[SceneGraph]:
        """Get the parent graph of a given graph."""
        graph = self._graphs.get(graph_id)
        if not graph or not graph.parent_graph_id:
            return None
        return self._graphs.get(graph.parent_graph_id)

    def get_child_graphs(self, graph_id: str) -> List[SceneGraph]:
        """Get all child graphs of a given graph."""
        return [g for g in self._graphs.values() if g.parent_graph_id == graph_id]

    def get_all_descendant_graphs(self, graph_id: str) -> List[SceneGraph]:
        """Get all descendant graphs (children, grandchildren, etc.)."""
        descendants = []
        children = self.get_child_graphs(graph_id)
        for child in children:
            descendants.append(child)
            descendants.extend(self.get_all_descendant_graphs(child.id))
        return descendants

    # ==================== Navigation ====================

    @property
    def current_graph(self) -> Optional[SceneGraph]:
        """Get the currently displayed graph."""
        if self._current_graph_id:
            return self._graphs.get(self._current_graph_id)
        return None

    @property
    def root_graph(self) -> Optional[SceneGraph]:
        """Get the root graph."""
        if self._root_graph_id:
            return self._graphs.get(self._root_graph_id)
        return None

    def navigate_to(self, graph_id: str) -> bool:
        """Navigate to a specific graph."""
        if graph_id not in self._graphs:
            return False

        self._current_graph_id = graph_id

        # Rebuild navigation stack from root to current
        self._navigation_stack = self._build_path_to_graph(graph_id)
        return True

    def navigate_to_child(self, node_id: str) -> bool:
        """Navigate to a node's child graph (drill down)."""
        if not self._current_graph_id:
            return False

        current = self._graphs.get(self._current_graph_id)
        if not current:
            return False

        node = current.get_node(node_id)
        if not node or not node.child_graph_id:
            return False

        return self.navigate_to(node.child_graph_id)

    def navigate_up(self) -> bool:
        """Navigate to the parent graph."""
        if not self._current_graph_id:
            return False

        current = self._graphs.get(self._current_graph_id)
        if not current or not current.parent_graph_id:
            return False

        return self.navigate_to(current.parent_graph_id)

    def navigate_to_root(self) -> bool:
        """Navigate to the root graph."""
        if not self._root_graph_id:
            return False
        return self.navigate_to(self._root_graph_id)

    def get_breadcrumb_path(self) -> List[Tuple[str, str]]:
        """
        Get the breadcrumb navigation path.

        Returns:
            List of (graph_id, graph_name) tuples from root to current
        """
        result = []
        for graph_id in self._navigation_stack:
            graph = self._graphs.get(graph_id)
            if graph:
                result.append((graph.id, graph.name or f"Level {graph.depth_level}"))
        return result

    def _build_path_to_graph(self, graph_id: str) -> List[str]:
        """Build the path from root to the given graph."""
        path = []
        current_id = graph_id

        while current_id:
            path.insert(0, current_id)
            graph = self._graphs.get(current_id)
            if graph:
                current_id = graph.parent_graph_id
            else:
                break

        return path

    # ==================== Serialization ====================

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the entire hierarchy to a dictionary."""
        return {
            "root_graph_id": self._root_graph_id,
            "current_graph_id": self._current_graph_id,
            "graphs": [graph.to_dict() for graph in self._graphs.values()]
        }

    def to_json(self, pretty: bool = True) -> str:
        """Serialize the hierarchy to JSON string."""
        if pretty:
            return json.dumps(self.to_dict(), indent=2)
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HierarchyManager':
        """Deserialize a hierarchy from a dictionary."""
        manager = cls()

        # Load all graphs
        for graph_data in data.get("graphs", []):
            graph = SceneGraph.from_dict(graph_data)
            manager._graphs[graph.id] = graph

        manager._root_graph_id = data.get("root_graph_id")
        manager._current_graph_id = data.get("current_graph_id")

        # Rebuild navigation stack
        if manager._current_graph_id:
            manager._navigation_stack = manager._build_path_to_graph(manager._current_graph_id)

        return manager

    @classmethod
    def from_json(cls, json_str: str) -> 'HierarchyManager':
        """Deserialize a hierarchy from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def save_project(self, filepath: str) -> None:
        """Save the entire hierarchy to a file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())

    def load_project(self, filepath: str) -> None:
        """Load a hierarchy from a file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        loaded = self.from_dict(data)
        self._graphs = loaded._graphs
        self._root_graph_id = loaded._root_graph_id
        self._current_graph_id = loaded._current_graph_id
        self._navigation_stack = loaded._navigation_stack

    # ==================== Utility ====================

    @property
    def graph_count(self) -> int:
        """Get the total number of graphs in the hierarchy."""
        return len(self._graphs)

    def get_all_graphs(self) -> List[SceneGraph]:
        """Get all graphs in the hierarchy."""
        return list(self._graphs.values())

    def __repr__(self) -> str:
        return f"HierarchyManager(graphs={self.graph_count}, current={self._current_graph_id[:8] if self._current_graph_id else 'None'}...)"
