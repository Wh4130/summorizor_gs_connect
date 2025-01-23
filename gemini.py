from dotenv import dotenv_values
import json
import google.generativeai as genai

API_KEY = dotenv_values()['GEMINI']

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash",
                              system_instruction = "Write a 100 word description for the concept/word I input",
                              generation_config = genai.GenerationConfig(
                                    max_output_tokens=40000,
                                    temperature=0.0,
                                ))
response = model.generate_content("Japan")
for chunk in response:
    print(chunk.text)


# url = f'https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={API_KEY}'
# headers = {'Content-Type': 'application/json'}
# data = {
#     "contents": [
#         {
#             "parts": [{"text": "你好，你是誰？"}]
#         }
#     ]
# }
# response = requests.post(url, headers=headers, json=data)
# print(f"response status_code: {response.status_code}")
# print(json.dumps(response.json(), indent=4, ensure_ascii=False))