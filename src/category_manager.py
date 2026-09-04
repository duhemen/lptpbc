# src/category_manager.py
import json
import os
from typing import Dict, Any, List, Optional


class CategoryManager:
    CATEGORIES = {
        'surat': {
            'name': '📄 Surat',
            'sub_categories': [
                'Surat Permohonan',
                'Surat Undangan',
                'Surat Tugas',
                'Surat Keterangan'
            ],
            'icon': '📄',
            'color': '#004B87'
        },
        'laporan': {
            'name': '📊 Laporan',
            'sub_categories': [
                'Laporan Hasil',
                'Laporan Keuangan',
                'Laporan Progres'
            ],
            'icon': '📊',
            'color': '#27AE60'
        },
        'kontrak': {
            'name': '📝 Kontrak',
            'sub_categories': [
                'Kontrak Kerja',
                'Addendum',
                'SPK'
            ],
            'icon': '📝',
            'color': '#E67E22'
        },
        'berita_acara': {
            'name': '📋 Berita Acara',
            'sub_categories': [
                'Berita Acara Penetapan Harga',
                'Berita Acara Serah Terima',
                'Berita Acara Pemeriksaan'
            ],
            'icon': '📋',
            'color': '#8E44AD'
        },
        'keputusan': {
            'name': '⚖️ Keputusan',
            'sub_categories': [
                'SK Tim',
                'Keputusan Pejabat',
                'Penetapan'
            ],
            'icon': '⚖️',
            'color': '#D35400'
        }
    }
    
    def __init__(self, config_path: str = "data/categories.json"):
        self.config_path = config_path
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        self.categories = self._load_categories()
    
    def _load_categories(self) -> Dict:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return self.CATEGORIES
    
    def save_categories(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.categories, f, indent=2)
    
    def get_all_categories(self) -> List[Dict]:
        return [{'key': key, **value} for key, value in self.categories.items()]
    
    def get_category(self, key: str) -> Optional[Dict]:
        return self.categories.get(key)
    
    def get_document_category(self, doc_type: str) -> Optional[str]:
        for key, cat in self.categories.items():
            if doc_type in cat.get('sub_categories', []):
                return key
        return None
    
    def get_all_sub_categories(self) -> List[str]:
        subs = []
        for cat in self.categories.values():
            subs.extend(cat.get('sub_categories', []))
        return subs
    
    def add_category(self, key: str, name: str, 
                     sub_categories: List[str] = None,
                     icon: str = '📁',
                     color: str = '#999999') -> bool:
        if key in self.categories:
            return False
        self.categories[key] = {
            'name': name,
            'sub_categories': sub_categories or [],
            'icon': icon,
            'color': color
        }
        self.save_categories()
        return True
    
    def get_statistics(self, documents: List[Dict]) -> Dict:
        stats = {}
        for key, cat in self.categories.items():
            stats[key] = {
                'name': cat['name'],
                'icon': cat['icon'],
                'color': cat['color'],
                'total': 0,
                'documents': []
            }
        for doc in documents:
            doc_type = doc.get('type', '')
            cat_key = self.get_document_category(doc_type)
            if cat_key and cat_key in stats:
                stats[cat_key]['total'] += 1
                stats[cat_key]['documents'].append(doc)
        return stats