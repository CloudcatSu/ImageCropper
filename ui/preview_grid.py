import os
from collections import Counter
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QSlider, QLabel, QPushButton, QFileDialog, QStackedWidget
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap, QColor
from core.image_processor import get_image_info

class PreviewGrid(QWidget):
    # Signals to communicate with MainWindow
    files_changed = Signal(bool) # True if all valid and > 0, False otherwise

    def __init__(self):
        super().__init__()
        self.image_data = [] # List of dicts with file info
        self.majority_size = None
        self.has_anomalies = False

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.stack = QStackedWidget()
        
        # Empty State Widget
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Title
        lbl_title = QLabel("ScrnshotMate")
        font = lbl_title.font()
        font.setPixelSize(64)
        font.setBold(True)
        lbl_title.setFont(font)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Calculate half width of the title for the icon
        from PySide6.QtGui import QFontMetrics
        fm = QFontMetrics(font)
        title_width = fm.horizontalAdvance("ScrnshotMate")
        icon_width = title_width // 2

        # Icon
        self.lbl_icon = QLabel()
        from utils.helpers import resource_path
        icon_path = resource_path(os.path.join("assets", "ScrnshotMate_icon.png"))
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            self.lbl_icon.setPixmap(pixmap.scaledToWidth(icon_width, Qt.TransformationMode.SmoothTransformation))
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_icon.setContentsMargins(0, 0, 0, 20)
        
        lbl_version = QLabel("v1.1.0")
        lbl_version.setStyleSheet("font-size: 18px; color: #888;")
        lbl_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_desc = QLabel("請按增加檔案，或將圖片檔案拖入視窗")
        lbl_desc.setStyleSheet("font-size: 24px; color: #666; margin-top: 30px;")
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        empty_layout.addStretch()
        empty_layout.addWidget(self.lbl_icon)
        empty_layout.addWidget(lbl_title)
        empty_layout.addWidget(lbl_version)
        empty_layout.addWidget(lbl_desc)
        empty_layout.addStretch()

        # The Grid
        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setIconSize(QSize(150, 150))
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_widget.setSpacing(10)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        
        self.stack.addWidget(self.empty_widget)
        self.stack.addWidget(self.list_widget)

        layout.addWidget(self.stack)
        
        # Enable dragging to rearrange or drop files
        self.setAcceptDrops(True)

        # Bottom control bar
        control_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("增加檔案 (Add Files)")
        self.add_btn.clicked.connect(self.browse_files)
        
        self.delete_btn = QPushButton("刪除選取 (Delete Selected)")
        self.delete_btn.clicked.connect(self.delete_selected)
        
        self.status_label = QLabel("請載入圖片")
        self.status_label.setStyleSheet("color: #888;")
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(50, 300)
        self.slider.setValue(150)
        self.slider.setFixedWidth(150)
        self.slider.valueChanged.connect(self.change_icon_size)

        control_layout.addWidget(self.add_btn)
        control_layout.addWidget(self.delete_btn)
        control_layout.addWidget(self.status_label)
        control_layout.addStretch()
        control_layout.addWidget(QLabel("縮圖大小:"))
        control_layout.addWidget(self.slider)

        layout.addLayout(control_layout)

    def change_icon_size(self, size):
        self.list_widget.setIconSize(QSize(size, size))

    def browse_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "選擇圖片", "", "Images (*.png *.jpg *.jpeg *.webp *.bmp *.tiff)"
        )
        if files:
            self.add_files(files)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        files = [u.toLocalFile() for u in urls if u.isLocalFile()]
        if files:
            self.add_files(files)
            event.acceptProposedAction()

    def add_files(self, files):
        valid_exts = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff'}
        new_files = [f for f in files if os.path.splitext(f)[1].lower() in valid_exts]
        
        for f in new_files:
            if not any(d['path'] == f for d in self.image_data):
                info = get_image_info(f)
                if info:
                    self.image_data.append(info)
        
        self.update_grid()

    def delete_selected(self):
        items = self.list_widget.selectedItems()
        if not items:
            return
            
        for item in items:
            path = item.data(Qt.ItemDataRole.UserRole)
            self.image_data = [d for d in self.image_data if d['path'] != path]
            
        self.update_grid()

    def update_grid(self):
        self.list_widget.clear()
        
        if not self.image_data:
            self.stack.setCurrentIndex(0)
            self.status_label.setText("請載入圖片")
            self.status_label.setStyleSheet("color: #888;")
            self.files_changed.emit(False)
            return

        self.stack.setCurrentIndex(1)

        # Calculate majority size
        sizes = [(d['width'], d['height']) for d in self.image_data]
        counter = Counter(sizes)
        self.majority_size = counter.most_common(1)[0][0]

        self.has_anomalies = False

        for data in self.image_data:
            path = data['path']
            filename = os.path.basename(path)
            w, h = data['width'], data['height']
            
            is_anomaly = (w, h) != self.majority_size
            if is_anomaly:
                self.has_anomalies = True

            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, path)
            
            label_text = f"{filename}\n{w}x{h}"
            item.setText(label_text)
            
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                item.setIcon(QIcon(pixmap))
            
            if is_anomaly:
                item.setBackground(QColor(255, 200, 200)) # Light red background
                item.setForeground(QColor(200, 0, 0))
                item.setSelected(True)
            
            self.list_widget.addItem(item)

        # Update status
        if self.has_anomalies:
            self.status_label.setText(f"警告：有圖片尺寸與大多數 ({self.majority_size[0]}x{self.majority_size[1]}) 不同！請刪除異常圖片。")
            self.status_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
            self.files_changed.emit(False)
        else:
            self.status_label.setText(f"共 {len(self.image_data)} 張圖片，尺寸皆為 {self.majority_size[0]}x{self.majority_size[1]}")
            self.status_label.setStyleSheet("color: #388e3c;")
            self.files_changed.emit(True)

    def get_valid_files(self):
        if self.has_anomalies:
            return []
        return [d['path'] for d in self.image_data]
