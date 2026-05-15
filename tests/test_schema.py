"""Smoke test — ensure imports work and schema is intact."""

from mnemo import schema


def test_constants_present():
    assert schema.EMBEDDING_DIM == 384
    assert schema.SIMILARITY_THRESHOLD == 0.4
    assert schema.TOP_K_DEFAULT == 3


def test_memory_types_exhaustive():
    assert set(schema.MEMORY_TYPES) == {"file", "screenshot", "activity"}


def test_response_types_exhaustive():
    assert set(schema.RESPONSE_TYPES) == {"answer", "action", "not_found"}


def test_schema_sql_creates_tables():
    import sqlite3
    conn = sqlite3.connect(":memory:")
    conn.executescript(schema.SCHEMA_SQL)
    tables = [row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]
    assert "memories" in tables
    assert "embeddings" in tables
    assert "activity_log" in tables
