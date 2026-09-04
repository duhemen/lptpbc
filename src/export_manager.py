# src/export_manager.py
import os
import json
import shutil
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import zipfile


class ExportManager:
    def __init__(self, export_dir: str = "data/exports"):
        self.export_dir = export_dir
        os.makedirs(export_dir, exist_ok=True)
        
        self.blockchain_file = "src/data/lpt_chain.json"
        self.db_file = "src/data/blockchain.db"
        self.cert_dir = "output/published"
    
    def export_blockchain(self, filename: Optional[str] = None) -> Tuple[bool, str, str]:
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"lptbc_backup_{timestamp}.lptbc"
            
            export_path = os.path.join(self.export_dir, filename)
            
            if not os.path.exists(self.blockchain_file):
                return False, "", "Blockchain file tidak ditemukan!"
            
            with open(self.blockchain_file, 'r') as f:
                chain_data = json.load(f)
            
            export_data = {
                "version": "LPTBC-EXPORT-1.0",
                "exported_at": datetime.now().isoformat(),
                "blockchain": chain_data,
                "metadata": {
                    "total_blocks": len(chain_data.get("blocks", [])),
                    "verified": chain_data.get("verified", False),
                    "exported_by": "LPTBC",
                    "blockchain_hash": hashlib.sha256(
                        json.dumps(chain_data, sort_keys=True).encode()
                    ).hexdigest()
                }
            }
            
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.writestr("blockchain.json", json.dumps(export_data, indent=2))
                
                if os.path.exists(self.cert_dir):
                    for cert_file in os.listdir(self.cert_dir):
                        if cert_file.endswith('.cert.json'):
                            cert_path = os.path.join(self.cert_dir, cert_file)
                            zipf.write(cert_path, f"certs/{cert_file}")
                
                metadata = {
                    "exported_at": datetime.now().isoformat(),
                    "total_blocks": len(chain_data.get("blocks", [])),
                    "total_certs": len([f for f in os.listdir(self.cert_dir) 
                                       if f.endswith('.cert.json')])
                }
                zipf.writestr("metadata.json", json.dumps(metadata, indent=2))
            
            return True, export_path, f"✅ Ekspor berhasil: {filename}"
        except Exception as e:
            return False, "", f"❌ Error ekspor: {str(e)}"
    
    def import_blockchain(self, file_path: str) -> Tuple[bool, str]:
        try:
            if not os.path.exists(file_path):
                return False, "File tidak ditemukan!"
            if not file_path.endswith('.lptbc'):
                return False, "Format file harus .lptbc!"
            
            backup_success, _, backup_msg = self.export_blockchain(
                f"pre_import_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.lptbc"
            )
            if backup_success:
                print(f"✅ Backup dibuat: {backup_msg}")
            else:
                print(f"⚠️ Gagal backup: {backup_msg}")
            
            with zipfile.ZipFile(file_path, 'r') as zipf:
                with zipf.open('blockchain.json') as f:
                    import_data = json.load(f)
                
                if import_data.get('version') != 'LPTBC-EXPORT-1.0':
                    return False, "Versi ekspor tidak kompatibel!"
                
                chain_data = import_data.get('blockchain')
                if not chain_data:
                    return False, "Data blockchain tidak ditemukan!"
                
                if os.path.exists(self.blockchain_file):
                    backup_chain = self.blockchain_file + ".bak"
                    shutil.copy2(self.blockchain_file, backup_chain)
                    print(f"✅ Backup blockchain: {backup_chain}")
                
                with open(self.blockchain_file, 'w') as f:
                    json.dump(chain_data, f, indent=2)
                
                certs = [name for name in zipf.namelist() if name.startswith('certs/') and name.endswith('.cert.json')]
                if certs:
                    os.makedirs(self.cert_dir, exist_ok=True)
                    for cert_file in certs:
                        cert_name = os.path.basename(cert_file)
                        cert_path = os.path.join(self.cert_dir, cert_name)
                        with zipf.open(cert_file) as src:
                            with open(cert_path, 'wb') as dst:
                                dst.write(src.read())
                        print(f"✅ Certificate imported: {cert_name}")
            
            return True, f"✅ Impor berhasil! {import_data.get('metadata', {}).get('total_blocks', 0)} blok diimpor."
        except Exception as e:
            return False, f"❌ Error impor: {str(e)}"
    
    def get_exports(self) -> list:
        exports = []
        for f in os.listdir(self.export_dir):
            if f.endswith('.lptbc'):
                path = os.path.join(self.export_dir, f)
                size = os.path.getsize(path)
                modified = datetime.fromtimestamp(os.path.getmtime(path))
                exports.append({
                    'filename': f,
                    'path': path,
                    'size': size,
                    'size_str': self._format_size(size),
                    'modified': modified.strftime("%Y-%m-%d %H:%M:%S")
                })
        return sorted(exports, key=lambda x: x['modified'], reverse=True)
    
    def _format_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"