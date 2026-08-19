import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

prompt = "Write a one-sentence tagline for a cybersecurity internship program."
temperatures = [0, 0.7, 1.0]

results = {}
for temp in temperatures:
    outputs = []
    for i in range(3):
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=temp)
        )
        outputs.append(response.text.strip())
    results[temp] = outputs
    print(f"\n=== Temperature {temp} ===")
    for i, o in enumerate(outputs, 1):
        print(f"{i}. {o}")