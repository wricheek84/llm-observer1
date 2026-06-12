import os
import re
import sys
import time
import numpy as np
import psycopg2
import grpc
import requests
from datetime import datetime
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import inference_pb2
import inference_pb2_grpc

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_COLLECTION = "knowledge_base"

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "wricheek"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

print("[INIT] Connecting to PostgreSQL...")
db_conn = psycopg2.connect(**DB_CONFIG)
db_cursor = db_conn.cursor()

print("[INIT] Connecting to Qdrant Vector Engine...")
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

print("[INIT] Loading Local Critic Model (BAAI/bge-small-en-v1.5) on CPU...")
critic_model = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu")

print("[INIT] Establishing gRPC Channel to C++ Inference Server...")
grpc_channel = grpc.insecure_channel("localhost:50051")
cpp_stub = inference_pb2_grpc.InferenceEngineStub(grpc_channel)

FAITHFULNESS_THRESHOLD = 0.60

def check_regex_pii(text):
    pii_patterns = {
        "EMAIL": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "PHONE": r"\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}",
        "CREDIT_CARD": r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}"
    }
    for pii_type, pattern in pii_patterns.items():
        if re.search(pattern, text):
            return True, pii_type
    return False, None

def dummy_tokenize(text):
    return [ord(char) for char in text]

def query_openrouter(prompt, system_context=None):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    messages = []
    if system_context:
        messages.append({"role": "system", "content": system_context})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": "openai/gpt-oss-20b:free",
        "messages": messages
    }
    
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        if response.status_code != 200:
            print(f"\n[OPENROUTER API REJECTION] Status: {response.status_code} | Link: {response.text}")
        res_json = response.json()
        return res_json['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"\n[OPENROUTER CRITICAL ERROR] {e}")
        return "API_ERROR_EMPTY_RESPONSE"

    

def calculate_faithfulness(cloud_response, ground_truth_chunks):
    if not ground_truth_chunks:
        return 0.0
    
    response_vector = critic_model.encode(cloud_response, convert_to_numpy=True)
    chunk_vectors = [critic_model.encode(chunk, convert_to_numpy=True) for chunk in ground_truth_chunks]
    
    max_sim = 0.0
    for cv in chunk_vectors:
        sim = np.dot(response_vector, cv) / (np.linalg.norm(response_vector) * np.linalg.norm(cv))
        if sim > max_sim:
            max_sim = sim
    return float(max_sim)

def log_transaction(user_input, regex_status, inference_result, inference_time, llm_response, critic_score, verdict, final_output):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        query = """
            INSERT INTO history (
                timestamp, user_input, regex_status, inference_result, 
                inference_time, llm_response, critic_score, verdict, final_output
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        db_cursor.execute(query, (
            timestamp, user_input, regex_status, inference_result, 
            inference_time, llm_response, critic_score, verdict, final_output
        ))
        db_conn.commit()
    except Exception as e:
        db_conn.rollback()
        print(f"[DATABASE ERROR] Failed to commit row: {e}")

def run_chat_sandbox():
    
    print(" SRE-PILOT WATCHDOG: LIVE INTERACTIVE SECURITY PROXY CHAT")
    print("Type your technical queries below. Type 'exit' or 'quit' to stop.\n")
    
    while True:
        try:
            user_prompt = input("User >>> ").strip()
            if not user_prompt:
                continue
            if user_prompt.lower() in ['exit', 'quit']:
                print("\n[SHUTDOWN] Exiting sandbox cleanly. Closing descriptors.")
                break
                
            start_time = time.time()
            
            has_pii, pii_type = check_regex_pii(user_prompt)
            if has_pii:
                print(f"\n[WATCHDOG SECURITY BLOCK] Local Regex flagged sensitive information path ({pii_type}).")
                print("Bot  >>> Security policy violation. Request dropped locally.\n")
                log_transaction(user_prompt, "FAILED", 0, 0.0, None, None, "SECURITY_BLOCK", "[WITHHELD_PII]")
                continue

            token_array = dummy_tokenize(user_prompt)
            grpc_request = inference_pb2.InferenceRequest(
                model_id="classifier",
                tokens=token_array
            )
            
            cpp_latency = 0.0
            try:
                grpc_response, call = cpp_stub.RunInference.with_call(grpc_request)
                
                for key, value in call.trailing_metadata():
                    if key == 'x-inference-latency-ms':
                        cpp_latency = float(value)
                
                if grpc_response.output_tokens and grpc_response.output_tokens[0] == 1:
                    print(f"\n[WATCHDOG SECURITY BLOCK] C++ ONNX Layer flagged malicious exploit signature.")
                    print(f"[TELEMETRY] Internal Engine Core processing speed: {cpp_latency:.4f}ms")
                    print("Bot  >>> Input intent verification failed. Request terminated.\n")
                    log_transaction(user_prompt, "PASSED", 1, cpp_latency, None, None, "SECURITY_BLOCK", "[WITHHELD_EXPLOIT]")
                    continue
                    
            except grpc.RpcError as g_err:
                if g_err.code() == grpc.StatusCode.RESOURCE_EXHAUSTED:
                    print("\n[GATEWAY CRITICAL] C++ Engine thrown backpressure overload block (>500 queue length).")
                    print("Bot  >>> Gateway busy. Try again shortly.\n")
                    continue
                else:
                    print(f"\n[CONNECTION ERROR] Local C++ pipeline unreachable: {g_err.details()}")
                    continue

            ground_truth_chunks = []
            try:
                search_results = qdrant_client.query_points(
                    collection_name=QDRANT_COLLECTION,
                    query=critic_model.encode(user_prompt).tolist(),
                    limit=2
                ).points
                
                ground_truth_chunks = [hit.payload["text_content"] for hit in search_results if hit.payload and "text_content" in hit.payload]
            except Exception as e:
                print(f"\n[RAG WARNING] Could not search collection '{QDRANT_COLLECTION}': {e}")
                ground_truth_chunks = []
            
            cloud_output = query_openrouter(user_prompt)
            
            if not ground_truth_chunks:
                faithfulness_score = 0.0
            else:
                faithfulness_score = calculate_faithfulness(cloud_output, ground_truth_chunks)

            total_round_trip_ms = (time.time() - start_time) * 1000.0

            if faithfulness_score >= FAITHFULNESS_THRESHOLD:
                print(f"\n[GATEWAY VERIFIED] Score: {faithfulness_score:.4f} >= {FAITHFULNESS_THRESHOLD}")
                print(f"Bot  >>> {cloud_output}\n")
                log_transaction(user_prompt, "PASSED", 0, cpp_latency, cloud_output, faithfulness_score, "SUCCESS", cloud_output)
                
            else:
                print(f"\n[WATCHDOG ALERT] Hallucination detected ({faithfulness_score:.4f} < {FAITHFULNESS_THRESHOLD}). Executing recovery...")
                
                context_injection = " ".join(ground_truth_chunks)
                healed_system_prompt = f"Strict Directive: Rely explicitly on this context data to formulate responses: {context_injection}"
                
                healed_cloud_output = query_openrouter(user_prompt, system_context=healed_system_prompt)
                healed_score = calculate_faithfulness(healed_cloud_output, ground_truth_chunks)
                total_round_trip_ms = (time.time() - start_time) * 1000.0
                
                if healed_score >= FAITHFULNESS_THRESHOLD:
                    print(f"[GATEWAY VERIFIED] Self-healing loop successful! Remedied score: {healed_score:.4f}")
                    print(f"Bot  >>> {healed_cloud_output}\n")
                    log_transaction(user_prompt, "PASSED", 0, cpp_latency, cloud_output, healed_score, "HEALED", healed_cloud_output)
                else:
                    print(f"[WATCHDOG CRITICAL] Recovery response failed security threshold ({healed_score:.4f}).")
                    print("Bot  >>> I do not have enough verified documentation to answer that safely.\n")
                    log_transaction(user_prompt, "PASSED", 0, cpp_latency, cloud_output, healed_score, "BLOCKED", "I do not have enough verified documentation to answer that safely.")
                    
        except KeyboardInterrupt:
            print("\n\n[SHUTDOWN] Intercepted break. Terminating.")
            break

    db_cursor.close()
    db_conn.close()
    grpc_channel.close()

if __name__ == "__main__":
    run_chat_sandbox()