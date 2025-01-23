from managers import *
import hashlib
# LlmManager.gemini_config()
# model = LlmManager.init_gemini_model("請依據我輸入的概念，產出與之有關的五個關鍵字。用中文")
# response = LlmManager.gemini_api_call(model, "日本")
# print(response)


def reversible_hash(data):
    hash_object = hashlib.sha256(data.encode())
    return hash_object.hexdigest()

def reverse_hash(hash_value):
    # Iterate through all possible combinations
    for i in range(1000000):
        test_data = str(i)
        if reversible_hash(test_data) == hash_value:
            return test_data
    return None

ps_encoded = reversible_hash("aaa")
print(ps_encoded)
print(reverse_hash(ps_encoded))