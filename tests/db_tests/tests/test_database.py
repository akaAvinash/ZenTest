"""
Database-level tests — these talk to database/database.py directly via
sqlite3, not over HTTP, so (unlike ui_tests/api_tests) they only make sense
against a local inventory.db and can't run against the deployed Render app.

Automates the 20 cases in ZenTest_DB_Test_Cases.pdf (DB-01 .. DB-20) —
each test's docstring names which case it covers.
"""

import sqlite3

import pytest

from database.database import DB_NAME, get_connection, init_db


@pytest.fixture
def sample_product():
    """Inserts one product, yields its id, and cleans up (including any
    inventory_items rows referencing it) afterward."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
        ("DB Fixture Product", 5.00, 10),
    )
    conn.commit()
    product_id = conn.execute(
        "SELECT id FROM products WHERE name = 'DB Fixture Product' ORDER BY id DESC LIMIT 1"
    ).fetchone()["id"]
    conn.close()

    yield product_id

    conn = get_connection()
    conn.execute("DELETE FROM inventory_items WHERE product_id = ?", (product_id,))
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()


def test_init_db_creates_expected_tables():
    """DB-01, DB-02: init_db() creates both products and inventory_items."""
    init_db()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row["name"] for row in cursor.fetchall()}
    conn.close()

    assert "products" in tables
    assert "inventory_items" in tables


def test_init_db_is_idempotent():
    """DB-03: calling init_db() repeatedly doesn't error or duplicate tables."""
    init_db()
    init_db()  # should not raise

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name, COUNT(*) as c FROM sqlite_master WHERE type='table' "
        "AND name IN ('products', 'inventory_items') GROUP BY name"
    )
    counts = {row["name"]: row["c"] for row in cursor.fetchall()}
    conn.close()

    assert counts["products"] == 1
    assert counts["inventory_items"] == 1


def test_product_id_autoincrements_sequentially():
    """DB-04: products.id is unique and strictly increasing across inserts."""
    conn = get_connection()
    ids = []
    for name in ("Seq A", "Seq B", "Seq C"):
        conn.execute(
            "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
            (name, 1.0, 1),
        )
        ids.append(conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])
    conn.commit()

    conn.execute(
        "DELETE FROM products WHERE name IN ('Seq A', 'Seq B', 'Seq C')"
    )
    conn.commit()
    conn.close()

    assert len(set(ids)) == 3  # all unique
    assert ids == sorted(ids)  # strictly increasing


def test_insert_and_query_product():
    """DB-05: a product round-trips exactly as inserted."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
        ("DB Test Widget", 4.25, 7),
    )
    product_id = cursor.lastrowid
    conn.commit()

    cursor.execute(
        "SELECT name, price, stock FROM products WHERE id = ?", (product_id,)
    )
    row = cursor.fetchone()

    # Clean up — this test talks to the DB directly, so it can (and should)
    # remove exactly what it inserted, unlike the HTTP-based suites which
    # can only clean up through the API.
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

    assert row["name"] == "DB Test Widget"
    assert row["price"] == 4.25
    assert row["stock"] == 7


def test_null_name_rejected():
    """DB-06: products.name is NOT NULL."""
    conn = get_connection()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
            (None, 5.0, 1),
        )
    conn.close()


def test_null_price_rejected():
    """DB-07: products.price is NOT NULL."""
    conn = get_connection()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
            ("No Price", None, 1),
        )
    conn.close()


def test_stock_defaults_to_zero_when_omitted():
    """DB-08: stock has DEFAULT 0 when not provided on insert."""
    conn = get_connection()
    conn.execute("INSERT INTO products (name, price) VALUES (?, ?)", ("No Stock Given", 3.0))
    conn.commit()

    row = conn.execute(
        "SELECT stock FROM products WHERE name = 'No Stock Given'"
    ).fetchone()

    conn.execute("DELETE FROM products WHERE name = 'No Stock Given'")
    conn.commit()
    conn.close()

    assert row["stock"] == 0


def test_update_product_stock_persists(sample_product):
    """DB-09: an UPDATE to stock is visible on a subsequent SELECT."""
    conn = get_connection()
    conn.execute("UPDATE products SET stock = ? WHERE id = ?", (12, sample_product))
    conn.commit()

    row = conn.execute(
        "SELECT stock FROM products WHERE id = ?", (sample_product,)
    ).fetchone()
    conn.close()

    assert row["stock"] == 12


def test_delete_product_removes_it():
    """DB-10: a deleted product no longer appears in subsequent queries."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
        ("To Delete", 1.0, 1),
    )
    conn.commit()
    product_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()

    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()

    assert row is None


def test_insert_cart_item_for_valid_product(sample_product):
    """DB-11: an inventory_items row referencing a real product inserts cleanly."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO inventory_items (product_id, quantity) VALUES (?, ?)",
        (sample_product, 3),
    )
    conn.commit()

    row = conn.execute(
        "SELECT product_id, quantity FROM inventory_items WHERE product_id = ?",
        (sample_product,),
    ).fetchone()
    conn.close()

    assert row["product_id"] == sample_product
    assert row["quantity"] == 3


def test_foreign_key_not_enforced_by_default():
    """DB-12: SQLite does not enforce the declared FK unless PRAGMA
    foreign_keys=ON is set — get_connection() doesn't set it, so an
    inventory_items row referencing a non-existent product silently
    succeeds. Documents a real gap, not a hypothetical one."""
    conn = get_connection()
    non_existent_product_id = 999999

    # Should NOT raise, since FK enforcement is off by default in this
    # connection — if this ever starts raising, it means someone added
    # `PRAGMA foreign_keys = ON` and this test (and the assumption behind
    # it) needs revisiting.
    conn.execute(
        "INSERT INTO inventory_items (product_id, quantity) VALUES (?, ?)",
        (non_existent_product_id, 1),
    )
    conn.commit()

    row = conn.execute(
        "SELECT * FROM inventory_items WHERE product_id = ?", (non_existent_product_id,)
    ).fetchone()

    conn.execute("DELETE FROM inventory_items WHERE product_id = ?", (non_existent_product_id,))
    conn.commit()
    conn.close()

    assert row is not None


def test_cart_join_matches_price_times_quantity(sample_product):
    """DB-13: the products/inventory_items JOIN (mirroring GET /api/cart
    in database/api.py) computes total = price * quantity correctly."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO inventory_items (product_id, quantity) VALUES (?, ?)",
        (sample_product, 3),
    )
    conn.commit()

    row = conn.execute(
        """
        SELECT products.price * inventory_items.quantity AS total
        FROM inventory_items
        JOIN products ON inventory_items.product_id = products.id
        WHERE products.id = ?
        """,
        (sample_product,),
    ).fetchone()
    conn.close()

    assert row["total"] == 5.00 * 3


def test_row_factory_allows_column_name_access():
    """DB-14: get_connection() rows support both row['col'] and row[index]."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
        ("Row Access Check", 2.0, 1),
    )
    conn.commit()

    row = conn.execute(
        "SELECT name FROM products WHERE name = 'Row Access Check'"
    ).fetchone()

    conn.execute("DELETE FROM products WHERE name = 'Row Access Check'")
    conn.commit()
    conn.close()

    assert row["name"] == "Row Access Check"
    assert row[0] == "Row Access Check"


def test_data_persists_across_separate_connections():
    """DB-15: a commit on one connection is visible from a brand-new
    get_connection() call — confirms both point at the same on-disk file."""
    conn_a = get_connection()
    conn_a.execute(
        "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
        ("Cross Connection", 1.0, 1),
    )
    conn_a.commit()
    conn_a.close()

    conn_b = get_connection()
    row = conn_b.execute(
        "SELECT name FROM products WHERE name = 'Cross Connection'"
    ).fetchone()
    conn_b.execute("DELETE FROM products WHERE name = 'Cross Connection'")
    conn_b.commit()
    conn_b.close()

    assert row is not None
    assert row["name"] == "Cross Connection"


def test_two_sequential_inserts_both_succeed():
    """DB-16: two inserts from separate connections, committed back-to-back,
    both land without error or overwriting each other."""
    conn_a = get_connection()
    conn_a.execute(
        "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
        ("Concurrent A", 1.0, 1),
    )
    conn_a.commit()
    conn_a.close()

    conn_b = get_connection()
    conn_b.execute(
        "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
        ("Concurrent B", 2.0, 2),
    )
    conn_b.commit()
    conn_b.close()

    conn = get_connection()
    rows = conn.execute(
        "SELECT name FROM products WHERE name IN ('Concurrent A', 'Concurrent B')"
    ).fetchall()
    conn.execute("DELETE FROM products WHERE name IN ('Concurrent A', 'Concurrent B')")
    conn.commit()
    conn.close()

    assert {r["name"] for r in rows} == {"Concurrent A", "Concurrent B"}


def test_float_price_round_trips_without_precision_loss():
    """DB-17: a price like 9.99 reads back exactly as stored."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
        ("Precision Check", 9.99, 1),
    )
    conn.commit()

    row = conn.execute(
        "SELECT price FROM products WHERE name = 'Precision Check'"
    ).fetchone()

    conn.execute("DELETE FROM products WHERE name = 'Precision Check'")
    conn.commit()
    conn.close()

    assert row["price"] == 9.99


def test_clearing_inventory_items_leaves_products_untouched(sample_product):
    """DB-18: DELETE FROM inventory_items (simulating checkout) doesn't
    touch the products table at all."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO inventory_items (product_id, quantity) VALUES (?, ?)",
        (sample_product, 2),
    )
    conn.commit()

    conn.execute("DELETE FROM inventory_items")
    conn.commit()

    cart_rows = conn.execute("SELECT * FROM inventory_items").fetchall()
    product_row = conn.execute(
        "SELECT * FROM products WHERE id = ?", (sample_product,)
    ).fetchone()
    conn.close()

    assert cart_rows == []
    assert product_row is not None


def test_inventory_db_created_on_disk_when_missing(tmp_path, monkeypatch):
    """DB-19: init_db() creates inventory.db fresh in a directory where it
    doesn't exist yet. Uses a temp cwd so this never touches the real
    project inventory.db."""
    monkeypatch.chdir(tmp_path)

    db_file = tmp_path / DB_NAME
    assert not db_file.exists()

    init_db()

    assert db_file.exists()


def test_query_nonexistent_product_returns_none():
    """DB-20: SELECT for a product id that doesn't exist returns no rows
    (fetchone() is None), not an error — the behavior database/api.py's
    404 handling in get_product() relies on."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM products WHERE id = ?", (999999,)).fetchone()
    conn.close()

    assert row is None
