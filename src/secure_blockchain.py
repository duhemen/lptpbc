# src/secure_blockchain.py
import sqlite3
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import os

class SecureBlockchainDB:
    def __init__(self, db_path="src/data/blockchain.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
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
                CHECK (block_index >= 0),
                CHECK (LENGTH(block_hash) = 64)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                block_index INTEGER,
                user TEXT,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_hash TEXT UNIQUE NOT NULL,
                doc_type TEXT NOT NULL,
                nomor TEXT,
                tanggal TEXT,
                file_path TEXT,
                file_hash TEXT,
                block_index INTEGER,
                published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data TEXT,
                FOREIGN KEY (block_index) REFERENCES blockchain(block_index)
            )
        ''')
        cursor.execute("SELECT COUNT(*) FROM blockchain WHERE block_index = 0")
        if cursor.fetchone()[0] == 0:
            self._create_genesis_block()
        conn.commit()
        conn.close()
    
    def _create_genesis_block(self):
        genesis_data = {
            "type": "GENESIS",
            "message": "Inisialisasi Secure Blockchain LPT",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0"
        }
        genesis_hash = self._calculate_hash(0, genesis_data, "0")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO blockchain 
            (block_index, block_hash, previous_hash, data, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (0, genesis_hash, "0", json.dumps(genesis_data), datetime.now().timestamp()))
        conn.commit()
        conn.close()
    
    def _calculate_hash(self, index: int, data: Dict, previous_hash: str) -> str:
        block_string = json.dumps({
            "index": index,
            "data": data,
            "previous_hash": previous_hash
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    def add_block(self, data: Dict[str, Any]) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        conn.execute("BEGIN TRANSACTION")
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT block_index, block_hash FROM blockchain ORDER BY block_index DESC LIMIT 1')
            last_block = cursor.fetchone()
            new_index = last_block[0] + 1 if last_block else 0
            previous_hash = last_block[1] if last_block else "0"
            block_hash = self._calculate_hash(new_index, data, previous_hash)
            cursor.execute('''
                INSERT INTO blockchain 
                (block_index, block_hash, previous_hash, data, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (new_index, block_hash, previous_hash, json.dumps(data), datetime.now().timestamp()))
            cursor.execute('''
                INSERT INTO audit_log (action, block_index, details)
                VALUES (?, ?, ?)
            ''', ("ADD_BLOCK", new_index, f"Block {new_index} added"))
            conn.commit()
            return {
                "block_index": new_index,
                "block_hash": block_hash,
                "previous_hash": previous_hash,
                "data": data,
                "verified": self.verify_chain()
            }
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def verify_chain(self) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT block_index, block_hash, previous_hash, data FROM blockchain ORDER BY block_index')
        blocks = cursor.fetchall()
        conn.close()
        if not blocks:
            return False
        for i in range(1, len(blocks)):
            curr_index, curr_hash, curr_prev_hash, curr_data = blocks[i]
            prev_index, prev_hash, prev_prev_hash, _ = blocks[i-1]
            if curr_prev_hash != prev_hash:
                return False
            recalculated = self._calculate_hash(curr_index, json.loads(curr_data), curr_prev_hash)
            if recalculated != curr_hash:
                return False
        return True
    
    def get_block_by_hash(self, block_hash: str) -> Optional[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT block_index, block_hash, previous_hash, data, timestamp FROM blockchain WHERE block_hash = ?', (block_hash,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "block_index": row[0],
                "block_hash": row[1],
                "previous_hash": row[2],
                "data": json.loads(row[3]),
                "timestamp": row[4]
            }
        return None
    
    def get_all_blocks(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT block_index, block_hash, previous_hash, data, timestamp FROM blockchain ORDER BY block_index DESC LIMIT ? OFFSET ?', (limit, offset))
        results = cursor.fetchall()
        conn.close()
        return [{
            "block_index": row[0],
            "block_hash": row[1],
            "previous_hash": row[2],
            "data": json.loads(row[3]),
            "timestamp": row[4]
        } for row in results]
    
    def get_audit_log(self, limit: int = 50) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?', (limit,))
        results = cursor.fetchall()
        conn.close()
        return [{
            "id": row[0], "action": row[1], "block_index": row[2], "user": row[3],
            "ip_address": row[4], "timestamp": row[5], "details": row[6]
        } for row in results]