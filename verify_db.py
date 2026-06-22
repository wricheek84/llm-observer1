import psycopg2
from llm_db import DB_CONFIG

def verify_database_integrity():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        c = conn.cursor()
    except Exception as e:
        print(f"Failed to connect to PostgreSQL: {e}")
        return
    
    print("=" * 60)
    print("POSTGRESQL DATA INTEGRITY & SANITY REPORT")
    print("=" * 60)
    
    # 1. Total Rows & Status Grouping Check
    c.execute("SELECT status, COUNT(*) FROM history GROUP BY status;")
    status_counts = c.fetchall()
    print("\n[1] Exact Row Breakdown in 'history' Table:")
    for status, count in status_counts:
        print(f"  • Logged Status: {status:<15} | Rows: {count}")
        
    # 2. Sequence ID Validation (Gaps & Loss Check)
    c.execute("SELECT MIN(id), MAX(id), COUNT(id) FROM history;")
    min_id, max_id, total_ids = c.fetchone()
    print(f"\n[2] Sequence ID Gaps Check:")
    print(f"  • Starting Primary Key ID : {min_id}")
    print(f"  • Ending Primary Key ID   : {max_id}")
    print(f"  • Total Actual Row Count  : {total_ids}")
    
    if min_id == 1 and max_id == 150 and total_ids == 150:
        print("  ⚡ STATUS: PERFECT. Exact 1:1 sequence match. Zero rows lost.")
    else:
        print("  ⚠️ WARNING: Data mismatch or gap detected in database sequences!")

    # 3. Check the Eval Runs Summary Sync
    c.execute("""
        SELECT success_count, healed_count, blocked_count, failures, avg_latency 
        FROM eval_runs 
        ORDER BY id DESC LIMIT 1;
    """)
    summary = c.fetchone()
    if summary:
        print("\n[3] Automated CI/CD Summary Sync ('eval_runs' table):")
        print(f"  • Logged Successes : {summary[0]}")
        print(f"  • Logged Heals     : {summary[1]}")
        print(f"  • Logged Blocks    : {summary[2]}")
        print(f"  • Logged Failures  : {summary[3]}")
        print(f"  • Recorded Latency : {summary[4]:.2f}ms")
    else:
        print("\n[3] Automated CI/CD Summary Sync: No data rows found in eval_runs.")

    # 4. Content Verification Sample
    print("\n[4] Database Content Sample (First 2 Logs):")
    c.execute("SELECT id, input_text, status FROM history ORDER BY id ASC LIMIT 2;")
    samples = c.fetchall()
    for row in samples:
        short_text = row[1][:50] + "..." if len(row[1]) > 50 else row[1]
        print(f"  • ID {row[0]} | Prompt: '{short_text}' | Status: {row[2]}")

    print("\n" + "=" * 60)
    c.close()
    conn.close()

if __name__ == "__main__":
    verify_database_integrity()