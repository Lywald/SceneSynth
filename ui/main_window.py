"""Main application window for SceneSynth."""
from PyQt6.QtWidgets import (
    QMainWindow, QDockWidget, QToolBar, QMenuBar,
    QMenu, QStatusBar, QWidget, QVBoxLayout, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence

from config import APP_NAME, APP_VERSION


class MainWindow(QMainWindow):
    """
    Main application window with dockable panels.

    Layout:
    +----------------------------------------------------------+
    | Menu Bar (File, Edit, View, Help)                        |
    +----------------------------------------------------------+
    | Toolbar (New, Open, Save, Undo, Redo, Generate)          |
    +----------------------------------------------------------+
    | Breadcrumb Bar                                           |
    +----------------------------------------------------------+
    |          |                              |                |
    | Node     |      Graph Canvas            | Prompt Panel   |
    | Tree     |      (Central)               | (Right Dock)   |
    | Sidebar  |                              |                |
    | (Left)   |                              +----------------+
    |          |                              | Node Inspector |
    |          |                              | (Right Dock)   |
    +----------+------------------------------+----------------+
    | Status Bar                                               |
    +----------------------------------------------------------+
    """

    def __init__(self, app_state=None):
        super().__init__()
        self.app_state = app_state
        self._setup_ui()
        self._create_menus()
        self._create_toolbar()
        self._create_statusbar()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the main UI layout."""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1400, 900)

        # Central widget - Graph Canvas (will be replaced with actual canvas)
        from ui.widgets.graph_canvas import GraphCanvas
        self.graph_canvas = GraphCanvas(self.app_state)
        self.setCentralWidget(self.graph_canvas)

        # Set canvas reference in app_state for screenshots
        if self.app_state:
            self.app_state.set_graph_canvas(self.graph_canvas)

        # Breadcrumb bar (toolbar at top)
        from ui.widgets.breadcrumb_bar import BreadcrumbBar
        self.breadcrumb_bar = BreadcrumbBar(self.app_state)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.breadcrumb_bar)

        # Left dock - Node Tree Sidebar
        self.node_tree_dock = QDockWidget("Node Tree", self)
        self.node_tree_dock.setMinimumWidth(200)
        from ui.widgets.node_tree import NodeTreeSidebar
        self.node_tree = NodeTreeSidebar(self.app_state)
        self.node_tree_dock.setWidget(self.node_tree)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.node_tree_dock)

        # Right dock - Prompt Panel
        self.prompt_dock = QDockWidget("AI Prompt", self)
        self.prompt_dock.setMinimumWidth(300)
        from ui.widgets.prompt_panel import PromptPanel
        self.prompt_panel = PromptPanel(self.app_state)
        self.prompt_dock.setWidget(self.prompt_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.prompt_dock)

        # Right dock - Node Inspector (below Prompt Panel)
        self.inspector_dock = QDockWidget("Node Inspector", self)
        from ui.widgets.node_inspector import NodeInspector
        self.node_inspector = NodeInspector(self.app_state)
        self.inspector_dock.setWidget(self.node_inspector)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.inspector_dock)

        # Stack docks vertically on the right
        self.splitDockWidget(self.prompt_dock, self.inspector_dock, Qt.Orientation.Vertical)

    def _create_menus(self) -> None:
        """Create the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_action = QAction("&New Project", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._on_new_project)
        file_menu.addAction(new_action)

        open_action = QAction("&Open Project...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._on_open_project)
        file_menu.addAction(open_action)

        save_action = QAction("&Save Project", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._on_save_project)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save Project &As...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self._on_save_project_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self._on_undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self._on_redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        api_key_action = QAction("&API Key Settings...", self)
        api_key_action.triggered.connect(self._on_api_key_settings)
        edit_menu.addAction(api_key_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        view_menu.addAction(self.node_tree_dock.toggleViewAction())
        view_menu.addAction(self.prompt_dock.toggleViewAction())
        view_menu.addAction(self.inspector_dock.toggleViewAction())

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _create_toolbar(self) -> None:
        """Create the main toolbar."""
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Add toolbar actions
        new_btn = QAction("New", self)
        new_btn.triggered.connect(self._on_new_project)
        toolbar.addAction(new_btn)

        open_btn = QAction("Open", self)
        open_btn.triggered.connect(self._on_open_project)
        toolbar.addAction(open_btn)

        save_btn = QAction("Save", self)
        save_btn.triggered.connect(self._on_save_project)
        toolbar.addAction(save_btn)

        toolbar.addSeparator()

        undo_btn = QAction("Undo", self)
        undo_btn.triggered.connect(self._on_undo)
        toolbar.addAction(undo_btn)

        redo_btn = QAction("Redo", self)
        redo_btn.triggered.connect(self._on_redo)
        toolbar.addAction(redo_btn)

        toolbar.addSeparator()

        generate_btn = QAction("Generate", self)
        generate_btn.triggered.connect(self._on_generate)
        toolbar.addAction(generate_btn)

        render_btn = QAction("Render Scene", self)
        render_btn.triggered.connect(self._on_render)
        toolbar.addAction(render_btn)

        view_render_btn = QAction("View Render", self)
        view_render_btn.triggered.connect(self._on_view_render)
        toolbar.addAction(view_render_btn)

    def _create_statusbar(self) -> None:
        """Create the status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready")

    def _connect_signals(self) -> None:
        """Connect signals from app state."""
        if self.app_state:
            self.app_state.loading_started.connect(self._on_loading_started)
            self.app_state.loading_finished.connect(self._on_loading_finished)
            self.app_state.error_occurred.connect(self._on_error)

    # ==================== Slots ====================

    def _on_new_project(self) -> None:
        """Handle new project action."""
        self.statusbar.showMessage("New project...")
        if self.app_state:
            self.app_state.new_project()

    def _on_open_project(self) -> None:
        """Handle open project action."""
        from PyQt6.QtWidgets import QFileDialog
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "SceneSynth Projects (*.scenesynth);;All Files (*)"
        )
        if filepath and self.app_state:
            self.app_state.load_project(filepath)
            self.statusbar.showMessage(f"Opened: {filepath}")

    def _on_save_project(self) -> None:
        """Handle save project action."""
        if self.app_state and self.app_state.project_path:
            self.app_state.save_project(self.app_state.project_path)
            self.statusbar.showMessage("Project saved")
        else:
            self._on_save_project_as()

    def _on_save_project_as(self) -> None:
        """Handle save project as action."""
        from PyQt6.QtWidgets import QFileDialog
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "", "SceneSynth Projects (*.scenesynth);;All Files (*)"
        )
        if filepath and self.app_state:
            if not filepath.endswith('.scenesynth'):
                filepath += '.scenesynth'
            self.app_state.save_project(filepath)
            self.statusbar.showMessage(f"Saved: {filepath}")

    def _on_undo(self) -> None:
        """Handle undo action."""
        if self.app_state:
            self.app_state.undo()

    def _on_redo(self) -> None:
        """Handle redo action."""
        if self.app_state:
            self.app_state.redo()

    def _on_api_key_settings(self) -> None:
        """Handle API key settings action."""
        from ui.widgets.api_key_dialog import ApiKeyDialog
        dialog = ApiKeyDialog(self, self.app_state)
        dialog.exec()

    def _on_about(self) -> None:
        """Handle about action."""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"{APP_NAME} v{APP_VERSION}\n\n"
            "A hierarchical semantic scene graph generator\n"
            "for 2D level design.\n\n"
            "Uses AI to generate and modify scene graphs\n"
            "with natural language prompts."
        )

    def _on_generate(self) -> None:
        """Handle generate button click."""
        # Trigger generation from prompt panel
        self.prompt_panel.trigger_generate()

    def _on_loading_started(self, message: str) -> None:
        """Handle loading started."""
        self.statusbar.showMessage(message)
        self.setCursor(Qt.CursorShape.WaitCursor)

    def _on_loading_finished(self) -> None:
        """Handle loading finished."""
        self.statusbar.showMessage("Ready")
        self.unsetCursor()

    def _on_error(self, message: str) -> None:
        """Handle error."""
        self.statusbar.showMessage(f"Error: {message}")
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "Error", message)

    def _on_render(self) -> None:
        """Handle render button click."""
        if self.app_state:
            from ui.widgets.render_dialog import RenderDialog
            style, accepted = RenderDialog.get_render_style(self)
            if accepted:
                self.app_state.render_scene(style=style)

    def _on_view_render(self) -> None:
        """Handle view render button click."""
        if self.app_state:
            image_data = self.app_state.get_rendered_image()
            if image_data:
                from ui.widgets.image_viewer import ImageViewerDialog
                graph_name = self.app_state.current_graph.name if self.app_state.current_graph else "Scene"
                dialog = ImageViewerDialog(self, image_data, f"Rendered: {graph_name}")
                dialog.exec()
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(
                    self, "No Render",
                    "No rendered image available for the current graph.\n"
                    "Click 'Render Scene' to generate one."
                )
