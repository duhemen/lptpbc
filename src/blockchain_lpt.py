import hashlib
import json
import time
from typing import Dict, Any, List, Optional
import os


class BlockLPT:
    """Blok blockchain untuk menyimpan data dokumen LPT"""
    
    def __init__(self, index: int, data: Dict[str, Any], previous_hash: str):
        self.index = index
        self.timestamp = time.time()
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    def to_dict(self) -> Dict:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "hash": self.hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BlockLPT':
        block = cls(data["index"], data["data"], data["previous_hash"])
        block.timestamp = data["timestamp"]
        block.hash = data["hash"]
        return block


class BlockchainLPT:
    """Blockchain untuk LPT dengan kemampuan verifikasi"""
    
    def __init__(self, chain_file: str = "src/data/lpt_chain.json"):
        self.chain_file = chain_file
        self.chain: List[BlockLPT] = []
        self._is_loading = False
        
        os.makedirs(os.path.dirname(chain_file), exist_ok=True)
        
        if os.path.exists(chain_file):
            self.load_from_file()
        else:
            self._create_genesis_block()
            self.save_to_file()
    
    def _create_genesis_block(self):
        genesis_data = {
            "type": "GENESIS",
            "message": "Inisialisasi Blockchain LPT",
            "timestamp": time.time()
        }
        genesis_block = BlockLPT(0, genesis_data, "0")
        self.chain.append(genesis_block)
    
    def add_block(self, data: Dict[str, Any]) -> BlockLPT:
        if not self.chain:
            self._create_genesis_block()
        
        previous_block = self.chain[-1]
        new_block = BlockLPT(
            index=len(self.chain),
            data=data,
            previous_hash=previous_block.hash
        )
        self.chain.append(new_block)
        self.save_to_file()
        return new_block
    
    def get_block_by_hash(self, hash_value: str) -> Optional[BlockLPT]:
        for block in self.chain:
            if block.hash == hash_value:
                return block
        return None
    
    def get_blocks_by_type(self, doc_type: str) -> List[BlockLPT]:
        return [b for b in self.chain if b.data.get("type") == doc_type]
    
    def get_last_block(self) -> Optional[BlockLPT]:
        return self.chain[-1] if self.chain else None
    
    def verify_chain(self) -> bool:
        if len(self.chain) <= 1:
            return True
        
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            
            if current.hash != current._calculate_hash():
                return False
            
            if current.previous_hash != previous.hash:
                return False
        
        return True
    
    def save_to_file(self):
        try:
            chain_data = {
                "blocks": [block.to_dict() for block in self.chain],
                "verified": self.verify_chain(),
                "last_updated": time.time()
            }
            
            temp_file = self.chain_file + ".tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(chain_data, f, indent=2, ensure_ascii=False)
            
            os.replace(temp_file, self.chain_file)
        except Exception as e:
            print(f"⚠️ Error saving blockchain: {e}")
            raise
    
    def load_from_file(self):
        try:
            with open(self.chain_file, 'r', encoding='utf-8') as f:
                chain_data = json.load(f)
        
            self.chain = [BlockLPT.from_dict(block) for block in chain_data.get("blocks", [])]
        
            if not self.verify_chain():
                print("⚠️ PERINGATAN: Blockchain tidak valid! Memperbaiki...")
                self._repair_chain()
        except FileNotFoundError:
            self._create_genesis_block()
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing blockchain file: {e}")
            print("🔄 Membuat blockchain baru...")
            self._create_genesis_block()
        except Exception as e:
            print(f"❌ Error loading blockchain: {e}")
            self._create_genesis_block()

    def _repair_chain(self):
        if len(self.chain) <= 1:
            self._create_genesis_block()
            self.save_to_file()
            return
    
        repaired = []
        genesis = self.chain[0]
        genesis.hash = genesis._calculate_hash()
        repaired.append(genesis)
    
        for i in range(1, len(self.chain)):
            block = self.chain[i]
            block.previous_hash = repaired[-1].hash
            block.hash = block._calculate_hash()
            repaired.append(block)
    
        self.chain = repaired
        self.save_to_file()
        print(f"✅ Blockchain diperbaiki! {len(self.chain)} blok valid.")
    
    def get_summary(self) -> Dict:
        return {
            "total_blocks": len(self.chain),
            "verified": self.verify_chain(),
            "last_block": self.chain[-1].to_dict() if self.chain else None,
            "total_documents": len([b for b in self.chain if b.data.get("type") != "GENESIS"])
        }