"""BreadcrumbBar - Navigation bar for graph hierarchy."""
from PyQt6.QtWidgets import QToolBar, QPushButton, QLabel, QWidget, QHBoxLayout
from PyQt6.QtCore import Qt


class BreadcrumbBar(QToolBar):
    """
    Navigation bar showing current depth in the hierarchy.

    Example: World > Baldur's Gate > City Entrance > House

    Clicking any breadcrumb navigates to that level.
    """

    def __init__(self, app_state=None):
        super().__init__("Navigation")
        self.app_state = app_state
        self.setMovable(False)

        self._breadcrumb_buttons = []
        self._separators = []

        # Home button
        self.home_btn = QPushButton("Home")
        self.home_btn.setFlat(True)
        self.home_btn.clicked.connect(self._on_home)
        self.addWidget(self.home_btn)

        # Up button
        self.up_btn = QPushButton("Up")
        self.up_btn.setFlat(True)
        self.up_btn.setToolTip("Go to parent graph")
        self.up_btn.clicked.connect(self._on_up)
        self.addWidget(self.up_btn)

        self.addSeparator()

        # Breadcrumb container
        self.breadcrumb_widget = QWidget()
        self.breadcrumb_layout = QHBoxLayout(self.breadcrumb_widget)
        self.breadcrumb_layout.setContentsMargins(0, 0, 0, 0)
        self.breadcrumb_layout.setSpacing(0)
        self.addWidget(self.breadcrumb_widget)

        self._connect_signals()
        self._refresh_breadcrumbs()

    def _connect_signals(self) -> None:
        """Connect to app state signals."""
        if self.app_state:
            self.app_state.current_graph_changed.connect(self._refresh_breadcrumbs)

    def _refresh_breadcrumbs(self) -> None:
        """Rebuild breadcrumb trail from current navigation state."""
        # Clear existing
        for btn in self._breadcrumb_buttons:
            self.breadcrumb_layout.removeWidget(btn)
            btn.deleteLater()
        for sep in self._separators:
            self.breadcrumb_layout.removeWidget(sep)
            sep.deleteLater()

        self._breadcrumb_buttons.clear()
        self._separators.clear()

        if not self.app_state:
            return

        hierarchy = self.app_state.hierarchy
        path = hierarchy.get_breadcrumb_path()

        # Update home/up buttons
        self.up_btn.setEnabled(len(path) > 1)

        # Build breadcrumbs
        for i, (graph_id, name) in enumerate(path):
            if i > 0:
                sep = QLabel(" > ")
                sep.setStyleSheet("color: #888;")
                self._separators.append(sep)
                self.breadcrumb_layout.addWidget(sep)

            btn = QPushButton(name)
            btn.setFlat(True)

            # Store graph_id for navigation
            btn.setProperty("graph_id", graph_id)
            btn.clicked.connect(lambda checked, gid=graph_id: self._navigate_to(gid))

            # Style current level differently
            current_id = hierarchy._current_graph_id
            if graph_id == current_id:
                btn.setStyleSheet("font-weight: bold; color: #2196F3;")
            else:
                btn.setStyleSheet("color: #333;")
                btn.setCursor(Qt.CursorShape.PointingHandCursor)

            self._breadcrumb_buttons.append(btn)
            self.breadcrumb_layout.addWidget(btn)

        # Add stretch at the end
        self.breadcrumb_layout.addStretch()

    def _navigate_to(self, graph_id: str) -> None:
        """Navigate to a specific graph."""
        if self.app_state:
            self.app_state.navigate_to_graph(graph_id)

    def _on_home(self) -> None:
        """Navigate to root graph."""
        if self.app_state:
            self.app_state.navigate_to_root()

    def _on_up(self) -> None:
        """Navigate to parent graph."""
        if self.app_state:
            self.app_state.navigate_up()
