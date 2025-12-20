"""GraphNodeItem - Visual representation of a SceneNode."""
from PyQt6.QtWidgets import (
    QGraphicsEllipseItem, QGraphicsTextItem,
    QGraphicsDropShadowEffect, QGraphicsItem
)
from PyQt6.QtCore import Qt, QRectF, QPointF, QTimer
from PyQt6.QtGui import QBrush, QPen, QColor, QFont, QPainter

from config import NODE_BASE_RADIUS


class GraphNodeItem(QGraphicsEllipseItem):
    """
    Visual representation of a SceneNode.

    Supports:
    - Drag to move
    - Click to select
    - Double-click to expand/drill-down
    - Visual indicators for expandable nodes
    """

    def __init__(self, node, canvas=None):
        self.node = node
        self.canvas = canvas

        # Calculate radius based on node size
        radius = NODE_BASE_RADIUS * node.size
        super().__init__(-radius, -radius, radius * 2, radius * 2)

        self.setPos(node.x, node.y)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        self._is_hovered = False
        self._setup_appearance()
        self._create_label()
        self._add_expand_indicator()

    def _setup_appearance(self) -> None:
        """Set up the visual appearance of the node."""
        color = QColor(self.node.color)
        self.setBrush(QBrush(color))
        self.setPen(QPen(color.darker(120), 2))

        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(3, 3)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

    def _create_label(self) -> None:
        """Create the node label."""
        self.label = QGraphicsTextItem(self.node.name, self)
        self.label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.label.setDefaultTextColor(QColor("#333333"))

        # Center label below node
        rect = self.label.boundingRect()
        radius = NODE_BASE_RADIUS * self.node.size
        self.label.setPos(-rect.width() / 2, radius + 5)

    def _add_expand_indicator(self) -> None:
        """Add visual indicator for expandable nodes."""
        if self.node.is_expandable:
            if self.node.child_graph_id:
                # Has child - show drill-down indicator
                self.indicator = QGraphicsTextItem("+", self)
            else:
                # Can expand - show expand indicator
                self.indicator = QGraphicsTextItem("+", self)

            self.indicator.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            self.indicator.setDefaultTextColor(QColor("#FFFFFF"))

            # Position in bottom-right of node
            radius = NODE_BASE_RADIUS * self.node.size
            self.indicator.setPos(radius - 15, radius - 20)
        else:
            self.indicator = None

    def update_from_node(self) -> None:
        """Update the visual representation from the node data."""
        radius = NODE_BASE_RADIUS * self.node.size
        self.setRect(-radius, -radius, radius * 2, radius * 2)
        self.setPos(self.node.x, self.node.y)

        color = QColor(self.node.color)
        self.setBrush(QBrush(color))
        self.setPen(QPen(color.darker(120), 2))

        self.label.setPlainText(self.node.name)
        rect = self.label.boundingRect()
        self.label.setPos(-rect.width() / 2, radius + 5)

    def itemChange(self, change, value):
        """Handle item changes."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Update node position
            pos = self.pos()
            self.node.x = pos.x()
            self.node.y = pos.y()

            # Notify canvas to update edges
            if self.canvas:
                self.canvas.update_edges_for_node(self.node.id)

        return super().itemChange(change, value)

    def hoverEnterEvent(self, event) -> None:
        """Handle hover enter."""
        self._is_hovered = True
        self.setPen(QPen(QColor(self.node.color).lighter(120), 3))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        """Handle hover leave."""
        self._is_hovered = False
        self.setPen(QPen(QColor(self.node.color).darker(120), 2))
        self.unsetCursor()
        super().hoverLeaveEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        """Handle double-click for drill-down."""
        if self.canvas:
            # Defer signal emission to avoid deleting self during event handling
            node_id = self.node.id
            QTimer.singleShot(0, lambda: self.canvas.node_double_clicked.emit(node_id))
        # Don't call super - it can cause issues after deferred deletion

    def mousePressEvent(self, event) -> None:
        """Handle mouse press for selection."""
        if self.canvas:
            self.canvas.node_clicked.emit(self.node.id)
        super().mousePressEvent(event)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        """Custom paint for selection highlighting."""
        # Draw selection ring if selected
        if self.isSelected():
            radius = NODE_BASE_RADIUS * self.node.size
            painter.setPen(QPen(QColor("#FFD700"), 3, Qt.PenStyle.DashLine))
            painter.drawEllipse(QRectF(-radius - 5, -radius - 5, (radius + 5) * 2, (radius + 5) * 2))

        super().paint(painter, option, widget)
