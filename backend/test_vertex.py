
import vertexai
from vertexai.generative_models import GenerativeModel
import os
import sys

# Mimic app config
PROJECT_ID = "profitscout-lx6bb"
LOCATION = "global"
MODEL_NAME = "gemini-3-flash-preview"

print(f"Testing Vertex AI init with:")
print(f"  Project: {PROJECT_ID}")
print(f"  Location: {LOCATION}")
print(f"  Model: {MODEL_NAME}")

try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = GenerativeModel(MODEL_NAME)
    print("Initialization successful.")
except Exception as e:
    print(f"CRITICAL: Failed to init Vertex AI: {e}")
    sys.exit(1)

print("Attempting to generate content...")
try:
    response = model.generate_content("Hello, can you hear me?")
    print(f"Generation successful. Response: {response.text}")
except Exception as e:
    print(f"Generation failed: {e}")
    sys.exit(1)
