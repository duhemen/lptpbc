# src/blockchain_manager.py
import os
import shutil
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from .blockchain_lpt import BlockchainLPT
from .database import LPTDatabase
from .security.signature_manager import SignatureManager


class BlockchainManager:
    def __init__(self):
        self.blockchain = BlockchainLPT()
        self.db = LPTDatabase()
        self.signer = SignatureManager()
        self.output_dir = "output"
        self.published_dir = os.path.join(self.output_dir, "published")
        os.makedirs(self.published_dir, exist_ok=True)

    def validate_document(self, file_path: str, block_hash: Optional[str] = None) -> Dict[str, Any]:
        result = {
            "is_valid": False,
            "message": "",
            "details": {}
        }

        try:
            if not os.path.exists(file_path):
                result["message"] = "❌ File tidak ditemukan"
                return result

            with open(file_path, 'rb') as f:
                file_content = f.read()
            file_hash = hashlib.sha256(file_content).hexdigest()

            block = None
            if block_hash:
                block = self.blockchain.get_block_by_hash(block_hash)

            if not block:
                for b in self.blockchain.chain:
                    stored_hash = b.data.get("file_hash")
                    if stored_hash and stored_hash == file_hash:
                        block = b
                        break

            if not block:
                file_name = os.path.basename(file_path)
                for b in self.blockchain.chain:
                    stored_path = b.data.get("file_path", "")
                    if stored_path and os.path.basename(stored_path) == file_name:
                        block = b
                        break

            if not block:
                for b in self.blockchain.chain:
                    stored_path = b.data.get("file_path", "")
                    if stored_path and stored_path == file_path:
                        block = b
                        break

            if not block:
                result["message"] = "❌ Dokumen tidak ditemukan di blockchain LPTBC"
                result["details"]["file_hash"] = file_hash
                result["details"]["file_name"] = os.path.basename(file_path)
                return result

            stored_file_hash = block.data.get("file_hash")
            if stored_file_hash and stored_file_hash != file_hash:
                result["message"] = "❌ File telah diubah! Hash tidak cocok."
                result["details"]["stored_hash"] = stored_file_hash
                result["details"]["current_hash"] = file_hash
                return result

            block_data = block.data
            signature = block_data.get("signature", "")

            if not signature:
                result["message"] = "⚠️ Dokumen tidak memiliki signature digital"
                result["details"]["block"] = block.to_dict()
                return result

            doc_info = {
                "type": block_data.get("type", ""),
                "nomor": block_data.get("nomor", ""),
                "tanggal": block_data.get("tanggal", ""),
                "judul": block_data.get("judul", ""),
                "file_hash": stored_file_hash,
                "timestamp": block_data.get("signature_timestamp", ""),
                "certificate": block_data.get("certificate", {})
            }

            # Pastikan certificate adalah dict
            if isinstance(doc_info["certificate"], str):
                try:
                    doc_info["certificate"] = json.loads(doc_info["certificate"])
                except:
                    doc_info["certificate"] = {}

            is_valid, sig_message = self.signer.verify_signature(
                doc_info, 
                signature, 
                file_content
            )

            result["is_valid"] = is_valid
            result["message"] = sig_message
            result["details"] = {
                "block_index": block.index,
                "block_hash": block.hash,
                "doc_type": block_data.get("type", ""),
                "doc_nomor": block_data.get("nomor", ""),
                "doc_tanggal": block_data.get("tanggal", ""),
                "doc_judul": block_data.get("judul", ""),
                "file_hash": file_hash,
                "stored_file_hash": stored_file_hash,
                "file_path": file_path,
                "signature_hex": block_data.get("signature_hex", ""),
                "signature_timestamp": block_data.get("signature_timestamp", ""),
                "published_at": datetime.fromtimestamp(block.timestamp).strftime("%Y-%m-%d %H:%M:%S"),
                "certificate": doc_info["certificate"]
            }

            return result

        except Exception as e:
            result["message"] = f"❌ Error validasi: {str(e)}"
            import traceback
            traceback.print_exc()
            return result

    def get_published_documents(self, doc_type: Optional[str] = None, 
                                limit: int = 100, offset: int = 0) -> List[Dict]:
        try:
            docs = self.db.get_all_documents(limit=limit, offset=offset)
            if doc_type:
                docs = [d for d in docs if d.get('type') == doc_type]
            return docs
        except Exception as e:
            print(f"❌ Error getting published documents: {e}")
            return []

    def get_published_documents_from_blockchain(self, doc_type: Optional[str] = None) -> list:
        if doc_type:
            blocks = self.blockchain.get_blocks_by_type(doc_type)
        else:
            blocks = [b for b in self.blockchain.chain if b.data.get("type") != "GENESIS"]
        
        return [{
            "hash": b.hash,
            "type": b.data.get("type", ""),
            "nomor": b.data.get("nomor", ""),
            "tanggal": b.data.get("tanggal", ""),
            "file_path": b.data.get("file_path", ""),
            "timestamp": datetime.fromtimestamp(b.timestamp).strftime("%Y-%m-%d %H:%M:%S"),
            "block_index": b.index
        } for b in blocks]

    def publish_document(self, doc_type: str, doc_data: Dict[str, Any], 
                         file_path: Optional[str] = None,
                         file_content: Optional[bytes] = None) -> Dict[str, Any]:
        try:
            file_hash = None
            if file_path and os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                    file_hash = hashlib.sha256(file_content).hexdigest()
            elif file_content:
                file_hash = hashlib.sha256(file_content).hexdigest()
            
            doc_info = {
                "type": doc_type,
                "nomor": doc_data.get("nomor", ""),
                "tanggal": doc_data.get("tanggal", ""),
                "judul": doc_data.get("judul", ""),
                "file_hash": file_hash,
                "timestamp": datetime.now().isoformat()
            }
            
            sig_result = self.signer.create_signature(doc_info, file_content)
            
            block_data = {
                "type": doc_type,
                "nomor": doc_data.get("nomor", ""),
                "tanggal": doc_data.get("tanggal", ""),
                "judul": doc_data.get("judul", ""),
                "file_hash": file_hash,
                "file_path": file_path,
                "data": doc_data,
                "signature": sig_result["signature"],
                "doc_hash": sig_result["doc_hash"],
                "certificate": sig_result["certificate"],
                "signature_timestamp": sig_result["timestamp"],
                "signature_version": self.signer.signature_version,
                "signature_hex": sig_result["signature_hex"]
            }
            
            block = self.blockchain.add_block(block_data)
            
            saved_path = None
            cert_path = None
    
            if file_path and os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                    file_hash = hashlib.sha256(file_content).hexdigest()
                block.data["file_hash"] = file_hash
        
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                block_id = block.hash[:8]
                ext = os.path.splitext(file_path)[1]
                if not ext:
                    ext = '.html'
        
                new_filename = f"{doc_type}_{timestamp}_{block_id}{ext}"
                new_path = os.path.join(self.published_dir, new_filename)
                shutil.copy2(file_path, new_path)
                saved_path = new_path
        
                cert_filename = f"{doc_type}_{timestamp}_{block_id}.cert.json"
                cert_path = os.path.join(self.published_dir, cert_filename)
                with open(cert_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        "block_hash": block.hash,
                        "block_index": block.index,
                        "signature": sig_result["signature"],
                        "certificate": sig_result["certificate"],
                        "document_data": doc_info
                    }, f, indent=2, ensure_ascii=False)
        
                block.data["file_path"] = new_path
                block.data["certificate_path"] = cert_path
                self.blockchain.save_to_file()
            
            # Simpan ke database
            block_dict = block.to_dict()
            block_dict['block_index'] = block.index
            
            signature_str = sig_result.get("signature", "")
            if not isinstance(signature_str, str):
                signature_str = str(signature_str)
            
            certificate = sig_result.get("certificate", {})
            if isinstance(certificate, dict):
                certificate_str = json.dumps(certificate)
            elif isinstance(certificate, str):
                certificate_str = certificate
            else:
                certificate_str = str(certificate)
            
            judul = doc_data.get("judul", "")
            if not isinstance(judul, str):
                judul = str(judul)
            
            try:
                self.db.save_block(
                    block_index=block.index,
                    block_hash=block.hash,
                    previous_hash=block.previous_hash,
                    data=block.data,
                    timestamp=block.timestamp,
                    signature=signature_str,
                    certificate=certificate_str
                )
            except Exception as e:
                print(f"   ❌ Error saving to blockchain table: {e}")
            
            try:
                doc_save_data = {
                    'hash': block.hash,
                    'doc_hash': block.hash,
                    'type': doc_type,
                    'doc_type': doc_type,
                    'nomor': doc_data.get("nomor", ""),
                    'tanggal': doc_data.get("tanggal", ""),
                    'judul': judul,
                    'file_path': saved_path or file_path,
                    'file_hash': file_hash,
                    'block_index': block.index,
                    'signature': signature_str,
                    'certificate': certificate_str,
                    'data': block_data
                }
                self.db.save_document(doc_save_data)
            except Exception as e:
                print(f"   ❌ Error saving to documents table: {e}")
                import traceback
                traceback.print_exc()
            
            print(f"\n✅ Dokumen diterbitkan dengan signature!")
            print(f"   Type: {doc_type} | Block: {block.index}")
            print(f"   Signature: {sig_result['signature_hex']}")
            if saved_path:
                print(f"   File: {saved_path}")
            if cert_path:
                print(f"   Certificate: {cert_path}")
            
            return {
                "block": block_dict,
                "verified": self.blockchain.verify_chain(),
                "signature": sig_result,
                "saved_path": saved_path,
                "certificate_path": cert_path,
                "message": f"Dokumen {doc_type} berhasil diterbitkan dengan signature digital!"
            }
        except Exception as e:
            print(f"❌ Error publishing document: {e}")
            import traceback
            traceback.print_exc()
            return {
                "verified": False,
                "message": f"Error: {str(e)}",
                "block": None
            }

    def get_documents(self, doc_type: Optional[str] = None, 
                      limit: int = 100, offset: int = 0) -> List[Dict]:
        return self.get_published_documents(doc_type, limit, offset)

    def get_all_documents(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        return self.get_published_documents(None, limit, offset)