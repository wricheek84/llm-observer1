import time
import re
import warnings
from transformers import pipeline

# Suppress HuggingFace warnings for a clean output
warnings.filterwarnings("ignore")

print("[INIT] Loading AI NER Model (this will take a few seconds to download/load into memory)...")
# We use a standard BERT model fine-tuned for finding entities like Names, Orgs, and Locations
ai_model = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple")

# Our lightning-fast Regex net
regex_email = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")

# The Test Subject
test_prompt = "Hello, my account is locked. Please contact me at john.doe@enterprise.com so we can fix this."

print("\n--- RUNNING THE 5-MINUTE MICRO-BENCHMARK ---")

# 1. Race the Regex
start_regex = time.perf_counter()
regex_result = regex_email.findall(test_prompt)
end_regex = time.perf_counter()
regex_time_ms = (end_regex - start_regex) * 1000

# 2. Race the AI Model
start_model = time.perf_counter()
model_result = ai_model(test_prompt)
end_model = time.perf_counter()
model_time_ms = (end_model - start_model) * 1000

# 3. The Verdict
print(f"\n[REGEX] Found target in: {regex_time_ms:.4f} milliseconds")
print(f"[AI MODEL] Processed text in: {model_time_ms:.4f} milliseconds")

speed_multiplier = model_time_ms / regex_time_ms if regex_time_ms > 0 else float('inf')
print(f"\n[CONCLUSION] The AI Model is {speed_multiplier:.0f}x slower than Regex on a single sentence.")