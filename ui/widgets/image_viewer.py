"""Image viewer dialog for rendered scenes."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QScrollArea, QFileDialog, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage


class ImageViewerDialog(QDialog):
    """Dialog to display rendered scene images."""

    def __init__(self, parent=None, image_data: bytes = None, title: str = "Rendered Scene"):
        super().__init__(parent)
        self.image_data = image_data
        self._setup_ui(title)
        if image_data:
            self._load_image(image_data)

    def _setup_ui(self, title: str) -> None:
        """Set up the UI."""
        self.setWindowTitle(title)
        self.setMinimumSize(600, 500)
        self.resize(800, 700)

        layout = QVBoxLayout(self)

        # Scroll area for the image
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.image_label.setScaledContents(False)

        self.scroll_area.setWidget(self.image_label)
        layout.addWidget(self.scroll_area)

        # Buttons
        btn_layout = QHBoxLayout()

        self.zoom_in_btn = QPushButton("Zoom In")
        self.zoom_in_btn.clicked.connect(self._zoom_in)
        btn_layout.addWidget(self.zoom_in_btn)

        self.zoom_out_btn = QPushButton("Zoom Out")
        self.zoom_out_btn.clicked.connect(self._zoom_out)
        btn_layout.addWidget(self.zoom_out_btn)

        self.fit_btn = QPushButton("Fit to Window")
        self.fit_btn.clicked.connect(self._fit_to_window)
        btn_layout.addWidget(self.fit_btn)

        btn_layout.addStretch()

        self.save_btn = QPushButton("Save Image...")
        self.save_btn.clicked.connect(self._save_image)
        btn_layout.addWidget(self.save_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

        self._scale_factor = 1.0
        self._pixmap = None

    def _load_image(self, image_data: bytes) -> None:
        """Load image from bytes."""
        qimage = QImage()
        qimage.loadFromData(image_data)

        if qimage.isNull():
            self.image_label.setText("Failed to load image")
            return

        self._pixmap = QPixmap.fromImage(qimage)
        self._scale_factor = 1.0
        self._update_image()
        self._fit_to_window()

    def _update_image(self) -> None:
        """Update the displayed image with current scale."""
        if self._pixmap:
            scaled = self._pixmap.scaled(
                int(self._pixmap.width() * self._scale_factor),
                int(self._pixmap.height() * self._scale_factor),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)
            self.image_label.adjustSize()

    def _zoom_in(self) -> None:
        """Zoom in."""
        self._scale_factor *= 1.25
        self._update_image()

    def _zoom_out(self) -> None:
        """Zoom out."""
        self._scale_factor *= 0.8
        self._update_image()

    def _fit_to_window(self) -> None:
        """Fit image to window size."""
        if not self._pixmap:
            return

        # Calculate scale to fit
        viewport_size = self.scroll_area.viewport().size()
        img_size = self._pixmap.size()

        scale_w = viewport_size.width() / img_size.width()
        scale_h = viewport_size.height() / img_size.height()
        self._scale_factor = min(scale_w, scale_h) * 0.95  # 95% to add margin

        self._update_image()

    def _save_image(self) -> None:
        """Save the image to a file."""
        if not self.image_data:
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Image",
            "rendered_scene.png",
            "PNG Images (*.png);;JPEG Images (*.jpg);;All Files (*)"
        )

        if filepath:
            with open(filepath, 'wb') as f:
                f.write(self.image_data)

    def set_image(self, image_data: bytes) -> None:
        """Set new image data."""
        self.image_data = image_data
        self._load_image(image_data)
