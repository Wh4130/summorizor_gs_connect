import streamlit as st
import pandas as pd
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import dotenv_values
from pypdf import PdfReader
import json
import requests
import base64
import google.generativeai as genai
import hashlib
import datetime as dt
import random
import string

class LlmManager:

    @staticmethod
    def gemini_config():
        try:
            genai.configure(api_key = dotenv_values()['GEMINI'])
        except:
            genai.configure(api_key = st.secrets['credits']['GEMINI_KEY'])
    
    @staticmethod
    def init_gemini_model(system_prompt, max_output_tokens = 40000, temperature = 0.00):
        model = genai.GenerativeModel("gemini-1.5-flash",
                                    system_instruction = system_prompt,
                                    generation_config = genai.GenerationConfig(
                                            max_output_tokens = max_output_tokens,
                                            temperature = temperature,
                                        ))
        return model
        
    @staticmethod
    def gemini_api_call(model, in_message):

        response = model.generate_content(in_message)

        return response.text

class SheetManager:

    @staticmethod
    def authenticate_google_sheets():
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(st.secrets['gsheet-conn']['credits']), scope)
        client = gspread.authorize(creds)
        return client
    
    @staticmethod
    def extract_sheet_id(sheet_url):
        try:
            return sheet_url.split("/d/")[1].split("/")[0]
        except IndexError:
            st.error("無效的試算表連結，請檢查 URL 格式。")
            return None
        
    @staticmethod
    def fetch(sheet_id, worksheet):
        if sheet_id:
            client = SheetManager.authenticate_google_sheets()
            try:
                sheet = client.open_by_key(sheet_id)
                ws = sheet.worksheet(worksheet)
                data = ws.get_all_records()
                
                return pd.DataFrame(data)
            except:
                st.write("Connection Failed")

    @staticmethod
    def insert(sheet_id, worksheet, row: list):
        if sheet_id:
            client = SheetManager.authenticate_google_sheets()
            try:
                sheet = client.open_by_key(sheet_id)
                worksheet = sheet.worksheet(worksheet)
                worksheet.freeze(rows = 1)
                worksheet.append_row(row)

                records = worksheet.get_all_records()
                
            except Exception as e:
                st.write(f"Connection Failed: {e}")

    @staticmethod
    def delete_row(sheet_id, worksheet_name, row_idx: int):
        if not sheet_id:
            st.write("No sheet_id provided!")
            return

        try:
            client = SheetManager.authenticate_google_sheets()

            sheet = client.open_by_key(sheet_id)
            worksheet = sheet.worksheet(worksheet_name)
            
            worksheet.delete_rows(row_idx)

        except Exception as e:
            st.write(f"Failed to delete row: {e}")


class DataManager:

    @staticmethod
    @st.dialog("請上傳欲處理的檔案（pdf）")
    def FORM_pdf_input():
        pdf_uploaded = st.file_uploader("**請上傳 pdf 檔案（支援多檔案上傳）**", accept_multiple_files = True)
        language = st.selectbox("請選擇摘要語言", ["Traditional Chinese", "English", "Japanese"])
        tag = st.selectbox("請選擇文件類別標籤", st.session_state["user_tags"][st.session_state["user_tags"]["_userId"] == st.session_state["user_id"]]["tags"].tolist())
        instructions = st.text_area("請輸入額外的摘要指示（Optional）")
        if st.button("確認"):
            if language is None:
                st.warning("請選擇語言")
                st.stop()
            if pdf_uploaded:
                for file in pdf_uploaded:
                    if file.name not in st.session_state["pdfs_raw"]["filename"]:
                        pdf_in_messages = DataManager.load_pdf(file)
                        st.session_state["pdfs_raw"].loc[len(st.session_state["pdfs_raw"]), ["filename", "content", "tag", "language", "selected", "additional_prompt"]] = [file.name, pdf_in_messages, tag, language, False, instructions]
                st.session_state["lang"] = language
                st.session_state["other_prompt"] = instructions if instructions else "None"
                st.session_state["tag"] = tag
            else:
                st.warning("請上傳檔案")
                st.stop()
            st.rerun()

    @staticmethod
    @st.cache_data
    def load_pdf(uploaded):

        '''load pdf data from user upload with caching'''
        reader = PdfReader(uploaded)
        number_of_pages = len(reader.pages)
        texts = []
        for i in range(number_of_pages):
            page = reader.pages[i]
            texts.append(f"【page {i}】\n" + page.extract_text())

        return "\n".join(texts)
    
    @staticmethod
    def find_json_object(input_string):
        '''catch the JSON format from LLM response'''

        # Match JSON-like patterns
        input_string = input_string.replace("\n", '').strip()
        input_string = input_string.encode("utf-8").decode("utf-8")
        start_index = input_string.find('{')
        end_index = input_string.rfind('}')

        if start_index != -1 and end_index != -1:
            json_string = input_string[start_index:end_index+1]
            try:
                json_object = json.loads(json_string)
                return json_object
            except json.JSONDecodeError:
                return "DecodeError"
        # st.write(json_string)

        return None  # Return None if no valid JSON is found
    
    # --- Transform Picture to Base64
    @staticmethod
    def image_to_b64(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    
    # --- Generate a random index for document
    def generate_random_index():
        characters = string.ascii_letters + string.digits  # a-z, A-Z, 0-9
        return ''.join(random.choices(characters, k = 8))
    
class UserManager:
    # * Hash password
    @staticmethod
    def ps_hash(password: str):
        hash_object = hashlib.sha256(password.encode())
        return hash_object.hexdigest()
    
    # * Verify password
    @staticmethod
    def ps_verify(attempt: str, ps_hashed: str):
        return UserManager.ps_hash(attempt) == ps_hashed


    @staticmethod
    @st.dialog("Login")
    def log_in():
        user_id = st.text_input("請輸入使用者 ID 或 Email")
        password = st.text_input("請輸入密碼", type = "password")

        # * 登入
        if st.button("登入"):
            # 驗證登入
            st.session_state['user_infos'] = SheetManager.fetch(SheetManager.extract_sheet_id(st.secrets['gsheet-urls']['user']), "user_info")
            if ((user_id not in st.session_state['user_infos']['_userId'].tolist()) and
                (user_id not in st.session_state['user_infos']['_email'].tolist())):

                st.warning("使用者ID / Email 不存在")
                st.stop()
            if user_id.endswith("@gmail.com"): 
                ps_hash_cached = st.session_state['user_infos'].loc[st.session_state['user_infos']['_email'] == user_id, "_password"].tolist()[0]
            else:
                ps_hash_cached = st.session_state['user_infos'].loc[st.session_state['user_infos']['_userId'] == user_id, "_password"].tolist()[0]
            
            if not UserManager.ps_verify(password, ps_hash_cached):
                st.warning("密碼錯誤，請重試一遍")
                st.stop()

            # 成功登入
            st.session_state['logged_in'] = True
            
            try:
                st.session_state['user_name'] = st.session_state['user_infos'].loc[st.session_state['user_infos']['_userId'] == user_id, "_username"].tolist()[0]
                st.session_state['user_id'] = st.session_state['user_infos'].loc[st.session_state['user_infos']['_userId'] == user_id, "_userId"].tolist()[0]

            except:
                st.session_state['user_name'] = st.session_state['user_infos'].loc[st.session_state['user_infos']['_email'] == user_id, "_username"].tolist()[0]
                st.session_state['user_id'] = st.session_state['user_infos'].loc[st.session_state['user_infos']['_email'] == user_id, "_userId"].tolist()[0]

            del ps_hash_cached
            del st.session_state["user_infos"]
            st.rerun()

    @staticmethod
    @st.dialog("Register")
    def register():
        username = st.text_input("請輸入使用者名稱")
        user_id = st.text_input("請輸入使用者ID")
        email = st.text_input("請輸入Gmail")
        password_ = st.text_input("請設定密碼", type = "password")
        password_confirm = st.text_input("再次確認密碼", type = "password")
        if st.button("送出", key = "Regist"):
            st.session_state['user_infos'] = SheetManager.fetch(SheetManager.extract_sheet_id(st.secrets['gsheet-urls']['user']), "user_info")
            # * 註冊驗證
            if not username:
                st.warning("請輸入使用者名稱")
                st.stop()
            if not user_id:
                st.warning("請輸入使用者ID")
                st.stop()
            if user_id in st.session_state['user_infos']['_userId'].tolist():
                st.warning("使用者ID已被使用，請重新輸入")
                st.stop()
            if not email:
                st.warning("請輸入Gmail")
                st.stop()
            if not email.endswith("@gmail.com"):
                st.warning("請輸入有效Gmail")
                st.stop()
            if email in st.session_state['user_infos']['_email'].tolist():
                st.warning("Gmail已被使用，請重新輸入")
                st.stop()
            if not password_:
                st.warning("請設定密碼")
                st.stop()
            if password_ != password_confirm:
                st.warning("密碼不相符，請重試")
                st.stop()
            
            # * 註冊資料送出
            with st.spinner("註冊中"):
                SheetManager.insert(
                    sheet_id = SheetManager.extract_sheet_id(st.secrets['gsheet-urls']['user']),
                    worksheet = "user_info",
                    row = [username, user_id, email, UserManager.ps_hash(password_), dt.datetime.now().strftime("%I:%M%p on %B %d, %Y")]
                )
                SheetManager.insert(
                    sheet_id = SheetManager.extract_sheet_id(st.secrets['gsheet-urls']['user']),
                    worksheet = "user_tags",
                    row = [user_id, "default"]
                )
            st.success("註冊成功！")
            time.sleep(3)
            st.session_state["logged_in"] = True
            st.session_state['user_name'] = username
            st.session_state['user_id'] = user_id
            del st.session_state["user_infos"]
            del st.session_state["user_tags"]
            st.rerun()

class PromptManager:

    @staticmethod
    def summarize(lang, other_prompt):
        return f"""
You are a competent research assistant. I would input a pdf essay / report, and I would like you to summarize that file precisely. 

Detailed instructions:
1. I would like you to output the summary in **{lang}**
2. The output should be in JSON format
3. Please summarize in details. All paragraphs should be summarized correctly.
4. The summary should follow the format that I give you. Give me structrual summary data rather than only description.
5. Summary should be a valid string format that does not affect the parsing of JSON. However, the content should be a valid HTML format!
6. Please also recognize and highlight the keywords in your summary, making them bold by <strong> tag.

Other instructions:
{other_prompt}

<output schema>
{{"summary": "<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Summary</title>
</head>
<body>

  <h3>Brief Summary</h3>

  <h3>Paragraphs</h3>
  <ul>
    <li>
      <h4>Paragraph 1 Title</h4>
      <p>Paragraph 1 summary</p>
    </li>
    <li>
      <h4>Paragraph 2 Title</h4>
      <p>Paragraph 2 summary</p>
    </li>
    </ul>

  <h3>Implication</h3>

  <h3>Keywords</h3>
  <p>
    #keyword1, #keyword2, #keyword3, ... list 7 - 10 
  </p>

</body>
</html>"}}
"""
    
class Others:

    @staticmethod
    def fetch_IP():
        response = requests.get("https://api.ipify.org?format=json")
        public_ip = response.json()["ip"]
        st.caption(f"Deployed IP Address: **:blue[{public_ip}]**")