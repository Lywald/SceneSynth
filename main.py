"""SceneSynth AI - Main entry point."""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from core.state import AppState
from ui.main_window import MainWindow
from config import APP_NAME


def main():
    """Main entry point for SceneSynth AI."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")

    # Create app state
    app_state = AppState()

    # Create initial empty project
    app_state.new_project()

    # Create and show main window
    window = MainWindow(app_state)
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
