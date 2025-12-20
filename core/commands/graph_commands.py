"""Graph commands for undo/redo support."""
from typing import Optional, Dict, Any, List
from PyQt6.QtGui import QUndoCommand

from core.graph import SceneGraph, SceneNode, SceneEdge


class AddNodeCommand(QUndoCommand):
    """Command to add a new node to the graph."""

    def __init__(self, graph: SceneGraph, node: SceneNode):
        super().__init__(f"Add node '{node.name}'")
        self.graph = graph
        self.node = node

    def redo(self) -> None:
        self.graph.add_node(self.node)

    def undo(self) -> None:
        self.graph.remove_node(self.node.id)


class RemoveNodeCommand(QUndoCommand):
    """Command to remove a node and its connected edges."""

    def __init__(self, graph: SceneGraph, node_id: str):
        super().__init__("Remove node")
        self.graph = graph
        self.node_id = node_id
        self.removed_node: Optional[SceneNode] = None
        self.removed_edges: List[SceneEdge] = []

    def redo(self) -> None:
        # Store for undo
        self.removed_node = self.graph.get_node(self.node_id)
        self.removed_edges = self.graph.get_edges_for_node(self.node_id)

        # Remove edges first, then node
        for edge in self.removed_edges:
            self.graph.remove_edge(edge.id)
        self.graph.remove_node(self.node_id)

    def undo(self) -> None:
        # Restore node and edges
        if self.removed_node:
            self.graph.add_node(self.removed_node)
        for edge in self.removed_edges:
            try:
                self.graph.add_edge(edge)
            except ValueError:
                pass  # Skip if nodes don't exist


class ModifyNodeCommand(QUndoCommand):
    """Command to modify node properties."""

    def __init__(self, graph: SceneGraph, node_id: str, **new_values):
        super().__init__("Modify node")
        self.graph = graph
        self.node_id = node_id
        self.new_values = new_values
        self.old_values: Dict[str, Any] = {}

    def redo(self) -> None:
        node = self.graph.get_node(self.node_id)
        if node:
            # Store old values for undo
            for key in self.new_values:
                self.old_values[key] = getattr(node, key, None)
            # Apply new values
            self.graph.update_node(self.node_id, **self.new_values)

    def undo(self) -> None:
        self.graph.update_node(self.node_id, **self.old_values)


class AddEdgeCommand(QUndoCommand):
    """Command to add an edge to the graph."""

    def __init__(self, graph: SceneGraph, edge: SceneEdge):
        super().__init__("Add edge")
        self.graph = graph
        self.edge = edge

    def redo(self) -> None:
        try:
            self.graph.add_edge(self.edge)
        except ValueError:
            pass

    def undo(self) -> None:
        self.graph.remove_edge(self.edge.id)


class RemoveEdgeCommand(QUndoCommand):
    """Command to remove an edge from the graph."""

    def __init__(self, graph: SceneGraph, edge_id: str):
        super().__init__("Remove edge")
        self.graph = graph
        self.edge_id = edge_id
        self.removed_edge: Optional[SceneEdge] = None

    def redo(self) -> None:
        self.removed_edge = self.graph.get_edge(self.edge_id)
        self.graph.remove_edge(self.edge_id)

    def undo(self) -> None:
        if self.removed_edge:
            try:
                self.graph.add_edge(self.removed_edge)
            except ValueError:
                pass


class ReplaceGraphCommand(QUndoCommand):
    """
    Replace entire graph contents (used after LLM generation/modification).
    """

    def __init__(self, graph: SceneGraph, new_nodes: List[SceneNode], new_edges: List[SceneEdge]):
        super().__init__("Update graph from AI")
        self.graph = graph
        self.new_nodes = new_nodes
        self.new_edges = new_edges
        self.old_nodes: List[SceneNode] = []
        self.old_edges: List[SceneEdge] = []

    def redo(self) -> None:
        # Store current state
        self.old_nodes = list(self.graph.nodes())
        self.old_edges = list(self.graph.edges())

        # Clear and repopulate
        self.graph.clear()
        for node in self.new_nodes:
            self.graph.add_node(node)
        for edge in self.new_edges:
            try:
                self.graph.add_edge(edge)
            except ValueError:
                pass

    def undo(self) -> None:
        self.graph.clear()
        for node in self.old_nodes:
            self.graph.add_node(node)
        for edge in self.old_edges:
            try:
                self.graph.add_edge(edge)
            except ValueError:
                pass
