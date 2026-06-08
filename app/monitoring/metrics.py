"""
In-Memory Metrics Collection.

Tracks operational metrics for observability and the feedback loop:
- Query latency (P50, P95, P99)
- Ingestion throughput
- Retrieval scores
- Error counts
- LLM token usage

Continuation Note:
    This module is complete. Metrics are stored in-memory (reset on restart).
    For production, replace with Prometheus or similar. Access via GET /health/metrics.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, List


@dataclass
class MetricsStore:
    """Thread-safe in-memory metrics store."""

    # Query metrics
    query_count: int = 0
    query_latencies_ms: List[float] = field(default_factory=list)
    
    # Ingestion metrics
    ingestion_count: int = 0
    total_chunks_created: int = 0
    total_pages_processed: int = 0
    ingestion_times_seconds: List[float] = field(default_factory=list)
    
    # Retrieval metrics
    retrieval_scores: List[float] = field(default_factory=list)
    
    # Error metrics
    error_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    # LLM metrics
    llm_calls: int = 0
    llm_total_tokens: int = 0
    
    # Feedback metrics
    thumbs_up: int = 0
    thumbs_down: int = 0

    # Lock for thread safety
    _lock: Lock = field(default_factory=Lock, repr=False)

    def record_query(self, latency_ms: float) -> None:
        """Record a completed query with its latency."""
        with self._lock:
            self.query_count += 1
            self.query_latencies_ms.append(latency_ms)
            # Keep only last 1000 latencies to bound memory
            if len(self.query_latencies_ms) > 1000:
                self.query_latencies_ms = self.query_latencies_ms[-1000:]

    def record_ingestion(self, chunks: int, pages: int, time_seconds: float) -> None:
        """Record a completed ingestion run."""
        with self._lock:
            self.ingestion_count += 1
            self.total_chunks_created += chunks
            self.total_pages_processed += pages
            self.ingestion_times_seconds.append(time_seconds)

    def record_retrieval_score(self, score: float) -> None:
        """Record top retrieval similarity score for a query."""
        with self._lock:
            self.retrieval_scores.append(score)
            if len(self.retrieval_scores) > 1000:
                self.retrieval_scores = self.retrieval_scores[-1000:]

    def record_error(self, error_type: str) -> None:
        """Increment error count for a given error type."""
        with self._lock:
            self.error_counts[error_type] += 1

    def record_llm_call(self, tokens: int = 0) -> None:
        """Record an LLM API call."""
        with self._lock:
            self.llm_calls += 1
            self.llm_total_tokens += tokens

    def record_feedback(self, is_positive: bool) -> None:
        """Record user feedback."""
        with self._lock:
            if is_positive:
                self.thumbs_up += 1
            else:
                self.thumbs_down += 1

    def get_summary(self) -> dict:
        """Get a summary of all metrics."""
        with self._lock:
            latencies = sorted(self.query_latencies_ms) if self.query_latencies_ms else [0]
            scores = sorted(self.retrieval_scores) if self.retrieval_scores else [0]
            
            return {
                "queries": {
                    "total": self.query_count,
                    "latency_p50_ms": latencies[len(latencies) // 2] if latencies else 0,
                    "latency_p95_ms": latencies[int(len(latencies) * 0.95)] if len(latencies) > 1 else latencies[0],
                    "latency_p99_ms": latencies[int(len(latencies) * 0.99)] if len(latencies) > 1 else latencies[0],
                },
                "ingestion": {
                    "total_runs": self.ingestion_count,
                    "total_chunks": self.total_chunks_created,
                    "total_pages": self.total_pages_processed,
                },
                "retrieval": {
                    "avg_top_score": sum(scores) / len(scores) if scores else 0,
                },
                "llm": {
                    "total_calls": self.llm_calls,
                    "total_tokens": self.llm_total_tokens,
                },
                "feedback": {
                    "thumbs_up": self.thumbs_up,
                    "thumbs_down": self.thumbs_down,
                    "satisfaction_rate": (
                        self.thumbs_up / (self.thumbs_up + self.thumbs_down)
                        if (self.thumbs_up + self.thumbs_down) > 0
                        else None
                    ),
                },
                "errors": dict(self.error_counts),
            }


# Global metrics instance — imported by all services
metrics = MetricsStore()


class Timer:
    """Context manager for timing operations."""

    def __init__(self):
        self.start_time = None
        self.elapsed_ms = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000
