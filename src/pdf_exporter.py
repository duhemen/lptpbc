# src/pdf_exporter.py
import os
import json
import tempfile
from datetime import datetime
from typing import Optional, Dict, Any
import hashlib
import base64
from io import BytesIO

from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter

import qrcode


class PDFExporter:
    def __init__(self):
        pass

    def export_to_pdf(self, html_content: str, output_path: str,
                      doc_data: Optional[Dict[str, Any]] = None,
                      signature: Optional[str] = None,
                      block_hash: Optional[str] = None) -> bool:
        try:
            watermark_html = self._create_watermark_html(doc_data, block_hash, signature)
            full_html = self._inject_watermark(html_content, watermark_html)

            with tempfile.NamedTemporaryFile(mode='w', suffix='.html',
                                            encoding='utf-8', delete=False) as f:
                f.write(full_html)
                temp_path = f.name

            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(output_path)
            printer.setPageSize(QPrinter.A4)
            printer.setPageMargins(10, 15, 10, 15, QPrinter.Millimeter)

            doc = QTextDocument()
            doc.setHtml(full_html)
            doc.print_(printer)

            os.unlink(temp_path)

            if signature and block_hash:
                try:
                    qr_data = {
                        "hash": block_hash,
                        "signature": signature[:64],
                        "verified": "LPTBC",
                        "timestamp": datetime.now().isoformat()
                    }
                    qr = qrcode.QRCode(
                        version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=4,
                        border=4,
                    )
                    qr.add_data(json.dumps(qr_data))
                    qr.make(fit=True)
                    qr_image = qr.make_image(fill_color="#004B87", back_color="white")
                    qr_path = output_path.replace('.pdf', '_qrcode.png')
                    qr_image.save(qr_path, 'PNG')
                    print(f"✅ QR Code saved: {qr_path}")
                except Exception as e:
                    print(f"⚠️ QR Code save failed: {e}")

            return True
        except Exception as e:
            print(f"❌ Error exporting to PDF: {e}")
            return False

    def _inject_watermark(self, html_content: str, watermark_html: str) -> str:
        if '</head>' in html_content:
            return html_content.replace('</head>', watermark_html + '</head>')
        elif '<body' in html_content:
            return html_content.replace('<body', watermark_html + '<body')
        else:
            return watermark_html + html_content

    def _create_watermark_html(self, doc_data: Optional[Dict[str, Any]],
                               block_hash: Optional[str],
                               signature: Optional[str]) -> str:
        doc_type = doc_data.get('type', '') if doc_data else ''
        doc_nomor = doc_data.get('nomor', '') if doc_data else ''

        return f'''
        <style>
            .watermark-badge {{
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) rotate(-30deg);
                font-size: 100px;
                color: rgba(0, 75, 135, 0.04);
                font-weight: bold;
                pointer-events: none;
                z-index: -1;
                user-select: none;
            }}
            .watermark-header {{
                position: absolute;
                top: 4px;
                right: 8px;
                font-size: 5px;
                color: rgba(0, 75, 135, 0.2);
                text-align: right;
                z-index: 0;
                pointer-events: none;
                line-height: 1.2;
            }}
            .watermark-footer {{
                position: absolute;
                bottom: 4px;
                left: 0;
                right: 0;
                text-align: center;
                font-size: 5px;
                color: rgba(153, 153, 153, 0.3);
                border-top: 0.5px solid rgba(221, 221, 221, 0.2);
                padding-top: 2px;
                pointer-events: none;
                z-index: 0;
            }}
        </style>

        <div class="watermark-badge">⚡ TERVERIFIKASI</div>
        <div class="watermark-header">
            LPTBC | {block_hash[:12] if block_hash else 'N/A'}...
            <br>
            {doc_type} | {doc_nomor}
        </div>
        <div class="watermark-footer">LPTBC - Verifikasi di Validator</div>
        '''