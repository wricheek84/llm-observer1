import time
import requests

def run_chat_sandbox():
    print(" LLM-OBSERVER : LIVE INTERACTIVE SECURITY PROXY CHAT")
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
            
            response = requests.post(
                "http://127.0.0.1:8001/chat",
                json={"user_query": user_prompt}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "error" in data:
                    print(f"\n[GATEWAY ERROR] {data['error']} - {data.get('details', '')}\n")
                elif data.get("status") in ["block", "BLOCKED"]:
                    reason = data.get("reason", data.get("details", "Blocked by security policy."))
                    print(f"\n[BLOCKED] {reason}")
                    if "response" in data:
                        print(f"Fallback: {data['response']}\n")
                    else:
                        print()
                else:
                    print(f"\nWatchdog [{data.get('status', 'SUCCESS')}] >>> {data.get('response', '')}")
                    latency = data.get('engine_latency_ms', 'N/A')
                    score = data.get('faithfulness_score', 'N/A')
                    print(f"[Metrics: Latency {latency} | Score: {score}]\n")
            else:
                print(f"\n[HTTP ERROR] Server responded with {response.status_code}\n")
                
        except requests.exceptions.ConnectionError:
            print("\n[NETWORK ERROR] Could not connect to gateway. Is gateway.py running on port 8001?\n")
        except KeyboardInterrupt:
            print("\n\n[SHUTDOWN] Intercepted break. Terminating.")
            break

if __name__ == "__main__":
    run_chat_sandbox()