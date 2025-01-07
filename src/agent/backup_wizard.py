from typing import List, Dict
import shutil
import subprocess
from pathlib import Path

class BackupWizard:
    def __init__(self):
        self.detected_dbs: Dict[str, bool] = {}
        self.backup_paths: List[str] = []
        self.default_paths = [
            "/etc",
            "/home",
            "/root",
            "/var/www",
            "/usr/local/bin"
        ]
    
    def detect_databases(self) -> Dict[str, bool]:
        """Detect installed databases and return dict of db_name: is_installed"""
        databases = {
            'postgresql': self._check_postgres(),
            'mysql': self._check_mysql(),
            'redis': self._check_redis()
        }
        self.detected_ 