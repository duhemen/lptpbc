# src/dashboard.py
import os
import subprocess
import platform
from datetime import datetime
from typing import Dict, Any, List, Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem,
    QGroupBox, QGridLayout, QHeaderView, QFrame,
    QTextBrowser, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QPalette, QFont

from .blockchain_manager import BlockchainManager


class DashboardWidget(QWidget):
    refresh_signal = pyqtSignal()
    
    def __init__(self, parent=None, blockchain_manager: BlockchainManager = None):
        super().__init__(parent)
        self.parent = parent
        self.manager = blockchain_manager or BlockchainManager()
        
        self.setup_ui()
        self.refresh_data()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(30000)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header = QLabel("📊 LPTBC Dashboard")
        header.setObjectName("DashboardHeader")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            QLabel#DashboardHeader {
                font-size: 28px;
                font-weight: bold;
                color: #004B87;
                padding: 20px;
                background-color: white;
                border-radius: 10px;
                border: 2px solid #FDB913;
            }
        """)
        layout.addWidget(header)
        
        self.stats_layout = QGridLayout()
        self.stats_layout.setSpacing(15)
        
        self.card_total_docs = self._create_stat_card("📄 Total Dokumen", "0")
        self.stats_layout.addWidget(self.card_total_docs, 0, 0)
        
        self.card_total_blocks = self._create_stat_card("🔗 Total Blok", "0")
        self.stats_layout.addWidget(self.card_total_blocks, 0, 1)
        
        self.card_status = self._create_stat_card("✅ Status", "Valid")
        self.stats_layout.addWidget(self.card_status, 0, 2)
        
        self.card_last_update = self._create_stat_card("🕐 Update Terakhir", "N/A")
        self.stats_layout.addWidget(self.card_last_update, 0, 3)
        
        layout.addLayout(self.stats_layout)
        
        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setObjectName("RefreshBtn")
        btn_refresh.clicked.connect(self.refresh_data)
        btn_refresh.setFixedHeight(40)
        layout.addWidget(btn_refresh)
        
        history_group = QGroupBox("📄 Riwayat Dokumen Terbit")
        history_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #FDB913;
                border-radius: 8px;
                margin-top: 15px;
                font-weight: bold;
                color: #004B87;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                color: #FDB913;
            }
        """)
        history_layout = QVBoxLayout(history_group)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["#", "Jenis", "Nomor", "Tanggal", "Aksi"])
        self.history_table.setColumnWidth(0, 40)
        self.history_table.setColumnWidth(1, 200)
        self.history_table.setColumnWidth(2, 150)
        self.history_table.setColumnWidth(3, 180)
        self.history_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.verticalHeader().setDefaultSectionSize(48)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setSelectionMode(QTableWidget.SingleSelection)
        self.history_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #DDDDDD;
                border-radius: 6px;
                gridline-color: #EEEEEE;
                alternate-background-color: #F8F9FA;
            }
            QTableWidget::item {
                padding: 6px 10px;
            }
            QTableWidget::item:selected {
                background-color: #004B8720;
                color: #004B87;
            }
            QHeaderView::section {
                background-color: #E8ECF0;
                padding: 8px 10px;
                border: none;
                border-bottom: 2px solid #004B87;
                font-weight: bold;
                color: #004B87;
                font-size: 12px;
            }
        """)
        
        history_layout.addWidget(self.history_table)
        layout.addWidget(history_group, 1)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #F5F7FA;
            }
            QPushButton#RefreshBtn {
                background-color: #004B87;
                color: white;
                border: 2px solid #FDB913;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#RefreshBtn:hover {
                background-color: #FDB913;
                color: #003366;
            }
            QPushButton#RefreshBtn:pressed {
                background-color: #003366;
                color: white;
            }
        """)
    
    def _create_stat_card(self, title: str, value: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 15px;
                border: 1px solid #E0E0E0;
            }
            QFrame:hover {
                border: 2px solid #FDB913;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)
        label_title = QLabel(title)
        label_title.setStyleSheet("font-size: 12px; color: #666666;")
        label_title.setAlignment(Qt.AlignCenter)
        label_value = QLabel(value)
        label_value.setObjectName("StatValue")
        label_value.setStyleSheet("font-size: 24px; font-weight: bold; color: #004B87;")
        label_value.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_title)
        layout.addWidget(label_value)
        card.value_label = label_value
        return card
    
    def refresh_data(self):
        try:
            summary = self.manager.blockchain.get_summary()
            self.card_total_docs.value_label.setText(str(summary.get('total_documents', 0)))
            self.card_total_blocks.value_label.setText(str(summary.get('total_blocks', 0)))
            verified = summary.get('verified', False)
            status_text = "✅ Valid" if verified else "❌ Tidak Valid"
            status_color = "#27AE60" if verified else "#E74C3C"
            self.card_status.value_label.setText(status_text)
            self.card_status.value_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {status_color};")
            last_block = summary.get('last_block')
            if last_block:
                timestamp = last_block.get('timestamp')
                if timestamp:
                    dt = datetime.fromtimestamp(timestamp)
                    self.card_last_update.value_label.setText(dt.strftime("%Y-%m-%d %H:%M:%S"))
            self._update_history()
            self.refresh_signal.emit()
        except Exception as e:
            print(f"❌ Error refreshing dashboard: {e}")
    
    def _update_history(self):
        self.history_table.setRowCount(0)
        try:
            docs = self.manager.get_published_documents(limit=50)
            for row, doc in enumerate(docs):
                self.history_table.insertRow(row)
                
                item = QTableWidgetItem(str(row + 1))
                item.setTextAlignment(Qt.AlignCenter)
                self.history_table.setItem(row, 0, item)
                
                doc_type = doc.get('type', 'Unknown')
                type_icon = "📄"
                if "Permohonan" in doc_type:
                    type_icon = "📨"
                elif "Undangan" in doc_type:
                    type_icon = "📩"
                elif "Berita" in doc_type:
                    type_icon = "📋"
                elif "Laporan" in doc_type:
                    type_icon = "📊"
                elif "Kontrak" in doc_type:
                    type_icon = "📝"
                elif "Keputusan" in doc_type:
                    type_icon = "⚖️"
                item = QTableWidgetItem(f"{type_icon} {doc_type}")
                self.history_table.setItem(row, 1, item)
                
                nomor = doc.get('nomor', 'N/A')
                item = QTableWidgetItem(nomor)
                self.history_table.setItem(row, 2, item)
                
                tanggal = doc.get('tanggal', doc.get('timestamp', 'N/A'))
                item = QTableWidgetItem(tanggal)
                self.history_table.setItem(row, 3, item)
                
                widget = QWidget()
                layout = QHBoxLayout(widget)
                layout.setContentsMargins(4, 2, 4, 2)
                layout.setSpacing(8)
                
                btn_validate = QPushButton("✅ Validasi")
                btn_validate.setObjectName("ActionValidateBtn")
                btn_validate.setCursor(Qt.PointingHandCursor)
                btn_validate.setFixedHeight(30)
                btn_validate.setMinimumWidth(80)
                btn_validate.setToolTip("🔍 Validasi keaslian dokumen")
                btn_validate.setStyleSheet("""
                    QPushButton#ActionValidateBtn {
                        background-color: #27AE60;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        padding: 4px 14px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton#ActionValidateBtn:hover {
                        background-color: #1E8449;
                    }
                    QPushButton#ActionValidateBtn:pressed {
                        background-color: #145A32;
                    }
                """)
                btn_validate.clicked.connect(lambda checked, d=doc: self._on_validate(d))
                
                btn_download = QPushButton("📥 Download")
                btn_download.setObjectName("ActionDownloadBtn")
                btn_download.setCursor(Qt.PointingHandCursor)
                btn_download.setFixedHeight(30)
                btn_download.setMinimumWidth(80)
                btn_download.setToolTip("📥 Download atau buka dokumen")
                btn_download.setStyleSheet("""
                    QPushButton#ActionDownloadBtn {
                        background-color: #2980B9;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        padding: 4px 14px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton#ActionDownloadBtn:hover {
                        background-color: #1A5276;
                    }
                    QPushButton#ActionDownloadBtn:pressed {
                        background-color: #0E2F44;
                    }
                """)
                btn_download.clicked.connect(lambda checked, d=doc: self._on_download(d))
                
                layout.addWidget(btn_validate)
                layout.addWidget(btn_download)
                layout.addStretch()
                self.history_table.setCellWidget(row, 4, widget)
        except Exception as e:
            print(f"❌ Error updating history: {e}")
    
    def _on_validate(self, doc: Dict):
        possible_paths = [
            doc.get('file_path', ''),
            os.path.join('output', 'published', os.path.basename(doc.get('file_path', ''))),
        ]
        file_path = None
        for path in possible_paths:
            if path and os.path.exists(path):
                file_path = path
                break
        if not file_path:
            QMessageBox.warning(self, "Warning", "File dokumen tidak ditemukan!")
            return
        from .validator_dialog import ValidatorDialog
        validator = ValidatorDialog(self)
        validator.selected_file = file_path
        validator.file_input.setText(file_path)
        validator.hash_input.setText(doc.get('hash', ''))
        validator.auto_find_block_hash(file_path)
        validator.exec_()
    
    def _on_download(self, doc: Dict):
        file_path = doc.get('file_path')
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "Warning", "File dokumen tidak ditemukan!")
            return
        try:
            if platform.system() == 'Windows':
                os.startfile(file_path)
            else:
                subprocess.Popen(['open', file_path])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Gagal membuka file: {str(e)}")