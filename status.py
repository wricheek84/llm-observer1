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



def check_database_salvage():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        c = conn.cursor()
        
        
        c.execute("SELECT verdict, COUNT(*) FROM history GROUP BY verdict;")
        records = c.fetchall()
        
       
        print(" POSTGRESQL RUNTIME SALVAGE REPORT")
        
        if not records:
            print(" Table is completely empty. The crash hit before the first commit.")
        else:
            total_saved = 0
            for verdict, count in records:
                print(f" Ledger Status: {verdict:<16} | Logs Committed: {count}")
                total_saved += count
            print("------------------------------------------------------------")
            print(f" Total safe rows captured: {total_saved} / 150")
       
        
        c.close()
        conn.close()
    except Exception as e:
        print(f"[-] Unable to query database: {e}")

if __name__ == "__main__":
    check_database_salvage()