"""GraphEdgeItem - Visual representation of a SceneEdge."""
from PyQt6.QtWidgets import QGraphicsLineItem, QGraphicsTextItem
from PyQt6.QtCore import Qt, QPointF, QLineF
from PyQt6.QtGui import QPen, QColor, QFont, QPainter, QPainterPath

from config import NODE_BASE_RADIUS


class GraphEdgeItem(QGraphicsLineItem):
    """
    Visual representation of a SceneEdge connecting two nodes.
    """

    def __init__(self, edge, get_node_position_func):
        super().__init__()
        self.edge = edge
        self._get_node_position = get_node_position_func

        self._setup_appearance()
        self._create_label()
        self.update_position()

    def _setup_appearance(self) -> None:
        """Set up the visual appearance of the edge."""
        color = QColor(self.edge.color)
        pen = QPen(color, self.edge.thickness)

        # Set line style
        if self.edge.style == "dashed":
            pen.setStyle(Qt.PenStyle.DashLine)
        elif self.edge.style == "dotted":
            pen.setStyle(Qt.PenStyle.DotLine)
        else:
            pen.setStyle(Qt.PenStyle.SolidLine)

        self.setPen(pen)
        self.setZValue(-1)  # Draw edges behind nodes

    def _create_label(self) -> None:
        """Create the edge label if present."""
        if self.edge.label:
            self.label = QGraphicsTextItem(self.edge.label, self)
            self.label.setFont(QFont("Segoe UI", 8))
            self.label.setDefaultTextColor(QColor("#666666"))
        else:
            self.label = None

    def update_position(self) -> None:
        """Update the edge position based on connected nodes."""
        source_pos = self._get_node_position(self.edge.source_id)
        target_pos = self._get_node_position(self.edge.target_id)

        if source_pos is None or target_pos is None:
            return

        # Calculate line endpoints (offset from node centers)
        line = QLineF(source_pos, target_pos)

        # Shorten line to not overlap with nodes
        if line.length() > 0:
            # Get node sizes for proper offset
            source_offset = NODE_BASE_RADIUS * 1.2  # Default size
            target_offset = NODE_BASE_RADIUS * 1.2

            # Shorten from source
            line.setLength(line.length() - source_offset)
            start = line.p2()

            # Shorten from target (reverse and shorten)
            line = QLineF(target_pos, source_pos)
            line.setLength(line.length() - target_offset)
            end = line.p2()

            self.setLine(QLineF(start, end))
        else:
            self.setLine(line)

        # Update label position
        if self.label:
            midpoint = QPointF(
                (source_pos.x() + target_pos.x()) / 2,
                (source_pos.y() + target_pos.y()) / 2
            )
            rect = self.label.boundingRect()
            self.label.setPos(midpoint.x() - rect.width() / 2, midpoint.y() - rect.height() / 2)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        """Custom paint with optional arrow for directed edges."""
        super().paint(painter, option, widget)

        # Draw arrow if not bidirectional
        if not self.edge.is_bidirectional:
            self._draw_arrow(painter)

    def _draw_arrow(self, painter: QPainter) -> None:
        """Draw an arrow at the target end of the edge."""
        line = self.line()
        if line.length() == 0:
            return

        # Arrow properties
        arrow_size = 10

        # Calculate arrow direction
        angle = line.angle()
        p1 = line.p2()

        # Calculate arrow points
        import math
        rad = math.radians(angle)
        p2 = QPointF(
            p1.x() - arrow_size * math.cos(rad - math.pi / 6),
            p1.y() + arrow_size * math.sin(rad - math.pi / 6)
        )
        p3 = QPointF(
            p1.x() - arrow_size * math.cos(rad + math.pi / 6),
            p1.y() + arrow_size * math.sin(rad + math.pi / 6)
        )

        # Draw arrow
        path = QPainterPath()
        path.moveTo(p1)
        path.lineTo(p2)
        path.lineTo(p3)
        path.closeSubpath()

        painter.setBrush(self.pen().color())
        painter.drawPath(path)
