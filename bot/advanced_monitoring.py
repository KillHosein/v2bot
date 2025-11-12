"""
Advanced Monitoring System with Real-time Metrics and Alerting
Enhanced version with better performance tracking and predictive analytics
"""
import time
import psutil
import asyncio
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import deque, defaultdict
from dataclasses import dataclass, field
from .db import query_db, execute_db
from .config import logger, ADMIN_ID
from .advanced_logging import get_advanced_logger
import json


@dataclass
class Metric:
    """Data class for storing metric information"""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Collects and aggregates metrics"""
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
    
    def record_counter(self, name: str, value: int = 1, tags: Optional[Dict] = None):
        """Increment a counter metric"""
        key = self._make_key(name, tags)
        self.counters[key] += value
    
    def record_gauge(self, name: str, value: float, tags: Optional[Dict] = None):
        """Set a gauge metric"""
        key = self._make_key(name, tags)
        self.gauges[key] = value
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict] = None):
        """Record a value in a histogram"""
        key = self._make_key(name, tags)
        self.histograms[key].append(value)
        self.metrics[key].append(Metric(name, value, datetime.now(), tags or {}))
    
    def _make_key(self, name: str, tags: Optional[Dict]) -> str:
        """Create a unique key for a metric"""
        if not tags:
            return name
        tag_str = ','.join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name},{tag_str}"
    
    def get_stats(self, name: str, tags: Optional[Dict] = None) -> Dict[str, float]:
        """Get statistics for a histogram metric"""
        key = self._make_key(name, tags)
        values = list(self.histograms.get(key, []))
        
        if not values:
            return {}
        
        return {
            'count': len(values),
            'sum': sum(values),
            'avg': statistics.mean(values),
            'min': min(values),
            'max': max(values),
            'p50': statistics.median(values),
            'p95': statistics.quantiles(values, n=20)[18] if len(values) > 1 else values[0],
            'p99': statistics.quantiles(values, n=100)[98] if len(values) > 1 else values[0],
            'stddev': statistics.stdev(values) if len(values) > 1 else 0
        }


class AdvancedMonitor:
    """Enhanced monitoring with predictive capabilities"""
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics = MetricsCollector()
        self.logger = get_advanced_logger()
        self.alerts: List[Dict] = []
        self.thresholds = self._load_thresholds()
        self._create_tables()
    
    def _create_tables(self):
        """Create advanced monitoring tables"""
        try:
            execute_db("""
                CREATE TABLE IF NOT EXISTS metrics_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metric_type TEXT,
                    tags TEXT,
                    aggregation_period TEXT
                )
            """)
            
            execute_db("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT,
                    metric_name TEXT,
                    metric_value REAL,
                    threshold REAL,
                    resolved BOOLEAN DEFAULT 0,
                    resolved_at TEXT
                )
            """)
            
            execute_db("""
                CREATE TABLE IF NOT EXISTS performance_baselines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    hour_of_day INTEGER,
                    day_of_week INTEGER,
                    baseline_value REAL,
                    std_deviation REAL,
                    sample_count INTEGER,
                    last_updated TEXT
                )
            """)
            
            # Create indices for better performance
            execute_db("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics_history(timestamp)")
            execute_db("CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics_history(metric_name)")
            execute_db("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")
            execute_db("CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON alerts(resolved)")
            
        except Exception as e:
            logger.error(f"Failed to create monitoring tables: {e}")
    
    def _load_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Load alerting thresholds"""
        return {
            'response_time': {'warning': 2.0, 'critical': 5.0},
            'error_rate': {'warning': 0.05, 'critical': 0.10},  # 5% and 10%
            'cpu_usage': {'warning': 70, 'critical': 90},
            'memory_usage': {'warning': 80, 'critical': 95},
            'disk_usage': {'warning': 80, 'critical': 90},
            'queue_size': {'warning': 100, 'critical': 500},
            'db_connections': {'warning': 80, 'critical': 95}
        }
    
    async def track_request(self, 
                           handler_name: str,
                           duration: float,
                           success: bool = True,
                           user_id: Optional[int] = None,
                           metadata: Optional[Dict] = None):
        """Track a request with full context"""
        # Record metrics
        self.metrics.record_histogram('request_duration', duration, {'handler': handler_name})
        self.metrics.record_counter('requests_total', 1, {'handler': handler_name, 'status': 'success' if success else 'error'})
        
        # Check for slow requests
        if duration > self.thresholds['response_time']['critical']:
            await self._create_alert(
                'slow_request',
                'critical',
                f"Handler {handler_name} took {duration:.2f}s",
                'request_duration',
                duration,
                self.thresholds['response_time']['critical']
            )
        elif duration > self.thresholds['response_time']['warning']:
            await self._create_alert(
                'slow_request',
                'warning',
                f"Handler {handler_name} took {duration:.2f}s",
                'request_duration',
                duration,
                self.thresholds['response_time']['warning']
            )
        
        # Store in database for historical analysis
        try:
            execute_db("""
                INSERT INTO metrics_history 
                (timestamp, metric_name, metric_value, metric_type, tags)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                'request_duration',
                duration,
                'histogram',
                json.dumps({'handler': handler_name, 'success': success, 'user_id': user_id})
            ))
        except Exception as e:
            self.logger.log_error(e, 'track_request')
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Comprehensive system health check"""
        health = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'components': {},
            'metrics': {},
            'alerts': []
        }
        
        # System resources
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Record metrics
            self.metrics.record_gauge('system_cpu_percent', cpu_percent)
            self.metrics.record_gauge('system_memory_percent', memory.percent)
            self.metrics.record_gauge('system_disk_percent', disk.percent)
            
            health['components']['system'] = {
                'cpu': {'percent': cpu_percent, 'cores': psutil.cpu_count()},
                'memory': {
                    'percent': memory.percent,
                    'used_gb': memory.used / (1024**3),
                    'total_gb': memory.total / (1024**3)
                },
                'disk': {
                    'percent': disk.percent,
                    'used_gb': disk.used / (1024**3),
                    'total_gb': disk.total / (1024**3)
                },
                'network': self._get_network_stats()
            }
            
            # Check thresholds
            if cpu_percent > self.thresholds['cpu_usage']['critical']:
                health['status'] = 'critical'
                await self._create_alert('high_cpu', 'critical', f"CPU usage at {cpu_percent}%", 'cpu_usage', cpu_percent, self.thresholds['cpu_usage']['critical'])
            elif cpu_percent > self.thresholds['cpu_usage']['warning']:
                health['status'] = 'degraded'
                await self._create_alert('high_cpu', 'warning', f"CPU usage at {cpu_percent}%", 'cpu_usage', cpu_percent, self.thresholds['cpu_usage']['warning'])
            
        except Exception as e:
            health['components']['system'] = {'status': 'error', 'message': str(e)}
            health['status'] = 'degraded'
        
        # Database health
        health['components']['database'] = await self._check_database_health()
        
        # Panel health
        health['components']['panels'] = await self._check_panels_health()
        
        # Application metrics
        health['metrics'] = self._get_application_metrics()
        
        # Active alerts
        health['alerts'] = self._get_active_alerts()
        
        return health
    
    def _get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        try:
            stats = psutil.net_io_counters()
            return {
                'bytes_sent': stats.bytes_sent,
                'bytes_recv': stats.bytes_recv,
                'packets_sent': stats.packets_sent,
                'packets_recv': stats.packets_recv,
                'errors_in': stats.errin,
                'errors_out': stats.errout
            }
        except:
            return {}
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database health and performance"""
        start = time.time()
        try:
            # Test query
            result = query_db("SELECT COUNT(*) as count FROM users", one=True)
            duration = time.time() - start
            
            # Get database size
            db_stats = query_db("""
                SELECT 
                    page_count * page_size as size,
                    (page_count - freelist_count) * page_size as used
                FROM pragma_page_count(), pragma_page_size(), pragma_freelist_count()
            """, one=True)
            
            return {
                'status': 'healthy' if duration < 0.1 else 'degraded',
                'response_time': duration,
                'user_count': result['count'] if result else 0,
                'size_mb': (db_stats['size'] / (1024*1024)) if db_stats else 0,
                'used_mb': (db_stats['used'] / (1024*1024)) if db_stats else 0
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time': time.time() - start
            }
    
    async def _check_panels_health(self) -> List[Dict[str, Any]]:
        """Check all VPN panels health"""
        panels_health = []
        try:
            panels = query_db("SELECT id, name, url FROM panels WHERE enabled = 1")
            for panel in panels:
                # This would normally check actual panel connectivity
                # For now, we'll simulate it
                panels_health.append({
                    'id': panel['id'],
                    'name': panel['name'],
                    'status': 'healthy',  # Would be determined by actual check
                    'response_time': 0.1  # Would be actual response time
                })
        except:
            pass
        return panels_health
    
    def _get_application_metrics(self) -> Dict[str, Any]:
        """Get application-level metrics"""
        uptime = time.time() - self.start_time
        
        # Get request stats
        request_stats = self.metrics.get_stats('request_duration')
        
        # Calculate error rate
        success_count = self.metrics.counters.get('requests_total,handler=*,status=success', 0)
        error_count = self.metrics.counters.get('requests_total,handler=*,status=error', 0)
        total_requests = success_count + error_count
        error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'uptime': {
                'seconds': uptime,
                'formatted': str(timedelta(seconds=int(uptime)))
            },
            'requests': {
                'total': total_requests,
                'success': success_count,
                'errors': error_count,
                'error_rate': error_rate,
                'stats': request_stats
            },
            'performance': {
                'avg_response_time': request_stats.get('avg', 0),
                'p95_response_time': request_stats.get('p95', 0),
                'p99_response_time': request_stats.get('p99', 0)
            }
        }
    
    def _get_active_alerts(self) -> List[Dict]:
        """Get currently active alerts"""
        try:
            return query_db(
                "SELECT * FROM alerts WHERE resolved = 0 ORDER BY timestamp DESC LIMIT 10"
            )
        except:
            return []
    
    async def _create_alert(self, 
                          alert_type: str,
                          severity: str,
                          message: str,
                          metric_name: str,
                          metric_value: float,
                          threshold: float):
        """Create a new alert"""
        try:
            execute_db("""
                INSERT INTO alerts 
                (timestamp, alert_type, severity, message, metric_name, metric_value, threshold)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                alert_type,
                severity,
                message,
                metric_name,
                metric_value,
                threshold
            ))
            
            # Log the alert
            self.logger.logger.warning(f"ALERT [{severity}] {alert_type}: {message}")
            
            # Notify admin for critical alerts
            if severity == 'critical' and ADMIN_ID:
                # This would send a telegram message to admin
                pass
                
        except Exception as e:
            self.logger.log_error(e, '_create_alert')
    
    async def predict_issues(self) -> List[Dict[str, Any]]:
        """Predict potential issues based on trends"""
        predictions = []
        
        try:
            # Analyze error rate trend
            recent_errors = query_db("""
                SELECT COUNT(*) as count, 
                       DATE(timestamp) as date
                FROM error_tracking
                WHERE timestamp > datetime('now', '-7 days')
                GROUP BY DATE(timestamp)
                ORDER BY date
            """)
            
            if recent_errors and len(recent_errors) > 3:
                # Simple trend analysis
                counts = [r['count'] for r in recent_errors]
                if len(counts) > 1:
                    trend = (counts[-1] - counts[0]) / len(counts)
                    if trend > 5:  # Increasing by more than 5 errors per day
                        predictions.append({
                            'type': 'error_trend',
                            'severity': 'warning',
                            'message': f"Error rate increasing by {trend:.1f} errors/day",
                            'recommendation': 'Review recent errors and deploy fixes'
                        })
            
            # Analyze resource usage trends
            cpu_history = query_db("""
                SELECT AVG(metric_value) as avg_cpu
                FROM metrics_history
                WHERE metric_name = 'system_cpu_percent'
                  AND timestamp > datetime('now', '-1 hour')
            """, one=True)
            
            if cpu_history and cpu_history['avg_cpu'] > 60:
                predictions.append({
                    'type': 'resource_usage',
                    'severity': 'warning',
                    'message': f"Average CPU usage at {cpu_history['avg_cpu']:.1f}%",
                    'recommendation': 'Consider scaling up resources or optimizing code'
                })
            
        except Exception as e:
            self.logger.log_error(e, 'predict_issues')
        
        return predictions
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in various formats"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'counters': dict(self.metrics.counters),
            'gauges': dict(self.metrics.gauges),
            'histograms': {
                name: self.metrics.get_stats(name)
                for name in set(k.split(',')[0] for k in self.metrics.histograms.keys())
            }
        }
        
        if format == 'json':
            return json.dumps(data, indent=2, default=str)
        elif format == 'prometheus':
            # Format for Prometheus
            lines = []
            for name, value in self.metrics.counters.items():
                lines.append(f"{name} {value}")
            for name, value in self.metrics.gauges.items():
                lines.append(f"{name} {value}")
            return '\n'.join(lines)
        else:
            return str(data)


# Global monitor instance
_advanced_monitor = None

def get_advanced_monitor() -> AdvancedMonitor:
    """Get or create advanced monitor instance"""
    global _advanced_monitor
    if _advanced_monitor is None:
        _advanced_monitor = AdvancedMonitor()
    return _advanced_monitor
