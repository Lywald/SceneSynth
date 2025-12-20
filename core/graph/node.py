"""SceneNode dataclass for semantic scene graph nodes."""
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
from uuid import uuid4
import json

from config import NODE_COLORS


@dataclass
class SceneNode:
    """
    Represents a single node in the semantic scene graph.

    Each node represents a location, element, character, or other
    component in the scene hierarchy.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    node_type: str = "location"

    # Spatial properties
    x: float = 0.0
    y: float = 0.0
    size: float = 1.0  # Relative importance/size (0.5 - 2.0)

    # Hierarchy
    parent_graph_id: Optional[str] = None
    child_graph_id: Optional[str] = None
    is_expandable: bool = True
    expansion_depth: int = 0

    # Visual properties
    color: Optional[str] = None
    icon: Optional[str] = None

    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set default color based on node type if not specified."""
        if self.color is None:
            self.color = NODE_COLORS.get(self.node_type, "#4A90D9")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON export."""
        return asdict(self)

    def to_json(self, pretty: bool = True) -> str:
        """Serialize to JSON string."""
        if pretty:
            return json.dumps(self.to_dict(), indent=2)
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SceneNode':
        """Deserialize from dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'SceneNode':
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def has_child_graph(self) -> bool:
        """Check if this node has been expanded to a child graph."""
        return self.child_graph_id is not None

    def can_expand(self) -> bool:
        """Check if this node can be expanded (drilled down)."""
        return self.is_expandable and self.child_graph_id is None

    def __repr__(self) -> str:
        return f"SceneNode(id={self.id[:8]}..., name='{self.name}', type='{self.node_type}')"
