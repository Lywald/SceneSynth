"""AppState - Central application state manager."""
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QUndoStack

from core.graph import SceneGraph, SceneNode, SceneEdge, HierarchyManager
from core.llm.base_provider import BaseLLMProvider, GraphGenerationRequest, GraphModificationRequest
from core.llm.gemini_provider import GeminiProvider, MockGeminiProvider
from core.llm.image_generator import SceneImageGenerator, MockSceneImageGenerator
from core.settings import get_settings
from config import NODE_COLORS, LAYOUT_SCALE


class AppState(QObject):
    """
    Central application state manager.
    Emits signals when state changes for UI updates.
    """

    # Signals
    graph_changed = pyqtSignal()
    current_graph_changed = pyqtSignal(str)  # graph_id
    node_selected = pyqtSignal(str)  # node_id or empty
    loading_started = pyqtSignal(str)  # operation description
    loading_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    image_rendered = pyqtSignal(str)  # graph_id that was rendered

    def __init__(self):
        super().__init__()
        self.hierarchy = HierarchyManager()
        self.undo_stack = QUndoStack()
        self.llm_provider: Optional[BaseLLMProvider] = None
        self.image_generator = None
        self._settings = get_settings()

        self._selected_node_id: Optional[str] = None
        self._is_loading: bool = False
        self._api_key: Optional[str] = None
        self._project_path: Optional[str] = None
        self._graph_canvas = None  # Reference to graph canvas for screenshots

        # Load saved API key and configure provider
        saved_key = self._settings.api_key
        project_id = self._settings.vertex_project_id
        if saved_key:
            self._api_key = saved_key
            self.llm_provider = GeminiProvider(saved_key)
            self.image_generator = SceneImageGenerator(api_key=saved_key, project_id=project_id)
        else:
            # Use mock provider by default for testing
            self.llm_provider = MockGeminiProvider()
            self.image_generator = MockSceneImageGenerator()

    # ==================== Properties ====================

    @property
    def current_graph(self) -> Optional[SceneGraph]:
        """Get the currently displayed graph."""
        return self.hierarchy.current_graph

    @property
    def selected_node(self) -> Optional[SceneNode]:
        """Get the currently selected node."""
        if self._selected_node_id and self.current_graph:
            return self.current_graph.get_node(self._selected_node_id)
        return None

    @property
    def api_key(self) -> Optional[str]:
        """Get the API key."""
        return self._api_key

    @property
    def project_path(self) -> Optional[str]:
        """Get the current project file path."""
        return self._project_path

    # ==================== API Key Management ====================

    def set_api_key(self, key: str) -> None:
        """Set the API key and configure the LLM provider."""
        self._api_key = key
        # Save to persistent settings
        self._settings.api_key = key
        project_id = self._settings.vertex_project_id
        if key:
            self.llm_provider = GeminiProvider(key)
            self.image_generator = SceneImageGenerator(api_key=key, project_id=project_id)
        else:
            self.llm_provider = MockGeminiProvider()
            self.image_generator = MockSceneImageGenerator()

    def set_graph_canvas(self, canvas) -> None:
        """Set the reference to the graph canvas for screenshots."""
        self._graph_canvas = canvas

    def test_api_key(self, key: str) -> bool:
        """Test if an API key is valid."""
        try:
            provider = GeminiProvider(key)
            return provider.validate_api_key()
        except Exception:
            return False

    # ==================== Project Management ====================

    def new_project(self) -> None:
        """Create a new empty project."""
        self.hierarchy = HierarchyManager()
        self._selected_node_id = None
        self._project_path = None

        # Create initial empty graph
        initial_graph = SceneGraph(name="New World")
        initial_graph.master_prompt = ""
        self.hierarchy.set_root(initial_graph)

        self.graph_changed.emit()
        self.current_graph_changed.emit(initial_graph.id)

    def save_project(self, filepath: str) -> None:
        """Save the project to a file."""
        try:
            self.hierarchy.save_project(filepath)
            self._project_path = filepath
        except Exception as e:
            self.error_occurred.emit(f"Failed to save project: {e}")

    def load_project(self, filepath: str) -> None:
        """Load a project from a file."""
        try:
            self.loading_started.emit("Loading project...")
            self.hierarchy.load_project(filepath)
            self._project_path = filepath
            self._selected_node_id = None

            self.graph_changed.emit()
            if self.hierarchy.current_graph:
                self.current_graph_changed.emit(self.hierarchy.current_graph.id)

            self.loading_finished.emit()
        except Exception as e:
            self.loading_finished.emit()
            self.error_occurred.emit(f"Failed to load project: {e}")

    # ==================== Graph Generation ====================

    def generate_graph(self, prompt: str, node_count: int = 8) -> None:
        """Generate a new graph from a prompt."""
        if not self.llm_provider:
            self.error_occurred.emit("No LLM provider configured")
            return

        self.loading_started.emit("Generating graph...")

        try:
            # Create request
            request = GraphGenerationRequest(
                master_prompt=prompt,
                depth_level=0,
                max_nodes=node_count
            )

            # Generate
            response = self.llm_provider.generate_graph(request)

            # Create new graph
            graph = SceneGraph(name=prompt[:50])
            graph.master_prompt = prompt

            # Add nodes with semantic positions from LLM
            name_to_id = {}
            for node_data in response.nodes:
                # Scale LLM positions (-1 to 1) to canvas coordinates
                x = node_data.get("x", 0.0) * LAYOUT_SCALE
                y = -node_data.get("y", 0.0) * LAYOUT_SCALE  # Invert Y (screen coords)

                node = SceneNode(
                    name=node_data.get("name", "Unknown"),
                    description=node_data.get("description", ""),
                    node_type=node_data.get("node_type", "location"),
                    size=node_data.get("size", 1.0),
                    is_expandable=node_data.get("is_expandable", True),
                    color=NODE_COLORS.get(node_data.get("node_type", "location"), "#4A90D9"),
                    x=x,
                    y=y
                )
                graph.add_node(node)
                name_to_id[node.name] = node.id

            # Add edges
            for edge_data in response.edges:
                source_name = edge_data.get("source", "")
                target_name = edge_data.get("target", "")

                if source_name in name_to_id and target_name in name_to_id:
                    edge = SceneEdge(
                        source_id=name_to_id[source_name],
                        target_id=name_to_id[target_name],
                        relationship=edge_data.get("relationship", "connected_to"),
                        label=edge_data.get("label", "")
                    )
                    graph.add_edge(edge)

            # Set as root
            self.hierarchy.set_root(graph)
            self._selected_node_id = None

            self.graph_changed.emit()
            self.current_graph_changed.emit(graph.id)
            self.loading_finished.emit()

        except Exception as e:
            self.loading_finished.emit()
            self.error_occurred.emit(f"Generation failed: {e}")

    def modify_graph(self, instruction: str) -> None:
        """Modify the current graph based on a natural language instruction."""
        if not self.llm_provider:
            self.error_occurred.emit("No LLM provider configured")
            return

        if not self.current_graph:
            self.error_occurred.emit("No graph to modify")
            return

        self.loading_started.emit("Modifying graph...")

        try:
            # Create request
            request = GraphModificationRequest(
                instruction=instruction,
                current_graph_json=self.current_graph.to_json()
            )

            # Modify
            response = self.llm_provider.modify_graph(request)

            # Update graph
            graph = self.current_graph
            graph.clear()

            # Add nodes with semantic positions from LLM
            name_to_id = {}
            for node_data in response.nodes:
                # Scale LLM positions (-1 to 1) to canvas coordinates
                x = node_data.get("x", 0.0) * LAYOUT_SCALE
                y = -node_data.get("y", 0.0) * LAYOUT_SCALE  # Invert Y

                node = SceneNode(
                    name=node_data.get("name", "Unknown"),
                    description=node_data.get("description", ""),
                    node_type=node_data.get("node_type", "location"),
                    size=node_data.get("size", 1.0),
                    is_expandable=node_data.get("is_expandable", True),
                    color=NODE_COLORS.get(node_data.get("node_type", "location"), "#4A90D9"),
                    x=x,
                    y=y
                )
                graph.add_node(node)
                name_to_id[node.name] = node.id

            # Add edges
            for edge_data in response.edges:
                source_name = edge_data.get("source", "")
                target_name = edge_data.get("target", "")

                if source_name in name_to_id and target_name in name_to_id:
                    edge = SceneEdge(
                        source_id=name_to_id[source_name],
                        target_id=name_to_id[target_name],
                        relationship=edge_data.get("relationship", "connected_to"),
                        label=edge_data.get("label", "")
                    )
                    graph.add_edge(edge)

            self._selected_node_id = None
            self.graph_changed.emit()
            self.loading_finished.emit()

        except Exception as e:
            self.loading_finished.emit()
            self.error_occurred.emit(f"Modification failed: {e}")

    def render_scene(self, graph_id: str = None, style: str = "top-down 2D game art") -> None:
        """
        Render the current or specified graph as an image.

        Args:
            graph_id: ID of graph to render, or None for current graph
            style: Art style for the rendered image
        """
        if not self.image_generator:
            self.error_occurred.emit("No image generator configured")
            return

        if not self._graph_canvas:
            self.error_occurred.emit("Graph canvas not available")
            return

        # Get the graph to render
        if graph_id:
            graph = self.hierarchy.get_graph(graph_id)
        else:
            graph = self.current_graph

        if not graph:
            self.error_occurred.emit("No graph to render")
            return

        self.loading_started.emit(f"Rendering '{graph.name}'...")

        try:
            # Capture screenshot of the graph
            screenshot = self._graph_canvas.capture_screenshot(800, 600)

            # Get graph JSON (without rendered_image to avoid recursion)
            graph_json = graph.to_json()

            # Generate image
            image_bytes = self.image_generator.generate_scene_image(
                graph_json=graph_json,
                graph_screenshot=screenshot,
                scene_name=graph.name or "Scene",
                style=style
            )

            if image_bytes:
                # Store the rendered image
                graph.set_rendered_image(image_bytes)
                self.image_rendered.emit(graph.id)
                self.graph_changed.emit()
                self.loading_finished.emit()
            else:
                self.loading_finished.emit()
                self.error_occurred.emit("Image generation returned no result")

        except Exception as e:
            self.loading_finished.emit()
            self.error_occurred.emit(f"Rendering failed: {e}")

    def get_rendered_image(self, graph_id: str = None) -> Optional[bytes]:
        """Get the rendered image for a graph."""
        if graph_id:
            graph = self.hierarchy.get_graph(graph_id)
        else:
            graph = self.current_graph

        if graph:
            return graph.get_rendered_image()
        return None

    def expand_node(self, node_id: str) -> None:
        """Expand a node to create a child graph (drill-down)."""
        if not self.current_graph:
            return

        node = self.current_graph.get_node(node_id)
        if not node:
            return

        # If already has child graph, navigate to it
        if node.child_graph_id:
            self.navigate_to_graph(node.child_graph_id)
            return

        # Check if expandable
        if not node.is_expandable:
            return

        if not self.llm_provider:
            self.error_occurred.emit("No LLM provider configured")
            return

        self.loading_started.emit(f"Expanding '{node.name}'...")

        try:
            # Create request with context from parent
            request = GraphGenerationRequest(
                master_prompt=node.description or node.name,
                context=f"This is a detailed view of '{node.name}' from the parent scene.",
                parent_node_info=node.to_dict(),
                depth_level=self.current_graph.depth_level + 1,
                max_nodes=8
            )

            # Generate
            response = self.llm_provider.generate_graph(request)

            # Create child graph
            child_graph = SceneGraph(name=node.name)
            child_graph.master_prompt = node.description or node.name

            # Add nodes with semantic positions from LLM
            name_to_id = {}
            for node_data in response.nodes:
                # Scale LLM positions (-1 to 1) to canvas coordinates
                x = node_data.get("x", 0.0) * LAYOUT_SCALE
                y = -node_data.get("y", 0.0) * LAYOUT_SCALE  # Invert Y

                child_node = SceneNode(
                    name=node_data.get("name", "Unknown"),
                    description=node_data.get("description", ""),
                    node_type=node_data.get("node_type", "location"),
                    size=node_data.get("size", 1.0),
                    is_expandable=node_data.get("is_expandable", True),
                    color=NODE_COLORS.get(node_data.get("node_type", "location"), "#4A90D9"),
                    x=x,
                    y=y
                )
                child_graph.add_node(child_node)
                name_to_id[child_node.name] = child_node.id

            # Add edges
            for edge_data in response.edges:
                source_name = edge_data.get("source", "")
                target_name = edge_data.get("target", "")

                if source_name in name_to_id and target_name in name_to_id:
                    edge = SceneEdge(
                        source_id=name_to_id[source_name],
                        target_id=name_to_id[target_name],
                        relationship=edge_data.get("relationship", "connected_to"),
                        label=edge_data.get("label", "")
                    )
                    child_graph.add_edge(edge)

            # Link to parent
            self.hierarchy.create_child_graph(node, child_graph)

            # Navigate to child
            self.hierarchy.navigate_to(child_graph.id)
            self._selected_node_id = None

            self.graph_changed.emit()
            self.current_graph_changed.emit(child_graph.id)
            self.loading_finished.emit()

        except Exception as e:
            self.loading_finished.emit()
            self.error_occurred.emit(f"Expansion failed: {e}")

    # ==================== Node Operations ====================

    def select_node(self, node_id: str) -> None:
        """Select a node."""
        self._selected_node_id = node_id
        self.node_selected.emit(node_id)

    def deselect_node(self) -> None:
        """Deselect the current node."""
        self._selected_node_id = None
        self.node_selected.emit("")

    def update_node(self, node_id: str, **kwargs) -> None:
        """Update node properties."""
        if not self.current_graph:
            return

        self.current_graph.update_node(node_id, **kwargs)
        self.graph_changed.emit()

    def delete_node(self, node_id: str) -> None:
        """Delete a node from the current graph."""
        if not self.current_graph:
            return

        # Check if it's the selected node
        if self._selected_node_id == node_id:
            self._selected_node_id = None
            self.node_selected.emit("")

        self.current_graph.remove_node(node_id)
        self.graph_changed.emit()

    # ==================== Navigation ====================

    def navigate_to_graph(self, graph_id: str) -> None:
        """Navigate to a specific graph."""
        if self.hierarchy.navigate_to(graph_id):
            self._selected_node_id = None
            self.graph_changed.emit()
            self.current_graph_changed.emit(graph_id)

    def navigate_up(self) -> None:
        """Navigate to parent graph."""
        if self.hierarchy.navigate_up():
            self._selected_node_id = None
            self.graph_changed.emit()
            if self.current_graph:
                self.current_graph_changed.emit(self.current_graph.id)

    def navigate_to_root(self) -> None:
        """Navigate to root graph."""
        if self.hierarchy.navigate_to_root():
            self._selected_node_id = None
            self.graph_changed.emit()
            if self.current_graph:
                self.current_graph_changed.emit(self.current_graph.id)

    # ==================== Undo/Redo ====================

    def undo(self) -> None:
        """Undo the last action."""
        self.undo_stack.undo()
        self.graph_changed.emit()

    def redo(self) -> None:
        """Redo the last undone action."""
        self.undo_stack.redo()
        self.graph_changed.emit()
