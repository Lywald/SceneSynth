"""NodeInspector - Node property editor with JSON view."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QTextEdit, QComboBox, QPushButton, QColorDialog,
    QTabWidget, QLabel, QHBoxLayout, QSpinBox, QDoubleSpinBox,
    QCheckBox, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from config import NODE_TYPES, NODE_COLORS


class NodeInspector(QWidget):
    """
    Panel showing details of the selected node.

    Features:
    - Property editor for selected node
    - JSON tab: Display raw JSON of selected node
    - Graph JSON tab: Display full current graph JSON
    - Copy JSON to clipboard button
    """

    def __init__(self, app_state=None):
        super().__init__()
        self.app_state = app_state
        self._current_node_id = None
        self._updating = False  # Prevent recursive updates
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # No selection message
        self.no_selection_widget = QWidget()
        no_sel_layout = QVBoxLayout(self.no_selection_widget)
        self.no_selection_label = QLabel("Select a node to view details")
        self.no_selection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_selection_label.setStyleSheet("color: #888;")
        no_sel_layout.addWidget(self.no_selection_label)
        layout.addWidget(self.no_selection_widget)

        # Tab widget for properties and JSON
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Properties tab
        self.properties_widget = QWidget()
        self._setup_properties_tab()
        self.tab_widget.addTab(self.properties_widget, "Properties")

        # Node JSON tab
        self.node_json_widget = QWidget()
        self._setup_node_json_tab()
        self.tab_widget.addTab(self.node_json_widget, "Node JSON")

        # Graph JSON tab
        self.graph_json_widget = QWidget()
        self._setup_graph_json_tab()
        self.tab_widget.addTab(self.graph_json_widget, "Graph JSON")

        # Initially hide tab widget
        self.tab_widget.hide()

    def _setup_properties_tab(self) -> None:
        """Set up the properties editing tab."""
        layout = QVBoxLayout(self.properties_widget)
        form = QFormLayout()

        # Name
        self.name_edit = QLineEdit()
        self.name_edit.editingFinished.connect(self._on_name_changed)
        form.addRow("Name:", self.name_edit)

        # Type
        self.type_combo = QComboBox()
        self.type_combo.addItems(NODE_TYPES)
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        form.addRow("Type:", self.type_combo)

        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.textChanged.connect(self._on_description_changed)
        form.addRow("Description:", self.description_edit)

        # Size
        self.size_spin = QDoubleSpinBox()
        self.size_spin.setRange(0.5, 2.0)
        self.size_spin.setSingleStep(0.1)
        self.size_spin.setValue(1.0)
        self.size_spin.valueChanged.connect(self._on_size_changed)
        form.addRow("Size:", self.size_spin)

        # Expandable
        self.expandable_check = QCheckBox("Can be expanded (drill-down)")
        self.expandable_check.stateChanged.connect(self._on_expandable_changed)
        form.addRow("", self.expandable_check)

        # Color
        color_layout = QHBoxLayout()
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(50, 25)
        self.color_btn.clicked.connect(self._on_color_clicked)
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch()
        form.addRow("Color:", color_layout)

        layout.addLayout(form)

        # Actions
        layout.addSpacing(10)
        actions_label = QLabel("Actions:")
        actions_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(actions_label)

        self.expand_btn = QPushButton("Expand Node (Drill Down)")
        self.expand_btn.clicked.connect(self._on_expand)
        layout.addWidget(self.expand_btn)

        self.delete_btn = QPushButton("Delete Node")
        self.delete_btn.setStyleSheet("background-color: #ffcccc;")
        self.delete_btn.clicked.connect(self._on_delete)
        layout.addWidget(self.delete_btn)

        layout.addStretch()

    def _setup_node_json_tab(self) -> None:
        """Set up the node JSON display tab."""
        layout = QVBoxLayout(self.node_json_widget)

        # JSON display
        self.node_json_text = QTextEdit()
        self.node_json_text.setReadOnly(True)
        self.node_json_text.setStyleSheet(
            "font-family: 'Consolas', 'Courier New', monospace; font-size: 11px;"
        )
        layout.addWidget(self.node_json_text)

        # Copy button
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(lambda: self._copy_to_clipboard(self.node_json_text.toPlainText()))
        layout.addWidget(copy_btn)

    def _setup_graph_json_tab(self) -> None:
        """Set up the graph JSON display tab."""
        layout = QVBoxLayout(self.graph_json_widget)

        # JSON display
        self.graph_json_text = QTextEdit()
        self.graph_json_text.setReadOnly(True)
        self.graph_json_text.setStyleSheet(
            "font-family: 'Consolas', 'Courier New', monospace; font-size: 11px;"
        )
        layout.addWidget(self.graph_json_text)

        # Copy button
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(lambda: self._copy_to_clipboard(self.graph_json_text.toPlainText()))
        layout.addWidget(copy_btn)

    def _connect_signals(self) -> None:
        """Connect to app state signals."""
        if self.app_state:
            self.app_state.node_selected.connect(self._on_node_selected)
            self.app_state.graph_changed.connect(self._refresh_json)

    def _on_node_selected(self, node_id: str) -> None:
        """Handle node selection."""
        if not node_id:
            self._show_no_selection()
            self._current_node_id = None
            return

        self._current_node_id = node_id
        node = self._get_current_node()

        if not node:
            self._show_no_selection()
            return

        self._show_properties()
        self._populate_from_node(node)
        self._refresh_json()

    def _get_current_node(self):
        """Get the currently selected node."""
        if not self.app_state or not self._current_node_id:
            return None
        if not self.app_state.current_graph:
            return None
        return self.app_state.current_graph.get_node(self._current_node_id)

    def _show_no_selection(self) -> None:
        """Show the no selection state."""
        self.no_selection_widget.show()
        self.tab_widget.hide()

    def _show_properties(self) -> None:
        """Show the properties panel."""
        self.no_selection_widget.hide()
        self.tab_widget.show()

    def _populate_from_node(self, node) -> None:
        """Populate fields from node data."""
        self._updating = True

        self.name_edit.setText(node.name)
        self.type_combo.setCurrentText(node.node_type)
        self.description_edit.setPlainText(node.description)
        self.size_spin.setValue(node.size)
        self.expandable_check.setChecked(node.is_expandable)

        # Color button
        self.color_btn.setStyleSheet(f"background-color: {node.color};")

        # Update expand button text
        if node.child_graph_id:
            self.expand_btn.setText("Go to Child Graph")
        else:
            self.expand_btn.setText("Expand Node (Drill Down)")
            self.expand_btn.setEnabled(node.is_expandable)

        self._updating = False

    def _refresh_json(self) -> None:
        """Refresh the JSON displays."""
        # Node JSON
        node = self._get_current_node()
        if node:
            self.node_json_text.setPlainText(node.to_json())
        else:
            self.node_json_text.clear()

        # Graph JSON
        if self.app_state and self.app_state.current_graph:
            self.graph_json_text.setPlainText(self.app_state.current_graph.to_json())
        else:
            self.graph_json_text.clear()

    def _copy_to_clipboard(self, text: str) -> None:
        """Copy text to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    # ==================== Property Change Handlers ====================

    def _on_name_changed(self) -> None:
        """Handle name change."""
        if self._updating:
            return
        node = self._get_current_node()
        if node and self.app_state:
            self.app_state.update_node(node.id, name=self.name_edit.text())

    def _on_type_changed(self, new_type: str) -> None:
        """Handle type change."""
        if self._updating:
            return
        node = self._get_current_node()
        if node and self.app_state:
            # Update color to match type
            new_color = NODE_COLORS.get(new_type, node.color)
            self.app_state.update_node(node.id, node_type=new_type, color=new_color)
            self.color_btn.setStyleSheet(f"background-color: {new_color};")

    def _on_description_changed(self) -> None:
        """Handle description change."""
        if self._updating:
            return
        node = self._get_current_node()
        if node and self.app_state:
            self.app_state.update_node(node.id, description=self.description_edit.toPlainText())

    def _on_size_changed(self, value: float) -> None:
        """Handle size change."""
        if self._updating:
            return
        node = self._get_current_node()
        if node and self.app_state:
            self.app_state.update_node(node.id, size=value)

    def _on_expandable_changed(self, state: int) -> None:
        """Handle expandable change."""
        if self._updating:
            return
        node = self._get_current_node()
        if node and self.app_state:
            self.app_state.update_node(node.id, is_expandable=state == Qt.CheckState.Checked.value)

    def _on_color_clicked(self) -> None:
        """Handle color button click."""
        node = self._get_current_node()
        if not node:
            return

        color = QColorDialog.getColor(QColor(node.color), self, "Choose Node Color")
        if color.isValid() and self.app_state:
            self.app_state.update_node(node.id, color=color.name())
            self.color_btn.setStyleSheet(f"background-color: {color.name()};")

    def _on_expand(self) -> None:
        """Handle expand button click."""
        node = self._get_current_node()
        if node and self.app_state:
            self.app_state.expand_node(node.id)

    def _on_delete(self) -> None:
        """Handle delete button click."""
        node = self._get_current_node()
        if node and self.app_state:
            self.app_state.delete_node(node.id)
