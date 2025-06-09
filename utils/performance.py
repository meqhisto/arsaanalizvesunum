"""
Performance monitoring and optimization utilities
"""

import time
import threading
from functools import wraps
from collections import defaultdict, deque
from datetime import datetime, timedelta
from flask import request, g, current_app

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class PerformanceMonitor:
    """Monitor application performance metrics"""
    
    def __init__(self):
        self.request_times = deque(maxlen=1000)  # Last 1000 requests
        self.slow_queries = deque(maxlen=100)    # Last 100 slow queries
        self.error_count = defaultdict(int)
        self.endpoint_stats = defaultdict(lambda: {'count': 0, 'total_time': 0, 'avg_time': 0})
        self._lock = threading.Lock()
    
    def record_request(self, endpoint, duration, status_code):
        """Record request performance data"""
        with self._lock:
            self.request_times.append({
                'endpoint': endpoint,
                'duration': duration,
                'status_code': status_code,
                'timestamp': datetime.now()
            })
            
            # Update endpoint statistics
            stats = self.endpoint_stats[endpoint]
            stats['count'] += 1
            stats['total_time'] += duration
            stats['avg_time'] = stats['total_time'] / stats['count']
            
            # Record errors
            if status_code >= 400:
                self.error_count[status_code] += 1
    
    def record_slow_query(self, query, duration, params=None):
        """Record slow database queries"""
        with self._lock:
            self.slow_queries.append({
                'query': str(query)[:500],  # Truncate long queries
                'duration': duration,
                'params': params,
                'timestamp': datetime.now()
            })
    
    def get_stats(self):
        """Get performance statistics"""
        with self._lock:
            if not self.request_times:
                return {}
            
            # Calculate request statistics
            durations = [req['duration'] for req in self.request_times]
            recent_requests = [req for req in self.request_times 
                             if req['timestamp'] > datetime.now() - timedelta(minutes=5)]
            
            stats = {
                'total_requests': len(self.request_times),
                'avg_response_time': sum(durations) / len(durations),
                'min_response_time': min(durations),
                'max_response_time': max(durations),
                'requests_per_minute': len(recent_requests),
                'error_rate': sum(1 for req in self.request_times if req['status_code'] >= 400) / len(self.request_times),
                'slow_queries_count': len(self.slow_queries),
                'endpoint_stats': dict(self.endpoint_stats),
                'error_breakdown': dict(self.error_count)
            }
            
            # Add percentiles
            sorted_durations = sorted(durations)
            stats['p50_response_time'] = sorted_durations[len(sorted_durations) // 2]
            stats['p95_response_time'] = sorted_durations[int(len(sorted_durations) * 0.95)]
            stats['p99_response_time'] = sorted_durations[int(len(sorted_durations) * 0.99)]
            
            return stats
    
    def get_slow_queries(self, limit=10):
        """Get slowest queries"""
        with self._lock:
            return sorted(list(self.slow_queries), 
                         key=lambda x: x['duration'], reverse=True)[:limit]
    
    def clear_stats(self):
        """Clear all performance statistics"""
        with self._lock:
            self.request_times.clear()
            self.slow_queries.clear()
            self.error_count.clear()
            self.endpoint_stats.clear()


# Global performance monitor
performance_monitor = PerformanceMonitor()


def monitor_performance(func):
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            if duration > 1.0:  # Log slow functions (>1 second)
                current_app.logger.warning(
                    f"Slow function: {func.__name__} took {duration:.2f}s"
                )
    return wrapper


def monitor_database_query(func):
    """Decorator to monitor database query performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            if duration > 0.5:  # Log slow queries (>500ms)
                performance_monitor.record_slow_query(
                    query=f"{func.__name__}",
                    duration=duration,
                    params=str(args)[:200] if args else None
                )
    return wrapper


class SystemMonitor:
    """Monitor system resources"""
    
    @staticmethod
    def get_system_stats():
        """Get current system statistics"""
        if not PSUTIL_AVAILABLE:
            return {'error': 'psutil not available'}

        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'memory_total_gb': memory.total / (1024**3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3),
                'disk_total_gb': disk.total / (1024**3),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            current_app.logger.error(f"Error getting system stats: {e}")
            return {}
    
    @staticmethod
    def get_process_stats():
        """Get current process statistics"""
        if not PSUTIL_AVAILABLE:
            return {'error': 'psutil not available'}

        try:
            process = psutil.Process()

            return {
                'pid': process.pid,
                'cpu_percent': process.cpu_percent(),
                'memory_percent': process.memory_percent(),
                'memory_rss_mb': process.memory_info().rss / (1024**2),
                'memory_vms_mb': process.memory_info().vms / (1024**2),
                'num_threads': process.num_threads(),
                'num_fds': process.num_fds() if hasattr(process, 'num_fds') else 0,
                'create_time': datetime.fromtimestamp(process.create_time()).isoformat()
            }
        except Exception as e:
            current_app.logger.error(f"Error getting process stats: {e}")
            return {}


class DatabaseMonitor:
    """Monitor database performance"""
    
    @staticmethod
    def get_connection_stats():
        """Get database connection statistics"""
        try:
            from models import db
            
            # Get connection pool info if available
            engine = db.engine
            pool = engine.pool
            
            stats = {
                'pool_size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'invalid': pool.invalid()
            }
            
            return stats
        except Exception as e:
            current_app.logger.error(f"Error getting DB connection stats: {e}")
            return {}
    
    @staticmethod
    def test_query_performance():
        """Test basic query performance"""
        try:
            from models import db
            from models.user_models import User
            
            start_time = time.time()
            
            # Simple query test
            user_count = User.query.count()
            
            duration = time.time() - start_time
            
            return {
                'query_duration': duration,
                'user_count': user_count,
                'status': 'healthy' if duration < 1.0 else 'slow'
            }
        except Exception as e:
            current_app.logger.error(f"Error testing query performance: {e}")
            return {'status': 'error', 'error': str(e)}


def setup_performance_monitoring(app):
    """Setup performance monitoring for Flask app"""
    
    @app.before_request
    def before_request():
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            endpoint = request.endpoint or 'unknown'
            
            performance_monitor.record_request(
                endpoint=endpoint,
                duration=duration,
                status_code=response.status_code
            )
            
            # Log slow requests
            if duration > 2.0:
                current_app.logger.warning(
                    f"Slow request: {request.method} {request.path} "
                    f"took {duration:.2f}s (status: {response.status_code})"
                )
        
        return response
    
    @app.route('/health/performance')
    def performance_health():
        """Performance health check endpoint"""
        stats = {
            'performance': performance_monitor.get_stats(),
            'system': SystemMonitor.get_system_stats(),
            'process': SystemMonitor.get_process_stats(),
            'database': DatabaseMonitor.get_connection_stats(),
            'query_test': DatabaseMonitor.test_query_performance()
        }
        
        return stats


class PerformanceOptimizer:
    """Automatic performance optimization utilities"""
    
    @staticmethod
    def optimize_query_cache():
        """Optimize query cache based on usage patterns"""
        from utils.cache import cache
        
        stats = performance_monitor.get_stats()
        
        # Clear cache if error rate is high
        if stats.get('error_rate', 0) > 0.1:
            cache.clear()
            current_app.logger.info("Cleared cache due to high error rate")
        
        # Warm cache for frequently accessed endpoints
        frequent_endpoints = [
            endpoint for endpoint, data in stats.get('endpoint_stats', {}).items()
            if data['count'] > 10 and data['avg_time'] > 0.5
        ]
        
        return frequent_endpoints
    
    @staticmethod
    def suggest_optimizations():
        """Suggest performance optimizations based on monitoring data"""
        suggestions = []
        stats = performance_monitor.get_stats()
        
        # Check response times
        if stats.get('avg_response_time', 0) > 1.0:
            suggestions.append("Average response time is high. Consider adding caching or optimizing queries.")
        
        # Check slow queries
        if stats.get('slow_queries_count', 0) > 10:
            suggestions.append("Multiple slow queries detected. Review database indexes and query optimization.")
        
        # Check error rate
        if stats.get('error_rate', 0) > 0.05:
            suggestions.append("High error rate detected. Review error logs and fix issues.")
        
        # Check system resources
        system_stats = SystemMonitor.get_system_stats()
        if system_stats.get('memory_percent', 0) > 80:
            suggestions.append("High memory usage. Consider optimizing memory usage or scaling up.")
        
        if system_stats.get('cpu_percent', 0) > 80:
            suggestions.append("High CPU usage. Consider optimizing CPU-intensive operations or scaling up.")
        
        return suggestions


# Utility functions for performance testing
def benchmark_function(func, *args, **kwargs):
    """Benchmark a function's execution time"""
    start_time = time.time()
    result = func(*args, **kwargs)
    duration = time.time() - start_time
    
    return {
        'result': result,
        'duration': duration,
        'function': func.__name__
    }


def profile_memory_usage(func):
    """Profile memory usage of a function"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        import tracemalloc
        
        tracemalloc.start()
        result = func(*args, **kwargs)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        current_app.logger.info(
            f"Memory usage for {func.__name__}: "
            f"current={current / 1024 / 1024:.2f}MB, "
            f"peak={peak / 1024 / 1024:.2f}MB"
        )
        
        return result
    return wrapper
