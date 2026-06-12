import psycopg2

DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "wricheek",
    "host": "localhost",
    "port": "5432"
}

def reset_ledger():
    conn = psycopg2.connect(**DB_CONFIG)
    c = conn.cursor()
   
    c.execute("TRUNCATE TABLE history RESTART IDENTITY;")
    conn.commit()
    c.close()
    conn.close()
    print("PostgreSQL 'history' table successfully cleared and reset to ID 1.")

if __name__ == "__main__":
    reset_ledger()