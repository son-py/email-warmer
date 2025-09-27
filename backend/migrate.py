import os
from sqlalchemy import text
from .db import engine

SQL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "migrations", "001_init.sql")

with open(SQL_PATH, "r", encoding="utf-8") as f:
    sql = f.read()

statements = [s.strip() for s in sql.split(";") if s.strip()]
with engine.begin() as conn:
    for stmt in statements:
        conn.execute(text(stmt))

print("Migrations applied.")
