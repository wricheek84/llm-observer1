import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()


DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
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