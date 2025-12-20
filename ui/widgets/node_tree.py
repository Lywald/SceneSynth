"""NodeTreeSidebar - Hierarchical tree view of all nodes."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLineEdit, QLabel, QHBoxLayout, QPushButton, QStyle
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QBrush, QIcon, QPainter, QPixmap

from config import NODE_COLORS


class NodeTreeSidebar(QWidget):
    """
    Tree sidebar showing hierarchical node structure.

    Features:
    - Top-level: nodes in current graph
    - Expandable: child graphs shown inline under their parent node
    - Click to select node on canvas
    - Double-click to drill-down/navigate
    - Search/filter field
    """

    node_selected = pyqtSignal(str)  # node_id
    node_double_clicked = pyqtSignal(str)  # node_id for drill-down
    view_render_requested = pyqtSignal(str)  # graph_id to view render

    def __init__(self, app_state=None):
        super().__init__()
        self.app_state = app_state
        self._node_items: dict = {}  # node_id -> QTreeWidgetItem
        self._eye_icon = None  # Cached eye icon
        self._setup_ui()
        self._connect_signals()
        self._create_eye_icon()

    def _setup_ui(self) -> None:
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Search/filter field
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Filter:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search nodes...")
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Type", ""])  # Third column for eye icon
        self.tree.setColumnWidth(0, 150)
        self.tree.setColumnWidth(1, 80)
        self.tree.setColumnWidth(2, 30)  # Small column for eye icon
        self.tree.setAlternatingRowColors(True)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.tree)

        # Stats label
        self.stats_label = QLabel("0 nodes")
        layout.addWidget(self.stats_label)

    def _connect_signals(self) -> None:
        """Connect to app state signals."""
        if self.app_state:
            self.app_state.graph_changed.connect(self.refresh_tree)
            self.app_state.current_graph_changed.connect(self.refresh_tree)
            self.app_state.node_selected.connect(self._on_external_selection)
            self.app_state.image_rendered.connect(self._on_image_rendered)

    def _create_eye_icon(self) -> None:
        """Create a simple eye icon programmatically."""
        # Create a 16x16 pixmap with an eye symbol
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw eye shape (simple ellipse with dot)
        painter.setPen(QColor("#4A90D9"))
        painter.setBrush(QColor("#4A90D9"))

        # Eye outline
        painter.drawEllipse(2, 5, 12, 6)

        # Pupil
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(6, 6, 4, 4)
        painter.setBrush(QColor("#2C3E50"))
        painter.drawEllipse(7, 7, 2, 2)

        painter.end()
        self._eye_icon = QIcon(pixmap)

    def _on_image_rendered(self, graph_id: str) -> None:
        """Handle when a graph's image is rendered - update eye icons."""
        self.refresh_tree()

    def refresh_tree(self) -> None:
        """Rebuild the tree from current graph and hierarchy."""
        self.tree.clear()
        self._node_items.clear()

        if not self.app_state:
            self.stats_label.setText("0 nodes")
            return

        hierarchy = self.app_state.hierarchy
        current_graph = hierarchy.current_graph

        if not current_graph:
            self.stats_label.setText("0 nodes")
            return

        # Add nodes from current graph
        for node in current_graph.nodes():
            item = self._create_node_item(node, hierarchy)
            self.tree.addTopLevelItem(item)
            self._node_items[node.id] = item

            # If node has child graph, add its nodes as children
            if node.child_graph_id:
                child_graph = hierarchy.get_graph(node.child_graph_id)
                if child_graph:
                    self._add_child_graph_nodes(item, child_graph, hierarchy)

        # Update stats
        total_nodes = sum(g.node_count for g in hierarchy.get_all_graphs())
        self.stats_label.setText(f"{current_graph.node_count} nodes (total: {total_nodes})")

        # Apply filter if any
        if self.search_input.text():
            self._apply_filter(self.search_input.text())

    def _create_node_item(self, node, hierarchy=None) -> QTreeWidgetItem:
        """Create a tree item for a node."""
        item = QTreeWidgetItem([node.name, node.node_type, ""])

        # Set color indicator
        color = QColor(node.color)
        item.setBackground(0, QBrush(color.lighter(170)))

        # Store node ID
        item.setData(0, Qt.ItemDataRole.UserRole, node.id)

        # Add expand indicator
        if node.is_expandable:
            if node.child_graph_id:
                item.setIcon(0, self._get_icon("expanded"))

                # Check if child graph has a rendered image
                if hierarchy:
                    child_graph = hierarchy.get_graph(node.child_graph_id)
                    if child_graph and child_graph.has_rendered_image():
                        item.setIcon(2, self._eye_icon)
                        # Store child graph ID for viewing the render
                        item.setData(2, Qt.ItemDataRole.UserRole, node.child_graph_id)
            else:
                item.setIcon(0, self._get_icon("expandable"))

        return item

    def _add_child_graph_nodes(self, parent_item: QTreeWidgetItem, child_graph, hierarchy) -> None:
        """Recursively add child graph nodes."""
        for node in child_graph.nodes():
            item = self._create_node_item(node, hierarchy)
            parent_item.addChild(item)
            self._node_items[node.id] = item

            # Recurse for nested children
            if node.child_graph_id:
                nested_graph = hierarchy.get_graph(node.child_graph_id)
                if nested_graph:
                    self._add_child_graph_nodes(item, nested_graph, hierarchy)

    def _get_icon(self, icon_type: str) -> QIcon:
        """Get an icon (placeholder - would use actual icons)."""
        # Return empty icon for now
        return QIcon()

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle item click."""
        # Check if clicking on eye icon column
        if column == 2:
            graph_id = item.data(2, Qt.ItemDataRole.UserRole)
            if graph_id:
                self._show_rendered_image(graph_id)
                return

        # Normal node selection
        node_id = item.data(0, Qt.ItemDataRole.UserRole)
        if node_id:
            self.node_selected.emit(node_id)
            if self.app_state:
                self.app_state.select_node(node_id)

    def _show_rendered_image(self, graph_id: str) -> None:
        """Show the rendered image for a graph."""
        if not self.app_state:
            return

        image_data = self.app_state.get_rendered_image(graph_id)
        if image_data:
            from ui.widgets.image_viewer import ImageViewerDialog
            graph = self.app_state.hierarchy.get_graph(graph_id)
            title = f"Rendered: {graph.name}" if graph else "Rendered Scene"
            dialog = ImageViewerDialog(self, image_data, title)
            dialog.exec()

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle item double-click for drill-down."""
        node_id = item.data(0, Qt.ItemDataRole.UserRole)
        if node_id:
            self.node_double_clicked.emit(node_id)
            if self.app_state:
                self.app_state.expand_node(node_id)

    def _on_external_selection(self, node_id: str) -> None:
        """Handle selection from outside (e.g., canvas)."""
        if node_id in self._node_items:
            self.tree.setCurrentItem(self._node_items[node_id])
        else:
            self.tree.clearSelection()

    def _on_search_changed(self, text: str) -> None:
        """Handle search text change."""
        self._apply_filter(text)

    def _apply_filter(self, text: str) -> None:
        """Filter tree items by search text."""
        text_lower = text.lower()

        def filter_item(item: QTreeWidgetItem) -> bool:
            """Returns True if item or any child matches."""
            name = item.text(0).lower()
            node_type = item.text(1).lower()
            matches = text_lower in name or text_lower in node_type

            # Check children
            child_matches = False
            for i in range(item.childCount()):
                if filter_item(item.child(i)):
                    child_matches = True

            # Show if matches or has matching children
            visible = matches or child_matches or not text
            item.setHidden(not visible)

            # Expand if has matching children
            if child_matches:
                item.setExpanded(True)

            return matches or child_matches

        # Apply to all top-level items
        for i in range(self.tree.topLevelItemCount()):
            filter_item(self.tree.topLevelItem(i))

    def select_node(self, node_id: str) -> None:
        """Select a node in the tree."""
        if node_id in self._node_items:
            item = self._node_items[node_id]
            self.tree.setCurrentItem(item)
            self.tree.scrollToItem(item)
