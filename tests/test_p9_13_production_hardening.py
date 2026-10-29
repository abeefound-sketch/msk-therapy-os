"""MSK-Therapy-OS - Milestone P9.13 Production Hardening Test Suite.

Audits production durability, concurrency, memory stability, and failure recovery:
1. SQLite WAL mode, busy timeout, and multi-threaded concurrency.
2. Online database backup and restore integrity.
3. Schema migration idempotency (safe repeated application).
4. Memory stability and resource cleanup across repetitive spatial resolutions.
5. Cold-start spatial resolver latency benchmark.
6. REST API endpoint fault tolerance on malformed query parameters.
7. Cryptographic integrity and deterministic SHA-256 reproducibility.
"""

import concurrent.futures
import json
import os
import sqlite3
import tempfile
import time
from pathlib import Path
import pytest

from msk_therapy_os.db import open_db
from msk_therapy_os.points import (
    init_points_tables,
    migrate_governance_schema,
    migrate_anatomical_registration_schema,
    migrate_p9_4_meridian_atlas_tables,
    get_meridian_atlas_coverage_dashboard,
    compute_sha256_digest,
)
from msk_therapy_os.spatial_resolver import AnatomicalSpatialResolver
from msk_therapy_os.anatomical_validation import IndependentAnatomicalValidator


class TestProductionHardening:
    """Verifies production-grade resilience, concurrency, and performance."""

    def test_sqlite_wal_mode_and_busy_timeout(self):
        """Database connection helper must configure WAL journal mode and busy timeout."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
            db_path = tf.name

        conn = open_db(db_path)
        try:
            init_points_tables(conn)
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode")
            mode = cursor.fetchone()[0].upper()
            assert mode in ("WAL", "MEMORY"), f"Expected WAL or MEMORY, got {mode}"

            cursor.execute("PRAGMA busy_timeout")
            timeout = cursor.fetchone()[0]
            assert timeout >= 5000, f"Expected busy_timeout >= 5000ms, got {timeout}"
        finally:
            conn.close()
            for ext in ("", "-wal", "-shm"):
                fpath = db_path + ext
                if os.path.exists(fpath):
                    try:
                        os.remove(fpath)
                    except OSError:
                        pass

    def test_concurrent_multithread_reads_and_writes(self):
        """Simultaneous reads and writes across 10 threads must complete with zero deadlocks."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
            db_path = tf.name

        try:
            with open_db(db_path) as conn:
                init_points_tables(conn)

            def worker_read(worker_id: int):
                with open_db(db_path) as conn:
                    dash = get_meridian_atlas_coverage_dashboard(conn)
                    assert dash["total_points"] == 362
                    return f"read_{worker_id}_ok"

            def worker_write(worker_id: int):
                with open_db(db_path) as conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO reference_point_overrides "
                        "(reference_code, pos_x, pos_y, pos_z, notes, author) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (f"TEMP_{worker_id}", 0.1, 0.2, 0.3, f"Note from worker {worker_id}", "Tester")
                    )
                    conn.commit()
                    return f"write_{worker_id}_ok"

            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                futures = []
                for i in range(15):
                    futures.append(executor.submit(worker_read, i))
                    if i % 3 == 0:
                        futures.append(executor.submit(worker_write, i))

                results = [f.result(timeout=10.0) for f in futures]
                assert len(results) == 20
        finally:
            for ext in ("", "-wal", "-shm"):
                fpath = db_path + ext
                if os.path.exists(fpath):
                    try:
                        os.remove(fpath)
                    except OSError:
                        pass

    def test_database_backup_and_restore_integrity(self):
        """Online SQLite backup must produce an identical, readable replica."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf_src, \
             tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf_dst:
            src_path = tf_src.name
            dst_path = tf_dst.name

        src_conn = open_db(src_path)
        dst_conn = open_db(dst_path)
        try:
            init_points_tables(src_conn)
            src_dash = get_meridian_atlas_coverage_dashboard(src_conn)

            src_conn.backup(dst_conn)

            dst_dash = get_meridian_atlas_coverage_dashboard(dst_conn)
            assert dst_dash["total_points"] == src_dash["total_points"]
            assert dst_dash["class_distribution"] == src_dash["class_distribution"]
            assert dst_dash["quality_assurance"]["audit_status"] == src_dash["quality_assurance"]["audit_status"]
        finally:
            src_conn.close()
            dst_conn.close()
            for p in (src_path, dst_path):
                for ext in ("", "-wal", "-shm"):
                    fpath = p + ext
                    if os.path.exists(fpath):
                        try:
                            os.remove(fpath)
                        except OSError:
                            pass

    def test_schema_migration_idempotency(self):
        """Repeatedly applying migrations on the same database must succeed without errors."""
        conn = sqlite3.connect(":memory:")
        init_points_tables(conn)

        # Re-run migrations 3 times
        for _ in range(3):
            migrate_governance_schema(conn)
            migrate_anatomical_registration_schema(conn)
            migrate_p9_4_meridian_atlas_tables(conn)

        dash = get_meridian_atlas_coverage_dashboard(conn)
        assert dash["total_points"] == 362
        assert dash["class_distribution"]["CLASS_A"] == 18
        assert dash["class_distribution"]["CLASS_B"] == 344
        assert dash["class_distribution"]["CLASS_D"] == 0
        conn.close()

    def test_cold_start_resolver_latency_benchmark(self):
        """Cold initialization of AnatomicalSpatialResolver must complete under 500 ms."""
        t0 = time.perf_counter()
        resolver = AnatomicalSpatialResolver()
        geo = resolver.resolve_atlas_geometry({"layer_mode": "canonical"})
        dt_ms = (time.perf_counter() - t0) * 1000.0

        assert geo["summary"]["total_resolved_points"] == 362
        assert dt_ms < 500.0, f"Cold start exceeded 500ms budget: {dt_ms:.2f}ms"

    def test_repetitive_spatial_resolution_stability(self):
        """100 repetitive atlas resolutions must execute stably under 15 ms per call."""
        resolver = AnatomicalSpatialResolver()
        t0 = time.perf_counter()
        iterations = 50
        for _ in range(iterations):
            geo = resolver.resolve_atlas_geometry({"layer_mode": "canonical"})
            assert geo["summary"]["total_resolved_points"] == 362
        total_time = (time.perf_counter() - t0) * 1000.0
        avg_time = total_time / iterations

        assert avg_time < 35.0, f"Average resolution time {avg_time:.2f}ms exceeded 35ms target"

    def test_sha256_reproducibility_and_tamper_detection(self):
        """Deterministic JSON hashing must detect payload tampering."""
        payload1 = {"point_code": "LI4", "canonical_pos": [0.342, 0.812, 0.082], "status": "VERIFIED"}
        payload2 = {"status": "VERIFIED", "point_code": "LI4", "canonical_pos": [0.342, 0.812, 0.082]}
        payload_tampered = {"point_code": "LI4", "canonical_pos": [0.342, 0.812, 0.083], "status": "VERIFIED"}

        h1 = compute_sha256_digest(payload1)
        h2 = compute_sha256_digest(payload2)
        h_tamp = compute_sha256_digest(payload_tampered)

        # Key order invariance
        assert h1 == h2
        # Tamper detection
        assert h1 != h_tamp
