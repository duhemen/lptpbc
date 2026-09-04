# src/main_windows.py
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QLineEdit, QDateEdit, QComboBox, 
    QTextEdit, QPushButton, QStackedWidget, QListWidget, 
    QFormLayout, QGroupBox, QFrame, QGraphicsDropShadowEffect,
    QFileDialog, QTextBrowser
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtPrintSupport import QPrinter

from .blockchain_manager import BlockchainManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LPT - Laporan Proses Tahapan Perencanaan")
        self.setGeometry(100, 100, 1450, 900)

        self.kop_path = None
        self.blockchain_manager = BlockchainManager()

        self.primary_blue = "#004B87"
        self.dark_blue = "#003366"
        self.accent_gold = "#FDB913"
        self.light_bg = "#F5F7FA"
        self.text_dark = "#333333"

        # Menyimpan data dokumen yang sedang aktif untuk keperluan save
        self.current_doc_data: Optional[Dict[str, Any]] = None

        self.apply_styles()
        self.setup_ui()
        self.setup_connections()

    def _format_text(self, text: str) -> str:
        if not text:
            return ""
        return text.replace("\n", "<br>").replace("\r\n", "<br>")

    def _format_tanggal_indonesia(self, date: QDate) -> str:
        """Format tanggal menjadi bahasa Indonesia yang benar."""
        hari = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
                 "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        
        nama_hari = hari[date.dayOfWeek() - 1]
        tanggal = date.day()
        nama_bulan = bulan[date.month() - 1]
        tahun = date.year()
        
        return f"{nama_hari}, {tanggal} {nama_bulan} {tahun}"

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.setup_sidebar(main_layout)
        self.setup_content_area(main_layout)

    def setup_sidebar(self, parent_layout):
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        title_label = QLabel("LPT")
        title_label.setObjectName("SidebarTitle")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFixedHeight(70)
        title_label.setStyleSheet("""
            QLabel#SidebarTitle {
                color: #FDB913;
                font-size: 22px;
                font-weight: bold;
                background-color: #003366;
                padding: 10px;
            }
        """)
        sidebar_layout.addWidget(title_label)

        self.nav_list = QListWidget()
        self.nav_list.setObjectName("SidebarList")
        self.nav_list.setStyleSheet("""
            QListWidget#SidebarList {
                background-color: transparent;
                border: none;
                outline: none;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            QListWidget#SidebarList::item {
                padding: 14px 20px;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
            QListWidget#SidebarList::item:hover {
                background-color: #004B87;
                color: #FDB913;
            }
            QListWidget#SidebarList::item:selected {
                background-color: #FDB913;
                color: #003366;
                border-left: 4px solid white;
            }
        """)
        self.nav_list.addItem("1. Data & KOP")
        self.nav_list.addItem("2. Surat Permohonan")
        self.nav_list.addItem("3. Surat Undangan")
        self.nav_list.addItem("4. Berita Acara")
        self.nav_list.addItem("5. Laporan Hasil")
        sidebar_layout.addWidget(self.nav_list)

        sidebar_layout.addSpacing(10)

        btn_validator = QPushButton("🔐 Validator Dokumen")
        btn_validator.setObjectName("ValidatorBtn")
        btn_validator.setFixedHeight(45)
        btn_validator.setCursor(Qt.PointingHandCursor)
        btn_validator.setStyleSheet("""
            QPushButton#ValidatorBtn {
                background-color: #FDB913;
                color: #003366;
                border: 2px solid #FFFFFF;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                margin: 5px 15px;
                padding: 8px 12px;
            }
            QPushButton#ValidatorBtn:hover {
                background-color: #FFFFFF;
                color: #004B87;
                border: 2px solid #FDB913;
            }
            QPushButton#ValidatorBtn:pressed {
                background-color: #E5A800;
                color: #002244;
            }
        """)
        btn_validator.clicked.connect(self.open_validator)
        sidebar_layout.addWidget(btn_validator)

        btn_dashboard = QPushButton("📊 Dashboard")
        btn_dashboard.setObjectName("NavBtn")
        btn_dashboard.setFixedHeight(40)
        btn_dashboard.setCursor(Qt.PointingHandCursor)
        btn_dashboard.setStyleSheet("""
            QPushButton#NavBtn {
                background-color: transparent;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 18px;
                margin: 2px 12px;
                text-align: left;
            }
            QPushButton#NavBtn:hover {
                background-color: rgba(253, 185, 19, 0.2);
                color: #FDB913;
            }
            QPushButton#NavBtn:pressed {
                background-color: rgba(253, 185, 19, 0.3);
                color: #FFFFFF;
            }
        """)
        btn_dashboard.clicked.connect(self.open_dashboard)
        sidebar_layout.addWidget(btn_dashboard)

        btn_export = QPushButton("🔄 Ekspor/Impor")
        btn_export.setObjectName("NavBtn")
        btn_export.setFixedHeight(40)
        btn_export.setCursor(Qt.PointingHandCursor)
        btn_export.setStyleSheet("""
            QPushButton#NavBtn {
                background-color: transparent;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 18px;
                margin: 2px 12px;
                text-align: left;
            }
            QPushButton#NavBtn:hover {
                background-color: rgba(253, 185, 19, 0.2);
                color: #FDB913;
            }
            QPushButton#NavBtn:pressed {
                background-color: rgba(253, 185, 19, 0.3);
                color: #FFFFFF;
            }
        """)
        btn_export.clicked.connect(self.open_export_import)
        sidebar_layout.addWidget(btn_export)

        sidebar_layout.addStretch()

        version_label = QLabel("v1.0 - Dev")
        version_label.setObjectName("SidebarFooter")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setFixedHeight(40)
        version_label.setStyleSheet("""
            QLabel#SidebarFooter {
                color: rgba(255,255,255,0.5);
                font-size: 11px;
                background-color: #002244;
                padding: 5px;
            }
        """)
        sidebar_layout.addWidget(version_label)

        parent_layout.addWidget(self.sidebar)

    def open_dashboard(self):
        from .dashboard import DashboardWidget
        dashboard = DashboardWidget(self, self.blockchain_manager)
        self.content_stack.addWidget(dashboard)
        self.content_stack.setCurrentWidget(dashboard)
        self.nav_list.clearSelection()

    def open_export_import(self):
        from .export_dialog import ExportImportDialog
        dialog = ExportImportDialog(self, self.blockchain_manager)
        dialog.exec_()

    def open_validator(self):
        from .validator_dialog import ValidatorDialog
        validator = ValidatorDialog(self)
        validator.exec_()

    def setup_content_area(self, parent_layout):
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("ContentArea")

        self.page_data_kop = QWidget()
        self.page_permohonan = QWidget()
        self.page_undangan = QWidget()
        self.page_berita = QWidget()
        self.page_laporan = QWidget()

        self.setup_page_data_kop()
        self.setup_page_permohonan()
        self.setup_page_undangan()
        self.setup_page_berita()
        self.setup_page_laporan()

        self.content_stack.addWidget(self.page_data_kop)
        self.content_stack.addWidget(self.page_permohonan)
        self.content_stack.addWidget(self.page_undangan)
        self.content_stack.addWidget(self.page_berita)
        self.content_stack.addWidget(self.page_laporan)

        parent_layout.addWidget(self.content_stack)

    def setup_connections(self):
        self.nav_list.currentRowChanged.connect(self.content_stack.setCurrentIndex)
        self.nav_list.setCurrentRow(0)

    def apply_styles(self):
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {self.light_bg}; }}
            QFrame#Sidebar {{ background-color: {self.primary_blue}; border-right: 2px solid {self.accent_gold}; }}
            QLabel#SidebarTitle {{ color: {self.accent_gold}; font-size: 24px; font-weight: bold; background-color: {self.dark_blue}; }}
            QLabel#SidebarFooter {{ color: white; font-size: 12px; background-color: {self.dark_blue}; }}
            QListWidget#SidebarList {{ background-color: transparent; border: none; outline: none; color: white; font-size: 14px; font-weight: bold; }}
            QListWidget#SidebarList::item {{ padding: 18px; border-bottom: 1px solid rgba(255,255,255,0.2); }}
            QListWidget#SidebarList::item:hover {{ background-color: {self.primary_blue}; color: {self.accent_gold}; }}
            QListWidget#SidebarList::item:selected {{ background-color: {self.accent_gold}; color: {self.dark_blue}; border-left: 5px solid white; }}
            QGroupBox {{ border: 2px solid {self.accent_gold}; border-radius: 8px; margin-top: 20px; background-color: white; font-weight: bold; color: {self.primary_blue}; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 15px; padding: 0 5px; color: {self.accent_gold}; }}
            QLineEdit, QTextEdit, QDateEdit, QComboBox, QTextBrowser {{ background-color: white; border: 1px solid {self.accent_gold}; border-radius: 6px; padding: 8px; color: {self.text_dark}; }}
            QLineEdit:focus, QTextEdit:focus, QDateEdit:focus, QComboBox:focus {{ border: 2px solid {self.primary_blue}; }}
            QPushButton {{ background-color: {self.primary_blue}; color: white; border: 2px solid {self.accent_gold}; border-radius: 6px; padding: 10px 20px; font-weight: bold; font-size: 14px; }}
            QPushButton:hover {{ background-color: {self.accent_gold}; color: {self.dark_blue}; }}
            QPushButton:pressed {{ background-color: {self.dark_blue}; color: white; }}
            QPushButton#uploadBtn {{ background-color: white; color: {self.dark_blue}; border: 2px dashed {self.primary_blue}; }}
            QPushButton#uploadBtn:hover {{ background-color: {self.primary_blue}; color: white; }}
            QPushButton#actionBtn {{ background-color: white; color: {self.primary_blue}; border: 2px solid {self.primary_blue}; font-size: 12px; padding: 5px 10px; }}
            QPushButton#actionBtn:hover {{ background-color: {self.primary_blue}; color: white; }}
            QPushButton#publishBtn {{ background-color: {self.primary_blue}; color: white; border: 2px solid {self.accent_gold}; font-weight: bold; }}
            QPushButton#publishBtn:hover {{ background-color: {self.accent_gold}; color: {self.dark_blue}; }}
            QPushButton#ValidatorBtn, QPushButton#NavBtn {{ background-color: transparent; color: white; border: none; border-radius: 8px; font-size: 14px; font-weight: bold; padding: 12px 15px; margin: 3px 10px; text-align: left; }}
            QPushButton#ValidatorBtn:hover, QPushButton#NavBtn:hover {{ background-color: {self.accent_gold}; color: {self.dark_blue}; }}
            QPushButton#ValidatorBtn:pressed, QPushButton#NavBtn:pressed {{ background-color: {self.dark_blue}; color: white; }}
        """)

    def add_shadow_effect(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 75, 135, 30))
        widget.setGraphicsEffect(shadow)

    def _get_document_css(self) -> str:
        return """
        <style>
            @page {
                size: A4;
                margin: 15mm 20mm 15mm 20mm;
                @bottom-center { content: ""; }
            }
            body {
                font-family: 'Times New Roman', Times, serif;
                font-size: 12pt;
                line-height: 1.15;
                color: #1a1a1a;
                margin: 0;
                padding: 0;
                text-align: justify;
                text-justify: inter-word;
            }
            p, div, li, td {
                text-align: justify;
                text-justify: inter-word;
                margin: 2px 0;
                padding: 0;
                line-height: 1.15;
            }
            h1, h2, h3, h4 {
                margin: 3px 0 5px 0;
                padding: 0;
                font-weight: bold;
            }
            h4.judul {
                text-align: center !important;
                font-size: 13pt;
                font-weight: bold;
                margin: 3px 0 5px 0;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            hr {
                border: none;
                border-top: 1px solid #333;
                margin: 4px 0;
                padding: 0;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 3px 0;
            }
            table td {
                padding: 1px 4px;
                vertical-align: top;
                line-height: 1.15;
                text-align: justify;
            }
            .kop-container {
                text-align: center;
                margin-bottom: 2px;
            }
            .kop-container img {
                max-height: 75px;
                max-width: 100%;
            }
            pre {
                white-space: pre-wrap;
                word-wrap: break-word;
                font-family: 'Times New Roman', Times, serif;
                font-size: 11pt;
                line-height: 1.15;
                background-color: #F9F9F9;
                padding: 4px 8px;
                border-radius: 3px;
                border-left: 3px solid #004B87;
                margin: 3px 0;
                text-align: justify;
            }
            ol {
                margin: 3px 0;
                padding-left: 25px;
                text-align: justify;
            }
            ol li {
                margin: 1px 0;
                line-height: 1.15;
                text-align: justify;
            }
            .signature-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 40px;
                margin-bottom: 10px;
                page-break-inside: avoid;
                border: none;
            }
            .signature-table td {
                border: none;
                padding: 0;
                vertical-align: middle;
            }
            .signature-table td.qr-col {
                width: 25%;
                text-align: left;
                padding-right: 20px;
            }
            .signature-table td.ttd-col {
                width: 75%;
                text-align: right;
                padding-left: 20px;
            }
            .signature-table .qr-wrapper {
                display: inline-block;
                text-align: center;
            }
            .signature-table .qr-wrapper img {
                width: 70px;
                height: 70px;
                border: 2px solid #004B87;
                border-radius: 4px;
            }
            .signature-table .qr-wrapper .qr-label {
                font-size: 7px;
                color: #888;
                margin: 2px 0;
                text-align: center;
            }
            .signature-table .qr-wrapper .qr-fallback {
                width: 70px;
                height: 70px;
                border: 2px dashed #004B87;
                border-radius: 4px;
                display: inline-block;
                line-height: 70px;
                font-size: 12px;
                color: #004B87;
                background-color: #F5F7FA;
                text-align: center;
            }
            .signature-table .ttd-col p {
                margin: 2px 0;
                line-height: 1.3;
                text-align: right;
            }
            .doc-footer {
                text-align: center;
                font-size: 7px;
                color: #999;
                margin-top: 8px;
                border-top: 0.5px solid #DDD;
                padding-top: 3px;
                line-height: 1.2;
            }
            .page-break {
                page-break-before: always;
            }
        </style>
        """

    def _wrap_with_css(self, content: str) -> str:
        css = self._get_document_css()
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>LPTBC Document</title>
    {css}
</head>
<body>
    {content}
</body>
</html>"""

    def _generate_qr_code_html(self) -> str:
        try:
            docs = self.blockchain_manager.get_published_documents(limit=1)
            if docs:
                block = self.blockchain_manager.blockchain.get_block_by_hash(docs[0].get('hash', ''))
                if block:
                    signature = block.data.get('signature', '')
                    block_hash = block.hash

                    import qrcode
                    import base64
                    from io import BytesIO
                    import json

                    qr_data = {
                        "hash": block_hash,
                        "signature": signature[:64] if signature else "",
                        "verified": "LPTBC",
                        "timestamp": datetime.now().isoformat()
                    }
                    qr = qrcode.QRCode(box_size=2, border=1)
                    qr.add_data(json.dumps(qr_data))
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="#004B87", back_color="white")
                    buffered = BytesIO()
                    img.save(buffered, format="PNG")
                    img_base64 = base64.b64encode(buffered.getvalue()).decode()

                    return f'''
                    <div class="qr-wrapper">
                        <img src="data:image/png;base64,{img_base64}" />
                        <p class="qr-label">Scan verifikasi</p>
                    </div>
                    '''
        except Exception as e:
            print(f"⚠️ QR Code generation failed: {e}")

        return '''
        <div class="qr-wrapper">
            <div class="qr-fallback">✅</div>
            <p class="qr-label">Terverifikasi</p>
        </div>
        '''

    def create_action_buttons(self, widget: QTextBrowser, name: str, doc_type: Optional[str] = None):
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        btn_copy = QPushButton("📋 Salin Teks")
        btn_copy.setObjectName("actionBtn")
        btn_copy.clicked.connect(lambda: self.copy_output(widget))

        btn_save = QPushButton("💾 Simpan (.TXT / .PDF)")
        btn_save.setObjectName("actionBtn")
        btn_save.clicked.connect(lambda: self.save_output(widget, name))

        btn_publish = QPushButton("📤 Terbitkan ke Blockchain")
        btn_publish.setObjectName("publishBtn")
        
        if doc_type:
            btn_publish.clicked.connect(lambda: self.publish_document(doc_type, widget))
        else:
            btn_publish.setEnabled(False)

        btn_layout.addWidget(btn_copy)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_publish)

        return btn_layout

    def copy_output(self, widget: QTextBrowser):
        QApplication.clipboard().setText(widget.toPlainText())

    def save_output(self, widget: QTextBrowser, default_name: str):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Simpan Dokumen", 
            f"{default_name}.pdf",
            "PDF Files (*.pdf);;Text Files (*.txt);;HTML Files (*.html)", 
            options=options
        )
        
        if not file_path:
            return

        try:
            if file_path.endswith('.pdf'):
                from .pdf_exporter import PDFExporter
                
                # Gunakan data dokumen yang sedang aktif jika ada
                doc_data = self.current_doc_data
                signature = None
                block_hash = None
                
                # Jika belum ada data aktif, coba ambil dari blockchain terbaru
                if doc_data is None:
                    docs = self.blockchain_manager.get_published_documents(limit=1)
                    if docs:
                        doc_data = docs[0]
                        block = self.blockchain_manager.blockchain.get_block_by_hash(doc_data.get('hash', ''))
                        if block:
                            signature = block.data.get('signature', '')
                            block_hash = block.hash
                            doc_info = {
                                "type": block.data.get('type', ''),
                                "nomor": block.data.get('nomor', ''),
                                "tanggal": block.data.get('tanggal', ''),
                                "judul": block.data.get('judul', '')
                            }
                            doc_data = doc_info
                
                exporter = PDFExporter()
                success = exporter.export_to_pdf(
                    html_content=widget.toHtml(),
                    output_path=file_path,
                    doc_data=doc_data,
                    signature=signature,
                    block_hash=block_hash
                )
                
                if success:
                    self.show_status_message(f"✅ PDF saved: {os.path.basename(file_path)}")
                else:
                    self.show_status_message("❌ Gagal export PDF")
            elif file_path.endswith('.html'):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(widget.toHtml())
                self.show_status_message(f"✅ HTML saved: {os.path.basename(file_path)}")
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(widget.toPlainText())
                self.show_status_message(f"✅ TXT saved: {os.path.basename(file_path)}")
        except Exception as e:
            self.show_status_message(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

    def show_status_message(self, message: str):
        if hasattr(self, 'statusBar'):
            self.statusBar().showMessage(message, 5000)

    def get_kop_html(self) -> str:
        if self.kop_path and os.path.exists(self.kop_path):
            return f'<img src="{os.path.abspath(self.kop_path)}" style="max-height: 75px; max-width: 100%;">'
        return "<h3 style='text-align: center; color: #004B87;'>[KOP BALAI]</h3>"

    def refresh_published_list(self):
        try:
            docs = self.blockchain_manager.get_published_documents(limit=50)
            if docs:
                self.show_status_message(f"📚 Total dokumen terbit: {len(docs)}")
            else:
                self.show_status_message("📚 Belum ada dokumen yang diterbitkan")
        except Exception as e:
            self.show_status_message(f"⚠️ Error refresh: {str(e)}")

    def publish_document(self, doc_type: str, widget: QTextBrowser, file_path: Optional[str] = None):
        try:
            doc_data = self._get_document_data(doc_type)
            temp_file = None
            try:
                import tempfile
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='wb')
                temp_file.write(widget.toHtml().encode('utf-8'))
                temp_file.close()
                file_path = temp_file.name
            except Exception as e:
                print(f"   ⚠️ Could not create temp file: {e}")
                file_path = None

            result = self.blockchain_manager.publish_document(
                doc_type=doc_type,
                doc_data=doc_data,
                file_path=file_path
            )

            if result.get("verified"):
                block_hash = result["block"]["hash"][:12]
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                current_html = widget.toHtml()
                watermark = f"""
                <div style='border: 3px solid #004B87; background-color: #FDB91320; 
                            padding: 15px; margin: 10px 0; border-radius: 8px;'>
                    <p style='color: #004B87; font-weight: bold; text-align: center; font-size: 16px;'>
                        ✅ TELAH DITERBITKAN KE BLOCKCHAIN
                    </p>
                    <p style='font-size: 12px; color: #666; text-align: center;'>
                        <b>Hash:</b> {block_hash}... | <b>Tanggal:</b> {timestamp}
                    </p>
                    <p style='font-size: 10px; color: #999; text-align: center;'>
                        Block Index: {result['block']['block_index']}
                    </p>
                </div>
                """
                widget.setHtml(watermark + current_html)

                self.show_status_message(f"✅ Berhasil! Hash: {block_hash}...")
                self.refresh_published_list()
            else:
                self.show_status_message(f"❌ {result.get('message', 'Gagal')}")
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"❌ [EXCEPTION] {str(e)}\n{error_trace}")
            self.show_status_message(f"❌ Error: {str(e)}")
        finally:
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception as e:
                    print(f"   ⚠️ Could not delete temp file: {e}")

    def _get_document_data(self, doc_type: str) -> Dict[str, Any]:
        data = {
            "nomor": "",
            "tanggal": "",
            "judul": "",
            "lokasi": self.lokasi.text(),
            "nama_balai": self.nama_balai.text(),
            "kepala_balai": self.kepala_balai.text(),
            "nip_kepala": self.nip_kepala.text(),
            "ketua_tim": self.ketua_tim.text(),
            "nip_ketua": self.nip_ketua.text()
        }

        if doc_type == "Surat Permohonan":
            data.update({
                "nomor": self.nomor_permohonan.text(),
                "tanggal": self._format_tanggal_indonesia(self.tanggal_permohonan.date()),
                "judul": self.hal_permohonan.text(),
                "tahun": self.tahun_permohonan.text(),
                "agenda": self.agenda_permohonan.toPlainText(),
                "waktu": self.waktu_permohonan.text(),
                "tempat": self.tempat_permohonan.text()
            })
        elif doc_type == "Surat Undangan":
            data.update({
                "nomor": self.nomor_undangan.text(),
                "tanggal": self._format_tanggal_indonesia(self.tanggal_undangan.date()),
                "judul": "Undangan Rekonsiliasi Data Harga Satuan Pokok",
                "sifat": self.sifat_undangan.text(),
                "lampiran": self.lampiran_undangan.text(),
                "tujuan": self.tujuan_undangan.toPlainText(),
                "narahubung": self.narahubung.text(),
                "tahun": self.tahun_undangan.text(),
                "waktu": self.waktu_undangan.text(),
                "tempat": self.tempat_undangan.text()
            })
        elif doc_type == "Berita Acara":
            data.update({
                "nomor": self.no_ba.text(),
                "tanggal": self._format_tanggal_indonesia(self.tanggal_ba.date()),
                "judul": "Berita Acara Penetapan Harga",
                "tempat": self.tempat_ba.text(),
                "waktu": self.waktu_ba.text(),
                "pejabat": self.pejabat_ba.text(),
                "nip_pejabat": self.nip_ba.text(),
                "isi": self.isi_ba.toPlainText()
            })
        elif doc_type == "Laporan Hasil":
            data.update({
                "nomor": self.nomor_laporan.text(),
                "tanggal": self._format_tanggal_indonesia(self.tanggal_laporan.date()),
                "judul": "Laporan Hasil Rekonsiliasi",
                "penyusun": self.penyusun_laporan.text(),
                "dasar": self.dasar_laporan.toPlainText(),
                "hadir": self.hadir_laporan.text(),
                "catatan": self.catatan_laporan.toPlainText(),
                "tempat_rekonsiliasi": self.tempat_laporan.text(),
                "tanggal_rekonsiliasi": self.tanggal_laporan_teks.text(),
                "no_berita_acara": self.no_berita_acara.text()
            })

        return data

    # ============================================================
    # PAGE: DATA & KOP
    # ============================================================
    def setup_page_data_kop(self):
        layout = QHBoxLayout(self.page_data_kop)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        form_panel = QGroupBox("Pengaturan Data & KOP Surat")
        self.add_shadow_effect(form_panel)
        form_layout = QFormLayout(form_panel)

        self.nama_balai = QLineEdit("Balai Teknis ...")
        self.lokasi = QLineEdit("Jakarta")
        self.kepala_balai = QLineEdit("Nama Kepala Balai")
        self.nip_kepala = QLineEdit("NIP. 123456789")
        self.ketua_tim = QLineEdit("Nama Ketua Tim")
        self.nip_ketua = QLineEdit("NIP. 987654321")

        form_layout.addRow("Nama Balai:", self.nama_balai)
        form_layout.addRow("Lokasi:", self.lokasi)
        form_layout.addRow("Kepala Balai:", self.kepala_balai)
        form_layout.addRow("NIP Kepala:", self.nip_kepala)
        form_layout.addRow("Ketua Tim:", self.ketua_tim)
        form_layout.addRow("NIP Ketua:", self.nip_ketua)

        upload_layout = QHBoxLayout()
        btn_upload = QPushButton("📤 Upload Gambar KOP (PNG/JPG)")
        btn_upload.setObjectName("uploadBtn")
        btn_upload.clicked.connect(self.upload_kop)
        btn_reset = QPushButton("🔄 Reset KOP")
        btn_reset.setObjectName("uploadBtn")
        btn_reset.clicked.connect(self.clear_kop)
        upload_layout.addWidget(btn_upload)
        upload_layout.addWidget(btn_reset)
        form_layout.addRow("KOP Surat:", upload_layout)

        preview_panel = QGroupBox("Preview Data KOP")
        self.add_shadow_effect(preview_panel)
        preview_layout = QVBoxLayout(preview_panel)

        self.output_umum = QTextBrowser()
        preview_layout.addWidget(self.output_umum)
        preview_layout.addLayout(self.create_action_buttons(
            self.output_umum, 
            "Kartu_Data_Balai"
        ))

        for widget in [self.nama_balai, self.lokasi, self.kepala_balai, 
                       self.nip_kepala, self.ketua_tim, self.nip_ketua]:
            widget.textChanged.connect(self.update_preview_umum)

        layout.addWidget(form_panel, 1)
        layout.addWidget(preview_panel, 2)

    def update_preview_umum(self):
        kop = self.get_kop_html()
        teks = f"""
        <div style='text-align: center;'>{kop}</div>
        <br>
        <h2 style='text-align:center; color:{self.primary_blue};'>KARTU DATA BALAI</h2>
        <hr>
        <p><b>Nama Balai:</b> {self.nama_balai.text()}</p>
        <p><b>Lokasi:</b> {self.lokasi.text()}</p>
        <p><b>Kepala Balai:</b> {self.kepala_balai.text()}</p>
        <p><b>NIP:</b> {self.nip_kepala.text()}</p>
        <p><b>Ketua Tim:</b> {self.ketua_tim.text()}</p>
        <p><b>NIP:</b> {self.nip_ketua.text()}</p>
        """
        self.output_umum.setHtml(teks)

    # ============================================================
    # PAGE: SURAT PERMOHONAN
    # ============================================================
    def setup_page_permohonan(self):
        layout = QHBoxLayout(self.page_permohonan)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        form_panel = QGroupBox("Form Surat Permohonan Rekonsiliasi")
        self.add_shadow_effect(form_panel)
        form_layout = QFormLayout(form_panel)

        self.nomor_permohonan = QLineEdit("SP-.......")
        self.tanggal_permohonan = QDateEdit(QDate.currentDate())
        self.tanggal_permohonan.setCalendarPopup(True)
        self.hal_permohonan = QLineEdit("Permohonan Rekonsiliasi Pengumpulan Data Harga Satuan Pokok")
        self.tahun_permohonan = QLineEdit("2026")
        
        self.waktu_permohonan = QLineEdit("...")
        self.tempat_permohonan = QLineEdit("Jakarta")
        
        self.agenda_permohonan = QTextEdit()
        self.agenda_permohonan.setPlaceholderText(
            "1. Pembahasan Kewajaran Harga\n2. Keterbandingan Antar Wilayah\n3. Penetapan Harga"
        )
        self.agenda_permohonan.setFixedHeight(120)

        form_layout.addRow("Nomor:", self.nomor_permohonan)
        form_layout.addRow("Tanggal:", self.tanggal_permohonan)
        form_layout.addRow("Hal:", self.hal_permohonan)
        form_layout.addRow("Tahun Kegiatan:", self.tahun_permohonan)
        form_layout.addRow("Waktu:", self.waktu_permohonan)
        form_layout.addRow("Tempat:", self.tempat_permohonan)
        form_layout.addRow("Agenda:", self.agenda_permohonan)

        btn_generate = QPushButton("Generate Teks Permohonan")
        btn_generate.clicked.connect(self.generate_permohonan)
        form_layout.addRow(btn_generate)

        preview_panel = QGroupBox("Preview Surat Permohonan")
        self.add_shadow_effect(preview_panel)
        preview_layout = QVBoxLayout(preview_panel)

        self.output_permohonan = QTextBrowser()
        preview_layout.addWidget(self.output_permohonan)
        preview_layout.addLayout(self.create_action_buttons(
            self.output_permohonan,
            "Surat_Permohonan",
            doc_type="Surat Permohonan"
        ))

        layout.addWidget(form_panel, 1)
        layout.addWidget(preview_panel, 2)

    def generate_permohonan(self):
        self.current_doc_data = self._get_document_data("Surat Permohonan")  # Simpan data aktif
        
        kop = self.get_kop_html()
        nomor = self.nomor_permohonan.text()
        tanggal = self._format_tanggal_indonesia(self.tanggal_permohonan.date())
        hal = self.hal_permohonan.text()
        tahun = self.tahun_permohonan.text()
        waktu = self.waktu_permohonan.text()
        tempat = self.tempat_permohonan.text()
        agenda = self._format_text(self.agenda_permohonan.toPlainText())
        qr_html = self._generate_qr_code_html()

        ttd_html = f"""
        <p>{tanggal}</p>
        <p>Ketua Tim Teknis Harga Satuan Pokok Balai</p>
        <p>(Cap dan Ttd)</p>
        <p><b>{self.ketua_tim.text()}</b><br>{self.nip_ketua.text()}</p>
        """

        content = f"""
        <div class="kop-container">{kop}</div>
        <h4 class="judul">NOTA DINAS</h4>
        <hr>
        <p><b>Nomor</b> : {nomor}</p>
        <p><b>Yth.</b> : Kepala Balai...</p>
        <p><b>Dari</b> : Tim Teknis Harga Satuan Pokok Balai</p>
        <p><b>Hal</b> : {hal}</p>
        <p><b>Tanggal</b> : {tanggal}</p>
        <p>Dalam rangka proses Pengumpulan Data Harga Satuan Pokok Sektor Konstruksi Tahun {tahun} dan pembahasan lebih lanjut hasil pemeriksaan data pengumpulan data Harga Satuan Pokok, dengan hormat kami mengusulkan pelaksanaan kegiatan rekonsiliasi Harga Satuan Pokok yang akan dilaksanakan:</p>
        <p>Hari, Tanggal : {tanggal}<br>Waktu : {waktu}<br>Tempat : {tempat}</p>
        <p>Agenda :<br>{agenda}</p>
        <p>Kami mohon persetujuan Bapak/Ibu agar dapat menyetujui dan memfasilitasi pelaksanaan kegiatan tersebut.</p>
        <p>Demikian kami sampaikan, atas perhatian Bapak/Ibu, kami ucapkan terima kasih.</p>
    
        <table class="signature-table">
            <tr>
                <td class="qr-col">{qr_html}</td>
                <td class="ttd-col">{ttd_html}</td>
            </tr>
        </table>
        <div class="doc-footer">Dokumen ini diterbitkan melalui LPTBC dan dilindungi oleh Digital Signature</div>
        """
        self.output_permohonan.setHtml(self._wrap_with_css(content))

    # ============================================================
    # PAGE: SURAT UNDANGAN
    # ============================================================
    def setup_page_undangan(self):
        layout = QHBoxLayout(self.page_undangan)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        form_panel = QGroupBox("Form Surat Undangan Rekonsiliasi")
        self.add_shadow_effect(form_panel)
        form_layout = QFormLayout(form_panel)

        self.nomor_undangan = QLineEdit("Nomor : ............")
        self.sifat_undangan = QLineEdit("Segera")
        self.lampiran_undangan = QLineEdit("Satu Berkas")
        self.tujuan_undangan = QTextEdit(
            "1. Kepala BP2JK Wilayah,\n2. Tim Pelaksana Pengumpulan Data Harga Satuan Pokok Balai...."
        )
        self.tujuan_undangan.setFixedHeight(80)
        self.tanggal_undangan = QDateEdit(QDate.currentDate())
        self.tanggal_undangan.setCalendarPopup(True)
        self.narahubung = QLineEdit("Nama Narahubung / No.HP")
        
        self.tahun_undangan = QLineEdit("2026")
        self.waktu_undangan = QLineEdit("...")
        self.tempat_undangan = QLineEdit("...")

        form_layout.addRow("Nomor:", self.nomor_undangan)
        form_layout.addRow("Sifat:", self.sifat_undangan)
        form_layout.addRow("Lampiran:", self.lampiran_undangan)
        form_layout.addRow("Yth (Tujuan):", self.tujuan_undangan)
        form_layout.addRow("Tanggal:", self.tanggal_undangan)
        form_layout.addRow("Tahun Kegiatan:", self.tahun_undangan)
        form_layout.addRow("Waktu:", self.waktu_undangan)
        form_layout.addRow("Tempat:", self.tempat_undangan)
        form_layout.addRow("Narahubung:", self.narahubung)

        btn_generate = QPushButton("Generate Teks Undangan")
        btn_generate.clicked.connect(self.generate_undangan)
        form_layout.addRow(btn_generate)

        preview_panel = QGroupBox("Preview Surat Undangan")
        self.add_shadow_effect(preview_panel)
        preview_layout = QVBoxLayout(preview_panel)

        self.output_undangan = QTextBrowser()
        preview_layout.addWidget(self.output_undangan)
        preview_layout.addLayout(self.create_action_buttons(
            self.output_undangan,
            "Surat_Undangan",
            doc_type="Surat Undangan"
        ))

        layout.addWidget(form_panel, 1)
        layout.addWidget(preview_panel, 2)

    def generate_undangan(self):
        self.current_doc_data = self._get_document_data("Surat Undangan")  # Simpan data aktif
        
        kop = self.get_kop_html()
        tanggal = self._format_tanggal_indonesia(self.tanggal_undangan.date())
        no = self.nomor_undangan.text()
        sifat = self.sifat_undangan.text()
        lampiran = self.lampiran_undangan.text()
        tujuan = self._format_text(self.tujuan_undangan.toPlainText())
        narahubung = self.narahubung.text()
        tahun = self.tahun_undangan.text()
        waktu = self.waktu_undangan.text()
        tempat = self.tempat_undangan.text()
        qr_html = self._generate_qr_code_html()

        ttd_html = f"""
        <p>{tanggal}</p>
        <p>Kepala Balai.....</p>
        <p>(Cap dan Ttd)</p>
        <p><b>{self.kepala_balai.text()}</b><br>{self.nip_kepala.text()}</p>
        """

        content = f"""
        <div class="kop-container">{kop}</div>
        <br>
        <table>
            <tr><td width="15%"><b>Nomor</b></td><td width="1%">:</td><td>{no}</td><td align="right">{self.lokasi.text()},</td></tr>
            <tr><td><b>Sifat</b></td><td>:</td><td>{sifat}</td></tr>
            <tr><td><b>Lampiran</b></td><td>:</td><td>{lampiran}</td></tr>
            <tr><td><b>Hal</b></td><td>:</td><td>Undangan Rekonsiliasi Data Harga Satuan Pokok</td></tr>
        </table>
        <p><b>Yth.</b><br>{tujuan}</p>
        <p><b>di Tempat</b></p>
        <p>Dalam rangka Pengumpulan Data Harga Satuan Pokok Sektor Konstruksi Tahun {tahun}, kami akan melaksanakan rekonsiliasi hasil pengumpulan data Harga Satuan Pokok yang akan dilaksanakan:</p>
        <p>Hari/Tanggal : {tanggal}<br>Waktu : {waktu}<br>Tempat : {tempat}</p>
        <p>Agenda :<br>1. Pembahasan Kewajaran Harga Satuan Pokok<br>2. Pembahasan Keterbandingan Harga Satuan Pokok antar Wilayah<br>3. Penetapan Harga Satuan Pokok</p>
        <p>Untuk Informasi dan koordinasi lebih lanjut dapat menghubungi narahubung Balai Teknis melalui Sdr. {narahubung}</p>
        <p>Demikian kami sampaikan, atas perhatian dan kehadiran Bapak/Ibu, kami ucapkan terima kasih.</p>
    
        <table class="signature-table">
            <tr>
                <td class="qr-col">{qr_html}</td>
                <td class="ttd-col">{ttd_html}</td>
            </tr>
        </table>
        <div class="doc-footer">Dokumen ini diterbitkan melalui LPTBC dan dilindungi por Digital Signature</div>
        """
        self.output_undangan.setHtml(self._wrap_with_css(content))

    # ============================================================
    # PAGE: BERITA ACARA
    # ============================================================
    def setup_page_berita(self):
        layout = QHBoxLayout(self.page_berita)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        form_panel = QGroupBox("Form Berita Acara Penetapan Harga")
        self.add_shadow_effect(form_panel)
        form_layout = QFormLayout(form_panel)

        self.no_ba = QLineEdit("NOMOR ............")
        self.tanggal_ba = QDateEdit(QDate.currentDate())
        self.tanggal_ba.setCalendarPopup(True)
        self.tempat_ba = QLineEdit("Jakarta")
        self.waktu_ba = QLineEdit("...")
        self.pejabat_ba = QLineEdit("Nama Pejabat")
        self.nip_ba = QLineEdit("NIP. 123456789")
        self.isi_ba = QTextEdit()
        self.isi_ba.setPlainText(
            "1. Kuisioner survei yang berisi:\n   a. Data Harga Satuan Pokok Material, Peralatan;\n   b. Data Upah Tenaga Kerja Konstruksi;\n   c. Informasi Vendor;\n2. Dokumen pendukung...\n3. SK Tim Survei."
        )
        self.isi_ba.setFixedHeight(150)

        form_layout.addRow("Nomor BA:", self.no_ba)
        form_layout.addRow("Tanggal:", self.tanggal_ba)
        form_layout.addRow("Tempat:", self.tempat_ba)
        form_layout.addRow("Waktu:", self.waktu_ba)
        form_layout.addRow("Nama Pejabat:", self.pejabat_ba)
        form_layout.addRow("NIP Pejabat:", self.nip_ba)
        form_layout.addRow("Isi Lampiran/BA:", self.isi_ba)

        btn_generate_ba = QPushButton("Generate Teks Berita Acara")
        btn_generate_ba.clicked.connect(self.generate_berita_acara)
        form_layout.addRow(btn_generate_ba)

        preview_panel = QGroupBox("Preview Hasil Generate")
        self.add_shadow_effect(preview_panel)
        preview_layout = QVBoxLayout(preview_panel)

        self.output_ba = QTextBrowser()
        preview_layout.addWidget(self.output_ba)
        preview_layout.addLayout(self.create_action_buttons(
            self.output_ba,
            "Berita_Acara",
            doc_type="Berita Acara"
        ))

        layout.addWidget(form_panel, 1)
        layout.addWidget(preview_panel, 2)

    def generate_berita_acara(self):
        self.current_doc_data = self._get_document_data("Berita Acara")  # Simpan data aktif
        
        kop = self.get_kop_html()
        no = self.no_ba.text()
        
        selected_date = self.tanggal_ba.date()
        hari = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"][selected_date.dayOfWeek() - 1]
        tanggal_angka = selected_date.day()
        bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
                 "Juli", "Agustus", "September", "Oktober", "November", "Desember"][selected_date.month() - 1]
        tahun = selected_date.year()
        
        tempat = self.tempat_ba.text()
        waktu = self.waktu_ba.text()
        pejabat = self.pejabat_ba.text()
        nip = self.nip_ba.text()
        isi = self._format_text(self.isi_ba.toPlainText())
        qr_html = self._generate_qr_code_html()

        ttd_html = f"""
        <p>{hari}, {tanggal_angka} {bulan} {tahun}</p>
        <p>Kepala Balai {self.nama_balai.text()}</p>
        <p>(Cap dan Ttd)</p>
        <p><b>{pejabat}</b><br>{nip}</p>
        """

        content = f"""
        <div class="kop-container">{kop}</div>
        <h4 class="judul">{no}</h4>
        <hr>
    
        <div class="no-page-break">
            <p>Pada hari ini {hari}, Tanggal {tanggal_angka}, Bulan {bulan}, Tahun {tahun}, bertempat di {tempat} pada pukul {waktu}, kami yang bertandatangan dibawah ini:</p>
            <p><b>Nama</b> : {pejabat}<br><b>NIP</b> : {nip}<br><b>Jabatan</b> : Kepala Balai {self.nama_balai.text()}</p>
            <p>Dengan ini menyatakan bahwa Balai {self.nama_balai.text()} telah menetapkan Harga Satuan Pokok Material, Peralatan, Tenaga Kerja Konstruksi yang menjadi kebutuhan paket di lingkungan balai dan sebagai sumber database fitur harga satuan yang merupakan fitur dari SIPASTI. Bersama Berita Acara ini kami lampirkan:</p>
            <pre>{isi}</pre>
            <p>Demikian berita acara ini dibuat dengan sebenarnya dapat dipergunakan sebagai mestinya.</p>
        </div>
    
        <table class="signature-table keep-together">
            <tr>
                <td class="qr-col">{qr_html}</td>
                <td class="ttd-col">{ttd_html}</td>
            </tr>
        </table>
        <div class="doc-footer">Dokumen ini diterbitkan melalui LPTBC dan dilindungi oleh Digital Signature</div>
        """
        self.output_ba.setHtml(self._wrap_with_css(content))

    # ============================================================
    # PAGE: LAPORAN HASIL
    # ============================================================
    def setup_page_laporan(self):
        layout = QHBoxLayout(self.page_laporan)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        form_panel = QGroupBox("Form Laporan Hasil Rekonsiliasi")
        self.add_shadow_effect(form_panel)
        form_layout = QFormLayout(form_panel)

        self.nomor_laporan = QLineEdit("LH-.......")
        self.dasar_laporan = QTextEdit()
        self.dasar_laporan.setPlaceholderText("Berdasarkan surat ... tanggal ...")
        self.dasar_laporan.setFixedHeight(80)
        self.hadir_laporan = QLineEdit("Dihadiri oleh ...")
        self.catatan_laporan = QTextEdit()
        self.catatan_laporan.setPlaceholderText("a. ...\nb. ...\nc. ...")
        self.catatan_laporan.setFixedHeight(100)
        self.tanggal_laporan = QDateEdit(QDate.currentDate())
        self.tanggal_laporan.setCalendarPopup(True)
        self.penyusun_laporan = QLineEdit("Nama Ketua Tim")
        
        self.tempat_laporan = QLineEdit("Jakarta")
        self.tanggal_laporan_teks = QLineEdit("4 September 2026")
        self.no_berita_acara = QLineEdit("NOMOR ............")

        form_layout.addRow("Nomor:", self.nomor_laporan)
        form_layout.addRow("Dasar Rapat:", self.dasar_laporan)
        form_layout.addRow("Kehadiran:", self.hadir_laporan)
        form_layout.addRow("Catatan:", self.catatan_laporan)
        form_layout.addRow("Tanggal Surat:", self.tanggal_laporan)
        form_layout.addRow("Penyusun:", self.penyusun_laporan)
        form_layout.addRow("Tempat Rekonsiliasi:", self.tempat_laporan)
        form_layout.addRow("Tanggal Rekonsiliasi:", self.tanggal_laporan_teks)
        form_layout.addRow("Nomor Berita Acara:", self.no_berita_acara)

        btn_generate_lap = QPushButton("Generate Teks Laporan")
        btn_generate_lap.clicked.connect(self.generate_laporan)
        form_layout.addRow(btn_generate_lap)

        preview_panel = QGroupBox("Preview Laporan Hasil")
        self.add_shadow_effect(preview_panel)
        preview_layout = QVBoxLayout(preview_panel)

        self.output_laporan = QTextBrowser()
        preview_layout.addWidget(self.output_laporan)
        preview_layout.addLayout(self.create_action_buttons(
            self.output_laporan,
            "Laporan_Hasil",
            doc_type="Laporan Hasil"
        ))

        layout.addWidget(form_panel, 1)
        layout.addWidget(preview_panel, 2)

    def generate_laporan(self):
        self.current_doc_data = self._get_document_data("Laporan Hasil")  # Simpan data aktif
        
        kop = self.get_kop_html()
        nomor = self.nomor_laporan.text()
        dasar = self._format_text(self.dasar_laporan.toPlainText())
        hadir = self.hadir_laporan.text()
        catatan = self._format_text(self.catatan_laporan.toPlainText())
        tanggal = self._format_tanggal_indonesia(self.tanggal_laporan.date())
        penyusun = self.penyusun_laporan.text()
        
        tempat_rekonsiliasi = self.tempat_laporan.text()
        tanggal_rekonsiliasi = self.tanggal_laporan_teks.text()
        no_berita_acara = self.no_berita_acara.text()
        
        qr_html = self._generate_qr_code_html()

        ttd_html = f"""
        <p>{tanggal}</p>
        <p>Ketua Tim Teknis Harga Satuan Pokok Balai</p>
        <p>(Cap dan Ttd)</p>
        <p><b>{penyusun}</b><br>{self.nip_ketua.text()}</p>
        """

        content = f"""
        <div class="kop-container">{kop}</div>
        <h4 class="judul">NOTA DINAS</h4>
        <hr>
        <p><b>Nomor</b> : {nomor}</p>
        <p><b>Yth.</b> : Kepala Balai...</p>
        <p><b>Dari</b> : Tim Teknis Harga Satuan Pokok Balai</p>
        <p><b>Hal</b> : Penyampaian Hasil Rekonsiliasi Pengumpulan Data Harga Satuan Pokok</p>
        <p><b>Tanggal</b> : {tanggal}</p>
        <p>Sehubungan dengan hasil rekonsiliasi yang dilaksanakan pada {tanggal_rekonsiliasi} di {tempat_rekonsiliasi}, bersama ini kami sampaikan hal-hal sebagai berikut:</p>
        <ol>
            <li>Pelaksanaan rapat dilakukan berdasarkan: {dasar}</li>
            <li>Pelaksanaan rapat dihadiri oleh: {hadir}</li>
            <li>Adapun beberapa hal yang menjadi catatan selama rekonsiliasi, antara lain: <br>{catatan}</li>
            <li>Hasil kesepakatan harga di rekonsiliasi, disampaikan dalam draft Berita Acara Penetapan Harga Nomor {no_berita_acara} (sebagaimana terlampir).</li>
        </ol>
        <p>Demikian kami sampaikan untuk mohon arahan dan persetujuan Bapak/Ibu Atas perhatian Bapak/Ibu diucapkan terima kasih.</p>
    
        <table class="signature-table">
            <tr>
                <td class="qr-col">{qr_html}</td>
                <td class="ttd-col">{ttd_html}</td>
            </tr>
        </table>
        <div class="doc-footer">Dokumen ini diterbitkan melalui LPTBC dan dilindungi oleh Digital Signature</div>
        """
        self.output_laporan.setHtml(self._wrap_with_css(content))

    # ============================================================
    # KOP FUNCTIONS
    # ============================================================
    def upload_kop(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Pilih Gambar KOP Surat", 
            "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.kop_path = file_path
            self.update_all_previews()

    def clear_kop(self):
        self.kop_path = None
        self.update_all_previews()

    def update_all_previews(self):
        self.update_preview_umum()
        self.generate_permohonan()
        self.generate_undangan()
        self.generate_berita_acara()
        self.generate_laporan()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())