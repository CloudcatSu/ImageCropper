import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QStackedWidget, QMessageBox, QProgressDialog, QDialog
)
from PySide6.QtCore import Qt, QThread

from ui.preview_grid import PreviewGrid
from ui.crop_editor import CropEditor
from ui.export_dialog import ExportDialog
from core.image_processor import BatchProcessorWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("自動化裁切圖片工具 (Image Cropper)")
        self.resize(1000, 700)
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        self.stacked_widget = QStackedWidget()
        
        # Page 0: Preview Grid
        self.preview_page = QWidget()
        preview_layout = QVBoxLayout(self.preview_page)
        
        self.preview_grid = PreviewGrid()
        self.preview_grid.files_changed.connect(self.on_files_changed)
        
        self.crop_btn = QPushButton("進入裁切 (Crop)")
        self.crop_btn.setFixedHeight(50)
        self.crop_btn.setEnabled(False)
        self.crop_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
        """)
        self.crop_btn.clicked.connect(self.go_to_crop)
        
        preview_layout.addWidget(self.preview_grid)
        preview_layout.addWidget(self.crop_btn)
        
        # Page 1: Crop Editor
        self.crop_page = QWidget()
        crop_layout = QVBoxLayout(self.crop_page)
        crop_layout.setContentsMargins(0, 0, 0, 0)
        
        self.crop_editor = CropEditor()
        self.crop_editor.back_btn.clicked.connect(self.go_to_preview)
        self.crop_editor.confirm_btn.clicked.connect(self.start_export)
        
        crop_layout.addWidget(self.crop_editor)
        
        self.stacked_widget.addWidget(self.preview_page)
        self.stacked_widget.addWidget(self.crop_page)
        
        main_layout.addWidget(self.stacked_widget)

    def on_files_changed(self, is_valid):
        self.crop_btn.setEnabled(is_valid)

    def go_to_crop(self):
        files = self.preview_grid.get_valid_files()
        if not files:
            return
            
        self.showMaximized()
        self.crop_editor.load_images(files)
        self.stacked_widget.setCurrentIndex(1)

    def go_to_preview(self):
        self.showNormal()
        self.stacked_widget.setCurrentIndex(0)

    def start_export(self):
        files = self.crop_editor.files
        if not files:
            return
            
        crop_rect = self.crop_editor.get_crop_rect()
        if not crop_rect:
            return

        first_name = os.path.splitext(os.path.basename(files[0]))[0]
        dialog = ExportDialog(self, first_filename=first_name)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.config
            self.run_batch_processor(files, crop_rect, config)

    def run_batch_processor(self, files, crop_rect, config):
        self.progress_dialog = QProgressDialog("正在裁切與儲存圖片...", "取消", 0, 100, self)
        self.progress_dialog.setWindowTitle("處理中")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.show()

        self.thread = QThread()
        
        mode = config['mode']
        fmt = config.get('format', 'original')
        out_dir = config.get('dir', '')
        rename_rule = config.get('rename_rule', None)
        
        base_name = ""
        if fmt == 'pdf' and rename_rule and rename_rule.get('type') == 'pdf':
            base_name = rename_rule.get('name', '')

        self.worker = BatchProcessorWorker(
            file_paths=files,
            crop_rect=crop_rect,
            export_mode=mode,
            export_format=fmt,
            export_dir=out_dir,
            base_name=base_name,
            rename_rule=rename_rule
        )
        
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.progress_dialog.setValue)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.error.connect(self.on_processing_error)
        
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        
        self.progress_dialog.canceled.connect(self.thread.requestInterruption)
        
        self.thread.start()

    def on_processing_finished(self, msg):
        self.progress_dialog.setValue(100)
        self.progress_dialog.close()
        
        # Message matching the requirement
        display_msg = "處理完成！\n"
        if "Done" in msg:
            if self.worker.export_mode == 'overwrite':
                display_msg += "已將原圖片丟至垃圾桶，並存入新檔。"
            else:
                display_msg += "圖片已另存新檔。"
        else:
            display_msg += msg # PDF path or other
            if self.worker.export_mode == 'overwrite':
                display_msg += "\n\n已將原圖片丟至垃圾桶。"
            
        QMessageBox.information(self, "完成", display_msg)
        
        self.preview_grid.image_data = []
        self.preview_grid.update_grid()
        self.go_to_preview()

    def on_processing_error(self, err):
        self.progress_dialog.close()
        QMessageBox.critical(self, "錯誤", f"處理時發生錯誤:\n{err}")
        self.thread.quit()
