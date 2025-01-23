from managers import *

LlmManager.gemini_config()
model = LlmManager.init_gemini_model("請依據我輸入的概念，產出與之有關的五個關鍵字。用中文")
response = LlmManager.gemini_api_call(model, "日本")
print(response)