"""
Application metrics for monitoring performance and usage.

This module tracks:
- Request counts per endpoint
- Response times
- Error rates
- Business metrics (goals created, quizzes taken, etc.)
"""
from collections import defaultdict
from datetime import datetime
from typing import Dict, Any
import time


class MetricsCollector:
    """
    Simple in-memory metrics collector.
    
    In production, use Prometheus/DataDog/New Relic instead.
    This is a lightweight alternative for learning.
    """
    
    def __init__(self):
        self.request_count = defaultdict(int)
        self.error_count = defaultdict(int)
        self.response_times = defaultdict(list)
        self.business_metrics = {
            "total_requests": 0,
            "total_errors": 0,
            "goals_created": 0,
            "quizzes_generated": 0,
            "quizzes_completed": 0,
            "users_registered": 0,
        }
        self.start_time = datetime.utcnow()
    
    def increment_request(self, endpoint: str, method: str):
        """Track request to an endpoint."""
        key = f"{method}:{endpoint}"
        self.request_count[key] += 1
        self.business_metrics["total_requests"] += 1
    
    def increment_error(self, endpoint: str, status_code: int):
        """Track error response."""
        key = f"{endpoint}:{status_code}"
        self.error_count[key] += 1
        self.business_metrics["total_errors"] += 1
    
    def record_response_time(self, endpoint: str, duration_ms: float):
        """Track response time for an endpoint."""
        self.response_times[endpoint].append(duration_ms)
        
        # Keep only last 100 requests per endpoint to avoid memory issues
        if len(self.response_times[endpoint]) > 100:
            self.response_times[endpoint] = self.response_times[endpoint][-100:]
    
    def increment_business_metric(self, metric_name: str):
        """Track business metrics (goals created, etc.)."""
        if metric_name in self.business_metrics:
            self.business_metrics[metric_name] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current metrics summary."""
        uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
        
        # Calculate average response times per endpoint
        avg_response_times = {}
        for endpoint, times in self.response_times.items():
            if times:
                avg_response_times[endpoint] = sum(times) / len(times)
        
        # Find slowest endpoints
        slowest_endpoints = sorted(
            avg_response_times.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Calculate error rate
        total_requests = self.business_metrics["total_requests"]
        total_errors = self.business_metrics["total_errors"]
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "uptime_seconds": int(uptime_seconds),
            "uptime_formatted": f"{int(uptime_seconds // 3600)}h {int((uptime_seconds % 3600) // 60)}m",
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate_percent": round(error_rate, 2),
            "requests_per_endpoint": dict(self.request_count),
            "slowest_endpoints": [
                {"endpoint": endpoint, "avg_ms": round(ms, 2)}
                for endpoint, ms in slowest_endpoints
            ],
            "business_metrics": {
                "users_registered": self.business_metrics["users_registered"],
                "goals_created": self.business_metrics["goals_created"],
                "quizzes_generated": self.business_metrics["quizzes_generated"],
                "quizzes_completed": self.business_metrics["quizzes_completed"],
            }
        }
    
    def reset(self):
        """Reset all metrics (for testing or daily reset)."""
        self.__init__()


# Global metrics collector instance
metrics = MetricsCollector()
