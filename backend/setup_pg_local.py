import psycopg

def setup():
    conn = psycopg.connect("postgresql://postgres@localhost:5432/postgres", autocommit=True)
    c = conn.cursor()
    c.execute("SELECT 1 FROM pg_roles WHERE rolname='converza'")
    if not c.fetchone():
        c.execute("CREATE ROLE converza WITH LOGIN PASSWORD 'converza_secret_pass' SUPERUSER")
        print("Role 'converza' criada com sucesso.")
    else:
        c.execute("ALTER ROLE converza WITH PASSWORD 'converza_secret_pass'")
        print("Role 'converza' atualizada.")

    c.execute("SELECT 1 FROM pg_database WHERE datname='converza'")
    if not c.fetchone():
        c.execute("CREATE DATABASE converza OWNER converza")
        print("Database 'converza' criado com sucesso.")
    else:
        print("Database 'converza' ja existe.")

    conn.close()

if __name__ == '__main__':
    setup()
