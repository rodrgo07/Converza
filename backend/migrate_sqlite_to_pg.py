"""
Script de Migração Segura: SQLite -> PostgreSQL para o Converza CRM
Lê todos os registros do SQLite converza.db e insere no PostgreSQL preservando integridade referencial,
relacionamentos, foreign keys e sequências de IDs.
"""
import os
import sys
import sqlite3
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Set paths
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app.core.config import settings

def migrate():
    sqlite_path = os.path.join(os.path.dirname(__file__), "converza.db")
    if not os.path.exists(sqlite_path):
        print("Arquivo SQLite converza.db não encontrado. Nada a migrar.")
        return

    print("=" * 60)
    print("INICIANDO MIGRAÇÃO SEGURA: SQLite -> PostgreSQL")
    print("=" * 60)

    # 1. Connect SQLite
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    s_cursor = sqlite_conn.cursor()

    # 2. Connect PostgreSQL
    pg_url = settings.DATABASE_URL
    print(f"Conectando ao PostgreSQL em: {pg_url.split('@')[-1] if '@' in pg_url else pg_url}")
    pg_engine = create_engine(pg_url)
    PgSession = sessionmaker(bind=pg_engine)
    pg_session = PgSession()

    # Order of tables respecting Foreign Keys
    tables_order = [
        "companies",
        "subscriptions",
        "users",
        "pipeline_stages",
        "tags",
        "quick_replies",
        "whatsapp_accounts",
        "customers",
        "customer_tags",
        "opportunities",
        "conversations",
        "messages",
        "follow_ups",
        "tasks",
        "notifications",
        "audit_logs"
    ]

    stats = {}

    try:
        # Disable foreign keys temporarily if needed or insert in dependency order
        for table in tables_order:
            s_cursor.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{table}'")
            if s_cursor.fetchone()[0] == 0:
                continue

            s_cursor.execute(f"SELECT * FROM {table}")
            rows = s_cursor.fetchall()
            stats[table] = len(rows)

            if not rows:
                print(f"• Tabela {table}: 0 registros (vazia)")
                continue

            print(f"• Migrando {table}: {len(rows)} registros...")

            col_names = [d[0] for d in s_cursor.description]
            cols_joined = ", ".join([f'"{c}"' for c in col_names])
            placeholders = ", ".join([f":{c}" for c in col_names])
            insert_sql = text(f'INSERT INTO "{table}" ({cols_joined}) VALUES ({placeholders}) ON CONFLICT DO NOTHING')

            for r in rows:
                row_dict = dict(r)
                # Convert SQLite integers (0/1) to Python bools for boolean columns
                for bool_col in ["is_active", "onboarding_completed", "is_connected", "is_read"]:
                    if bool_col in row_dict and row_dict[bool_col] is not None:
                        row_dict[bool_col] = bool(row_dict[bool_col])
                pg_session.execute(insert_sql, row_dict)

            pg_session.commit()

            # Update PostgreSQL sequence to match MAX(id)
            try:
                pg_session.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM \"{table}\""))
                pg_session.commit()
            except Exception:
                pass

        print("=" * 60)
        print("MIGRAÇÃO DE DADOS CONCLUÍDA COM SUCESSO!")
        print("RESUMO DOS REGISTROS MIGRADOS:")
        for t, count in stats.items():
            print(f"  - {t}: {count} registros")
        print("=" * 60)

    except Exception as e:
        pg_session.rollback()
        print(f"ERRO durante a migração: {e}")
        raise e
    finally:
        sqlite_conn.close()
        pg_session.close()

if __name__ == "__main__":
    migrate()
