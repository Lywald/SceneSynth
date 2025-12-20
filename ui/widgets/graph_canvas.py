"""GraphCanvas - Interactive canvas for visualizing scene graphs."""
from typing import Dict, Optional
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QWheelEvent, QColor

from config import LAYOUT_SCALE, LAYOUT_ITERATIONS


class GraphCanvas(QGraphicsView):
    """
    Interactive canvas for visualizing and manipulating the scene graph.
    Uses QGraphicsScene for efficient rendering of nodes/edges.
    """

    node_clicked = pyqtSignal(str)  # node_id
    node_double_clicked = pyqtSignal(str)  # For drill-down
    node_moved = pyqtSignal(str, float, float)  # node_id, x, y
    canvas_clicked = pyqtSignal()  # Deselect

    def __init__(self, app_state=None):
        super().__init__()
        self.app_state = app_state

        self._scene = QGraphicsScene()
        self.setScene(self._scene)

        # Node and edge items
        self._node_items: Dict[str, 'GraphNodeItem'] = {}
        self._edge_items: Dict[str, 'GraphEdgeItem'] = {}

        self._setup_view()
        self._connect_signals()

    def _setup_view(self) -> None:
        """Configure the graphics view."""
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        # Background
        self.setBackgroundBrush(QColor("#F5F5F5"))

        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)

        # Set scene rect
        self._scene.setSceneRect(-2000, -2000, 4000, 4000)

    def _connect_signals(self) -> None:
        """Connect signals."""
        if self.app_state:
            self.app_state.graph_changed.connect(self.refresh_graph)
            self.app_state.current_graph_changed.connect(self.refresh_graph)
            self.node_clicked.connect(self._on_node_clicked)
            self.node_double_clicked.connect(self._on_node_double_clicked)

    def _on_node_clicked(self, node_id: str) -> None:
        """Handle node click."""
        if self.app_state:
            self.app_state.select_node(node_id)

    def _on_node_double_clicked(self, node_id: str) -> None:
        """Handle node double-click for drill-down."""
        if self.app_state:
            self.app_state.expand_node(node_id)

    def refresh_graph(self) -> None:
        """Rebuild the visual representation from current graph."""
        self._scene.clear()
        self._node_items.clear()
        self._edge_items.clear()

        if not self.app_state or not self.app_state.current_graph:
            return

        graph = self.app_state.current_graph

        # Import here to avoid circular imports
        from ui.widgets.graph_node_item import GraphNodeItem
        from ui.widgets.graph_edge_item import GraphEdgeItem

        # Create edge items first (under nodes)
        for edge in graph.edges():
            edge_item = GraphEdgeItem(edge, self._get_node_position)
            self._edge_items[edge.id] = edge_item
            self._scene.addItem(edge_item)

        # Create node items
        for node in graph.nodes():
            node_item = GraphNodeItem(node, self)
            self._node_items[node.id] = node_item
            self._scene.addItem(node_item)

        # Apply layout if nodes don't have positions
        if self._needs_layout():
            self._apply_force_directed_layout()

        # Update edge positions after layout
        for edge_item in self._edge_items.values():
            edge_item.update_position()

        # Fit view to content
        self._fit_to_content()

    def _needs_layout(self) -> bool:
        """Check if nodes need automatic layout."""
        if not self.app_state or not self.app_state.current_graph:
            return False

        # Check if all nodes are at origin
        for node in self.app_state.current_graph.nodes():
            if node.x != 0 or node.y != 0:
                return False
        return True

    def _apply_force_directed_layout(self) -> None:
        """Apply force-directed layout algorithm using networkx."""
        if not self.app_state or not self.app_state.current_graph:
            return

        graph = self.app_state.current_graph

        try:
            import networkx as nx

            G = nx.Graph()

            # Add nodes
            for node in graph.nodes():
                G.add_node(node.id)

            # Add edges
            for edge in graph.edges():
                G.add_edge(edge.source_id, edge.target_id)

            # Compute layout
            if G.number_of_nodes() > 0:
                pos = nx.spring_layout(G, k=200, iterations=LAYOUT_ITERATIONS, seed=42)

                # Apply positions
                for node_id, (x, y) in pos.items():
                    node = graph.get_node(node_id)
                    if node:
                        node.x = x * LAYOUT_SCALE
                        node.y = y * LAYOUT_SCALE

                        # Update visual item
                        if node_id in self._node_items:
                            self._node_items[node_id].setPos(node.x, node.y)

        except ImportError:
            # Fallback: simple circular layout
            import math
            nodes = list(graph.nodes())
            n = len(nodes)
            if n > 0:
                for i, node in enumerate(nodes):
                    angle = 2 * math.pi * i / n
                    node.x = LAYOUT_SCALE * math.cos(angle)
                    node.y = LAYOUT_SCALE * math.sin(angle)

                    if node.id in self._node_items:
                        self._node_items[node.id].setPos(node.x, node.y)

    def _get_node_position(self, node_id: str) -> Optional[QPointF]:
        """Get the position of a node for edge drawing."""
        if node_id in self._node_items:
            return self._node_items[node_id].pos()
        return None

    def update_edges_for_node(self, node_id: str) -> None:
        """Update all edges connected to a node after it moves."""
        if not self.app_state or not self.app_state.current_graph:
            return

        graph = self.app_state.current_graph
        for edge in graph.get_edges_for_node(node_id):
            if edge.id in self._edge_items:
                self._edge_items[edge.id].update_position()

    def _fit_to_content(self) -> None:
        """Fit the view to show all content."""
        rect = self._scene.itemsBoundingRect()
        if not rect.isEmpty():
            rect.adjust(-100, -100, 100, 100)  # Add padding
            self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Zoom with scroll wheel."""
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15

        # Limit zoom
        current_scale = self.transform().m11()
        if (factor > 1 and current_scale < 5) or (factor < 1 and current_scale > 0.1):
            self.scale(factor, factor)

    def mousePressEvent(self, event) -> None:
        """Handle mouse press."""
        # Check if clicking on empty space
        item = self.itemAt(event.pos())
        if item is None:
            self.canvas_clicked.emit()
            if self.app_state:
                self.app_state.deselect_node()

        super().mousePressEvent(event)

    def keyPressEvent(self, event) -> None:
        """Handle key presses."""
        if event.key() == Qt.Key.Key_Delete:
            # Delete selected nodes
            if self.app_state:
                selected = self.app_state.selected_node
                if selected:
                    self.app_state.delete_node(selected.id)

        elif event.key() == Qt.Key.Key_Escape:
            # Deselect
            if self.app_state:
                self.app_state.deselect_node()

        elif event.key() == Qt.Key.Key_F:
            # Fit to content
            self._fit_to_content()

        super().keyPressEvent(event)

    def zoom_in(self) -> None:
        """Zoom in."""
        self.scale(1.15, 1.15)

    def zoom_out(self) -> None:
        """Zoom out."""
        self.scale(1 / 1.15, 1 / 1.15)

    def reset_zoom(self) -> None:
        """Reset zoom to default."""
        self.resetTransform()
        self._fit_to_content()

    def capture_screenshot(self, width: int = 800, height: int = 600) -> bytes:
        """
        Capture the current graph view as a PNG image.

        Args:
            width: Output image width
            height: Output image height

        Returns:
            PNG image as bytes
        """
        from PyQt6.QtGui import QImage, QPainter
        from PyQt6.QtCore import QBuffer, QIODevice

        # Create image
        image = QImage(width, height, QImage.Format.Format_RGB32)
        image.fill(QColor("#F5F5F5"))  # Background color

        # Create painter
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # Render the scene to the image
        self._scene.render(painter)
        painter.end()

        # Convert to PNG bytes
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, "PNG")
        return bytes(buffer.data())
