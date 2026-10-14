import sqlite3
import pandas as pd
import os

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.csv")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fashion.db")
TABLE_NAME = "products"


def setup_database():
    """Load CSV into SQLite. Skip when fashion.db already exists."""

    if os.path.exists(DB_PATH):
        print(f"[database] Using existing {DB_PATH}")
        return

    print(f"[database] Loading CSV from {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)

    df.columns = df.columns.str.strip()

    for col in ["launch_on", "last_seen_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col], errors="coerce"
            ).dt.strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_PATH)
    df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
    conn.close()

    print(f"[database] {len(df)} rows written to {DB_PATH}")


def execute_readonly_query(sql: str, params: list) -> list:
    """Execute a parameterized SELECT query in read-only mode."""

    if not sql.lstrip().upper().startswith("SELECT "):
        raise ValueError("Only SELECT queries are permitted.")

    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    try:
        conn.execute("PRAGMA query_only = ON")
        cursor = conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


if __name__ == "__main__":
    setup_database()

    results = execute_readonly_query(
        "SELECT product_name, brand, selling_price_INR FROM products LIMIT 5",
        []
    )

    print("\nSample rows:")
    for row in results:
        print(row)