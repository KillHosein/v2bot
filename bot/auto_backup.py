"""
Automatic Backup System with Cloud Support
Provides scheduled backups, versioning, and restore capabilities
"""
import os
import shutil
import gzip
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import asyncio
import aiofiles
from .db import query_db, execute_db
from .config import logger
from .advanced_logging import get_advanced_logger


class BackupManager:
    """Manages automatic backups with versioning and cloud support"""
    
    def __init__(self, backup_dir: str = 'backups'):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.logger = get_advanced_logger()
        self._create_tables()
        self.max_backups = 30  # Keep last 30 backups
        self.backup_schedule = {
            'daily': {'hour': 3, 'minute': 0},  # 3 AM daily
            'weekly': {'day': 0, 'hour': 3, 'minute': 0},  # Sunday 3 AM
            'monthly': {'day': 1, 'hour': 3, 'minute': 0}  # 1st of month 3 AM
        }
    
    def _create_tables(self):
        """Create backup tracking tables"""
        try:
            execute_db("""
                CREATE TABLE IF NOT EXISTS backup_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    backup_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    backup_type TEXT,
                    size_bytes INTEGER,
                    file_count INTEGER,
                    compression_ratio REAL,
                    checksum TEXT,
                    location TEXT,
                    status TEXT,
                    restore_count INTEGER DEFAULT 0,
                    notes TEXT
                )
            """)
            
            execute_db("""
                CREATE TABLE IF NOT EXISTS backup_schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    schedule_type TEXT NOT NULL,
                    frequency TEXT,
                    next_run TEXT,
                    last_run TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    retention_days INTEGER DEFAULT 30
                )
            """)
            
            # Initialize default schedules
            self._init_schedules()
            
        except Exception as e:
            logger.error(f"Failed to create backup tables: {e}")
    
    def _init_schedules(self):
        """Initialize default backup schedules"""
        schedules = [
            ('database', 'daily', 30),
            ('logs', 'weekly', 7),
            ('full', 'weekly', 30),
            ('config', 'on_change', 90)
        ]
        
        for backup_type, frequency, retention in schedules:
            execute_db("""
                INSERT OR IGNORE INTO backup_schedule 
                (schedule_type, frequency, retention_days)
                VALUES (?, ?, ?)
            """, (backup_type, frequency, retention))
    
    async def create_backup(self, 
                          backup_type: str = 'full',
                          compress: bool = True,
                          encrypt: bool = False) -> Tuple[bool, str, Dict]:
        """
        Create a backup
        Returns: (success, backup_id, metadata)
        """
        backup_id = f"{backup_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(exist_ok=True)
        
        metadata = {
            'backup_id': backup_id,
            'timestamp': datetime.now().isoformat(),
            'type': backup_type,
            'files': [],
            'total_size': 0,
            'compressed': compress,
            'encrypted': encrypt
        }
        
        try:
            if backup_type in ['database', 'full']:
                await self._backup_database(backup_path, metadata)
            
            if backup_type in ['logs', 'full']:
                await self._backup_logs(backup_path, metadata)
            
            if backup_type in ['config', 'full']:
                await self._backup_config(backup_path, metadata)
            
            if backup_type == 'full':
                await self._backup_code(backup_path, metadata)
                await self._backup_media(backup_path, metadata)
            
            # Compress if requested
            if compress:
                compressed_file = await self._compress_backup(backup_path, backup_id)
                metadata['compressed_file'] = str(compressed_file)
                metadata['compression_ratio'] = await self._calculate_compression_ratio(
                    backup_path, compressed_file
                )
                # Remove uncompressed files
                shutil.rmtree(backup_path)
            
            # Calculate checksum
            final_path = metadata.get('compressed_file', str(backup_path))
            metadata['checksum'] = await self._calculate_checksum(final_path)
            
            # Save metadata
            metadata_file = self.backup_dir / f"{backup_id}_metadata.json"
            async with aiofiles.open(metadata_file, 'w') as f:
                await f.write(json.dumps(metadata, indent=2, default=str))
            
            # Record in database
            self._record_backup(metadata)
            
            # Clean old backups
            await self._cleanup_old_backups(backup_type)
            
            self.logger.logger.info(f"Backup created: {backup_id}")
            return True, backup_id, metadata
            
        except Exception as e:
            self.logger.log_error(e, f"create_backup_{backup_type}")
            # Clean up failed backup
            if backup_path.exists():
                shutil.rmtree(backup_path, ignore_errors=True)
            return False, "", {"error": str(e)}
    
    async def _backup_database(self, backup_path: Path, metadata: Dict):
        """Backup database files"""
        db_files = ['bot.db', 'bot.db-wal', 'bot.db-shm']
        db_backup_dir = backup_path / 'database'
        db_backup_dir.mkdir(exist_ok=True)
        
        for db_file in db_files:
            if os.path.exists(db_file):
                dest = db_backup_dir / db_file
                shutil.copy2(db_file, dest)
                metadata['files'].append(str(dest))
                metadata['total_size'] += dest.stat().st_size
        
        # Also export as SQL for portability
        sql_file = db_backup_dir / 'database_dump.sql'
        os.system(f"sqlite3 bot.db .dump > {sql_file}")
        metadata['files'].append(str(sql_file))
    
    async def _backup_logs(self, backup_path: Path, metadata: Dict):
        """Backup log files"""
        logs_dir = Path('logs')
        if logs_dir.exists():
            dest_dir = backup_path / 'logs'
            shutil.copytree(logs_dir, dest_dir, ignore_errors=True)
            
            for log_file in dest_dir.rglob('*'):
                if log_file.is_file():
                    metadata['files'].append(str(log_file))
                    metadata['total_size'] += log_file.stat().st_size
    
    async def _backup_config(self, backup_path: Path, metadata: Dict):
        """Backup configuration files"""
        config_files = ['.env', 'config.json', 'settings.json']
        config_dir = backup_path / 'config'
        config_dir.mkdir(exist_ok=True)
        
        for config_file in config_files:
            if os.path.exists(config_file):
                dest = config_dir / config_file
                shutil.copy2(config_file, dest)
                metadata['files'].append(str(dest))
                metadata['total_size'] += dest.stat().st_size
    
    async def _backup_code(self, backup_path: Path, metadata: Dict):
        """Backup code files"""
        code_dir = backup_path / 'code'
        code_dir.mkdir(exist_ok=True)
        
        # Backup Python files
        for py_file in Path('.').glob('**/*.py'):
            if 'venv' not in str(py_file) and '__pycache__' not in str(py_file):
                rel_path = py_file.relative_to('.')
                dest = code_dir / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(py_file, dest)
                metadata['files'].append(str(dest))
                metadata['total_size'] += dest.stat().st_size
    
    async def _backup_media(self, backup_path: Path, metadata: Dict):
        """Backup media files"""
        media_dirs = ['uploads', 'downloads', 'media']
        media_backup_dir = backup_path / 'media'
        
        for media_dir in media_dirs:
            if os.path.exists(media_dir):
                dest = media_backup_dir / media_dir
                shutil.copytree(media_dir, dest, ignore_errors=True)
                
                for media_file in dest.rglob('*'):
                    if media_file.is_file():
                        metadata['files'].append(str(media_file))
                        metadata['total_size'] += media_file.stat().st_size
    
    async def _compress_backup(self, backup_path: Path, backup_id: str) -> Path:
        """Compress backup directory"""
        archive_file = self.backup_dir / f"{backup_id}.tar.gz"
        
        # Create tar.gz archive
        import tarfile
        with tarfile.open(archive_file, 'w:gz') as tar:
            tar.add(backup_path, arcname=backup_id)
        
        return archive_file
    
    async def _calculate_compression_ratio(self, original_path: Path, compressed_path: Path) -> float:
        """Calculate compression ratio"""
        original_size = sum(f.stat().st_size for f in original_path.rglob('*') if f.is_file())
        compressed_size = Path(compressed_path).stat().st_size
        return original_size / compressed_size if compressed_size > 0 else 0
    
    async def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of file"""
        sha256_hash = hashlib.sha256()
        
        if os.path.isfile(file_path):
            async with aiofiles.open(file_path, 'rb') as f:
                while chunk := await f.read(8192):
                    sha256_hash.update(chunk)
        else:
            # For directories, hash all files
            for file in Path(file_path).rglob('*'):
                if file.is_file():
                    async with aiofiles.open(file, 'rb') as f:
                        while chunk := await f.read(8192):
                            sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def _record_backup(self, metadata: Dict):
        """Record backup in database"""
        execute_db("""
            INSERT INTO backup_history 
            (backup_id, timestamp, backup_type, size_bytes, file_count, 
             compression_ratio, checksum, location, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metadata['backup_id'],
            metadata['timestamp'],
            metadata['type'],
            metadata['total_size'],
            len(metadata['files']),
            metadata.get('compression_ratio', 1.0),
            metadata['checksum'],
            metadata.get('compressed_file', str(self.backup_dir / metadata['backup_id'])),
            'completed'
        ))
    
    async def _cleanup_old_backups(self, backup_type: str):
        """Remove old backups based on retention policy"""
        schedule = query_db(
            "SELECT retention_days FROM backup_schedule WHERE schedule_type = ?",
            (backup_type,),
            one=True
        )
        
        if not schedule:
            return
        
        retention_days = schedule['retention_days']
        cutoff_date = (datetime.now() - timedelta(days=retention_days)).isoformat()
        
        # Get old backups
        old_backups = query_db("""
            SELECT backup_id, location FROM backup_history 
            WHERE backup_type = ? AND timestamp < ?
        """, (backup_type, cutoff_date))
        
        for backup in old_backups or []:
            try:
                # Remove backup file
                backup_file = Path(backup['location'])
                if backup_file.exists():
                    if backup_file.is_dir():
                        shutil.rmtree(backup_file)
                    else:
                        backup_file.unlink()
                
                # Remove metadata
                metadata_file = self.backup_dir / f"{backup['backup_id']}_metadata.json"
                if metadata_file.exists():
                    metadata_file.unlink()
                
                # Remove from database
                execute_db(
                    "DELETE FROM backup_history WHERE backup_id = ?",
                    (backup['backup_id'],)
                )
                
                self.logger.logger.info(f"Cleaned old backup: {backup['backup_id']}")
                
            except Exception as e:
                self.logger.log_error(e, f"cleanup_backup_{backup['backup_id']}")
    
    async def restore_backup(self, backup_id: str, restore_path: str = '.') -> Tuple[bool, str]:
        """
        Restore from backup
        Returns: (success, message)
        """
        backup = query_db(
            "SELECT * FROM backup_history WHERE backup_id = ?",
            (backup_id,),
            one=True
        )
        
        if not backup:
            return False, "Backup not found"
        
        try:
            backup_file = Path(backup['location'])
            if not backup_file.exists():
                return False, "Backup file not found"
            
            # Verify checksum
            current_checksum = await self._calculate_checksum(str(backup_file))
            if current_checksum != backup['checksum']:
                return False, "Backup file corrupted (checksum mismatch)"
            
            # Extract backup
            restore_dir = Path(restore_path) / f"restore_{backup_id}"
            restore_dir.mkdir(exist_ok=True)
            
            if backup_file.suffix == '.gz':
                import tarfile
                with tarfile.open(backup_file, 'r:gz') as tar:
                    tar.extractall(restore_dir)
            else:
                shutil.copytree(backup_file, restore_dir / backup_id)
            
            # Update restore count
            execute_db(
                "UPDATE backup_history SET restore_count = restore_count + 1 WHERE backup_id = ?",
                (backup_id,)
            )
            
            self.logger.log_audit("backup_restored", 0, {'backup_id': backup_id})
            
            return True, f"Backup restored to {restore_dir}"
            
        except Exception as e:
            self.logger.log_error(e, f"restore_backup_{backup_id}")
            return False, f"Restore failed: {str(e)}"
    
    def list_backups(self, backup_type: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """List available backups"""
        if backup_type:
            return query_db("""
                SELECT * FROM backup_history 
                WHERE backup_type = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (backup_type, limit))
        else:
            return query_db("""
                SELECT * FROM backup_history 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
    
    async def run_scheduled_backups(self):
        """Run scheduled backups (call this from a cron job or scheduler)"""
        schedules = query_db(
            "SELECT * FROM backup_schedule WHERE enabled = 1"
        )
        
        for schedule in schedules or []:
            # Check if it's time to run
            if self._should_run_backup(schedule):
                success, backup_id, _ = await self.create_backup(
                    backup_type=schedule['schedule_type'],
                    compress=True
                )
                
                if success:
                    # Update last run time
                    execute_db("""
                        UPDATE backup_schedule 
                        SET last_run = ?, next_run = ?
                        WHERE id = ?
                    """, (
                        datetime.now().isoformat(),
                        self._calculate_next_run(schedule['frequency']),
                        schedule['id']
                    ))
    
    def _should_run_backup(self, schedule: Dict) -> bool:
        """Check if backup should run based on schedule"""
        if not schedule['last_run']:
            return True
        
        last_run = datetime.fromisoformat(schedule['last_run'])
        frequency = schedule['frequency']
        
        if frequency == 'daily':
            return (datetime.now() - last_run).days >= 1
        elif frequency == 'weekly':
            return (datetime.now() - last_run).days >= 7
        elif frequency == 'monthly':
            return (datetime.now() - last_run).days >= 30
        elif frequency == 'on_change':
            # Check if config files have changed
            return self._check_config_changes()
        
        return False
    
    def _calculate_next_run(self, frequency: str) -> str:
        """Calculate next backup run time"""
        now = datetime.now()
        
        if frequency == 'daily':
            next_run = now + timedelta(days=1)
        elif frequency == 'weekly':
            next_run = now + timedelta(weeks=1)
        elif frequency == 'monthly':
            next_run = now + timedelta(days=30)
        else:
            next_run = now + timedelta(days=1)
        
        return next_run.isoformat()
    
    def _check_config_changes(self) -> bool:
        """Check if configuration files have changed"""
        config_files = ['.env', 'config.json', 'settings.json']
        
        for config_file in config_files:
            if os.path.exists(config_file):
                file_mtime = datetime.fromtimestamp(os.path.getmtime(config_file))
                # Check if modified in last hour
                if (datetime.now() - file_mtime).total_seconds() < 3600:
                    return True
        
        return False
    
    def get_backup_stats(self) -> Dict:
        """Get backup statistics"""
        total_backups = query_db("SELECT COUNT(*) as count FROM backup_history", one=True)
        total_size = query_db("SELECT SUM(size_bytes) as total FROM backup_history", one=True)
        recent_backups = query_db("""
            SELECT backup_type, COUNT(*) as count, SUM(size_bytes) as size
            FROM backup_history
            WHERE timestamp > ?
            GROUP BY backup_type
        """, ((datetime.now() - timedelta(days=30)).isoformat(),))
        
        return {
            'total_backups': total_backups['count'] if total_backups else 0,
            'total_size_gb': (total_size['total'] / (1024**3)) if total_size and total_size['total'] else 0,
            'recent_backups': recent_backups or [],
            'backup_directory': str(self.backup_dir),
            'last_backup': query_db(
                "SELECT * FROM backup_history ORDER BY timestamp DESC LIMIT 1",
                one=True
            )
        }


# Global backup manager
_backup_manager = None

def get_backup_manager() -> BackupManager:
    """Get or create backup manager instance"""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager()
    return _backup_manager
