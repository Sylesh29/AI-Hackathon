INCIDENTS = {
    "db_timeout": {
        "signature": "db_timeout p95>1200 errors>2",
        "symptoms": [
            "p95_latency=1280ms",
            "db_pool_wait=340ms",
            "error_rate=2.4%",
        ],
        "root_cause": "Missing index on high-traffic lookup table.",
        "fix": "Add index on account_id and increase pool size.",
        "patch": "CREATE INDEX idx_accounts_account_id; DB_POOL_SIZE=40",
        "metrics_before": {"p95_latency_ms": 1280, "error_rate": 2.4},
        "metrics_after": {"p95_latency_ms": 240, "error_rate": 0.3},
    },
    "memory_leak": {
        "signature": "rss>2.4gb gc_pause>400",
        "symptoms": [
            "rss_memory=2.6GB",
            "gc_pause=520ms",
            "restart_count=3",
        ],
        "root_cause": "Cache retains unbounded session objects.",
        "fix": "Add TTL eviction and cap cache size.",
        "patch": "Enable cache TTL=15m; cap entries=50k",
        "metrics_before": {"rss_gb": 2.6, "gc_pause_ms": 520},
        "metrics_after": {"rss_gb": 1.1, "gc_pause_ms": 80},
    },
    "rate_limit": {
        "signature": "429>18 api_qps>1200",
        "symptoms": [
            "429_rate=19%",
            "api_qps=1400",
            "queue_depth=high",
        ],
        "root_cause": "Burst traffic with overly strict limits.",
        "fix": "Raise burst limit and add token bucket smoothing.",
        "patch": "Set BURST=300; TOKEN_BUCKET=enabled",
        "metrics_before": {"rate_429": 19, "api_qps": 1400},
        "metrics_after": {"rate_429": 1.2, "api_qps": 1100},
    },
}
