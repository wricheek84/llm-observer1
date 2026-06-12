import psycopg2

DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "wricheek",
    "host": "localhost",
    "port": "5432"
}

def check_database_salvage():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        c = conn.cursor()
        
        # Aggregate logs grouped by pipeline outcome
        c.execute("SELECT verdict, COUNT(*) FROM history GROUP BY verdict;")
        records = c.fetchall()
        
        print("\n============================================================")
        print(" POSTGRESQL RUNTIME SALVAGE REPORT")
        print("============================================================")
        if not records:
            print(" Table is completely empty. The crash hit before the first commit.")
        else:
            total_saved = 0
            for verdict, count in records:
                print(f" Ledger Status: {verdict:<16} | Logs Committed: {count}")
                total_saved += count
            print("------------------------------------------------------------")
            print(f" Total safe rows captured: {total_saved} / 150")
        print("============================================================\n")
        
        c.close()
        conn.close()
    except Exception as e:
        print(f"[-] Unable to query database: {e}")

if __name__ == "__main__":
    check_database_salvage()