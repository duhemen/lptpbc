# src/validator_dialog.py
import os
from datetime import datetime
from typing import Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFileDialog, QTextBrowser, 
    QGroupBox, QLineEdit, QFormLayout, QProgressBar,
    QMessageBox, QWidget, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QPalette, QFont

from .blockchain_manager import BlockchainManager


class ValidatorThread(QThread):
    finished = pyqtSignal(dict)
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    
    def __init__(self, manager: BlockchainManager, file_path: str, block_hash: Optional[str] = None):
        super().__init__()
        self.manager = manager
        self.file_path = file_path
        self.block_hash = block_hash
    
    def run(self):
        try:
            self.status.emit("📂 Membaca file...")
            self.progress.emit(20)
            self.status.emit("🔍 Memverifikasi hash...")
            self.progress.emit(40)
            self.status.emit("🔐 Memeriksa signature...")
            self.progress.emit(60)
            result = self.manager.validate_document(self.file_path, self.block_hash)
            self.progress.emit(100)
            self.status.emit("✅ Validasi selesai!")
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({
                "is_valid": False,
                "message": f"❌ Error: {str(e)}",
                "details": {}
            })


class ValidatorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.manager = BlockchainManager()
        self.selected_file = None
        self.block_hash = None
        
        self.setWindowTitle("🔐 Validator Dokumen LPTBC")
        self.setGeometry(100, 100, 800, 600)
        self.setModal(True)
        
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        header = QLabel("🔐 LPTBC Document Validator")
        header.setObjectName("Header")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        file_group = QGroupBox("📄 Pilih Dokumen")
        file_layout = QHBoxLayout(file_group)
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Pilih file dokumen yang akan divalidasi...")
        self.file_input.setReadOnly(True)
        btn_browse = QPushButton("📂 Browse")
        btn_browse.clicked.connect(self.browse_file)
        file_layout.addWidget(self.file_input)
        file_layout.addWidget(btn_browse)
        layout.addWidget(file_group)
        
        hash_group = QGroupBox("🔑 Block Hash (Opsional)")
        hash_layout = QHBoxLayout(hash_group)
        self.hash_input = QLineEdit()
        self.hash_input.setPlaceholderText("Masukkan block hash untuk verifikasi spesifik...")
        hash_layout.addWidget(self.hash_input)
        layout.addWidget(hash_group)
        
        btn_layout = QHBoxLayout()
        btn_validate = QPushButton("🔍 Validasi Dokumen")
        btn_validate.setObjectName("ValidateBtn")
        btn_validate.clicked.connect(self.validate_document)
        btn_validate.setFixedHeight(50)
        btn_clear = QPushButton("🗑️ Clear")
        btn_clear.clicked.connect(self.clear_all)
        btn_layout.addWidget(btn_validate)
        btn_layout.addWidget(btn_clear)
        layout.addLayout(btn_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Menunggu validasi...")
        self.status_label.setObjectName("Status")
        layout.addWidget(self.status_label)
        
        result_group = QGroupBox("📋 Hasil Validasi")
        result_layout = QVBoxLayout(result_group)
        self.result_browser = QTextBrowser()
        self.result_browser.setObjectName("ResultBrowser")
        result_layout.addWidget(self.result_browser)
        layout.addWidget(result_group)
    
    def apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #F5F7FA;
            }
            QLabel#Header {
                font-size: 24px;
                font-weight: bold;
                color: #004B87;
                padding: 15px;
                background-color: #FFFFFF;
                border-radius: 10px;
            }
            QGroupBox {
                border: 2px solid #FDB913;
                border-radius: 8px;
                margin-top: 15px;
                background-color: white;
                font-weight: bold;
                color: #004B87;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                color: #FDB913;
            }
            QPushButton#ValidateBtn {
                background-color: #004B87;
                color: white;
                border: 2px solid #FDB913;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton#ValidateBtn:hover {
                background-color: #FDB913;
                color: #003366;
            }
            QPushButton#ValidateBtn:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
            QTextBrowser#ResultBrowser {
                background-color: #FAFAFA;
                border: 1px solid #DDDDDD;
                border-radius: 6px;
                padding: 10px;
                font-family: monospace;
            }
            QLabel#Status {
                font-size: 14px;
                padding: 8px;
                background-color: white;
                border-radius: 6px;
                border: 1px solid #DDDDDD;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #DDDDDD;
                border-radius: 6px;
                padding: 8px;
            }
            QLineEdit:focus {
                border: 2px solid #004B87;
            }
            QProgressBar {
                border: 1px solid #DDDDDD;
                border-radius: 6px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #FDB913;
                border-radius: 6px;
            }
        """)
    
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Pilih Dokumen untuk Validasi",
            "",
            "All Files (*.*);;PDF Files (*.pdf);;Text Files (*.txt);;HTML Files (*.html)"
        )
        if file_path:
            self.selected_file = file_path
            self.file_input.setText(file_path)
            self.auto_find_block_hash(file_path)
    
    def auto_find_block_hash(self, file_path: str):
        try:
            import hashlib
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            print(f"🔍 File hash: {file_hash}")
            print(f"🔍 Total blocks: {len(self.manager.blockchain.chain)}")
            for block in self.manager.blockchain.chain:
                stored_hash = block.data.get("file_hash")
                stored_path = block.data.get("file_path", "")
                if stored_hash and stored_hash == file_hash:
                    self.block_hash = block.hash
                    self.hash_input.setText(block.hash)
                    self.status_label.setText(f"✅ Ditemukan di blockchain! Block #{block.index}")
                    return
                file_name = os.path.basename(file_path)
                if stored_path and os.path.basename(stored_path) == file_name:
                    self.block_hash = block.hash
                    self.hash_input.setText(block.hash)
                    self.status_label.setText(f"✅ Ditemukan di blockchain! Block #{block.index} (by filename)")
                    return
            self.status_label.setText("ℹ️ Dokumen belum terdaftar di blockchain")
        except Exception as e:
            self.status_label.setText(f"⚠️ Error: {str(e)}")
            print(f"❌ Auto-find error: {e}")
    
    def validate_document(self):
        if not self.selected_file:
            QMessageBox.warning(self, "Peringatan", "Silakan pilih file terlebih dahulu!")
            return
        if not os.path.exists(self.selected_file):
            QMessageBox.warning(self, "Peringatan", "File tidak ditemukan!")
            return
        block_hash = self.hash_input.text().strip() or None
        self.findChild(QPushButton, "ValidateBtn").setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.result_browser.clear()
        self.thread = ValidatorThread(self.manager, self.selected_file, block_hash)
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.status.connect(self.status_label.setText)
        self.thread.finished.connect(self.on_validation_finished)
        self.thread.start()
    
    def on_validation_finished(self, result: dict):
        self.progress_bar.setVisible(False)
        self.findChild(QPushButton, "ValidateBtn").setEnabled(True)
        self.display_result(result)
    
    def display_result(self, result: dict):
        is_valid = result.get("is_valid", False)
        message = result.get("message", "")
        details = result.get("details", {})
        if is_valid:
            status_color = "#27AE60"
            icon = "✅"
            status_text = "VALID"
        else:
            status_color = "#E74C3C"
            icon = "❌"
            status_text = "TIDAK VALID"
        
        html = f"""
        <div style='font-family: monospace; padding: 10px;'>
            <h2 style='color: {status_color}; text-align: center;'>{icon} Dokumen {status_text}!</h2>
            <p style='text-align: center; color: #666;'>{message}</p>
            <hr>
        """
        if details:
            html += "<h3>📋 Detail Validasi:</h3><ul>"
            important_keys = ['block_index', 'doc_type', 'doc_nomor', 'doc_tanggal', 'file_hash', 'stored_file_hash']
            for key in important_keys:
                if key in details:
                    value = details[key]
                    if key == 'file_hash' and len(str(value)) > 16:
                        value = f"{value[:16]}..."
                    html += f"<li><b>{key}:</b> {value}</li>"
            for key, value in details.items():
                if key in important_keys:
                    continue
                if isinstance(value, dict):
                    html += f"<li><b>{key}:</b><br>"
                    for sub_key, sub_val in value.items():
                        if sub_key == 'public_key':
                            sub_val = sub_val[:50] + "..."
                        html += f"&nbsp;&nbsp;{sub_key}: {sub_val}<br>"
                    html += "</li>"
                else:
                    html += f"<li><b>{key}:</b> {value}</li>"
            html += "</ul>"
        html += """
        <hr>
        <p style='font-size: 10px; color: #999; text-align: center;'>
            Diverifikasi oleh LPTBC Validator v1.0
        </p>
        </div>
        """
        self.result_browser.setHtml(html)
        if is_valid:
            QMessageBox.information(self, "Validasi Berhasil", "✅ Dokumen VALID!\n\nDokumen ini asli dan diterbitkan oleh LPTBC.")
        else:
            QMessageBox.warning(self, "Validasi Gagal", f"❌ Dokumen TIDAK VALID!\n\n{message}")
    
    def clear_all(self):
        self.selected_file = None
        self.file_input.clear()
        self.hash_input.clear()
        self.block_hash = None
        self.result_browser.clear()
        self.status_label.setText("Menunggu validasi...")
        self.progress_bar.setVisible(False)