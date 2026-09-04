# src/database.py
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import os


class LPTDatabase:
    def __init__(self, db_path: str = "src/data/blockchain.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._create_tables()
        self._migrate_if_needed()
    
    def _create_tables(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blockchain (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                block_index INTEGER UNIQUE NOT NULL,
                block_hash TEXT UNIQUE NOT NULL,
                previous_hash TEXT NOT NULL,
                data TEXT NOT NULL,
                timestamp REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                signature TEXT,
                certificate TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_hash TEXT UNIQUE NOT NULL,
                doc_type TEXT NOT NULL,
                nomor TEXT,
                tanggal TEXT,
                judul TEXT,
                file_path TEXT,
                file_hash TEXT,
                block_index INTEGER,
                published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data TEXT,
                signature TEXT,
                certificate TEXT,
                FOREIGN KEY (block_index) REFERENCES blockchain(block_index)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                block_index INTEGER,
                user TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_doc_hash ON documents(doc_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_doc_type ON documents(doc_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_block_hash ON blockchain(block_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_block_index ON blockchain(block_index)')
        
        conn.commit()
        conn.close()
    
    def _migrate_if_needed(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(documents)")
        columns = [col[1] for col in cursor.fetchall()]
        for col in ['judul', 'signature', 'certificate', 'doc_hash']:
            if col not in columns:
                try:
                    cursor.execute(f"ALTER TABLE documents ADD COLUMN {col} TEXT")
                    print(f"✅ Kolom '{col}' ditambahkan ke documents")
                except sqlite3.OperationalError:
                    pass
        
        cursor.execute("PRAGMA table_info(blockchain)")
        bc_columns = [col[1] for col in cursor.fetchall()]
        for col in ['signature', 'certificate']:
            if col not in bc_columns:
                try:
                    cursor.execute(f"ALTER TABLE blockchain ADD COLUMN {col} TEXT")
                    print(f"✅ Kolom '{col}' ditambahkan ke blockchain")
                except sqlite3.OperationalError:
                    pass
        
        conn.commit()
        conn.close()
    
    def save_block(self, block_index: int, block_hash: str, previous_hash: str, 
                   data: Dict[str, Any], timestamp: float, 
                   signature: Optional[str] = None,
                   certificate: Optional[str] = None) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cert_str = certificate
            if isinstance(certificate, dict):
                cert_str = json.dumps(certificate)
            elif certificate is not None:
                cert_str = str(certificate)
            cursor.execute('''
                INSERT OR REPLACE INTO blockchain 
                (block_index, block_hash, previous_hash, data, timestamp, signature, certificate)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (block_index, block_hash, previous_hash, json.dumps(data), timestamp,
                  str(signature) if signature else None, cert_str))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Error saving block: {e}")
            return False
    
    def save_document(self, block_data: Dict[str, Any]) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            doc_hash = block_data.get('hash') or block_data.get('doc_hash') or ''
            doc_type = block_data.get('type') or block_data.get('doc_type') or ''
            nomor = block_data.get('nomor', '')
            tanggal = block_data.get('tanggal', '')
            judul = block_data.get('judul', '')
            file_path = block_data.get('file_path', '')
            file_hash = block_data.get('file_hash', '')
            block_index = block_data.get('block_index', 0)
            
            signature = block_data.get('signature', '')
            if not isinstance(signature, str):
                signature = str(signature) if signature else ''
            
            certificate = block_data.get('certificate', '')
            if isinstance(certificate, dict):
                certificate = json.dumps(certificate)
            elif not isinstance(certificate, str):
                certificate = str(certificate) if certificate else ''
            
            try:
                data = json.dumps(block_data, ensure_ascii=False)
            except:
                data = str(block_data)
            
            published_at = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT OR REPLACE INTO documents 
                (doc_hash, doc_type, nomor, tanggal, judul, file_path, 
                 file_hash, block_index, published_at, data, signature, certificate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (str(doc_hash), str(doc_type), str(nomor), str(tanggal), str(judul),
                  str(file_path), str(file_hash), int(block_index), str(published_at),
                  str(data), str(signature), str(certificate)))
            
            cursor.execute('''
                INSERT INTO audit_log (action, block_index, details)
                VALUES (?, ?, ?)
            ''', ("DOCUMENT_PUBLISHED", int(block_index), f"Published {doc_type} - {nomor}"))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Error saving document: {e}")
            return False
    
    def get_all_documents(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT doc_hash, doc_type, nomor, tanggal, judul, file_path, 
                   published_at, file_hash, block_index, signature
            FROM documents
            ORDER BY published_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        results = cursor.fetchall()
        conn.close()
        return [{
            'hash': row[0], 'type': row[1], 'nomor': row[2], 'tanggal': row[3],
            'judul': row[4], 'file_path': row[5], 'published_at': row[6],
            'file_hash': row[7], 'block_index': row[8], 'has_signature': bool(row[9])
        } for row in results]
    
    def get_document_by_hash(self, hash_value: str) -> Optional[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''SELECT * FROM documents WHERE doc_hash = ?''', (hash_value,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                'id': row[0], 'hash': row[1], 'type': row[2], 'nomor': row[3],
                'tanggal': row[4], 'judul': row[5], 'file_path': row[6],
                'file_hash': row[7], 'block_index': row[8], 'published_at': row[9],
                'data': json.loads(row[10]) if row[10] else {},
                'signature': row[11], 'certificate': json.loads(row[12]) if row[12] else None
            }
        return None
    
    def get_block_count(self) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM blockchain")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_audit_log(self, limit: int = 50) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?''', (limit,))
        results = cursor.fetchall()
        conn.close()
        return [{
            'id': row[0], 'action': row[1], 'block_index': row[2], 'user': row[3],
            'details': row[4], 'timestamp': row[5]
        } for row in results]
    
    def clear_all(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documents")
        cursor.execute("DELETE FROM blockchain")
        cursor.execute("DELETE FROM audit_log")
        conn.commit()
        conn.close()