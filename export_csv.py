import os

import psycopg2
import csv

from dotenv import load_dotenv
load_dotenv()


DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

def export_ledger_to_csv():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        c = conn.cursor()
        
        
        c.execute("SELECT * FROM history LIMIT 0;")
        colnames = [desc[0] for desc in c.description]
        
        
        c.execute("SELECT * FROM history ORDER BY id ASC;")
        rows = c.fetchall()
        
       
        with open("gateway_benchmark_results.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(colnames)  
            writer.writerows(rows)     
            
        print(f"Successfully exported {len(rows)} records to 'gateway_benchmark_results.csv'")
        
        c.close()
        conn.close()
    except Exception as e:
        print(f"Failed to export data: {e}")

if __name__ == "__main__":
    export_ledger_to_csv()