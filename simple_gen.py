
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

print(f"Key: {api_key[:5]}...{api_key[-5:] if api_key else ''}")
print(f"Model: {model_name}")

genai.configure(api_key=api_key)
model = genai.GenerativeModel(model_name)

try:
    response = model.generate_content("Hello")
    print("Response:", response.text)
except Exception as e:
    print("Error:", e)
