import psycopg2
from datetime import datetime


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
def create_db():
    """Initializes the PostgreSQL history table if it doesn't exist."""
    conn = psycopg2.connect(**DB_CONFIG)
    c = conn.cursor()
    
   
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id SERIAL PRIMARY KEY,
            timestamp TEXT NOT NULL,
            user_input TEXT NOT NULL,
            regex_status TEXT NOT NULL,
            inference_result INTEGER NOT NULL,
            inference_time REAL NOT NULL,
            llm_response TEXT,
            critic_score REAL,
            verdict TEXT NOT NULL,
            final_output TEXT NOT NULL
        )
    ''')
    conn.commit()
    c.close()
    conn.close()
    print("PostgreSQL 'history' table verified successfully.")

def insert_request(user_input, regex_status, inference_result, inference_time, llm_response, critic_score, verdict, final_output):
    """Inserts a multi-stage request tracing log into PostgreSQL."""
    conn = psycopg2.connect(**DB_CONFIG)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    
    c.execute('''
        INSERT INTO history (
            timestamp, user_input, regex_status, inference_result, 
            inference_time, llm_response, critic_score, verdict, final_output
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (timestamp, user_input, regex_status, inference_result, 
          inference_time, llm_response, critic_score, verdict, final_output))
    
    conn.commit()
    c.close()
    conn.close()

if __name__ == "__main__":
    create_db()