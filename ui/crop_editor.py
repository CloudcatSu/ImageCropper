from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGraphicsView, 
    QGraphicsScene, QGraphicsObject, QLabel, QSlider
)
from PySide6.QtCore import Qt, QRectF, Signal, QPointF
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QCursor, QPainterPath
import os

class CropOverlay(QGraphicsObject):
    rectChanged = Signal(QRectF)
    
    def __init__(self, scene_rect, parent=None):
        super().__init__(parent)
        self.scene_rect = scene_rect
        
        # Initial crop rect (centered, 80% size)
        w, h = scene_rect.width(), scene_rect.height()
        self.crop_rect = QRectF(w * 0.1, h * 0.1, w * 0.8, h * 0.8)
        
        self.handle_size = 20
        self.edge_handle_size = 30
        self.current_action = None # 'tl', 'tr', 'bl', 'br', 't', 'b', 'l', 'r', 'move'
        self.drag_offset = QPointF()
        
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)

    def boundingRect(self):
        return self.scene_rect

    def paint(self, painter, option, widget):
        # Draw 50% black mask over the entire scene, except crop_rect
        painter.setBrush(QColor(0, 0, 0, 128))
        painter.setPen(Qt.PenStyle.NoPen)
        
        full_path = QPainterPath()
        full_path.addRect(self.scene_rect)
        
        crop_path = QPainterPath()
        crop_path.addRect(self.crop_rect)
        
        mask_path = full_path.subtracted(crop_path)
        painter.drawPath(mask_path)
        
        # Draw crop rect border
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self.crop_rect)
        
        # Draw handles
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Corners
        corners = self.get_corner_rects()
        for c in corners.values():
            painter.drawRect(c)
            
        # Edges (vertical/horizontal bars)
        painter.setPen(QPen(QColor(255, 255, 255), 20))
        ehs = self.edge_handle_size
        
        cx = self.crop_rect.center().x()
        cy = self.crop_rect.center().y()
        
        # top line
        painter.drawLine(cx - ehs, self.crop_rect.top(), cx + ehs, self.crop_rect.top())
        # bottom line
        painter.drawLine(cx - ehs, self.crop_rect.bottom(), cx + ehs, self.crop_rect.bottom())
        # left line (vertical)
        painter.drawLine(self.crop_rect.left(), cy - ehs, self.crop_rect.left(), cy + ehs)
        # right line (vertical)
        painter.drawLine(self.crop_rect.right(), cy - ehs, self.crop_rect.right(), cy + ehs)

    def get_corner_rects(self):
        hs = self.handle_size
        r = self.crop_rect
        return {
            'tl': QRectF(r.left() - hs/2, r.top() - hs/2, hs, hs),
            'tr': QRectF(r.right() - hs/2, r.top() - hs/2, hs, hs),
            'bl': QRectF(r.left() - hs/2, r.bottom() - hs/2, hs, hs),
            'br': QRectF(r.right() - hs/2, r.bottom() - hs/2, hs, hs)
        }

    def get_edge_rects(self):
        r = self.crop_rect
        hs = self.handle_size
        return {
            't': QRectF(r.left() + hs, r.top() - hs, r.width() - 2*hs, 2*hs),
            'b': QRectF(r.left() + hs, r.bottom() - hs, r.width() - 2*hs, 2*hs),
            'l': QRectF(r.left() - hs, r.top() + hs, 2*hs, r.height() - 2*hs),
            'r': QRectF(r.right() - hs, r.top() + hs, 2*hs, r.height() - 2*hs)
        }

    def hoverMoveEvent(self, event):
        pos = event.pos()
        action = self.get_action_at(pos)
        
        if action in ['tl', 'br']:
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif action in ['tr', 'bl']:
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif action in ['t', 'b']:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        elif action in ['l', 'r']:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif action == 'move':
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        pos = event.pos()
        self.current_action = self.get_action_at(pos)
        
        if self.current_action == 'move':
            self.drag_offset = pos - self.crop_rect.topLeft()
        
        if self.current_action:
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self.current_action:
            super().mouseMoveEvent(event)
            return

        pos = event.pos()
        r = self.crop_rect

        MIN_SIZE = 50

        if self.current_action == 'move':
            new_top_left = pos - self.drag_offset
            x = max(0, min(new_top_left.x(), self.scene_rect.width() - r.width()))
            y = max(0, min(new_top_left.y(), self.scene_rect.height() - r.height()))
            r.moveTo(x, y)
        else:
            if 't' in self.current_action:
                new_top = min(pos.y(), r.bottom() - MIN_SIZE)
                r.setTop(max(0, new_top))
            if 'b' in self.current_action:
                new_bottom = max(pos.y(), r.top() + MIN_SIZE)
                r.setBottom(min(self.scene_rect.height(), new_bottom))
            if 'l' in self.current_action:
                new_left = min(pos.x(), r.right() - MIN_SIZE)
                r.setLeft(max(0, new_left))
            if 'r' in self.current_action:
                new_right = max(pos.x(), r.left() + MIN_SIZE)
                r.setRight(min(self.scene_rect.width(), new_right))

        self.crop_rect = r
        self.update()
        self.rectChanged.emit(self.crop_rect)

    def mouseReleaseEvent(self, event):
        self.current_action = None
        super().mouseReleaseEvent(event)

    def get_action_at(self, pos):
        for key, rect in self.get_corner_rects().items():
            if rect.contains(pos):
                return key
        for key, rect in self.get_edge_rects().items():
            if rect.contains(pos):
                return key
        if self.crop_rect.contains(pos):
            return 'move'
        return None


class CropEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.files = []
        self.current_pixmap = None
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QHBoxLayout()
        header.setContentsMargins(10, 10, 10, 10)
        self.back_btn = QPushButton("返回 (Back)")
        self.back_btn.setFixedSize(100, 40)
        
        self.title_label = QLabel("第一張圖片作為範例")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(5, 20)
        self.zoom_slider.setValue(10)
        self.zoom_slider.setFixedWidth(150)
        self.zoom_label = QLabel("1.0x")
        self.zoom_slider.valueChanged.connect(self.apply_zoom)
        
        self.confirm_btn = QPushButton("確定裁切 (Confirm)")
        self.confirm_btn.setFixedSize(150, 40)
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        header.addWidget(self.back_btn)
        header.addWidget(self.title_label, 1)
        header.addWidget(QLabel("縮放:"))
        header.addWidget(self.zoom_slider)
        header.addWidget(self.zoom_label)
        header.addWidget(self.confirm_btn)
        
        layout.addLayout(header)
        
        # Graphics View
        self.view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        
        # Styling
        self.view.setStyleSheet("border: none; background-color: #222;")
        
        # Allow scrollbars for zooming
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        layout.addWidget(self.view)
        
        self.pixmap_item = None
        self.overlay = None

    def load_images(self, files):
        self.files = files
        if not files:
            return
            
        first_file = files[0]
        self.current_pixmap = QPixmap(first_file)
        
        self.scene.clear()
        
        self.pixmap_item = self.scene.addPixmap(self.current_pixmap)
        
        # Add overlay
        self.overlay = CropOverlay(self.pixmap_item.boundingRect())
        self.scene.addItem(self.overlay)
        
        # Fit view
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(10)
        self.zoom_label.setText("1.0x")
        self.zoom_slider.blockSignals(False)
        self.apply_zoom()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.apply_zoom()
        
    def apply_zoom(self, _=None):
        if not self.pixmap_item:
            return
            
        zoom_val = self.zoom_slider.value()
        zoom_factor = zoom_val / 10.0
        self.zoom_label.setText(f"{zoom_factor:.1f}x")
        
        self.view.resetTransform()
        self.view.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        self.view.scale(zoom_factor, zoom_factor)

    def get_crop_rect(self):
        if not self.overlay:
            return None
        r = self.overlay.crop_rect
        return (r.x(), r.y(), r.width(), r.height())
