from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QRadioButton, QButtonGroup,
    QComboBox, QLabel, QLineEdit, QPushButton, QFileDialog, QStackedWidget,
    QWidget, QGroupBox, QSpinBox, QMessageBox
)
from PySide6.QtCore import Qt

class ExportDialog(QDialog):
    def __init__(self, parent=None, first_filename=""):
        super().__init__(parent)
        self.setWindowTitle("匯出設定 (Export Settings)")
        self.setMinimumWidth(500)
        
        self.config = {}
        self.first_filename = first_filename
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 模式選擇
        mode_group = QGroupBox("輸出模式")
        mode_layout = QVBoxLayout()
        self.radio_overwrite = QRadioButton("a. 對原圖片檔案裁切 (裁切後將原檔案丟至垃圾桶，並存入新檔)")
        self.radio_save_as = QRadioButton("b. 另存新檔案")
        self.radio_save_as.setChecked(True)
        
        self.mode_btn_group = QButtonGroup()
        self.mode_btn_group.addButton(self.radio_overwrite)
        self.mode_btn_group.addButton(self.radio_save_as)
        
        mode_layout.addWidget(self.radio_overwrite)
        mode_layout.addWidget(self.radio_save_as)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # 另存新檔案的設定區塊
        self.save_as_widget = QWidget()
        save_as_layout = QVBoxLayout(self.save_as_widget)
        save_as_layout.setContentsMargins(0, 0, 0, 0)
        
        # 區塊一：選擇存檔類型
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("存檔類型:"))
        self.combo_format = QComboBox()
        self.combo_format.addItems(["original", "jpg", "png", "webp", "pdf"])
        type_layout.addWidget(self.combo_format)
        type_layout.addStretch()
        save_as_layout.addLayout(type_layout)
        
        # 區塊二：選擇存檔路徑
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("存檔路徑:"))
        self.path_edit = QLineEdit()
        self.path_btn = QPushButton("瀏覽...")
        self.path_btn.clicked.connect(self.browse_dir)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.path_btn)
        save_as_layout.addLayout(path_layout)
        
        # 區塊三：命名規則
        self.rename_group = QGroupBox("命名規則")
        rename_layout = QVBoxLayout(self.rename_group)
        
        # 命名方式切換
        rename_type_layout = QHBoxLayout()
        rename_type_layout.addWidget(QLabel("方式:"))
        self.combo_rename_type = QComboBox()
        self.combo_rename_type.addItems(["取代文字", "加入文字", "格式化 (連續編號)", "PDF 單一檔名"])
        rename_type_layout.addWidget(self.combo_rename_type)
        rename_type_layout.addStretch()
        rename_layout.addLayout(rename_type_layout)
        
        # Stacked widget for different rename options
        self.rename_stack = QStackedWidget()
        
        # Replace page
        page_replace = QWidget()
        l_replace = QHBoxLayout(page_replace)
        l_replace.setContentsMargins(0, 0, 0, 0)
        self.edit_target = QLineEdit()
        self.edit_target.setPlaceholderText("尋找文字")
        self.edit_replacement = QLineEdit()
        self.edit_replacement.setPlaceholderText("取代為")
        l_replace.addWidget(self.edit_target)
        l_replace.addWidget(QLabel("->"))
        l_replace.addWidget(self.edit_replacement)
        self.rename_stack.addWidget(page_replace)
        
        # Add page
        page_add = QWidget()
        l_add = QHBoxLayout(page_add)
        l_add.setContentsMargins(0, 0, 0, 0)
        self.edit_prefix = QLineEdit()
        self.edit_prefix.setPlaceholderText("加入前綴")
        self.edit_suffix = QLineEdit()
        self.edit_suffix.setPlaceholderText("加入後綴")
        l_add.addWidget(self.edit_prefix)
        l_add.addWidget(QLabel("[原檔名]"))
        l_add.addWidget(self.edit_suffix)
        self.rename_stack.addWidget(page_add)
        
        # Format page
        page_format = QWidget()
        l_format = QHBoxLayout(page_format)
        l_format.setContentsMargins(0, 0, 0, 0)
        self.edit_base = QLineEdit()
        self.edit_base.setPlaceholderText("自訂名稱")
        l_format.addWidget(self.edit_base)
        l_format.addWidget(QLabel("起始數字:"))
        self.spin_start = QSpinBox()
        self.spin_start.setMinimum(0)
        self.spin_start.setMaximum(9999)
        self.spin_start.setValue(1)
        l_format.addWidget(self.spin_start)
        l_format.addWidget(QLabel("位數:"))
        self.spin_digits = QSpinBox()
        self.spin_digits.setMinimum(1)
        self.spin_digits.setMaximum(6)
        self.spin_digits.setValue(3)
        l_format.addWidget(self.spin_digits)
        self.rename_stack.addWidget(page_format)
        
        # PDF page
        page_pdf = QWidget()
        l_pdf = QHBoxLayout(page_pdf)
        l_pdf.setContentsMargins(0, 0, 0, 0)
        self.edit_pdf_name = QLineEdit()
        if self.first_filename:
            self.edit_pdf_name.setText(self.first_filename)
        else:
            self.edit_pdf_name.setPlaceholderText("PDF 檔案名稱 (不含副檔名)")
        l_pdf.addWidget(self.edit_pdf_name)
        self.rename_stack.addWidget(page_pdf)
        
        rename_layout.addWidget(self.rename_stack)
        
        # Add preview label
        self.preview_label = QLabel("範例: ")
        self.preview_label.setStyleSheet("color: #666; font-style: italic; margin-top: 10px;")
        rename_layout.addWidget(self.preview_label)
        
        save_as_layout.addWidget(self.rename_group)
        
        layout.addWidget(self.save_as_widget)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok = QPushButton("確定")
        self.btn_ok.clicked.connect(self.accept_config)
        self.btn_ok.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold; padding: 5px 20px;")
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_ok)
        layout.addLayout(btn_layout)
        
        # Connections
        self.radio_overwrite.toggled.connect(self.toggle_save_as)
        self.combo_format.currentTextChanged.connect(self.toggle_pdf)
        self.combo_rename_type.currentIndexChanged.connect(self.rename_stack.setCurrentIndex)
        
        self.combo_rename_type.setCurrentIndex(2) # Default format

        # Connect signals for live preview update
        self.edit_target.textChanged.connect(self.update_preview)
        self.edit_replacement.textChanged.connect(self.update_preview)
        self.edit_prefix.textChanged.connect(self.update_preview)
        self.edit_suffix.textChanged.connect(self.update_preview)
        self.edit_base.textChanged.connect(self.update_preview)
        self.spin_start.valueChanged.connect(self.update_preview)
        self.spin_digits.valueChanged.connect(self.update_preview)
        self.edit_pdf_name.textChanged.connect(self.update_preview)
        self.radio_overwrite.toggled.connect(self.update_preview)
        self.combo_rename_type.currentIndexChanged.connect(self.update_preview)
        self.combo_format.currentTextChanged.connect(self.update_preview)
        
        self.update_preview()

    def update_preview(self, *args):
        orig_name = self.first_filename or "image_001"
        ext = self.combo_format.currentText()
        if ext == 'original':
            ext = 'jpg' # just a dummy for preview
            
        fmt_str = f".{ext}"
        
        if self.radio_overwrite.isChecked():
            self.preview_label.setText(f"預覽: 將覆蓋原檔並丟進垃圾桶")
            return
            
        if ext == 'pdf':
            pdf_n = self.edit_pdf_name.text() or orig_name
            self.preview_label.setText(f"預覽: 將所有圖片合併為 {pdf_n}.pdf")
            return
            
        idx = self.combo_rename_type.currentIndex()
        new_name = orig_name
        
        if idx == 0:
            target = self.edit_target.text()
            rep = self.edit_replacement.text()
            if target:
                new_name = orig_name.replace(target, rep)
        elif idx == 1:
            new_name = f"{self.edit_prefix.text()}{orig_name}{self.edit_suffix.text()}"
        elif idx == 2:
            base = self.edit_base.text() or orig_name
            start = self.spin_start.value()
            digits = self.spin_digits.value()
            num = str(start).zfill(digits)
            new_name = f"{base}{num}"
            
        self.preview_label.setText(f"範例: {orig_name}  ➔  {new_name}{fmt_str}")

    def browse_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "選擇存檔路徑")
        if dir_path:
            self.path_edit.setText(dir_path)

    def toggle_save_as(self, checked):
        self.save_as_widget.setVisible(not checked)

    def toggle_pdf(self, text):
        if text == 'pdf':
            self.combo_rename_type.setCurrentIndex(3)
            self.combo_rename_type.setEnabled(False)
        else:
            self.combo_rename_type.setEnabled(True)
            if self.combo_rename_type.currentIndex() == 3:
                self.combo_rename_type.setCurrentIndex(2)

    def accept_config(self):
        if self.radio_overwrite.isChecked():
            self.config = {
                'mode': 'overwrite',
                'format': 'original'
            }
        else:
            format_ext = self.combo_format.currentText()
            rename_idx = self.combo_rename_type.currentIndex()
            rename_rule = {}
            
            if format_ext == 'pdf':
                rename_rule = {'type': 'pdf', 'name': self.edit_pdf_name.text()}
            elif rename_idx == 0:
                rename_rule = {'type': 'replace', 'target': self.edit_target.text(), 'replacement': self.edit_replacement.text()}
            elif rename_idx == 1:
                rename_rule = {'type': 'add', 'prefix': self.edit_prefix.text(), 'suffix': self.edit_suffix.text()}
            elif rename_idx == 2:
                rename_rule = {'type': 'format', 'base': self.edit_base.text(), 'digits': self.spin_digits.value(), 'start': self.spin_start.value()}

            if not self.path_edit.text():
                QMessageBox.warning(self, "錯誤", "請選擇存檔路徑！")
                return

            self.config = {
                'mode': 'save_as',
                'format': format_ext,
                'dir': self.path_edit.text(),
                'rename_rule': rename_rule
            }
        
        self.accept()
