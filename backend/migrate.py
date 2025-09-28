# backend/migrate.py
# Runs SQL files in backend/migrations AND applies a safety patch to ensure
# peer_pool.created_at exists (prevents HTTP 500 on /peers even if a file was missed).

import os
from pathlib import Path
from sqlalchemy import create_engine, text

HERE = Path(__file__).parent
MIGRATIONS_DIR = HERE / "migrations"

CREATE_MIGRATION_TABLE = """
CREATE TABLE IF NOT EXISTS _migrations (
  id serial PRIMARY KEY,
  filename text UNIQUE NOT NULL,
  applied_at timestamptz NOT NULL DEFAULT now()
);
"""

def ensure_peerpool_created_at(conn):
    # Safety patch: add the column if it doesn't exist
    exists = conn.execute(text("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'peer_pool' AND column_name = 'created_at';
    """)).first()
    if not exists:
        conn.exec_driver_sql(
            "ALTER TABLE peer_pool ADD COLUMN created_at timestamptz DEFAULT now();"
        )
        print("✓ Added peer_pool.created_at")
    else:
        print("✓ peer_pool.created_at already exists")

def apply_file_migrations(conn):
    conn.execute(text(CREATE_MIGRATION_TABLE))
    done = {r.filename for r in conn.execute(text("SELECT filename FROM _migrations"))}

    files = []
    if MIGRATIONS_DIR.exists():
        files = sorted(p for p in MIGRATIONS_DIR.glob("*.sql") if p.is_file())

    if not files:
        print("No migration files found in", MIGRATIONS_DIR)
        return

    for f in files:
        if f.name in done:
            continue
        sql = f.read_text(encoding="utf-8")
        print(f"Applying: {f.name}")
        if sql.strip():
            conn.exec_driver_sql(sql)
        conn.execute(text("INSERT INTO _migrations (filename) VALUES (:f)"), {"f": f.name})
        print(f"✓ {f.name} applied")

def main():
    db_url = os.environ["DATABASE_URL"]
    engine = create_engine(db_url, future=True)
    with engine.begin() as conn:
        apply_file_migrations(conn)
        # Always run the safety patch
        ensure_peerpool_created_at(conn)
    print("Migrations applied.")

if __name__ == "__main__":
    main()
