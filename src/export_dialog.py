# src/export_dialog.py
import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFileDialog, QTableWidget, QTableWidgetItem,
    QGroupBox, QHeaderView, QMessageBox, QProgressBar,
    QWidget, QLineEdit, QFormLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from .export_manager import ExportManager


class ExportThread(QThread):
    finished = pyqtSignal(bool, str, str)
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    
    def __init__(self, manager: ExportManager, filename: str = None):
        super().__init__()
        self.manager = manager
        self.filename = filename
    
    def run(self):
        try:
            self.status.emit("📦 Mengekspor blockchain...")
            self.progress.emit(30)
            success, path, message = self.manager.export_blockchain(self.filename)
            self.progress.emit(100)
            self.status.emit("✅ Selesai!" if success else "❌ Gagal")
            self.finished.emit(success, path, message)
        except Exception as e:
            self.finished.emit(False, "", f"❌ Error: {str(e)}")


class ImportThread(QThread):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    
    def __init__(self, manager: ExportManager, file_path: str):
        super().__init__()
        self.manager = manager
        self.file_path = file_path
    
    def run(self):
        try:
            self.status.emit("📥 Mengimpor blockchain...")
            self.progress.emit(30)
            success, message = self.manager.import_blockchain(self.file_path)
            self.progress.emit(100)
            self.status.emit("✅ Selesai!" if success else "❌ Gagal")
            self.finished.emit(success, message)
        except Exception as e:
            self.finished.emit(False, f"❌ Error: {str(e)}")


class ExportImportDialog(QDialog):
    def __init__(self, parent=None, blockchain_manager=None):
        super().__init__(parent)
        self.manager = ExportManager()
        
        self.setWindowTitle("🔄 Ekspor/Impor Blockchain LPTBC")
        self.setGeometry(100, 100, 700, 500)
        self.setModal(True)
        
        self.setup_ui()
        self.refresh_exports()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        header = QLabel("🔄 Manajemen Ekspor/Impor Blockchain")
        header.setObjectName("Header")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            QLabel#Header {
                font-size: 20px;
                font-weight: bold;
                color: #004B87;
                padding: 15px;
                background-color: white;
                border-radius: 10px;
            }
        """)
        layout.addWidget(header)
        
        export_group = QGroupBox("📤 Ekspor Blockchain")
        export_layout = QVBoxLayout(export_group)
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Nama File:"))
        self.filename_input = QLineEdit()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename_input.setText(f"lptbc_backup_{timestamp}.lptbc")
        file_layout.addWidget(self.filename_input)
        export_layout.addLayout(file_layout)
        
        btn_export = QPushButton("📤 Ekspor Blockchain")
        btn_export.setObjectName("ExportBtn")
        btn_export.clicked.connect(self.do_export)
        btn_export.setFixedHeight(40)
        export_layout.addWidget(btn_export)
        layout.addWidget(export_group)
        
        import_group = QGroupBox("📥 Impor Blockchain")
        import_layout = QVBoxLayout(import_group)
        import_file_layout = QHBoxLayout()
        self.import_file_input = QLineEdit()
        self.import_file_input.setPlaceholderText("Pilih file .lptbc untuk diimpor...")
        btn_browse = QPushButton("📂 Browse")
        btn_browse.clicked.connect(self.browse_import_file)
        import_file_layout.addWidget(self.import_file_input)
        import_file_layout.addWidget(btn_browse)
        import_layout.addLayout(import_file_layout)
        
        btn_import = QPushButton("📥 Impor Blockchain")
        btn_import.setObjectName("ImportBtn")
        btn_import.clicked.connect(self.do_import)
        btn_import.setFixedHeight(40)
        import_layout.addWidget(btn_import)
        layout.addWidget(import_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Menunggu...")
        self.status_label.setObjectName("Status")
        self.status_label.setStyleSheet("""
            QLabel#Status {
                padding: 8px;
                background-color: white;
                border-radius: 6px;
                border: 1px solid #DDDDDD;
            }
        """)
        layout.addWidget(self.status_label)
        
        list_group = QGroupBox("📂 Riwayat Ekspor")
        list_layout = QVBoxLayout(list_group)
        self.exports_table = QTableWidget()
        self.exports_table.setColumnCount(4)
        self.exports_table.setHorizontalHeaderLabels(["Nama File", "Ukuran", "Tanggal", "Aksi"])
        self.exports_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.exports_table.setAlternatingRowColors(True)
        self.exports_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #DDDDDD;
                border-radius: 6px;
            }
            QTableWidget::item {
                padding: 8px;
            }
        """)
        list_layout.addWidget(self.exports_table)
        layout.addWidget(list_group)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #F5F7FA;
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
            QPushButton#ExportBtn {
                background-color: #004B87;
                color: white;
                border: 2px solid #FDB913;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton#ExportBtn:hover {
                background-color: #FDB913;
                color: #003366;
            }
            QPushButton#ImportBtn {
                background-color: #27AE60;
                color: white;
                border: 2px solid #FDB913;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton#ImportBtn:hover {
                background-color: #FDB913;
                color: #003366;
            }
            QPushButton#ActionBtn {
                background-color: transparent;
                color: #004B87;
                border: 1px solid #004B87;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
            }
            QPushButton#ActionBtn:hover {
                background-color: #004B87;
                color: white;
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
    
    def refresh_exports(self):
        self.exports_table.setRowCount(0)
        exports = self.manager.get_exports()
        for row, exp in enumerate(exports):
            self.exports_table.insertRow(row)
            self.exports_table.setItem(row, 0, QTableWidgetItem(exp['filename']))
            self.exports_table.setItem(row, 1, QTableWidgetItem(exp['size_str']))
            self.exports_table.setItem(row, 2, QTableWidgetItem(exp['modified']))
            btn_delete = QPushButton("🗑️ Hapus")
            btn_delete.setObjectName("ActionBtn")
            btn_delete.clicked.connect(lambda checked, p=exp['path']: self.delete_export(p))
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(2, 2, 2, 2)
            layout.addWidget(btn_delete)
            self.exports_table.setCellWidget(row, 3, widget)
    
    def browse_import_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Pilih File Blockchain (.lptbc)", "", "LPTBC Files (*.lptbc);;All Files (*.*)")
        if file_path:
            self.import_file_input.setText(file_path)
    
    def do_export(self):
        filename = self.filename_input.text().strip()
        if not filename:
            filename = f"lptbc_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.lptbc"
        btn_export = self.findChild(QPushButton, "ExportBtn")
        if btn_export:
            btn_export.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("⏳ Mengekspor...")
        self.thread = ExportThread(self.manager, filename)
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.status.connect(self.status_label.setText)
        self.thread.finished.connect(self.on_export_finished)
        self.thread.start()
    
    def on_export_finished(self, success: bool, path: str, message: str):
        self.progress_bar.setVisible(False)
        self.findChild(QPushButton, "ExportBtn").setEnabled(True)
        if success:
            self.status_label.setText(f"✅ {message}")
            QMessageBox.information(self, "Sukses", f"✅ Blockchain berhasil diekspor!\n\nFile: {path}")
            self.refresh_exports()
        else:
            self.status_label.setText(f"❌ {message}")
            QMessageBox.critical(self, "Gagal", f"❌ {message}")
    
    def do_import(self):
        file_path = self.import_file_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, "Peringatan", "Silakan pilih file .lptbc terlebih dahulu!")
            return
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Peringatan", "File tidak ditemukan!")
            return
        if not file_path.endswith('.lptbc'):
            QMessageBox.warning(self, "Peringatan", "File harus berformat .lptbc!")
            return
        
        reply = QMessageBox.question(
            self, "Konfirmasi Impor",
            "⚠️ Impor akan mengganti blockchain saat ini.\n\nBackup otomatis akan dibuat terlebih dahulu.\n\nLanjutkan?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        
        self.findChild(QPushButton, "ImportBtn").setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("⏳ Mengimpor...")
        self.thread = ImportThread(self.manager, file_path)
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.status.connect(self.status_label.setText)
        self.thread.finished.connect(self.on_import_finished)
        self.thread.start()
    
    def on_import_finished(self, success: bool, message: str):
        self.progress_bar.setVisible(False)
        self.findChild(QPushButton, "ImportBtn").setEnabled(True)
        if success:
            self.status_label.setText(f"✅ {message}")
            QMessageBox.information(self, "Sukses", f"✅ {message}\n\nSilakan restart aplikasi untuk melihat perubahan.")
            self.refresh_exports()
        else:
            self.status_label.setText(f"❌ {message}")
            QMessageBox.critical(self, "Gagal", f"❌ {message}")
    
    def delete_export(self, file_path: str):
        reply = QMessageBox.question(
            self, "Konfirmasi Hapus",
            f"Yakin ingin menghapus file ini?\n\n{file_path}",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                os.remove(file_path)
                self.refresh_exports()
                self.status_label.setText(f"✅ File berhasil dihapus")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"❌ Gagal menghapus: {e}")