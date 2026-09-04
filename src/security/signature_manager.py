# src/security/signature_manager.py
import hashlib
import json
import base64
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


class SignatureManager:
    def __init__(self, key_dir: str = "src/data/keys"):
        self.key_dir = key_dir
        os.makedirs(key_dir, exist_ok=True)
        
        self.private_key_path = os.path.join(key_dir, "lptbc_private.pem")
        self.public_key_path = os.path.join(key_dir, "lptbc_public.pem")
        
        self._load_or_create_keys()
        self.signature_version = "LPTBC-SIG-1.0"
    
    def _load_or_create_keys(self):
        if os.path.exists(self.private_key_path) and os.path.exists(self.public_key_path):
            with open(self.private_key_path, 'rb') as f:
                self.private_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())
            with open(self.public_key_path, 'rb') as f:
                self.public_key = serialization.load_pem_public_key(f.read(), backend=default_backend())
        else:
            self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
            self.public_key = self.private_key.public_key()
            with open(self.private_key_path, 'wb') as f:
                f.write(self.private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            with open(self.public_key_path, 'wb') as f:
                f.write(self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
            print("✅ LPTBC Key Pair generated successfully!")
    
    def create_signature(self, document_data: Dict[str, Any], 
                         file_content: Optional[bytes] = None) -> Dict[str, Any]:
        file_hash = None
        if file_content:
            file_hash = hashlib.sha256(file_content).hexdigest()
        
        doc_string = json.dumps({
            "type": document_data.get("type", ""),
            "nomor": document_data.get("nomor", ""),
            "tanggal": document_data.get("tanggal", ""),
            "judul": document_data.get("judul", ""),
            "file_hash": file_hash,
            "timestamp": datetime.now().isoformat(),
            "version": self.signature_version
        }, sort_keys=True)
        doc_hash = hashlib.sha256(doc_string.encode()).hexdigest()
        
        signature_bytes = self.private_key.sign(
            doc_hash.encode(),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        signature = base64.b64encode(signature_bytes).decode()
        
        cert = {
            "version": self.signature_version,
            "doc_hash": doc_hash,
            "file_hash": file_hash,
            "signature": signature,
            "timestamp": datetime.now().isoformat(),
            "doc_type": document_data.get("type", ""),
            "doc_nomor": document_data.get("nomor", ""),
            "public_key": self._get_public_key_pem()
        }
        
        return {
            "signature": signature,
            "doc_hash": doc_hash,
            "file_hash": file_hash,
            "certificate": cert,
            "signature_hex": signature[:32] + "...",
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_public_key_pem(self) -> str:
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
    
    def verify_signature(self, document_data: Dict[str, Any], 
                         signature: str, 
                         file_content: Optional[bytes] = None) -> Tuple[bool, str]:
        try:
            cert = document_data.get('certificate', {})
            if isinstance(cert, str):
                try:
                    cert = json.loads(cert)
                except:
                    cert = {}
            if cert:
                doc_hash = cert.get('doc_hash', '')
                if not doc_hash:
                    return False, "❌ Certificate tidak memiliki doc_hash"
            else:
                file_hash = None
                if file_content:
                    file_hash = hashlib.sha256(file_content).hexdigest()
                doc_type = document_data.get("type", "")
                doc_nomor = document_data.get("nomor", "")
                doc_tanggal = document_data.get("tanggal", "")
                doc_judul = document_data.get("judul", "")
                timestamp = document_data.get("timestamp", datetime.now().isoformat())
                doc_string = json.dumps({
                    "type": doc_type,
                    "nomor": doc_nomor,
                    "tanggal": doc_tanggal,
                    "judul": doc_judul,
                    "file_hash": file_hash,
                    "timestamp": timestamp,
                    "version": self.signature_version
                }, sort_keys=True)
                doc_hash = hashlib.sha256(doc_string.encode()).hexdigest()
            
            signature_bytes = base64.b64decode(signature)
            try:
                self.public_key.verify(
                    signature_bytes,
                    doc_hash.encode(),
                    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                    hashes.SHA256()
                )
                return True, "✅ Dokumen VALID! Signature cocok."
            except Exception as e:
                print(f"   ⚠️ Signature verification failed: {e}")
                return False, "❌ Dokumen TIDAK VALID! Signature tidak cocok."
        except Exception as e:
            return False, f"❌ Error verifikasi: {str(e)}"
    
    def verify_document_integrity(self, file_path: str, 
                                  stored_file_hash: str) -> Tuple[bool, str]:
        try:
            if not os.path.exists(file_path):
                return False, "❌ File tidak ditemukan"
            with open(file_path, 'rb') as f:
                current_hash = hashlib.sha256(f.read()).hexdigest()
            if current_hash == stored_file_hash:
                return True, "✅ File integrity OK! File tidak berubah."
            else:
                return False, "❌ File integrity FAIL! File telah diubah."
        except Exception as e:
            return False, f"❌ Error: {str(e)}"
    
    def create_validation_report(self, document_data: Dict[str, Any], 
                                 signature: str,
                                 file_content: Optional[bytes] = None) -> Dict[str, Any]:
        is_valid, message = self.verify_signature(document_data, signature, file_content)
        report = {
            "validation_result": "VALID" if is_valid else "INVALID",
            "message": message,
            "document_info": {
                "type": document_data.get("type", ""),
                "nomor": document_data.get("nomor", ""),
                "tanggal": document_data.get("tanggal", ""),
                "judul": document_data.get("judul", ""),
                "timestamp": document_data.get("timestamp", "")
            },
            "signature_info": {
                "version": self.signature_version,
                "signature_preview": signature[:32] + "..." if signature else "N/A"
            },
            "verified_at": datetime.now().isoformat(),
            "verified_by": "LPTBC Validator v1.0"
        }
        return report