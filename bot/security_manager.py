"""
Advanced Security Manager with Encryption and Authentication
Provides end-to-end security, encryption, and threat detection
"""
import hashlib
import hmac
import secrets
import base64
import json
from typing import Dict, Optional, Tuple, List, Any
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import jwt
from .db import execute_db, query_db
from .advanced_logging import get_advanced_logger
from .config import logger


class SecurityManager:
    """Comprehensive security management system"""
    
    def __init__(self):
        self.logger = get_advanced_logger()
        self._create_tables()
        self.encryption_key = self._get_or_create_key()
        self.fernet = Fernet(self.encryption_key)
        self.jwt_secret = self._get_jwt_secret()
        self.threat_patterns = self._load_threat_patterns()
    
    def _create_tables(self):
        """Create security-related tables"""
        try:
            execute_db("""
                CREATE TABLE IF NOT EXISTS security_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_type TEXT NOT NULL,
                    key_value TEXT NOT NULL,
                    created_at TEXT,
                    expires_at TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            execute_db("""
                CREATE TABLE IF NOT EXISTS security_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT,
                    user_id INTEGER,
                    ip_address TEXT,
                    action TEXT,
                    result TEXT,
                    risk_level TEXT,
                    details TEXT
                )
            """)
            
            execute_db("""
                CREATE TABLE IF NOT EXISTS threat_detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    threat_type TEXT,
                    severity TEXT,
                    source TEXT,
                    user_id INTEGER,
                    action_taken TEXT,
                    blocked BOOLEAN DEFAULT 0
                )
            """)
            
            execute_db("""
                CREATE TABLE IF NOT EXISTS api_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_hash TEXT UNIQUE NOT NULL,
                    user_id INTEGER,
                    name TEXT,
                    permissions TEXT,
                    created_at TEXT,
                    last_used TEXT,
                    expires_at TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            execute_db("""
                CREATE TABLE IF NOT EXISTS ip_blacklist (
                    ip_address TEXT PRIMARY KEY,
                    reason TEXT,
                    added_at TEXT,
                    expires_at TEXT,
                    permanent BOOLEAN DEFAULT 0
                )
            """)
            
        except Exception as e:
            logger.error(f"Failed to create security tables: {e}")
    
    def _get_or_create_key(self) -> bytes:
        """Get or create master encryption key"""
        key = query_db(
            "SELECT key_value FROM security_keys WHERE key_type = 'master_key' AND is_active = 1",
            one=True
        )
        
        if key:
            return base64.urlsafe_b64decode(key['key_value'])
        else:
            # Generate new key
            new_key = Fernet.generate_key()
            execute_db("""
                INSERT INTO security_keys (key_type, key_value, created_at)
                VALUES (?, ?, ?)
            """, ('master_key', base64.urlsafe_b64encode(new_key).decode(), datetime.now().isoformat()))
            return new_key
    
    def _get_jwt_secret(self) -> str:
        """Get JWT secret for token generation"""
        secret = query_db(
            "SELECT key_value FROM security_keys WHERE key_type = 'jwt_secret' AND is_active = 1",
            one=True
        )
        
        if secret:
            return secret['key_value']
        else:
            # Generate new secret
            new_secret = secrets.token_urlsafe(64)
            execute_db("""
                INSERT INTO security_keys (key_type, key_value, created_at)
                VALUES (?, ?, ?)
            """, ('jwt_secret', new_secret, datetime.now().isoformat()))
            return new_secret
    
    def _load_threat_patterns(self) -> List[Dict]:
        """Load threat detection patterns"""
        return [
            {
                'pattern': r'(?i)(union\s+select|drop\s+table|delete\s+from)',
                'type': 'sql_injection',
                'severity': 'critical'
            },
            {
                'pattern': r'<script[^>]*>.*?</script>',
                'type': 'xss',
                'severity': 'high'
            },
            {
                'pattern': r'(?i)(cmd|powershell|bash|sh)\s*[|;&]',
                'type': 'command_injection',
                'severity': 'critical'
            },
            {
                'pattern': r'\.\./|\.\.\\',
                'type': 'path_traversal',
                'severity': 'high'
            },
            {
                'pattern': r'(?i)(password|token|api_key)\s*=\s*["\']?[a-zA-Z0-9]+',
                'type': 'credential_leak',
                'severity': 'high'
            }
        ]
    
    def encrypt_data(self, data: Any) -> str:
        """Encrypt sensitive data"""
        try:
            if not isinstance(data, bytes):
                data = json.dumps(data).encode()
            
            encrypted = self.fernet.encrypt(data)
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            self.logger.log_error(e, "encrypt_data")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> Any:
        """Decrypt sensitive data"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data)
            decrypted = self.fernet.decrypt(encrypted_bytes)
            
            # Try to parse as JSON
            try:
                return json.loads(decrypted.decode())
            except:
                return decrypted.decode()
        except Exception as e:
            self.logger.log_error(e, "decrypt_data")
            raise
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash password with salt"""
        if not salt:
            salt = secrets.token_hex(32)
        
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            100000  # iterations
        )
        
        return base64.b64encode(key).decode(), salt
    
    def verify_password(self, password: str, hashed: str, salt: str) -> bool:
        """Verify password against hash"""
        try:
            rehashed, _ = self.hash_password(password, salt)
            return hmac.compare_digest(rehashed, hashed)
        except:
            return False
    
    def generate_api_token(self, 
                          user_id: int,
                          name: str = "API Token",
                          permissions: List[str] = None,
                          expires_days: int = 30) -> str:
        """Generate secure API token"""
        token_data = {
            'user_id': user_id,
            'name': name,
            'permissions': permissions or ['read'],
            'exp': datetime.utcnow() + timedelta(days=expires_days),
            'iat': datetime.utcnow(),
            'jti': secrets.token_hex(16)  # JWT ID
        }
        
        token = jwt.encode(token_data, self.jwt_secret, algorithm='HS256')
        
        # Store token hash in database
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        execute_db("""
            INSERT INTO api_tokens 
            (token_hash, user_id, name, permissions, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            token_hash,
            user_id,
            name,
            json.dumps(permissions or ['read']),
            datetime.now().isoformat(),
            token_data['exp'].isoformat()
        ))
        
        self.audit_event('api_token_created', user_id, {'name': name})
        
        return token
    
    def verify_api_token(self, token: str) -> Optional[Dict]:
        """Verify and decode API token"""
        try:
            # Decode token
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            
            # Verify token exists and is active
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            db_token = query_db(
                "SELECT * FROM api_tokens WHERE token_hash = ? AND is_active = 1",
                (token_hash,),
                one=True
            )
            
            if not db_token:
                return None
            
            # Update last used
            execute_db(
                "UPDATE api_tokens SET last_used = ? WHERE token_hash = ?",
                (datetime.now().isoformat(), token_hash)
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            self.logger.logger.warning("Expired token attempted")
            return None
        except jwt.InvalidTokenError as e:
            self.logger.logger.warning(f"Invalid token: {e}")
            return None
    
    def detect_threats(self, data: str, user_id: Optional[int] = None) -> List[Dict]:
        """Detect security threats in user input"""
        threats = []
        
        import re
        for pattern_info in self.threat_patterns:
            if re.search(pattern_info['pattern'], data, re.IGNORECASE):
                threat = {
                    'type': pattern_info['type'],
                    'severity': pattern_info['severity'],
                    'detected_at': datetime.now().isoformat()
                }
                threats.append(threat)
                
                # Record threat
                execute_db("""
                    INSERT INTO threat_detections
                    (timestamp, threat_type, severity, source, user_id, action_taken)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    pattern_info['type'],
                    pattern_info['severity'],
                    data[:100],  # Store first 100 chars
                    user_id,
                    'detected'
                ))
        
        if threats:
            self.logger.logger.warning(
                f"Threats detected: {len(threats)} threats from user {user_id}"
            )
        
        return threats
    
    def check_ip_blacklist(self, ip_address: str) -> bool:
        """Check if IP is blacklisted"""
        blacklisted = query_db(
            """SELECT * FROM ip_blacklist 
               WHERE ip_address = ? 
               AND (permanent = 1 OR expires_at > ?)""",
            (ip_address, datetime.now().isoformat()),
            one=True
        )
        
        return blacklisted is not None
    
    def blacklist_ip(self, 
                    ip_address: str, 
                    reason: str,
                    duration_hours: Optional[int] = None):
        """Add IP to blacklist"""
        expires_at = None
        permanent = duration_hours is None
        
        if duration_hours:
            expires_at = (datetime.now() + timedelta(hours=duration_hours)).isoformat()
        
        execute_db("""
            INSERT OR REPLACE INTO ip_blacklist 
            (ip_address, reason, added_at, expires_at, permanent)
            VALUES (?, ?, ?, ?, ?)
        """, (ip_address, reason, datetime.now().isoformat(), expires_at, permanent))
        
        self.audit_event('ip_blacklisted', None, {
            'ip': ip_address,
            'reason': reason,
            'permanent': permanent
        })
    
    def audit_event(self,
                   event_type: str,
                   user_id: Optional[int] = None,
                   details: Optional[Dict] = None,
                   risk_level: str = 'low',
                   ip_address: Optional[str] = None):
        """Audit security events"""
        execute_db("""
            INSERT INTO security_audit
            (timestamp, event_type, user_id, ip_address, action, result, risk_level, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            event_type,
            user_id,
            ip_address,
            details.get('action', '') if details else '',
            details.get('result', 'success') if details else 'success',
            risk_level,
            json.dumps(details) if details else None
        ))
    
    def validate_input(self, 
                      data: str,
                      input_type: str = 'text',
                      max_length: int = 1000) -> Tuple[bool, Optional[str]]:
        """Validate and sanitize user input"""
        # Check length
        if len(data) > max_length:
            return False, f"Input too long (max {max_length} characters)"
        
        # Check for threats
        threats = self.detect_threats(data)
        if threats:
            return False, f"Security threat detected: {threats[0]['type']}"
        
        # Type-specific validation
        import re
        
        if input_type == 'email':
            if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', data):
                return False, "Invalid email format"
        
        elif input_type == 'phone':
            if not re.match(r'^[\d\+\-\(\)\s]+$', data):
                return False, "Invalid phone format"
        
        elif input_type == 'username':
            if not re.match(r'^[a-zA-Z0-9_]{3,30}$', data):
                return False, "Username must be 3-30 alphanumeric characters"
        
        elif input_type == 'url':
            if not re.match(r'^https?://[\w\.-]+(:\d+)?(/.*)?$', data):
                return False, "Invalid URL format"
        
        return True, None
    
    def generate_2fa_secret(self, user_id: int) -> str:
        """Generate 2FA secret for user"""
        import pyotp
        secret = pyotp.random_base32()
        
        # Store encrypted secret
        encrypted_secret = self.encrypt_data(secret)
        execute_db("""
            INSERT OR REPLACE INTO security_keys 
            (key_type, key_value, created_at)
            VALUES (?, ?, ?)
        """, (f'2fa_{user_id}', encrypted_secret, datetime.now().isoformat()))
        
        return secret
    
    def verify_2fa_code(self, user_id: int, code: str) -> bool:
        """Verify 2FA code"""
        import pyotp
        
        # Get encrypted secret
        secret_data = query_db(
            "SELECT key_value FROM security_keys WHERE key_type = ?",
            (f'2fa_{user_id}',),
            one=True
        )
        
        if not secret_data:
            return False
        
        try:
            secret = self.decrypt_data(secret_data['key_value'])
            totp = pyotp.TOTP(secret)
            return totp.verify(code, valid_window=1)
        except:
            return False
    
    def get_security_stats(self) -> Dict:
        """Get security statistics"""
        threats = query_db(
            "SELECT threat_type, COUNT(*) as count FROM threat_detections GROUP BY threat_type"
        )
        
        recent_audits = query_db("""
            SELECT event_type, COUNT(*) as count 
            FROM security_audit 
            WHERE timestamp > ?
            GROUP BY event_type
        """, ((datetime.now() - timedelta(days=1)).isoformat(),))
        
        blacklisted_ips = query_db(
            "SELECT COUNT(*) as count FROM ip_blacklist WHERE permanent = 1 OR expires_at > ?",
            (datetime.now().isoformat(),),
            one=True
        )
        
        active_tokens = query_db(
            "SELECT COUNT(*) as count FROM api_tokens WHERE is_active = 1 AND expires_at > ?",
            (datetime.now().isoformat(),),
            one=True
        )
        
        return {
            'threats_detected': threats or [],
            'recent_events': recent_audits or [],
            'blacklisted_ips': blacklisted_ips['count'] if blacklisted_ips else 0,
            'active_api_tokens': active_tokens['count'] if active_tokens else 0,
            'encryption_status': 'active' if self.fernet else 'inactive',
            'last_security_audit': query_db(
                "SELECT * FROM security_audit ORDER BY timestamp DESC LIMIT 1",
                one=True
            )
        }
    
    def perform_security_scan(self) -> Dict:
        """Perform comprehensive security scan"""
        issues = []
        
        # Check for weak passwords in config
        if query_db("SELECT * FROM users WHERE password IS NULL OR password = ''"):
            issues.append({
                'type': 'weak_authentication',
                'severity': 'high',
                'message': 'Users found with empty passwords'
            })
        
        # Check for expired tokens
        expired_tokens = query_db(
            "SELECT COUNT(*) as count FROM api_tokens WHERE is_active = 1 AND expires_at < ?",
            (datetime.now().isoformat(),),
            one=True
        )
        if expired_tokens and expired_tokens['count'] > 0:
            issues.append({
                'type': 'expired_tokens',
                'severity': 'medium',
                'message': f"{expired_tokens['count']} expired tokens still active"
            })
        
        # Check encryption key age
        key_age = query_db(
            "SELECT created_at FROM security_keys WHERE key_type = 'master_key'",
            one=True
        )
        if key_age:
            age_days = (datetime.now() - datetime.fromisoformat(key_age['created_at'])).days
            if age_days > 90:
                issues.append({
                    'type': 'old_encryption_key',
                    'severity': 'medium',
                    'message': f"Encryption key is {age_days} days old"
                })
        
        return {
            'scan_time': datetime.now().isoformat(),
            'issues_found': len(issues),
            'issues': issues,
            'security_score': max(0, 100 - (len(issues) * 10))
        }


# Global security manager
_security_manager = None

def get_security_manager() -> SecurityManager:
    """Get or create security manager instance"""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager


# Security decorators
def require_authentication(permissions: List[str] = None):
    """Decorator to require authentication"""
    def decorator(func):
        from functools import wraps
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract token from context
            context = args[1] if len(args) > 1 else None
            if not context:
                return {'error': 'Authentication required'}
            
            token = context.user_data.get('api_token')
            if not token:
                return {'error': 'No token provided'}
            
            security = get_security_manager()
            payload = security.verify_api_token(token)
            
            if not payload:
                return {'error': 'Invalid or expired token'}
            
            # Check permissions
            if permissions:
                user_perms = payload.get('permissions', [])
                if not any(p in user_perms for p in permissions):
                    return {'error': 'Insufficient permissions'}
            
            # Add user info to context
            context.user_data['authenticated_user'] = payload
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
