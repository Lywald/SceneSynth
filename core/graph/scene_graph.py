"""SceneGraph container for semantic scene graphs."""
from typing import Dict, List, Optional, Iterator, Any
from uuid import uuid4
import json

from .node import SceneNode
from .edge import SceneEdge


class SceneGraph:
    """
    Container for a semantic scene graph at a single hierarchy level.

    Manages nodes and edges, provides CRUD operations, and handles
    JSON serialization for the entire graph.
    """

    def __init__(self, graph_id: str = None, name: str = ""):
        self.id: str = graph_id or str(uuid4())
        self.name: str = name
        self.master_prompt: str = ""
        self.depth_level: int = 0

        # Parent reference (for navigation)
        self.parent_graph_id: Optional[str] = None
        self.parent_node_id: Optional[str] = None

        # Graph data
        self._nodes: Dict[str, SceneNode] = {}
        self._edges: Dict[str, SceneEdge] = {}
        self._adjacency: Dict[str, List[str]] = {}  # node_id -> [connected node_ids]

        # Rendered image (PNG bytes, base64 encoded for JSON serialization)
        self._rendered_image: Optional[str] = None  # Base64 encoded PNG

    # ==================== Node Operations ====================

    def add_node(self, node: SceneNode) -> None:
        """Add a node to the graph."""
        node.parent_graph_id = self.id
        self._nodes[node.id] = node
        if node.id not in self._adjacency:
            self._adjacency[node.id] = []

    def remove_node(self, node_id: str) -> Optional[SceneNode]:
        """Remove a node and its connected edges from the graph."""
        if node_id not in self._nodes:
            return None

        node = self._nodes.pop(node_id)

        # Remove all edges connected to this node
        edges_to_remove = [e.id for e in self._edges.values() if e.connects(node_id)]
        for edge_id in edges_to_remove:
            self.remove_edge(edge_id)

        # Remove from adjacency
        if node_id in self._adjacency:
            del self._adjacency[node_id]

        return node

    def get_node(self, node_id: str) -> Optional[SceneNode]:
        """Get a node by ID."""
        return self._nodes.get(node_id)

    def update_node(self, node_id: str, **kwargs) -> bool:
        """Update node properties."""
        node = self._nodes.get(node_id)
        if not node:
            return False

        for key, value in kwargs.items():
            if hasattr(node, key):
                setattr(node, key, value)

        return True

    def get_node_by_name(self, name: str) -> Optional[SceneNode]:
        """Find a node by its name (case-insensitive)."""
        name_lower = name.lower()
        for node in self._nodes.values():
            if node.name.lower() == name_lower:
                return node
        return None

    # ==================== Edge Operations ====================

    def add_edge(self, edge: SceneEdge) -> None:
        """Add an edge to the graph."""
        if edge.source_id not in self._nodes or edge.target_id not in self._nodes:
            raise ValueError("Both source and target nodes must exist in the graph")

        self._edges[edge.id] = edge

        # Update adjacency
        if edge.source_id not in self._adjacency:
            self._adjacency[edge.source_id] = []
        if edge.target_id not in self._adjacency[edge.source_id]:
            self._adjacency[edge.source_id].append(edge.target_id)

        if edge.is_bidirectional:
            if edge.target_id not in self._adjacency:
                self._adjacency[edge.target_id] = []
            if edge.source_id not in self._adjacency[edge.target_id]:
                self._adjacency[edge.target_id].append(edge.source_id)

    def remove_edge(self, edge_id: str) -> Optional[SceneEdge]:
        """Remove an edge from the graph."""
        if edge_id not in self._edges:
            return None

        edge = self._edges.pop(edge_id)

        # Update adjacency
        if edge.source_id in self._adjacency:
            if edge.target_id in self._adjacency[edge.source_id]:
                self._adjacency[edge.source_id].remove(edge.target_id)

        if edge.is_bidirectional and edge.target_id in self._adjacency:
            if edge.source_id in self._adjacency[edge.target_id]:
                self._adjacency[edge.target_id].remove(edge.source_id)

        return edge

    def get_edge(self, edge_id: str) -> Optional[SceneEdge]:
        """Get an edge by ID."""
        return self._edges.get(edge_id)

    def get_edges_for_node(self, node_id: str) -> List[SceneEdge]:
        """Get all edges connected to a node."""
        return [e for e in self._edges.values() if e.connects(node_id)]

    def get_edge_between(self, node1_id: str, node2_id: str) -> Optional[SceneEdge]:
        """Find an edge connecting two specific nodes."""
        for edge in self._edges.values():
            if (edge.source_id == node1_id and edge.target_id == node2_id) or \
               (edge.is_bidirectional and edge.source_id == node2_id and edge.target_id == node1_id):
                return edge
        return None

    # ==================== Queries ====================

    def get_neighbors(self, node_id: str) -> List[SceneNode]:
        """Get all nodes directly connected to the given node."""
        neighbor_ids = self._adjacency.get(node_id, [])
        return [self._nodes[nid] for nid in neighbor_ids if nid in self._nodes]

    def find_nodes_by_type(self, node_type: str) -> List[SceneNode]:
        """Find all nodes of a specific type."""
        return [n for n in self._nodes.values() if n.node_type == node_type]

    def find_nodes_by_name(self, name_pattern: str) -> List[SceneNode]:
        """Find nodes with names containing the pattern (case-insensitive)."""
        pattern_lower = name_pattern.lower()
        return [n for n in self._nodes.values() if pattern_lower in n.name.lower()]

    # ==================== Iteration ====================

    def nodes(self) -> Iterator[SceneNode]:
        """Iterate over all nodes."""
        return iter(self._nodes.values())

    def edges(self) -> Iterator[SceneEdge]:
        """Iterate over all edges."""
        return iter(self._edges.values())

    @property
    def node_count(self) -> int:
        """Get the number of nodes."""
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        """Get the number of edges."""
        return len(self._edges)

    # ==================== Graph Operations ====================

    def clear(self) -> None:
        """Remove all nodes and edges."""
        self._nodes.clear()
        self._edges.clear()
        self._adjacency.clear()

    # ==================== Rendered Image ====================

    def set_rendered_image(self, image_bytes: bytes) -> None:
        """Set the rendered image from PNG bytes."""
        import base64
        self._rendered_image = base64.b64encode(image_bytes).decode('utf-8')

    def get_rendered_image(self) -> Optional[bytes]:
        """Get the rendered image as PNG bytes."""
        import base64
        if self._rendered_image:
            return base64.b64decode(self._rendered_image)
        return None

    def has_rendered_image(self) -> bool:
        """Check if this graph has a rendered image."""
        return self._rendered_image is not None

    def clear_rendered_image(self) -> None:
        """Clear the rendered image."""
        self._rendered_image = None

    # ==================== Serialization ====================

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the entire graph to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "master_prompt": self.master_prompt,
            "depth_level": self.depth_level,
            "parent_graph_id": self.parent_graph_id,
            "parent_node_id": self.parent_node_id,
            "nodes": [node.to_dict() for node in self._nodes.values()],
            "edges": [edge.to_dict() for edge in self._edges.values()],
            "rendered_image": self._rendered_image
        }

    def to_json(self, pretty: bool = True) -> str:
        """Serialize the graph to JSON string."""
        if pretty:
            return json.dumps(self.to_dict(), indent=2)
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SceneGraph':
        """Deserialize a graph from a dictionary."""
        graph = cls(
            graph_id=data.get("id"),
            name=data.get("name", "")
        )
        graph.master_prompt = data.get("master_prompt", "")
        graph.depth_level = data.get("depth_level", 0)
        graph.parent_graph_id = data.get("parent_graph_id")
        graph.parent_node_id = data.get("parent_node_id")
        graph._rendered_image = data.get("rendered_image")

        # Add nodes first
        for node_data in data.get("nodes", []):
            node = SceneNode.from_dict(node_data)
            graph.add_node(node)

        # Then add edges
        for edge_data in data.get("edges", []):
            edge = SceneEdge.from_dict(edge_data)
            try:
                graph.add_edge(edge)
            except ValueError:
                # Skip edges with missing nodes
                pass

        return graph

    @classmethod
    def from_json(cls, json_str: str) -> 'SceneGraph':
        """Deserialize a graph from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def __repr__(self) -> str:
        return f"SceneGraph(id={self.id[:8]}..., name='{self.name}', nodes={self.node_count}, edges={self.edge_count})"
