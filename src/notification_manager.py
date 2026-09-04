# src/notification_manager.py
import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from PyQt5.QtWidgets import QSystemTrayIcon, QApplication
from PyQt5.QtCore import QTimer, pyqtSignal, QObject


class NotificationManager(QObject):
    new_notification = pyqtSignal(dict)
    
    def __init__(self, db_path: str = "data/notifications.db"):
        super().__init__()
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_database()
        
        self.tray_icon = None
        self._init_tray()
        
        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self._check_reminders)
        self.reminder_timer.start(60000)
        
        self.notification_timer = QTimer()
        self.notification_timer.timeout.connect(self._check_notifications)
        self.notification_timer.start(5000)
        
        self.pending_notifications = []
    
    def _init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read INTEGER DEFAULT 0,
                is_dismissed INTEGER DEFAULT 0,
                data TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                remind_at TIMESTAMP NOT NULL,
                doc_hash TEXT,
                doc_type TEXT,
                is_done INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _init_tray(self):
        try:
            self.tray_icon = QSystemTrayIcon(QApplication.instance())
            self.tray_icon.setToolTip("LPTBC - Notifikasi")
            icon_path = "assets/icon.png"
            if os.path.exists(icon_path):
                from PyQt5.QtGui import QIcon
                self.tray_icon.setIcon(QIcon(icon_path))
            self.tray_icon.messageClicked.connect(self._on_tray_clicked)
            self.tray_icon.show()
        except Exception as e:
            print(f"⚠️ Tray icon not available: {e}")
    
    def _on_tray_clicked(self):
        pass
    
    def add_notification(self, title: str, message: str, 
                         notif_type: str = "info", 
                         data: Optional[Dict] = None) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO notifications (title, message, type, data)
            VALUES (?, ?, ?, ?)
        ''', (title, message, notif_type, json.dumps(data) if data else None))
        notif_id = cursor.lastrowid
        conn.commit()
        conn.close()
        self._show_notification(title, message, notif_type)
        self.new_notification.emit({'id': notif_id, 'title': title, 'message': message, 'type': notif_type, 'data': data})
        return notif_id
    
    def _show_notification(self, title: str, message: str, notif_type: str):
        if self.tray_icon:
            icon_map = {
                'info': QSystemTrayIcon.Information,
                'success': QSystemTrayIcon.Information,
                'warning': QSystemTrayIcon.Warning,
                'error': QSystemTrayIcon.Critical,
            }
            icon = icon_map.get(notif_type, QSystemTrayIcon.Information)
            self.tray_icon.showMessage(title, message, icon, 3000)
    
    def add_reminder(self, title: str, message: str, 
                     remind_at: datetime,
                     doc_hash: Optional[str] = None,
                     doc_type: Optional[str] = None) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reminders (title, message, remind_at, doc_hash, doc_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, message, remind_at.isoformat(), doc_hash, doc_type))
        reminder_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return reminder_id
    
    def add_document_reminder(self, doc_type: str, doc_nomor: str, 
                              expire_days: int = 30) -> int:
        remind_at = datetime.now() + timedelta(days=expire_days)
        return self.add_reminder(
            title="📄 Dokumen Akan Expired",
            message=f"Dokumen {doc_type} ({doc_nomor}) akan expired dalam {expire_days} hari",
            remind_at=remind_at,
            doc_type=doc_type
        )
    
    def _check_reminders(self):
        try:
            now = datetime.now().isoformat()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM reminders WHERE remind_at <= ? AND is_done = 0', (now,))
            reminders = cursor.fetchall()
            for reminder in reminders:
                self.add_notification(title=reminder[1], message=reminder[2], notif_type="warning", data={'reminder_id': reminder[0]})
                cursor.execute('UPDATE reminders SET is_done = 1 WHERE id = ?', (reminder[0],))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ Error checking reminders: {e}")
    
    def _check_notifications(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM notifications WHERE is_read = 0 AND is_dismissed = 0 ORDER BY created_at DESC LIMIT 10')
            notifications = cursor.fetchall()
            conn.close()
            for notif in notifications:
                self.new_notification.emit({'id': notif[0], 'title': notif[1], 'message': notif[2], 'type': notif[3], 'created_at': notif[4], 'data': json.loads(notif[6]) if notif[6] else {}})
                self.mark_as_read(notif[0])
        except Exception as e:
            print(f"❌ Error checking notifications: {e}")
    
    def mark_as_read(self, notif_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE notifications SET is_read = 1 WHERE id = ?', (notif_id,))
        conn.commit()
        conn.close()
    
    def get_unread_count(self) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM notifications WHERE is_read = 0 AND is_dismissed = 0')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_notifications(self, limit: int = 50) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM notifications ORDER BY created_at DESC LIMIT ?', (limit,))
        results = cursor.fetchall()
        conn.close()
        return [{
            'id': r[0], 'title': r[1], 'message': r[2], 'type': r[3], 'created_at': r[4],
            'is_read': bool(r[5]), 'is_dismissed': bool(r[6]), 'data': json.loads(r[7]) if r[7] else {}
        } for r in results]